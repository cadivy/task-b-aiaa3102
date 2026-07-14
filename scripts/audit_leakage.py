"""Adjudicate cross-split similarity and quantify leakage-aware evaluation."""

from __future__ import annotations

import pandas as pd

from common import RESULTS_DIR, classification_metrics, ensure_dirs, load_canonical


# Explicit false-positive traps found during text review. Pairs are sorted IDs.
REJECTED_PAIRS = {
    tuple(sorted(pair))
    for pair in [
        ("T1881", "H0850"),  # same frame but opposite semantic adjective
        ("T2085", "H0531"),  # generic short acknowledgement
        ("H0924", "T3761"),  # generic short acknowledgement
        ("H0136", "T4269"),  # shared gym phrase but different addressee/content
        ("T0233", "H0551"),  # generic thanks phrase
        ("T0233", "H0660"),  # generic thanks phrase
    ]
}

REJECTION_REASONS = {
    tuple(sorted(("T1881", "H0850"))): (
        "Rejected: word TF-IDF ignores the semantic reversal between "
        "'affectionate' and 'hostile'."
    ),
    tuple(sorted(("T2085", "H0531"))): (
        "Rejected as leakage: a very short generic acknowledgement can recur independently."
    ),
    tuple(sorted(("H0924", "T3761"))): (
        "Rejected as leakage: generic 'ok no prob' wording is not event-specific."
    ),
    tuple(sorted(("H0136", "T4269"))): (
        "Rejected as leakage: shared gym wording is insufficient to identify one source message."
    ),
    tuple(sorted(("T0233", "H0551"))): (
        "Rejected as leakage: generic thanks phrase lacks distinctive context."
    ),
    tuple(sorted(("T0233", "H0660"))): (
        "Rejected as leakage: generic thanks phrase lacks distinctive context."
    ),
}


def heldout_and_train(row: pd.Series) -> tuple[str, str]:
    if row["split_1"] == "heldout":
        return row["id_1"], row["id_2"]
    return row["id_2"], row["id_1"]


def main() -> None:
    ensure_dirs()
    canonical = load_canonical()
    predictions = pd.read_csv(RESULTS_DIR / "heldout_predictions.csv", keep_default_na=False)
    clusters = pd.read_csv(RESULTS_DIR / "exact_duplicate_clusters.csv", keep_default_na=False)
    members = pd.read_csv(RESULTS_DIR / "exact_duplicate_members.csv", keep_default_na=False)
    near = pd.read_csv(RESULTS_DIR / "cross_split_near_candidates.csv", keep_default_na=False)

    exact_cases = []
    exact_heldout_ids: set[str] = set()
    for _, cluster in clusters[clusters["is_cross_split"]].iterrows():
        cluster_members = members[members["cluster_id"] == cluster["cluster_id"]]
        train_ids = cluster_members.loc[cluster_members["split"] == "train", "id"].tolist()
        heldout_rows = cluster_members[cluster_members["split"] == "heldout"]
        for _, heldout_row in heldout_rows.iterrows():
            exact_heldout_ids.add(heldout_row["id"])
            exact_cases.append(
                {
                    "heldout_id": heldout_row["id"],
                    "train_id": train_ids[0],
                    "match_type": "exact",
                    "primary_similarity": 1.0,
                    "word_similarity": 1.0,
                    "char_similarity": 1.0,
                    "label": heldout_row["label"],
                    "cluster_id": cluster["cluster_id"],
                    "manual_decision": "accepted",
                    "manual_confidence": "high",
                    "manual_reason": "Identical after lowercasing and whitespace collapse.",
                }
            )

    adjudication_rows = []
    near_cases = []
    accepted_near_heldout_ids: set[str] = set()
    for _, row in near.iterrows():
        pair = tuple(sorted((row["id_1"], row["id_2"])))
        heldout_id, train_id = heldout_and_train(row)
        min_length = min(len(str(row["text_1"])), len(str(row["text_2"])))
        rejected = pair in REJECTED_PAIRS
        strong_template = (
            min_length >= 30
            and (
                float(row["char_similarity"]) >= 0.90
                or float(row["word_similarity"]) >= 0.95
            )
        )
        decision = "rejected_false_positive" if rejected else "accepted"
        confidence = "high" if (not rejected and strong_template) else "medium"
        if rejected:
            reason = REJECTION_REASONS[pair]
        elif strong_template:
            reason = (
                "Accepted: distinctive message template is preserved with only minor "
                "formatting, entity, number, or wording changes."
            )
        else:
            reason = (
                "Accepted with medium confidence: similarity meets the public threshold, "
                "but the message is short or less distinctive."
            )
        adjudication_rows.append(
            {
                **row.to_dict(),
                "heldout_id": heldout_id,
                "train_id": train_id,
                "manual_decision": decision,
                "manual_confidence": confidence,
                "manual_reason": reason,
            }
        )
        if not rejected:
            accepted_near_heldout_ids.add(heldout_id)
            near_cases.append(
                {
                    "heldout_id": heldout_id,
                    "train_id": train_id,
                    "match_type": "near",
                    "primary_similarity": row["primary_similarity"],
                    "word_similarity": row["word_similarity"],
                    "char_similarity": row["char_similarity"],
                    "label": row["label_1"] if row["id_1"] == heldout_id else row["label_2"],
                    "cluster_id": "",
                    "manual_decision": "accepted",
                    "manual_confidence": confidence,
                    "manual_reason": reason,
                }
            )

    adjudication = pd.DataFrame(adjudication_rows).sort_values(
        ["manual_decision", "primary_similarity"], ascending=[True, False]
    )
    adjudication.to_csv(RESULTS_DIR / "near_duplicate_adjudication.csv", index=False)
    leakage_cases = pd.DataFrame(exact_cases + near_cases).drop_duplicates(
        ["heldout_id", "train_id", "match_type"]
    )
    leakage_cases.to_csv(RESULTS_DIR / "leakage_cases.csv", index=False)

    metric_rows = []
    conditions = {
        "original_heldout": set(),
        "exclude_exact_leakage": exact_heldout_ids,
        "exclude_exact_and_near_leakage": exact_heldout_ids | accepted_near_heldout_ids,
    }
    for condition, excluded_ids in conditions.items():
        subset = predictions[~predictions["id"].isin(excluded_ids)]
        metrics = classification_metrics(subset["label"], subset["word_pred"])
        metrics.update(
            {
                "condition": condition,
                "excluded_rows": len(predictions) - len(subset),
                "excluded_spam": int(
                    predictions[
                        predictions["id"].isin(excluded_ids)
                        & (predictions["label"] == "spam")
                    ].shape[0]
                ),
            }
        )
        metric_rows.append(metrics)
    pd.DataFrame(metric_rows).to_csv(RESULTS_DIR / "leakage_metrics.csv", index=False)

    print(f"Accepted exact held-out leakage rows: {len(exact_heldout_ids)}")
    print(f"Accepted near held-out leakage rows: {len(accepted_near_heldout_ids)}")
    print(f"Rejected cross-split near candidates: {int((adjudication['manual_decision'] != 'accepted').sum())}")
    print(
        pd.DataFrame(metric_rows)[
            ["condition", "n", "excluded_rows", "accuracy", "spam_recall", "spam_f1", "macro_f1"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
