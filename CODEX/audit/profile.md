# Dataset Profile and Baseline

## Data integrity

The official UCI archive was downloaded from the URL in the starter package. Its SHA-256 is `1587ea43e58e82b14ff1f5425c88e17f8496bfcdb67a583dbff9eefaf9963ce3`; the extracted `SMSSpamCollection` SHA-256 is `7d039a24a6083ed9ef0f806ebad56bbb976e3aeb8de05669173bfdc4996c239d`.

The raw file decoded as UTF-8 and contained 5574 rows. A one-to-one join against the fixed 1-based manifest produced 5574 unique course IDs with no empty texts, missing joins, prefix errors, or unexpected labels.

| Split | Ham | Spam | Total | Spam share |
|---|---:|---:|---:|---:|
| Train | 3862 | 598 | 4460 | 13.41% |
| Held-out | 965 | 149 | 1114 | 13.38% |
| All | 4827 | 747 | 5574 | 13.40% |

The near-identical class proportions mean the fixed split is not materially shifted in its label prior.

## Message profile

Spam messages are substantially longer and contain much stronger numeric/contact cues.

| Quantity | Ham | Spam |
|---|---:|---:|
| Median characters | 52 | 149 |
| Median tokens | 11 | 27 |
| Median digits | 0 | 16 |
| Contains URL | 0.29% | 18.47% |
| Contains phone-like number | 0.10% | 60.78% |
| Contains currency cue | 0.62% | 38.15% |
| Mean promotional-token count | 0.10 | 2.14 |

The original-row spam rate ranges from 11.67% to 15.80% across position deciles. This fluctuation does not make row position useful by itself: the row-position-only classifier predicts the majority class for every held-out row.

Whitespace-collapse and lowercasing leave 5159 unique normalized texts, so 415 rows beyond the first occurrence are repetitions. This motivated cluster-aware analysis before interpreting the high baseline score.

## Baseline models

The primary model is word TF-IDF over unigrams and bigrams followed by Logistic Regression. The secondary model uses character TF-IDF 3-5-grams. Training results are five-fold out-of-fold (OOF); held-out results use models fitted on all 4460 training rows.

| Condition | Accuracy | Spam precision | Spam recall | Spam F1 | Macro-F1 |
|---|---:|---:|---:|---:|---:|
| Word TF-IDF, train OOF | 98.21% | 99.24% | 87.29% | 92.88% | 95.93% |
| Character TF-IDF, train OOF | 98.27% | 99.43% | 87.63% | 93.16% | 96.08% |
| Word TF-IDF, held-out | 99.10% | 99.29% | 93.96% | 96.55% | 98.02% |
| Character TF-IDF, held-out | 98.74% | 99.27% | 91.28% | 95.10% | 97.19% |

The word baseline makes 10 held-out errors: nine public spam rows predicted ham and one public ham row predicted spam. Two of those ten errors (`H0143` and `H0896`) are independently flagged as likely label-policy errors, showing why raw accuracy alone is not an adequate quality measure.

## Interpretation

The raw 99.10% held-out accuracy is a strong file-level result, but three findings limit its interpretation:

1. held-out messages are not all independent of training because exact and near templates cross the split;
2. shallow contact and promotional features alone reach 98.20% accuracy;
3. several errors lie on annotation-policy boundaries or are likely public-label errors.

The appropriate claim is therefore not “the task is solved.” It is that a simple text model scores highly on this fixed corpus, while audit-aware analyses are necessary to estimate how much of that score reflects robust generalization.

## Reproducible evidence

- `results/data_provenance.json`
- `results/data_validation.json`
- `results/profile_summary.csv`
- `results/shallow_features.csv`
- `results/baseline_metrics.csv`
- `results/oof_predictions.csv`
- `results/heldout_predictions.csv`
- `results/figures/class_distribution.png`
- `results/figures/length_distribution.png`

