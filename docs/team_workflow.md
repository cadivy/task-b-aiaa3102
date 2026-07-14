# Three-Person Team Workflow

## 1. 分工原则

三人按研究模块分工，每个人都负责“代码或自动证据 + 审计文档 + 他人结果复核”，避免出现一人只写代码、另一人只写报告的不可验证分工。

角色名称先使用 Member A、B、C，确定姓名后统一替换。角色主责不代表其他人无需理解该模块；最终答辩时每个人都应能够解释完整证据链。

## 2. 主责划分

| 成员 | 主责 | 主要输入 | 主要交付 |
|---|---|---|---|
| Member A | 数据工程、画像、重复与泄漏 | UCI 原始数据、split manifest | canonical table、`profile.md`、`duplicates.md`、`leakage.md` |
| Member B | 文本基线、标签噪声与捷径特征 | canonical table、A 的 cluster 信息 | 模型预测、`label_noise.md`、`shortcut_features.md` |
| Member C | 模糊性、人工裁决、影响分析与报告整合 | A/B 的候选和证据 | `ambiguity.md`、裁决 memo、干预实验、报告草稿 |

## 3. Member A：数据、重复与泄漏

### 主要任务

- 下载 UCI 数据并记录 checksum；
- 解析原始行并与 manifest 一对一连接；
- 实现完整性断言和数据画像；
- 构建 normalized text 与 exact duplicate clusters；
- 构建 near-duplicate candidates 和阈值敏感性表；
- 标记所有跨 train/held-out 的 exact/near matches；
- 为 Member B 提供 cluster ID、nearest-neighbor ID 和 similarity。

### 交付接口

```text
data/canonical_sms.csv
results/profile_summary.csv
results/exact_duplicate_clusters.csv
results/near_duplicate_pairs.csv
results/cross_split_leakage.csv
audit/profile.md
audit/duplicates.md
audit/leakage.md
```

### 自检责任

- 不使用重新随机生成的 split；
- near-duplicate 表中排除 exact pairs；
- 每个 pair 使用稳定 ID；
- 记录被人工拒绝的相似候选，而不只保留成功案例。

## 4. Member B：模型、标签噪声与 shortcut

### 主要任务

- 建立主 TF-IDF 文本基线；
- 生成训练集 out-of-fold predictions 和 held-out predictions；
- 使用 word/character 模型、最近邻和 duplicate conflict 生成 label-error 候选；
- 构建 shallow-only features 和分类器；
- 进行促销词 masking、row-order 和特征消融实验；
- 为每个候选保存至少两个可能的证据字段；
- 将需要语义判断的候选交给 Member C。

### 交付接口

```text
results/baseline_metrics.csv
results/oof_predictions.csv
results/heldout_predictions.csv
results/label_error_candidates.csv
results/shortcut_metrics.csv
results/shortcut_ablation.csv
audit/label_noise.md
audit/shortcut_features.md
```

### 自检责任

- 训练样本优先使用 OOF 而不是 in-sample probability；
- Accuracy 之外必须报告 spam Precision、Recall、F1 和 macro-F1；
- 两个高度相关的模型输出不能自动当作两个独立证据；
- shortcut feature 的高预测力需要解释来源，不能自动判定为数据错误。

## 5. Member C：裁决、干预与报告

### 主要任务

- 根据统一政策筛选 ambiguity candidates；
- 组织双人盲审和第三人仲裁；
- 维护 `adjudication_memo.csv`；
- 合并、排序并校验 `suspicious_examples.csv`；
- 设计至少两个数据干预并保持实验设置一致；
- 编写 `impact_analysis.md`；
- 汇总报告、Difficulties and Solutions 与 AI usage declaration。

### 交付接口

```text
results/ambiguity_candidates.csv
adjudication_memo.csv
suspicious_examples.csv
results/intervention_metrics.csv
impact_analysis.md
audit/ambiguity.md
report.pdf
```

### 自检责任

- 不修改 held-out 标签；
- 训练标签修正使用单独 overlay；
- high-confidence 比例不超过 55%；
- 六个 issue types 均出现；
- 报告中的数字与 results 文件一致；
- 报告清楚区分已观察事实、人工判断和推测。

## 6. 交叉复核矩阵

| 内容 | 第一作者 | 第二复核人 | 分歧仲裁 |
|---|---|---|---|
| 数据行数、join、ID 与 split | A | B | C |
| exact/near duplicate | A | C | B |
| cross-split leakage | A | B | C |
| label error | B | C | A |
| shortcut features | B | A | C |
| ambiguous examples | C | A | B |
| intervention 设置与数字 | C | B | A |
| 最终报告可复现性 | C | A | B |

所有 high-confidence label error、ambiguous 和建议 `should_fix` 的案例必须至少两人独立阅读原文。复核人不能只看第一作者的结论，应先看文本和证据，再记录自己的决定。

## 7. 文件交接约定

每张 results 表至少包含：

```text
id,source_script,method_version,generated_at
```

成对结果应另含：

```text
paired_id,similarity_or_score
```

每个候选不得只用自然语言描述。交给下一位成员前必须提供稳定 ID、计算值和来源脚本，以避免人工复制时丢失证据。

## 8. 推荐工作顺序

### Phase 1：共同冻结规则

三人一起确认规范化规则、near-duplicate 主阈值、主模型、指标、置信度定义和人工裁决政策。冻结后如需修改，必须在日志中说明理由和影响。

### Phase 2：A 解锁数据

A 完成标准表和断言。B、C 只用该标准表，不各自重新解析原始数据。

### Phase 3：A/B 并行分析

A 运行 duplicate/leakage，B 运行 baseline/shortcut。A 将 cluster 和 neighbor 信息交给 B，B 再生成更可靠的 label-error candidates。

### Phase 4：交叉人工裁决

C 发放候选包；三人按复核矩阵独立填写决定。对分歧案例进行一次有记录的讨论。

### Phase 5：干预和报告

C 运行统一干预管线，B 核对指标，A 核对样本变化。报告按模块由主责人提供事实段落，C 统一语言和结构。

### Phase 6：提交前审计

三人共同执行 schema 检查、从空环境复现、PDF 阅读和数字抽查。任何无法追溯的数字从报告移除，直到证据补齐。

## 9. 每次会议的最小记录

```text
日期：
参与者：
已完成：
新发现：
规则变更：
待解决分歧：
负责人和截止时间：
```

规则变更尤其需要记录，因为阈值和标签政策若在看到 held-out 结果后随意改变，会削弱结论可信度。

## 10. 贡献证明

每位成员应保留：

- 自己负责的脚本和文档提交记录；
- 至少一类他人结果的复核记录；
- 一项可在答辩中展示的代表 finding；
- 一项本人发现并解决的实际困难；
- 对 AI 输出进行验证的具体记录。

这样既方便报告写作，也能清楚证明三人的实质贡献。

