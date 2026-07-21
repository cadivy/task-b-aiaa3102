"""Intervention 2: leakage-aware evaluation.

Deduplication-by-cluster / rebuild-split applied to the evaluation side: drop the
held-out rows that are recoverable from training (exact or accepted-near
duplicates) and re-score the frozen baseline on the clean subset. This measures
how much of the official held-out number is earned on rows the model already saw.

Pairs with intervention 1 (scripts/label_overlay_experiment.py, a relabel
overlay) to satisfy the "compare at least two data interventions" requirement:
the two target different data problems (label noise vs leakage).

Run from project/ with:  python scripts/intervention_leakage_eval.py
"""

from __future__ import annotations

import pandas as pd

from common import RESULTS_DIR, classification_metrics, write_json

LEAKED_PATH = RESULTS_DIR / "leakage" / "leakage_heldout_rows.csv"


def main() -> None:
    heldout = pd.read_csv(RESULTS_DIR / "heldout_predictions.csv", keep_default_na=False)
    leaked = pd.read_csv(LEAKED_PATH, keep_default_na=False)
    leaked_ids = set(leaked["heldout_id"])

    clean = heldout[~heldout["id"].isin(leaked_ids)].copy()

    full_metrics = classification_metrics(heldout["label"], heldout["word_pred"])
    clean_metrics = classification_metrics(clean["label"], clean["word_pred"])

    # How many of the removed rows were actually being predicted correctly? Those
    # are the "free" correct answers leakage was handing the model.
    leaked_rows = heldout[heldout["id"].isin(leaked_ids)]
    leaked_correct = int((leaked_rows["word_pred"] == leaked_rows["label"]).sum())

    payload = {
        "intervention": "leakage_aware_evaluation",
        "description": "Drop held-out rows recoverable from training, re-score frozen baseline.",
        "heldout_rows_full": int(len(heldout)),
        "leaked_rows_removed": int(len(leaked_ids)),
        "leaked_rows_predicted_correctly": leaked_correct,
        "heldout_rows_clean": int(len(clean)),
        "full_heldout": full_metrics,
        "clean_heldout": clean_metrics,
        "accuracy_delta": clean_metrics["accuracy"] - full_metrics["accuracy"],
        "spam_recall_delta": clean_metrics["spam_recall"] - full_metrics["spam_recall"],
    }
    write_json(RESULTS_DIR / "intervention_leakage_eval.json", payload)

    print(f"full  held-out : n={full_metrics['n']:4d}  acc={full_metrics['accuracy']:.6f}  spam_recall={full_metrics['spam_recall']:.6f}")
    print(f"clean held-out : n={clean_metrics['n']:4d}  acc={clean_metrics['accuracy']:.6f}  spam_recall={clean_metrics['spam_recall']:.6f}")
    print(f"removed {len(leaked_ids)} leaked rows, {leaked_correct} of which the baseline got right for free")
    print(f"accuracy delta : {payload['accuracy_delta']:+.6f}")


if __name__ == "__main__":
    main()
