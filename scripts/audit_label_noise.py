"""Generate evidence-rich label-noise and ambiguity candidates."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from common import RESULTS_DIR, ensure_dirs, normalize_text


def main() -> None:
    ensure_dirs()
    predictions = pd.read_csv(RESULTS_DIR / "all_predictions.csv", keep_default_na=False)
    predictions = predictions.sort_values("uci_row_number").reset_index(drop=True)
    predictions["normalized_text"] = predictions["text"].map(normalize_text)

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        lowercase=True,
        ngram_range=(3, 5),
        min_df=2,
        max_features=60000,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(predictions["text"])
    neighbors = NearestNeighbors(metric="cosine", algorithm="brute", n_neighbors=9)
    neighbors.fit(matrix)
    distances, indices = neighbors.kneighbors(matrix)

    rows = []
    for row_idx, row in predictions.iterrows():
        neighbor_records = []
        for distance, neighbor_idx in zip(distances[row_idx, 1:], indices[row_idx, 1:]):
            neighbor = predictions.iloc[int(neighbor_idx)]
            neighbor_records.append(
                {
                    "id": neighbor["id"],
                    "label": neighbor["label"],
                    "similarity": 1.0 - float(distance),
                    "is_exact_text": neighbor["normalized_text"] == row["normalized_text"],
                }
            )

        non_exact = [record for record in neighbor_records if not record["is_exact_text"]]
        evidence_neighbors = non_exact[:5] if non_exact else neighbor_records[:5]
        opposite_neighbors = [
            record for record in evidence_neighbors if record["label"] != row["label"]
        ]
        weighted_total = sum(max(record["similarity"], 0.0) for record in evidence_neighbors)
        weighted_opposite = sum(
            max(record["similarity"], 0.0) for record in opposite_neighbors
        )
        opposite_neighbor_fraction = (
            weighted_opposite / weighted_total if weighted_total else 0.0
        )
        closest_opposite = max(
            opposite_neighbors, key=lambda item: item["similarity"], default=None
        )

        mean_p_spam = (float(row["word_p_spam"]) + float(row["char_p_spam"])) / 2
        opposite_model_score = mean_p_spam if row["label"] == "ham" else 1 - mean_p_spam
        word_opposes = row["word_pred"] != row["label"]
        char_opposes = row["char_pred"] != row["label"]
        neighbor_opposes = (
            opposite_neighbor_fraction >= 0.60
            and closest_opposite is not None
            and closest_opposite["similarity"] >= 0.30
        )
        model_signal_count = int(word_opposes) + int(char_opposes)
        automated_signal_count = model_signal_count + int(neighbor_opposes)

        rows.append(
            {
                **row.drop(labels=["normalized_text"]).to_dict(),
                "mean_p_spam": mean_p_spam,
                "opposite_model_score": opposite_model_score,
                "word_model_opposes": word_opposes,
                "char_model_opposes": char_opposes,
                "models_agree_opposite": word_opposes and char_opposes,
                "opposite_neighbor_fraction": opposite_neighbor_fraction,
                "closest_opposite_id": closest_opposite["id"] if closest_opposite else "",
                "closest_opposite_label": closest_opposite["label"] if closest_opposite else "",
                "closest_opposite_similarity": (
                    closest_opposite["similarity"] if closest_opposite else 0.0
                ),
                "neighbor_signal_opposes": neighbor_opposes,
                "automated_signal_count": automated_signal_count,
                "neighbor_ids": "|".join(record["id"] for record in evidence_neighbors),
                "neighbor_labels": "|".join(record["label"] for record in evidence_neighbors),
                "neighbor_similarities": "|".join(
                    f"{record['similarity']:.4f}" for record in evidence_neighbors
                ),
            }
        )

    evidence = pd.DataFrame(rows)
    evidence.to_csv(RESULTS_DIR / "label_noise_evidence.csv", index=False)

    label_candidates = evidence[
        (evidence["automated_signal_count"] >= 2)
        | (evidence["opposite_model_score"] >= 0.60)
        | (
            (evidence["opposite_neighbor_fraction"] >= 0.80)
            & (evidence["closest_opposite_similarity"] >= 0.55)
        )
    ].copy()
    label_candidates["candidate_score"] = (
        label_candidates["opposite_model_score"]
        + 0.20 * label_candidates["automated_signal_count"]
        + 0.20 * label_candidates["opposite_neighbor_fraction"]
        + 0.10 * label_candidates["closest_opposite_similarity"]
    )
    label_candidates = label_candidates.sort_values(
        ["candidate_score", "opposite_model_score"], ascending=False
    )
    label_candidates.to_csv(RESULTS_DIR / "label_error_candidates.csv", index=False)

    evidence["model_disagreement"] = evidence["word_pred"] != evidence["char_pred"]
    evidence["distance_to_boundary"] = (evidence["mean_p_spam"] - 0.5).abs()
    evidence["neighbor_mixedness"] = 1 - (
        (evidence["opposite_neighbor_fraction"] - 0.5).abs() * 2
    ).clip(lower=0, upper=1)
    ambiguity = evidence[
        evidence["model_disagreement"]
        | (evidence["distance_to_boundary"] <= 0.18)
        | (evidence["neighbor_mixedness"] >= 0.70)
    ].copy()
    ambiguity["ambiguity_score"] = (
        (1 - 2 * ambiguity["distance_to_boundary"]).clip(lower=0)
        + 0.40 * ambiguity["model_disagreement"].astype(float)
        + 0.40 * ambiguity["neighbor_mixedness"]
    )
    ambiguity.sort_values("ambiguity_score", ascending=False).to_csv(
        RESULTS_DIR / "ambiguity_candidates.csv", index=False
    )

    print(f"Label-error candidates: {len(label_candidates)}")
    print(f"Ambiguity candidates: {len(ambiguity)}")
    print(
        label_candidates[
            [
                "id",
                "split",
                "label",
                "opposite_model_score",
                "automated_signal_count",
                "closest_opposite_id",
                "closest_opposite_similarity",
                "candidate_score",
            ]
        ].head(20).to_string(index=False)
    )


if __name__ == "__main__":
    main()
