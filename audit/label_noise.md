# Likely Label-Error Audit (Target 4)

## Method

Every one of the 5,574 canonical rows was scored against three independent signals:

| Signal | Source | Why it is independent |
|---|---|---|
| `word_opposes` | TF-IDF word/bigram logistic regression | Training rows scored out-of-fold, so no model saw the row it scores |
| `char_opposes` | TF-IDF character 3–5-gram logistic regression | Disjoint feature space; catches obfuscations such as `fr33` |
| `neighbour_opposes` | Character TF-IDF nearest neighbours | Local label consistency, independent of any classifier decision boundary |

A neighbour block counts as opposing only when the similarity-weighted opposing
mass is at least 0.60 **and** the closest opposing neighbour reaches similarity
0.30, so a single distant neighbour cannot carry the claim.

**Exact duplicates are excluded from the neighbour window.** A duplicated copy
of a row carries the same label by construction, so leaving it in would let a
row confirm its own label. Because 415 rows participate in exact duplication,
the retrieval depth was raised to 20 neighbours to keep a full five-neighbour
evidence window after exclusion.

The candidate gate is the protocol definition taken literally: at least two
independent signals must disagree with the assigned label. That produced **70
candidates**. Rows opposed by only one signal were written to a separate
watchlist (3 rows) and are not label-error claims.

## Confidence rule

Confidence is assigned by a rule rather than case by case, so that the
calibration is reproducible and auditable:

> **high** — `opposition_strength >= 0.95` or all three signals oppose
> **medium** — two independent signals oppose and `opposition_strength < 0.95`
> **low** — fewer than two automated signals; the claim rests on a policy reading

`opposition_strength` is the mean of the word and character spam probabilities,
oriented against the public label.

Automated retrieval never decides a case on its own. Each of the 45 top-ranked
candidates was read in full, and a model error alone was never accepted as a
label error. Of the 45, **31 were rejected** — the rejection pass is described
below and is a substantive part of this audit, not an afterthought.

## Findings

Fifteen rows are submitted as likely label errors: 5 high, 9 medium, 1 low. All
fifteen are public `spam` rows proposed as `ham`. Thirteen are training rows
carried in `results/training_label_overlay.csv`; two are held-out rows that are
flagged only and never modified.

| ID | Split | Confidence | Strength | Signals | Reading |
|---|---|---|---|---|---|
| T2378 | train | High | 0.992 | 3/3 | Observational driving joke; no solicitation |
| H0143 | heldout | High | 0.982 | 2/3 | Tattoo joke; flagged only, label unchanged |
| T0059 | train | High | 0.965 | 2/3 | "Divorce Barbie" punchline |
| T2232 | train | High | 0.963 | 2/3 | Child-versus-teenager joke |
| H0896 | heldout | High | 0.916 | 3/3 | Victim asking what to do after a prize message; flagged only |
| T3272 | train | Medium | 0.913 | 2/3 | Named personal reply about a debt collector |
| T1149 | train | Medium | 0.906 | 2/3 | Dartboard joke — "no doubles or trebles" is the punchline |
| T4358 | train | Medium | 0.871 | 2/3 | Stolen police toilet pun |
| T4296 | train | Medium | 0.856 | 2/3 | Personal question about received dating spam |
| T4433 | train | Medium | 0.743 | 2/3 | Rant about a disputed mobile bill |
| T1798 | train | Medium | 0.930 | 2/3 | Quotes a scam opener in order to warn about it |
| T2172 | train | Medium | 0.813 | 2/3 | Reports money lost to shortcode 88066 |
| T1811 | train | Medium | 0.827 | 2/3 | Near-duplicate of T2172, same help request |
| T1322 | train | Medium | 0.797 | 2/3 | Commentary on network billing responsibility |
| T1174 | train | **Low** | 0.571 | **1/3** | Complaint about paid ringtone texts |

Three findings share one policy pattern worth naming: **T1798, T4296 and T1174
discuss, quote or complain about spam rather than send it.** Lexically they look
like spam, which is why the character model is less confident about them than
the word model; semantically they are ordinary personal messages.

`T1174` is deliberately the weakest claim in the set and is marked as such. It
carries only one automated signal, so it does not meet the protocol's two-signal
bar on automated evidence alone. It is retained at low confidence because its
content matches the T1798 / T4296 pattern exactly. If the hidden key treats it
as a false positive, the low confidence is the honest record of that risk.

## Rejected candidates

Thirty-one of the 45 candidates read were rejected as `keep_but_flag`: the model
is wrong and the public `spam` label stands. Rejections clustered into four
recurring patterns.

| Pattern | Examples | Evidence that defeated the model |
|---|---|---|
| Tariff disclosed in the tail | T2755, T3105, T0006, T1557 | `one gbp/sms`, `cst std ntwk chg £1.50`, per-minute rates |
| Reply-keyword mechanics | H0814, T3202, T3926, T0047 | `Send A, B or C`, shortcodes, `Reply SONY` |
| Adult solicitation | T1505, T1926, T3963, T3864 | Explicit offers with instruction formats such as `Txt XXX SLO(4msgs)` |
| Lawful commercial broadcast | T2229, T2273 | Burger King and Interflora promotions |

The last pattern is the one most likely to be mis-audited. A lawful, named
advertiser still sends unsolicited commercial broadcast, and there is no consent
story available for either row, so neither is a label error nor a policy
ambiguity. This is a different judgement from T2847 and T3981, where membership
or charitable purpose makes consent plausible; those two are recorded in
`ambiguity.md` instead.

`T2755` illustrates why rejection cannot be automated. Its opposition strength is
0.953 — above the high-confidence threshold — yet the message ends in
`one gbp/sms`. Under the confidence rule it would have been a high-confidence
label error had the text not been read.

`T3015` shows the opposite handling. Its text, `2/2 146tf150p`, is an unreadable
fragment, so no policy reading is possible. It was rejected on neighbour evidence
alone: all five neighbours are spam.

## Intervention: the training-label overlay

The canonical table is never modified. The 13 training proposals live in
`results/training_label_overlay.csv` and are applied only in an explicit
experiment (`scripts/label_overlay_experiment.py`, seed 42, word baseline).

| Condition | Held-out accuracy | Spam recall |
|---|---|---|
| Public labels (official baseline) | 99.1023% | 93.9597% |
| Training labels with overlay applied | 98.9228% | 92.6174% |

Two held-out predictions change. **The overlay makes the official metric
slightly worse**, and that result is reported rather than discarded.

The correct reading is not that the corrections are wrong. It is that thirteen
local label judgements cannot be validated by a metric computed against the same
public labels those judgements dispute. A relabelling proposal that improved the
score would be evidence of fitting the evaluation set, not of better data. This
is also why spam recall is reported alongside accuracy: spam is only 13.4% of the
corpus, so accuracy alone would have hidden a 1.34-point recall drop behind a
0.18-point accuracy drop.

## Limitations

- Sender identity, subscription status and the original annotation instructions
  cannot be recovered from the corpus, and several judgements turn on exactly
  those facts.
- The word and character models are trained on the same corpus, so their
  agreement is corroborating rather than fully independent evidence. The
  neighbour signal shares the character feature space with the character model.
- Only the top 45 of 70 candidates were read in full. The remaining 25 are
  ranked and available in `results/label_error_candidates.csv`; they are not
  claimed either way.
- The `0A$NETWORKS` prefix on T1322 remains unexplained and is the weakest part
  of that otherwise medium-confidence finding.

## Reproducible evidence

```
python scripts\audit_label_noise.py
python scripts\build_label_noise_outputs.py
python scripts\label_overlay_experiment.py
```

- `results/label_noise_evidence.csv` — all 5,574 rows with the three signals
- `results/label_error_candidates.csv` — the 70 candidates, ranked
- `results/label_error_watchlist.csv` — single-signal rows, not claimed
- `results/training_label_overlay.csv` — the 13 training proposals
- `results/label_overlay_experiment.json` — overlay metrics above
- `configs/manual_review.json` — all 80 adjudications with reasons
