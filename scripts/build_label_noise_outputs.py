"""Turn the target 4 and 6 adjudications into submission rows and the overlay."""

from __future__ import annotations

import json

import pandas as pd

from common import ROOT, RESULTS_DIR, load_canonical, load_protocol

REVIEW_PATH = ROOT / "configs" / "manual_review.json"


def evidence_tokens(row: pd.Series) -> tuple[str, str]:
    signals = []
    if row["word_opposes"]:
        signals.append(f"word_oof_p_spam={row['word_p_spam']:.3f}")
    if row["char_opposes"]:
        signals.append(f"char_oof_p_spam={row['char_p_spam']:.3f}")
    if row["neighbour_opposes"]:
        signals.append(
            f"neighbour_oppose_frac={row['opposite_neighbour_fraction']:.2f}"
        )

    if len(signals) >= 2:
        return signals[0], signals[1]
    if len(signals) == 1:
        return signals[0], "manual_policy_reading"
    return "manual_policy_reading", (
        f"neighbour_labels={row['neighbour_labels']}"
        if row["neighbour_labels"]
        else "no_opposing_signal"
    )


def main() -> None:
    protocol = load_protocol()
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    canonical = load_canonical().set_index("id")
    evidence = pd.read_csv(
        RESULTS_DIR / "label_noise_evidence.csv", keep_default_na=False
    ).set_index("id")

    suspicious: list[dict[str, object]] = []
    memo: list[dict[str, object]] = []
    overlay: list[dict[str, object]] = []

    groups = [
        ("label_errors", "label_error"),
        ("ambiguous", "ambiguous"),
        ("false_positive_audit_findings", "ambiguous"),
        ("keep_but_flag", None),
    ]

    for key, issue_type in groups:
        for entry in review[key]:
            row_id = entry["id"]
            row = evidence.loc[row_id]
            split = canonical.loc[row_id, "split"]
            decision = entry.get("decision", "keep_but_flag")

            memo.append(
                {
                    "id": row_id,
                    "split": split,
                    "public_label": row["label"],
                    "proposed_label": entry.get("proposed_label", row["label"]),
                    "decision": decision,
                    "confidence": entry["confidence"],
                    "signal_count": int(row["signal_count"]),
                    "opposition_strength": round(float(row["opposition_strength"]), 4),
                    "reason": entry["reason"],
                }
            )

            if issue_type is None:
                continue

            if decision == "should_fix":
                action = (
                    "flag_only_no_relabel"
                    if split == "heldout"
                    else "apply_training_label_overlay"
                )
            elif decision == "false_positive_audit_finding":
                action = "reject_audit_finding"
            else:
                action = "clarify_annotation_policy"

            first, second = evidence_tokens(row)
            suspicious.append(
                {
                    "id": row_id,
                    "split": split,
                    "issue_type": issue_type,
                    "rank": 0,
                    "confidence": entry["confidence"],
                    "evidence_1": first,
                    "evidence_2": second,
                    "recommended_action": action,
                    "short_explanation": entry["reason"],
                }
            )

            if decision == "should_fix" and split == "train":
                overlay.append(
                    {
                        "id": row_id,
                        "public_label": row["label"],
                        "overlay_label": entry["proposed_label"],
                        "confidence": entry["confidence"],
                        "reason": entry["reason"],
                    }
                )

    suspicious_frame = pd.DataFrame(suspicious)
    order = {"high": 0, "medium": 1, "low": 2}
    suspicious_frame = suspicious_frame.sort_values(
        ["issue_type", "confidence"], key=lambda col: col.map(order).fillna(col)
    ).reset_index(drop=True)
    suspicious_frame["rank"] = suspicious_frame.index + 1
    suspicious_frame = suspicious_frame[protocol["suspicious_examples_schema"]]

    suspicious_frame.to_csv(RESULTS_DIR / "suspicious_examples_b.csv", index=False)
    pd.DataFrame(memo).to_csv(RESULTS_DIR / "adjudication_memo_b.csv", index=False)
    pd.DataFrame(overlay).to_csv(RESULTS_DIR / "training_label_overlay.csv", index=False)

    overlay_splits = canonical.loc[[row["id"] for row in overlay], "split"]
    assert set(overlay_splits) == {"train"}, "held-out row reached the overlay"
    assert set(suspicious_frame["confidence"]) <= set(protocol["confidence_values"])
    assert set(suspicious_frame["issue_type"]) <= set(protocol["issue_types"])

    high = int((suspicious_frame["confidence"] == "high").sum())
    print(f"adjudicated rows      : {len(memo)}")
    print(f"suspicious rows (B)   : {len(suspicious_frame)}")
    print(f"  label_error         : {int((suspicious_frame['issue_type'] == 'label_error').sum())}")
    print(f"  ambiguous           : {int((suspicious_frame['issue_type'] == 'ambiguous').sum())}")
    print(f"  high                : {high} ({high / len(suspicious_frame):.1%})")
    print(f"training overlay rows : {len(overlay)}")
    print(f"rejected (keep_but_flag): {len(review['keep_but_flag'])}")


if __name__ == "__main__":
    main()
