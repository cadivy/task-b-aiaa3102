"""Evaluate shallow shortcut features, corpus position, and token masking."""

from __future__ import annotations

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from common import (
    FIGURES_DIR,
    MODELS_DIR,
    RESULTS_DIR,
    classification_metrics,
    ensure_dirs,
    load_canonical,
    mask_promotional_tokens,
    shallow_features,
)


SEED = 42
SHAPE_FEATURES = [
    "char_count",
    "token_count",
    "avg_token_length",
    "uppercase_ratio",
    "exclamation_count",
]
CONTACT_PROMO_FEATURES = [
    "digit_count",
    "digit_ratio",
    "currency_count",
    "has_url",
    "has_phone",
    "promo_token_count",
]
ALL_SHALLOW_FEATURES = SHAPE_FEATURES + CONTACT_PROMO_FEATURES


def shallow_model() -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "model",
                LogisticRegression(C=1.0, max_iter=2000, solver="liblinear", random_state=SEED),
            ),
        ]
    )


def text_model() -> Pipeline:
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


def main() -> None:
    ensure_dirs()
    df = load_canonical().reset_index(drop=True)
    features = shallow_features(df)
    train_mask = df["split"] == "train"
    heldout_mask = df["split"] == "heldout"
    train = df[train_mask].reset_index(drop=True)
    heldout = df[heldout_mask].reset_index(drop=True)
    train_features = features[train_mask].reset_index(drop=True)
    heldout_features = features[heldout_mask].reset_index(drop=True)

    rows = []
    prediction_table = heldout[["id", "split", "label", "text"]].copy()

    majority_pred = np.repeat(train["label"].mode().iat[0], len(heldout))
    majority_metrics = classification_metrics(heldout["label"], majority_pred)
    majority_metrics["condition"] = "majority_ham"
    rows.append(majority_metrics)

    fitted_all_model = None
    for condition, columns in (
        ("shape_only", SHAPE_FEATURES),
        ("contact_promo_only", CONTACT_PROMO_FEATURES),
        ("all_shallow", ALL_SHALLOW_FEATURES),
        ("row_position_only", ["row_position"]),
        ("all_shallow_plus_position", ALL_SHALLOW_FEATURES + ["row_position"]),
    ):
        model = shallow_model()
        model.fit(train_features[columns], train["label"])
        pred = model.predict(heldout_features[columns])
        probability = model.predict_proba(heldout_features[columns])[
            :, list(model.classes_).index("spam")
        ]
        metrics = classification_metrics(heldout["label"], pred)
        metrics["condition"] = condition
        rows.append(metrics)
        prediction_table[f"{condition}_p_spam"] = probability
        prediction_table[f"{condition}_pred"] = pred
        if condition == "all_shallow":
            fitted_all_model = model

    masked_train = train["text"].map(mask_promotional_tokens)
    masked_heldout = heldout["text"].map(mask_promotional_tokens)
    masked_model = text_model().fit(masked_train, train["label"])
    masked_pred = masked_model.predict(masked_heldout)
    masked_probability = masked_model.predict_proba(masked_heldout)[
        :, list(masked_model.classes_).index("spam")
    ]
    masked_metrics = classification_metrics(heldout["label"], masked_pred)
    masked_metrics["condition"] = "masked_text"
    rows.append(masked_metrics)
    prediction_table["masked_text_p_spam"] = masked_probability
    prediction_table["masked_text_pred"] = masked_pred

    baseline_predictions = pd.read_csv(RESULTS_DIR / "heldout_predictions.csv")
    baseline_metrics = classification_metrics(
        baseline_predictions["label"], baseline_predictions["word_pred"]
    )
    baseline_metrics["condition"] = "full_text"
    rows.append(baseline_metrics)
    prediction_table = prediction_table.merge(
        baseline_predictions[["id", "word_p_spam", "word_pred"]], on="id", how="left"
    )

    metrics_df = pd.DataFrame(rows)
    metrics_df.to_csv(RESULTS_DIR / "shortcut_metrics.csv", index=False)
    prediction_table.to_csv(RESULTS_DIR / "shortcut_predictions.csv", index=False)

    if fitted_all_model is None:
        raise AssertionError("All-shallow model was not fitted")
    coefficients = fitted_all_model.named_steps["model"].coef_[0]
    pd.DataFrame(
        {"feature": ALL_SHALLOW_FEATURES, "standardized_coefficient": coefficients}
    ).sort_values("standardized_coefficient", ascending=False).to_csv(
        RESULTS_DIR / "shortcut_coefficients.csv", index=False
    )
    joblib.dump(fitted_all_model, MODELS_DIR / "shallow_logreg.joblib")
    joblib.dump(masked_model, MODELS_DIR / "masked_text_logreg.joblib")

    plot_order = [
        "majority_ham",
        "shape_only",
        "contact_promo_only",
        "all_shallow",
        "row_position_only",
        "masked_text",
        "full_text",
    ]
    plot_df = metrics_df.set_index("condition").loc[plot_order, ["accuracy", "spam_f1"]]
    ax = plot_df.plot(
        kind="bar",
        figsize=(9.0, 4.7),
        color=["#2563EB", "#EF4444"],
        rot=24,
    )
    ax.axhline(0.70, color="#111827", linestyle="--", linewidth=1, label="protocol warning")
    ax.set_title("Shortcut probes versus the text baseline", loc="left", fontweight="bold")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.03)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.18)
    ax.legend(frameon=False, ncol=3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "shortcut_metrics.png", dpi=180)
    plt.close()

    print(
        metrics_df[
            ["condition", "n", "accuracy", "spam_precision", "spam_recall", "spam_f1", "macro_f1"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
