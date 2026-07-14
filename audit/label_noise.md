# Likely Label-Error Audit

## Method

Training rows were scored with five-fold out-of-fold word and character models; held-out rows were scored by models fitted only on training. Character TF-IDF nearest neighbours supplied a separate local-consistency signal. Automated retrieval produced 73 candidates.

A final label-error claim required at least two independent evidence sources. In practice each submitted case combines model/neighbor evidence with a policy-based reading of the original text. A model error by itself was never accepted as a label error.

## Adjudicated findings

Eleven rows are included as likely label errors: seven high-confidence and four medium-confidence. Nine are training rows represented in a separate overlay; two are held-out rows that remain unchanged.

| ID | Public label | Proposed interpretation | Confidence | Main reason |
|---|---|---|---|---|
| T2378 | spam | ham | High | Standalone driving joke, no solicitation |
| T0059 | spam | ham | High | “Divorce Barbie” joke, no action or charge |
| T2232 | spam | ham | High | Child/teenager joke, no commercial intent |
| T4358 | spam | ham | High | Stolen-toilet joke |
| T1149 | spam | ham | High | Arsenal dartboard joke |
| T3791 | ham | spam | High | Unsolicited social-platform promotion with opt-out |
| H0143 | spam | ham-like | High | Tattoo joke; held-out label not changed |
| T1798 | spam | ham | Medium | Warns recipient about a scam rather than soliciting |
| T4296 | spam | ham | Medium | Discusses received dating spam |
| T3272 | spam | ham | Medium | Personal debt-collection update |
| H0896 | spam | ham-like | Medium | Reads as a recipient response to a prize message |

For example, `T2378` has OOF spam probabilities 0.009 (word) and 0.008 (character), ham-labelled neighbours, and text that is plainly an observational joke. Conversely, `T3791` promotes a free-SMS contact platform and gives an opt-out instruction; both OOF models predict spam despite its public ham label.

## Rejected and downgraded candidates

Several high-loss spam rows were not reclassified because the public spam interpretation remains defensible:

- `H0814` is a quiz with a required reply; lack of an explicit price does not make it ham.
- `T2755` contains `one gbp/sms`, so the personal-sounding opening is a paid service lure.
- `T1505`, `T2793` and `T1926` imitate personal adult messages but contain service, number or charge evidence.
- `T1020`/`T4039` are duplicated job-description notifications. Their bulk-recruitment appearance is policy-sensitive, so `T1020` is treated as ambiguous rather than corrected.

This rejection step prevents the conservative text model's false negatives from becoming bulk relabels.

## Intervention policy

The canonical table is unchanged. The nine training proposals are stored in `results/training_label_overlay.csv` and applied only in the explicit overlay experiment. The two held-out cases are analysis flags only.

The overlay changes held-out Accuracy from 99.10% to 98.92% and leaves spam Recall at 93.96%; two predictions change. A lower score does not invalidate the proposed corrections. It shows that nine local label judgments do not improve this model's official held-out metric and should not be justified by performance chasing.

## Limitations

The audit cannot recover sender consent or the original annotation instructions. Word and character models share the same corpus, so their agreement is supporting rather than definitive evidence. The policy pass was AI-assisted and is not represented as independent human annotation; this remains a disclosure and a recommended team verification step.

## Reproducible evidence

- `results/label_noise_evidence.csv`
- `results/label_error_candidates.csv`
- `results/training_label_overlay.csv`
- `configs/manual_review.json`
- `adjudication_memo.csv`

