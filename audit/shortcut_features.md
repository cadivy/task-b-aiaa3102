# Shortcut-Feature Audit

## Method

The shallow models use only message shape, digits, contact markers, currency cues, promotional-token counts and optionally normalized UCI row position. They never receive the raw word sequence. All conditions use the fixed train/held-out split.

## Performance

| Condition | Accuracy | Spam precision | Spam recall | Spam F1 | Macro-F1 |
|---|---:|---:|---:|---:|---:|
| Majority ham | 86.62% | 0.00% | 0.00% | 0.00% | 46.42% |
| Shape only | 88.96% | 66.25% | 35.57% | 46.29% | 70.07% |
| Contact/promotion only | 98.11% | 95.07% | 90.60% | 92.78% | 95.85% |
| All shallow | 98.20% | 95.10% | 91.28% | 93.15% | 96.06% |
| Row position only | 86.62% | 0.00% | 0.00% | 0.00% | 46.42% |
| Masked promotional tokens | 98.92% | 97.90% | 93.96% | 95.89% | 97.64% |
| Full text | 99.10% | 99.29% | 93.96% | 96.55% | 98.02% |

The public shortcut warning threshold is 70% accuracy, but the majority baseline already reaches 86.62%. The meaningful finding is not threshold crossing alone: contact/promotion features add high spam discrimination and reach 98.11% accuracy with a 92.78% spam F1.

Standardized coefficients for the all-shallow Logistic Regression are led by digit count (2.434), promotional-token count (1.671), average token length (0.740), URL presence (0.666) and currency count (0.636). Row position adds no measurable value.

## Example-level stress cases

- `H0946` is public ham discussing prices. The shallow model gives spam probability 0.991 while the text model gives 0.028: monetary cues produce a clear false positive.
- `H0044` is a ringtone-club solicitation. The shallow model gives 0.088 while the text model gives 0.961: spam without usual digits can evade the cue set.
- `H0287` and `H0318` are premium adult-chat lures. Shallow probabilities are approximately 0.997 and 1.000 while the full text model misses both at the 0.5 threshold.
- `H0491` is a recruitment message labelled ham. Contact details push the shallow spam probability to 0.900, exposing a policy-sensitive boundary.
- `H0896` is a likely label-noise case with almost no shallow spam markers, showing that shortcut errors and label errors interact.

## Interpretation

Digits, phone numbers, price and promotional language are genuinely relevant to SMS spam, so predictive power is not direct leakage. They are nevertheless fragile shortcuts: legitimate price discussions generate false positives, and service promotions without numeric markers generate false negatives.

Promotional-token masking reduces held-out accuracy by only 0.18 percentage points and does not change spam Recall. The full model therefore does not depend on the small hand-built lexicon alone. Broader surface structure and character patterns still carry substantial signal.

## Reproducible evidence

- `results/shortcut_metrics.csv`
- `results/shortcut_coefficients.csv`
- `results/shortcut_predictions.csv`
- `results/figures/shallow_feature_prevalence.png`
- `results/figures/shortcut_metrics.png`

