"""Build suspicious_examples.csv from reviewed duplicate and leakage outputs.

This is a broad candidate-pool version, not the final trimmed submission. It
includes only issue types that have actually been reviewed in the current
workflow: exact_duplicate, near_duplicate, and leakage. It intentionally does
not emit shortcut, label_error, or ambiguous rows because those require separate
adjudication work.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
OUTPUT_PATH = ROOT / "suspicious_examples_dup_leak.csv"

SCHEMA = [
    "id",
    "split",
    "issue_type",
    "rank",
    "confidence",
    "evidence_1",
    "evidence_2",
    "recommended_action",
    "short_explanation",
]



def clip(text: object, limit: int = 220) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def add_row(rows: list[dict[str, object]], seen: set[tuple[str, str]], row: dict[str, object]) -> None:
    key = (str(row["id"]), str(row["issue_type"]))
    if key in seen:
        return
    seen.add(key)
    rows.append(row)


def bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().eq("true")


def build_leakage_rows(rows: list[dict[str, object]], seen: set[tuple[str, str]]) -> None:
    path = RESULTS_DIR / "leakage" / "leakage_heldout_rows.csv"
    leakage = pd.read_csv(path, keep_default_na=False)
    severity_order = {"high": 0, "medium_high": 1, "medium": 2, "low": 3}
    leakage["severity_order"] = leakage["severity"].map(severity_order).fillna(9)
    leakage["n_total_train_partners"] = leakage["n_total_train_partners"].astype(int)
    leakage["max_similarity"] = leakage["max_similarity"].astype(float)
    leakage = leakage.sort_values(
        ["severity_order", "n_total_train_partners", "max_similarity", "heldout_id"],
        ascending=[True, False, False, True],
    )

    for _, item in leakage.iterrows():
        confidence = "high" if item["severity"] == "high" else "medium"
        duplicate_ref = item["exact_cluster_ids"] or item["near_pair_ids"]
        add_row(
            rows,
            seen,
            {
                "id": item["heldout_id"],
                "split": "heldout",
                "issue_type": "leakage",
                "rank": 0,
                "confidence": confidence,
                "evidence_1": clip(
                    f"Held-out row has {item['n_total_train_partners']} training duplicate partner(s): {item['train_partner_ids']}"
                ),
                "evidence_2": clip(
                    f"leakage_type={item['leakage_type']}; duplicate_ref={duplicate_ref}; max_similarity={float(item['max_similarity']):.4f}"
                ),
                "recommended_action": "should_fix",
                "short_explanation": clip(
                    "Held-out evaluation row is recoverable from training duplicate evidence, so leakage-aware scoring should exclude or flag it."
                ),
            },
        )


def build_exact_rows(rows: list[dict[str, object]], seen: set[tuple[str, str]]) -> None:
    path = RESULTS_DIR / "duplicate" / "reviewed_duplicate_samples.csv"
    samples = pd.read_csv(path, keep_default_na=False)
    exact = samples[samples["n_exact_duplicate_clusters"].astype(int) > 0].copy()
    exact["n_exact_duplicate_partner_samples"] = exact["n_exact_duplicate_partner_samples"].astype(int)
    exact["cross_split_sort"] = bool_series(exact["cross_split_duplicate"])
    exact = exact.sort_values(
        ["cross_split_sort", "n_exact_duplicate_partner_samples", "sample_id"],
        ascending=[False, False, True],
    )

    for _, item in exact.iterrows():
        action = "should_fix" if str(item["split"]) == "heldout" and bool(item["cross_split_sort"]) else "keep_but_flag"
        add_row(
            rows,
            seen,
            {
                "id": item["sample_id"],
                "split": item["split"],
                "issue_type": "exact_duplicate",
                "rank": 0,
                "confidence": "high",
                "evidence_1": clip(
                    f"Exact duplicate cluster(s) {item['exact_cluster_ids']} after lowercase and whitespace normalization"
                ),
                "evidence_2": clip(
                    f"{item['n_exact_duplicate_partner_samples']} duplicate partner sample(s): {item['partner_ids']}; cross_split={item['cross_split_duplicate']}"
                ),
                "recommended_action": action,
                "short_explanation": clip(
                    "This row belongs to an objective exact duplicate cluster; common short SMS phrases are still exact duplicates under the audit rule."
                ),
            },
        )


def near_confidence(categories: str, max_similarity: float) -> str:
    category_set = set(filter(None, str(categories).split("|")))
    if "same_spam_campaign_template" in category_set or max_similarity >= 0.98:
        return "high"
    return "medium"


def build_near_rows(rows: list[dict[str, object]], seen: set[tuple[str, str]]) -> None:
    path = RESULTS_DIR / "duplicate" / "reviewed_duplicate_samples.csv"
    samples = pd.read_csv(path, keep_default_na=False)
    near = samples[samples["n_near_reviewed_accepted_pairs"].astype(int) > 0].copy()
    near["max_near_similarity"] = near["max_near_similarity"].replace("", "0").astype(float)
    near["n_near_reviewed_accepted_pairs"] = near["n_near_reviewed_accepted_pairs"].astype(int)
    near["cross_split_sort"] = bool_series(near["cross_split_duplicate"])
    near = near.sort_values(
        ["cross_split_sort", "n_near_reviewed_accepted_pairs", "max_near_similarity", "sample_id"],
        ascending=[False, False, False, True],
    )

    for _, item in near.iterrows():
        confidence = near_confidence(item["review_categories"], float(item["max_near_similarity"]))
        partner_ids = item["cross_split_partner_ids"] or item["partner_ids"]
        action = "should_fix" if str(item["split"]) == "heldout" and bool(item["cross_split_sort"]) else "keep_but_flag"
        add_row(
            rows,
            seen,
            {
                "id": item["sample_id"],
                "split": item["split"],
                "issue_type": "near_duplicate",
                "rank": 0,
                "confidence": confidence,
                "evidence_1": clip(
                    f"Accepted near pair(s) {item['near_pair_ids']} with max cosine {float(item['max_near_similarity']):.4f}"
                ),
                "evidence_2": clip(
                    f"Manual review category={item['review_categories']}; partner sample(s)={partner_ids}; cross_split={item['cross_split_duplicate']}"
                ),
                "recommended_action": action,
                "short_explanation": clip(
                    "Manual review accepted this as the same campaign/template, message variant, forwarded content, or personalized near duplicate."
                ),
            },
        )


def validate(rows: list[dict[str, object]]) -> dict[str, object]:
    frame = pd.DataFrame(rows, columns=SCHEMA)
    issue_counts = frame["issue_type"].value_counts().to_dict()
    confidence_counts = frame["confidence"].value_counts().to_dict()
    high_fraction = float((frame["confidence"] == "high").mean()) if len(frame) else 0.0
    return {
        "rows": int(len(frame)),
        "issue_types": sorted(frame["issue_type"].unique().tolist()),
        "issue_counts": issue_counts,
        "confidence_counts": confidence_counts,
        "high_fraction": high_fraction,
    }


def main() -> None:
    rows: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    build_leakage_rows(rows, seen)
    build_exact_rows(rows, seen)
    build_near_rows(rows, seen)

    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank

    frame = pd.DataFrame(rows, columns=SCHEMA)
    frame.to_csv(OUTPUT_PATH, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"wrote={OUTPUT_PATH}")
    print(validate(rows))


if __name__ == "__main__":
    main()
