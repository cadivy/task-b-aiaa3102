# Ambiguity and Annotation-Policy Audit

## Definition

Ambiguity is reserved for messages where both ham and spam remain reasonable under missing consent, sender relationship or campaign context. It is not a synonym for low model confidence. Candidate retrieval used model disagreement, near-boundary probability and mixed-label neighbours; the final decision used a separate policy reading.

## Findings

Eight ambiguity claims appear in the ranked audit: seven medium-confidence policy cases and one low-confidence rejected candidate.

| ID | Public label | Decision | Policy boundary |
|---|---|---|---|
| T2139 | spam | Ambiguous | Personal flirtation versus adult-chat lure |
| T2710 | spam | Ambiguous | Personal missed-call follow-up versus premium-number lure |
| T0702 | spam | Ambiguous | Expected research recruitment versus unsolicited promotion |
| T3981 | spam | Ambiguous | Charity fundraising versus billable promotion |
| T2847 | spam | Ambiguous | Expected club notice versus ticket advertising |
| T1020 | ham | Ambiguous | Recruiter follow-up versus bulk recruitment message |
| H0949 | ham | Ambiguous | Known-contact social invitation versus website promotion |
| H0935 | ham | False positive | Ordinary statement; model uncertainty only |

`H0935` (“I liked the new mobile”) is deliberately retained as a false-positive audit finding. Its word and character probabilities straddle 0.5, but the content is ordinary ham. This demonstrates that predictive uncertainty is neither label error nor semantic ambiguity by itself.

## Effect on score interpretation

The word baseline makes ten held-out errors. Two errors (`H0143` and `H0896`) are separately judged likely public-label errors, while other false negatives such as paid chat and quiz messages remain defensible spam. If the two likely label-policy errors are treated as unresolved rather than model failures, the file-level error count changes from 10 to 8, corresponding to a sensitivity accuracy of 99.28% rather than 99.10%.

This 99.28% value is not a corrected official score. It is a boundary analysis showing that two examples account for 20% of the baseline's apparent held-out errors. The official public-label metric remains 99.10%.

## Recommended policy clarification

A future annotation guide should explicitly state how to handle:

- opted-in service and club notifications;
- charity and socially beneficial campaigns;
- recruitment or product-trial invitations;
- messages that quote, discuss or warn about spam;
- personal-sounding messages containing premium-rate numbers;
- automated contact-list and social-platform invitations.

Where consent or sender context cannot be recovered, `uncertain` or a second-stage policy label would be more honest than forcing every message into ham/spam.

## Review limitation

The evidence and policy passes were performed in an AI-assisted workflow and logged as such. No fabricated inter-annotator agreement or Cohen's kappa is reported. Independent human verification would strengthen these policy judgments but is not falsely claimed in this repository.

## Reproducible evidence

- `results/ambiguity_candidates.csv`
- `results/label_noise_evidence.csv`
- `configs/manual_review.json`
- `adjudication_memo.csv`

