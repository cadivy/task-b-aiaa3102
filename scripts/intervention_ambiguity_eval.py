"""Intervention 4: adjudication-aware evaluation.

Held-out rows that the audit judged ambiguous have no single defensible label,
and rows judged likely label errors are scored against a label we argue is
wrong. Neither is a fair test of the model. This drops them from scoring and
re-scores the frozen baseline, which puts a reproducible number on the
sensitivity bound that section 6 of the report otherwise states by hand.

Targets the label-noise/ambiguity findings (targets 4 and 6), so it pairs with
scripts/intervention_leakage_eval.py the way target 6 pairs with target 3: same
mechanism, different data problem, deliberately different magnitude.

Run from project/ with:  python scripts/intervention_ambiguity_eval.py
"""

from __future__ import annotations

import pandas as pd

from common import RESULTS_DIR, classification_metrics, write_json

SUSPICIOUS_PATH = RESULTS_DIR / "suspicious_examples_b.csv"


def heldout_ids(suspicious: pd.DataFrame, issue_type: str) -> list[str]:
    rows = suspicious[
        (suspicious["issue_type"] == issue_type) & (suspicious["split"] == "heldout")
    ]
    return sorted(rows["id"])


def scenario(heldout: pd.DataFrame, excluded: list[str]) -> dict[str, object]:
    kept = heldout[~heldout["id"].isin(excluded)]
    dropped = heldout[heldout["id"].isin(excluded)]
    metrics = classification_metrics(kept["label"], kept["word_pred"])
    metrics["excluded_rows"] = len(excluded)
    # The whole argument rests on these rows being concentrated in the error
    # set: if the baseline already got them right, removing them proves nothing.
    metrics["excluded_rows_baseline_got_wrong"] = int(
        (dropped["word_pred"] != dropped["label"]).sum()
    )
    return metrics


def main() -> None:
    heldout = pd.read_csv(RESULTS_DIR / "heldout_predictions.csv", keep_default_na=False)
    suspicious = pd.read_csv(SUSPICIOUS_PATH, keep_default_na=False)

    ambiguous = heldout_ids(suspicious, "ambiguous")
    label_errors = heldout_ids(suspicious, "label_error")

    conditions = {
        "original_heldout": [],
        "exclude_ambiguous": ambiguous,
        "exclude_ambiguous_and_suspected_label_errors": ambiguous + label_errors,
    }
    results = {name: scenario(heldout, ids) for name, ids in conditions.items()}

    baseline = results["original_heldout"]
    final = results["exclude_ambiguous_and_suspected_label_errors"]
    payload = {
        "intervention": "adjudication_aware_evaluation",
        "description": "Drop held-out rows the audit judged ambiguous or mislabelled, re-score frozen baseline.",
        "ambiguous_heldout_ids": ambiguous,
        "suspected_label_error_heldout_ids": label_errors,
        "conditions": results,
        "accuracy_delta": final["accuracy"] - baseline["accuracy"],
        "spam_recall_delta": final["spam_recall"] - baseline["spam_recall"],
    }
    write_json(RESULTS_DIR / "intervention_ambiguity_eval.json", payload)

    print(f"ambiguous held-out rows        : {len(ambiguous)} {ambiguous}")
    print(f"suspected label errors held-out: {len(label_errors)} {label_errors}")
    print()
    for name, metrics in results.items():
        print(
            f"{name:46s} n={metrics['n']:4d}  acc={metrics['accuracy']:.6f}  "
            f"spam_recall={metrics['spam_recall']:.6f}"
        )
    print()
    print(f"removed rows the baseline got wrong: {final['excluded_rows_baseline_got_wrong']}/{final['excluded_rows']}")
    print(f"accuracy delta : {payload['accuracy_delta']:+.6f}")


if __name__ == "__main__":
    main()
