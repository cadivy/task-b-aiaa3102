"""Run the complete reproducible project pipeline in dependency order."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "download_data.py",
    "build_dataset.py",
    "profile_data.py",
    "train_baseline.py",
    "audit_duplicates.py",
    "audit_leakage.py",
    "audit_shortcuts.py",
    "audit_label_noise.py",
    "build_audit_outputs.py",
    "run_interventions.py",
    "generate_report.py",
    "validate_submission.py",
]


def main() -> None:
    for number, script in enumerate(STEPS, start=1):
        print(f"\n[{number}/{len(STEPS)}] Running {script}", flush=True)
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script)],
            cwd=ROOT,
            check=True,
        )
    print("\nComplete project pipeline: PASS")


if __name__ == "__main__":
    main()
