# Topic B — 数据集取证与标签审计

本文档说明重新生成全部交付物所需的**环境版本**与**精确命令**。

---

## 1. 交付物

```
audit/profile.md  duplicates.md  leakage.md  label_noise.md  shortcut_features.md  ambiguity.md
scripts/                  全部分析代码
results/                  中间产物与证据表
suspicious_examples.csv   排序后的审计发现（670 行）
adjudication_memo.csv     裁定记录，含被拒候选（444 行）
impact_analysis.md        数据干预对比
logs/chat.md              AI 使用记录
report.pdf                最终报告（由 report.md 生成）
```

`starter/` 为课程起始包（只读）：划分 manifest、审计协议、数据字典、格式样例。

---

## 2. 环境

```powershell
conda activate ai2
```

| 包           | 版本    |
| ------------ | ------- |
| Python       | 3.12.11 |
| scikit-learn | 1.8.0   |
| pandas       | 2.2.3   |
| numpy        | 2.2.6   |
| scipy        | 1.16.0  |
| matplotlib   | 3.10.8  |
| joblib       | 1.5.3   |

与 `requirements.txt` 一致。数值结果由 scikit-learn 决定，上述版本下实测逐位复现。

生成 `report.pdf` 另需 PATH 上有 **pandoc**（实测 3.1.2）与已安装的 **Edge 或 Chrome**。

> 不要用裸 `python` / `pip`——本机上它们指向未安装 scikit-learn 的其他环境。

---

## 3. 精确命令

从干净克隆开始，按顺序执行：

```powershell
conda activate ai2

# 数据与基线信号
python scripts\download_data.py            # 下载 UCI 语料，校验 5574 行 + SHA-256
python scripts\build_dataset.py            # 对齐 manifest → data/canonical_sms.csv
python scripts\train_baseline.py           # word/char 基线，SEED=42

# 数据画像
python scripts\profile_data.py             # → audit/profile.md

# 目标 1-3：重复与泄漏（顺序不可调换，见第 4 节）
python scripts\audit_duplicates.py         # → audit/duplicates.md
python scripts\review_near_duplicates.py   # 合入人工评审，追加评审节
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
python scripts\build_suspicious_examples.py
python scripts\build_submission_outputs.py # → suspicious_examples.csv、adjudication_memo.csv

# 最终报告
python scripts\build_report_pdf.py         # report.md → report.pdf
```

必须用 `python scripts\xxx.py` 形式调用。脚本内部是 `from common import ...`，依赖 Python 把
`scripts/` 放入 `sys.path[0]`，用 `python -m scripts.xxx` 会导入失败。

---

## 4. 执行顺序约束

目标 1–3 的三个脚本互相依赖，必须按上列顺序执行：

- `audit_duplicates.py` **从头重写** `audit/duplicates.md` 并生成近重复候选队列；
- `review_near_duplicates.py` 合入人工评审判断，向该文件追加评审节；
- `audit_leakage.py` 依赖上一步产出的已评审队列汇总跨划分证据。

单独重跑第一步会冲掉第二步追加的评审节；跳过第二步则第三步拿到未评审的队列。

干预脚本依赖各自目标的产物，须在对应审计脚本之后运行；两个汇总脚本须在全部审计脚本之后运行。

---

## 5. 复现校验

`train_baseline.py` 应输出：

```
   n  accuracy  spam_precision  spam_recall  spam_f1  macro_f1    condition
4460  0.982063        0.992395     0.872910 0.928826  0.959282     word_oof
4460  0.982735        0.994307     0.876254 0.931556  0.960839     char_oof
1114  0.991023        0.992908     0.939597 0.965517  0.980179 word_heldout
1114  0.987433        0.992701     0.912752 0.951049  0.971920 char_heldout
```

`build_submission_outputs.py` 应打印 670 行、六类全覆盖、high 占比 0.4522，并通过四项协议断言
（≥35 行 / 六类 / high ≤55% / schema 匹配）。

各步骤均带硬断言：原始语料恰好 5574 行且 SHA-256 匹配，标准表 5574 行（train 4460 /
heldout 1114）、id 唯一、无空文本。断言失败或数字不符，说明环境或数据未对齐。
