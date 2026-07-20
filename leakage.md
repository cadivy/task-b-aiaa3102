# Leakage Analysis

## Scope

This leakage workflow is a check-only stage. It does not rewrite the dataset, retrain any model, or perform a second manual near-duplicate review.

Leakage evidence is defined as held-out messages that have training-set duplicate evidence from either exact cross-split duplicates or accepted cross-split near duplicates from the completed duplicate review.

## Leakage Types

| Type | Meaning | Included here |
|---|---|---|
| `exact` | Held-out text appears in train under the exact duplicate rule: lowercase plus whitespace collapse. | Yes, direct leakage. |
| `near_reviewed_accepted` | Held-out and train texts are not exact duplicates, but duplicate-stage review accepted them as substantively the same message, campaign, or template. | Yes, template leakage. |
| rejected near candidate | A high-similarity candidate that duplicate review rejected as too generic or not substantively duplicated. | No. |

Severity is a lightweight reporting field: exact leakage is `high`; near leakage with high review confidence is `medium_high`; other accepted near leakage is `medium`.

## Inputs

- `results/duplicate/exact_duplicate_clusters.csv` and `results/duplicate/exact_duplicate_members.csv` provide exact duplicate clusters and members.
- `results/duplicate/near_duplicate_review_queue.csv` provides reviewed near-duplicate pairs; only `review_decision=accepted` and `cross_split=True` rows are used.
- `results/duplicate/near_duplicate_review_summary.json` is checked to require `remaining_needs_review_pairs=0`.
- `results/heldout_predictions.csv` provides existing held-out predictions for metric sensitivity. These predictions are reused as-is.

## Findings

| Finding | Result |
|---|---|
| Cross-split exact leakage pairs | 6 |
| Unique held-out rows with exact leakage | 5 |
| Accepted cross-split near leakage pairs | 85 |
| Unique held-out rows with accepted near leakage | 60 |
| Unique held-out rows with any duplicate leakage evidence | 63 |

Held-out rows by leakage type:

| leakage_type | heldout_rows |
|---|---|
| exact | 3 |
| exact_and_near_reviewed_accepted | 2 |
| near_reviewed_accepted | 58 |

Held-out rows by label:

| label | heldout_rows |
|---|---|
| ham | 13 |
| spam | 50 |

Held-out rows by severity:

| severity | heldout_rows |
|---|---|
| high | 5 |
| medium | 12 |
| medium_high | 46 |

## Representative Examples

| example_type | case_id | heldout_id | train_id | max_cosine | review_category | confidence | heldout_text | train_text |
|---|---|---|---|---|---|---|---|---|
| exact_duplicate | L_EXACT_E0009_H0009_T3705 | H0009 | T3705 | 1.0000 | exact_duplicate | high | Sorry, I'll call later in meeting. | Sorry, I'll call later In meeting. |
| near_spam_campaign_template | L_NEAR_N0434 | H0908 | T4439 | 1.0000 | same_spam_campaign_template | high | Had your contract mobile 11 Mnths? Latest Motorola, Nokia etc. all FREE! Double Mins & Text on Orange tariffs. TEXT Y... | Had your contract mobile 11 Mnths? Latest Motorola, Nokia etc. all FREE! Double Mins & Text on Orange tariffs. TEXT Y... |
| near_ham_personalization | L_NEAR_N0102 | H0136 | T4269 | 1.0000 | minor_personalization_change | medium | So when do you wanna gym harri | So when do you wanna gym? |

## Metric Sensitivity

The table below keeps the trained baseline predictions fixed and only removes affected held-out rows from scoring. This estimates how much reported performance depends on contaminated evaluation rows without retraining or changing data.

| condition | scored_n | excluded_rows | excluded_ham | excluded_spam | accuracy | spam_precision | spam_recall | spam_f1 | macro_f1 |
|---|---|---|---|---|---|---|---|---|---|
| original_heldout | 1114 | 0 | 0 | 0 | 0.9910 | 0.9929 | 0.9396 | 0.9655 | 0.9802 |
| exclude_exact_leakage | 1109 | 5 | 1 | 4 | 0.9910 | 0.9927 | 0.9379 | 0.9645 | 0.9797 |
| exclude_exact_and_reviewed_near_leakage | 1051 | 63 | 13 | 50 | 0.9905 | 0.9890 | 0.9091 | 0.9474 | 0.9711 |

`word_pred` is shown as the primary baseline signal. `results/leakage/leakage_metrics.csv` also includes the same sensitivity rows for `char_pred`.

Because the affected rows are mostly spam, spam recall and spam F1 are more sensitive than accuracy. Accuracy changes little because the held-out set is dominated by ham rows, so a small number of removed spam rows has limited effect on the overall correct/incorrect ratio.

## Related Files

- `scripts/audit_leakage.py`: rebuilds the leakage check, evidence tables, metric sensitivity table, figures, and this report. It consumes reviewed duplicate outputs and does not retrain or adjudicate pairs.
- `results/leakage/leakage_cases.csv`: pair-level leakage evidence. One row is one train-heldout duplicate relationship, with exact cluster IDs or reviewed near pair IDs.
- `results/leakage/leakage_heldout_rows.csv`: sample-level leakage summary. One row is one affected held-out sample, including leakage type, severity, train partners, prediction fields, and text.
- `results/leakage/leakage_metrics.csv`: metric sensitivity results for `word_pred` and `char_pred` under original, exact-excluded, and exact-plus-near-excluded scoring conditions.
- `results/leakage/leakage_representative_examples.csv`: a small fixed set of example pairs for report illustration: exact duplicate, spam template near duplicate, and ham personalization near duplicate when available.
- `results/leakage/leakage_summary.json`: machine-readable aggregate counts, input paths, output paths, and review dependency metadata.
- `results/figures/leakage_heldout_by_type.png`: bar chart of affected held-out rows by leakage type.
- `results/figures/leakage_heldout_by_label.png`: bar chart of affected held-out rows by label.
- `results/figures/leakage_metric_sensitivity.png`: line chart showing how core held-out metrics change after excluding leakage rows.

## Interpretation

Exact cross-split duplicates are direct evaluation-independence problems: the held-out text already appears in training under the same normalization rule used by the duplicate audit.

Accepted cross-split near duplicates are template leakage findings: the held-out message is not exactly identical under the public rule, but the duplicate-stage review accepted it as substantively the same message, campaign, or template. Rejected near candidates are intentionally excluded here.
