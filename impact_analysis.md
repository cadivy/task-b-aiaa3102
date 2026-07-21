# Impact Analysis

## Scope

The unified experiment compares five data-intervention families: leakage handling, training-label overlay, ambiguous-row handling, shortcut masking, and duplicate de-duplication. Canonical data and held-out labels are not edited; each condition is an experimental view produced by `scripts/run_impact_interventions.py`. Each training-set intervention is capped at at most 30 modified or removed training rows, selected deterministically by original UCI row order from the eligible candidate set. A separate adjudication-aware evaluation is produced by `scripts/intervention_ambiguity_eval.py`.

The impact model is the shared word TF-IDF + Logistic Regression baseline from `scripts/train_baseline.py` (`word_pipeline`: unigram/bigram TF-IDF, `C=4.0`, `solver='liblinear'`, `random_state=42`). Each condition retrains the same pipeline on the relevant intervention view.

## Intervention Results

| Condition | Family | Train rows | Held-out rows | Accuracy | Spam precision | Spam recall | Spam F1 | Macro-F1 | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `baseline_public_labels` | baseline | 4460 | 1114 | 99.10% | 99.29% | 93.96% | 96.55% | 98.02% | Original public training labels evaluated on all held-out rows. |
| `baseline_excluding_leaked_heldout` | leakage_aware_evaluation | 4460 | 1051 | 99.05% | 98.90% | 90.91% | 94.74% | 97.11% | Evaluation sensitivity after excluding held-out rows with exact or reviewed near train partners. |
| `remove_leakage_train_partners` | leakage_removal | 4430 | 1114 | 99.19% | 100.00% | 93.96% | 96.89% | 98.21% | Retrain after removing training rows that are exact or reviewed near partners of held-out rows. |
| `training_label_overlay` | label_overlay | 4460 | 1114 | 98.92% | 99.28% | 92.62% | 95.83% | 97.61% | Apply training-only label-error overlay; held-out labels remain unchanged. |
| `exclude_ambiguous_training_rows` | ambiguous_row_handling | 4448 | 1114 | 99.01% | 100.00% | 92.62% | 96.17% | 97.80% | Retrain after excluding training rows adjudicated as ambiguous policy cases. |
| `shortcut_cue_masking` | shortcut_masking | 4460 | 1114 | 98.47% | 99.25% | 89.26% | 93.99% | 96.56% | Replace URLs, phone-like strings, money/rate markers, digit runs, and promotional lexicon before training and evaluation. |
| `duplicate_deduplication` | duplicate_deduplication | 4430 | 1114 | 98.92% | 97.90% | 93.96% | 95.89% | 97.64% | Keep the earliest training row in each exact or reviewed train-train near-duplicate component. |
| `combined_training_view` | combined | 4430 | 1114 | 98.47% | 99.25% | 89.26% | 93.99% | 96.56% | Apply leakage-partner removal, duplicate de-duplication, ambiguous-row exclusion, remaining label overlay, and shortcut cue masking. |
| `adjudication_aware_evaluation` | adjudication_aware_evaluation | 4460 | 1110 | 99.37% | 99.29% | 95.86% | 97.54% | 98.59% | Frozen baseline after excluding two policy-ambiguous and two suspected-label-error held-out rows. |

## Conclusions

The public-label reference reaches 99.10% accuracy, 93.96% spam recall, and 96.55% spam F1 on all held-out rows. This is the comparison anchor: every intervention uses the same word TF-IDF + Logistic Regression pipeline, so metric changes mainly reflect the changed data view rather than a changed model family.

### Leakage Handling

Leakage-aware evaluation removes 63 held-out rows that have exact or reviewed near-duplicate partners in training, leaving 1051 held-out rows and 99.05% accuracy. This view asks how much of the headline score depends on examples that are partly recoverable from training. The drop in spam F1 from 96.55% to 94.74% suggests that leaked held-out rows make the original evaluation look cleaner than a fully independent held-out set would.

The training-side leakage intervention has 71 eligible training partners, but applies the 30-row cap and removes 30 of them before retraining on 4430 rows. It reaches 99.19% accuracy and 96.89% spam F1. This does not edit held-out labels; it estimates whether the model was benefiting from memorized or near-memorized training rows under a limited intervention budget.

### Label Overlay

The training-label overlay applies 13 training-only relabel proposals and reaches 98.92% accuracy with 95.83% spam F1. The limited metric movement means the baseline is not highly sensitive to the small reviewed label-error set, but the intervention still matters for audit validity: mislabeled training rows can distort feature weights, error analysis, and any qualitative claim about what the classifier learned.

### Ambiguous Rows

Ambiguous-row handling excludes 12 policy-ambiguous training rows and retrains on 4448 rows, again reaching 99.01% accuracy and 96.17% spam F1. The stable score should not be read as ambiguity being irrelevant. Instead, it means the ambiguous set is small enough not to move this particular aggregate metric, while still lowering confidence in row-level adjudication and in any strict claim that the public label policy is perfectly consistent.

### Adjudication-Aware Evaluation

The separate frozen-model evaluation removes two policy-ambiguous held-out rows and two suspected held-out label errors, leaving 1110 rows. Accuracy becomes 99.37% and spam recall becomes 95.86%. This increase must be interpreted cautiously: the two suspected label errors were retrieved because model signals oppose their labels, so removing them is partly circular. The ambiguity-only step is more informative because those rows were selected by policy reading rather than by model failure.

### Shortcut Masking

Shortcut cue masking replaces URLs, phone-like strings, money/rate markers, digit runs, and fixed promotional words before both training and evaluation. It reaches 98.47% accuracy and 93.99% spam F1. The model still performs well, so the task is not solved only by one obvious token family; however, the lower precision and F1 show that shallow artifacts are part of the learned signal. This affects data-quality interpretation because strong shortcut cues can inflate apparent generalization while hiding weaker semantic robustness.

### Duplicate De-Duplication

Duplicate de-duplication has 417 eligible repeated training rows, but removes only 30 under the 30-row cap by prioritizing earliest corpus order. The retrained model uses 4430 rows and reaches 98.92% accuracy with 95.89% spam F1. This intervention tests whether repeated messages overweight common templates under a bounded edit budget.

### Combined View

The combined training view applies the same 30-row cap to row removals, then applies capped label overlay and capped shortcut masking. It trains on 4430 rows and reaches 98.47% accuracy with 93.99% spam F1. This is a bounded stress test rather than a proposed replacement dataset, so the result should be read as directional evidence about cumulative data-quality sensitivity.

## Reproducible Artifacts

- `scripts/run_impact_interventions.py`: builds all intervention views and rewrites this report.
- `results/impact/intervention_metrics.csv`: one row per condition with metrics and confusion counts.
- `results/impact/intervention_summary.json`: row counts, seed, and source files used by the interventions.
- `scripts/intervention_ambiguity_eval.py` and `results/intervention_ambiguity_eval.json`: adjudication-aware frozen-model evaluation.
- `impact_analysis.md`: narrative interpretation of the intervention comparison.
