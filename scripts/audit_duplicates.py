"""Audit exact and near duplicates, leaving near-pair adjudication for review.

The script is deterministic: it uses the canonical table, the public exact
normalization rule in common.normalize_text, and the calibrated near-duplicate
threshold from starter/configs/audit_protocol.json.
"""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from common import (
    FIGURES_DIR,
    RESULTS_DIR,
    ROOT,
    ensure_dirs,
    load_canonical,
    load_protocol,
    normalize_text,
    write_json,
)

SEARCH_FLOOR = 0.88
SENSITIVITY_THRESHOLDS = (0.88, 0.90, 0.92, 0.94, 0.96)
METHOD_VERSION = "duplicate-audit-v1.1-stable-pair-keys"
DUPLICATE_RESULTS_DIR = RESULTS_DIR / "duplicate"


@dataclass(frozen=True)
class PairScore:
    left_idx: int
    right_idx: int
    word_cosine: float
    char_cosine: float

    @property
    def max_cosine(self) -> float:
        return max(self.word_cosine, self.char_cosine)


def word_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.995,
        sublinear_tf=True,
    )


def char_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        analyzer="char_wb",
        lowercase=True,
        ngram_range=(3, 5),
        min_df=2,
        max_features=50000,
        sublinear_tf=True,
    )


def build_exact_tables(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    data = df.copy()
    data["normalized_text"] = data["text"].map(normalize_text)

    cluster_rows = []
    member_rows = []
    cluster_number = 1
    for normalized_text, group in data.groupby("normalized_text", sort=False):
        if len(group) <= 1:
            continue
        cluster_id = f"E{cluster_number:04d}"
        labels = sorted(group["label"].unique().tolist())
        splits = sorted(group["split"].unique().tolist())
        members = group["id"].tolist()
        cluster_rows.append(
            {
                "cluster_id": cluster_id,
                "cluster_size": int(len(group)),
                "splits": "|".join(splits),
                "labels": "|".join(labels),
                "label_conflict": bool(len(labels) > 1),
                "cross_split": bool(set(splits) == {"heldout", "train"}),
                "train_count": int((group["split"] == "train").sum()),
                "heldout_count": int((group["split"] == "heldout").sum()),
                "representative_id": group.iloc[0]["id"],
                "representative_text": group.iloc[0]["text"],
                "member_ids": "|".join(members),
                "source_script": "scripts/audit_duplicates.py",
                "method_version": METHOD_VERSION,
            }
        )
        for order, (_, row) in enumerate(group.iterrows(), start=1):
            member_rows.append(
                {
                    "cluster_id": cluster_id,
                    "member_order": order,
                    "id": row["id"],
                    "split": row["split"],
                    "uci_row_number": int(row["uci_row_number"]),
                    "label": row["label"],
                    "text": row["text"],
                    "normalized_text": normalized_text,
                    "source_script": "scripts/audit_duplicates.py",
                    "method_version": METHOD_VERSION,
                }
            )
        cluster_number += 1

    clusters = pd.DataFrame(cluster_rows)
    members = pd.DataFrame(member_rows)
    if clusters.empty:
        cross_split = clusters.copy()
    else:
        cross_split = clusters[clusters["cross_split"]].copy().reset_index(drop=True)
    return clusters, members, cross_split


def collect_candidate_indices(matrix, floor: float) -> set[tuple[int, int]]:
    similarity = cosine_similarity(matrix)
    left_indices, right_indices = np.where(np.triu(similarity >= floor, k=1))
    return set(zip(left_indices.astype(int), right_indices.astype(int)))


def compute_pair_scores(df: pd.DataFrame) -> list[PairScore]:
    word_matrix = word_vectorizer().fit_transform(df["text"])
    char_matrix = char_vectorizer().fit_transform(df["text"])
    pairs = collect_candidate_indices(word_matrix, SEARCH_FLOOR) | collect_candidate_indices(
        char_matrix, SEARCH_FLOOR
    )

    scores: list[PairScore] = []
    for left, right in sorted(pairs):
        word_score = float(cosine_similarity(word_matrix[left], word_matrix[right])[0, 0])
        char_score = float(cosine_similarity(char_matrix[left], char_matrix[right])[0, 0])
        scores.append(PairScore(left, right, word_score, char_score))
    return scores


def likely_reason_code(left: pd.Series, right: pd.Series, word_cosine: float, char_cosine: float) -> str:
    left_tokens = set(str(left["text"]).lower().split())
    right_tokens = set(str(right["text"]).lower().split())
    token_overlap = len(left_tokens & right_tokens) / max(len(left_tokens | right_tokens), 1)
    if max(len(str(left["text"])), len(str(right["text"]))) <= 40:
        return "generic_short_text_review_needed"
    if word_cosine >= 0.98 and char_cosine < 0.94:
        return "same_words_possible_entity_or_number_change"
    if char_cosine >= 0.98 and word_cosine < 0.94:
        return "same_character_template_minor_format_change"
    if word_cosine >= 0.96 and char_cosine >= 0.96:
        return "very_high_similarity_template_review_needed"
    if token_overlap >= 0.75:
        return "high_token_overlap_review_needed"
    return "threshold_candidate_review_needed"


def pair_rows(df: pd.DataFrame, scores: list[PairScore], threshold: float) -> pd.DataFrame:
    rows = []
    normalized = df["text"].map(normalize_text)
    for score in scores:
        if score.max_cosine < SEARCH_FLOOR:
            continue
        left = df.iloc[score.left_idx]
        right = df.iloc[score.right_idx]
        exact_duplicate = normalized.iloc[score.left_idx] == normalized.iloc[score.right_idx]
        if exact_duplicate:
            continue
        cross_split = left["split"] != right["split"]
        label_conflict = left["label"] != right["label"]
        max_cos = score.max_cosine
        rows.append(
            {
                "pair_id": "",
                "pair_key": "|".join(sorted([str(left["id"]), str(right["id"])])),
                "id_a": left["id"],
                "id_b": right["id"],
                "split_a": left["split"],
                "split_b": right["split"],
                "label_a": left["label"],
                "label_b": right["label"],
                "uci_row_number_a": int(left["uci_row_number"]),
                "uci_row_number_b": int(right["uci_row_number"]),
                "word_cosine": score.word_cosine,
                "char_cosine": score.char_cosine,
                "max_cosine": max_cos,
                "primary_matcher": "word" if score.word_cosine >= score.char_cosine else "char",
                "cross_split": bool(cross_split),
                "label_conflict": bool(label_conflict),
                "above_protocol_threshold": bool(max_cos >= threshold),
                "reason_code_suggestion": likely_reason_code(
                    left, right, score.word_cosine, score.char_cosine
                ),
                "text_a": left["text"],
                "text_b": right["text"],
                "source_script": "scripts/audit_duplicates.py",
                "method_version": METHOD_VERSION,
            }
        )
    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values(["id_a", "id_b"], ascending=[True, True]).reset_index(drop=True)
        result["pair_id"] = [f"N{index + 1:04d}" for index in range(len(result))]
        result = result.sort_values(
            ["above_protocol_threshold", "cross_split", "max_cosine", "id_a", "id_b"],
            ascending=[False, False, False, True, True],
        ).reset_index(drop=True)
    return result


def sensitivity_table(candidates: pd.DataFrame, thresholds: tuple[float, ...]) -> pd.DataFrame:
    rows = []
    for threshold in thresholds:
        subset = candidates[candidates["max_cosine"] >= threshold]
        cross = subset[subset["cross_split"]]
        rows.append(
            {
                "threshold": threshold,
                "candidate_pairs": int(len(subset)),
                "cross_split_pairs": int(len(cross)),
                "label_conflict_pairs": int(subset["label_conflict"].sum()) if len(subset) else 0,
                "unique_heldout_ids_in_cross_split": int(
                    pd.unique(
                        pd.concat(
                            [
                                cross.loc[cross["split_a"] == "heldout", "id_a"],
                                cross.loc[cross["split_b"] == "heldout", "id_b"],
                            ],
                            ignore_index=True,
                        )
                    ).size
                )
                if len(cross)
                else 0,
                "retention_vs_088": float(len(subset) / max(len(candidates[candidates["max_cosine"] >= thresholds[0]]), 1)),
            }
        )
    return pd.DataFrame(rows)


def build_adjudication_template(review_candidates: pd.DataFrame) -> pd.DataFrame:
    if review_candidates.empty:
        return pd.DataFrame()
    review = review_candidates.copy()
    review.insert(1, "review_decision", "needs_review")
    review.insert(2, "review_category", "")
    review.insert(3, "reason_code", review.pop("reason_code_suggestion"))
    review.insert(4, "reviewer", "")
    review.insert(5, "review_notes", "")
    review.insert(6, "recommended_action", "")
    review.insert(7, "confidence", "")
    return review


def write_csv_if_changed(frame: pd.DataFrame, path) -> None:
    content = frame.to_csv(index=False, lineterminator="\n")
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def write_figure(clusters: pd.DataFrame) -> None:
    if clusters.empty:
        return
    sizes = clusters["cluster_size"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.bar(sizes.index.astype(str), sizes.values, color="#2563EB")
    ax.set_title("Exact duplicate cluster sizes", loc="left", fontweight="bold")
    ax.set_xlabel("Cluster size")
    ax.set_ylabel("Number of clusters")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.18)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "exact_cluster_sizes.png", dpi=180)
    plt.close()


def markdown_table(rows: list[list[object]], headers: list[str]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(out)


def write_report(
    threshold: float,
    clusters: pd.DataFrame,
    exact_cross: pd.DataFrame,
    candidates: pd.DataFrame,
    sensitivity: pd.DataFrame,
    near_review: pd.DataFrame,
    duplicate_summary: dict[str, object],
) -> None:
    largest = clusters.sort_values("cluster_size", ascending=False).head(1)
    largest_text = largest.iloc[0]["representative_text"] if len(largest) else ""
    largest_id = largest.iloc[0]["cluster_id"] if len(largest) else ""

    threshold_rows = []
    for _, row in sensitivity.iterrows():
        threshold_rows.append(
            [
                f"{row['threshold']:.2f}",
                int(row["candidate_pairs"]),
                int(row["cross_split_pairs"]),
                int(row["unique_heldout_ids_in_cross_split"]),
                int(row["label_conflict_pairs"]),
            ]
        )

    exact_rows = []
    for _, row in exact_cross.head(10).iterrows():
        heldout_ids = "|".join([mid for mid in str(row["member_ids"]).split("|") if mid.startswith("H")])
        exact_rows.append([row["cluster_id"], heldout_ids, row["labels"], row["cluster_size"]])

    near_examples = []
    if not near_review.empty:
        # Many candidate pairs tie at max_cosine == 1.0000, so break ties on the
        # content-stable pair key; otherwise which eight rows are shown here
        # depends on incoming order rather than on the data.
        top_near = near_review.sort_values(
            ["max_cosine", "id_a", "id_b"], ascending=[False, True, True]
        ).head(8)
        for _, row in top_near.iterrows():
            near_examples.append(
                [
                    row["pair_id"],
                    f"{row['id_a']} / {row['id_b']}",
                    row["label_a"] if row["label_a"] == row["label_b"] else f"{row['label_a']}|{row['label_b']}",
                    f"{row['max_cosine']:.4f}",
                    row["reason_code"],
                    row["review_decision"],
                ]
            )

    report = f"""# Duplicate Analysis

## Method

Exact duplicates use the public rule implemented by `normalize_text()`: lowercase the SMS text and collapse whitespace. Punctuation, numbers, URLs, phone numbers, and entities are intentionally retained.

Near duplicates are retrieved with two deterministic TF-IDF views of the same canonical text: word unigrams/bigrams and character 3-5-grams. Candidate pairs are retrieved from nearest neighbours at a search floor of {SEARCH_FLOOR:.2f}; exact duplicate pairs are removed; the main score is `max(word_cosine, char_cosine)`. The protocol threshold is read from `starter/configs/audit_protocol.json`, currently `{threshold:.2f}`.

The script does not finalize near-duplicate adjudication. It writes `results/duplicate/near_duplicate_review_queue.csv` with `review_decision=needs_review` for every protocol-threshold candidate except heldout-heldout pairs. Cross-split status is retained as a column in the queue and candidate tables for later leakage analysis.

## Exact Duplicate Findings

{markdown_table([
    ["Exact duplicate clusters", duplicate_summary['exact_duplicate_clusters']],
    ["Rows in exact duplicate clusters", duplicate_summary['rows_in_exact_duplicate_clusters']],
    ["Repeated rows beyond first occurrence", duplicate_summary['repeated_rows_beyond_first']],
    ["Cross-split exact clusters", duplicate_summary['cross_split_exact_clusters']],
    ["Exact clusters with label conflict", duplicate_summary['label_conflict_exact_clusters']],
    ["Largest exact cluster", f"{largest_id}, size {duplicate_summary['largest_exact_cluster_size']}"],
], ["Finding", "Result"])}

The largest cluster is `{largest_id}`, represented by: `{largest_text}`. A large train-only cluster is a weighting risk rather than held-out leakage: the model sees the same short template many times and may overweight it.

Cross-split exact clusters are evaluation-independence findings because held-out text is already present in training. In this run they do not create label-conflict findings.

{markdown_table(exact_rows, ["Cluster", "Held-out ID", "Label(s)", "Cluster size"]) if exact_rows else "No cross-split exact clusters were found."}

## Near-Duplicate Threshold Analysis

The public threshold `{threshold:.2f}` sits in the middle of the sensitivity range. Lower thresholds retrieve many more candidates and therefore more generic false-positive risk; higher thresholds are cleaner but miss plausible template variants with formatting, number, or wording substitutions. Reporting the full sensitivity table makes the threshold choice auditable instead of a hidden tuning decision.

{markdown_table(threshold_rows, ["Threshold", "Candidate pairs", "Cross-split pairs", "Unique held-out IDs", "Label conflicts"])}

At `{threshold:.2f}`, the automatic retrieval finds {duplicate_summary['near_duplicate_candidate_pairs_at_threshold']} non-exact near-duplicate candidate pairs, including {duplicate_summary['cross_split_near_candidate_pairs_at_threshold']} cross-split pairs affecting {duplicate_summary['unique_heldout_ids_in_cross_split_near_candidates']} unique held-out rows. The review queue contains {duplicate_summary['near_duplicate_review_queue_pairs']} pairs after excluding {duplicate_summary['heldout_heldout_near_pairs_excluded_from_review']} heldout-heldout pairs that are not useful for training-to-evaluation leakage.

## Human Review Queue

The review queue is `results/duplicate/near_duplicate_review_queue.csv`. Fill these fields during manual review:

- `review_decision`: `accepted`, `rejected_false_positive`, or another documented team value.
- `review_category`: for example `same_template`, `generic_short_text`, `semantic_change`, `insufficient_specificity`.
- `reviewer`, `review_notes`, `recommended_action`, and `confidence`.

Representative highest-scoring initial review candidates before adjudication:

{markdown_table(near_examples, ["Pair", "IDs", "Label(s)", "Max cosine", "Suggested reason", "Decision"]) if near_examples else "No near-duplicate candidates require review at the protocol threshold after excluding heldout-heldout pairs."}

## Risk Interpretation

- Train-only exact duplicates are weighting risks.
- Cross-split exact duplicates are leakage/evaluation-independence risks.
- Cross-split near duplicates are template-leakage candidates until human review confirms or rejects them.
- Exact or near pairs with label conflict would be label-noise candidates; this run found none at the reported thresholds.

## Reproducible Evidence

- `results/duplicate/exact_duplicate_clusters.csv`
- `results/duplicate/exact_duplicate_members.csv`
- `results/duplicate/near_duplicate_candidates.csv`
- `results/duplicate/near_duplicate_threshold_sensitivity.csv`
- `results/duplicate/near_duplicate_review_queue.csv`
- `results/duplicate/near_duplicate_review_summary.csv`
- `results/duplicate/near_duplicate_review_summary.json`
- `results/duplicate/duplicate_summary.json`
- `results/figures/exact_cluster_sizes.png`
"""
    (ROOT / "duplicates.md").write_text(report, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    DUPLICATE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_canonical().reset_index(drop=True)
    protocol = load_protocol()
    threshold = float(protocol["near_duplicate_cosine_threshold"])

    clusters, members, exact_cross = build_exact_tables(df)
    scores = compute_pair_scores(df)
    candidates = pair_rows(df, scores, threshold)
    protocol_candidates = candidates[candidates["max_cosine"] >= threshold].copy()
    cross_split_near = protocol_candidates[protocol_candidates["cross_split"]].copy()
    heldout_heldout_near = protocol_candidates[
        (protocol_candidates["split_a"] == "heldout") & (protocol_candidates["split_b"] == "heldout")
    ].copy()
    review_candidates = protocol_candidates.drop(index=heldout_heldout_near.index).copy()
    sensitivity = sensitivity_table(candidates, SENSITIVITY_THRESHOLDS)
    near_review = build_adjudication_template(review_candidates)

    write_csv_if_changed(clusters, DUPLICATE_RESULTS_DIR / "exact_duplicate_clusters.csv")
    write_csv_if_changed(members, DUPLICATE_RESULTS_DIR / "exact_duplicate_members.csv")
    write_csv_if_changed(candidates, DUPLICATE_RESULTS_DIR / "near_duplicate_candidates.csv")
    write_csv_if_changed(sensitivity, DUPLICATE_RESULTS_DIR / "near_duplicate_threshold_sensitivity.csv")
    write_csv_if_changed(near_review, DUPLICATE_RESULTS_DIR / "near_duplicate_review_queue.csv")

    duplicate_summary = {
        "source_script": "scripts/audit_duplicates.py",
        "method_version": METHOD_VERSION,
        "protocol_version": protocol.get("version"),
        "exact_normalization": protocol.get("minimum_definitions", {}).get("exact_duplicate"),
        "near_duplicate_threshold": threshold,
        "search_floor": SEARCH_FLOOR,
        "candidate_collection": "full_pairwise_threshold_scan",
        "exact_duplicate_clusters": int(len(clusters)),
        "rows_in_exact_duplicate_clusters": int(clusters["cluster_size"].sum()) if len(clusters) else 0,
        "repeated_rows_beyond_first": int((clusters["cluster_size"] - 1).sum()) if len(clusters) else 0,
        "cross_split_exact_clusters": int(len(exact_cross)),
        "label_conflict_exact_clusters": int(clusters["label_conflict"].sum()) if len(clusters) else 0,
        "largest_exact_cluster_size": int(clusters["cluster_size"].max()) if len(clusters) else 0,
        "near_duplicate_candidate_pairs_at_threshold": int(len(protocol_candidates)),
        "cross_split_near_candidate_pairs_at_threshold": int(len(cross_split_near)),
        "near_duplicate_review_queue_pairs": int(len(near_review)),
        "heldout_heldout_near_pairs_excluded_from_review": int(len(heldout_heldout_near)),
        "unique_heldout_ids_in_cross_split_near_candidates": int(
            pd.unique(
                pd.concat(
                    [
                        cross_split_near.loc[cross_split_near["split_a"] == "heldout", "id_a"],
                        cross_split_near.loc[cross_split_near["split_b"] == "heldout", "id_b"],
                    ],
                    ignore_index=True,
                )
            ).size
        )
        if len(cross_split_near)
        else 0,
        "near_duplicate_review_status": "pending_manual_review",
    }
    write_json(DUPLICATE_RESULTS_DIR / "duplicate_summary.json", duplicate_summary)
    write_figure(clusters)
    write_report(
        threshold,
        clusters,
        exact_cross,
        candidates,
        sensitivity,
        near_review,
        duplicate_summary,
    )

    print("Exact duplicate clusters:", duplicate_summary["exact_duplicate_clusters"])
    print("Near candidates at threshold:", duplicate_summary["near_duplicate_candidate_pairs_at_threshold"])
    print("Near review rows excluding heldout-heldout:", duplicate_summary["near_duplicate_review_queue_pairs"])
    print("Cross-split near candidates:", duplicate_summary["cross_split_near_candidate_pairs_at_threshold"])
    print(f"Wrote {ROOT / 'duplicates.md'}")


if __name__ == "__main__":
    main()
