"""Validate the V1 documentation contract without requiring the raw dataset."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require_files(paths: list[str]) -> None:
    missing = [path for path in paths if not (ROOT / path).is_file()]
    if missing:
        raise AssertionError(f"Missing required files: {missing}")


def read_header(path: str) -> list[str]:
    with (ROOT / path).open(encoding="utf-8", newline="") as handle:
        return next(csv.reader(handle))


def main() -> None:
    required_files = [
        "README.md",
        "docs/project_plan.md",
        "docs/team_workflow.md",
        "docs/adjudication_protocol.md",
        "docs/report_outline.md",
        "audit/profile.md",
        "audit/duplicates.md",
        "audit/leakage.md",
        "audit/label_noise.md",
        "audit/shortcut_features.md",
        "audit/ambiguity.md",
        "impact_analysis.md",
        "logs/chat.md",
        "suspicious_examples.csv",
        "adjudication_memo.csv",
    ]
    require_files(required_files)

    protocol_path = ROOT / "starter/configs/audit_protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))

    actual_header = read_header("suspicious_examples.csv")
    assert actual_header == protocol["suspicious_examples_schema"], (
        "suspicious_examples.csv header does not match audit_protocol.json"
    )

    corpus = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in required_files
        if path.endswith(".md")
    )
    for issue_type in protocol["issue_types"]:
        assert issue_type in corpus, f"Issue type not documented: {issue_type}"

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    contract_values = [
        str(protocol["near_duplicate_cosine_threshold"]),
        str(protocol["shortcut_warning_accuracy"]),
        str(protocol["strict_submission_min_rows"]),
        "55%",
    ]
    for value in contract_values:
        assert value in readme, f"README does not document contract value: {value}"

    manifest_path = ROOT / "starter/data/split_manifest.csv"
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 5574, f"Unexpected manifest size: {len(rows)}"
    assert sum(row["split"] == "train" for row in rows) == 4460
    assert sum(row["split"] == "heldout" for row in rows) == 1114
    assert len({row["id"] for row in rows}) == len(rows)

    print("Documentation contract: PASS")
    print(f"Required files checked: {len(required_files)}")
    print(f"Audit issue types covered: {len(protocol['issue_types'])}")
    print(f"Manifest rows checked: {len(rows)}")


if __name__ == "__main__":
    main()

