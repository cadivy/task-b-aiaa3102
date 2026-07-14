# Exact and Near-Duplicate Audit

## Exact duplicates

The public exact rule was applied literally: lowercase each message and collapse whitespace. Punctuation, numbers and entities were not removed.

| Finding | Result |
|---|---:|
| Exact clusters | 290 |
| Rows belonging to exact clusters | 705 |
| Cross-split exact clusters | 5 |
| Exact clusters with label conflict | 0 |
| Largest cluster | 30 training rows |

The largest cluster is `E0014`, containing 30 copies of “Sorry, I'll call later.” It does not cross the split, but treating 30 identical texts as independent gives one short template disproportionate training weight.

Five exact clusters cross train and held-out:

| Cluster | Held-out ID | Example class | Cluster size |
|---|---|---|---:|
| E0009 | H0009 | ham | 2 |
| E0049 | H0548 | spam | 3 |
| E0091 | H0909 | spam | 2 |
| E0164 | H0412 | spam | 2 |
| E0285 | H0922 | spam | 2 |

All five have consistent labels, so they are not label-conflict findings. They are evaluation-independence findings: the held-out text already occurs in training.

## Near-duplicate search

Candidates were retrieved from word and character TF-IDF nearest-neighbour searches. A pair was eligible when the larger TF-IDF cosine similarity was at least the public 0.92 threshold and the texts were not exact under the official normalization.

| Threshold | Candidate pairs | Cross-split pairs | Label conflicts |
|---:|---:|---:|---:|
| 0.88 | 443 | 129 | 0 |
| 0.90 | 401 | 108 | 0 |
| 0.92 | 361 | 90 | 0 |
| 0.94 | 309 | 56 | 0 |
| 0.96 | 271 | 46 | 0 |

The 0.92 result contains 90 cross-split pairs. Evidence-and-policy review accepted 84 as shared templates and rejected six as leakage claims. The accepted pairs affect 59 unique held-out IDs; some held-out messages match more than one training variant.

Representative accepted cases include:

- `H0470` versus `T1013`: identical urgent-call template with a substituted phone number;
- `H0548` versus `T4090`: the same mobile-upgrade promotion with one inserted character;
- `H0738` versus `T0218`: the same video-handset promotion with a small wording change;
- `H0311` versus `T0885`: the same guaranteed-prize message with formatting changes.

## False-positive traps

Threshold crossing was not treated as sufficient evidence of a common source.

- `T1881` says “That seems unnecessarily affectionate,” whereas `H0850` replaces the final word with “hostile.” Word TF-IDF cosine is 1.0 because the shared words dominate, but the semantic judgment reverses. This pair was explicitly rejected.
- `T2085`/`H0531` and `H0924`/`T3761` are very short generic acknowledgements. They may recur independently and were rejected as leakage even though punctuation-insensitive word features produce very high similarity.
- Two generic “thanks” candidates and one shared “gym” phrase were also rejected for insufficient event-specific evidence.

This is the main reason the audit reports both retrieval counts and adjudicated counts. A numeric threshold provides reproducibility; text comparison protects precision.

## Recommended treatment

- Preserve the official split for the public reference score.
- Report leakage-aware sensitivity metrics alongside it.
- For a rebuilt benchmark, assign exact and accepted near-duplicate templates to one split as a cluster.
- Deduplicate or cluster-weight repeated training rows when estimating generalization to novel messages.
- Keep rejected pairs in the evidence table to demonstrate false-positive control.

## Reproducible evidence

- `results/exact_duplicate_clusters.csv`
- `results/exact_duplicate_members.csv`
- `results/near_duplicate_candidates.csv`
- `results/near_duplicate_threshold_sensitivity.csv`
- `results/near_duplicate_adjudication.csv`
- `results/figures/exact_cluster_sizes.png`

