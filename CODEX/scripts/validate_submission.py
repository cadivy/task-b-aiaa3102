"""Strict validation for the complete Topic B project submission."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pypdf import PdfReader

from common import CANONICAL_PATH, PROTOCOL_PATH, RESULTS_DIR, ROOT, load_canonical


REQUIRED_FILES = [
    "README.md",
    "audit/profile.md",
    "audit/duplicates.md",
    "audit/leakage.md",
    "audit/label_noise.md",
    "audit/shortcut_features.md",
    "audit/ambiguity.md",
    "suspicious_examples.csv",
    "adjudication_memo.csv",
    "impact_analysis.md",
    "logs/chat.md",
    "report.pdf",
    "results/data_provenance.json",
    "results/data_validation.json",
    "results/profile_summary.csv",
    "results/baseline_metrics.csv",
    "results/exact_duplicate_clusters.csv",
    "results/near_duplicate_candidates.csv",
    "results/near_duplicate_adjudication.csv",
    "results/leakage_metrics.csv",
    "results/label_error_candidates.csv",
    "results/shortcut_metrics.csv",
    "results/training_label_overlay.csv",
    "results/intervention_metrics.csv",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_no_placeholders(paths: list[str]) -> None:
    forbidden = ["TBD", "results pending", "待实现", "待完成", "V1 method specification"]
    for relative in paths:
        content = (ROOT / relative).read_text(encoding="utf-8")
        for token in forbidden:
            if token.lower() in content.lower():
                raise AssertionError(f"Placeholder {token!r} remains in {relative}")


def main() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    assert not missing, f"Missing required files: {missing}"

    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    canonical = load_canonical()
    assert len(canonical) == 5574
    assert canonical["id"].nunique() == 5574
    assert (canonical["split"] == "train").sum() == 4460
    assert (canonical["split"] == "heldout").sum() == 1114
    assert set(canonical["label"]) == {"ham", "spam"}

    suspicious_path = ROOT / "suspicious_examples.csv"
    with suspicious_path.open(encoding="utf-8", newline="") as handle:
        actual_header = next(csv.reader(handle))
    assert actual_header == protocol["suspicious_examples_schema"]
    suspicious = pd.read_csv(suspicious_path, keep_default_na=False)
    assert len(suspicious) >= protocol["strict_submission_min_rows"]
    assert set(suspicious["issue_type"]) == set(protocol["issue_types"])
    assert set(suspicious["confidence"]).issubset(protocol["confidence_values"])
    assert set(suspicious["split"]).issubset(protocol["split_values"])
    assert suspicious["rank"].tolist() == list(range(1, len(suspicious) + 1))
    assert suspicious[["id", "issue_type"]].duplicated().sum() == 0
    high_fraction = float((suspicious["confidence"] == "high").mean())
    assert high_fraction <= protocol["strict_high_confidence_max_fraction"]
    for column in ["evidence_1", "evidence_2", "recommended_action", "short_explanation"]:
        assert suspicious[column].str.strip().ne("").all(), f"Empty values in {column}"

    id_to_split = canonical.set_index("id")["split"].to_dict()
    assert set(suspicious["id"]).issubset(id_to_split)
    assert all(id_to_split[row.id] == row.split for row in suspicious.itertuples())

    memo = pd.read_csv(ROOT / "adjudication_memo.csv", keep_default_na=False)
    assert len(memo) == len(suspicious)
    assert set(memo["final_decision"]).issubset(protocol["adjudication_categories"])
    assert memo["review_status"].str.contains("AI-assisted", regex=False).all()

    overlay = pd.read_csv(RESULTS_DIR / "training_label_overlay.csv", keep_default_na=False)
    assert len(overlay) > 0
    assert overlay["id"].str.startswith("T").all()
    assert set(overlay["id"]).issubset(set(canonical.loc[canonical["split"] == "train", "id"]))
    assert set(overlay["original_label"]).issubset({"ham", "spam"})
    assert set(overlay["proposed_label"]).issubset({"ham", "spam"})

    metrics_files = [
        "baseline_metrics.csv",
        "leakage_metrics.csv",
        "shortcut_metrics.csv",
        "intervention_metrics.csv",
    ]
    for filename in metrics_files:
        table = pd.read_csv(RESULTS_DIR / filename)
        for column in ["accuracy", "spam_recall", "spam_f1", "macro_f1"]:
            assert np.isfinite(table[column]).all(), f"Non-finite {column} in {filename}"
            assert table[column].between(0, 1).all(), f"Out-of-range {column} in {filename}"

    report_path = ROOT / "report.pdf"
    report_copy = ROOT / "output" / "pdf" / "report.pdf"
    assert report_copy.is_file()
    assert sha256(report_path) == sha256(report_copy)
    reader = PdfReader(str(report_path))
    assert len(reader.pages) == 12
    extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
    for required_phrase in [
        "Difficulties and Solutions",
        "AI usage declaration",
        "Leakage-Aware Evaluation",
        "10. Conclusions and Recommendations",
    ]:
        assert required_phrase in extracted, f"Report section missing: {required_phrase}"

    assert_no_placeholders(
        [
            "README.md",
            "audit/profile.md",
            "audit/duplicates.md",
            "audit/leakage.md",
            "audit/label_noise.md",
            "audit/shortcut_features.md",
            "audit/ambiguity.md",
            "impact_analysis.md",
        ]
    )

    print("Submission validation: PASS")
    print(f"Canonical rows: {len(canonical)}")
    print(f"Suspicious claims: {len(suspicious)}")
    print(f"Issue types: {len(set(suspicious['issue_type']))}")
    print(f"High-confidence fraction: {high_fraction:.3f}")
    print(f"Adjudication rows: {len(memo)}")
    print(f"Report pages: {len(reader.pages)}")


if __name__ == "__main__":
    main()
