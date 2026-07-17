# Final Project - Topic B：数据集取证与标签审计

## Dataset Forensics and Label Audit

*审计一个带噪声的分类数据集，识别可信与不可信样本，并解释数据质量如何改变模型评估的含义。*

### I. 背景

许多机器学习失败本质上是数据失败。分类器看起来很强，可能是因为 near-duplicate examples 泄漏到了 evaluation split，浅层文本 artifacts 暴露了 label，ambiguous examples 让任务定义变得模糊，或者少量 mislabeled rows 扭曲了 error analysis。只改模型是不够的；如果数据集本身不可信，评估结果也不可信。

在本项目中，你将扮演 dataset auditor。你需要检查一个由公开 UCI SMS Spam Collection 构建的 CPU-friendly 文本分类数据集，定位 suspicious examples，判断哪些 finding 真实可信，并解释不同数据质量问题如何影响 evaluation。核心挑战是 judgment：不是每个可疑样本都是错的，也不是每个弱信号都应成为 high-confidence finding。

### II. 项目概览

starter package 包含：

- UCI SMS Spam Collection 的 public data-source information；
- `data/split_manifest.csv`，用于把 public raw rows 映射到 stable course ids 和 splits；
- 描述 canonical working table 的 `data/data_dictionary.md`；
- 展示 audit submission format 的 `examples/suspicious_examples_sample.csv`；
- `configs/audit_protocol.json`，定义 issue labels、allowed values 和 public strict-check rules。

你需要自己下载公开 SMS messages 和 labels，将其与 split manifest 对齐，并编写 profiling、baseline 和 audit 代码。数据足够小，可以用本地 pandas 和 scikit-learn 完成；但也足够大，不能只靠手工逐行查看解决。

Final grading 可能使用 hidden audit key，其中包含 known duplicate、leakage、label-error、shortcut、ambiguous 和 false-positive-trap cases。Hidden key 用来奖励 precision、recall、evidence quality 和 uncertainty calibration。

### III. 审计目标

你必须调查六类 audit targets。每一类都需要可复现证据，而不是只给结论。

| # | 审计目标                 | 核心问题                                                                                                                |
| - | ------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| 1 | Exact duplicate clusters | 哪些 examples 是 exact duplicates？duplicate clusters 中是否存在 label 或 split conflicts？                             |
| 2 | Near-duplicate clusters  | 在你证明合理的 threshold 下，哪些 examples 是 near duplicates？哪些 candidates 应被拒绝为 false positives？             |
| 3 | Cross-split leakage      | held-out examples 是否能从 training examples 或 corpus artifacts 中恢复出来？                                           |
| 4 | Likely label errors      | 哪些 labels 在至少两个 independent signals 下可疑？                                                                     |
| 5 | Shortcut features        | length、digits、contact tokens、promotional phrases 或 row-order artifacts 等浅层 features 是否解释了过多 performance？ |
| 6 | Ambiguous examples       | 哪些 examples 有多个合理 label？它们如何限制 score ceiling？                                                            |

### IV. 预期证据

你的 audit 应该是 ranked 且 evidence-backed 的。目标不是尽可能多地标记 rows，而是用清楚证据区分 strong findings、uncertain findings 和 false positives。

你应设计结合 automated signals 与 manual judgment 的分析。强证据可能来自 duplicate rules、nearest-neighbor agreement、model disagreement、shallow-feature baselines 或 annotation-policy reasoning。starter README 会说明 `suspicious_examples.csv` 的 exact schema。

High-confidence rows 应有强支持。Bulk over-reporting 会被惩罚：一长串弱证据 high-confidence findings，不如一个能清楚解释 uncertainty 和 rejected candidates 的 ranked list。

### V. 分析范围

你的 analysis 应覆盖六个 audit targets，并解释数据质量如何影响 evaluation。你还应比较至少两种 data interventions，例如 relabel overlays、deduplication-by-cluster、removing suspicious training rows 或 rebuilding split by duplicate cluster。

不要修改 held-out labels。如果你测试 training-label correction，请用 experimental overlay file 表示，不要覆盖 public labels。required audit files 的细节在 starter README 中说明。

### VI. Starter 包结构

starter package 提供 public data source、split manifest、audit protocol 和 sample submission file。请使用其中的 `README.md` 查看 canonical row-id mapping、exact CSV schemas 和 issue-label choices。下载、profiling、建模和审计代码都由你自己实现。

### VII. 报告要求

最终的 `report.pdf` 应总结你的 methodology、analysis、key findings 和 conclusions。它应该是一份自洽的项目报告，而不是 audit outputs 的集合。

一份优秀报告应清楚说明你如何从 raw data 得到 ranked audit findings，为什么这些 findings 可信，以及哪些不确定性仍然存在。对于本 topic，报告应体现 judgment：对真实问题给出强证据，对 false positives 做出明确处理，并说明数据质量问题如何影响 evaluation。

报告中也应设置单独的 **Difficulties and Solutions** section，说明至少三个具体、可验证的项目困难，以及你如何解决它们。请包含 AI usage declaration，说明你如何使用 AI 工具，以及如何验证 AI 输出。

### VIII. 提交内容

```
repo/
|-- audit/
|   |-- profile.md
|   |-- duplicates.md
|   |-- leakage.md
|   |-- label_noise.md
|   |-- shortcut_features.md
|   `-- ambiguity.md
|-- scripts/
|-- results/
|-- suspicious_examples.csv
|-- adjudication_memo.csv
|-- impact_analysis.md
|-- logs/chat.md
|-- report.pdf
`-- README.md
```

`README.md` 必须包含重新生成主要 artifacts 所需的 exact commands 和 software versions。

### IX. 学术诚信与 AI 使用

允许并鼓励使用 AI 工具，但最终 audit 必须是你自己的 evidence-backed work。你必须引用 datasets、code、tools 和阅读过的 public analyses。伪造 manual judgments 或编造 examples 属于 academic-integrity violations。
