# Adjudication Protocol and Decision Record

## Purpose

This protocol converts high-recall automated candidates into calibrated audit claims. It prevents two common errors: treating every model error as a label error and treating every TF-IDF threshold crossing as shared-source leakage.

## Actual review design

This repository was completed through an explicitly AI-assisted workflow. It uses two separate passes:

1. **Evidence pass:** inspect model probabilities, nearest neighbours, duplicate clusters, similarity values and shallow-feature counterexamples.
2. **Policy pass:** read the original text without using score improvement as a decision rule and apply the written ham/spam policy boundary.

These passes reduce confirmation bias but are not represented as two independent human annotators. No human agreement statistic is reported. Every memo row contains the review-status disclosure.

## Claim-level decision categories

### `should_fix`

The evidence supports a concrete dataset or split action. Examples include confirmed cross-split leakage and a training label supported by model evidence plus a clear policy reading.

### `keep_but_flag`

The row remains in the public dataset but should be marked in interpretation, such as a repeated template, shortcut stress case or held-out label concern that cannot be edited.

### `ambiguous_policy_case`

Both labels remain plausible because consent, sender relationship or campaign context is missing. The action is policy clarification, not forced relabeling.

### `false_positive_audit_finding`

The automated method retrieves a candidate, but original-text review rejects the issue claim. These rows remain visible to document precision control.

## Evidence requirements

### Exact duplicate

- Identical after lowercasing and whitespace collapse.
- Stable cluster ID and members recorded.

### Near duplicate

- Primary word or character TF-IDF cosine at least 0.92.
- Not exact under the official normalization.
- Text comparison supports a shared distinctive template.
- Generic short phrases or semantic reversals may be rejected despite the threshold.

### Leakage

- A specific held-out ID links to a specific training ID through an accepted exact/near relationship.
- Generic vocabulary overlap is insufficient.

### Label error

- At least one automated signal such as OOF model opposition, representation-diverse agreement or neighbour inconsistency.
- A separate policy reading that explains why the alternative label better fits the message.
- Performance improvement is never used as proof.

### Shortcut

- An example-level shallow/full-model contrast or a reproducible global shallow baseline.
- The explanation distinguishes a task-relevant cue from a fragile corpus shortcut.

### Ambiguous

- A named missing context or annotation-policy boundary.
- Low probability margin alone is rejected as evidence.

## Confidence calibration

- **High:** direct definitional evidence, a reproducible quantitative value and no unresolved counterexample.
- **Medium:** multiple supporting signals, but the result depends on threshold, context or policy interpretation.
- **Low:** deliberately retained weak/rejected candidate that illustrates uncertainty or false-positive control.

The final audit contains 26 high-confidence claims among 51 rows, or 51.0%, below the public 55% maximum.

## Final memo schema

`adjudication_memo.csv` uses:

```text
claim_id,id,split,issue_type,current_label,automated_evidence,policy_review,
final_decision,final_confidence,recommended_action,final_reason,review_status
```

The memo has one row for every ranked audit claim and uses only the four public decision categories.

## Preserved false positives

The final evidence explicitly preserves:

- the `T1881`/`H0850` near pair, where word cosine is 1.0 but the decisive word reverses from “affectionate” to “hostile”;
- a generic short acknowledgement retrieved as cross-split near duplication but rejected as leakage;
- `H0935`, whose model probabilities straddle the boundary although the message is ordinary ham.

These cases show that the audit did not maximize candidate count by promoting weak signals.

## Label safety

- The canonical public labels are never overwritten.
- No held-out label is modified.
- Nine proposed training corrections are stored in `results/training_label_overlay.csv`.
- Overlay effects are reported as sensitivity analysis rather than recovered truth.

## Independent human follow-up

For academic submission, the team can strengthen the subjective portion by independently reading the 11 likely label-error and seven genuine ambiguity cases. If human decisions differ from the current policy pass, update `configs/manual_review.json`, rerun the complete pipeline and report the change. The present repository does not fabricate that step.
