# Project Research Plan

## 1. 项目目标与范围

本项目将 UCI SMS Spam Collection 视为一个需要审计的数据产品，而不是默认可信的监督学习 benchmark。研究目标是建立一条从原始数据到审计结论的可复现证据链，并判断数据缺陷如何改变模型评估的含义。

范围内工作包括：数据完整性验证、描述性画像、文本分类基线、六类审计、人工裁决、至少两种数据干预和影响分析。

范围外工作包括：追求大型语言模型或复杂深度学习模型、修改公开 held-out 标签、把当前模型的所有错误等同于数据错误，以及仅凭关键词自动决定最终标签。

## 2. 研究原则

### 2.1 证据优先

每条最终 finding 都必须能够追溯到稳定 ID、生成脚本、定量信号和必要的人工解释。结论必须比生成候选的算法更严格。

### 2.2 候选生成与最终裁决分离

自动化方法用于提高召回率，人工裁决用于控制精确率。进入 candidate table 不等于进入 `suspicious_examples.csv`，进入 `suspicious_examples.csv` 也不等于应直接修改标签。

### 2.3 不确定性校准

置信度描述证据强度，而不是问题严重程度。高影响但证据不足的案例仍应标为 low 或 medium；容易修复也不代表可以标为 high。

### 2.4 评估隔离

held-out 标签只用于评估和事后审计，不参与训练、阈值调优或人工 overlay。训练样本的模型分歧优先使用 out-of-fold predictions，避免用训练内拟合结果判断标签质量。

## 3. 数据构建与完整性检查

### 3.1 标准工作表

原始文件每行为 `label<TAB>message_text`，以 1-based 行号生成 `uci_row_number`，再与 manifest 一对一连接。

标准列：

```text
id,split,uci_row_number,text,label
```

建议派生列：

```text
normalized_text,char_count,token_count,digit_count,
uppercase_ratio,has_url,has_phone,has_currency,promo_token_count,
row_position,label_binary
```

### 3.2 必须通过的断言

- 原始数据和 manifest 都有 5574 行；
- `uci_row_number` 完整覆盖 1 至 5574，且没有重复；
- join 后不缺行、不增行；
- `id` 全部唯一；
- train ID 以 `T` 开头，held-out ID 以 `H` 开头；
- split 只有 `train` 和 `heldout`；
- label 只有 `ham` 和 `spam`；
- text 不为空；
- 输出顺序可以还原到原始 UCI 行顺序。

任何断言失败时停止下游分析，不生成最终审计表。

## 4. 数据画像与基线

### 4.1 数据画像

按 split 和 label 报告：

- 样本数及类别比例；
- 字符数、词数、数字数的中位数和四分位数；
- URL、电话、货币符号、促销词出现率；
- 原始行号分段的 spam 比例；
- 空白规范化后唯一文本数和重复率。

画像的目的不是堆积图表，而是发现可能影响后续审计的类别不平衡、分布差异和浅层线索。

### 4.2 主文本基线

建议固定以下可解释且 CPU-friendly 的主模型：

```text
TF-IDF word n-grams (1, 2) + Logistic Regression
```

可增加 character n-gram Logistic Regression 作为独立信号。所有随机过程固定 `random_state=42`。

报告指标：

- Accuracy；
- spam Precision、Recall、F1；
- macro-F1；
- confusion matrix；
- 预测概率分布；
- train OOF 与 held-out 错误清单。

Accuracy 不能作为唯一指标，因为 spam 是少数类。

## 5. 六类审计设计

### 5.1 Exact duplicate

按协议使用下列规范化：

```text
lowercase + whitespace collapse
```

同一规范化文本形成 duplicate cluster。对每个簇记录：成员 ID、split、label、簇大小、是否跨 split、是否标签冲突。

强证据：规范化文本完全一致且能展示同簇成员。标签或 split 冲突属于额外严重性证据，但不是 exact duplicate 成立的前提。

### 5.2 Near duplicate

使用 TF-IDF cosine similarity 搜索非 exact 的候选对。主协议阈值为 0.92，同时检查 0.88 至 0.96 区间，以说明阈值附近的 precision/recall 权衡。

每个最终案例需要：相似度、对方 ID、关键差异、人工判断和是否跨 split。仅共享常见模板词、电话号码或短语的文本可能是 false positive。

### 5.3 Cross-split leakage

主要定义为 held-out 样本与训练样本 exact/near duplicate，或元数据直接暴露标签或 split。每个 held-out 案例关联最接近的 train ID，并报告标签是否一致。

影响分析中比较原始 held-out 指标与去除泄漏簇后的指标。若分数下降，应解释为评估变严格，而不是模型退化。

### 5.4 Likely label error

候选生成信号包括：

1. OOF 或 held-out 模型高置信度预测与标签冲突；
2. character 模型与 word 模型独立同意相反标签；
3. 最近邻标签多数与当前标签冲突；
4. duplicate cluster 内部标签冲突；
5. 文本语义与书面标注政策明显不一致。

最终 label-error finding 至少需要两个相互独立的信号。两个只由同一个模型概率派生的量不算两个独立信号。

### 5.5 Shortcut features

建立只使用浅层派生特征的模型，包括长度、数字、符号、联系方式、促销词和 row position。若 accuracy >= 0.70，触发公开协议中的 shortcut warning。

同时进行：

- full-text 与 shallow-only 比较；
- 屏蔽明显促销词后的性能比较；
- 不含 row position 与包含 row position 的比较；
- shortcut 特征在 train/held-out 中的稳定性比较。

高预测力不自动等于不合法捷径。报告必须区分与任务真实相关的简单模式和由采集过程产生的脆弱 artifact。

### 5.6 Ambiguous examples

由人工阅读模型不确定、模型分歧、近邻冲突和边界政策案例。判断重点是：在明确写出的标注政策下，是否存在两个合理标签。

Ambiguous 不等于 label error。最终文档需要展示至少三种案例：保留原标签但标记、需要政策澄清、审计后判定不是模糊案例。

## 6. 证据和置信度标准

### High

- finding 的定义被直接满足；
- 至少一个强定量证据可以复现；
- 政策判断与自动证据分别记录，且没有尚未解决的关键反证；
- 本次独立实现不把 AI 的两次判断伪装成两名人类审核人。

### Medium

- 有多个支持信号，但至少一个依赖阈值或政策解释；或
- 自动证据很强，但人工判断仍存在合理分歧。

### Low

- 主要用于记录值得复核的弱候选、阈值边界或反例；
- 不应给出确定性的 `relabel` 或 `remove` 建议。

## 7. Ranked audit 输出

`suspicious_examples.csv` 严格使用以下列：

```text
id,split,issue_type,rank,confidence,evidence_1,evidence_2,
recommended_action,short_explanation
```

排序优先级综合考虑：评估威胁、证据强度、影响范围和可操作性。rank 必须唯一、从 1 开始且连续。

同一个 ID 可以因不同问题出现多行，但每行只能表达一个清楚的 issue claim。证据字段应包含可核查值，例如 paired ID、cluster ID、cosine similarity 或 OOF probability，而不是只写“模型认为可疑”。

## 8. 人工裁决

四种最终类别：

- `should_fix`
- `keep_but_flag`
- `ambiguous_policy_case`
- `false_positive_audit_finding`

裁决过程见 `docs/adjudication_protocol.md`。本次实现使用分离的 evidence pass 与 policy pass，并在 memo 中明确披露为 AI-assisted；没有虚构独立人类复核或一致性统计。

## 9. 数据干预与因果边界

预注册的主干预为：

1. **Cluster-aware evaluation**：移除或重建跨 split duplicate clusters，测量去泄漏后的评估变化；
2. **Training audit filter**：仅过滤 high-confidence、`should_fix` 的可疑训练样本；
3. **Training label overlay**：只对同时通过自动证据和政策判断的训练样本使用独立 overlay，不修改源标签。

至少完成前两项。所有干预使用同一特征、模型、随机种子和评估指标。一次只改变一个数据条件，再提供组合干预作为补充实验。

这些实验只能显示“在当前模型和审计规则下的影响”，不能证明某个清洗步骤普遍提高真实世界性能。

## 10. 复现与质量控制

- 原始下载文件记录来源、时间和 SHA-256；
- 依赖版本写入最终 README 或 requirements 文件；
- 中间表保留 stable ID；
- 所有关键阈值集中配置，不散落在 notebook 中；
- 图表和表格由脚本生成，不手工改数；
- 最终 CSV 运行 schema、枚举、数量和 rank 检查；
- 报告中的每个具体数字可以追溯到 results 文件；
- 保留 AI 使用记录和人工验证记录。

## 11. 项目风险

| 风险 | 后果 | 控制方法 |
|---|---|---|
| 把模型错误当作标签错误 | 大量 false positives | 两个独立信号加人工复核 |
| near-duplicate 阈值过低 | 常见模板被误报 | 阈值敏感性分析和拒绝案例 |
| 在 held-out 上调阈值 | 评估污染 | 规则预注册，held-out 只做最终评估 |
| 主观判断缺少独立人类复核 | 结论可能受单一审核来源影响 | 披露 AI-assisted 状态、保留证据并支持后续团队复核 |
| 为满足 35 行而过度报告 | precision 和校准受损 | 允许 low-confidence 反例，绝不虚构强证据 |
| 清洗前后实验设置变化 | 无法归因 | 除数据条件外保持管线一致 |

## 12. 阶段性完成标准

### Milestone 1：数据可信

标准表生成，所有完整性断言通过，profile 草稿含真实统计。

### Milestone 2：候选可复现

基线、duplicate、leakage、label-noise 和 shortcut 脚本可运行，候选均保留证据字段。

### Milestone 3：裁决可审计

三人完成交叉复核，最终 CSV 满足协议，明确保留 false positives 和不确定性。

### Milestone 4：影响可解释

至少两种干预使用同一设置比较，结果能解释 score 变化而不夸大因果。

### Milestone 5：提交可复现

从 README 命令可重新生成主要 artifacts，report 与结果文件数字一致。
