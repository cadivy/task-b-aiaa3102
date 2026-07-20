# Duplicate Analysis

## Method

Exact duplicates use the public rule implemented by `normalize_text()`: lowercase the SMS text and collapse whitespace. Punctuation, numbers, URLs, phone numbers, and entities are intentionally retained.

Near duplicates are retrieved with two deterministic TF-IDF views of the same canonical text: word unigrams/bigrams and character 3-5-grams. Candidate pairs are retrieved from nearest neighbours at a search floor of 0.88; exact duplicate pairs are removed; the main score is `max(word_cosine, char_cosine)`. The protocol threshold is read from `starter/configs/audit_protocol.json`, currently `0.92`.

The script does not finalize near-duplicate adjudication. It writes `results/duplicate/near_duplicate_review_queue.csv` with `review_decision=needs_review` for every protocol-threshold candidate except heldout-heldout pairs. Cross-split status is retained as a column in the queue and candidate tables for later leakage analysis.

## Exact Duplicate Findings

| Finding | Result |
|---|---|
| Exact duplicate clusters | 290 |
| Rows in exact duplicate clusters | 705 |
| Repeated rows beyond first occurrence | 415 |
| Cross-split exact clusters | 5 |
| Exact clusters with label conflict | 0 |
| Largest exact cluster | E0014, size 30 |

The largest cluster is `E0014`, represented by: `Sorry, I'll call later`. A large train-only cluster is a weighting risk rather than held-out leakage: the model sees the same short template many times and may overweight it.

Cross-split exact clusters are evaluation-independence findings because held-out text is already present in training. In this run they do not create label-conflict findings.

| Cluster | Held-out ID | Label(s) | Cluster size |
|---|---|---|---|
| E0009 | H0009 | ham | 2 |
| E0049 | H0548 | spam | 3 |
| E0091 | H0909 | spam | 2 |
| E0164 | H0412 | spam | 2 |
| E0285 | H0922 | spam | 2 |

## Near-Duplicate Threshold Analysis

The public threshold `0.92` sits in the middle of the sensitivity range. Lower thresholds retrieve many more candidates and therefore more generic false-positive risk; higher thresholds are cleaner but miss plausible template variants with formatting, number, or wording substitutions. Reporting the full sensitivity table makes the threshold choice auditable instead of a hidden tuning decision.

| Threshold | Candidate pairs | Cross-split pairs | Unique held-out IDs | Label conflicts |
|---|---|---|---|---|
| 0.88 | 445 | 129 | 82 | 0 |
| 0.90 | 403 | 108 | 75 | 0 |
| 0.92 | 363 | 90 | 65 | 0 |
| 0.94 | 311 | 56 | 45 | 0 |
| 0.96 | 273 | 46 | 38 | 0 |

At `0.92`, the automatic retrieval finds 363 non-exact near-duplicate candidate pairs, including 90 cross-split pairs affecting 65 unique held-out rows. The review queue contains 346 pairs after excluding 17 heldout-heldout pairs that are not useful for training-to-evaluation leakage.

## Human Review Queue

The review queue is `results/duplicate/near_duplicate_review_queue.csv`. Fill these fields during manual review:

- `review_decision`: `accepted`, `rejected_false_positive`, or another documented team value.
- `review_category`: for example `same_template`, `generic_short_text`, `semantic_change`, `insufficient_specificity`.
- `reviewer`, `review_notes`, `recommended_action`, and `confidence`.

Representative highest-scoring initial review candidates before adjudication:

| Pair | IDs | Label(s) | Max cosine | Suggested reason | Decision |
|---|---|---|---|---|---|
| N0174 | T1056 / T4093 | spam | 1.0000 | very_high_similarity_template_review_needed | needs_review |
| N0434 | H0908 / T4439 | spam | 1.0000 | very_high_similarity_template_review_needed | needs_review |
| N0082 | T0388 / T3131 | spam | 1.0000 | very_high_similarity_template_review_needed | needs_review |
| N0297 | T1847 / T3265 | spam | 1.0000 | very_high_similarity_template_review_needed | needs_review |
| N0414 | T3193 / T4050 | spam | 1.0000 | very_high_similarity_template_review_needed | needs_review |
| N0065 | T0279 / T1948 | spam | 1.0000 | very_high_similarity_template_review_needed | needs_review |
| N0110 | T0621 / T2569 | spam | 1.0000 | threshold_candidate_review_needed | needs_review |
| N0227 | T1332 / T2237 | spam | 1.0000 | very_high_similarity_template_review_needed | needs_review |

## Risk Interpretation

- Train-only exact duplicates are weighting risks.
- Cross-split exact duplicates are leakage/evaluation-independence risks.
- Cross-split near duplicates are template-leakage candidates until human review confirms or rejects them.
- Exact or near pairs with label conflict would be label-noise candidates; this run found none at the reported thresholds.

## Reproducible Evidence

- `results/duplicate/exact_duplicate_clusters.csv`
- `results/duplicate/exact_duplicate_members.csv`
- `results/duplicate/near_duplicate_candidates.csv`
- `results/duplicate/near_duplicate_threshold_sensitivity.csv`
- `results/duplicate/near_duplicate_review_queue.csv`
- `results/duplicate/near_duplicate_review_summary.csv`
- `results/duplicate/near_duplicate_review_summary.json`
- `results/duplicate/duplicate_summary.json`
- `results/figures/exact_cluster_sizes.png`

## Near-Duplicate Review Results

The review queue has been adjudicated from the fixed manual decision set embedded in `scripts/review_near_duplicates.py` using `near-duplicate-review-v1.3-manual-ledger` and `near-duplicate-review-policy-v1.0`. The script writes `results/duplicate/near_duplicate_manual_review_decisions.csv` as a reproducible ledger, then merges it into `results\duplicate\near_duplicate_review_queue.csv`; it does not classify pairs with text heuristics. Punctuation-only variants remain near duplicates rather than exact duplicates because the exact-duplicate rule intentionally keeps punctuation.

### Review Policy

The review policy separates objective string repetition from inferred near-duplicate evidence. Exact duplicates are retained whenever the normalized strings are identical, even if the text is a common short reply such as `Sorry, I'll call later`; exact matching is a direct dataset fact. Near duplicates require a higher evidentiary bar because similar wording may come from ordinary language use rather than repeated data.

Near-duplicate pairs are accepted when they appear to be the same substantive SMS, the same spam campaign/template, the same forwarded or template-style ham message, an embedded/transcript variant, or a specific personalized variant with only names, addressees, punctuation, casing, spacing, entities, numbers, URLs, dates, or minor wording changed. They are rejected as false positives when the similarity is only a generic short conversational phrase or acknowledgement without a specific content anchor, or when lexically similar texts have a material semantic change.

This means a common phrase can count as a duplicate when it is exactly repeated, but a non-exact variant of that phrase is not automatically accepted as a near duplicate. For near duplicates, the review asks whether the pair is likely the same source message/template/content, not merely whether the two texts are semantically close.

| Review decision | Pair count |
|---|---|
| accepted | 200 |
| rejected_false_positive | 146 |
| needs_review | 0 |

The expanded queue includes train-train and cross-split candidates, excluding heldout-heldout pairs. Accepted cross-split near duplicates total 85 pairs and affect 60 unique held-out messages. The reviewed sample-level table contains 922 samples involved in either exact duplicates or accepted near duplicates, including 134 samples with cross-split duplicate evidence.

## Scripts And Outputs

| Path | Function / content |
|---|---|
| `scripts/audit_duplicates.py` | Deterministically rebuilds exact duplicate clusters, all near-duplicate candidates, threshold sensitivity, the review queue, and this report. It keeps cross-split status as columns rather than writing a separate cross-split near-candidate file. |
| `scripts/review_near_duplicates.py` | Stores the Codex-assisted manual re-review and review policy as an embedded pair-id decision set, writes `near_duplicate_manual_review_decisions.csv`, merges it into `near_duplicate_review_queue.csv` or `near_duplicate_review_queue_reviewed.csv` if the original file is locked, then writes pair-level and sample-level summaries. |
| `results/duplicate/exact_duplicate_clusters.csv` | One row per exact duplicate cluster after lowercase plus whitespace normalization; includes cluster size, split mix, labels, representative text, and member IDs. |
| `results/duplicate/exact_duplicate_members.csv` | One row per member of each exact duplicate cluster; useful when you need the original row ID, split, label, text, and normalized text. |
| `results/duplicate/near_duplicate_candidates.csv` | All non-exact candidate pairs found above the search floor 0.88, with word/character cosine scores, cross-split status, and a flag for the protocol threshold 0.92. |
| `results/duplicate/near_duplicate_threshold_sensitivity.csv` | Counts at thresholds 0.88, 0.90, 0.92, 0.94, and 0.96; used to justify why 0.92 is a balanced review threshold. |
| `results/duplicate/near_duplicate_review_queue.csv` | The adjudicated review queue: all protocol-threshold candidates except heldout-heldout pairs, including train-train and cross-split pairs, with manual review fields merged in. |
| `results/duplicate/near_duplicate_manual_review_decisions.csv` | Fixed manual decision ledger keyed by `pair_id`; this is the source used to reproduce review decisions without script heuristics. |
| `results/duplicate/near_duplicate_review_summary.csv` | Compact decision-level counts split by decision, cross-split/train-train status, label type, and affected heldout IDs. |
| `results/duplicate/near_duplicate_review_summary.json` | Machine-readable review summary with aggregate counts only; pair ID lists are intentionally omitted. |
| `results/duplicate/reviewed_duplicate_samples.csv` | One row per sample involved in exact duplicates or accepted near duplicates; includes duplicate type, cross-split status, partner IDs, counts, categories, and text. |
| `results/duplicate/duplicate_summary.json` | Machine-readable headline duplicate metrics, including exact duplicate counts, near candidate counts, review queue size, excluded heldout-heldout count, completed review totals, and reviewed sample counts. |
| `results/figures/exact_cluster_sizes.png` | Bar chart of exact duplicate cluster sizes; kept in the shared figures folder because images were not moved into `results/duplicate/`. |
