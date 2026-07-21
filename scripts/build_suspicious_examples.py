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
        # Certainty follows the evidence type: a byte-identical training match is
        # a fact, while near-duplicate-based leakage inherits the inference risk
        # of the near-duplicate judgement. Severity drives rank, not confidence.
        confidence = "high" if "exact" in str(item["leakage_type"]) else "medium"
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
    # Report exact duplicates by CLUSTER (one representative row each), not by
    # member. 290 clusters cover 705 rows; dumping every member would be bulk
    # over-reporting. Only the 5 cross-split clusters threaten evaluation
    # integrity, so those are high; the rest are ordinary dedup housekeeping.
    clusters = pd.read_csv(
        RESULTS_DIR / "duplicate" / "exact_duplicate_clusters.csv", keep_default_na=False
    )
    members = pd.read_csv(
        RESULTS_DIR / "duplicate" / "exact_duplicate_members.csv", keep_default_na=False
    )
    split_by_id = dict(zip(members["id"], members["split"]))

    clusters["cross_split_sort"] = bool_series(clusters["cross_split"])
    clusters["cluster_size"] = clusters["cluster_size"].astype(int)
    clusters = clusters.sort_values(
        ["cross_split_sort", "cluster_size", "cluster_id"],
        ascending=[False, False, True],
    )

    for _, item in clusters.iterrows():
        cross_split = bool(item["cross_split_sort"])
        rep_id = item["representative_id"]
        # Exact duplication is a deterministic string rule, so certainty that the
        # issue holds is high for every cluster. Severity lives in rank order and
        # in recommended_action, not in the confidence column.
        confidence = "high"
        action = "rebuild_split_by_cluster" if cross_split else "dedupe_by_cluster"
        add_row(
            rows,
            seen,
            {
                "id": rep_id,
                "split": split_by_id.get(rep_id, item["splits"]),
                "issue_type": "exact_duplicate",
                "rank": 0,
                "confidence": confidence,
                "evidence_1": clip(
                    f"Exact duplicate cluster {item['cluster_id']} of size {item['cluster_size']} "
                    f"after lowercase and whitespace normalization; splits={item['splits']}"
                ),
                "evidence_2": clip(
                    f"member_ids={item['member_ids']}; cross_split={item['cross_split']}; "
                    f"label_conflict={item['label_conflict']}"
                ),
                "recommended_action": action,
                "short_explanation": clip(
                    "Cross-split exact duplicate: a held-out row is byte-identical to training text, "
                    "so evaluation should rebuild the split by cluster."
                    if cross_split
                    else "Objective within-split exact duplicate cluster; dedupe by cluster before training."
                ),
            },
        )


def near_confidence(max_similarity: float) -> str:
    # Unlike an exact match, a near-duplicate claim is an inference from a cosine
    # threshold plus manual review, so it never reaches high certainty. Evidence
    # strength is the similarity itself, not how severe the consequence is.
    return "medium" if max_similarity >= 0.98 else "low"


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
        confidence = near_confidence(float(item["max_near_similarity"]))
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
