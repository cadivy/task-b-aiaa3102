# Data-Quality Impact Analysis

## Controlled design

All training interventions use the same word TF-IDF and Logistic Regression settings, random seed and official 1114-row held-out labels. Leakage-aware rows keep the fitted baseline model fixed and change only the evaluation subset. No held-out label is edited.

## Results

| Condition | Train N | Held-out N | Accuracy | Spam recall | Spam F1 | Macro-F1 | Changed predictions |
|---|---:|---:|---:|---:|---:|---:|---:|
| Original baseline | 4460 | 1114 | 99.10% | 93.96% | 96.55% | 98.02% | 0 |
| Exact-deduplicated training | 4128 | 1114 | 98.83% | 92.62% | 95.50% | 97.42% | 5 |
| Filter high-confidence training errors | 4454 | 1114 | 98.92% | 93.96% | 95.89% | 97.64% | 2 |
| Training-label overlay | 4460 | 1114 | 98.92% | 93.96% | 95.89% | 97.64% | 2 |
| Exact deduplication plus overlay | 4128 | 1114 | 98.92% | 93.29% | 95.86% | 97.62% | 4 |
| Exclude exact leakage | 4460 | 1109 | 99.10% | 93.79% | 96.45% | 97.97% | Not applicable |
| Exclude exact and accepted near leakage | 4460 | 1052 | 99.05% | 90.91% | 94.74% | 97.11% | Not applicable |

## Intervention 1: Exact-deduplicated training

Keeping one deterministic representative per normalized training text reduces the training set from 4460 to 4128 rows, a reduction of 332 rows (7.44%). Held-out Accuracy falls by 0.27 percentage points, spam Recall by 1.34 points and spam F1 by 1.05 points. Five predictions change.

The decline indicates that repeated messages help the model learn recurring templates. This does not automatically mean deduplication is harmful: the result depends on whether deployment is expected to repeat known templates or prioritize novel messages. The original and deduplicated conditions answer different frequency assumptions.

## Intervention 2: High-confidence training filter

Removing six high-confidence suspected training label errors changes only two held-out predictions. Accuracy and spam F1 both decline slightly, while spam Recall stays unchanged. The filtered model makes more ham false positives rather than recovering additional spam.

This is evidence against selecting audit corrections by whether they improve the official score. Local label quality and benchmark performance are different objectives.

## Intervention 3: Training-label overlay

Nine adjudicated training corrections are applied through `results/training_label_overlay.csv`; the canonical labels remain unchanged. The overlay produces the same aggregate metrics as the six-row high-confidence filter and changes two predictions. The result shows low aggregate sensitivity to this small correction set.

## Intervention 4: Leakage-aware evaluation

Exact leakage alone affects only five held-out rows and barely moves aggregate metrics. Excluding exact plus accepted near leakage removes 62 unique held-out rows and lowers spam Recall from 93.96% to 90.91%. This is the most important evaluation-validity change because it targets independence rather than attempting to improve the classifier.

Overall accuracy hides the effect: it falls only from 99.10% to 99.05% because ham dominates the corpus. Spam Recall and F1 provide the clearer view.

## Conclusions

1. The raw score is robust in overall Accuracy but optimistic for minority-class generalization to novel templates.
2. Exact training deduplication modestly reduces performance because repeated templates contain useful frequency information.
3. The small label-error overlay does not improve the official metric and should be justified by evidence, not score chasing.
4. Leakage-aware evaluation produces the largest meaningful change: a 3.05-point spam-Recall reduction.
5. Future benchmarks should split by duplicate/template cluster, publish an annotation policy and report class-specific metrics.

## Reproducible evidence

- `results/intervention_metrics.csv`
- `results/intervention_predictions.csv`
- `results/training_label_overlay.csv`
- `results/leakage_metrics.csv`
- `results/figures/intervention_metrics.png`

