# Topic B: Dataset Forensics and Label Audit

本仓库用于完成 AIAA3102 Final Project Topic B。项目对象是公开的 UCI SMS Spam Collection，目标不是单纯追求更高的分类准确率，而是审计数据集是否足以支撑可信的模型评估。

项目将系统调查六类问题：完全重复、近重复、跨划分泄漏、疑似标签错误、捷径特征和语义模糊样本。最终结论必须同时具备可复现的自动化证据和可追溯的人工判断。

## 当前状态

当前为 **V1 文档与研究设计阶段**。

| 内容 | 状态 | 说明 |
|---|---|---|
| 官方 handout 与 starter | 已提供 | 保持原样，作为要求来源 |
| Git 仓库与目录结构 | 已完成 | 独立仓库，默认分支为 `main` |
| 审计方法与证据标准 | 已设计 | 见 `docs/` 与 `audit/` |
| 数据下载与标准表构建 | 待实现 | 不在文档阶段虚构数据结果 |
| 六类审计实验 | 待运行 | 运行后回填审计文档中的结果区 |
| 干预实验与最终报告 | 待完成 | 至少比较两种数据干预 |

## 核心研究问题

1. 当前 held-out score 在多大程度上反映真实泛化能力，而不是重复或跨划分泄漏？
2. 哪些样本值得修正、保留但标记、视为政策边界，或判定为审计误报？
3. 模型性能是否主要由长度、数字、联系方式、促销词或数据顺序等浅层特征驱动？
4. 去重、过滤或训练标签 overlay 后，模型分数与错误结构如何变化？
5. 数据质量问题如何改变我们对 Accuracy、F1 和 spam Recall 的解释？

## 数据与固定划分

原始数据来自 UCI SMS Spam Collection：

- 数据页面：<https://archive.ics.uci.edu/dataset/228/sms+spam+collection>
- 原始压缩包：<https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip>

必须使用 `starter/data/split_manifest.csv` 提供的固定划分。该 manifest 包含 5574 个稳定 ID：4460 个训练样本和 1114 个 held-out 样本。标准工作表至少包含：

```text
id,split,uci_row_number,text,label
```

原始标签只能是 `ham` 或 `spam`。不得重新生成主实验划分，不得修改 held-out 标签。训练标签修正必须通过单独的 experimental overlay 表达。

## 公开审计协议

`starter/configs/audit_protocol.json` 是输出格式与最低判定标准的正式依据。

| 规则 | 要求 |
|---|---|
| Near-duplicate 参考阈值 | TF-IDF cosine similarity >= 0.92，且不是 exact duplicate |
| Shortcut warning | 仅使用浅层特征的模型 accuracy >= 0.70，或能解释大量错误 |
| Label error | 至少两个相互独立的信号与现有标签冲突 |
| `suspicious_examples.csv` 最少行数 | 35 |
| issue type 覆盖 | 六类全部出现 |
| high-confidence 上限 | 不超过全部记录的 55% |
| impact analysis 重点样本上限 | 30 |

协议中的行数是最低格式检查，不是鼓励批量报可疑样本。评分可能包含 false-positive traps，因此 precision、证据质量和置信度校准优先于候选数量。

## 研究流程

```text
公开原始数据 + 固定 manifest
        |
        v
标准工作表与完整性校验
        |
        +--> 数据画像与文本分类基线
        |
        +--> 完全重复 / 近重复 / 跨划分泄漏
        |
        +--> 模型分歧 / 最近邻 / 疑似标签错误
        |
        +--> 浅层特征基线 / masking / row-order probe
        |
        +--> 人工模糊性判断与交叉裁决
        |
        v
排序后的 suspicious_examples.csv
        |
        v
至少两种数据干预与影响分析
        |
        v
自洽、可复现的 report.pdf
```

详细方法、证据等级和完成标准见 [项目研究计划](docs/project_plan.md)；三人职责、交接格式和复核机制见 [团队协作方案](docs/team_workflow.md)。

## 仓库结构

```text
.
|-- audit/                         # 六类审计的定义、方法、结果与局限
|   |-- profile.md
|   |-- duplicates.md
|   |-- leakage.md
|   |-- label_noise.md
|   |-- shortcut_features.md
|   `-- ambiguity.md
|-- docs/
|   |-- project_plan.md            # 统一研究设计与验收标准
|   |-- team_workflow.md           # 三人分工、依赖和交叉复核
|   |-- adjudication_protocol.md   # 人工裁决规则
|   `-- report_outline.md          # 最终报告写作骨架
|-- scripts/                       # 后续加入可复现分析脚本
|-- results/                       # 小型结果表与图；临时文件不入库
|-- suspicious_examples.csv        # 最终排序审计结果
|-- adjudication_memo.csv          # 人工复核与最终裁决
|-- impact_analysis.md             # 数据干预比较
|-- logs/chat.md                   # AI 使用与验证记录
|-- report.pdf                     # 最终自洽报告
|-- starter/                       # 课程提供的协议、manifest 和示例
|-- topic-b-handout.md
|-- topic-b-handout-zh.md
`-- topic-b-handout.pdf
```

## 计划中的复现接口

V1 当前可执行的文档与协议检查为：

```powershell
python scripts/validate_documentation.py
```

该检查验证必需文档、审计 CSV 表头、六类 issue type、公开协议数值和 manifest 的 5574/4460/1114 行数约束。

以下命令定义后续脚本应提供的统一接口；在相应脚本实现前，不把它们声明为已验证命令。

```powershell
python scripts/download_data.py
python scripts/build_dataset.py
python scripts/profile_data.py
python scripts/train_baseline.py
python scripts/audit_duplicates.py
python scripts/audit_leakage.py
python scripts/audit_label_noise.py
python scripts/audit_shortcuts.py
python scripts/build_audit_outputs.py
python scripts/run_interventions.py
python scripts/validate_submission.py
```

最终 README 将补充 Python 版本、主要依赖版本、随机种子、每条命令的输入输出和一次从空目录开始的验证记录。

## 完成定义

项目只有同时满足下列条件才算完成：

- 原始行数、manifest 行数、ID 唯一性和 split 前缀全部通过断言；
- 六类审计均有可复现方法、结果、代表案例、误报和局限；
- `suspicious_examples.csv` 通过协议字段与取值检查；
- high-confidence 发现具备足够强的证据，label-error 具备两个独立信号；
- 至少两名成员复核高风险人工判断；
- 至少两种数据干预在同一评估设置下比较；
- held-out 标签未被修改，训练标签修正以 overlay 保存；
- `report.pdf` 包含至少三个可验证的 Difficulties and Solutions；
- AI usage declaration 与 `logs/chat.md` 一致；
- 所有主要结果可通过 README 中的命令重新生成。

## 学术诚信

AI 可以协助解释要求、检查代码、生成候选分析思路和改善表达，但不能代替人工裁决。任何由 AI 提出的具体样本判断都必须由组员读取原文、检查定量证据并记录验证方式。不得编造审计发现、实验分数或人工一致性。
