# Topic B: Dataset Forensics and Label Audit

This repository contains a complete, reproducible audit of the UCI SMS Spam Collection for AIAA3102 Final Project Topic B.

The project does not treat high classifier accuracy as sufficient evidence of a trustworthy benchmark. It audits exact duplicates, near duplicates, cross-split leakage, likely label errors, shortcut features and annotation ambiguity, then measures how data interventions change evaluation.

## Final status

All required project artifacts have been generated from the official public data and fixed course manifest.

| Artifact | Status |
|---|---|
| Public data download and checksum record | Complete |
| Canonical 5574-row table and split validation | Complete |
| Dataset profile and two text baselines | Complete |
| Six required audit targets | Complete |
| Ranked `suspicious_examples.csv` | 51 claims, all six issue types |
| `adjudication_memo.csv` | 51 evidence-linked decisions |
| Controlled data interventions | Five training/evaluation conditions plus baseline |
| Final report | 12-page rendered and visually inspected PDF |
| Strict submission validation | Passing |

The final report is [report.pdf](report.pdf).

## Main findings

- The fixed split contains 4460 training rows and 1114 held-out rows. Spam shares are 13.41% and 13.38%, respectively.
- The word TF-IDF baseline reaches 99.10% held-out Accuracy, 93.96% spam Recall and 96.55% spam F1.
- There are 290 exact-duplicate clusters containing 705 rows. Five exact clusters cross train and held-out.
- At the public 0.92 TF-IDF cosine threshold, 361 non-exact candidate pairs remain and 90 cross the split.
- Evidence review accepts 84 cross-split near-template pairs and rejects six false-positive traps. Accepted exact/near relationships affect 62 unique held-out rows.
- Excluding those 62 rows changes Accuracy only from 99.10% to 99.05%, but spam Recall falls from 93.96% to 90.91%.
- Contact and promotional features alone reach 98.20% Accuracy and 93.15% spam F1, demonstrating strong but fragile shallow cues.
- Eleven likely label errors are included: nine training rows represented in an overlay and two held-out rows that remain unchanged.
- The final ranked audit contains 51 claims. High-confidence claims account for 51.0%, below the public 55% cap.

The central conclusion is that the classifier is genuinely strong on this file, but the raw Accuracy overstates how confidently we can claim minority-class generalization to novel templates.

## Data source and integrity

Dataset: UCI SMS Spam Collection.

- Dataset page: <https://archive.ics.uci.edu/dataset/228/sms+spam+collection>
- Archive: <https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip>
- DOI: <https://doi.org/10.24432/C5CC84>
- License: CC BY 4.0

Verified download hashes for this run:

```text
archive SHA-256: 1587ea43e58e82b14ff1f5425c88e17f8496bfcdb67a583dbff9eefaf9963ce3
raw file SHA-256: 7d039a24a6083ed9ef0f806ebad56bbb976e3aeb8de05669173bfdc4996c239d
```

The raw file is parsed using a 1-based line number and joined one-to-one with `starter/data/split_manifest.csv`. The build stops on any row-count, ID, split-prefix, label-domain, empty-text or join failure. The canonical table contains:

```text
id,split,uci_row_number,text,label
```

The fixed split is never regenerated. Public held-out labels are never modified. Proposed training corrections are stored separately in `results/training_label_overlay.csv`.

## Environment

The verified environment used:

```text
Python 3.13.2
pandas 3.0.2
numpy 2.4.4
scipy 1.17.1
scikit-learn 1.8.0
matplotlib 3.10.8
reportlab 5.0.0
pdfplumber 0.11.10
pypdf 6.14.2
```

Install the pinned Python dependencies with:

```powershell
python -m pip install -r requirements.txt
```

## Reproduce the entire project

From the repository root, run:

```powershell
python scripts/run_all.py
```

This performs the following verified sequence:

```powershell
python scripts/download_data.py
python scripts/build_dataset.py
python scripts/profile_data.py
python scripts/train_baseline.py
python scripts/audit_duplicates.py
python scripts/audit_leakage.py
python scripts/audit_shortcuts.py
python scripts/audit_label_noise.py
python scripts/build_audit_outputs.py
python scripts/run_interventions.py
python scripts/generate_report.py
python scripts/validate_submission.py
```

The full pipeline is CPU-friendly and uses deterministic model/split seeds where randomness is involved.

## Submission validation

The final command verifies:

- canonical data counts and stable IDs;
- the exact `suspicious_examples.csv` schema;
- at least 35 audit rows and all six issue types;
- allowed split, confidence and decision values;
- unique continuous ranks;
- high-confidence fraction no greater than 55%;
- evidence fields and stable-ID/split agreement;
- training-only label overlays;
- finite, in-range metrics;
- matching root and output PDF copies;
- 12 report pages and required report sections;
- absence of unfinished result placeholders in final deliverables.

Expected result:

```text
Submission validation: PASS
Canonical rows: 5574
Suspicious claims: 51
Issue types: 6
High-confidence fraction: 0.510
Adjudication rows: 51
Report pages: 12
```

## Audit outputs

The six target-specific reports are:

- [Dataset profile and baseline](audit/profile.md)
- [Exact and near duplicates](audit/duplicates.md)
- [Cross-split leakage](audit/leakage.md)
- [Likely label errors](audit/label_noise.md)
- [Shortcut features](audit/shortcut_features.md)
- [Ambiguity and policy boundaries](audit/ambiguity.md)

The intervention comparison is [impact_analysis.md](impact_analysis.md).

The public-format ranked output is [suspicious_examples.csv](suspicious_examples.csv), and the claim-level decision trace is [adjudication_memo.csv](adjudication_memo.csv).

## Repository structure

```text
.
|-- audit/                         # Six completed audit reports
|-- configs/
|   `-- manual_review.json         # Explicit selected policy judgments
|-- data/                          # Reproducible canonical tables, ignored by Git
|-- docs/                          # Research design, workflow and protocols
|-- logs/
|   `-- chat.md                    # AI usage and verification log
|-- models/                        # Reproducible fitted models, ignored by Git
|-- output/pdf/report.pdf          # Final PDF copy required by PDF workflow
|-- raw/                           # Downloaded UCI archive and text, ignored by Git
|-- results/                       # Tracked tables and figures supporting claims
|-- scripts/                       # Complete reproducible analysis pipeline
|-- starter/                       # Course manifest, protocol and format example
|-- adjudication_memo.csv
|-- impact_analysis.md
|-- report.pdf
|-- requirements.txt
`-- suspicious_examples.csv
```

## Public protocol compliance

The project follows `starter/configs/audit_protocol.json`:

| Rule | Implemented result |
|---|---|
| Near-duplicate threshold | 0.92 primary TF-IDF cosine |
| Shortcut warning threshold | 0.70 Accuracy; compared against 0.866 majority baseline |
| Label-error evidence | Model/neighbor signal plus policy review |
| Minimum ranked rows | 51 versus required 35 |
| Issue types | All six represented |
| High-confidence limit | 51.0% versus maximum 55% |
| Maximum highlighted impact examples | No more than 30 |

False-positive control is explicit. The output includes rejected near-duplicate and ambiguity candidates rather than turning every retrieval into a high-confidence finding.

## AI usage and review limitation

OpenAI Codex was used to implement and execute the pipeline, generate candidate evidence, perform an explicitly AI-assisted evidence and policy pass, draft the documentation and create the PDF. Numerical claims are regenerated from saved results, mappings are protected by assertions, and the final report was rendered page-by-page for visual verification.

No claim of two independent human reviewers or fabricated agreement statistics is made. AI is not presented as a source of ground-truth labels. The exact disclosure is recorded in [logs/chat.md](logs/chat.md) and in the report. Independent team reading remains advisable before academic submission, especially for subjective label-error and ambiguity decisions.

## Citation

Almeida, T. and Hidalgo, J. (2011). *SMS Spam Collection*. UCI Machine Learning Repository. DOI: `10.24432/C5CC84`.
