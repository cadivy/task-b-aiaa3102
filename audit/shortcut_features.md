# Shortcut-Feature Audit

## Status

**V1 method specification — shallow baselines and ablations are pending.**

## Audit question

Can simple surface features or corpus artifacts explain an unexpectedly large share of spam-classification performance, and are those cues stable enough to support the intended evaluation claim?

## Feature groups

### Message shape

- character count and token count;
- average token length;
- uppercase ratio;
- punctuation and exclamation counts.

### Numeric and contact cues

- digit count and digit ratio;
- phone-like token indicator;
- URL indicator;
- currency symbol indicator;
- short-code or long-number indicator.

### Promotional lexicon

- counts or indicators for terms such as `free`, `win`, `prize`, `claim`, `call`, `urgent` and `reply`;
- lexicon must be declared before evaluating the held-out result.

### Corpus metadata

- normalized `uci_row_number`;
- coarse row-position bins;
- split indicator is never used as a model feature and is tested only as an audit target.

## Models and comparisons

Use an interpretable shallow model, such as standardized Logistic Regression or a small decision tree, with the same train/held-out split.

| Condition | Purpose |
|---|---|
| Full-text TF-IDF | Main performance reference |
| Shape-only | Tests length and punctuation |
| Contact/promotion-only | Tests overt spam markers |
| All shallow features | Public shortcut warning check |
| Row-position-only | Tests corpus-order artifact |
| Text after promotion-token masking | Measures dependence on obvious lexicon |

## Warning rule

The public protocol triggers a shortcut warning when the shallow-only model reaches accuracy >= 0.70 or explains many errors. Because class imbalance can make accuracy misleading, the analysis must also compare against majority-class accuracy and report spam Recall, F1 and macro-F1.

## Result table to complete

| Feature condition | Accuracy | Spam precision | Spam recall | Spam F1 | Macro-F1 |
|---|---:|---:|---:|---:|---:|
| Majority reference | TBD | TBD | TBD | TBD | TBD |
| Full text | TBD | TBD | TBD | TBD | TBD |
| Shape only | TBD | TBD | TBD | TBD | TBD |
| Contact/promotion only | TBD | TBD | TBD | TBD | TBD |
| All shallow | TBD | TBD | TBD | TBD | TBD |
| Row position only | TBD | TBD | TBD | TBD | TBD |
| Masked text | TBD | TBD | TBD | TBD | TBD |

## Interpretation framework

A predictive feature is not automatically an illegitimate shortcut. The final report distinguishes:

- **task-relevant surface cue**: genuine spam often contains contact and promotional language;
- **fragile shortcut**: a cue works in this corpus but can easily change in deployment;
- **collection artifact**: row order or source formatting reflects dataset construction rather than message meaning;
- **direct leakage**: a field exposes the label or split itself.

The strongest shortcut claim requires both predictive evidence and a reason the feature is unreliable or unrelated to the intended decision rule.

## Example-level findings

The `shortcut` rows in `suspicious_examples.csv` should identify representative messages where a shallow cue dominates the prediction, not duplicate a global model-level claim across hundreds of rows. Each row should reference the cue and an ablation or counterfactual result.

## False-positive controls

- Compare shallow accuracy with majority-class accuracy.
- Check precision/recall rather than using accuracy alone.
- Confirm lexicon features were not selected after inspecting held-out labels.
- Test train versus held-out feature prevalence.
- Avoid calling all promotional language leakage.
- Record examples where the same cue appears in both ham and spam.

## Limitations

- Masking tokens changes message meaning as well as shortcut availability.
- A small hand-built lexicon may underestimate broader semantic shortcuts.
- Feature importance is associative and does not prove causal reliance for every prediction.

