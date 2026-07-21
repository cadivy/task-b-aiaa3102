"""Build the final ranked audit table and its adjudication memo.

The module-specific audits intentionally keep broader candidate pools.  The
course submission, however, asks for a concise ranked list that covers all six
issue types without bulk over-reporting.  This script selects the six strongest
reviewed examples per issue type and verifies the public confidence cap.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
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
ISSUE_ORDER = [
    "exact_duplicate",
    "near_duplicate",
    "leakage",
    "label_error",
    "shortcut",
    "ambiguous",
]
ROWS_PER_TYPE = 6
MAX_HIGH_FRACTION = 0.55

SOURCE_BY_TYPE = {
    "exact_duplicate": ROOT / "suspicious_examples_dup_leak.csv",
    "near_duplicate": ROOT / "suspicious_examples_dup_leak.csv",
    "leakage": ROOT / "suspicious_examples_dup_leak.csv",
    "label_error": ROOT / "results" / "suspicious_examples_b.csv",
    "shortcut": ROOT / "results" / "shortcut" / "shortcut_findings.csv",
    "ambiguous": ROOT / "results" / "suspicious_examples_b.csv",
}


def load_ranked(issue_type: str) -> pd.DataFrame:
    source = SOURCE_BY_TYPE[issue_type]
    frame = pd.read_csv(source, keep_default_na=False)
    missing = [column for column in SCHEMA if column not in frame.columns]
    if missing:
        raise AssertionError(f"{source} is missing columns: {missing}")
    selected = frame.loc[frame["issue_type"].eq(issue_type), SCHEMA].copy()
    selected["rank"] = pd.to_numeric(selected["rank"], errors="raise")
    selected = selected.sort_values(["rank", "id"], kind="stable").head(ROWS_PER_TYPE)
    if len(selected) != ROWS_PER_TYPE:
        raise AssertionError(
            f"Expected {ROWS_PER_TYPE} reviewed {issue_type} rows, found {len(selected)}"
        )
    return selected


def validate_submission(frame: pd.DataFrame) -> None:
    if list(frame.columns) != SCHEMA:
        raise AssertionError("Submission columns do not match the public schema")
    if len(frame) < 35:
        raise AssertionError(f"Submission needs at least 35 rows, found {len(frame)}")
    if set(frame["issue_type"]) != set(ISSUE_ORDER):
        raise AssertionError("Submission must cover all six issue types")
    if not frame["confidence"].isin(["low", "medium", "high"]).all():
        raise AssertionError("Unexpected confidence value")
    if frame[["id", "split", "evidence_1", "short_explanation"]].eq("").any().any():
        raise AssertionError("Required evidence fields must not be empty")
    high_fraction = float(frame["confidence"].eq("high").mean())
    if high_fraction > MAX_HIGH_FRACTION:
        raise AssertionError(
            f"High-confidence fraction {high_fraction:.3f} exceeds {MAX_HIGH_FRACTION:.2f}"
        )


def build_adjudication_memo(frame: pd.DataFrame) -> pd.DataFrame:
    canonical = pd.read_csv(ROOT / "data" / "canonical_sms.csv", keep_default_na=False)
    labels = dict(zip(canonical["id"], canonical["label"]))
    decisions = {
        "exact_duplicate": "duplicate_confirmed",
        "near_duplicate": "near_duplicate_accepted",
        "leakage": "leakage_confirmed",
        "label_error": "likely_label_error",
        "shortcut": "shortcut_stress_case",
        "ambiguous": "ambiguous_policy_case",
    }
    rows = []
    for index, item in enumerate(frame.itertuples(index=False), start=1):
        rows.append(
            {
                "claim_id": f"C{index:03d}",
                "id": item.id,
                "split": item.split,
                "issue_type": item.issue_type,
                "public_label": labels.get(item.id, ""),
                "automated_evidence": f"{item.evidence_1}; {item.evidence_2}",
                "policy_review": item.short_explanation,
                "final_decision": decisions[item.issue_type],
                "final_confidence": item.confidence,
                "recommended_action": item.recommended_action,
                "final_reason": item.short_explanation,
                "review_status": "integrated_from_reviewed_team_artifacts",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    selected = []
    for issue_type in ISSUE_ORDER:
        selected.append(load_ranked(issue_type))
    submission = pd.concat(selected, ignore_index=True)
    submission["rank"] = range(1, len(submission) + 1)
    validate_submission(submission)

    output = ROOT / "suspicious_examples.csv"
    submission.to_csv(output, index=False, quoting=csv.QUOTE_MINIMAL)

    memo = build_adjudication_memo(submission)
    memo.to_csv(ROOT / "adjudication_memo.csv", index=False, quoting=csv.QUOTE_MINIMAL)

    issue_counts = submission["issue_type"].value_counts().sort_index().to_dict()
    confidence_counts = submission["confidence"].value_counts().to_dict()
    high_fraction = submission["confidence"].eq("high").mean()
    print(f"wrote={output}")
    print(f"rows={len(submission)} issue_counts={issue_counts}")
    print(f"confidence_counts={confidence_counts} high_fraction={high_fraction:.3f}")


if __name__ == "__main__":
    main()
