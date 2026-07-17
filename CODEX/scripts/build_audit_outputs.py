"""Build ranked audit and adjudication files from reproducible evidence and review config."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from common import ROOT, RESULTS_DIR, load_canonical, load_protocol


MANUAL_REVIEW_PATH = ROOT / "configs" / "manual_review.json"


def pair_row(table: pd.DataFrame, left: str, right: str) -> pd.Series:
    mask = (
        ((table["id_1"] == left) & (table["id_2"] == right))
        | ((table["id_1"] == right) & (table["id_2"] == left))
    )
    if not mask.any():
        raise KeyError(f"Pair not found: {left}, {right}")
    return table[mask].iloc[0]


def concise(text: str, limit: int = 210) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def main() -> None:
    protocol = load_protocol()
    review = json.loads(MANUAL_REVIEW_PATH.read_text(encoding="utf-8"))
    canonical = load_canonical().set_index("id", drop=False)
    clusters = pd.read_csv(RESULTS_DIR / "exact_duplicate_clusters.csv", keep_default_na=False)
    members = pd.read_csv(RESULTS_DIR / "exact_duplicate_members.csv", keep_default_na=False)
    near = pd.read_csv(RESULTS_DIR / "near_duplicate_adjudication.csv", keep_default_na=False)
    leakage = pd.read_csv(RESULTS_DIR / "leakage_cases.csv", keep_default_na=False)
    label_evidence = pd.read_csv(RESULTS_DIR / "label_noise_evidence.csv", keep_default_na=False).set_index("id")
    shortcut = pd.read_csv(RESULTS_DIR / "shortcut_predictions.csv", keep_default_na=False).set_index("id")

    claims: list[dict] = []

    def add_claim(
        *,
        id_: str,
        issue_type: str,
        confidence: str,
        evidence_1: str,
        evidence_2: str,
        action: str,
        explanation: str,
        priority: int,
        decision: str,
    ) -> None:
        row = canonical.loc[id_]
        claims.append(
            {
                "id": id_,
                "split": row["split"],
                "issue_type": issue_type,
                "confidence": confidence,
                "evidence_1": concise(evidence_1),
                "evidence_2": concise(evidence_2),
                "recommended_action": action,
                "short_explanation": concise(explanation),
                "_priority": priority,
                "_decision": decision,
                "_current_label": row["label"],
            }
        )

    exact_selection = [
        ("E0009", "H0009", "high"),
        ("E0049", "H0548", "high"),
        ("E0091", "H0909", "high"),
        ("E0164", "H0412", "high"),
        ("E0285", "H0922", "high"),
        ("E0014", "T0069", "medium"),
        ("E0028", "T0161", "medium"),
    ]
    for cluster_id, id_, confidence in exact_selection:
        cluster = clusters[clusters["cluster_id"] == cluster_id].iloc[0]
        cross = bool(cluster["is_cross_split"])
        add_claim(
            id_=id_,
            issue_type="exact_duplicate",
            confidence=confidence,
            evidence_1=f"cluster={cluster_id};size={cluster['cluster_size']};members={cluster['member_ids']}",
            evidence_2=f"splits={cluster['splits']};labels={cluster['labels']};normalization=lowercase+whitespace-collapse",
            action="rebuild_split_by_cluster" if cross else "deduplicate_training_cluster",
            explanation=(
                "This normalized text occurs across train and held-out, so the held-out row is not independent."
                if cross
                else "This repeated training template receives disproportionate weight unless clustering is respected."
            ),
            priority=10 if cross else 35,
            decision="should_fix" if cross else "keep_but_flag",
        )

    near_selection = [
        ("T1013", "H0470", "high"),
        ("H0644", "T2769", "high"),
        ("H0445", "T4014", "high"),
        ("H0548", "T4090", "high"),
        ("T0218", "H0738", "medium"),
        ("T0885", "H0311", "medium"),
        ("T1881", "H0850", "low"),
        ("T2085", "H0531", "low"),
    ]
    for left, right, confidence in near_selection:
        pair = pair_row(near, left, right)
        accepted = pair["manual_decision"] == "accepted"
        target_id = pair["heldout_id"]
        add_claim(
            id_=target_id,
            issue_type="near_duplicate",
            confidence=confidence,
            evidence_1=(
                f"paired_id={pair['train_id']};word_cos={float(pair['word_similarity']):.4f};"
                f"char_cos={float(pair['char_similarity']):.4f}"
            ),
            evidence_2=pair["manual_reason"],
            action="review_for_cluster_aware_evaluation" if accepted else "retain_as_rejected_candidate",
            explanation=(
                "The held-out message preserves a distinctive training template with minor substitutions."
                if accepted
                else "Similarity crosses the numeric threshold, but manual comparison rejects a shared-source claim."
            ),
            priority=18 if accepted else 92,
            decision="keep_but_flag" if accepted else "false_positive_audit_finding",
        )

    leakage_selection = [
        "H0009",
        "H0548",
        "H0909",
        "H0412",
        "H0922",
        "H0470",
        "H0644",
        "H0445",
        "H0738",
    ]
    for id_ in leakage_selection:
        cases = leakage[leakage["heldout_id"] == id_].sort_values(
            ["match_type", "primary_similarity"], ascending=[True, False]
        )
        case = cases.iloc[0]
        exact = case["match_type"] == "exact"
        add_claim(
            id_=id_,
            issue_type="leakage",
            confidence="high" if exact else "medium",
            evidence_1=(
                f"train_id={case['train_id']};match={case['match_type']};"
                f"similarity={float(case['primary_similarity']):.4f}"
            ),
            evidence_2=f"manual={case['manual_decision']};{case['manual_reason']}",
            action="exclude_from_leakage_aware_metric_and_rebuild_split",
            explanation=(
                "This held-out row is recoverable from a training row and inflates the independence claim of evaluation."
            ),
            priority=1 if exact else 12,
            decision="should_fix",
        )

    for item in review["label_errors"]:
        id_ = item["id"]
        evidence = label_evidence.loc[id_]
        source = "OOF" if evidence["split"] == "train" else "heldout"
        add_claim(
            id_=id_,
            issue_type="label_error",
            confidence=item["confidence"],
            evidence_1=(
                f"{source}_word_p_spam={float(evidence['word_p_spam']):.3f};"
                f"char_p_spam={float(evidence['char_p_spam']):.3f};assigned={evidence['label']}"
            ),
            evidence_2=f"independent_policy_review={item['reason']}",
            action=item["action"],
            explanation=(
                f"Assigned {evidence['label']}; evidence supports {item['proposed_label']}. "
                f"{item['reason']}"
            ),
            priority=8 if item["confidence"] == "high" else 28,
            decision=item["decision"],
        )

    for item in review["shortcut_examples"]:
        id_ = item["id"]
        evidence = shortcut.loc[id_]
        add_claim(
            id_=id_,
            issue_type="shortcut",
            confidence=item["confidence"],
            evidence_1=(
                f"shallow_p_spam={float(evidence['all_shallow_p_spam']):.3f};"
                f"shallow_pred={evidence['all_shallow_pred']}"
            ),
            evidence_2=(
                f"full_text_p_spam={float(evidence['word_p_spam']):.3f};"
                f"full_text_pred={evidence['word_pred']};label={evidence['label']}"
            ),
            action="retain_for_shortcut_stress_test",
            explanation=item["reason"],
            priority=42 if item["confidence"] == "high" else 58,
            decision="keep_but_flag",
        )

    for item in review["ambiguous"]:
        id_ = item["id"]
        evidence = label_evidence.loc[id_]
        add_claim(
            id_=id_,
            issue_type="ambiguous",
            confidence=item["confidence"],
            evidence_1=(
                f"word_p_spam={float(evidence['word_p_spam']):.3f};"
                f"char_p_spam={float(evidence['char_p_spam']):.3f};label={evidence['label']}"
            ),
            evidence_2=f"policy_review={item['reason']}",
            action=item["action"],
            explanation=item["reason"],
            priority=70 if item["decision"] != "false_positive_audit_finding" else 98,
            decision=item["decision"],
        )

    claims.sort(key=lambda item: (item["_priority"], item["issue_type"], item["id"]))
    for rank, claim in enumerate(claims, start=1):
        claim["rank"] = rank

    output_columns = protocol["suspicious_examples_schema"]
    suspicious = pd.DataFrame(claims)[
        [
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
    ]
    suspicious = suspicious[output_columns]
    suspicious.to_csv(ROOT / "suspicious_examples.csv", index=False)

    memo_rows = []
    for claim in claims:
        memo_rows.append(
            {
                "claim_id": f"C{claim['rank']:03d}",
                "id": claim["id"],
                "split": claim["split"],
                "issue_type": claim["issue_type"],
                "current_label": claim["_current_label"],
                "automated_evidence": claim["evidence_1"],
                "policy_review": claim["evidence_2"],
                "final_decision": claim["_decision"],
                "final_confidence": claim["confidence"],
                "recommended_action": claim["recommended_action"],
                "final_reason": claim["short_explanation"],
                "review_status": review["review_method"],
            }
        )
    pd.DataFrame(memo_rows).to_csv(ROOT / "adjudication_memo.csv", index=False)

    high_fraction = (suspicious["confidence"] == "high").mean()
    print(f"Suspicious claims: {len(suspicious)}")
    print(f"Issue types: {sorted(suspicious['issue_type'].unique())}")
    print(f"High-confidence fraction: {high_fraction:.3f}")
    print(suspicious.groupby(["issue_type", "confidence"]).size().to_string())


if __name__ == "__main__":
    main()
