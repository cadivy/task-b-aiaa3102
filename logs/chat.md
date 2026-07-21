# AI Usage Log

## Scope

OpenAI Codex was used as an implementation and review assistant for this project. It helped interpret the supplied handout, inspect the repository, write and revise reproducible scripts, integrate team outputs, prepare presentation material, and generate the final report.

## Evidence controls

- Dataset counts, split membership, labels, and hashes were taken from tracked result files produced by the repository scripts.
- Numerical claims in the report and presentation were read from CSV or JSON artifacts rather than invented from prose.
- Duplicate and leakage claims were tied to stable row IDs, pair keys, cluster IDs, and the completed manual review ledger.
- Training-label proposals were stored in an overlay. Held-out labels were never modified.
- The final ranked table was checked for the required schema, at least 35 rows, all six issue types, and a high-confidence fraction no greater than 55%.
- The English presentation and final PDF were rendered page by page and visually inspected for clipping, overflow, and unreadable charts.

## Human judgement and limitations

AI-assisted policy review was used to organize evidence and draft explanations. It is not presented as independent double annotation, and no inter-annotator agreement statistic is claimed. Subjective label-error and ambiguity findings should receive final team sign-off before submission.

## Main AI-assisted artifacts

- `scripts/build_final_submission.py`
- `scripts/generate_report.py`
- `suspicious_examples.csv`
- `adjudication_memo.csv`
- `presentation/cadivy_shortcut_interventions_en.pptx`
- `report.pdf`
