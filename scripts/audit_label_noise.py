"""Retrieve label-error and ambiguity candidates with reproducible evidence."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from common import RESULTS_DIR, ensure_dirs, normalize_text

N_EVIDENCE_NEIGHBOURS = 5
N_RETRIEVED = 20
NEIGHBOUR_OPPOSE_FRACTION = 0.60
NEIGHBOUR_OPPOSE_MIN_SIM = 0.30


def build_neighbour_evidence(frame: pd.DataFrame) -> pd.DataFrame:
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        lowercase=True,
        ngram_range=(3, 5),
        min_df=2,
        max_features=60000,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(frame["text"])
    neighbours = NearestNeighbors(
        metric="cosine", algorithm="brute", n_neighbors=N_RETRIEVED
    )
    neighbours.fit(matrix)
    distances, indices = neighbours.kneighbors(matrix)

    ids = frame["id"].to_numpy()
    labels = frame["label"].to_numpy()
    normalized = frame["normalized_text"].to_numpy()

    records: list[dict[str, object]] = []
    for position in range(len(frame)):
        own_label = labels[position]
        own_norm = normalized[position]

        window: list[tuple[str, str, float]] = []
        for distance, neighbour_position in zip(
            distances[position, 1:], indices[position, 1:]
        ):
            neighbour_position = int(neighbour_position)
            # A duplicate copy carries the same label by construction, so it
            # would let the row confirm its own label.
            if normalized[neighbour_position] == own_norm:
                continue
            window.append(
                (
                    ids[neighbour_position],
                    labels[neighbour_position],
                    1.0 - float(distance),
                )
            )
            if len(window) == N_EVIDENCE_NEIGHBOURS:
                break

        opposing = [item for item in window if item[1] != own_label]
        total_mass = sum(max(item[2], 0.0) for item in window)
        opposing_mass = sum(max(item[2], 0.0) for item in opposing)
        closest = max(opposing, key=lambda item: item[2], default=None)

        records.append(
            {
                "neighbour_count": len(window),
                "opposite_neighbour_fraction": (
                    opposing_mass / total_mass if total_mass else 0.0
                ),
                "closest_opposite_id": closest[0] if closest else "",
                "closest_opposite_similarity": closest[2] if closest else 0.0,
                "neighbour_ids": "|".join(item[0] for item in window),
                "neighbour_labels": "|".join(item[1] for item in window),
                "neighbour_similarities": "|".join(f"{item[2]:.4f}" for item in window),
            }
        )
    return pd.DataFrame(records, index=frame.index)


def main() -> None:
    ensure_dirs()
    frame = pd.read_csv(RESULTS_DIR / "all_predictions.csv", keep_default_na=False)
    frame = frame.sort_values("uci_row_number").reset_index(drop=True)
    frame["normalized_text"] = frame["text"].map(normalize_text)

    evidence = pd.concat([frame, build_neighbour_evidence(frame)], axis=1)

    evidence["word_opposes"] = evidence["word_pred"] != evidence["label"]
    evidence["char_opposes"] = evidence["char_pred"] != evidence["label"]
    evidence["neighbour_opposes"] = (
        evidence["opposite_neighbour_fraction"] >= NEIGHBOUR_OPPOSE_FRACTION
    ) & (evidence["closest_opposite_similarity"] >= NEIGHBOUR_OPPOSE_MIN_SIM)
    evidence["signal_count"] = (
        evidence["word_opposes"].astype(int)
        + evidence["char_opposes"].astype(int)
        + evidence["neighbour_opposes"].astype(int)
    )

    mean_p_spam = (evidence["word_p_spam"] + evidence["char_p_spam"]) / 2
    evidence["mean_p_spam"] = mean_p_spam
    evidence["opposition_strength"] = np.where(
        evidence["label"] == "ham", mean_p_spam, 1.0 - mean_p_spam
    )
    evidence["proposed_label"] = np.where(evidence["label"] == "ham", "spam", "ham")

    export = evidence.drop(columns=["normalized_text"])
    export.to_csv(RESULTS_DIR / "label_noise_evidence.csv", index=False)

    candidates = evidence[evidence["signal_count"] >= 2].copy()
    candidates["candidate_score"] = (
        candidates["opposition_strength"]
        + 0.20 * candidates["signal_count"]
        + 0.20 * candidates["opposite_neighbour_fraction"]
    )
    candidates = candidates.sort_values("candidate_score", ascending=False)
    candidates.drop(columns=["normalized_text"]).to_csv(
        RESULTS_DIR / "label_error_candidates.csv", index=False
    )

    watchlist = evidence[
        (evidence["signal_count"] == 1) & (evidence["opposition_strength"] >= 0.60)
    ].sort_values("opposition_strength", ascending=False)
    watchlist.drop(columns=["normalized_text"]).to_csv(
        RESULTS_DIR / "label_error_watchlist.csv", index=False
    )

    evidence["model_disagreement"] = evidence["word_pred"] != evidence["char_pred"]
    evidence["boundary_distance"] = (mean_p_spam - 0.5).abs()
    evidence["neighbour_mixedness"] = 1.0 - (
        (evidence["opposite_neighbour_fraction"] - 0.5).abs() * 2
    ).clip(lower=0.0, upper=1.0)

    ambiguity = evidence[
        evidence["model_disagreement"]
        | (evidence["boundary_distance"] <= 0.18)
        | (evidence["neighbour_mixedness"] >= 0.70)
    ].copy()
    ambiguity["ambiguity_score"] = (
        (1.0 - 2.0 * ambiguity["boundary_distance"]).clip(lower=0.0)
        + 0.40 * ambiguity["model_disagreement"].astype(float)
        + 0.40 * ambiguity["neighbour_mixedness"]
    )
    ambiguity = ambiguity.sort_values("ambiguity_score", ascending=False)
    ambiguity.drop(columns=["normalized_text"]).to_csv(
        RESULTS_DIR / "ambiguity_candidates.csv", index=False
    )

    both_models = int((candidates["word_opposes"] & candidates["char_opposes"]).sum())
    print(f"rows scored                     : {len(evidence)}")
    print(f"label-error candidates (>=2 sig): {len(candidates)}")
    print(f"  both models oppose            : {both_models}")
    print(f"  all three signals oppose      : {int((candidates['signal_count'] == 3).sum())}")
    print(f"single-signal watchlist         : {len(watchlist)}")
    print(f"ambiguity candidates            : {len(ambiguity)}")
    print()
    print(
        candidates[
            [
                "id",
                "split",
                "label",
                "signal_count",
                "opposition_strength",
                "opposite_neighbour_fraction",
                "candidate_score",
            ]
        ]
        .head(15)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
