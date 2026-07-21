# Cadivy — two-minute English script

Use the three-slide deck `cadivy_two_minute_summary_en.pptx`. The main script is about 175 words and is designed for roughly 1:30–1:45 with natural pauses.

## Slide 1 — Task, method, outcome (about 30 seconds)

My part asks whether 99.10 percent accuracy reflects semantic understanding or shortcuts. I kept the classifier fixed as Logistic Regression, but used only shallow cues such as digits, prices, URLs, and promotional words, without the original word sequence. These cues still reached 98.11 percent accuracy, only 0.99 points below the full-text model.

## Slide 2 — Data intervention outcome (about 30 seconds)

Next, we tested how data quality changes the result. After removing 63 held-out messages recoverable from training, spam recall fell from 93.96 to 90.91 percent, and spam F1 fell from 96.55 to 94.74. The score became lower because the evaluation became more independent, not because the model or data suddenly became worse.

## Slide 3 — Four conclusions (about 40 seconds)

So we draw four conclusions. First, data quality changes what the score means. Second, the benchmark is in a noise-dominated regime: label and policy issues are now comparable to the remaining model errors. Third, metric choice is itself a data-quality issue, because accuracy hides minority-class changes. Finally, judgment matters more than labeling: automated signals retrieve candidates, but people make the final decision. Overall, the model is strong, but the score needs an audit.

## If time is cut to one minute

Our shortcut probe kept Logistic Regression fixed but removed the original word sequence. Contact and promotion cues still reached 98.11 percent accuracy, only 0.99 points below the full-text model. After removing 63 held-out messages recoverable from training, spam recall fell by 3.05 points. This shows that data quality changes what the score means, the benchmark is becoming noise-dominated, metric choice is itself a data-quality issue, and final judgment must remain human. The model is strong, but the score needs an audit.

## One-line answers for likely questions

- **Why keep Logistic Regression fixed?** To isolate the effect of the feature view instead of mixing feature and model changes.
- **Does 98.11% prove leakage?** No. It proves strong shortcut accessibility; duplicate analysis separately tests recoverability across the split.
- **Why emphasize spam recall and F1?** Accuracy is dominated by the majority ham class and can hide changes in spam detection.
- **Why did the score fall after intervention?** The evaluation became more independent and therefore more credible.
