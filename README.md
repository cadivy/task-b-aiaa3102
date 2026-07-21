# Topic B — 数据集取证与标签审计

本文档同时承担两个用途：**handout 第 VIII 节要求的复现说明**（第 1、2 节给出 exact
commands 与 software versions），以及队员上手指南（第 3 节起）。

---

## 0. 仓库结构

```
project/
├── audit/                ← 六份审计报告（交付物）
│   ├── profile.md            数据画像
│   ├── duplicates.md         目标 1、2：精确/近重复
│   ├── leakage.md            目标 3：跨 split 泄漏
│   ├── label_noise.md        目标 4：疑似标签错误
│   ├── shortcut_features.md  目标 5：捷径特征
│   └── ambiguity.md          目标 6：模糊样本
├── scripts/              ← 全部分析代码，见第 2 节
├── results/              ← 中间产物与证据表
├── starter/              ← 课程起始包（只读）
│   ├── data/split_manifest.csv       固定的 train/heldout 划分
│   ├── configs/audit_protocol.json   六类问题定义 + 阈值
│   └── examples/                     提交格式样例
├── suspicious_examples.csv   ← 交付物：排序后的审计发现
├── adjudication_memo.csv     ← 交付物：裁定记录（含被拒候选）
├── impact_analysis.md        ← 交付物：数据干预对比
├── logs/chat.md              ← 交付物：AI 使用记录
├── report.pdf                ← 交付物：最终报告
├── requirements.txt
└── topic-b-handout.md    ← 需求文档，先读这个
```

---

## 1. 环境（第一步，必做）

**用 `ai2` conda 环境**：

```powershell
conda activate ai2
```

⚠️ **不要用裸 `python` / `pip`**。这台机器上它们指向不同环境，且都没装 scikit-learn：

```
python  →  D:\pYthon\python.exe        (无 sklearn)
pip     →  D:\Anaconda\envs\ftec\...   (无 sklearn)   ← 甚至不是同一个环境
```

VS Code 里记得把解释器切到 `ai2`（`Ctrl+Shift+P` → Python: Select Interpreter →
`D:\Anaconda\envs\ai2\python.exe`）。

### Software versions（实测，与 `requirements.txt` 一致）

| 包           | 版本    |
| ------------ | ------- |
| Python       | 3.12.11 |
| scikit-learn | 1.8.0   |
| pandas       | 2.2.3   |
| numpy        | 2.2.6   |
| scipy        | 1.16.0  |
| matplotlib   | 3.10.8  |
| joblib       | 1.5.3   |

> 决定数值结果的是 scikit-learn。全部产物在上述版本下实测**逐位复现**（word heldout 99.1023%）。

---

## 2. 跑通公共底座（一次性，约 10 秒）

**严格按这个顺序**，后一步依赖前一步：

```powershell
conda activate ai2
python scripts\download_data.py     # 1. 下载原始语料   (~2s，需要联网)
python scripts\build_dataset.py     # 2. 建标准工作表   (~1s)
python scripts\train_baseline.py    # 3. 训练基准模型   (~8s)
```

> ⚠️ 必须用 `python scripts\xxx.py` 这种形式跑。**不要**用 `python -m scripts.xxx`——
> 脚本内部是 `from common import ...`，靠 Python 把 `scripts/` 放进 `sys.path[0]` 才能找到。

每步都有硬断言，**跑通了就等于数据是对的**：

| 步骤                  | 校验了什么                                                                |
| --------------------- | ------------------------------------------------------------------------- |
| `download_data.py`  | 原始文件恰好 5574 行；记录 SHA-256 到`results/data_provenance.json`     |
| `build_dataset.py`  | 5574 行 / train 4460 / heldout 1114 / id 唯一 / 前缀 T·H 正确 / 无空文本 |
| `train_baseline.py` | 输出四行指标，对照下表                                                    |

### 实测基准值（跑出来应该完全一致）

```
   n  accuracy  spam_precision  spam_recall  spam_f1  macro_f1    condition
4460  0.982063        0.992395     0.872910 0.928826  0.959282     word_oof
4460  0.982735        0.994307     0.876254 0.931556  0.960839     char_oof
1114  0.991023        0.992908     0.939597 0.965517  0.980179 word_heldout   ← 官方基线 99.10%
1114  0.987433        0.992701     0.912752 0.951049  0.971920 char_heldout
```

其他实测数：原始语料 SHA-256 开头 `1587ea43…`，归一化后唯一文本 **5159** 条
（→ 5574−5159 = **415 行**参与精确重复，这是 A 的起点参考）。

如果哪个断言炸了或数字对不上，**先别往下做**，八成是数据没对齐或环境不对。

### 2.1 重新生成全部交付物（exact commands）

从干净克隆开始，按顺序执行以下命令即可重建 `audit/`、`results/`、
`suspicious_examples.csv`、`adjudication_memo.csv` 与 `impact_analysis.md`：

```powershell
conda activate ai2

# 底座：数据与基线信号
python scripts\download_data.py            # 下载 UCI 语料，校验 5574 行 + SHA-256
python scripts\build_dataset.py            # 对齐 manifest → data/canonical_sms.csv
python scripts\train_baseline.py           # word/char 基线，SEED=42

# 数据画像
python scripts\profile_data.py             # → audit/profile.md

# 目标 1-3：重复与泄漏（必须按此顺序，见第 7 节）
python scripts\audit_duplicates.py         # → audit/duplicates.md、近重复候选队列
python scripts\review_near_duplicates.py   # 合入人工判断，追加评审节
python scripts\audit_leakage.py            # → audit/leakage.md

# 目标 4、6：标签错误与模糊
python scripts\audit_label_noise.py
python scripts\build_label_noise_outputs.py  # → audit/label_noise.md、audit/ambiguity.md

# 目标 5：捷径特征
python scripts\audit_shortcuts.py          # → audit/shortcut_features.md

# 目标 7：数据干预
python scripts\label_overlay_experiment.py
python scripts\intervention_leakage_eval.py
python scripts\intervention_ambiguity_eval.py
python scripts\run_impact_interventions.py # → impact_analysis.md

# 汇总提交文件
python scripts\build_suspicious_examples.py  # → suspicious_examples_dup_leak.csv
python scripts\build_submission_outputs.py   # → suspicious_examples.csv、adjudication_memo.csv

# 最终报告
python scripts\build_report_pdf.py           # report.md → report.pdf
```

> `build_report_pdf.py` 需要 PATH 上有 **pandoc**（实测 3.1.2）以及已安装的
> **Edge 或 Chrome**（走 headless print-to-pdf）。这条链路避开了 LaTeX 依赖——
> 本项目机器上没有任何 TeX 引擎。

最后一步会打印协议硬校验结果（≥35 行 / 六类全覆盖 / high ≤55% / schema 匹配），
四项断言全过才算通过。

---

## 3. 底座产出了什么

### 数据（`.gitignore` 里，不进 git，每人本地生成）

| 文件                                      | 内容                                                                     |
| ----------------------------------------- | ------------------------------------------------------------------------ |
| `raw/SMSSpamCollection`                 | UCI 原始语料，TAB 分隔无表头                                             |
| **`data/canonical_sms.csv`**      | **标准工作表 5574 行**：`id, split, uci_row_number, text, label` |
| `data/train.csv` / `data/heldout.csv` | 按 split 切好的两份                                                      |

> 数据不进 git 但**完全可复现**——manifest 固定 + 断言 + SHA-256，每人生成的都逐字节相同。

### 模型信号（进 git，**别各自重训**）

| 文件                                          | 内容                          | 谁要用            |
| --------------------------------------------- | ----------------------------- | ----------------- |
| **`results/all_predictions.csv`**     | 全部 5574 行的 word/char 概率 | **B [4,6]** |
| **`results/heldout_predictions.csv`** | heldout 1114 行的概率         | **C [5]**   |
| `results/oof_predictions.csv`               | train 4460 行的 OOF 概率      | —                |
| `results/baseline_metrics.csv/json`         | 基线性能                      | 报告              |
| `results/baseline_top_features.csv`         | 词模型 top40 spam/ham 特征词  | 报告              |

关键列：`word_p_spam` `word_pred` `char_p_spam` `char_pred` `prediction_source`

**为什么训两个模型？**

- `word` = **正牌 baseline**（TF-IDF 词/bigram + 逻辑回归）。官方分 99.10% 就是它，T5 的 `full_text`
  对照、干预实验全用它。
- `char` = **辅助信号源**（字符 3-5gram）。存在的唯一理由是满足协议对 label_error 的
  「**至少两个独立信号**」要求，顺便抓 `fr33` `w1n` 这类混淆写法。

**为什么训练集用 OOF（5折）？**
如果用全训练集训练再预测训练集自己，模型已经背下了每条的标签——那「模型反对这个标签」
这个信号就废了。OOF 保证给每条打分的模型**从没见过这条**。这是 T4 能成立的前提。

---

## 4. 公共契约：这些**不要改**

`common.py` 里有三块是**约定，不是算法**。算法各写各的没关系，约定必须只有一份：

| 组件                                             | 是什么                                                                              | 谁用                   | 改了会怎样                                        |
| ------------------------------------------------ | ----------------------------------------------------------------------------------- | ---------------------- | ------------------------------------------------- |
| **`normalize_text`**                     | 精确重复的官方规则（小写 + 空白折叠），就是`audit_protocol.json` 里那句定义的实现 | **A + B**        | A 建的重复簇和 B 排除的近邻对不上号，数字互相矛盾 |
| **`load_canonical`** / `load_protocol` | 唯一数据真相源入口；阈值(0.92)从 protocol 读，**不硬编码**                    | **A + C**        | 用错数据，或阈值散落各处                          |
| **`classification_metrics`**             | 统一指标口径，**`pos_label="spam"`**                                        | **A + C + 干预** | 各人数字没法横向比                                |

> **为什么盯 spam 而不是 accuracy**：spam 只占 13.4%，全猜 ham 就有 86.62%。
> 干预实验里剔除泄漏后总准确率只掉 0.05 个点，但 **spam recall 掉了 3 个点**——
> 总准确率会把真相藏起来。

### 可以搬走的部分

`common.py` 里这些**只有 C [5] 用**，C 可以直接剪切进自己的 `audit_shortcuts.py`：

- `PROMO_TOKENS`（15 个促销词表）
- `URL_RE` / `PHONE_RE` / `CURRENCY_RE` / `TOKEN_RE`
- `shallow_features()`（12 个手工特征）
- `mask_promotional_tokens()`

搬走前在群里说一声即可，不影响 A 和 B。

### 改 `common.py` 的规矩

要加函数 → 群里说 + 走 PR，**不要三个人同时改这个文件**（必冲突）。

---

## 5. 三人分工：你从哪开始

前提：第 1、2 节跑完。

### A — [目标 1,2,3] 重复 + 泄漏

- **读**：`data/canonical_sms.csv`（`load_canonical()`）
- **不需要** baseline 预测
- **写**：`scripts/audit_duplicates.py`、`scripts/audit_leakage.py` → `audit/duplicates.md`、`audit/leakage.md`
- **要点**：
  - 精确重复 = `groupby(normalize_text)`，簇内查 label / split 冲突
  - 近重复 = TF-IDF 余弦 ≥ **0.92**（从 `load_protocol()` 读，别硬编码），**要做阈值敏感度分析**并说明为什么是 0.92
  - 泄漏 = 把上面两个**跨 split 做**；另外查 `uci_row_number` 位置有没有暴露标签

### B — [目标 4,6] 标错 + 模糊

- **读**：`results/all_predictions.csv`（**不要自己重训模型**）
- **写**：`scripts/audit_label_noise.py` → `audit/label_noise.md`、`audit/ambiguity.md`
- **要点**：
  - 标错需 **≥2 个独立信号**（word 反对 / char 反对 / 近邻反对）。
    **单靠模型判错绝不能定案**——必须叠人工策略复核。
  - 模糊 ≠ 低置信度。要**主动保留假阳性案例**（概率骑在 0.5 但内容就是普通 ham），
    证明「模型不确定」不等于「语义模糊」。
  - 用 `normalize_text` 排除完全相同文本的近邻，否则重复副本会自我污染证据。

### C — [目标 5] 捷径

- **读**：`data/canonical_sms.csv` + `results/heldout_predictions.csv`（当 `full_text` 对照组）
- **写**：`scripts/audit_shortcuts.py` → `audit/shortcut_features.md`
- **要点**：
  - 浅层模型**只喂手工特征，绝不给原始词序**
  - 对照组必须**同算法（逻辑回归）**，唯一变量是特征——否则混淆了变量
  - 注意协议的 70% 阈值形同虚设（多数类已 86.62%），别只报「过阈值」
  - 逻辑回归的**标准化系数**要导出，这是「具体是哪个捷径」的证据

### 已完成的收尾

- **[目标 7] data intervention** —— `run_impact_interventions.py` 等四个脚本，
  九种干预 → `impact_analysis.md`
- **集成** —— `build_submission_outputs.py` 汇总三方 findings →
  `suspicious_examples.csv`（670 行）、`adjudication_memo.csv`（444 行），
  并内置协议硬校验

- **报告** —— `report.md`（英文，656 行）→ `report.pdf`（22 页），
  由 `build_report_pdf.py` 生成；`report_zh_draft_new.md` 为中文工作稿

---

## 6. 输出格式契约（现在就说好，最后才拼得起来）

每人往 `suspicious_examples.csv` 写行时用**同一个 9 列 schema**（见 `audit_protocol.json`）：

```
id, split, issue_type, rank, confidence, evidence_1, evidence_2, recommended_action, short_explanation
```

`issue_type` 只能是：`exact_duplicate` `near_duplicate` `leakage` `label_error` `shortcut` `ambiguous`
`confidence` 只能是：`low` `medium` `high`

**协议的硬约束**（`build_submission_outputs.py` 每次运行都会断言）：

| 规则                                    | 值             | 含义                                            |
| --------------------------------------- | -------------- | ----------------------------------------------- |
| `strict_submission_min_rows`          | 35             | 至少 35 行                                      |
| `strict_submission_min_issue_types`   | 6              | 六类**都要**覆盖                          |
| `strict_high_confidence_max_fraction` | **0.55** | high 最多占 55%——**逼你做不确定性校准** |

> 评分用的是老师手里的 **hidden audit key**，里面埋了 **false-positive trap**。
> 乱报 high 会扣分。宁可少报、把「被拒候选」写清楚。

---

## 7. 已知的坑

### 🟡 `keep_default_na=False` 不能删

`load_canonical()` 里读 CSV 带了这个参数。默认 pandas 会把 `"NA"` `"null"` `"nan"`
这些**字符串**转成 NaN——短信里真的有人发 "NA"，那条数据就被悄悄破坏了。

### 🟡 别自己重训 baseline

B 和 C 直接读 `results/*.csv`。各自重训会导致 `word_pred` 不一致，
T5 报告里的 `full_text` 对照组和 T4 用的信号**对不上号**，交叉引用直接崩。

### 🟡 seed 固定不能动

`SEED = 42` 在 `train_baseline.py` 里。handout 要求 README 写明「重生成 artifacts 的
exact commands」——改了 seed 就没法复现了。

### 🔴 目标 1–3 的三个脚本必须按顺序跑

```powershell
python scripts\audit_duplicates.py        # 1. 建簇、建候选队列，从头重写 duplicates.md
python scripts\review_near_duplicates.py  # 2. 合入人工判断，向 duplicates.md 追加评审节
python scripts\audit_leakage.py           # 3. 汇总跨 split 证据，写 leakage.md
```

`audit_duplicates.py` 会**从头重写** `duplicates.md`，把第 2 步追加的
「Near-Duplicate Review Results」整节冲掉。单独重跑第 1 步 = 报告缺 39 行。
第 3 步依赖第 2 步产出的 `near_duplicate_review_queue.csv`，跳过就拿到未评审的队列。

人工判断存在 `results/duplicate/near_duplicate_manual_review_decisions.csv`，
按 `pair_key = "|".join(sorted([id_a, id_b]))` 索引——**别改成按 `pair_id` 索引**，
`pair_id` 只是展示用的序号，候选集合一变就会错位。

### 🟡 别改 heldout 标签

handout 硬规定。测试重标只能用 **overlay 文件**表示（`results/training_label_overlay.csv`），
不覆盖原始标签。heldout 的疑似标错**只做标记，不改**---

## 8. 快速自检

确认底座就绪（在 `project/` 目录下跑）：

```powershell
conda activate ai2
python -c "import sys; sys.path.insert(0,'scripts'); from common import load_canonical; import pandas as pd; df=load_canonical(); p=pd.read_csv('results/all_predictions.csv',keep_default_na=False); h=p[p.split=='heldout']; print('canonical:',len(df),df['split'].value_counts().to_dict()); print('baseline heldout acc:',round((h.word_pred==h.label).mean(),6))"
```

应输出：

```
canonical: 5574 {'train': 4460, 'heldout': 1114}
baseline heldout acc: 0.991023
```

对上了就可以开工。对不上就回第 1、2 节。
