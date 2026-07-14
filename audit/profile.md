# Dataset Profile and Baseline

## Status

**V1 method specification — results not yet generated.** All numerical result fields below must be filled by the reproducible profiling script; no value should be copied manually from an exploratory notebook.

## Objective

Establish whether the downloaded corpus is correctly aligned with the fixed course split, describe the distributions that matter for later audits, and create an interpretable text-classification baseline.

## Data integrity checks

The build pipeline must verify:

- 5574 raw rows and 5574 manifest rows;
- 4460 `train` and 1114 `heldout` rows;
- unique `uci_row_number` and course `id`;
- a one-to-one join without missing rows;
- labels restricted to `ham` and `spam`;
- split and ID prefix agreement;
- no empty text after parsing.

These checks establish mapping integrity only. They do not imply that the public labels are correct.

## Descriptive profile

The final version will report the following by split and label:

| Quantity | Why it matters | Result source |
|---|---|---|
| Number and class percentage | Measures imbalance and split comparability | `results/profile_summary.csv` |
| Character and token length | Potential shortcut and distribution shift | `results/profile_summary.csv` |
| Digit, URL and phone prevalence | Potential commercial/contact shortcut | `results/profile_summary.csv` |
| Currency and promotion-token prevalence | Potential shallow label cue | `results/profile_summary.csv` |
| Normalized unique-text count | Starting point for duplication audit | `results/profile_summary.csv` |
| Spam rate by row-position bin | Tests corpus-order artifact | `results/profile_summary.csv` |

Plots should be limited to those used in the argument: class distribution, text-length distribution, shallow-feature prevalence, and spam rate by row-position bin.

## Baseline model

Primary model:

```text
word TF-IDF (1,2)-grams + Logistic Regression
```

Secondary diagnostic model:

```text
character TF-IDF n-grams + Logistic Regression
```

The training set will produce out-of-fold predictions for audit signals. A final model fitted on all training rows will produce held-out predictions. The held-out split will not be used to choose the model or tune audit thresholds.

## Metrics to report

| Model | Accuracy | Spam precision | Spam recall | Spam F1 | Macro-F1 |
|---|---:|---:|---:|---:|---:|
| Word TF-IDF | TBD | TBD | TBD | TBD | TBD |
| Character TF-IDF | TBD | TBD | TBD | TBD | TBD |
| Shallow-only diagnostic | TBD | TBD | TBD | TBD | TBD |

The final version will also include confusion matrices and counts, not only normalized rates. Accuracy will not be interpreted in isolation because spam is the minority class.

## Required observations after execution

The result narrative must answer:

1. Are train and held-out class proportions materially different?
2. Which shallow distributions most strongly separate labels?
3. Does a character model disagree systematically with the word model?
4. Which error type dominates: false positives or false negatives?
5. Does the raw held-out score remain similar after removing leakage cases?

## Limitations

- The fixed split is part of the course design and may not represent temporal or deployment shift.
- Strong baseline performance does not validate the labels or split.
- Prediction confidence is a model property, not a direct probability that a label is wrong.

