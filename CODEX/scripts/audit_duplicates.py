"""Find exact clusters and TF-IDF near-duplicate pairs."""

from __future__ import annotations

from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from common import (
    FIGURES_DIR,
    RESULTS_DIR,
    ensure_dirs,
    load_canonical,
    load_protocol,
    normalize_text,
)


SEARCH_FLOOR = 0.88
N_NEIGHBORS = 15


def neighbor_pairs(matrix, floor: float) -> dict[tuple[int, int], float]:
    n_neighbors = min(N_NEIGHBORS, matrix.shape[0])
    model = NearestNeighbors(metric="cosine", algorithm="brute", n_neighbors=n_neighbors)
    model.fit(matrix)
    distances, indices = model.kneighbors(matrix)
    pairs: dict[tuple[int, int], float] = {}
    for row_idx, (row_distances, row_indices) in enumerate(zip(distances, indices)):
        for distance, other_idx in zip(row_distances[1:], row_indices[1:]):
            similarity = 1.0 - float(distance)
            if similarity < floor:
                continue
            pair = tuple(sorted((row_idx, int(other_idx))))
            pairs[pair] = max(pairs.get(pair, 0.0), similarity)
    return pairs


def main() -> None:
    ensure_dirs()
    protocol = load_protocol()
    threshold = float(protocol["near_duplicate_cosine_threshold"])
    df = load_canonical().sort_values("uci_row_number").reset_index(drop=True)
    df["normalized_text"] = df["text"].map(normalize_text)

    cluster_rows = []
    member_rows = []
    duplicate_groups = [
        group for _, group in df.groupby("normalized_text", sort=False) if len(group) > 1
    ]
    duplicate_groups.sort(key=lambda group: int(group["uci_row_number"].min()))
    for number, group in enumerate(duplicate_groups, start=1):
        cluster_id = f"E{number:04d}"
        splits = sorted(group["split"].unique().tolist())
        labels = sorted(group["label"].unique().tolist())
        cluster_rows.append(
            {
                "cluster_id": cluster_id,
                "cluster_size": len(group),
                "member_ids": "|".join(group["id"]),
                "splits": "|".join(splits),
                "labels": "|".join(labels),
                "is_cross_split": len(splits) > 1,
                "has_label_conflict": len(labels) > 1,
                "normalized_text": group["normalized_text"].iloc[0],
            }
        )
        for _, row in group.iterrows():
            member_rows.append(
                {
                    "cluster_id": cluster_id,
                    "id": row["id"],
                    "split": row["split"],
                    "label": row["label"],
                    "uci_row_number": row["uci_row_number"],
                    "text": row["text"],
                }
            )
    clusters = pd.DataFrame(cluster_rows)
    members = pd.DataFrame(member_rows)
    clusters.to_csv(RESULTS_DIR / "exact_duplicate_clusters.csv", index=False)
    members.to_csv(RESULTS_DIR / "exact_duplicate_members.csv", index=False)

    word_vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
    )
    char_vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        lowercase=True,
        ngram_range=(3, 5),
        min_df=2,
        max_features=60000,
        sublinear_tf=True,
    )
    word_matrix = word_vectorizer.fit_transform(df["text"])
    char_matrix = char_vectorizer.fit_transform(df["text"])
    word_pairs = neighbor_pairs(word_matrix, SEARCH_FLOOR)
    char_pairs = neighbor_pairs(char_matrix, SEARCH_FLOOR)

    candidate_pairs = set(word_pairs) | set(char_pairs)
    near_rows = []
    for left, right in sorted(candidate_pairs):
        if df.at[left, "normalized_text"] == df.at[right, "normalized_text"]:
            continue
        word_similarity = float(word_matrix[left].multiply(word_matrix[right]).sum())
        char_similarity = float(char_matrix[left].multiply(char_matrix[right]).sum())
        primary_similarity = max(word_similarity, char_similarity)
        if primary_similarity < SEARCH_FLOOR:
            continue
        basis = "word" if word_similarity >= char_similarity else "character"
        near_rows.append(
            {
                "id_1": df.at[left, "id"],
                "id_2": df.at[right, "id"],
                "split_1": df.at[left, "split"],
                "split_2": df.at[right, "split"],
                "label_1": df.at[left, "label"],
                "label_2": df.at[right, "label"],
                "word_similarity": word_similarity,
                "char_similarity": char_similarity,
                "primary_similarity": primary_similarity,
                "similarity_basis": basis,
                "meets_protocol_threshold": primary_similarity >= threshold,
                "is_cross_split": df.at[left, "split"] != df.at[right, "split"],
                "has_label_conflict": df.at[left, "label"] != df.at[right, "label"],
                "text_1": df.at[left, "text"],
                "text_2": df.at[right, "text"],
            }
        )
    near = pd.DataFrame(near_rows).sort_values(
        ["primary_similarity", "is_cross_split"], ascending=[False, False]
    )
    near.to_csv(RESULTS_DIR / "near_duplicate_candidates.csv", index=False)

    sensitivity = []
    for candidate_threshold in (0.88, 0.90, 0.92, 0.94, 0.96):
        subset = near[near["primary_similarity"] >= candidate_threshold]
        sensitivity.append(
            {
                "threshold": candidate_threshold,
                "candidate_pairs": len(subset),
                "cross_split_pairs": int(subset["is_cross_split"].sum()),
                "label_conflict_pairs": int(subset["has_label_conflict"].sum()),
            }
        )
    pd.DataFrame(sensitivity).to_csv(
        RESULTS_DIR / "near_duplicate_threshold_sensitivity.csv", index=False
    )

    cross_exact = clusters[clusters["is_cross_split"]].copy()
    cross_exact["match_type"] = "exact"
    cross_near = near[
        near["meets_protocol_threshold"] & near["is_cross_split"]
    ].copy()
    cross_near["match_type"] = "near"
    cross_exact.to_csv(RESULTS_DIR / "cross_split_exact_clusters.csv", index=False)
    cross_near.to_csv(RESULTS_DIR / "cross_split_near_candidates.csv", index=False)

    if not clusters.empty:
        sizes = clusters["cluster_size"].value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(7.2, 4.2))
        ax.bar(sizes.index.astype(str), sizes.values, color="#2563EB")
        ax.set_title("Exact-duplicate cluster-size distribution", loc="left", fontweight="bold")
        ax.set_xlabel("Rows per cluster")
        ax.set_ylabel("Clusters")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.18)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "exact_cluster_sizes.png", dpi=180)
        plt.close()

    print(f"Exact clusters: {len(clusters)}")
    print(f"Rows in exact clusters: {len(members)}")
    print(f"Cross-split exact clusters: {int(clusters['is_cross_split'].sum())}")
    print(f"Label-conflict exact clusters: {int(clusters['has_label_conflict'].sum())}")
    print(
        f"Near pairs >= {threshold:.2f}: "
        f"{int((near['primary_similarity'] >= threshold).sum())}"
    )
    print(
        f"Cross-split near pairs >= {threshold:.2f}: "
        f"{int(((near['primary_similarity'] >= threshold) & near['is_cross_split']).sum())}"
    )


if __name__ == "__main__":
    main()
