# Cross-Split Leakage Audit

## Definition and procedure

A held-out row is counted as leakage when it is exact under the public normalization or is an accepted near duplicate of a training row. Generic vocabulary overlap is not enough. Each case retains a concrete training ID, match type, similarity and review reason.

## Findings

| Finding | Result |
|---|---:|
| Unique held-out rows in cross-split exact clusters | 5 |
| Unique held-out rows in accepted near matches | 59 |
| Unique held-out rows affected by exact or near leakage | 62 |
| Rejected cross-split near candidates | 6 |

The combined count is 62 rather than 64 because two held-out rows are represented by both exact and near relationships.

The strongest exact examples are `H0548`, `H0909`, `H0412` and `H0922`, all spam templates already present in training. Strong near examples include substituted premium-rate numbers, prize claim codes and minor punctuation or character changes. These patterns are especially easy for n-gram models to memorize.

## Evaluation impact

The trained word TF-IDF model was kept fixed while confirmed leakage rows were excluded from sensitivity subsets.

| Evaluation set | N | Excluded | Accuracy | Spam recall | Spam F1 | Macro-F1 |
|---|---:|---:|---:|---:|---:|---:|
| Original held-out | 1114 | 0 | 99.10% | 93.96% | 96.55% | 98.02% |
| Excluding exact leakage | 1109 | 5 | 99.10% | 93.79% | 96.45% | 97.97% |
| Excluding exact and accepted near leakage | 1052 | 62 | 99.05% | 90.91% | 94.74% | 97.11% |

Removing exact duplicates alone changes little because only five rows are affected. Removing exact and accepted near matches lowers spam recall by 3.05 percentage points and spam F1 by 1.81 points. Overall accuracy moves only 0.05 points because the dataset is dominated by ham.

This result changes the meaning of the score. The model does not materially collapse, but its strongest headline metric hides a larger change in minority-class generalization. The lower leakage-aware spam recall is a stricter and more credible estimate for novel templates.

## Rejected evidence

The `T1881`/`H0850` semantic reversal and five generic short-message pairs remain in `near_duplicate_adjudication.csv` with `rejected_false_positive`. They are not removed from the leakage-aware subset.

## Recommended action

1. Keep the official 1114-row score for comparability.
2. Present the 1052-row leakage-aware sensitivity score beside it.
3. Rebuild future splits by duplicate/template cluster rather than individual row.
4. Never describe the current held-out set as fully unseen without this qualification.

## Reproducible evidence

- `results/leakage_cases.csv`
- `results/leakage_metrics.csv`
- `results/cross_split_exact_clusters.csv`
- `results/cross_split_near_candidates.csv`
- `results/near_duplicate_adjudication.csv`

