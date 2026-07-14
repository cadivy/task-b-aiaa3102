# Data-Quality Impact Analysis

## Status

**V1 pre-registered analysis plan — no intervention result has been generated.** This document will be updated only with metrics produced by the shared intervention script.

## 1. Purpose

The goal is to determine how documented data-quality problems change model evaluation. The analysis does not assume that a higher post-cleaning score is better. In particular, removing leakage may lower the score while making the evaluation more credible.

## 2. Controlled comparison

All conditions will keep the following fixed:

- word TF-IDF feature settings;
- Logistic Regression hyperparameters;
- random seed `42`;
- metric definitions;
- official held-out labels;
- preprocessing code, except for the explicitly named intervention.

Each intervention changes one data condition at a time. A combined condition may be reported after the individual effects.

## 3. Baseline condition

Train on every row assigned to `train` by the fixed manifest and evaluate on every official `heldout` row.

This score is the public reference, not an unquestioned estimate of deployment performance.

## 4. Intervention A: Leakage-aware evaluation

### Change

Keep the trained baseline model fixed and evaluate additionally on held-out subsets that exclude confirmed cross-split exact matches, then confirmed exact plus near matches.

### Question

How much of the original score comes from held-out messages recoverable from training examples?

### Expected interpretation

- Lower score after exclusion: original evaluation was probably optimistic.
- Similar score: detected leakage exists but does not materially drive aggregate performance.
- Higher score: leaked cases may be unusually difficult or label-conflicted; inspect them rather than assuming leakage helps.

## 5. Intervention B: Duplicate-aware training

### Change

Deduplicate training rows by accepted cluster while preserving one representative and cluster metadata. Representative choice must be deterministic. As a sensitivity check, compare simple deduplication with cluster weighting if time permits.

### Question

Does repeated exposure to identical or near-identical templates materially affect performance or calibration?

### Risk

Deduplication changes the empirical message frequency. If repeated templates are realistic in deployment, fully removing them may answer a different question. Both original and deduplicated results remain visible.

## 6. Intervention C: High-confidence training audit filter

### Change

Remove only training examples that satisfy all of the following:

- adjudicated as `should_fix`;
- final confidence is `high`;
- supported by the required evidence;
- not removed merely because the baseline model misclassified them.

### Question

Does excluding the strongest suspected training-data errors change held-out performance or error composition?

This intervention is optional only if Intervention A and B are fully completed; otherwise it is the second required intervention.

## 7. Intervention D: Training-label overlay

### Change

Apply a separate overlay to doubly reviewed training labels. Never overwrite the canonical working table. Never modify held-out labels.

### Question

Are results sensitive to a small, explicitly documented set of proposed training corrections?

Because the proposed labels are judgments rather than new ground truth, this condition is reported as a sensitivity analysis, not as the definitive clean dataset.

## 8. Result table

| Condition | Train N | Held-out N | Accuracy | Spam precision | Spam recall | Spam F1 | Macro-F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Original baseline | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Leakage-aware: exclude exact | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Leakage-aware: exclude exact + near | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Duplicate-aware training | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| High-confidence training filter | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Training-label overlay | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Combined sensitivity condition | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## 9. Additional comparisons

For each condition, also report:

- absolute and percentage change in sample count;
- confusion-matrix count changes;
- number of predictions changed relative to baseline;
- whether changes concentrate in duplicate, ambiguous or shortcut-heavy examples;
- bootstrap confidence intervals or paired bootstrap differences when feasible;
- the top changed examples, capped by the protocol’s `max_impact_examples=30`.

## 10. Interpretation checklist

The final analysis must answer:

1. Which data problem had the largest effect on the official score?
2. Did any intervention change model ranking or only absolute performance?
3. Are score changes larger than plausible sampling uncertainty?
4. Did spam Recall improve at the expense of many ham false positives?
5. Does a lower cleaned score indicate a harder and more credible test?
6. Which conclusions remain stable across all conditions?
7. Which intervention should be recommended for future dataset construction?

## 11. Claims we will not make

- A higher cleaned score proves the labels are correct.
- A lower leakage-aware score proves every duplicate was invalid.
- A small metric change proves data quality is unimportant.
- A training overlay recovers true held-out ground truth.
- Results from this corpus directly generalize to current real-world SMS systems.

## 12. Final conclusion placeholder

After experiments, replace this section with a concise conclusion containing only traceable numbers. It should explain whether the original evaluation is trustworthy, which intervention most changes its meaning, and what dataset-level action is recommended.

