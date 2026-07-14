# Ambiguity and Annotation-Policy Audit

## Status

**V1 method specification — manual review results are pending.**

## Audit question

Which messages plausibly admit both `ham` and `spam` under a reasonable annotation guideline, and how does this policy uncertainty limit the interpretation of model errors and maximum attainable score?

## Ambiguity is not label error

The distinction used in this project is:

- **Likely label error:** one label is clearly better supported after applying the policy and available context.
- **Ambiguous example:** two labels remain reasonable because the policy or message context is insufficient.
- **Ordinary model error:** the label is reasonable and the model simply failed.
- **False-positive audit finding:** initial signals suggested ambiguity, but review found a clear interpretation.

## Candidate sources

- word and character models strongly disagree;
- prediction probabilities are persistently near the decision boundary;
- nearest semantic neighbors have mixed labels;
- short or context-dependent messages;
- service notifications, subscriptions, relationship-dependent promotions or opt-in messages;
- human reviewers independently disagree.

Low model confidence alone does not establish ambiguity.

## Review rubric

Reviewers answer the following without seeing each other’s decision:

1. Is the message clearly unsolicited commercial or deceptive content?
2. Could it plausibly come from an expected personal or service relationship?
3. Does the classification depend on unavailable sender/context information?
4. Does the working annotation policy resolve the case?
5. Would two careful annotators reasonably choose different labels?

## Cases to document

The final version should include:

- at least one high-quality `ambiguous_policy_case`;
- at least one `keep_but_flag` example;
- at least one candidate reclassified as likely label error;
- at least two rejected ambiguity candidates;
- a short description of which policy clarification would resolve each genuine boundary case.

## Result table to complete

| ID | Current label | Reviewer 1 | Reviewer 2 | Missing context or policy boundary | Final decision | Confidence |
|---|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## Score-ceiling analysis

The project will not claim an exact irreducible-error rate from a small manual sample. Instead it will report:

- number of reviewed candidates;
- number and percentage judged genuinely ambiguous;
- inter-reviewer raw agreement and Cohen’s kappa when sample size permits;
- model errors overlapping with ambiguous cases;
- an explicitly labelled sensitivity range obtained by treating ambiguous errors as unresolved rather than definitively wrong.

This analysis changes the meaning of the score: some errors may measure annotation-policy disagreement rather than failure to recognize spam.

## Recommended actions

- Keep the public labels unchanged for official evaluation.
- Flag genuine policy-boundary cases in the memo.
- Propose a clearer annotation guideline for future data collection.
- Where context is structurally unavailable, report uncertainty rather than forcing a relabel.

## Limitations

- Reviewers do not know the sender-recipient relationship.
- The working policy may differ from the original UCI annotation process.
- Agreement statistics from a targeted candidate sample do not estimate full-corpus agreement.
- Human review can be influenced by model explanations; reviewers should make an initial blinded judgment.

