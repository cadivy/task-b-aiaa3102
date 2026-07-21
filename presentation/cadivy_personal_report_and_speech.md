# Cadivy — Personal Report Draft, Speech, and Q&A

> Preparation document only. This is not a replacement for the team `report.pdf`.
>
> Primary personal scope: Target 5 (shortcut-feature audit), plus contribution to the data-intervention comparison, final integration, and presentation materials.

## 0. Read This Before Presenting

Use `cadivy_shortcut_interventions_summary_en.pptx` for the formal presentation. It contains eight slides, adds the project Summary section, and synchronizes Slides 5–6 with the current protocol-capped intervention results.

The repository still contains two intervention scopes that must not be mixed:

- The older six-slide English PowerPoint was generated before the latest protocol-cap update. Its last slide reports an earlier uncapped combined-view spam F1 of **94.16%**.
- The current `impact_analysis.md` follows `max_impact_examples = 30` for training-side interventions. Its capped combined view reports **93.99% spam F1**.
- `report_zh_draft_new.md` still describes the earlier uncapped training views, including a 3,982-row combined training set. It is not numerically aligned with the current `impact_analysis.md`.

Use the current protocol-capped result as the final intervention result unless the team explicitly decides otherwise. The new eight-slide deck is already synchronized. If someone opens the old six-slide deck, say:

> The number displayed here comes from our earlier uncapped stress test. After enforcing the protocol's 30-example cap, the final combined-view spam F1 is 93.99%. The direction of the conclusion is unchanged, but the two runs have different scopes, so we do not compare them as if they were the same experiment.

The following results are stable and safe to use:

| Result | Value |
|---|---:|
| Majority-ham accuracy | 86.62% |
| Contact/promotion-only accuracy / spam F1 | 98.11% / 92.78% |
| All-shallow accuracy / spam F1 | 98.20% / 93.15% |
| Frozen full-text accuracy / spam F1 / spam recall | 99.10% / 96.55% / 93.96% |
| Row-position-only accuracy / spam F1 | 86.62% / 0.00% |
| Leakage-aware held-out rows | 1,051 after removing 63 recoverable rows |
| Leakage-aware spam recall / spam F1 | 90.91% / 94.74% |
| Adjudication-aware accuracy / spam recall / spam F1 | 99.37% / 95.86% / 97.54% |
| Current capped shortcut-masking accuracy / spam F1 | 98.47% / 93.99% |
| Current capped combined-view accuracy / spam F1 | 98.47% / 93.99% |

## 1. Honest Description of My Contribution

### Short English version

> My primary responsibility was Target 5, the shortcut-feature audit. I designed and ran controlled shallow-feature probes, analyzed standardized coefficients, manually reviewed representative stress cases, and documented the findings. I also contributed to the data-intervention comparison and integrated the final English presentation and report artifacts. The duplicate, leakage, label-noise, and ambiguity audits were team results; I use them in the intervention synthesis but do not present them as my individual discoveries.

### 中文理解

你的个人贡献可以诚实地概括为：

1. 主要完成 Target 5：检查模型是不是依赖数字、价格、URL、电话号码、促销词和文本形状等 shortcut。
2. 用相同的逻辑回归做公平对照，导出标准化系数，分析具体线索。
3. 人工复核 H0946、H0044、H0287 等代表案例，不把模型分歧自动当成数据错误。
4. 参与 data intervention 的汇总、最终英文 PPT、最终报告和提交文件集成。
5. A/B 负责的重复、泄漏、标签错误和模糊性可以作为团队结果介绍，但不要说成全部由你独立发现。

## 2. Individual Report Draft (English)

### Individual Contribution: Shortcut Features and Data Interventions

My primary contribution to the project was the Target 5 shortcut-feature audit. The team baseline achieved 99.10% held-out accuracy and 96.55% spam F1, but a high classification score does not by itself show that the model learned the semantic distinction between legitimate and unsolicited messages. My research question was therefore: how much of the benchmark performance could be reproduced using surface cues without access to the original word sequence?

I implemented controlled shallow probes using eleven content-shape, contact, and promotional features, while testing normalized corpus position separately as a negative control. The features included message length, token count, average token length, digit statistics, uppercase ratio, exclamation marks, currency markers, URL and phone indicators, and promotional-token counts. All numeric inputs were standardized and every learned comparison used Logistic Regression. The full-text reference was taken from the frozen team baseline, so the main difference between conditions was the feature representation rather than the classifier family.

The results showed that surface structure explains a large share of the benchmark score. Contact and promotion cues alone reached 98.11% accuracy and 92.78% spam F1. All shallow features reached 98.20% accuracy and 93.15% spam F1, compared with 99.10% accuracy and 96.55% spam F1 for the full-text baseline. Row position alone matched the majority-ham baseline and produced zero spam F1, so there was no evidence of a row-order shortcut. Because ham accounts for 86.62% of the data, the protocol's 70% accuracy warning was not informative by itself; spam recall and spam F1 were necessary for interpretation.

Standardized coefficients identified the strongest positive spam cues as digit count, promotional-token count, average token length, URL presence, and currency count. I then manually reviewed example-level failures. H0946 is a legitimate apartment-price discussion that the shallow probe pushes toward spam because it contains many digits and currency markers. H0044 is a ringtone-club solicitation that the shallow probe misses because it lacks the usual numeric and contact pattern. H0287 is a premium-rate solicitation recovered mainly through a phone number and price cue. These examples demonstrate failure in both directions and prevent the aggregate score from being mistaken for semantic robustness.

I also contributed to the intervention synthesis. The canonical data and held-out labels were never overwritten. In the final protocol-capped analysis, training-side interventions modified or removed at most 30 rows. The clearest evaluation-side result was the leakage-aware view: removing 63 held-out messages recoverable from training reduced spam recall from 93.96% to 90.91% and spam F1 from 96.55% to 94.74%. Shortcut masking also reduced the capped-view spam F1 to 93.99%. These interventions are stress tests, not proposed replacement datasets, and a lower score does not automatically mean lower data quality.

My main conclusion is that this dataset is highly predictable, but part of that predictability comes from redundant surface cues and non-independent evaluation examples. The audit therefore changes the strength of the claim we can make: the baseline performs very well on this fixed benchmark, but its score should not be interpreted as pure semantic understanding or fully independent generalization. The main limitations are the small reviewed sets, the age and domain specificity of the UCI corpus, the use of hand-built cue families, and the absence of an external distribution-shift test set.

## 3. Eight-Slide English Speech (About 7 Minutes)

### Slide 1 — Task statement (about 40 seconds)

> Good afternoon. My part of the project asks a simple question: our full-text model reaches 99.10 percent accuracy, but did it learn message meaning, or can it obtain almost the same score from shortcuts? I focus on Target 5, the shortcut-feature audit, and I also summarize the related data-intervention results. Here, a shortcut means a surface correlation, such as digits, prices, URLs, phone-number patterns, or promotional words. These cues can be legitimate evidence, but they do not require sentence-level understanding and may fail when the data distribution changes.

Transition:

> To test this fairly, I changed the features while keeping the classifier family fixed.

### Slide 2 — Methodology (about 55 seconds)

> We used the fixed split of 4,460 training messages and 1,114 held-out messages, with seed 42, and we never edited held-out labels. The shallow probe received eleven derived content, contact, and promotional features, while row position was tested separately. It never received the original word sequence. All numeric features were standardized and passed to Logistic Regression. The full-text result came from the frozen shared Logistic Regression baseline. This control matters because, if we changed both the features and the model, we could not tell which change caused the performance difference. We report spam recall and spam F1 as well as accuracy because 86.62 percent of the corpus is ham.

Transition:

> The controlled comparison produced a surprisingly small gap.

### Slide 3 — Main outcome (about 60 seconds)

> A classifier using only contact and promotional cues reached 98.11 percent accuracy and 92.78 percent spam F1. Using all shallow cues increased this to 98.20 percent accuracy and 93.15 percent spam F1. The full-text reference reached 99.10 percent accuracy and 96.55 percent spam F1. So the accuracy gap was only about 0.9 percentage points, even though the shallow model never saw the word order. The protocol's 70 percent warning threshold is weak for this dataset because a classifier that always predicts ham already reaches 86.62 percent accuracy. Row position also matched that majority baseline and had zero spam F1, so we found no row-order shortcut.

Transition:

> Aggregate performance is not enough, so I checked where these cues fail.

### Slide 4 — Representative cases (about 75 seconds)

> H0946 is a legitimate apartment-price discussion. It contains eleven digits and three currency markers, so the shallow probe assigns a spam probability of 0.992, while the full-text model correctly uses the context. This is a cue-induced false positive. H0044 is the opposite case: it is a ringtone-club solicitation, but it lacks the usual phone and price pattern. The shallow probability is only 0.085, while the full-text model detects it. H0287 is a premium-rate adult-chat solicitation that the shallow probe recovers mainly from a phone number and a price cue, while the full-text baseline misses it. Together, these cases show failure in both directions. High average accuracy therefore does not prove that the learned rule is robust.

Transition:

> We then tested whether changing the data view changes the evaluation claim.

### Slide 5 — Data-intervention outcome (about 80 seconds)

> Our interventions preserve the canonical table and never overwrite held-out labels. For training-side changes, the current protocol-capped run modifies or removes at most 30 training rows per experiment. The strongest and most defensible evaluation-side result is leakage-aware evaluation. We removed 63 held-out messages that had exact or manually accepted near-duplicate partners in training. The model was frozen; only the scoring set changed. Spam recall fell from 93.96 to 90.91 percent, and spam F1 fell from 96.55 to 94.74 percent. This means the original benchmark included many relatively easy, recoverable spam examples. In the current capped shortcut-masking view, accuracy is 98.47 percent and spam F1 is 93.99 percent. The model remains strong, so no single cue family explains everything, but the score is sensitive to surface evidence.

Transition:

> The important point is not whether every intervention raises or lowers one number.

### Slide 6 — Implication and conclusion (about 55 seconds)

> These interventions reveal different distortions. Leakage makes the test set less independent. Ambiguity and suspected label errors affect whether a prediction should count as wrong. Shortcut masking tests reliance on surface form. The adjudication-aware accuracy rises to 99.37 percent, but we explicitly treat part of that increase as circular because suspected label errors were retrieved using model disagreement. Therefore, our goal is not to maximize the benchmark score. Our goal is to make the generalization claim more credible.

Transition:

> I will close by summarizing what the whole audit changes and what we recommend.

### Slide 7 — Overall project summary (about 55 seconds)

> To summarize the full audit, the 99.10 percent baseline remains strong on this fixed split, but three findings qualify what that score means. First, 63 held-out messages can be recovered from training. Second, contact and promotion cues alone reach 98.11 percent accuracy without word order. Third, three of the ten baseline errors are tied to suspected label errors or policy ambiguity rather than ordinary model failure. The result is not that the model has no ability. It is that the headline score combines genuine predictive performance with an easier and less independent benchmark than the number suggests.

Transition:

> These findings lead directly to four practical safeguards.

### Slide 8 — Recommendations and closing (about 55 seconds)

> First, split exact and accepted near-duplicate variants by cluster so one message template cannot appear on both sides. Second, clarify recurring policy boundaries, especially subscriptions, charity, 070 numbers, and messages that quote or discuss spam. Third, report spam recall and spam F1 together with accuracy, including leakage-aware sensitivity. Finally, preserve the audit trail through overlays and review ledgers instead of overwriting canonical data or held-out labels. The goal is not simply a higher score. It is an evaluation claim that another reviewer can reproduce and defend. Thank you.

## 4. Likely Q&A and Strong Answers

### Q1. What is the project actually auditing?

> This is a dataset-quality audit, not a competition to build the highest-scoring spam classifier. The classifier is an instrument used to detect duplicates, leakage, label inconsistencies, ambiguous cases, and shortcut features. The final question is whether the evaluation result is trustworthy.

中文要点：先把研究目标和分类工具分开。重点是“99.10% 是否可信”，不是“怎么刷到 99.10%”。

### Q2. What is the difference between a shortcut and leakage?

> Leakage means information from the held-out set, or a recoverable copy of a held-out example, is available during training. A shortcut is a real but fragile correlation, such as phone numbers or price markers. Shortcut cues do not necessarily cross the train-test boundary, so they are not leakage, but they may fail under distribution shift.

### Q3. Why did you use Logistic Regression for the shallow probe?

> The full-text baseline also uses Logistic Regression, so keeping the model family fixed isolates the effect of the feature representation. Logistic Regression is also suitable for this audit because its standardized coefficients provide interpretable evidence about which shallow cues matter.

### Q4. Why standardize the numeric features?

> The features use different units, for example message length, digit count, and binary URL presence. Standardization prevents scale alone from controlling the coefficient magnitude and makes coefficients comparable within the fitted shallow model.

### Q5. Why is the 70% shortcut warning threshold insufficient?

> Ham is 86.62 percent of the corpus. A useless classifier that always predicts ham already exceeds 70 percent accuracy while detecting no spam. We therefore compare against the majority baseline and report spam recall and spam F1.

### Q6. Does 98.20% shallow accuracy prove that the full-text model uses only shortcuts?

> No. It proves that the dataset can be classified extremely well using shallow information. It does not prove that every full-text decision uses those cues. That is why we also use masking experiments and manually reviewed failure cases. The correct claim is high shortcut availability and sensitivity, not complete causal dependence.

### Q7. Are the feature coefficients causal evidence?

> No. They are standardized associations within the fitted probe. We use them to identify candidate cues, then use controlled comparisons and example-level review to interpret how those cues can fail.

### Q8. Why are H0946, H0044, and H0287 good examples?

> They show different failure directions. H0946 is benign but looks promotional to the shallow model. H0044 is spam but lacks typical shallow markers. H0287 is spam recovered mainly from phone and price evidence even though the full-text baseline misses it. Together they show that the issue is a mechanism, not one cherry-picked error.

### Q9. Why not simply remove every digit, URL, or phone number?

> Those cues are often legitimate spam evidence. Removing them globally could discard useful information and create an artificial distribution. Our masking experiment is a stress test of sensitivity, not a recommended production preprocessing rule.

### Q10. Why can a data intervention lower the score but still be useful?

> A benchmark may reward duplicates, noisy labels, or easy surface cues. Removing those advantages can lower the measured score while making the evaluation more independent or the training data more defensible. Therefore, score direction and data-quality direction are not always the same.

### Q11. Why did leakage-aware spam recall fall so much while accuracy barely changed?

> Spam is the minority class. The 63 removed held-out rows included 50 spam messages, and all 63 were correctly predicted by the baseline. Removing these easy recoverable examples reduces spam recall from 93.96 to 90.91 percent, but the many ham examples keep overall accuracy near 99 percent. This is exactly why accuracy alone hides the effect.

### Q12. Why is the adjudication-aware improvement partly circular?

> Two suspected held-out label errors were retrieved because multiple model signals opposed their public labels. Removing them from evaluation therefore removes cases already associated with model errors, so part of the score increase is built into the selection rule. The ambiguity-only subset is more informative because it was selected through policy reading rather than model failure.

### Q13. What does the 30-example cap mean?

> The audit protocol specifies `max_impact_examples = 30`. In the final unified run, each training-side intervention modifies or removes at most 30 training rows, selected deterministically by original UCI row order. Leakage-aware evaluation is reported separately as a scoring-set sensitivity analysis: it freezes the model and excludes every held-out row with accepted train-set recoverability evidence.

### Q14. Did you edit the held-out labels?

> No. The canonical table and held-out labels remain unchanged. Training-label corrections are expressed as an overlay, and evaluation-side analyses change only which rows are scored, not their labels.

### Q15. What was your individual contribution?

> My primary contribution was Target 5. I implemented and interpreted the controlled shortcut probes, exported the coefficient evidence, reviewed representative cases, and documented the audit. I also contributed to the intervention synthesis and integrated the English presentation and final report artifacts. Other audit targets were team results, which I use but do not claim as solely my own.

### Q16. What are the main limitations?

> First, the UCI corpus is old and domain-specific. Second, the shallow feature families and promotional lexicon are hand-designed and cannot cover every shortcut. Third, manually adjudicated label and ambiguity sets are small. Fourth, we do not have an external time-shifted or domain-shifted test set, so shortcut fragility is supported by stress tests and reviewed cases rather than a full deployment study.

### Q17. How was AI used, and how did you verify it?

> AI tools assisted with code drafting, document integration, and presentation preparation. Numerical claims were taken from tracked CSV and JSON outputs rather than generated from prose. Scripts were rerun, required schemas and row counts were checked, manual decisions were stored in review ledgers, and the PDF and presentation were rendered and visually inspected. AI suggestions were treated as candidates, not ground truth.

### Q18. Why do the old slide and the latest impact file show different combined F1 values?

> They are different experiment scopes. The old slide shows the earlier uncapped stress test, while the latest impact file enforces the protocol's 30-example cap for training-side interventions. The protocol-capped result is the final one. We should not compare the two values as repeated estimates of the same condition.

### Q19. What is the overall conclusion of the full project?

> The model is genuinely strong on the fixed benchmark, but the 99.10 percent accuracy is not a clean estimate of independent semantic generalization. Leakage makes part of the test set recoverable, shallow cues make the task easier without sentence-level understanding, and label-policy uncertainty changes what some errors mean.

### Q20. What are your main recommendations?

> Rebuild the split by duplicate cluster, clarify recurring annotation boundaries, report spam recall and spam F1 together with accuracy, and preserve all corrections as auditable overlays or ledgers rather than overwriting canonical data.

## 5. One-Minute Emergency Version

> My main responsibility was the shortcut-feature audit. I tested whether the SMS benchmark could be solved using only surface cues such as digits, prices, URLs, phone patterns, and promotional words. I kept the classifier family fixed as Logistic Regression and standardized the numeric features. Contact and promotion cues alone achieved 98.11 percent accuracy and 92.78 percent spam F1, while the full-text model achieved 99.10 percent accuracy and 96.55 percent spam F1. Row position had zero spam F1, so there was no row-order shortcut. Manual cases showed failures in both directions: legitimate price discussions could look like spam, while solicitations without typical numeric cues could be missed. In the intervention analysis, removing 63 held-out messages recoverable from training reduced spam recall from 93.96 to 90.91 percent. Therefore, the model is strong on the benchmark, but the headline score overstates semantic robustness and fully independent generalization.

## 6. Delivery Checklist

- Memorize the logic, not every decimal: **question → fair probe → key contrast → cases → intervention → synthesis → safeguards**.
- Say "surface correlation" instead of saying shortcuts are fake or useless.
- Never claim that a coefficient proves causality.
- Never say that all 99.10% performance comes from shortcuts.
- When discussing interventions, state whether the model was retrained or frozen.
- Lead with spam recall/F1 when accuracy appears almost unchanged.
- If challenged on a small score difference, say it is directional evidence, not a causal significance claim.
- Do not present the adjudication-aware 99.37% as an independent improvement; state the circularity caveat immediately.
- Present from `cadivy_shortcut_interventions_summary_en.pptx`; the older six-slide deck retains the obsolete uncapped number.
