# Cross-Split Leakage Audit

## Status

**V1 method specification — leakage cases and corrected evaluation are pending.**

## Definition

A leakage claim is made when a held-out message is an exact or accepted near duplicate of a training message, or when a metadata artifact directly exposes the label or split. General vocabulary overlap is not sufficient.

## Threat model

The held-out set is intended to measure generalization to unseen examples. If the same underlying message template appears in training, the model can succeed through memorization. The resulting score may be numerically correct for the fixed file but optimistic for the intended generalization claim.

## Detection procedure

1. Build exact clusters across the full corpus without using labels.
2. Flag each cluster containing both train and held-out IDs.
3. For every held-out row, retrieve the most similar training rows.
4. Retain non-exact pairs meeting the near-duplicate rule and manual review.
5. Test whether row position or another metadata field directly predicts split or label.
6. Link every leakage row to a concrete training source ID.

Required output fields:

```text
heldout_id,train_id,match_type,similarity,heldout_label,train_label,
cluster_id,manual_decision,evaluation_action
```

## Severity categories

### High

Exact cross-split match or a near-identical message with only substituted contact/entity fields, supported by direct text comparison.

### Medium

Similarity meets the threshold and likely shares a template, but independent generation remains plausible.

### Low

Threshold-boundary candidate or suspected metadata artifact requiring more evidence.

## Evaluation impact

Run the same fitted-model evaluation on:

1. the original held-out set;
2. held-out rows excluding confirmed cross-split exact matches;
3. held-out rows excluding confirmed exact and near matches;
4. an optional cluster-aware rebuilt split.

| Evaluation set | N | Accuracy | Spam precision | Spam recall | Spam F1 | Macro-F1 |
|---|---:|---:|---:|---:|---:|---:|
| Original held-out | TBD | TBD | TBD | TBD | TBD | TBD |
| Excluding exact leakage | TBD | TBD | TBD | TBD | TBD | TBD |
| Excluding exact + near leakage | TBD | TBD | TBD | TBD | TBD | TBD |
| Cluster-aware split | TBD | TBD | TBD | TBD | TBD | TBD |

The primary interpretation is not “cleaning improves the score.” If the score decreases after removing leakage, that is evidence that the original evaluation was easier and potentially optimistic.

## Evidence to show

- number and class composition of affected held-out rows;
- representative high-confidence train/held-out pairs;
- performance contribution of leaked versus non-leaked subsets;
- false-positive near matches rejected during manual review;
- whether leakage changes model ranking or only absolute scores.

## Recommended actions

- Do not silently delete held-out cases from the official score.
- Report the official score and a leakage-aware sensitivity score side by side.
- For a rebuilt experiment, group exact/near duplicate clusters before splitting.
- Preserve the original IDs and mapping so every removal is auditable.

## Limitations

- Removing detected leakage only addresses leakage visible to the chosen similarity method.
- A cluster-aware split may change class composition and sample size.
- A near-duplicate relationship can represent a realistic recurring production template; its treatment depends on the intended deployment claim.

