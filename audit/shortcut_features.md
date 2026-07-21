# Shortcut-Feature Audit

## Scope and Controls

This audit tests whether surface cues explain an excessive share of SMS spam performance. The shallow probes receive only derived numeric features: message shape, digits, currency, URL/phone indicators, promotional-token counts and, in a separate probe, normalized UCI row position. They never receive raw token order. Every learned comparison uses Logistic Regression; numeric probes are standardized, and the `full_text` result is read from the frozen shared held-out predictions rather than retrained.

## Results

| Condition | Accuracy | Spam precision | Spam recall | Spam F1 | Macro-F1 |
|---|---:|---:|---:|---:|---:|
| Majority ham | 86.62% | 0.00% | 0.00% | 0.00% | 46.42% |
| Shape only | 89.50% | 70.00% | 37.58% | 48.91% | 71.53% |
| Contact/promotion only | 98.11% | 95.07% | 90.60% | 92.78% | 95.85% |
| All shallow | 98.20% | 95.10% | 91.28% | 93.15% | 96.06% |
| Row position only | 86.62% | 0.00% | 0.00% | 0.00% | 46.42% |
| All shallow + position | 98.20% | 95.10% | 91.28% | 93.15% | 96.06% |
| Masked promotional tokens | 98.92% | 97.90% | 93.96% | 95.89% | 97.64% |
| Frozen full text | 99.10% | 99.29% | 93.96% | 96.55% | 98.02% |

The protocol's 70% accuracy warning is not meaningful on its own because the majority-ham classifier already reaches 86.62% while detecting no spam. The stronger evidence is that contact/promotion cues alone reach 98.11% accuracy and 92.78% spam F1. Combining all shallow cues reaches 98.20% accuracy and 93.15% spam F1, close to the frozen full-text model's 99.10% accuracy and 96.55% spam F1.

Row position alone reaches 86.62% accuracy and 0.00% spam F1, so corpus order adds no useful spam discrimination. This is evidence against a row-order shortcut.

## Which Cues Matter

The largest absolute standardized coefficients in the all-shallow model are `digit_count` (+2.566), `promo_token_count` (+1.723), `avg_token_length` (+0.760), `has_url` (+0.678), `currency_count` (+0.642), `exclamation_count` (+0.336). Positive coefficients point toward spam; negative coefficients point toward ham. Because inputs are standardized, their magnitudes are comparable within this fitted probe.

## Promotional-Token Stress Test

Masking the fixed 15-token promotional lexicon gives 98.92% accuracy and 95.89% spam F1, versus 99.10% and 96.55% for full text. The small change shows that the baseline is not explained by that lexicon alone, although broader contact and promotional structure remains highly predictive.

## Example-Level Findings

| ID | Confidence | Evidence pattern |
|---|---|---|
| `H0946` | high | Legitimate apartment-price discussion is pushed to spam by eleven digits and three currency markers; this is a clear cue-induced false positive. |
| `H0044` | high | A ringtone-club solicitation has almost none of the usual numeric or contact cues so the shallow model misses clear spam that the text model detects. |
| `H0287` | high | A premium-rate adult-chat lure is recovered mainly from a telephone number and price marker while the full-text baseline remains below threshold. |
| `H0318` | medium | Phone and reply-cost markers drive the shallow probability to nearly one even though the full-text baseline remains below threshold. |
| `H0891` | medium | A mobile-club offer is missed by the shallow probe because it lacks the usual phone currency and promotional-token pattern. |
| `H0076` | medium | A benign chain-message questionnaire contains many digits and a reply cue which causes a shallow false positive despite ordinary conversational context. |
| `H0400` | medium | An informal message about a pay rise contains digits currency and uppercase text which pushes the shallow model over the spam threshold. |
| `H0927` | medium | URL stop and price cues recover a genuine subscription spam message that the frozen full-text baseline narrowly misses. |

These rows are stress cases, not requests to change held-out labels. They show where shallow cues either overwhelm benign context or rescue/miss spam for the wrong reason.

## Rejected Candidates

- `H0143`: The public spam label reads like an ordinary joke; a joint model miss does not isolate a shortcut and is better handled by label adjudication.
- `H0896`: This appears to be a recipient reply rather than an originating promotion so the disagreement is likely label noise rather than shortcut evidence.
- `H0491`: Recruitment advertising with a URL and contact request is policy-sensitive so calling the shallow prediction a false positive would overstate the evidence.
- `H0475`: This message is an exact-text duplicate of H0949 and should not be counted as an independent shortcut example.
- `H0949`: The free-SMS service message is both policy-sensitive and duplicated so it is retained for ambiguity review rather than shortcut ranking.
- `H0814`: The quiz could be a paid service but lacks explicit price or contact evidence; two model misses do not identify a specific shortcut mechanism.
- `H0550`: The generic horoscope-style wording has uncertain label semantics and no strong shallow-versus-text contrast.
- `H0889`: The word call is polysemous but the full-text score is also near the boundary making this weaker than the retained benign hard negatives.

Rejected rows remain in the review ledger so model disagreement is not silently converted into a high-confidence audit claim.

## Interpretation and Limitations

Digits, prices, URLs, telephone numbers and promotional wording are legitimate spam evidence, so their predictive value is not direct leakage. They are shortcuts because they can work without sentence meaning and fail under distribution shift: ordinary price discussions can trigger false positives, while solicitations without familiar numeric markers can be missed. Coefficients describe association, not causation. The held-out labels remain untouched, and possible label-policy cases should be adjudicated jointly with the label-noise audit.

## Reproducible Evidence

- `scripts/audit_shortcuts.py`
- `configs/shortcut_manual_review.csv`
- `results/shortcut/shortcut_metrics.csv`
- `results/shortcut/shortcut_coefficients.csv`
- `results/shortcut/shortcut_predictions.csv`
- `results/shortcut/shortcut_review_queue.csv`
- `results/shortcut/shortcut_findings.csv`
- `results/figures/shortcut_metrics.png`
- `results/figures/shortcut_coefficients.png`
- `results/figures/shortcut_cue_prevalence.png`
