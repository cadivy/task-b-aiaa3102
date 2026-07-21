# Impact Analysis

## Scope

The experiments compare five data interventions: leakage handling, training-label overlay, ambiguous-row handling, shortcut masking, and duplicate de-duplication. Canonical data and held-out labels are not edited; each condition is an experimental view produced by `scripts/run_impact_interventions.py`.

The impact model is the shared word TF-IDF + Logistic Regression baseline from `scripts/train_baseline.py` (`word_pipeline`: unigram/bigram TF-IDF, `C=4.0`, `solver='liblinear'`, `random_state=42`). Each condition retrains the same pipeline on the relevant intervention view.

## Intervention Results

| Condition | Family | Train rows | Held-out rows | Accuracy | Spam precision | Spam recall | Spam F1 | Macro-F1 | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `baseline_public_labels` | baseline | 4460 | 1114 | 99.10% | 99.29% | 93.96% | 96.55% | 98.02% | Original public training labels evaluated on all held-out rows. |
| `baseline_excluding_leaked_heldout` | leakage_aware_evaluation | 4460 | 1051 | 99.05% | 98.90% | 90.91% | 94.74% | 97.11% | Evaluation sensitivity after excluding held-out rows with exact or reviewed near train partners. |
| `remove_leakage_train_partners` | leakage_removal | 4389 | 1114 | 99.01% | 100.00% | 92.62% | 96.17% | 97.80% | Retrain after removing training rows that are exact or reviewed near partners of held-out rows. |
| `training_label_overlay` | label_overlay | 4460 | 1114 | 98.92% | 99.28% | 92.62% | 95.83% | 97.61% | Apply training-only label-error overlay; held-out labels remain unchanged. |
| `exclude_ambiguous_training_rows` | ambiguous_row_handling | 4448 | 1114 | 99.01% | 100.00% | 92.62% | 96.17% | 97.80% | Retrain after excluding training rows adjudicated as ambiguous policy cases. |
| `shortcut_cue_masking` | shortcut_masking | 4460 | 1114 | 98.74% | 96.55% | 93.96% | 95.24% | 97.26% | Replace URLs, phone-like strings, money/rate markers, digit runs, and promotional lexicon before training and evaluation. |
| `duplicate_deduplication` | duplicate_deduplication | 4043 | 1114 | 98.83% | 98.57% | 92.62% | 95.50% | 97.42% | Keep the earliest training row in each exact or reviewed train-train near-duplicate component. |
| `combined_training_view` | combined | 3982 | 1114 | 98.47% | 96.48% | 91.95% | 94.16% | 96.64% | Apply leakage-partner removal, duplicate de-duplication, ambiguous-row exclusion, remaining label overlay, and shortcut cue masking. |

## Conclusions

The public-label reference reaches 99.10% accuracy, 93.96% spam recall, and 96.55% spam F1 on all held-out rows. This is the comparison anchor: every intervention uses the same word TF-IDF + Logistic Regression pipeline, so metric changes mainly reflect the changed data view rather than a changed model family.

### Leakage Handling

Leakage-aware evaluation removes 63 held-out rows that have exact or reviewed near-duplicate partners in training, leaving 1051 held-out rows and 99.05% accuracy. This view asks how much of the headline score depends on examples that are partly recoverable from training. The drop in spam F1 from 96.55% to 94.74% suggests that leaked held-out rows make the original evaluation look cleaner than a fully independent held-out set would.

The training-side leakage intervention removes 71 training partners and retrains on 4389 rows, reaching 99.01% accuracy and 96.17% spam F1. This does not edit held-out labels; it estimates whether the model was benefiting from memorized or near-memorized training rows. The result shows that leakage is a data-quality risk for performance interpretation even when aggregate accuracy remains high.

### Label Overlay

The training-label overlay applies 13 training-only relabel proposals and reaches 98.92% accuracy with 95.83% spam F1. The limited metric movement means the baseline is not highly sensitive to the small reviewed label-error set, but the intervention still matters for audit validity: mislabeled training rows can distort feature weights, error analysis, and any qualitative claim about what the classifier learned.

### Ambiguous Rows

Ambiguous-row handling excludes 12 policy-ambiguous training rows and retrains on 4448 rows, again reaching 99.01% accuracy and 96.17% spam F1. The stable score should not be read as ambiguity being irrelevant. Instead, it means the ambiguous set is small enough not to move this particular aggregate metric, while still lowering confidence in row-level adjudication and in any strict claim that the public label policy is perfectly consistent.

### Shortcut Masking

Shortcut cue masking replaces URLs, phone-like strings, money/rate markers, digit runs, and fixed promotional words before both training and evaluation. It reaches 98.74% accuracy and 95.24% spam F1. The model still performs well, so the task is not solved only by one obvious token family; however, the lower precision and F1 show that shallow artifacts are part of the learned signal. This affects data-quality interpretation because strong shortcut cues can inflate apparent generalization while hiding weaker semantic robustness.

### Duplicate De-Duplication

Duplicate de-duplication removes 417 repeated training rows by keeping the earliest training member in each exact or accepted train-train near-duplicate component. The retrained model uses 4043 rows and reaches 98.83% accuracy with 95.50% spam F1. This intervention tests whether repeated messages overweight common templates. The small but visible movement means duplicates are not the sole driver of performance, but they do affect the effective training distribution and can make certain message templates count more than independent examples should.

### Combined View

The combined training view removes leakage partners, removes duplicate repeats, excludes ambiguous training rows, applies remaining training-label overlay entries, and masks shortcut cues. It trains on 3982 rows and reaches 98.47% accuracy with 94.16% spam F1. This is a conservative stress test rather than a proposed replacement dataset. Its lower score summarizes the cumulative impact of data-quality issues: each issue is individually modest, but together they reduce confidence that the original headline metric fully represents clean, independent generalization.

## Reproducible Artifacts

- `scripts/run_impact_interventions.py`: builds all intervention views and rewrites this report.
- `results/impact/intervention_metrics.csv`: one row per condition with metrics and confusion counts.
- `results/impact/intervention_summary.json`: row counts, seed, and source files used by the interventions.
- `impact_analysis.md`: narrative interpretation of the intervention comparison.
