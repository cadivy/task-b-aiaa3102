# Exact and Near-Duplicate Audit

## Status

**V1 method specification — candidate pairs and cluster results are pending.**

## Audit questions

1. Which messages are exact duplicates under the public normalization rule?
2. Do duplicate clusters cross splits or contain conflicting labels?
3. Which non-exact pairs are genuine near duplicates at the protocol threshold?
4. Which high-similarity candidates are false positives, and why?

## Exact-duplicate method

The protocol defines an exact duplicate as identical text after lowercasing and whitespace collapse. No punctuation removal, stemming or phone-number masking is included in the primary exact rule because those transformations can merge meaningfully different messages.

For each cluster, record:

```text
cluster_id,normalized_text,cluster_size,member_ids,splits,labels,
is_cross_split,has_label_conflict
```

Clusters should be ranked by evaluation risk:

1. cross-split and label conflict;
2. cross-split with consistent labels;
3. within-split label conflict;
4. large within-split repeated clusters;
5. small benign repetitions.

## Near-duplicate method

Use TF-IDF cosine similarity over the canonical text. The primary public threshold is 0.92. Exact pairs are removed before generating the near-duplicate table.

For each pair, save:

```text
id_1,id_2,split_1,split_2,label_1,label_2,cosine_similarity,
key_text_difference,manual_decision,manual_reason
```

The final report will show a threshold sensitivity table:

| Threshold | Candidate pairs | Manually accepted | Rejected | Estimated precision |
|---:|---:|---:|---:|---:|
| 0.88 | TBD | TBD | TBD | TBD |
| 0.90 | TBD | TBD | TBD | TBD |
| 0.92 | TBD | TBD | TBD | TBD |
| 0.94 | TBD | TBD | TBD | TBD |
| 0.96 | TBD | TBD | TBD | TBD |

The protocol threshold remains the primary output criterion; the surrounding thresholds are diagnostic and justify the false-positive tradeoff.

## Evidence standard

An accepted near duplicate needs all of the following:

- cosine similarity >= 0.92;
- not exact under the specified normalization;
- the full messages share the same underlying communicative template or event;
- differences are plausibly edits, substituted entities or formatting variations rather than generic shared words.

## Expected false positives

Likely traps include:

- very short messages sharing one common phrase;
- unrelated promotions sharing words such as “free”, “call” or “win”;
- messages dominated by the same phone number or URL but with different intent;
- personal messages using common greetings;
- two messages with high bag-of-words similarity but opposite negation or action.

At least three rejected candidates should be documented to demonstrate precision control.

## Results to complete

| Finding | Count |
|---|---:|
| Exact clusters | TBD |
| Rows in exact clusters | TBD |
| Exact clusters crossing splits | TBD |
| Exact clusters with label conflict | TBD |
| Accepted near-duplicate pairs | TBD |
| Accepted near pairs crossing splits | TBD |
| Reviewed false-positive candidates | TBD |

Representative findings must show stable IDs and concise text excerpts. The report should avoid reproducing unnecessary personal information from messages.

## Recommended actions

- Cross-split clusters: rebuild evaluation by cluster or exclude leakage cases in a sensitivity analysis.
- Conflicting-label clusters: review the whole cluster before any training overlay.
- Benign repeated training templates: consider cluster-aware weighting or deduplication.
- Weak near candidates: keep as false-positive audit findings rather than forcing them into a stronger category.

## Limitations

- TF-IDF similarity is representation-dependent and misses semantic paraphrases.
- Similar messages are not always duplicates; common commercial templates can be independent observations.
- Duplicate removal changes the empirical deployment question, so both original and cluster-aware results should be reported.

