# Manual Adjudication Protocol

## 1. 目的

本协议将自动候选转换为可解释的最终审计判断。它用于降低“模型错了，所以标签错了”以及“文本相似，所以一定泄漏”这两类常见误判。

## 2. 裁决单位

裁决以单个 issue claim 为单位，而不是以单个样本为单位。同一个样本可能同时具有 duplicate 和 leakage 问题，两个 claim 应分别记录和判断。

审核包应向审核人展示：

- 稳定 ID、split 和当前 label；
- 原始 text；
- issue type；
- 必要的 paired text 或 cluster members；
- 定量证据，但不先展示第一审核人的最终结论。

## 3. 四类最终决定

### `should_fix`

证据表明数据或划分存在可以明确修复的问题，例如同一 duplicate cluster 的明显标签冲突、确定的跨 split 泄漏，或经双人确认的训练错标。

### `keep_but_flag`

样本本身可以保留，但其重复、模板化、极端性或不确定性需要在分析中标记。此类别不主张直接修改原始标签。

### `ambiguous_policy_case`

在当前标注规则下存在两个合理标签，需要明确政策才能稳定决定。该类别描述任务定义边界，不等同于错误标签。

### `false_positive_audit_finding`

自动方法产生候选，但人工证据不足或存在更合理解释。保留这些案例是为了证明团队主动控制 false positives。

## 4. 审核问题

每名审核人按顺序回答：

1. 自动方法声称的事实是否可由原文或计算值直接验证？
2. 该事实是否满足协议对 issue type 的最低定义？
3. 是否存在反证或更简单的替代解释？
4. 问题影响的是训练、评估、标签政策，还是仅影响个别样本？
5. 建议动作是否与证据强度匹配？
6. 自己的 confidence 是 low、medium 还是 high？

## 5. 独立证据判断

可作为不同证据来源的示例：

- duplicate-cluster label conflict；
- out-of-fold model disagreement；
- 不同表示方式的模型一致反对当前标签；
- nearest-neighbor label agreement；
- 人工按预先写出的标注政策进行语义判断。

以下通常不能算两个独立信号：

- 同一模型的 probability 和 predicted label；
- 同一 TF-IDF 矩阵上只改变正则参数的两个模型；
- 同一 duplicate fact 的 cluster size 和 exact similarity；
- 审核人阅读了模型解释后简单重复模型结论。

## 6. 双人审核与仲裁

- high-confidence、`should_fix`、label-error 和 ambiguous claims 必须双人独立审核；
- 两人 decision 与 confidence 均一致时可直接进入最终 memo；
- 决定相同但 confidence 不同时，采用较低 confidence，除非第三人提供新证据；
- 决定不同时，第三人只基于完整证据包仲裁；
- 仲裁不得删除原始分歧记录。

## 7. 建议 memo 字段

starter 没有公开规定 `adjudication_memo.csv` 的严格列顺序，因此在向教师确认前，V1 采用以下可审计 schema：

```text
claim_id,id,split,issue_type,current_label,
reviewer_1_decision,reviewer_1_confidence,reviewer_1_reason,
reviewer_2_decision,reviewer_2_confidence,reviewer_2_reason,
adjudicator,final_decision,final_confidence,recommended_action,final_reason
```

如果教师提供正式 schema，应保留信息内容并映射到正式列名。

## 8. 标注政策草案

为保证一致性，人工审核使用以下工作定义：

- 明确的非请求式商业推广、奖品、付费号码或诱导行动通常支持 `spam`；
- 正常个人交流、已建立关系中的通知或上下文明确的私人消息通常支持 `ham`；
- 仅包含营销词不自动构成 spam；上下文和发送关系不可见时应降低置信度；
- 服务通知、合法订阅、慈善、政治或半商业消息可能成为 policy boundary；
- 短文本和缺少上下文不是标签错误的直接证据。

这只是本组用于一致审核的操作定义，不声称恢复 UCI 原始标注者的完整政策。

## 9. 质量抽查

最终提交前随机抽查：

- 至少 5 条 high-confidence；
- 至少 5 条 medium/low；
- 每个 issue type 至少 2 条；
- 所有 `should_fix`；
- 至少 5 条 `false_positive_audit_finding`。

抽查者需要从 CSV 反查原始文本和生成结果。如果无法复现 evidence 字段，该 claim 必须降级或移除。

