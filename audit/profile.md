# Dataset Profile

## 1. Provenance and Integrity

The profile uses `data/canonical_sms.csv`, loaded through `load_canonical()` with `keep_default_na=False` so literal SMS strings such as `NA`, `null`, or `nan` are not silently converted to missing values. The canonical table is the same public working table used by the downstream duplicate, leakage, label-noise, and shortcut audits.

| Check | Result |
|---|---:|
| Total rows | 5574 |
| Train rows | 4460 |
| Held-out rows | 1114 |
| Unique IDs | 5574 |
| Unique UCI row numbers | 5574 |
| Empty text rows | 0 |
| Decoded encoding | utf-8 |

The UCI archive SHA-256 is `1587ea43e58e82b14ff1f5425c88e17f8496bfcdb67a583dbff9eefaf9963ce3`. The extracted raw file SHA-256 is `7d039a24a6083ed9ef0f806ebad56bbb976e3aeb8de05669173bfdc4996c239d`. The join against the fixed manifest preserves the official split and does not regenerate row assignments.

## 2. Split and Class Balance

| Split | Ham | Spam | Total | Spam share |
|---|---:|---:|---:|---:|
| Train | 3862 | 598 | 4460 | 13.41% |
| Held-out | 965 | 149 | 1114 | 13.38% |
| All | 4827 | 747 | 5574 | 13.40% |

Train and held-out have nearly identical spam prevalence, so the fixed split is not visibly shifted in its label prior. The strong class imbalance still matters: because spam is only 13.40% of the corpus, later model summaries should emphasize spam recall, spam F1, and macro-F1 rather than accuracy alone.

## 3. Message Length and Surface Cues

| Quantity | Ham | Spam |
|---|---:|---:|
| Median characters | 52 | 149 |
| Median tokens | 11 | 27 |
| Median digits | 0 | 16 |
| Contains URL | 0.29% | 18.47% |
| Contains phone-like number | 0.10% | 60.78% |
| Contains currency cue | 0.62% | 38.15% |
| Contains promotional token | 9.16% | 87.55% |
| Over 160 characters | 4.47% | 8.30% |
| Mean promotional-token count | 0.10 | 2.14 |

Spam messages are much longer and have far stronger contact, currency, digit, and promotional cues. This is a descriptive profile finding, not by itself a claim that labels are wrong. It motivates the separate shortcut audit.

## 4. Train/Held-out Comparability Beyond Labels

| Metric | Train | Held-out |
|---|---:|---:|
| `char_median` | 62 | 60 |
| `has_url_rate` | 2.69% | 2.87% |
| `has_phone_rate` | 8.07% | 8.89% |
| `has_promo_rate` | 19.91% | 18.67% |
| `over_160_chars_rate` | 5.27% | 3.86% |

The held-out set is broadly similar to train on these coarse surface metrics. The most important visible difference is slightly higher phone-like-number prevalence in held-out, which is useful context when interpreting spam recall on the fixed split.

## 5. Duplicate Overview

Applying the public exact-duplicate rule through `normalize_text()` leaves 5159 unique normalized texts. That means 415 rows are repetitions beyond the first occurrence.

| Metric | Result |
|---|---:|
| Exact duplicate clusters | 290 |
| Rows in exact duplicate clusters | 705 |
| Cross-split exact clusters | 5 |
| Exact clusters with label conflict | 0 |
| Largest exact cluster size | 30 |

This section is only a profile-level overview. The full cluster lists, near-duplicate search, threshold sensitivity, and manual accept/reject decisions belong in `audit/duplicates.md` and `audit/leakage.md`.

## 6. Row Position and Encoding Artifacts

The original UCI row position was checked by decile. Spam prevalence ranges from 11.67% to 15.80% across deciles, so row position does not show a strong label leak in this profile pass.

| Artifact type | Rows | Rate | Example IDs |
|---|---:|---:|---|
| `html_escape` | 309 | 5.54% | T0026|H0007|T0044|T0048|T0067 |
| `replacement_character` | 0 | 0.00% | - |
| `mojibake_marker` | 0 | 0.00% | - |
| `non_ascii` | 483 | 8.67% | T0006|T0009|T0013|T0019|T0020 |

HTML escapes and non-ASCII characters are retained because they are part of the released corpus. The profile stage records them rather than cleaning them away, so later scripts continue to audit the same public text.

## 7. Implications for the Audit

The data foundation is internally consistent, but three properties shape the rest of the audit: spam is a minority class, spam has strong surface cues, and repeated normalized texts are common. The next steps should therefore keep duplicate/leakage findings separate from shortcut findings, and should avoid interpreting high accuracy without class-specific metrics and leakage-aware sensitivity checks.

## Reproducible Evidence

- `results/data_provenance.json`
- `results/data_validation.json`
- `results/profile/profile_summary.csv`
- `results/profile/split_comparison.csv`
- `results/profile/encoding_artifact_summary.csv`
- `results/profile/row_position_spam_rate.csv`
- `results/profile/shallow_features.csv`
- `results/figures/class_distribution.png`
- `results/figures/length_distribution.png`
- `results/figures/shallow_feature_prevalence.png`
- `results/figures/row_position_spam_rate.png`
