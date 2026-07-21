"""Build the final suspicious_examples.csv and adjudication_memo.csv.

This script merges the per-target audit outputs into the two submission files
required by the handout. It does not re-run any audit; it only selects, ranks,
and calibrates rows that the target scripts and manual review have already
produced.

Confidence policy
-----------------
Confidence states how certain we are that the row is a real instance of the
stated issue type. It is deliberately kept separate from severity, which is
carried by ``recommended_action``.

    high    mechanically provable evidence (exact string identity), or a
            manual adjudication backed by >=0.95 opposition strength or three
            independent signals
    medium  objective evidence that still required a judgement call, such as
            an accepted near-duplicate pair or a two-signal label error
    low     the weakest retained claims, including rows kept on purpose as
            false positives so the calibration can be audited

Rows are ranked within each issue type, strongest evidence first, and the
issue types are emitted in audit-target order.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
CONFIGS_DIR = ROOT / "configs"

SUSPICIOUS_PATH = ROOT / "suspicious_examples.csv"
MEMO_PATH = ROOT / "adjudication_memo.csv"

DUP_LEAK_POOL = ROOT / "suspicious_examples_dup_leak.csv"
LABEL_AMBIG_POOL = RESULTS_DIR / "suspicious_examples_b.csv"
SHORTCUT_POOL = ROOT / "suspicious_examples.csv"

MEMO_B = RESULTS_DIR / "adjudication_memo_b.csv"
NEAR_DUP_DECISIONS = RESULTS_DIR / "duplicate" / "near_duplicate_manual_review_decisions.csv"
SHORTCUT_REVIEW = CONFIGS_DIR / "shortcut_manual_review.csv"

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

MEMO_SCHEMA = [
    "claim_ref",
    "audit_target",
    "issue_type",
    "split",
    "adjudication",
    "confidence",
    "recommended_action",
    "reviewer",
    "reason",
]

ISSUE_ORDER = [
    "exact_duplicate",
    "near_duplicate",
    "leakage",
    "label_error",
    "shortcut",
    "ambiguous",
]

CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2}

# Adjudication categories fixed by starter/configs/audit_protocol.json.
SHOULD_FIX = "should_fix"
KEEP_BUT_FLAG = "keep_but_flag"
AMBIGUOUS_POLICY = "ambiguous_policy_case"
FALSE_POSITIVE = "false_positive_audit_finding"


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False)


def calibrate_exact_duplicates(frame: pd.DataFrame) -> pd.DataFrame:
    """Exact duplicates are provable string identity, so every cluster is high.

    Severity still differs: a cluster that straddles the split threatens
    evaluation integrity and is routed to rebuild_split_by_cluster, while a
    within-split cluster is ordinary de-duplication work.
    """
    output = frame.copy()
    output["confidence"] = "high"
    cross_split = output["recommended_action"] == "rebuild_split_by_cluster"
    output["_sort"] = (~cross_split).astype(int)
    return output


def calibrate_leakage(frame: pd.DataFrame) -> pd.DataFrame:
    """Leakage backed by exact duplicates is high; near-duplicate backed is medium."""
    output = frame.copy()
    exact_backed = output["evidence_2"].str.contains("exact", case=False, na=False)
    output["confidence"] = exact_backed.map({True: "high", False: "medium"})
    output["_sort"] = (~exact_backed).astype(int)
    return output


def keep_pool_calibration(frame: pd.DataFrame) -> pd.DataFrame:
    """Preserve the confidence assigned during manual review."""
    output = frame.copy()
    output["_sort"] = output["confidence"].map(CONFIDENCE_ORDER).fillna(9)
    return output


def build_suspicious_examples() -> pd.DataFrame:
    dup_leak = read_csv(DUP_LEAK_POOL)
    label_ambig = read_csv(LABEL_AMBIG_POOL)
    shortcut = read_csv(SHORTCUT_POOL)
    shortcut = shortcut[shortcut["issue_type"] == "shortcut"]

    parts = {
        "exact_duplicate": calibrate_exact_duplicates(
            dup_leak[dup_leak["issue_type"] == "exact_duplicate"]
        ),
        "near_duplicate": keep_pool_calibration(
            dup_leak[dup_leak["issue_type"] == "near_duplicate"]
        ),
        "leakage": calibrate_leakage(dup_leak[dup_leak["issue_type"] == "leakage"]),
        "label_error": keep_pool_calibration(
            label_ambig[label_ambig["issue_type"] == "label_error"]
        ),
        "shortcut": keep_pool_calibration(shortcut),
        "ambiguous": keep_pool_calibration(
            label_ambig[label_ambig["issue_type"] == "ambiguous"]
        ),
    }

    ordered = []
    for issue_type in ISSUE_ORDER:
        block = parts[issue_type].sort_values(["_sort", "id"], kind="stable")
        ordered.append(block.drop(columns=["_sort"]))

    combined = pd.concat(ordered, ignore_index=True)
    combined["rank"] = range(1, len(combined) + 1)
    return combined[SCHEMA]


def memo_from_target_b() -> pd.DataFrame:
    frame = read_csv(MEMO_B)
    issue_type = frame["decision"].map(
        {AMBIGUOUS_POLICY: "ambiguous", FALSE_POSITIVE: "ambiguous"}
    ).fillna("label_error")
    return pd.DataFrame(
        {
            "claim_ref": frame["id"],
            "audit_target": "4/6 label error and ambiguity",
            "issue_type": issue_type,
            "split": frame["split"],
            "adjudication": frame["decision"],
            "confidence": frame["confidence"],
            "recommended_action": frame["decision"].map(
                {
                    "should_fix": "apply_training_label_overlay",
                    "keep_but_flag": "keep_public_label",
                    "ambiguous_policy_case": "clarify_annotation_policy",
                    "false_positive_audit_finding": "reject_audit_finding",
                }
            ),
            "reviewer": "team manual policy review",
            "reason": frame["reason"],
        }
    )


def memo_from_near_duplicates() -> pd.DataFrame:
    frame = read_csv(NEAR_DUP_DECISIONS)
    adjudication = frame["review_decision"].map(
        {"accepted": SHOULD_FIX, "rejected_false_positive": FALSE_POSITIVE}
    )
    return pd.DataFrame(
        {
            "claim_ref": frame["pair_key"],
            "audit_target": "2 near-duplicate review",
            "issue_type": "near_duplicate",
            "split": "pair",
            "adjudication": adjudication,
            "confidence": frame["confidence"],
            "recommended_action": frame["recommended_action"],
            "reviewer": frame["reviewer"],
            "reason": frame["review_notes"],
        }
    )


def memo_from_shortcuts() -> pd.DataFrame:
    frame = read_csv(SHORTCUT_REVIEW)
    adjudication = frame["decision"].map(
        {"include": KEEP_BUT_FLAG, "exclude": FALSE_POSITIVE}
    )
    return pd.DataFrame(
        {
            "claim_ref": frame["id"],
            "audit_target": "5 shortcut features",
            "issue_type": "shortcut",
            "split": "heldout",
            "adjudication": adjudication,
            "confidence": frame["confidence"],
            "recommended_action": frame["recommended_action"],
            "reviewer": "team manual policy review",
            "reason": frame["review_note"],
        }
    )


def build_adjudication_memo() -> pd.DataFrame:
    memo = pd.concat(
        [memo_from_target_b(), memo_from_near_duplicates(), memo_from_shortcuts()],
        ignore_index=True,
    )
    return memo[MEMO_SCHEMA]


def report(suspicious: pd.DataFrame, memo: pd.DataFrame) -> None:
    high_fraction = (suspicious["confidence"] == "high").mean()
    print(f"suspicious_examples.csv: {len(suspicious)} rows")
    print(f"  issue types      : {suspicious['issue_type'].nunique()}")
    print(f"  high fraction    : {high_fraction:.4f}")
    print(suspicious.groupby(["issue_type", "confidence"]).size().to_string())
    print()
    print(f"adjudication_memo.csv: {len(memo)} rows")
    print(memo["adjudication"].value_counts().to_string())

    assert len(suspicious) >= 35, "protocol requires at least 35 rows"
    assert suspicious["issue_type"].nunique() == 6, "protocol requires all six issue types"
    assert high_fraction <= 0.55, "protocol caps high confidence at 55%"
    assert list(suspicious.columns) == SCHEMA, "schema mismatch"
    assert not memo["adjudication"].isna().any(), "unmapped adjudication category"
    print("\nAll protocol strict checks passed.")


def main() -> None:
    suspicious = build_suspicious_examples()
    memo = build_adjudication_memo()
    suspicious.to_csv(SUSPICIOUS_PATH, index=False)
    memo.to_csv(MEMO_PATH, index=False)
    report(suspicious, memo)


if __name__ == "__main__":
    main()
