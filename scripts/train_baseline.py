"""Train reproducible word/character TF-IDF baselines and save audit predictions."""

from __future__ import annotations

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline

from common import (
    FIGURES_DIR,
    MODELS_DIR,
    RESULTS_DIR,
    classification_metrics,
    ensure_dirs,
    load_canonical,
    write_json,
)


SEED = 6767


def word_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.995,
                    sublinear_tf=True,
                ),
            ),
            (
                "model",
                LogisticRegression(C=4.0, max_iter=2000, solver="liblinear", random_state=SEED),
            ),
        ]
    )


def char_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",
                    lowercase=True,
                    ngram_range=(3, 5),
                    min_df=2,
                    max_features=50000,
                    sublinear_tf=True,
                ),
            ),
            (
                "model",
                LogisticRegression(C=4.0, max_iter=2000, solver="liblinear", random_state=SEED),
            ),
        ]
    )


def oof_probabilities(factory, texts: pd.Series, labels: pd.Series) -> np.ndarray:
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    output = np.zeros(len(texts), dtype=float)
    for fold, (train_idx, valid_idx) in enumerate(folds.split(texts, labels), start=1):
        model = factory()
        model.fit(texts.iloc[train_idx], labels.iloc[train_idx])
        spam_index = list(model.classes_).index("spam")
        output[valid_idx] = model.predict_proba(texts.iloc[valid_idx])[:, spam_index]
        print(f"Completed fold {fold}/5 for {factory.__name__}")
    return output


def predictions_from_probability(probability: np.ndarray) -> np.ndarray:
    return np.where(probability >= 0.5, "spam", "ham")


def top_features(model: Pipeline, n: int = 40) -> pd.DataFrame:
    vectorizer = model.named_steps["tfidf"]
    classifier = model.named_steps["model"]
    names = np.asarray(vectorizer.get_feature_names_out())
    coefficients = classifier.coef_[0]
    spam_idx = np.argsort(coefficients)[-n:][::-1]
    ham_idx = np.argsort(coefficients)[:n]
    return pd.DataFrame(
        {
            "spam_feature": names[spam_idx],
            "spam_coefficient": coefficients[spam_idx],
            "ham_feature": names[ham_idx],
            "ham_coefficient": coefficients[ham_idx],
        }
    )


def main() -> None:
    ensure_dirs()
    df = load_canonical().reset_index(drop=True)
    train = df[df["split"] == "train"].copy().reset_index(drop=True)
    heldout = df[df["split"] == "heldout"].copy().reset_index(drop=True)

    train_word_prob = oof_probabilities(word_pipeline, train["text"], train["label"])
    train_char_prob = oof_probabilities(char_pipeline, train["text"], train["label"])

    word_model = word_pipeline().fit(train["text"], train["label"])
    char_model = char_pipeline().fit(train["text"], train["label"])
    word_spam_index = list(word_model.classes_).index("spam")
    char_spam_index = list(char_model.classes_).index("spam")
    heldout_word_prob = word_model.predict_proba(heldout["text"])[:, word_spam_index]
    heldout_char_prob = char_model.predict_proba(heldout["text"])[:, char_spam_index]

    train_predictions = train[["id", "split", "uci_row_number", "label", "text"]].copy()
    train_predictions["word_p_spam"] = train_word_prob
    train_predictions["word_pred"] = predictions_from_probability(train_word_prob)
    train_predictions["char_p_spam"] = train_char_prob
    train_predictions["char_pred"] = predictions_from_probability(train_char_prob)
    train_predictions["prediction_source"] = "5-fold-oof"

    heldout_predictions = heldout[["id", "split", "uci_row_number", "label", "text"]].copy()
    heldout_predictions["word_p_spam"] = heldout_word_prob
    heldout_predictions["word_pred"] = predictions_from_probability(heldout_word_prob)
    heldout_predictions["char_p_spam"] = heldout_char_prob
    heldout_predictions["char_pred"] = predictions_from_probability(heldout_char_prob)
    heldout_predictions["prediction_source"] = "fit-all-train"

    train_predictions.to_csv(RESULTS_DIR / "oof_predictions.csv", index=False)
    heldout_predictions.to_csv(RESULTS_DIR / "heldout_predictions.csv", index=False)
    pd.concat([train_predictions, heldout_predictions], ignore_index=True).to_csv(
        RESULTS_DIR / "all_predictions.csv", index=False
    )

    metric_rows = []
    for name, table in (
        ("word_oof", train_predictions),
        ("char_oof", train_predictions),
        ("word_heldout", heldout_predictions),
        ("char_heldout", heldout_predictions),
    ):
        pred_col = "word_pred" if name.startswith("word") else "char_pred"
        values = classification_metrics(table["label"], table[pred_col])
        values["condition"] = name
        metric_rows.append(values)
    metrics = pd.DataFrame(metric_rows)
    metrics.to_csv(RESULTS_DIR / "baseline_metrics.csv", index=False)
    write_json(RESULTS_DIR / "baseline_metrics.json", metric_rows)
    top_features(word_model).to_csv(RESULTS_DIR / "baseline_top_features.csv", index=False)

    joblib.dump(word_model, MODELS_DIR / "word_tfidf_logreg.joblib")
    joblib.dump(char_model, MODELS_DIR / "char_tfidf_logreg.joblib")

    plot_metrics = metrics.set_index("condition")[["accuracy", "spam_f1", "macro_f1"]]
    ax = plot_metrics.plot(
        kind="bar",
        figsize=(8.0, 4.5),
        color=["#2563EB", "#EF4444", "#7C3AED"],
        rot=20,
    )
    ax.set_title("Baseline performance", loc="left", fontweight="bold")
    ax.set_ylim(0, 1.03)
    ax.set_ylabel("Score")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.18)
    ax.legend(frameon=False, ncol=3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "baseline_metrics.png", dpi=180)
    plt.close()

    print(metrics.drop(columns=["confusion_matrix_ham_spam"]).to_string(index=False))


if __name__ == "__main__":
    main()
