"""Run controlled data interventions and compare evaluation outcomes."""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import (
    FIGURES_DIR,
    RESULTS_DIR,
    ROOT,
    classification_metrics,
    load_canonical,
    normalize_text,
)
from train_baseline import word_pipeline


def fit_condition(name: str, train: pd.DataFrame, heldout: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    model = word_pipeline().fit(train["text"], train["label"])
    pred = model.predict(heldout["text"])
    probability = model.predict_proba(heldout["text"])[
        :, list(model.classes_).index("spam")
    ]
    metrics = classification_metrics(heldout["label"], pred)
    metrics.update(
        {
            "condition": name,
            "train_n": len(train),
            "heldout_n": len(heldout),
            "changed_train_rows": 4460 - len(train),
        }
    )
    predictions = heldout[["id", "label"]].copy()
    predictions["condition"] = name
    predictions["pred"] = pred
    predictions["p_spam"] = probability
    return metrics, predictions


def main() -> None:
    df = load_canonical()
    train = df[df["split"] == "train"].copy().reset_index(drop=True)
    heldout = df[df["split"] == "heldout"].copy().reset_index(drop=True)
    review = json.loads((ROOT / "configs" / "manual_review.json").read_text(encoding="utf-8"))

    overlay_rows = []
    for item in review["label_errors"]:
        if item["decision"] != "should_fix" or not item["id"].startswith("T"):
            continue
        original = train.loc[train["id"] == item["id"], "label"]
        if original.empty:
            raise AssertionError(f"Overlay ID missing from training set: {item['id']}")
        overlay_rows.append(
            {
                "id": item["id"],
                "original_label": original.iloc[0],
                "proposed_label": item["proposed_label"],
                "confidence": item["confidence"],
                "evidence_summary": item["reason"],
                "review_status": "AI-assisted policy review; no held-out labels changed",
            }
        )
    overlay = pd.DataFrame(overlay_rows)
    overlay.to_csv(RESULTS_DIR / "training_label_overlay.csv", index=False)

    conditions: dict[str, pd.DataFrame] = {"original_baseline": train.copy()}

    deduplicated = train.assign(normalized_text=train["text"].map(normalize_text))
    deduplicated = (
        deduplicated.sort_values("uci_row_number")
        .drop_duplicates("normalized_text", keep="first")
        .drop(columns="normalized_text")
    )
    conditions["deduplicate_exact_training"] = deduplicated

    high_filter_ids = set(
        overlay.loc[overlay["confidence"] == "high", "id"].tolist()
    )
    conditions["filter_high_confidence_label_errors"] = train[
        ~train["id"].isin(high_filter_ids)
    ].copy()

    overlaid = train.copy()
    overlay_map = overlay.set_index("id")["proposed_label"].to_dict()
    overlaid["label"] = overlaid.apply(
        lambda row: overlay_map.get(row["id"], row["label"]), axis=1
    )
    conditions["training_label_overlay"] = overlaid

    combined = overlaid.assign(normalized_text=overlaid["text"].map(normalize_text))
    combined = (
        combined.sort_values("uci_row_number")
        .drop_duplicates("normalized_text", keep="first")
        .drop(columns="normalized_text")
    )
    conditions["deduplicate_plus_overlay"] = combined

    metric_rows = []
    prediction_rows = []
    for name, condition_train in conditions.items():
        metrics, predictions = fit_condition(name, condition_train, heldout)
        metric_rows.append(metrics)
        prediction_rows.append(predictions)

    all_predictions = pd.concat(prediction_rows, ignore_index=True)
    baseline_map = (
        all_predictions[all_predictions["condition"] == "original_baseline"]
        .set_index("id")["pred"]
        .to_dict()
    )
    all_predictions["changed_vs_baseline"] = all_predictions.apply(
        lambda row: row["pred"] != baseline_map[row["id"]], axis=1
    )
    all_predictions.to_csv(RESULTS_DIR / "intervention_predictions.csv", index=False)

    for row in metric_rows:
        condition_changes = all_predictions[
            all_predictions["condition"] == row["condition"]
        ]["changed_vs_baseline"].sum()
        row["prediction_changes_vs_baseline"] = int(condition_changes)

    leakage_metrics = pd.read_csv(RESULTS_DIR / "leakage_metrics.csv")
    for _, leakage_row in leakage_metrics.iterrows():
        if leakage_row["condition"] == "original_heldout":
            continue
        metric_rows.append(
            {
                "condition": leakage_row["condition"],
                "train_n": len(train),
                "heldout_n": int(leakage_row["n"]),
                "changed_train_rows": 0,
                "n": int(leakage_row["n"]),
                "accuracy": leakage_row["accuracy"],
                "spam_precision": leakage_row["spam_precision"],
                "spam_recall": leakage_row["spam_recall"],
                "spam_f1": leakage_row["spam_f1"],
                "macro_f1": leakage_row["macro_f1"],
                "confusion_matrix_ham_spam": leakage_row["confusion_matrix_ham_spam"],
                "prediction_changes_vs_baseline": 0,
            }
        )

    metrics_df = pd.DataFrame(metric_rows)
    metrics_df.to_csv(RESULTS_DIR / "intervention_metrics.csv", index=False)

    plot_order = [
        "original_baseline",
        "deduplicate_exact_training",
        "filter_high_confidence_label_errors",
        "training_label_overlay",
        "deduplicate_plus_overlay",
        "exclude_exact_leakage",
        "exclude_exact_and_near_leakage",
    ]
    plot_df = metrics_df.set_index("condition").loc[
        plot_order, ["accuracy", "spam_f1", "macro_f1"]
    ]
    ax = plot_df.plot(
        kind="bar",
        figsize=(10.0, 5.0),
        color=["#2563EB", "#EF4444", "#7C3AED"],
        rot=24,
    )
    ax.set_title("Controlled data-intervention results", loc="left", fontweight="bold")
    ax.set_ylabel("Score")
    ax.set_ylim(0.88, 1.005)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.18)
    ax.legend(frameon=False, ncol=3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "intervention_metrics.png", dpi=180)
    plt.close()

    print(
        metrics_df[
            [
                "condition",
                "train_n",
                "heldout_n",
                "accuracy",
                "spam_recall",
                "spam_f1",
                "macro_f1",
                "prediction_changes_vs_baseline",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
