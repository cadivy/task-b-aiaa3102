# Final Report Content Map

The generated 12-page `report.pdf` is the authoritative project report. This file maps each report section to its reproducible sources.

| Report section                    | Main evidence                                                               |
| --------------------------------- | --------------------------------------------------------------------------- |
| Executive Summary                 | `baseline_metrics.csv`, `leakage_metrics.csv`, ranked-audit counts      |
| Dataset and Research Questions    | `data_provenance.json`, `data_validation.json`, `profile_summary.csv` |
| Methodology                       | Scripts and`starter/configs/audit_protocol.json`                          |
| Dataset Profile and Baseline      | `baseline_metrics.csv`, profile figures                                   |
| Duplicate and Leakage Findings    | exact clusters, near candidates, threshold sensitivity                      |
| Leakage-Aware Evaluation          | `leakage_cases.csv`, `leakage_metrics.csv`                              |
| Likely Label Errors and Ambiguity | label evidence, manual review config, adjudication memo                     |
| Shortcut Features                 | shortcut metrics, coefficients and example predictions                      |
| Data-Intervention Results         | intervention metrics and predictions                                        |
| Difficulties and Solutions        | validation evidence, false-positive cases and execution log                 |
| Conclusions and Recommendations   | Cross-section synthesis                                                     |
| AI usage declaration              | `logs/chat.md` and memo review status                                     |

## Required content confirmed

The final report contains:

- methodology for all six audit targets;
- ranked and calibrated findings;
- accepted and rejected near-duplicate candidates;
- baseline and class-specific metrics;
- at least two data interventions;
- explicit held-out-label protection;
- five concrete Difficulties and Solutions;
- limitations of AI-assisted policy judgment;
- dataset, handout and software references;
- exact reproduction command.

## Generation and visual verification

Run:

```powershell
python scripts/generate_report.py
```

The script generates `output/pdf/report.pdf` and an identical root `report.pdf`. The final PDF was rendered at 120 DPI to 12 PNG pages. The first render exposed an incorrect page-template transition that made body pages dark; the template was corrected, the PDF was regenerated, and all pages were visually rechecked for clipping, contrast, table fit, chart legibility, page numbering and section transitions.
