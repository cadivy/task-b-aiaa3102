# Topic B — Dataset Forensics and Label Audit

Exact commands and software versions needed to regenerate the main artifacts.

## Software Versions

| Package | Version |
| ------------ | ------- |
| Python | 3.12.11 |
| scikit-learn | 1.8.0 |
| pandas | 2.2.3 |
| numpy | 2.2.6 |
| scipy | 1.16.0 |
| matplotlib | 3.10.8 |
| joblib | 1.5.3 |

These match `requirements.txt`. scikit-learn determines the numeric results, which reproduce bit-for-bit at word held-out accuracy 99.1023%.

Building `report.pdf` additionally requires **pandoc** (tested with 3.1.2) on PATH and either **Microsoft Edge** or **Google Chrome** installed.

## Commands

Run from a clean clone, in order:

```powershell
# Data and baseline signals
python scripts\download_data.py             # verifies 5574 rows and SHA-256
python scripts\build_dataset.py             # -> data/canonical_sms.csv
python scripts\train_baseline.py            # word/char baselines, SEED=42

# Dataset profile
python scripts\profile_data.py              # -> audit/profile.md

# Targets 1-3: duplicates and leakage (order is required, see note below)
python scripts\audit_duplicates.py          # -> audit/duplicates.md
python scripts\review_near_duplicates.py    # merges the manual review decisions
python scripts\audit_leakage.py             # -> audit/leakage.md

# Targets 4 and 6: label errors and ambiguity
python scripts\audit_label_noise.py
python scripts\build_label_noise_outputs.py # -> audit/label_noise.md, audit/ambiguity.md

# Target 5: shortcut features
python scripts\audit_shortcuts.py           # -> audit/shortcut_features.md

# Target 7: data interventions
python scripts\label_overlay_experiment.py
python scripts\intervention_leakage_eval.py
python scripts\intervention_ambiguity_eval.py
python scripts\run_impact_interventions.py  # -> impact_analysis.md

# Submission files
python scripts\build_suspicious_examples.py
python scripts\build_submission_outputs.py  # -> suspicious_examples.csv, adjudication_memo.csv

# Final report
python scripts\build_report_pdf.py          # report.md -> report.pdf
```

Call the scripts as `python scripts\name.py`. They use `from common import ...` and rely on Python placing `scripts/` on `sys.path[0]`, so `python -m scripts.name` fails to import.

**Ordering note.** The three Target 1-3 scripts depend on each other. `audit_duplicates.py` rewrites `audit/duplicates.md` from scratch and generates the near-duplicate candidate queue; `review_near_duplicates.py` merges in the manual review decisions and appends the review section; `audit_leakage.py` consumes the reviewed queue. Re-running the first script alone discards the appended review section, and skipping the second leaves the third with an unreviewed queue. The intervention scripts must run after their respective audit scripts, and the two build scripts after all audit scripts.
