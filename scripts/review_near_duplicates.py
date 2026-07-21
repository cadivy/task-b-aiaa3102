"""Reproduce the manual near-duplicate adjudication pass.

The candidate queue is created by scripts/audit_duplicates.py. This script reads
the fixed manual re-review from a stable pair_key ledger, merges it into the
queue, and emits pair-level and sample-level duplicate evidence. It does not
infer review decisions from text heuristics or bind decisions to unstable pair_id
values.
"""

from __future__ import annotations

from collections import Counter
import json

import pandas as pd

from common import RESULTS_DIR, ROOT, ensure_dirs, load_canonical, write_json

REVIEWER = "Codex-assisted manual review"
REVIEW_VERSION = "near-duplicate-review-v1.4-stable-pair-key-ledger"
REVIEW_POLICY_VERSION = "near-duplicate-review-policy-v1.0"
DUPLICATE_RESULTS_DIR = RESULTS_DIR / "duplicate"
QUEUE_PATH = DUPLICATE_RESULTS_DIR / "near_duplicate_review_queue.csv"
DECISIONS_PATH = DUPLICATE_RESULTS_DIR / "near_duplicate_manual_review_decisions.csv"
REVIEWED_QUEUE_PATH = DUPLICATE_RESULTS_DIR / "near_duplicate_review_queue_reviewed.csv"
SUMMARY_CSV_PATH = DUPLICATE_RESULTS_DIR / "near_duplicate_review_summary.csv"
SUMMARY_JSON_PATH = DUPLICATE_RESULTS_DIR / "near_duplicate_review_summary.json"
SAMPLE_SUMMARY_PATH = DUPLICATE_RESULTS_DIR / "reviewed_duplicate_samples.csv"
DUPLICATE_SUMMARY_PATH = DUPLICATE_RESULTS_DIR / "duplicate_summary.json"
REPORT_PATH = ROOT / "duplicates.md"

REVIEW_COLUMNS = [
    "review_decision",
    "review_category",
    "reviewer",
    "review_notes",
    "recommended_action",
    "confidence",
]

def stable_pair_key(id_a: object, id_b: object) -> str:
    return "|".join(sorted([str(id_a), str(id_b)]))


def load_manual_decisions(queue: pd.DataFrame) -> pd.DataFrame:
    if not DECISIONS_PATH.exists():
        raise FileNotFoundError(f"Manual review ledger not found: {DECISIONS_PATH}")
    decisions = pd.read_csv(DECISIONS_PATH, keep_default_na=False)
    if "pair_key" not in decisions.columns:
        if {"id_a", "id_b"}.issubset(decisions.columns):
            decisions["pair_key"] = decisions.apply(lambda row: stable_pair_key(row["id_a"], row["id_b"]), axis=1)
        else:
            raise ValueError("Manual review ledger must contain pair_key or id_a/id_b columns")
    duplicated = decisions[decisions["pair_key"].duplicated()]["pair_key"].tolist()
    if duplicated:
        raise ValueError(f"Manual review ledger has duplicate pair_key values: {duplicated[:10]}")
    required = ["pair_key", *REVIEW_COLUMNS]
    missing_columns = [column for column in required if column not in decisions.columns]
    if missing_columns:
        raise ValueError(f"Manual review ledger is missing columns: {missing_columns}")
    queue_keys = set(queue["pair_key"])
    extra_keys = sorted(set(decisions["pair_key"]) - queue_keys)
    if extra_keys:
        print(f"Ignoring {len(extra_keys)} manual decision(s) not present in the current queue")
    return decisions[required].copy()


def adjudicate(queue: pd.DataFrame, decisions: pd.DataFrame) -> pd.DataFrame:
    stale_review_columns = [column for column in REVIEW_COLUMNS if column in queue.columns]
    base = queue.drop(columns=stale_review_columns)
    reviewed = base.merge(decisions, on="pair_key", how="left", validate="one_to_one")
    missing = reviewed["review_decision"].eq("") | reviewed["review_decision"].isna()
    reviewed.loc[missing, "review_decision"] = "needs_review"
    reviewed.loc[missing, "review_category"] = "pending_manual_review"
    reviewed.loc[missing, "reviewer"] = ""
    reviewed.loc[missing, "review_notes"] = "No stable-key manual decision exists for this newly surfaced candidate."
    reviewed.loc[missing, "recommended_action"] = "review_before_use"
    reviewed.loc[missing, "confidence"] = "low"
    reviewed["reviewer"] = reviewed["reviewer"].replace("", REVIEWER)
    reviewed["review_version"] = REVIEW_VERSION
    return reviewed


def heldout_ids(frame: pd.DataFrame) -> list[str]:
    if frame.empty:
        return []
    values = pd.concat(
        [
            frame.loc[frame["split_a"] == "heldout", "id_a"],
            frame.loc[frame["split_b"] == "heldout", "id_b"],
        ],
        ignore_index=True,
    )
    return sorted(value for value in pd.unique(values) if value)


def summarize(reviewed: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    decision_counts = Counter(reviewed["review_decision"])
    category_counts = Counter(reviewed["review_category"])
    split_pair_counts = Counter(reviewed["split_a"] + "-" + reviewed["split_b"])
    accepted = reviewed[reviewed["review_decision"] == "accepted"]
    rejected = reviewed[reviewed["review_decision"] == "rejected_false_positive"]
    accepted_cross = accepted[accepted["cross_split"].astype(bool)]
    rejected_cross = rejected[rejected["cross_split"].astype(bool)]
    accepted_train_train = accepted[
        (accepted["split_a"] == "train") & (accepted["split_b"] == "train")
    ]

    summary_rows = []
    for decision, count in sorted(decision_counts.items()):
        subset = reviewed[reviewed["review_decision"] == decision]
        summary_rows.append(
            {
                "review_decision": decision,
                "pairs": int(count),
                "cross_split_pairs": int(subset["cross_split"].astype(bool).sum()),
                "train_train_pairs": int(((subset["split_a"] == "train") & (subset["split_b"] == "train")).sum()),
                "unique_heldout_ids": int(len(heldout_ids(subset))),
                "spam_pairs": int(((subset["label_a"] == "spam") & (subset["label_b"] == "spam")).sum()),
                "ham_pairs": int(((subset["label_a"] == "ham") & (subset["label_b"] == "ham")).sum()),
            }
        )

    payload = {
        "source_script": "scripts/review_near_duplicates.py",
        "review_version": REVIEW_VERSION,
        "review_policy_version": REVIEW_POLICY_VERSION,
        "review_policy_summary": [
            "Exact duplicates are retained whenever the normalized strings are identical, even if the text is a common short reply.",
            "Near duplicates are accepted only when manual review finds evidence of the same message, template, spam campaign, forwarded content, embedded content, or specific personalized variant.",
            "Near-duplicate candidates that only share generic short conversational wording are rejected unless they contain a specific content anchor beyond the common phrase.",
            "Lexically similar pairs with material semantic changes are rejected as false positives.",
        ],
        "input": str(QUEUE_PATH.relative_to(ROOT)),
        "manual_review_ledger": str(DECISIONS_PATH.relative_to(ROOT)),
        "reviewed_queue": str(QUEUE_PATH.relative_to(ROOT)),
        "reviewed_rows": int(len(reviewed)),
        "accepted_pairs": int(decision_counts.get("accepted", 0)),
        "rejected_false_positive_pairs": int(decision_counts.get("rejected_false_positive", 0)),
        "remaining_needs_review_pairs": int(decision_counts.get("needs_review", 0)),
        "accepted_cross_split_pairs": int(len(accepted_cross)),
        "rejected_cross_split_false_positive_pairs": int(len(rejected_cross)),
        "accepted_train_train_pairs": int(len(accepted_train_train)),
        "accepted_unique_heldout_ids": int(len(heldout_ids(accepted_cross))),
        "decision_counts": dict(decision_counts),
        "category_counts": dict(category_counts),
        "split_pair_counts": dict(split_pair_counts),
    }
    return pd.DataFrame(summary_rows), payload


def add_partner(entry: dict[str, object], partner_id: str, cross_split: bool) -> None:
    entry["partner_ids"].add(partner_id)
    if cross_split:
        entry["cross_split_partner_ids"].add(partner_id)


def sample_entry(row: pd.Series) -> dict[str, object]:
    return {
        "sample_id": row["id"],
        "split": row["split"],
        "label": row["label"],
        "uci_row_number": int(row["uci_row_number"]),
        "text": row["text"],
        "exact_cluster_ids": set(),
        "near_pair_ids": set(),
        "review_categories": set(),
        "partner_ids": set(),
        "cross_split_partner_ids": set(),
        "exact_partner_ids": set(),
        "near_partner_ids": set(),
        "cross_split_exact_partner_ids": set(),
        "cross_split_near_pair_ids": set(),
        "max_near_similarity": None,
    }


def build_reviewed_duplicate_samples(reviewed: pd.DataFrame) -> pd.DataFrame:
    canonical = load_canonical().set_index("id", drop=False)
    entries: dict[str, dict[str, object]] = {}

    exact_members_path = DUPLICATE_RESULTS_DIR / "exact_duplicate_members.csv"
    exact_clusters_path = DUPLICATE_RESULTS_DIR / "exact_duplicate_clusters.csv"
    if exact_members_path.exists() and exact_clusters_path.exists():
        members = pd.read_csv(exact_members_path, keep_default_na=False)
        clusters = pd.read_csv(exact_clusters_path, keep_default_na=False)
        cross_by_cluster = dict(zip(clusters["cluster_id"], clusters["cross_split"].astype(bool)))
        for cluster_id, group in members.groupby("cluster_id", sort=False):
            cross_split = bool(cross_by_cluster.get(cluster_id, False))
            ids = group["id"].tolist()
            for sample_id in ids:
                if sample_id not in entries:
                    entries[sample_id] = sample_entry(canonical.loc[sample_id])
                entry = entries[sample_id]
                entry["exact_cluster_ids"].add(cluster_id)
                for partner_id in ids:
                    if partner_id == sample_id:
                        continue
                    entry["exact_partner_ids"].add(partner_id)
                    add_partner(entry, partner_id, cross_split)
                    if cross_split and canonical.loc[partner_id, "split"] != canonical.loc[sample_id, "split"]:
                        entry["cross_split_exact_partner_ids"].add(partner_id)

    accepted = reviewed[reviewed["review_decision"] == "accepted"]
    for _, pair in accepted.iterrows():
        pair_id = pair["pair_id"]
        id_a = pair["id_a"]
        id_b = pair["id_b"]
        cross_split = bool(pair["cross_split"])
        for sample_id, partner_id in ((id_a, id_b), (id_b, id_a)):
            if sample_id not in entries:
                entries[sample_id] = sample_entry(canonical.loc[sample_id])
            entry = entries[sample_id]
            entry["near_pair_ids"].add(pair_id)
            entry["review_categories"].add(pair["review_category"])
            entry["near_partner_ids"].add(partner_id)
            add_partner(entry, partner_id, cross_split)
            if cross_split:
                entry["cross_split_near_pair_ids"].add(pair_id)
            current = entry["max_near_similarity"]
            similarity = float(pair["max_cosine"])
            if current is None or similarity > current:
                entry["max_near_similarity"] = similarity

    rows = []
    for sample_id, entry in entries.items():
        has_exact = bool(entry["exact_cluster_ids"])
        has_near = bool(entry["near_pair_ids"])
        if has_exact and has_near:
            duplicate_type = "exact_and_near_reviewed_accepted"
        elif has_exact:
            duplicate_type = "exact"
        else:
            duplicate_type = "near_reviewed_accepted"
        cross_split_duplicate = bool(entry["cross_split_exact_partner_ids"] or entry["cross_split_near_pair_ids"])
        rows.append(
            {
                "sample_id": sample_id,
                "split": entry["split"],
                "label": entry["label"],
                "uci_row_number": entry["uci_row_number"],
                "duplicate_type": duplicate_type,
                "cross_split_duplicate": cross_split_duplicate,
                "exact_cluster_ids": "|".join(sorted(entry["exact_cluster_ids"])),
                "near_pair_ids": "|".join(sorted(entry["near_pair_ids"])),
                "n_exact_duplicate_clusters": len(entry["exact_cluster_ids"]),
                "n_exact_duplicate_partner_samples": len(entry["exact_partner_ids"]),
                "n_near_reviewed_accepted_pairs": len(entry["near_pair_ids"]),
                "n_cross_split_exact_partner_samples": len(entry["cross_split_exact_partner_ids"]),
                "n_cross_split_near_reviewed_accepted_pairs": len(entry["cross_split_near_pair_ids"]),
                "partner_ids": "|".join(sorted(entry["partner_ids"])),
                "cross_split_partner_ids": "|".join(sorted(entry["cross_split_partner_ids"])),
                "review_categories": "|".join(sorted(entry["review_categories"])),
                "max_near_similarity": "" if entry["max_near_similarity"] is None else entry["max_near_similarity"],
                "text": entry["text"],
            }
        )
    return pd.DataFrame(rows).sort_values(["cross_split_duplicate", "split", "sample_id"], ascending=[False, True, True])


def update_duplicate_summary(summary: dict[str, object], sample_summary: pd.DataFrame) -> None:
    if not DUPLICATE_SUMMARY_PATH.exists():
        return
    payload = json.loads(DUPLICATE_SUMMARY_PATH.read_text(encoding="utf-8"))
    payload.update(
        {
            "near_duplicate_review_status": "completed",
            "near_duplicate_review_version": REVIEW_VERSION,
            "reviewed_near_duplicate_pairs": summary["reviewed_rows"],
            "accepted_near_duplicate_pairs": summary["accepted_pairs"],
            "rejected_near_false_positive_pairs": summary["rejected_false_positive_pairs"],
            "accepted_cross_split_near_duplicate_pairs": summary["accepted_cross_split_pairs"],
            "rejected_cross_split_near_false_positive_pairs": summary["rejected_cross_split_false_positive_pairs"],
            "remaining_near_duplicate_pairs_needing_review": summary["remaining_needs_review_pairs"],
            "accepted_unique_heldout_ids_in_cross_split_near_duplicates": summary["accepted_unique_heldout_ids"],
            "reviewed_duplicate_samples": int(len(sample_summary)),
            "reviewed_cross_split_duplicate_samples": int(sample_summary["cross_split_duplicate"].astype(bool).sum()),
            "reviewed_near_duplicate_samples": int((sample_summary["n_near_reviewed_accepted_pairs"] > 0).sum()),
            "reviewed_exact_duplicate_samples": int((sample_summary["n_exact_duplicate_clusters"] > 0).sum()),
        }
    )
    write_json(DUPLICATE_SUMMARY_PATH, payload)


def append_report_section(summary: dict[str, object], sample_summary: pd.DataFrame) -> None:
    if not REPORT_PATH.exists():
        return
    report = REPORT_PATH.read_text(encoding="utf-8")
    for marker in ("## Near-Duplicate Review Results", "## Scripts And Outputs"):
        if marker in report:
            report = report.split(marker)[0].rstrip() + "\n\n"

    section = f"""## Near-Duplicate Review Results

The review queue has been adjudicated from the stable manual decision ledger `results/duplicate/near_duplicate_manual_review_decisions.csv` using `{REVIEW_VERSION}` and `{REVIEW_POLICY_VERSION}`. The ledger is keyed by `pair_key = sorted(id_a, id_b)`, so manual judgments attach to the underlying sample pair rather than to a display-only `pair_id` that can change when candidates are regenerated. The script merges the ledger into `{summary['reviewed_queue']}`; it does not classify pairs with text heuristics. Punctuation-only variants remain near duplicates rather than exact duplicates because the exact-duplicate rule intentionally keeps punctuation.

### Review Policy

The review policy separates objective string repetition from inferred near-duplicate evidence. Exact duplicates are retained whenever the normalized strings are identical, even if the text is a common short reply such as `Sorry, I'll call later`; exact matching is a direct dataset fact. Near duplicates require a higher evidentiary bar because similar wording may come from ordinary language use rather than repeated data.

Near-duplicate pairs are accepted when they appear to be the same substantive SMS, the same spam campaign/template, the same forwarded or template-style ham message, an embedded/transcript variant, or a specific personalized variant with only names, addressees, punctuation, casing, spacing, entities, numbers, URLs, dates, or minor wording changed. They are rejected as false positives when the similarity is only a generic short conversational phrase or acknowledgement without a specific content anchor, or when lexically similar texts have a material semantic change.

This means a common phrase can count as a duplicate when it is exactly repeated, but a non-exact variant of that phrase is not automatically accepted as a near duplicate. For near duplicates, the review asks whether the pair is likely the same source message/template/content, not merely whether the two texts are semantically close.

| Review decision | Pair count |
|---|---|
| accepted | {summary['accepted_pairs']} |
| rejected_false_positive | {summary['rejected_false_positive_pairs']} |
| needs_review | {summary['remaining_needs_review_pairs']} |

The expanded queue includes train-train and cross-split candidates, excluding heldout-heldout pairs. Accepted cross-split near duplicates total {summary['accepted_cross_split_pairs']} pairs and affect {summary['accepted_unique_heldout_ids']} unique held-out messages. The reviewed sample-level table contains {len(sample_summary)} samples involved in either exact duplicates or accepted near duplicates, including {int(sample_summary['cross_split_duplicate'].astype(bool).sum())} samples with cross-split duplicate evidence.

## Scripts And Outputs

| Path | Function / content |
|---|---|
| `scripts/audit_duplicates.py` | Deterministically rebuilds exact duplicate clusters, all near-duplicate candidates, threshold sensitivity, the review queue, and this report. It keeps cross-split status as columns rather than writing a separate cross-split near-candidate file. |
| `scripts/review_near_duplicates.py` | Reproduces the Codex-assisted manual re-review by reading `near_duplicate_manual_review_decisions.csv` as stable `pair_key` data, merges decisions into `near_duplicate_review_queue.csv` or `near_duplicate_review_queue_reviewed.csv` if the original file is locked, then writes pair-level and sample-level summaries. |
| `results/duplicate/exact_duplicate_clusters.csv` | One row per exact duplicate cluster after lowercase plus whitespace normalization; includes cluster size, split mix, labels, representative text, and member IDs. |
| `results/duplicate/exact_duplicate_members.csv` | One row per member of each exact duplicate cluster; useful when you need the original row ID, split, label, text, and normalized text. |
| `results/duplicate/near_duplicate_candidates.csv` | All non-exact candidate pairs found above the search floor 0.88, with word/character cosine scores, cross-split status, and a flag for the protocol threshold 0.92. |
| `results/duplicate/near_duplicate_threshold_sensitivity.csv` | Counts at thresholds 0.88, 0.90, 0.92, 0.94, and 0.96; used to justify why 0.92 is a balanced review threshold. |
| `results/duplicate/near_duplicate_review_queue.csv` | The review queue input: all protocol-threshold candidates except heldout-heldout pairs, including train-train and cross-split pairs. If writable, the review script overwrites this with adjudicated fields. |
| `results/duplicate/near_duplicate_review_queue_reviewed.csv` | The adjudicated review queue copy written when `near_duplicate_review_queue.csv` is locked by another program. |
| `results/duplicate/near_duplicate_manual_review_decisions.csv` | Fixed manual decision ledger keyed by stable `pair_key`; this is the source used to reproduce review decisions without script heuristics or unstable pair numbering. |
| `results/duplicate/near_duplicate_review_summary.csv` | Compact decision-level counts split by decision, cross-split/train-train status, label type, and affected heldout IDs. |
| `results/duplicate/near_duplicate_review_summary.json` | Machine-readable review summary with aggregate counts only; pair ID lists are intentionally omitted. |
| `results/duplicate/reviewed_duplicate_samples.csv` | One row per sample involved in exact duplicates or accepted near duplicates; includes duplicate type, cross-split status, partner IDs, counts, categories, and text. |
| `results/duplicate/duplicate_summary.json` | Machine-readable headline duplicate metrics, including exact duplicate counts, near candidate counts, review queue size, excluded heldout-heldout count, completed review totals, and reviewed sample counts. |
| `results/figures/exact_cluster_sizes.png` | Bar chart of exact duplicate cluster sizes; kept in the shared figures folder because images were not moved into `results/duplicate/`. |
"""
    REPORT_PATH.write_text(report.rstrip() + "\n\n" + section, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    if not QUEUE_PATH.exists():
        raise FileNotFoundError(f"Review queue not found: {QUEUE_PATH}")
    queue = pd.read_csv(QUEUE_PATH, keep_default_na=False)
    if "pair_key" not in queue.columns:
        queue["pair_key"] = queue.apply(lambda row: stable_pair_key(row["id_a"], row["id_b"]), axis=1)
    decisions = load_manual_decisions(queue)
    reviewed = adjudicate(queue, decisions)
    summary_table, summary_json = summarize(reviewed)
    sample_summary = build_reviewed_duplicate_samples(reviewed)

    try:
        reviewed.to_csv(QUEUE_PATH, index=False, lineterminator="\n")
        output_queue = QUEUE_PATH
    except PermissionError:
        output_queue = REVIEWED_QUEUE_PATH
        reviewed.to_csv(output_queue, index=False, lineterminator="\n")
        summary_json["reviewed_queue"] = str(output_queue.relative_to(ROOT))
        summary_json["write_warning"] = "Original review queue was locked; wrote reviewed copy instead."
    summary_table.to_csv(SUMMARY_CSV_PATH, index=False, lineterminator="\n")
    sample_summary.to_csv(SAMPLE_SUMMARY_PATH, index=False, lineterminator="\n")
    write_json(SUMMARY_JSON_PATH, summary_json)
    update_duplicate_summary(summary_json, sample_summary)
    append_report_section(summary_json, sample_summary)

    print(f"Reviewed rows: {summary_json['reviewed_rows']}")
    print(f"Reviewed queue: {output_queue}")
    print(f"Accepted pairs: {summary_json['accepted_pairs']}")
    print(f"Accepted cross-split pairs: {summary_json['accepted_cross_split_pairs']}")
    print(f"Rejected false positives: {summary_json['rejected_false_positive_pairs']}")
    print(f"Remaining needs_review: {summary_json['remaining_needs_review_pairs']}")
    print(f"Reviewed duplicate samples: {len(sample_summary)}")
    print(f"Accepted unique held-out IDs: {summary_json['accepted_unique_heldout_ids']}")


if __name__ == "__main__":
    main()
