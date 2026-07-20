# Ambiguity and Annotation-Policy Audit (Target 6)

## Definition

Ambiguity is reserved for messages where **both `ham` and `spam` remain
defensible** once the missing context is acknowledged — sender relationship,
subscription status, or campaign purpose. It is not a synonym for low model
confidence, and this audit treats the two as separate phenomena that happen to
overlap.

The distinction matters because the obvious retrieval strategy — take everything
near the 0.5 decision boundary — measures the classifier, not the annotation
guideline.

## Retrieval

Candidates were drawn from two pools and then read manually:

- **177 rows** flagged by boundary proximity, word/character model disagreement,
  or mixed-label neighbourhoods (`results/ambiguity_candidates.csv`);
- the **70 label-error candidates**, because a row can be opposed by two signals
  and still be a policy question rather than an error.

Eighty rows were read in total. The result is worth stating plainly:

> **Ten of the fourteen ambiguity findings came from the label-error pool, not
> from the boundary pool.** Only four came from rows where the models were
> genuinely uncertain.

This is direct evidence that semantic ambiguity and predictive uncertainty are
different properties. The two strongest cases below, T2139 and T2710, have
opposition strengths of 0.987 and 0.951 with all three signals opposing — the
models are not uncertain about them at all. They are still policy questions.

## Findings

Fourteen rows are submitted as `ambiguous`: 13 medium and 1 low.

| ID | Split | Public label | Policy boundary |
|---|---|---|---|
| T2139 | train | spam | Personal flirtation vs adult-chat lure; no price, shortcode or premium number |
| T2710 | train | spam | UK `070` number, no tariff — personal follow-me range vs premium redirect |
| T3390 | train | spam | Missed-call alert quoting a `070` number, no tariff |
| H0550 | heldout | spam | `ROMCAPspam` prefix may be campaign residue or a corpus artifact; body is ordinary warm chat |
| T0774 | train | spam | Truncated adult-content teaser; no tariff or number survives in the row |
| T0702 | train | spam | Product-trial recruitment requesting address and date of birth |
| T2847 | train | spam | Club ticket notice — plausible member opt-in |
| T3981 | train | spam | UNICEF disaster appeal — charitable carve-out |
| T1951 | train | spam | Personal web page shared for opinions; `1/1` marks a single-part message |
| T3461 | train | spam | Meta commentary demonstrating an anonymous SMS service |
| T2758 | train | spam | Service onboarding asking age and gender — user-initiated vs cold enrolment |
| T3123 | train | spam | Picture link with no tariff — photo-sharing notice vs marketing |
| H0030 | heldout | spam | Teaser URL campaign with no price, number or reply keyword |
| T2658 | train | spam | Truncated fragment reading as a personal thank-you (low confidence) |

Three groupings carry most of the argument.

**The `070` pair (T2710, T3390).** UK `070` is a personal follow-me range that
is also routinely abused for premium redirects. Neither message discloses a
tariff. The two rows were deliberately judged on one standard: if the number
range alone were treated as sufficient evidence, both would be spam; since it is
not, both are ambiguous. Consistency here was a conscious choice — T3390 was
initially rejected as spam and revised once T2710 surfaced the same question.

**Consent-plausible solicitation (T2847, T3981).** A club ticket notice and a
UNICEF appeal both solicit, but a member mailing list and a charitable purpose
are real carve-outs in most messaging policies. These are contrasted directly
against T2229 (Burger King) and T2273 (Interflora) in `label_noise.md`, which
solicit identically but have no available consent story and were therefore
rejected as ordinary spam rather than promoted to ambiguity.

**Irrecoverable context (T0774, T2658, H0550).** These rows are truncated or
carry corpus artifacts. The honest position is that the text no longer contains
enough information to decide, which is itself an audit finding about the corpus.

## False positives deliberately retained

Two rows are submitted at **low** confidence as explicit rejected candidates.
Their purpose is to demonstrate that predictive uncertainty alone is neither
label error nor ambiguity.

| ID | Text | Signals | Why it is not a finding |
|---|---|---|---|
| H0935 | "I liked the new mobile" | word 0.435 / char 0.527, neighbours mixed | Probabilities straddle 0.5 and neighbours disagree, but the content is ordinary ham with nothing to adjudicate |
| T0470 | "Waiting for your call." | word 0.689 / char 0.349 | The word model reacts to lexical overlap with call-to-action spam; **no neighbour opposes the label at all** |

`T0470` is the more instructive of the two. Its word probability of 0.689 would
place it above the decision boundary, yet its opposing-neighbour fraction is
exactly 0.00 — every neighbour is ham. A single-signal pipeline would have
flagged it; requiring independent agreement does not.

## Effect on the score ceiling

The word baseline makes **10 errors on the 1,114 held-out rows** (99.1023%
accuracy). Classifying each error by audit status:

| Status | Count | Rows |
|---|---|---|
| Genuine model error | 7 | H0287, H0318, H0330, H0461, H0814, H0903, H0927 |
| Likely public-label error | 2 | H0143, H0896 |
| Ambiguous policy case | 1 | H0550 |

**Three of the ten held-out errors are data problems rather than model
failures.** If the two likely label errors are treated as unresolved rather than
counted against the model, the error count falls from 10 to 8, which corresponds
to 99.28%.

That figure is a sensitivity bound, **not a corrected score**. The official
public-label metric remains 99.1023%. The point is that at this accuracy level
the model is close enough to the annotation noise floor that two individual
label judgements move the headline number by 0.18 points — so further gains on
this benchmark are no longer clearly measuring model quality.

Held-out labels were not modified. H0143, H0896 and H0550 are flagged only.

## Recommended policy clarification

The recurring ambiguities are systematic, not incidental. A future annotation
guide should state explicitly how to treat:

- opted-in service, club and membership notifications;
- charitable and public-interest campaigns;
- recruitment, market research and product-trial invitations;
- messages that quote, discuss, forward or warn about spam;
- personal-sounding messages carrying `070`-range or premium numbers;
- automated notifications from services the recipient may have initiated;
- truncated rows where the deciding evidence has been lost.

Where consent or sender relationship cannot be recovered, an explicit
`uncertain` label or a second-stage policy tag would be more honest than forcing
every message into a binary that the text cannot support.

## Limitations

- Sender identity and subscription status are unrecoverable from this corpus,
  and most findings here turn on exactly that missing evidence.
- Only 80 of the 177 boundary candidates were read; the remainder are ranked in
  `results/ambiguity_candidates.csv` and are not claimed either way.
- The `070` reasoning relies on general UK numbering conventions, not on
  per-number verification against an operator registry.

## Reproducible evidence

```
python scripts\audit_label_noise.py
python scripts\build_label_noise_outputs.py
python scripts\label_overlay_experiment.py
```

- `results/ambiguity_candidates.csv` — the 177 retrieved candidates, ranked
- `results/label_noise_evidence.csv` — per-row signals for every claim above
- `results/heldout_baseline_errors.csv` — the 10 held-out errors with audit status
- `results/label_overlay_experiment.json` — held-out error breakdown
- `configs/manual_review.json` — all 80 adjudications with reasons
