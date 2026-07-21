
帮我 git push 一下
Bash Check status, branch, remote
IN
cd /d/_NewFactory/pyai/project && git status --short && echo "---BRANCH---" && git branch --show-current && echo "---REMOTE---" && git remote -v && echo "---AHEAD---" && git log --oneline origin/HEAD..HEAD 2>/dev/null | head

OUT
---BRANCH---
main
---REMOTE---
origin	git@github.com:cadivy/task-b-aiaa3102.git (fetch)
origin	git@github.com:cadivy/task-b-aiaa3102.git (push)
---AHEAD---
7c7ae84 add report new
9c3b034 fix: report the overlay intervention as a null result
工作区干净，main 领先 origin 两个提交（其中 add report new 是你自己提交的新报告）。推送：

Bash Push main to origin
IN
git push origin main 2>&1 | tail -20

OUT
To github.com:cadivy/task-b-aiaa3102.git
 ! [rejected]        main -> main (fetch first)
error: failed to push some refs to 'github.com:cadivy/task-b-aiaa3102.git'
hint: Updates were rejected because the remote contains work that you do not
hint: have locally. This is usually caused by another repository pushing to
hint: the same ref. If you want to integrate the remote changes, use
hint: 'git pull' before pushing again.
hint: See the 'Note about fast-forwards' in 'git push --help' for details.
远程有别人的新提交。先看看是什么：

Bash Fetch and compare divergence
IN
git fetch origin && echo "---THEIRS (remote not local)---" && git log --oneline HEAD..origin/main && echo "---OURS (local not remote)---" && git log --oneline origin/main..HEAD && echo "---FILES THEY TOUCHED---" && git diff --stat HEAD...origin/main

OUT
From github.com:cadivy/task-b-aiaa3102
   8a9adbd..845922c  main       -> origin/main
---THEIRS (remote not local)---
845922c Cap impact interventions at 30 training rows
44422b1 feat: complete English presentation and final report
---OURS (local not remote)---
7c7ae84 add report new
9c3b034 fix: report the overlay intervention as a null result
---FILES THEY TOUCHED---
 .gitattributes                                     |   3 +
 adjudication_memo.csv                              |  37 +
 audit/duplicates.md                                | 125 ++++
 audit/leakage.md                                   |  97 +++
 audit/profile.md                                   | 100 +++
 audit/shortcut_features.md                         |  75 ++
 impact_analysis.md                                 |  24 +-
 logs/chat.md                                       |  27 +
 output/pdf/report.pdf                              | 372 ++++++++++
 presentation/cadivy_shortcut_interventions_en.pptx | Bin 0 -> 32654 bytes
 report.pdf                                         | 372 ++++++++++
 results/figures/intervention_metrics.png           | Bin 0 -> 55529 bytes
 results/impact/intervention_metrics.csv            |   8 +-
 results/impact/intervention_summary.json           |  14 +-
 scripts/build_final_submission.py                  | 139 ++++
 scripts/generate_report.py                         | 757 +++++++++++++++++++++
 scripts/run_impact_interventions.py                |  96 ++-
 suspicious_examples.csv                            |  44 +-
 18 files changed, 2257 insertions(+), 33 deletions(-)
队友推了两个提交，正好补上了我之前说的缺口（adjudication_memo.csv、audit/ 六件套、重建的 suspicious_examples.csv、report.pdf）。先确认会不会冲突：

Bash List files our commits changed
IN
echo "=== OUR 2 COMMITS TOUCHED ===" && git diff --stat origin/main...HEAD --name-only 2>/dev/null; git log --name-only --oneline origin/main..HEAD | grep -v "^[0-9a-f]\{7\} " | sort -u | grep -v '^$'

OUT
=== OUR 2 COMMITS TOUCHED ===
report_zh_draft.md
report_zh_draft_new.md
report_zh_draft.md
report_zh_draft_new.md
没有文件重叠——我们只动了 report_zh_draft*.md，他们没碰。合并推送：

Bash Merge origin/main and push
IN
git merge origin/main -m "Merge remote-tracking branch 'origin/main'" 2>&1 | tail -5 && git push origin main 2>&1 | tail -5

OUT
 create mode 100644 presentation/cadivy_shortcut_interventions_en.pptx
 create mode 100644 report.pdf
 create mode 100644 results/figures/intervention_metrics.png
 create mode 100644 scripts/build_final_submission.py
 create mode 100644 scripts/generate_report.py
To github.com:cadivy/task-b-aiaa3102.git
   845922c..3ab0a6e  main -> main
推送成功。但队友那个提交动了干预实验的数字，我核对一下对报告的影响：

Bash Check metric changes from cap commit
IN
git diff 8a9adbd 845922c -- results/impact/intervention_metrics.csv | head -30

OUT
diff --git a/results/impact/intervention_metrics.csv b/results/impact/intervention_metrics.csv
index 76592c1..742b89d 100644
--- a/results/impact/intervention_metrics.csv
+++ b/results/impact/intervention_metrics.csv
@@ -1,9 +1,9 @@
 condition,intervention_family,evaluation_scope,random_seed,train_rows,heldout_rows,train_spam_rows,heldout_spam_rows,accuracy,spam_precision,spam_recall,spam_f1,macro_f1,tn,fp,fn,tp,notes
 baseline_public_labels,baseline,heldout,42,4460,1114,598,149,0.9910233393177738,0.9929078014184397,0.9395973154362416,0.9655172413793104,0.9801786413294901,964,1,9,140,Original public training labels evaluated on all held-out rows.
 baseline_excluding_leaked_heldout,leakage_aware_evaluation,heldout,42,4460,1051,598,99,0.9904852521408183,0.989010989010989,0.9090909090909091,0.9473684210526315,0.9710691477648095,951,1,9,90,Evaluation sensitivity after excluding held-out rows with exact or reviewed near train partners.
-remove_leakage_train_partners,leakage_removal,heldout,42,4389,1114,541,149,0.9901256732495511,1.0,0.9261744966442953,0.9616724738675958,0.9780026460012889,965,0,11,138,Retrain after removing training rows that are exact or reviewed near partners of held-out rows.
+remove_leakage_train_partners,leakage_removal,heldout,42,4430,1114,575,149,0.9919210053859964,1.0,0.9395973154362416,0.9688581314878892,0.9821082818347131,965,0,9,140,Retrain after removing training rows that are exact or reviewed near partners of held-out rows.
 training_label_overlay,label_overlay,heldout,42,4460,1114,585,149,0.9892280071813285,0.9928057553956835,0.9261744966442953,0.9583333333333334,0.9760738831615121,964,1,11,138,Apply training-only label-error overlay; held-out labels remain unchanged.
 exclude_ambiguous_training_rows,ambiguous_row_handling,heldout,42,4448,1114,586,149,0.9901256732495511,1.0,0.9261744966442953,0.9616724738675958,0.9780026460012889,965,0,11,138,Retrain after excluding training rows adjudicated as ambiguous policy cases.
-shortcut_cue_masking,shortcut_masking,heldout,42,4460,1114,598,149,0.9874326750448833,0.9655172413793104,0.9395973154362416,0.9523809523809523,0.9725710346186044,960,5,9,140,"Replace URLs, phone-like strings, money/rate markers, digit runs, and promotional lexicon before training and evaluation."
-duplicate_deduplication,duplicate_deduplication,heldout,42,4043,1114,450,149,0.9883303411131059,0.9857142857142858,0.9261744966442953,0.9550173010380623,0.9741564070945856,963,2,11,138,Keep the earliest training row in each exact or reviewed train-train near-duplicate component.
-combined_training_view,combined,heldout,42,3982,1114,387,149,0.9847396768402155,0.9647887323943662,0.9194630872483222,0.9415807560137457,0.9664021487864289,960,5,12,137,"Apply leakage-partner removal, duplicate de-duplication, ambiguous-row exclusion, remaining label overlay, and shortcut cue masking."
+shortcut_cue_masking,shortcut_masking,heldout,42,4460,1114,598,149,0.9847396768402155,0.9925373134328358,0.8926174496644296,0.9399293286219081,0.9655944843623679,964,1,16,133,"Replace URLs, phone-like strings, money/rate markers, digit runs, and promotional lexicon before training and evaluation."
+duplicate_deduplication,duplicate_deduplication,heldout,42,4430,1114,591,149,0.9892280071813285,0.9790209790209791,0.9395973154362416,0.958904109589041,0.9763528812408016,962,3,9,140,Keep the earliest training row in each exact or reviewed train-train near-duplicate component.
+combined_training_view,combined,heldout,42,4430,1114,570,149,0.9847396768402155,0.9925373134328358,0.8926174496644296,0.9399293286219081,0.9655944843623679,964,1,16,133,"Apply leakage-partner removal, duplicate de-duplication, ambiguous-row exclusion, remaining label overlay, and shortcut cue masking."
Bash Inspect cap implementation
IN
git show 845922c --stat | head -12 && echo "=== CAP LOGIC ===" && git diff 8a9adbd 845922c -- scripts/run_impact_interventions.py | grep -n "^[+-].*\(30\|max_impact\|cap\|head\|limit\)" | head -25

OUT
commit 845922c9f15efd98c98bfeb9c694866a9a1ef7ba
Author: HW-LI183 <hli183@conncet.hkust-gz.edu.cn>
Date:   Tue Jul 21 20:07:35 2026 +0800

    Cap impact interventions at 30 training rows

    # Conflicts:
    #       impact_analysis.md
    #       scripts/run_impact_interventions.py

 impact_analysis.md                       | 18 ++++----
 results/impact/intervention_metrics.csv  |  8 ++--
=== CAP LOGIC ===
9:+MAX_TRAIN_INTERVENTION_ROWS = 30
24:+def cap_train_ids(ids: set[str], order: dict[str, tuple[int, str]], limit: int = MAX_TRAIN_INTERVENTION_ROWS) -> set[str]:
25:+    return set(sorted(ids, key=lambda item: order.get(item, (10**9, item)))[:limit])
28:+def cap_label_mapping(mapping: dict[str, str], order: dict[str, tuple[int, str]], limit: int = MAX_TRAIN_INTERVENTION_ROWS) -> dict[str, str]:
29:+    kept_ids = sorted(mapping, key=lambda item: order.get(item, (10**9, item)))[:limit]
33:+def cap_mask_train_ids(train: pd.DataFrame, limit: int = MAX_TRAIN_INTERVENTION_ROWS) -> set[str]:
38:+    return {row_id for _, row_id in sorted(candidates)[:limit]}
79:+        "The unified experiment compares five data-intervention families: leakage handling, training-label overlay, ambiguous-row handling, shortcut masking, and duplicate de-duplication. Canonical data and held-out labels are not edited; each condition is an experimental view produced by `scripts/run_impact_interventions.py`. Each training-set intervention is capped at at most 30 modified or removed training rows, selected deterministically by original UCI row order from the eligible candidate set. A separate adjudication-aware evaluation is produced by `scripts/intervention_ambiguity_eval.py`.",
106:+            f"The training-side leakage intervention has {summary['leakage_train_partner_candidate_rows']} eligible training partners, but applies the 30-row cap and removes {summary['leakage_train_partner_rows_removed']} of them before retraining on {int(leakage_remove['train_rows'])} rows. It reaches {pct(leakage_remove['accuracy'])} accuracy and {pct(leakage_remove['spam_f1'])} spam F1. This does not edit held-out labels; it estimates whether the model was benefiting from memorized or near-memorized training rows under a limited intervention budget.",
129:+            f"Duplicate de-duplication has {summary['duplicate_training_candidate_rows']} eligible repeated training rows, but removes only {summary['duplicate_training_rows_removed']} under the 30-row cap by prioritizing earliest corpus order. The retrained model uses {int(dedup['train_rows'])} rows and reaches {pct(dedup['accuracy'])} accuracy with {pct(dedup['spam_f1'])} spam F1. This intervention tests whether repeated messages overweight common templates under a bounded edit budget.",
133:-            f"The combined training view removes leakage partners, removes duplicate repeats, excludes ambiguous training rows, applies remaining training-label overlay entries, and masks shortcut cues. It trains on {int(combined['train_rows'])} rows and reaches {pct(combined['accuracy'])} accuracy with {pct(combined['spam_f1'])} spam F1. This is a conservative stress test rather than a proposed replacement dataset. Its lower score summarizes the cumulative impact of data-quality issues: each issue is individually modest, but together they reduce confidence that the original headline metric fully represents clean, independent generalization.",
134:+            f"The combined training view applies the same 30-row cap to row removals, then applies capped label overlay and capped shortcut masking. It trains on {int(combined['train_rows'])} rows and reaches {pct(combined['accuracy'])} accuracy with {pct(combined['spam_f1'])} spam F1. This is a bounded stress test rather than a proposed replacement dataset, so the result should be read as directional evidence about cumulative data-quality sensitivity.",
158:+    leakage_train_ids = cap_train_ids(leakage_train_candidate_ids, row_order)
164:+    label_mapping = cap_label_mapping(label_mapping_candidates, row_order)
170:+    ambiguous_ids = cap_train_ids(ambiguous_candidate_ids, row_order)
175:+    shortcut_mask_ids = cap_mask_train_ids(train)
183:+    duplicate_remove_ids = cap_train_ids(duplicate_candidate_remove_ids, row_order)
189:+    combined_remove = cap_train_ids(combined_candidate_remove, row_order)
193:+    combined_mask_ids = cap_train_ids(shortcut_mask_ids - combined_remove, row_order)
推送成功（845922c..3ab0a6e）。但队友的提交对我们刚写的报告有实质影响，你需要知道。

推送结果
合并干净——我们只动 report_zh_draft*.md，队友没碰这两个文件。队友（HW-LI183）补上的正是我之前指出的缺口：adjudication_memo.csv(37 行)、audit/ 下补齐 profile/duplicates/leakage/shortcut_features、重建的 suspicious_examples.csv(44 行)、report.pdf、build_final_submission.py、generate_report.py。

⚠️ 但 Cap impact interventions at 30 training rows 让报告 §7 的数字全部过期
这个提交给所有训练侧干预加了 MAX_TRAIN_INTERVENTION_ROWS = 30 的上限：

干预	我报告里写的	现在实际
移除泄漏伙伴行	−71 行	−30
按簇去重	−417 行	−30
组合训练视图	4460→3982	4460→4430
shortcut 遮蔽 spam 召回	0.9396	0.8926
其中一处不只是数字变了，是论证塌了。 报告 §7.3 我写的是：

删掉 417 行（近 10% 训练数据）与删掉 12 行效果相同，说明被删的绝大多数是冗余副本，模型本就未从中获得额外信息——这从反面印证了 §3.1 的重复发现。

去重现在只删 30 行，这个"规模跨 35 倍而效果相同"的对比不存在了。同理 §7.3 那句"四个条件的 spam 召回全部落在 92.6174%"、§7.4 的组合视图分析、§7.6 的整张 delta 表，都要重算。

另外 §7.5 的交叉验证也失效了——run_impact_interventions.py 加了 cap，但 B 的三个单目标脚本没加，两套实现现在不会再给出一致数字。

我对这个 cap 的看法
我怀疑它源于 audit_protocol.json 里的 max_impact_examples: 30。但那个字段按字面读是限制 impact analysis 里展示多少个样例，不是限制干预能删多少训练行。把去重上限设成 30，而语料里有 417 行重复副本，会让"去重"这个干预基本测不出东西——它现在删的是 7% 的重复行。

不过这是队友的判断，我不清楚他们是不是有别的理由（比如老师另外说过什么）。建议你先跟他确认 cap 的依据，再决定报告怎么改。两条路：

cap 站得住 → 我按新数字重写 §7，并把论证从"规模无关"改成"有限编辑预算下的方向性证据"（队友改写的 impact_analysis.md 已经是这个口径）
cap 是误读 → 应该回退，impact_analysis.md 和 report.pdf 也要跟着重生成
要我先把 §7 按现有数字更新，还是等你问完队友？

如果他是对的，他的部分都做完了吧，只用改 draft 吧
好问题——但得先验证他那边是不是真的都一致了。查一下:

Bash Check impact_analysis consistency
IN
cd /d/_NewFactory/pyai/project && echo "=== impact_analysis.md 是否用新数字 ===" && grep -n "4430\|4389\|4043\|3982\|30-row\|cap" impact_analysis.md | head -12

OUT
=== impact_analysis.md 是否用新数字 ===
5:The unified experiment compares five data-intervention families: leakage handling, training-label overlay, ambiguous-row handling, shortcut masking, and duplicate de-duplication. Canonical data and held-out labels are not edited; each condition is an experimental view produced by `scripts/run_impact_interventions.py`. Each training-set intervention is capped at at most 30 modified or removed training rows, selected deterministically by original UCI row order from the eligible candidate set. A separate adjudication-aware evaluation is produced by `scripts/intervention_ambiguity_eval.py`.
15:| `remove_leakage_train_partners` | leakage_removal | 4430 | 1114 | 99.19% | 100.00% | 93.96% | 96.89% | 98.21% | Retrain after removing training rows that are exact or reviewed near partners of held-out rows. |
19:| `duplicate_deduplication` | duplicate_deduplication | 4430 | 1114 | 98.92% | 97.90% | 93.96% | 95.89% | 97.64% | Keep the earliest training row in each exact or reviewed train-train near-duplicate component. |
20:| `combined_training_view` | combined | 4430 | 1114 | 98.47% | 99.25% | 89.26% | 93.99% | 96.56% | Apply leakage-partner removal, duplicate de-duplication, ambiguous-row exclusion, remaining label overlay, and shortcut cue masking. |
31:The training-side leakage intervention has 71 eligible training partners, but applies the 30-row cap and removes 30 of them before retraining on 4430 rows. It reaches 99.19% accuracy and 96.89% spam F1. This does not edit held-out labels; it estimates whether the model was benefiting from memorized or near-memorized training rows under a limited intervention budget.
51:Duplicate de-duplication has 417 eligible repeated training rows, but removes only 30 under the 30-row cap by prioritizing earliest corpus order. The retrained model uses 4430 rows and reaches 98.92% accuracy with 95.89% spam F1. This intervention tests whether repeated messages overweight common templates under a bounded edit budget.
55:The combined training view applies the same 30-row cap to row removals, then applies capped label overlay and capped shortcut masking. It trains on 4430 rows and reaches 98.47% accuracy with 93.99% spam F1. This is a bounded stress test rather than a proposed replacement dataset, so the result should be read as directional evidence about cumulative data-quality sensitivity.
Bash Check B single-target intervention outputs
IN
echo "=== B 的单目标脚本产物(未加cap) ===" && /d/Anaconda/envs/ai2/python.exe -c "
import json
for f in ['results/intervention_leakage_eval.json','results/label_overlay_experiment.json','results/intervention_ambiguity_eval.json']:
    d=json.load(open(f))
    print(f); print(' ',str(d)[:260]); print()
"

OUT
=== B 的单目标脚本产物(未加cap) ===
results/intervention_leakage_eval.json
  {'intervention': 'leakage_aware_evaluation', 'description': 'Drop held-out rows recoverable from training, re-score frozen baseline.', 'heldout_rows_full': 1114, 'leaked_rows_removed': 63, 'leaked_rows_predicted_correctly': 63, 'heldout_rows_clean': 1051, 'ful

results/label_overlay_experiment.json
  {'seed': 42, 'overlay_rows_applied': 13, 'heldout_baseline': {'n': 1114, 'accuracy': 0.9910233393177738, 'spam_precision': 0.9929078014184397, 'spam_recall': 0.9395973154362416, 'spam_f1': 0.9655172413793104, 'macro_f1': 0.9801786413294901, 'confusion_matrix_h

results/intervention_ambiguity_eval.json
  {'intervention': 'adjudication_aware_evaluation', 'description': 'Drop held-out rows the audit judged ambiguous or mislabelled, re-score frozen baseline.', 'ambiguous_heldout_ids': ['H0030', 'H0550'], 'suspected_label_error_heldout_ids': ['H0143', 'H0896'], 'c
Bash Check if report.pdf has stale numbers
IN
/d/Anaconda/envs/ai2/python.exe -c "
import re
d=open('report.pdf','rb').read().decode('latin-1')
for n in ['4043','3982','4389','4430','98.83','98.47','91.95','89.26']:
    print(n, 'FOUND' if n in d else '-')
" 2>&1; echo "=== report.pdf vs cap commit 时序 ==="; git log --oneline --name-only 44422b1 -1 | grep -c "report.pdf"; git log --format="%h %s" 44422b1 845922c

OUT
The user doesn't want to proceed with this tool use. The tool use was rejected (eg. if it was a file edit, the new_string was NOT written to the file). STOP what you are doing and wait for the user to tell you how to proceed.

Note: The user's next message may contain a correction or preference. Pay close attention — if they explain what went wrong or how they'd prefer you to work, consider saving that to memory for future sessions.
我的意思是，我想的是如果合并这个 commit，要改很多东西的话，那就不合并了；如果只用改 draft，那就可以。当然，你现在只用判断，不用实际修改，也不用变更版本
只用判断，不动任何东西。

先纠正我上一轮的一个错误
我说"§7.5 交叉验证也失效了"——这是错的。cap 只作用于训练侧干预，而交叉验证的三个共有条件里：泄漏感知评估是评估侧（冻结模型、只丢 held-out 行，不受 cap 影响，仍是 63 行）、标签 overlay 只有 13 条（低于 30 的上限，没被截）、基线本身不变。这三个数字两套实现依然一致。我当时是从"cap 加在统一脚本上、没加在 B 的脚本上"推的，没核对实际产物就下了结论。

合并这个 commit 要改多少
我核对过的部分——他自己那一摊是干净的：

产物	状态
impact_analysis.md	已完整重生成，正文叙述也改成了 "30-row cap / bounded edit budget" 口径 ✓
intervention_metrics.csv / summary.json	已重生成 ✓
B 的三个单目标干预产物	不受 cap 影响，无需改 ✓
suspicious_examples.csv / adjudication_memo.csv	与干预实验无关，不受影响 ✓
但不止改 draft——report.pdf 大概率也是旧数字。 依据是提交顺序：44422b1（加入 report.pdf）在前，845922c（加 cap）在后，而 cap 那个提交没有碰 report.pdf。所以 PDF 里存的应该还是 4043 / 3982 那套。这一条我没实际验证——刚才查 PDF 内容的命令被你中断了，是从提交顺序推的。

如果这个推断成立，改动范围是两处：

report_zh_draft_new.md §7 — 实质性重写，不是替换数字。有一个论证会整个失效：我写的"删掉 417 行与删掉 12 行效果相同，说明被删的是冗余副本"，在去重只删 30 行之后不成立了。需要换成队友那个口径（有限编辑预算下的方向性证据）。§7.1 总表、§7.3、§7.4、§7.6 delta 表都要重算。
report.pdf — 重新生成。成本取决于 generate_report.py 是从 intervention_metrics.csv 读数还是硬编码了数字，前者就是重跑一条命令，后者要改脚本。这个我也没查。
判断
合并的代价不大，主要工作量集中在 draft 的 §7，其余基本是重跑脚本。

不过有件事要说清楚："不合并"现在已经不是免费选项了——我上一轮已经 merge 并 push 到 origin/main（845922c..3ab0a6e）。现在要退回去，得 revert 那两个提交再推一次，而队友可能已经基于它继续工作了。相比之下，改 §7 明显更省事。

我的建议是保留合并，去问队友 cap 的依据。如果依据是 audit_protocol.json 里的 max_impact_examples: 30，那值得掰扯一下——那个字段按字面读是限制展示样例数，不是限制干预能删多少训练行；把去重上限设成 30 而语料有 417 行重复，这个干预基本测不出东西。但这是内容层面的分歧，跟要不要合并是两回事。

请你告诉我，我差可以整个提交，还差哪些步骤
Bash Check handout deliverable tree
IN
cd /d/_NewFactory/pyai/project && for f in audit/profile.md audit/duplicates.md audit/leakage.md audit/label_noise.md audit/shortcut_features.md audit/ambiguity.md scripts results suspicious_examples.csv adjudication_memo.csv impact_analysis.md logs/chat.md report.pdf README.md requirements.txt; do [ -e "$f" ] && echo "OK   $f" || echo "MISS $f"; done

OUT
OK   audit/profile.md
OK   audit/duplicates.md
OK   audit/leakage.md
OK   audit/label_noise.md
OK   audit/shortcut_features.md
OK   audit/ambiguity.md
OK   scripts
OK   results
OK   suspicious_examples.csv
OK   adjudication_memo.csv
OK   impact_analysis.md
OK   logs/chat.md
OK   report.pdf
OK   README.md
OK   requirements.txt
Bash Validate submission against protocol
IN
/d/Anaconda/envs/ai2/python.exe -c "
import pandas as pd,json
p=json.load(open('starter/configs/audit_protocol.json'))
d=pd.read_csv('suspicious_examples.csv',keep_default_na=False)
m=pd.read_csv('adjudication_memo.csv',keep_default_na=False)
print('suspicious rows:',len(d),'(min',p['strict_submission_min_rows'],')')
print('issue types:',len(d.issue_type.unique()),'(min',p['strict_submission_min_issue_types'],')',d.issue_type.value_counts().to_dict())
hf=(d.confidence=='high').mean()
print('high frac: %.3f'%hf,'(max',p['strict_high_confidence_max_fraction'],')')
print('schema ok:',list(d.columns)==p['suspicious_examples_schema'])
print('memo rows:',len(m),'decisions:',m.decision.value_counts().to_dict() if 'decision' in m else list(m.columns))
"

OUT
suspicious rows: 36 (min 35 )
issue types: 6 (min 6 ) {'exact_duplicate': 6, 'near_duplicate': 6, 'leakage': 6, 'label_error': 6, 'shortcut': 6, 'ambiguous': 6}
high frac: 0.528 (max 0.55 )
schema ok: True
memo rows: 36 decisions: ['claim_id', 'id', 'split', 'issue_type', 'public_label', 'automated_evidence', 'policy_review', 'final_decision', 'final_confidence', 'recommended_action', 'final_reason', 'review_status']
Bash Check chat log, README, requirements
IN
echo "=== logs/chat.md ===" && cat logs/chat.md | head -30 && echo && echo "=== README 前 30 行 ===" && head -30 README.md && echo && echo "=== requirements.txt ===" && cat requirements.txt

OUT
=== logs/chat.md ===

# AI Usage Log

## Scope

OpenAI Codex was used as an implementation and review assistant for this project. It helped interpret the supplied handout, inspect the repository, write and revise reproducible scripts, integrate team outputs, prepare presentation material, and generate the final report.

## Evidence controls

- Dataset counts, split membership, labels, and hashes were taken from tracked result files produced by the repository scripts.
- Numerical claims in the report and presentation were read from CSV or JSON artifacts rather than invented from prose.
- Duplicate and leakage claims were tied to stable row IDs, pair keys, cluster IDs, and the completed manual review ledger.
- Training-label proposals were stored in an overlay. Held-out labels were never modified.
- The final ranked table was checked for the required schema, at least 35 rows, all six issue types, and a high-confidence fraction no greater than 55%.
- The English presentation and final PDF were rendered page by page and visually inspected for clipping, overflow, and unreadable charts.

## Human judgement and limitations

AI-assisted policy review was used to organize evidence and draft explanations. It is not presented as independent double annotation, and no inter-annotator agreement statistic is claimed. Subjective label-error and ambiguity findings should receive final team sign-off before submission.

## Main AI-assisted artifacts

- `scripts/build_final_submission.py`
- `scripts/generate_report.py`
- `suspicious_examples.csv`
- `adjudication_memo.csv`
- `presentation/cadivy_shortcut_interventions_en.pptx`
- `report.pdf`

=== README 前 30 行 ===

# Topic B — 数据集取证与标签审计 · 团队 README

> 这份文档是**队员上手指南**。提交前需要按 handout 第 VIII 节补上 `exact commands` 和
> `software versions`（本文第 1、2 节的内容可以直接复用）。

---

## 0. 现在 repo 里有什么

```
project/
├── scripts/              ← 公共底座（已就位，见第 2 节）
│   ├── common.py             共享工具库【冻结】
│   ├── download_data.py      下载 UCI 原始语料
│   ├── build_dataset.py      对齐 manifest → 标准工作表
│   └── train_baseline.py     训练基准/信号模型
├── starter/              ← 老师给的起始包（只读，别改）
│   ├── data/split_manifest.csv       固定的 train/heldout 划分
│   ├── configs/audit_protocol.json   六类问题定义 + 阈值
│   └── examples/                     提交格式样例
├── CODEX/                ← 上一版完整实现（参考用，勿直接抄）
├── requirements.txt
└── topic-b-handout-zh.md ← 需求文档，先读这个
```

**还没有的**（这是我们要做的）：`audit/`、`results/`、`suspicious_examples.csv`、
`adjudication_memo.csv`、`impact_analysis.md`、`report.pdf`。

---

=== requirements.txt ===
pandas==3.0.2
numpy==2.4.4
scipy==1.17.1
scikit-learn==1.8.0
matplotlib==3.10.8
reportlab==5.0.0
pdfplumber==0.11.10
pypdf==6.14.2
查完了。交付清单 15 项全部存在，协议硬校验也全过：

36 行 (≥35) ✓    六类全覆盖 ✓    high 占比 52.8% (≤55%) ✓    schema 匹配 ✓
剩下的都不是"没做"，是"没收尾"。按优先级：

硬缺口（handout 明文要求，现在不满足）

1. README.md — handout 第 VIII 节："must contain exact commands and software versions needed to regenerate the main artifacts"。现在这份是队员上手指南，它自己开头就写着"提交前需要补上 exact commands 和 software versions"，而 §0 还在说"还没有的：audit/、results/、suspicious_examples.csv…"——这些现在全都有了。里面确实有命令和版本，但组织方式是入门教程不是复现规格，而且漏了后来加的脚本（audit_*、build_final_submission.py、generate_report.py、run_impact_interventions.py）。
2. requirements.txt 与实际环境对不上：

包	pin	实际跑的
pandas	3.0.2	2.2.3
numpy	2.4.4	2.2.6
scipy	1.17.1	1.16.0
scikit-learn 和 matplotlib 是对的（数值结果由 sklearn 决定，所以结果本身没问题）。但交上去的 pin 文件描述的不是产出这些结果的环境，这是复现性硬伤。



1. 修复一下 A 的代码，并重新生成，比如簇方式，使得 high rate 没有这么高（你应当参考 project handout 的本意来处理）
2. 看一下 A 为什么会做 shortcut。如果有对应代码，找出来。如果没有则说明
3. 整理一下报告和代码的目录，以及对应的代码生成路径。（但要避免他们相互覆盖）
   Show less
   三件事一起推进。先搞清楚两个关键问题:suspicious_examples_dup_leak.csv 是哪个脚本生成的、A 的 shortcut 从哪来。

Bash Find which script generates dup_leak suspicious rows and shortcut
IN
cd /d/_NewFactory/pyai/project && echo "=== 谁生成 dup_leak / suspicious 行 ===" && grep -rn "suspicious_examples_dup_leak\|suspicious_examples.csv\|shortcut_score\|issue_type" scripts/audit_duplicates.py scripts/audit_leakage.py scripts/profile_data.py 2>/dev/null | grep -iE "suspicious|shortcut_score|to_csv" | head -20 && echo && echo "=== 全仓库谁写 shortcut 到 suspicious ===" && grep -rln "shortcut_score\|suspicious_examples_dup_leak" scripts/

OUT
=== 谁生成 dup_leak / suspicious 行 ===

=== 全仓库谁写 shortcut 到 suspicious ===
脚本里都没有。查一下这些文件是怎么来的——可能是手工生成或在别的地方。

Bash Trace origin of dup_leak file across repo and history
IN
echo "=== 全仓库(含所有py)谁提到 dup_leak 或写 suspicious ===" && grep -rln "suspicious_examples" --include=*.py . | grep -v CODEX && echo "---" && grep -rln "shortcut_score" --include=*.py . | grep -v CODEX && echo && echo "=== dup_leak 是哪个 commit 加的 ===" && git log --oneline --all -- suspicious_examples_dup_leak.csv && echo && echo "=== 那个 commit 同时加了哪些文件 ===" && git show --stat e258dc8 | grep -E "\.py|\.csv" | head

OUT
Exit code 1
=== 全仓库(含所有py)谁提到 dup_leak 或写 suspicious ===
./pyai/project/scripts/audit_shortcuts.py
./pyai/project/scripts/build_label_noise_outputs.py
---------------------------------------------------

Bash Check history of dup_leak and shortcut script content
IN
echo "=== dup_leak 的提交历史 ===" && git log --oneline --all --follow -- suspicious_examples_dup_leak.csv 2>/dev/null && echo && echo "=== e258dc8 加了哪些文件（A 的提交）===" && git show --stat --oneline e258dc8 | head -20 && echo && echo "=== audit_shortcuts.py 里 suspicious 相关行 ===" && grep -n "suspicious\|shortcut_score\|dup_leak" scripts/audit_shortcuts.py | head

OUT
Exit code 128
=== dup_leak 的提交历史 ===
Bash Trace dup_leak history and shortcut script
IN
git log --oneline --all -- suspicious_examples_dup_leak.csv; echo "==="; git show --stat e258dc8 2>/dev/null | grep -iE "suspicious|\.py" ; echo "=== shortcut 脚本内容 ==="; grep -n "suspicious\|shortcut_score\|keep_but_flag\|dup_leak" scripts/audit_shortcuts.py | head

OUT
fatal: not a git repository (or any of the parent directories): .git
====================================================================

=== shortcut 脚本内容 ===
grep: scripts/audit_shortcuts.py: No such file or directory
Bash Re-cd and trace dup_leak origin
IN
cd /d/_NewFactory/pyai/project && git log --oneline --all -- suspicious_examples_dup_leak.csv && echo "=== e258dc8 内容 ===" && git show --stat e258dc8 | grep -iE "suspicious|\.py" && echo "=== shortcut 脚本 suspicious 相关 ===" && grep -n "suspicious\|shortcut_score\|keep_but_flag" scripts/audit_shortcuts.py | head

OUT
e258dc8 Add suspicious duplicate leakage examples
=== e258dc8 内容 ===
    Add suspicious duplicate leakage examples
 suspicious_examples_dup_leak.csv | 1501 ++++++++++++++++++++++++++++++++++++++
=== shortcut 脚本 suspicious 相关 ===
438:    schema = load_protocol()["suspicious_examples_schema"]
Bash Confirm no shortcut code and inspect rebuildable data
IN
echo "=== 全仓库(非CODEX)有无生成 shortcut_score 的代码 ===" && grep -rln "shortcut_score" . --include=*.py | grep -v CODEX || echo "→ 无任何代码生成 shortcut_score(确认:A 的 shortcut 无对应代码)" && echo && echo "=== A 的可复现产出(committed CSV)可用于重建 suspicious ===" && ls results/duplicate/ results/leakage/ && echo && echo "=== exact 簇结构 ===" && head -3 results/duplicate/exact_duplicate_clusters.csv && echo "..." && head -3 results/duplicate/exact_duplicate_members.csv

OUT
=== 全仓库(非CODEX)有无生成 shortcut_score 的代码 ===
→ 无任何代码生成 shortcut_score(确认:A 的 shortcut 无对应代码)

=== A 的可复现产出(committed CSV)可用于重建 suspicious ===
results/duplicate/:
duplicate_summary.json
exact_duplicate_clusters.csv
exact_duplicate_members.csv
near_duplicate_candidates.csv
near_duplicate_manual_review_decisions.csv
near_duplicate_review_queue.csv
near_duplicate_review_summary.csv
near_duplicate_review_summary.json
near_duplicate_threshold_sensitivity.csv
reviewed_duplicate_samples.csv

results/leakage/:
leakage_cases.csv
leakage_heldout_rows.csv
leakage_metrics.csv
leakage_representative_examples.csv
leakage_summary.json

=== exact 簇结构 ===
cluster_id,cluster_size,splits,labels,label_conflict,cross_split,train_count,heldout_count,representative_id,representative_text,member_ids,source_script,method_version
E0001,2,train,spam,False,False,2,0,T0003,Free entry in 2 a wkly comp to win FA Cup final tkts 21st May 2005. Text FA to 87121 to receive entry question(std txt rate)T&C's apply 08452810075over18's,T0003|T0942,scripts/audit_duplicates.py,duplicate-audit-v1.0
E0002,3,train,ham,False,False,3,0,T0008,As per your request 'Melle Melle (Oru Minnaminunginte Nurungu Vettam)' has been set as your callertune for all Callers. Press *9 to copy your friends Callertune,T0008|T0089|T0131,scripts/audit_duplicates.py,duplicate-audit-v1.0
...
cluster_id,member_order,id,split,uci_row_number,label,text,normalized_text,source_script,method_version
E0001,1,T0003,train,3,spam,Free entry in 2 a wkly comp to win FA Cup final tkts 21st May 2005. Text FA to 87121 to receive entry question(std txt rate)T&C's apply 08452810075over18's,free entry in 2 a wkly comp to win fa cup final tkts 21st may 2005. text fa to 87121 to receive entry question(std txt rate)t&c's apply 08452810075over18's,scripts/audit_duplicates.py,duplicate-audit-v1.0
E0001,2,T0942,train,1164,spam,Free entry in 2 a wkly comp to win FA Cup final tkts 21st May 2005. Text FA to 87121 to receive entry question(std txt rate)T&C's apply 08452810075over18's,free entry in 2 a wkly comp to win fa cup final tkts 21st may 2005. text fa to 87121 to receive entry question(std txt rate)t&c's apply 08452810075over18's,scripts/audit_duplicates.py,duplicate-audit-v1.0
Task 2 有结论了。 先回答这个,再动手修。

Task 2:A 的 shortcut 从哪来?—— 无对应代码
提交 e258dc8 只加了 suspicious_examples_dup_leak.csv 一个文件,没有任何脚本。
全仓库(排除 CODEX)搜 shortcut_score,零命中——生成那 454 条 shortcut 的 evidence 字符串的代码根本没提交。
C 的 audit_shortcuts.py:438 才是正牌 shortcut 生成器。
结论:A 的 1500 行是用一个没提交的脚本(或手工)生成的,本身就不可复现。 那 454 条 shortcut 是 A 自己另算了一套「表面特征打分」,越界进了 C 的领域。处理方式明确:A 的 suspicious 行应从可复现的 results/duplicate/、results/leakage/ CSV 重新生成,shortcut 整类删除,归还 C。

先看两个文件的结构,决定怎么重建 + 怎么把 P0 的不可复现根因一起修掉。

Bash Inspect ledger, queue, leakage structure and cluster stats
IN
echo "=== 人工账本列(能否改挂 id 对以摆脱 N 编号)===" && head -1 results/duplicate/near_duplicate_manual_review_decisions.csv && echo && echo "=== review_queue 列 ===" && head -1 results/duplicate/near_duplicate_review_queue.csv && echo && echo "=== leakage_cases 列+样例 ===" && head -2 results/leakage/leakage_cases.csv && echo && echo "=== 各簇统计:跨split/标签冲突有多少 ===" && D:/Anaconda/envs/ai2/python.exe -c "
import pandas as pd
c=pd.read_csv('results/duplicate/exact_duplicate_clusters.csv',keep_default_na=False)
print('exact 簇总数:',len(c),'| 成员总数:',c.cluster_size.sum())
print('  跨split簇:',c.cross_split.sum(),'| 标签冲突簇:',c.label_conflict.sum())
q=pd.read_csv('results/duplicate/near_duplicate_review_queue.csv',keep_default_na=False)
print('near review_queue:',len(q),'| 列:',list(q.columns)[:8])
if 'review_decision' in q: print('  decision分布:',q.review_decision.value_counts().to_dict())
"

OUT
=== 人工账本列(能否改挂 id 对以摆脱 N 编号)===
pair_id,review_decision,review_category,reviewer,review_notes,recommended_action,confidence

=== review_queue 列 ===
pair_id,reason_code,id_a,id_b,split_a,split_b,label_a,label_b,uci_row_number_a,uci_row_number_b,word_cosine,char_cosine,max_cosine,primary_matcher,cross_split,label_conflict,above_protocol_threshold,text_a,text_b,source_script,method_version,review_decision,review_category,reviewer,review_notes,recommended_action,confidence,review_version

=== leakage_cases 列+样例 ===
case_id,match_type,heldout_id,train_id,heldout_label,train_label,label_conflict,heldout_uci_row_number,train_uci_row_number,cluster_id,pair_id,word_cosine,char_cosine,max_cosine,review_decision,review_category,confidence,heldout_text,train_text,source_script,method_version
L_EXACT_E0009_H0009_T3705,exact,H0009,T3705,ham,ham,False,58,4621,E0009,,1.0,1.0,1.0,not_applicable_exact_duplicate,exact_duplicate,high,"Sorry, I'll call later in meeting.","Sorry, I'll call later In meeting.",scripts/audit_leakage.py,leakage-audit-v1.1

=== 各簇统计:跨split/标签冲突有多少 ===
exact ������: 290 | ��Ա����: 705
  ��split��: 5 | ��ǩ��ͻ��: 0
near review_queue: 346 | ��: ['pair_id', 'reason_code', 'id_a', 'id_b', 'split_a', 'split_b', 'label_a', 'label_b']
  decision�ֲ�: {'accepted': 200, 'rejected_false_positive': 146}
全部摸清了,关键突破口:near_duplicate_review_queue.csv 里同时有 pair_id 和 id_a/id_b,所以能把 A 的 200 接受/146 拒绝决定改挂到稳定的 id 对上,彻底摆脱会漂移的 N 编号,同时一字不差保留 A 的人工判断。

而且簇统计揭示了 high 爆表的荒谬:290 个精确重复簇里只有 5 个跨 split、0 个标签冲突,A 却把 705 个成员全标 high。

读关键代码段,做外科手术式修改。

Bash Read pair-building and review main logic
IN
echo "=== audit_duplicates.py: pair 构建+编号 (185-230) ===" && sed -n '185,230p' scripts/audit_duplicates.py && echo "=== review_near_duplicates.py: main 流程 (100-160) ===" && sed -n '100,165p' scripts/review_near_duplicates.py

OUT
=== audit_duplicates.py: pair 构建+编号 (185-230) ===
        if score.max_cosine < SEARCH_FLOOR:
            continue
        left = df.iloc[score.left_idx]
        right = df.iloc[score.right_idx]
        exact_duplicate = normalized.iloc[score.left_idx] == normalized.iloc[score.right_idx]
        if exact_duplicate:
            continue
        cross_split = left["split"] != right["split"]
        label_conflict = left["label"] != right["label"]
        max_cos = score.max_cosine
        rows.append(
            {
                "pair_id": f"N{len(rows) + 1:04d}",
                "id_a": left["id"],
                "id_b": right["id"],
                "split_a": left["split"],
                "split_b": right["split"],
                "label_a": left["label"],
                "label_b": right["label"],
                "uci_row_number_a": int(left["uci_row_number"]),
                "uci_row_number_b": int(right["uci_row_number"]),
                "word_cosine": score.word_cosine,
                "char_cosine": score.char_cosine,
                "max_cosine": max_cos,
                "primary_matcher": "word" if score.word_cosine >= score.char_cosine else "char",
                "cross_split": bool(cross_split),
                "label_conflict": bool(label_conflict),
                "above_protocol_threshold": bool(max_cos >= threshold),
                "reason_code_suggestion": likely_reason_code(
                    left, right, score.word_cosine, score.char_cosine
                ),
                "text_a": left["text"],
                "text_b": right["text"],
                "source_script": "scripts/audit_duplicates.py",
                "method_version": METHOD_VERSION,
            }
        )
    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values(
            ["above_protocol_threshold", "cross_split", "max_cosine", "pair_id"],
            ascending=[False, False, False, True],
        ).reset_index(drop=True)
    return result

=== review_near_duplicates.py: main 流程 (100-160) ===
            "confidence": confidence,
        }
    if pair_id in SEMANTIC_CHANGE_REJECT_PAIR_IDS:
        return {
            "review_decision": "rejected_false_positive",
            "review_category": "semantic_change",
            "reviewer": REVIEWER,
            "review_notes": "Texts are lexically similar but the manual review found a material meaning change, so this is not duplicate evidence.",
            "recommended_action": "exclude_from_duplicate_evidence",
            "confidence": "high",
        }
    return {
        "review_decision": "rejected_false_positive",
        "review_category": "generic_short_text",
        "reviewer": REVIEWER,
        "review_notes": "Manual review found only a generic short conversational phrase or acknowledgement. Exact duplicates of such phrases remain objective string duplicates, but non-exact variants need a specific source/template/content anchor to count as near-duplicate evidence.",
        "recommended_action": "exclude_from_duplicate_evidence",
        "confidence": "high",
    }

def generate_manual_decisions(queue: pd.DataFrame) -> pd.DataFrame:
    missing_accepted = sorted(ACCEPTED_HAM_PAIR_IDS - set(queue["pair_id"]))
    missing_semantic = sorted(SEMANTIC_CHANGE_REJECT_PAIR_IDS - set(queue["pair_id"]))
    if missing_accepted or missing_semantic:
        raise ValueError(
            f"Decision set refers to missing pair IDs: accepted={missing_accepted}, semantic={missing_semantic}"
        )
    rows = [{"pair_id": row["pair_id"], **manual_decision(row)} for _, row in queue.iterrows()]
    decisions = pd.DataFrame(rows)
    duplicated = decisions[decisions["pair_id"].duplicated()]["pair_id"].tolist()
    if duplicated:
        raise ValueError(f"Manual review ledger has duplicate pair_id values: {duplicated[:10]}")
    if len(decisions) != len(queue):
        raise ValueError(f"Expected {len(queue)} decisions, wrote {len(decisions)}")
    decisions.to_csv(DECISIONS_PATH, index=False)
    return decisions[["pair_id", *REVIEW_COLUMNS]].copy()

def adjudicate(queue: pd.DataFrame, decisions: pd.DataFrame) -> pd.DataFrame:
    stale_review_columns = [column for column in REVIEW_COLUMNS if column in queue.columns]
    base = queue.drop(columns=stale_review_columns)
    reviewed = base.merge(decisions, on="pair_id", how="left", validate="one_to_one")

    missing = reviewed[reviewed["review_decision"].eq("") | reviewed["review_decision"].isna()]
    if len(missing):
        ids = missing["pair_id"].head(20).tolist()
        raise ValueError(f"Missing manual review decisions for queued pairs: {ids}")

    reviewed["reviewer"] = reviewed["reviewer"].replace("", REVIEWER)
    reviewed["review_version"] = REVIEW_VERSION
    return reviewed

def heldout_ids(frame: pd.DataFrame) -> list[str]:
    if frame.empty:
        return []
    values = pd.concat(
        [
            frame.loc[frame["split_a"] == "heldout", "id_a"],
            frame.loc[frame["split_b"] == "heldout", "id_b"],
        ],
        ignore_index=True,
    )
    return sorted(value for value in pd.unique(values) if value)
方案定了,三处修改。核心思路:A 的错误在于把"人工判断"(数据)硬编码成 N 编号(代码)。正确做法是把判断固化成按稳定 id 对索引的数据文件——正如我 B 部分用的 manual_review.json。

先修确定性根因。

Edit D:\_NewFactory\pyai\project\scripts\audit_duplicates.py
Removed 1 line
Edit D:\_NewFactory\pyai\project\scripts\audit_duplicates.py
Added 5 lines
Now freeze A's 200 accept/146 reject decisions to an id-pair-keyed ledger, then rewrite the review script to read it.

Bash Freeze A's manual decisions to id-pair ledger
IN
D:/Anaconda/envs/ai2/python.exe -c "
import pandas as pd
q=pd.read_csv('results/duplicate/near_duplicate_review_queue.csv',keep_default_na=False)

# 以稳定 id 对为键固化 A 的人工判断

led=q[['id_a','id_b','review_decision','review_category','recommended_action','confidence','review_notes']].copy()
led['pair_key']=led.apply(lambda r: '|'.join(sorted([r.id_a,r.id_b])),axis=1)
led=led[['pair_key','id_a','id_b','review_decision','review_category','recommended_action','confidence','review_notes']]
assert led.pair_key.is_unique, '账本 id 对不唯一'
led.to_csv('configs/near_duplicate_review_ledger.csv',index=False)
print('固化账本:',len(led),'条  decision分布:',led.review_decision.value_counts().to_dict())
print('cross-split accepted 中有多少(将影响high):', )
"

OUT
�̻��˱�: 346 ��  decision�ֲ�: {'accepted': 200, 'rejected_false_positive': 146}
cross-split accepted ���ж���(��Ӱ��high):
账本已固化(346 条,完整保留 A 的判断)。现在改写 review 脚本读这个账本。先看文件头部结构。

Bash Read header and main of review script
IN
sed -n '1,55p' scripts/review_near_duplicates.py && echo "=== main ===" && sed -n '165,260p' scripts/review_near_duplicates.py

OUT
"""Reproduce the manual near-duplicate adjudication pass.

The candidate queue is created by scripts/audit_duplicates.py. This script stores
the fixed manual re-review as pair_id decision sets, writes the reproducible
manual ledger, merges it into the queue, and emits pair-level and sample-level
duplicate evidence. It does not infer review decisions from text heuristics.
"""

from __future__ import annotations

from collections import Counter
import json

import pandas as pd

from common import RESULTS_DIR, ROOT, ensure_dirs, load_canonical, write_json

REVIEWER = "Codex-assisted manual review"
REVIEW_VERSION = "near-duplicate-review-v1.3-manual-ledger"
REVIEW_POLICY_VERSION = "near-duplicate-review-policy-v1.0"
DUPLICATE_RESULTS_DIR = RESULTS_DIR / "duplicate"
QUEUE_PATH = DUPLICATE_RESULTS_DIR / "near_duplicate_review_queue.csv"
DECISIONS_PATH = DUPLICATE_RESULTS_DIR / "near_duplicate_manual_review_decisions.csv"
REVIEWED_QUEUE_PATH = DUPLICATE_RESULTS_DIR / "near_duplicate_review_queue_reviewed.csv"
SUMMARY_CSV_PATH = DUPLICATE_RESULTS_DIR / "near_duplicate_review_summary.csv"
SUMMARY_JSON_PATH = DUPLICATE_RESULTS_DIR / "near_duplicate_review_summary.json"
SAMPLE_SUMMARY_PATH = DUPLICATE_RESULTS_DIR / "reviewed_duplicate_samples.csv"
DUPLICATE_SUMMARY_PATH = DUPLICATE_RESULTS_DIR / "duplicate_summary.json"
REPORT_PATH = ROOT / "duplicates.md"

REVIEW_COLUMNS = [
    "review_decision",
    "review_category",
    "reviewer",
    "review_notes",
    "recommended_action",
    "confidence",
]

ACCEPTED_HAM_PAIR_IDS = {
    "N0102", "N0001", "N0003", "N0017", "N0153", "N0094", "N0327", "N0016", "N0093",
    "N0380", "N0124", "N0377", "N0023", "N0091", "N0092", "N0007", "N0292", "N0426",
    "N0223", "N0025", "N0291", "N0366", "N0387", "N0341", "N0345", "N0346", "N0209",
    "N0210", "N0283", "N0344", "N0035", "N0036", "N0037", "N0142", "N0143", "N0266",
    "N0273", "N0128", "N0123", "N0149", "N0231", "N0373", "N0024", "N0081",
}
SEMANTIC_CHANGE_REJECT_PAIR_IDS = {"N0313", "N0274", "N0138"}
FORWARDED_OR_TEMPLATE_HAM_PAIR_IDS = {
    "N0341", "N0345", "N0346", "N0209", "N0210", "N0283", "N0344", "N0035", "N0036",
    "N0037", "N0142", "N0143", "N0266", "N0273",
}
EMBEDDED_OR_TRANSCRIPT_HAM_PAIR_IDS = {"N0007", "N0292", "N0426", "N0223", "N0025", "N0291", "N0366", "N0387"}
MINOR_PERSONALIZATION_HAM_PAIR_IDS = ACCEPTED_HAM_PAIR_IDS - FORWARDED_OR_TEMPLATE_HAM_PAIR_IDS - EMBEDDED_OR_TRANSCRIPT_HAM_PAIR_IDS

=== main ===

def summarize(reviewed: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    decision_counts = Counter(reviewed["review_decision"])
    category_counts = Counter(reviewed["review_category"])
    split_pair_counts = Counter(reviewed["split_a"] + "-" + reviewed["split_b"])
    accepted = reviewed[reviewed["review_decision"] == "accepted"]
    rejected = reviewed[reviewed["review_decision"] == "rejected_false_positive"]
    accepted_cross = accepted[accepted["cross_split"].astype(bool)]
    rejected_cross = rejected[rejected["cross_split"].astype(bool)]
    accepted_train_train = accepted[
        (accepted["split_a"] == "train") & (accepted["split_b"] == "train")
    ]

    summary_rows = []
    for decision, count in sorted(decision_counts.items()):
        subset = reviewed[reviewed["review_decision"] == decision]
        summary_rows.append(
            {
                "review_decision": decision,
                "pairs": int(count),
                "cross_split_pairs": int(subset["cross_split"].astype(bool).sum()),
                "train_train_pairs": int(((subset["split_a"] == "train") & (subset["split_b"] == "train")).sum()),
                "unique_heldout_ids": int(len(heldout_ids(subset))),
                "spam_pairs": int(((subset["label_a"] == "spam") & (subset["label_b"] == "spam")).sum()),
                "ham_pairs": int(((subset["label_a"] == "ham") & (subset["label_b"] == "ham")).sum()),
            }
        )

    payload = {
        "source_script": "scripts/review_near_duplicates.py",
        "review_version": REVIEW_VERSION,
        "review_policy_version": REVIEW_POLICY_VERSION,
        "review_policy_summary": [
            "Exact duplicates are retained whenever the normalized strings are identical, even if the text is a common short reply.",
            "Near duplicates are accepted only when manual review finds evidence of the same message, template, spam campaign, forwarded content, embedded content, or specific personalized variant.",
            "Near-duplicate candidates that only share generic short conversational wording are rejected unless they contain a specific content anchor beyond the common phrase.",
            "Lexically similar pairs with material semantic changes are rejected as false positives.",
        ],
        "input": str(QUEUE_PATH.relative_to(ROOT)),
        "manual_review_ledger": str(DECISIONS_PATH.relative_to(ROOT)),
        "reviewed_queue": str(QUEUE_PATH.relative_to(ROOT)),
        "reviewed_rows": int(len(reviewed)),
        "accepted_pairs": int(decision_counts.get("accepted", 0)),
        "rejected_false_positive_pairs": int(decision_counts.get("rejected_false_positive", 0)),
        "remaining_needs_review_pairs": int(decision_counts.get("needs_review", 0)),
        "accepted_cross_split_pairs": int(len(accepted_cross)),
        "rejected_cross_split_false_positive_pairs": int(len(rejected_cross)),
        "accepted_train_train_pairs": int(len(accepted_train_train)),
        "accepted_unique_heldout_ids": int(len(heldout_ids(accepted_cross))),
        "decision_counts": dict(decision_counts),
        "category_counts": dict(category_counts),
        "split_pair_counts": dict(split_pair_counts),
    }
    return pd.DataFrame(summary_rows), payload

def add_partner(entry: dict[str, object], partner_id: str, cross_split: bool) -> None:
    entry["partner_ids"].add(partner_id)
    if cross_split:
        entry["cross_split_partner_ids"].add(partner_id)

def sample_entry(row: pd.Series) -> dict[str, object]:
    return {
        "sample_id": row["id"],
        "split": row["split"],
        "label": row["label"],
        "uci_row_number": int(row["uci_row_number"]),
        "text": row["text"],
        "exact_cluster_ids": set(),
        "near_pair_ids": set(),
        "review_categories": set(),
        "partner_ids": set(),
        "cross_split_partner_ids": set(),
        "exact_partner_ids": set(),
        "near_partner_ids": set(),
        "cross_split_exact_partner_ids": set(),
        "cross_split_near_pair_ids": set(),
        "max_near_similarity": None,
    }

def build_reviewed_duplicate_samples(reviewed: pd.DataFrame) -> pd.DataFrame:
    canonical = load_canonical().set_index("id", drop=False)
    entries: dict[str, dict[str, object]] = {}

    exact_members_path = DUPLICATE_RESULTS_DIR / "exact_duplicate_members.csv"
    exact_clusters_path = DUPLICATE_RESULTS_DIR / "exact_duplicate_clusters.csv"
    if exact_members_path.exists() and exact_clusters_path.exists():
        members = pd.read_csv(exact_members_path, keep_default_na=False)
        clusters = pd.read_csv(exact_clusters_path, keep_default_na=False)
        cross_by_cluster = dict(zip(clusters["cluster_id"], clusters["cross_split"].astype(bool)))
        for cluster_id, group in members.groupby("cluster_id", sort=False):
            cross_split = bool(cross_by_cluster.get(cluster_id, False))
            ids = group["id"].tolist()
Bash Read remaining decision functions
IN
sed -n '56,99p' scripts/review_near_duplicates.py

OUT
def accepted_ham_category(pair_id: str) -> tuple[str, str, str]:
    if pair_id in FORWARDED_OR_TEMPLATE_HAM_PAIR_IDS:
        return (
            "same_forwarded_or_template_ham",
            "Same substantive forwarded/template-style ham message with only punctuation, spacing, or minor wording changes.",
            "medium",
        )
    if pair_id in EMBEDDED_OR_TRANSCRIPT_HAM_PAIR_IDS:
        return (
            "embedded_or_transcript_variant",
            "One message substantially embeds the other or repeats the same specific conversation content with surrounding context.",
            "medium",
        )
    if pair_id in MINOR_PERSONALIZATION_HAM_PAIR_IDS:
        return (
            "minor_personalization_change",
            "Same specific ham message with only a name, addressee, punctuation, casing, or small wording detail changed.",
            "medium",
        )
    raise ValueError(f"Accepted ham pair {pair_id} has no category")

def manual_decision(row: pd.Series) -> dict[str, str]:
    pair_id = row["pair_id"]
    label_pair = (row["label_a"], row["label_b"])
    if label_pair == ("spam", "spam"):
        return {
            "review_decision": "accepted",
            "review_category": "same_spam_campaign_template",
            "reviewer": REVIEWER,
            "review_notes": "Same spam campaign/template with changed phone numbers, URLs, reference IDs, amounts, dates, names, formatting, casing, or minor wording.",
            "recommended_action": "treat_as_near_duplicate_leakage_candidate",
            "confidence": "high",
        }
    if label_pair != ("ham", "ham"):
        raise ValueError(f"Unexpected label pair for {pair_id}: {label_pair}")
    if pair_id in ACCEPTED_HAM_PAIR_IDS:
        category, notes, confidence = accepted_ham_category(pair_id)
        return {
            "review_decision": "accepted",
            "review_category": category,
            "reviewer": REVIEWER,
            "review_notes": notes,
            "recommended_action": "treat_as_near_duplicate_leakage_candidate",
Now replace the whole hardcoded-N-ID block with id-pair ledger loading. Replacing from ACCEPTED_HAM_PAIR_IDS = { through the end of generate_manual_decisions.

Read D:\_NewFactory\pyai\project\scripts\review_near_duplicates.py (lines 100-139)
Edit D:\_NewFactory\pyai\project\scripts\review_near_duplicates.py
Removed 6 lines
Edit D:\_NewFactory\pyai\project\scripts\review_near_duplicates.py
Removed 46 lines
Now test the full reproducibility chain end-to-end, twice, to prove it's stable.

Bash Run full pipeline first pass and check leakage recovery
IN
echo "=== 第1次完整跑 ===" && D:/Anaconda/envs/ai2/python.exe scripts/audit_duplicates.py 2>&1 | tail -3 && D:/Anaconda/envs/ai2/python.exe scripts/review_near_duplicates.py 2>&1 | tail -3 && D:/Anaconda/envs/ai2/python.exe scripts/audit_leakage.py 2>&1 | tail -3 && echo && echo "=== leakage 恢复到 63 了吗 ===" && D:/Anaconda/envs/ai2/python.exe -c "import json;d=json.load(open('results/leakage/leakage_summary.json'));print('unique_heldout_leakage_ids:',d['all_leakage_unique_heldout_ids'],'| near_accepted:',d['near_reviewed_accepted_cross_split_cases'])"

OUT
=== 第1次完整跑 ===
Near review rows excluding heldout-heldout: 346
Cross-split near candidates: 90
Wrote D:\_NewFactory\pyai\project\duplicates.md
  File "D:\_NewFactory\pyai\project\scripts\review_near_duplicates.py", line 61, in generate_manual_decisions
    raise ValueError(
ValueError: 2 queued pairs have no ledger decision (first 10: ['T1545|T3892', 'T3609|T3892']). Re-freeze configs/near_duplicate_review_ledger.csv from the review queue.
Wrote results/leakage/leakage_metrics.csv (6 rows)
Wrote results/leakage/leakage_summary.json
Wrote leakage.md

=== leakage 恢复到 63 了吗 ===
unique_heldout_leakage_ids: 5 | near_accepted: 0
冒出一个更深的问题:我的确定性重跑得到的候选对集合和 A 提交的差了 2 对(T1545|T3892、T3609|T3892)。说明不只是编号不稳,近邻检索的成员本身在并列边界处就不确定。这才是最底层的根因。看检索代码。

Bash Inspect neighbor retrieval logic
IN
grep -n "SEARCH_FLOOR\|n_neighbors\|NearestNeighbors\|kneighbors\|TOP_K\|def candidate_scores\|def.*scores\|argsort\|def pair_scores" scripts/audit_duplicates.py | head && echo "=== 检索主体 ===" && sed -n '/def.*scores/,/return/p' scripts/audit_duplicates.py | head -60

OUT
20:from sklearn.neighbors import NearestNeighbors
33:SEARCH_FLOOR = 0.88
132:    n_neighbors = min(N_NEIGHBORS + 1, matrix.shape[0])
133:    model = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine", algorithm="brute")
135:    distances, indices = model.kneighbors(matrix)
149:def compute_pair_scores(df: pd.DataFrame) -> list[PairScore]:
152:    pairs = collect_candidate_indices(word_matrix, SEARCH_FLOOR) | collect_candidate_indices(
153:        char_matrix, SEARCH_FLOOR
181:def pair_rows(df: pd.DataFrame, scores: list[PairScore], threshold: float) -> pd.DataFrame:
185:        if score.max_cosine < SEARCH_FLOOR:
=== 检索主体 ===
def compute_pair_scores(df: pd.DataFrame) -> list[PairScore]:
    word_matrix = word_vectorizer().fit_transform(df["text"])
    char_matrix = char_vectorizer().fit_transform(df["text"])
    pairs = collect_candidate_indices(word_matrix, SEARCH_FLOOR) | collect_candidate_indices(
        char_matrix, SEARCH_FLOOR
    )

    scores: list[PairScore] = []
    for left, right in sorted(pairs):
        word_score = float(cosine_similarity(word_matrix[left], word_matrix[right])[0, 0])
        char_score = float(cosine_similarity(char_matrix[left], char_matrix[right])[0, 0])
        scores.append(PairScore(left, right, word_score, char_score))
    return scores
def pair_rows(df: pd.DataFrame, scores: list[PairScore], threshold: float) -> pd.DataFrame:
    rows = []
    normalized = df["text"].map(normalize_text)
    for score in scores:
        if score.max_cosine < SEARCH_FLOOR:
            continue
        left = df.iloc[score.left_idx]
        right = df.iloc[score.right_idx]
        exact_duplicate = normalized.iloc[score.left_idx] == normalized.iloc[score.right_idx]
        if exact_duplicate:
            continue
        cross_split = left["split"] != right["split"]
        label_conflict = left["label"] != right["label"]
        max_cos = score.max_cosine
        rows.append(
            {
                "id_a": left["id"],
                "id_b": right["id"],
                "split_a": left["split"],
                "split_b": right["split"],
                "label_a": left["label"],
                "label_b": right["label"],
                "uci_row_number_a": int(left["uci_row_number"]),
                "uci_row_number_b": int(right["uci_row_number"]),
                "word_cosine": score.word_cosine,
                "char_cosine": score.char_cosine,
                "max_cosine": max_cos,
                "primary_matcher": "word" if score.word_cosine >= score.char_cosine else "char",
                "cross_split": bool(cross_split),
                "label_conflict": bool(label_conflict),
                "above_protocol_threshold": bool(max_cos >= threshold),
                "reason_code_suggestion": likely_reason_code(
                    left, right, score.word_cosine, score.char_cosine
                ),
                "text_a": left["text"],
                "text_b": right["text"],
                "source_script": "scripts/audit_duplicates.py",
                "method_version": METHOD_VERSION,
            }
        )
    result = pd.DataFrame(rows)
    if not result.empty:
        # Assign pair_id from a content-stable key so the numbering is identical
        # on every run. The manual review ledger keys off (id_a, id_b), not the
        # N-number, but a reproducible N-number keeps reports diffable.
        result = result.sort_values(["id_a", "id_b"]).reset_index(drop=True)
        result.insert(0, "pair_id", [f"N{i + 1:04d}" for i in range(len(result))])
Bash Read collect_candidate_indices
IN
sed -n '125,148p' scripts/audit_duplicates.py

OUT
        cross_split = clusters.copy()
    else:
        cross_split = clusters[clusters["cross_split"]].copy().reset_index(drop=True)
    return clusters, members, cross_split



好了，你再 merge 一下。看看这次 A 有没有做好
Bash Fetch and check divergence before merge
IN
cd /d/_NewFactory/pyai/project && echo "=== 本地状态 ===" && git status --short && echo "(空=干净)" && echo && echo "=== 我的草稿是未跟踪文件,先看在不在 ===" && ls report_zh_draft.md 2>/dev/null && echo && echo "=== fetch ===" && git fetch --all --prune 2>&1 | tail -5 && echo && git log --oneline --graph --all -8

OUT
=== 本地状态 ===
?? report_zh_draft.md
(空=干净)

=== 我的草稿是未跟踪文件,先看在不在 ===
report_zh_draft.md

=== fetch ===
From github.com:cadivy/task-b-aiaa3102
   e258dc8..2a2c8d2  main       -> origin/main

* 2a2c8d2 Remove shortcut rows from suspicious examples
  | *   8cd0660 Merge remote-tracking branch 'origin/main'
  | |\| |/|/|
* | e258dc8 Add suspicious duplicate leakage examples
* | 4d5c264 fix: add shortcut suspicious examples
* | af53118 feat: add shortcut feature audit
  | *   fed942a Merge remote-tracking branch 'origin/main'
  | |\| |/|/|
* | 12a009d Add profile duplicate and leakage audits
  | * f4369bd finish 4&6
  |/
  A push 了一个新提交 2a2c8d2 Remove shortcut rows from suspicious examples。但提交信息只提"删除 shortcut 行"——这让我担心他可能只删了 454 行,没修根因。合并前先看他到底改了什么。

Bash Check what A's new commit changed
IN
echo "=== 2a2c8d2 相对上一版改了哪些文件 ===" && git diff --stat e258dc8 2a2c8d2 && echo && echo "=== A 有没有碰那两个根因脚本? ===" && git diff --stat e258dc8 2a2c8d2 -- scripts/audit_duplicates.py scripts/review_near_duplicates.py && echo "(空=没碰,根因未修)"

OUT
=== 2a2c8d2 相对上一版改了哪些文件 ===
 scripts/build_suspicious_examples.py | 205 ++++++++++++++++
 suspicious_examples_dup_leak.csv     | 454 -----------------------------------
 2 files changed, 205 insertions(+), 454 deletions(-)

=== A 有没有碰那两个根因脚本? ===
(空=没碰,根因未修)
A 做了两件事:新增 build_suspicious_examples.py(205行,解决了"无代码来源"问题)、删掉 454 条 shortcut。但没碰那两个根因脚本——不可复现的 bug 大概率还在。合并后实测。

Bash Merge A's new commit
IN
git merge origin/main --no-edit 2>&1 | tail -6 && echo "=== 合并后 ===" && git status --short && echo "(?? 是我的草稿,正常)" && echo && git log --oneline -3

OUT
Merge made by the 'ort' strategy.
 scripts/build_suspicious_examples.py | 205 ++++++++++++++++
 suspicious_examples_dup_leak.csv     | 454 -----------------------------------
 2 files changed, 205 insertions(+), 454 deletions(-)
 create mode 100644 scripts/build_suspicious_examples.py
=== 合并后 ===
?? report_zh_draft.md
(?? 是我的草稿,正常)

30b13b6 Merge remote-tracking branch 'origin/main'
2a2c8d2 Remove shortcut rows from suspicious examples
8cd0660 Merge remote-tracking branch 'origin/main'
合并干净。现在核查 A 这次到底修没修好——先看新脚本能不能跑、是不是按簇生成,再验根因是否还在。

Bash Run A's new build script and check reproducibility
IN
echo "=== 新脚本能否复现出 dup_leak.csv? ===" && D:/Anaconda/envs/ai2/python.exe scripts/build_suspicious_examples.py 2>&1 | tail -8; echo "exit: $?" && echo && echo "=== 跑完后 dup_leak 有没有变化(=是否可复现) ===" && git status --short | grep -v "report_zh"

OUT
=== 新脚本能否复现出 dup_leak.csv? ===
wrote=D:\_NewFactory\pyai\project\suspicious_examples_dup_leak.csv
{'rows': 1046, 'issue_types': ['exact_duplicate', 'leakage', 'near_duplicate'], 'issue_counts': {'exact_duplicate': 705, 'near_duplicate': 278, 'leakage': 63}, 'confidence_counts': {'high': 940, 'medium': 106}, 'high_fraction': 0.8986615678776291}
exit: 0

=== 跑完后 dup_leak 有没有变化(=是否可复现) ===
A 的新脚本能确定性复现出 dup_leak.csv(重跑无变化),shortcut 也删干净了——"无代码来源"和 shortcut 越界这两个问题解决了。但还有严重问题。核算合并影响 + 验根因。

Bash Check combined protocol compliance and root cause
IN
echo "=== 三份合并后是否满足协议 ===" && D:/Anaconda/envs/ai2/python.exe -c "
import pandas as pd
a=pd.read_csv('suspicious_examples_dup_leak.csv',keep_default_na=False)
c=pd.read_csv('suspicious_examples.csv',keep_default_na=False)
b=pd.read_csv('results/suspicious_examples_b.csv',keep_default_na=False)
allc=pd.concat([a,c,b],ignore_index=True)
print('总行数:',len(allc))
print('A 单独: %d行, high %d (%.1f%%)'%(len(a),(a.confidence=='high').sum(),100*(a.confidence=='high').mean()))
print('issue_type:',allc.issue_type.value_counts().to_dict())
print('合并 high 占比: %.1f%%  <- 协议上限 55%%'%(100*(allc.confidence=='high').mean()))
print('exact_duplicate 是按成员(705)还是按簇(290)?',(a.issue_type=='exact_duplicate').sum(),'行')
"
echo && echo "=== 根因:重跑上游流水线还崩不崩 ===" && D:/Anaconda/envs/ai2/python.exe scripts/audit_duplicates.py >/dev/null 2>&1 && D:/Anaconda/envs/ai2/python.exe scripts/review_near_duplicates.py 2>&1 | tail -3; echo "exit: $?"

OUT
=== 三份合并后是否满足协议 ===
������: 1085
A ����: 1046��, high 940 (89.9%)
