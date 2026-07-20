> **工作记录（非提交件）。** 最终裁定以 `configs/manual_review.json` 为准——三处修正
> （T2755→medium、T2229/T2273→keep_but_flag、should_fix 置信度按规则重排）已合并进该文件。
> 本文保留推理过程，下方表格中被修正的条目以文末「修正」各表为准。

### A 部分剩余 31 条

| ID    | decision              | confidence | 理由                                             |
| ----- | --------------------- | ---------- | ------------------------------------------------ |
| H0330 | keep_but_flag         | medium     | wap密码通知，绑定订阅服务(mobsi.com)，仍是spam   |
| T3272 | should_fix            | high       | 个人回复讨债公司的吐槽，无招揽                   |
| T3390 | keep_but_flag         | low        | "missed call alert"是经典070X溢价号回拨骗局      |
| T1798 | should_fix            | medium     | 内容是提醒朋友"这是骗局"的meta警示，不是骗局本身 |
| T1505 | keep_but_flag         | low        | XXX成人图片招揽，证据明确                        |
| T4358 | should_fix            | high       | 纯段子，无招揽                                   |
| T3105 | keep_but_flag         | low        | 结尾"cst std ntwk chg £1.50"是计费披露          |
| T2793 | keep_but_flag         | low        | 露骨内容+个人号码，成人聊天招揽                  |
| T4296 | should_fix            | high       | 私人提问式闲聊，无招揽                           |
| T3963 | keep_but_flag         | low        | 明确许诺"access to all adult parties"招揽        |
| T1926 | keep_but_flag         | low        | "Txt XXX SLO(4msgs)"是标准成人短信指令格式       |
| T2229 | keep_but_flag         | medium     | 汉堡王促销广告，商业群发性质成立                 |
| T1149 | should_fix            | high       | 个人二手物品出售，典型误标ham                    |
| T2847 | ambiguous_policy_case | medium     | 俱乐部通知vs广告群发，取决于收件人是否会员       |
| T1322 | should_fix            | high       | 关于计费责任的对话片段，无招揽                   |
| T1951 | keep_but_flag         | low        | "1/1"编号是连续群发链式spam的标志                |
| T2521 | keep_but_flag         | low        | 已收费确认+升级购买引导，证据明确                |
| T2273 | keep_but_flag         | medium     | Interflora鲜花广告，商业群发                     |
| T4433 | should_fix            | high       | 个人对3mobile账单纠纷的吐槽                      |
| T3864 | keep_but_flag         | low        | 成人网站+账号密码，招揽明确                      |
| T3947 | keep_but_flag         | low        | Lucozade促销+资费代码，广告成立                  |
| T0948 | keep_but_flag         | low        | 同T3947，重复文本                                |
| T3981 | ambiguous_policy_case | medium     | 慈善捐款群发算不算spam是政策问题                 |
| T2172 | should_fix            | medium     | 像是本人被扣款后求助的吐槽                       |
| T1811 | should_fix            | medium     | 同T2172，重复表述                                |
| T3015 | keep_but_flag         | low        | 文本残缺无法判读，但邻居100%一致support spam     |
| T3461 | ambiguous_policy_case | medium     | 讨论匿名短信服务的meta评论，动机不明             |
| T1557 | keep_but_flag         | low        | "dogging"+资费披露，明确成人招揽                 |
| T0006 | keep_but_flag         | low        | 调情包装+资费披露                                |
| T3202 | keep_but_flag         | medium     | 铃声短代码典型格式，邻居100%support              |
| T3926 | keep_but_flag         | medium     | 影院促销+短代码回复，广告成立                    |

### B 部分（全部 35 条）

| ID    | decision                     | confidence | 理由                                                    |
| ----- | ---------------------------- | ---------- | ------------------------------------------------------- |
| H0935 | false_positive_audit_finding | high       | "I liked the new mobile"内容毫无可疑之处                |
| T0935 | keep_but_flag                | low        | 露骨招揽+资费号码，无实质歧义                           |
| T3511 | keep_but_flag                | low        | 溢价竞猜格式明确                                        |
| T0660 | keep_but_flag                | low        | 拍卖竞价提醒，典型spam模式                              |
| H0146 | keep_but_flag                | low        | 旅游促销广告                                            |
| T0712 | keep_but_flag                | medium     | 付费内容提醒，批量自动化消息                            |
| H0151 | keep_but_flag                | low        | 交友群发+资费                                           |
| T2259 | keep_but_flag                | low        | 铃声广告片段                                            |
| H0181 | keep_but_flag                | low        | 同H0151模式                                             |
| T2758 | ambiguous_policy_case        | medium     | 服务开通问询——用户主动注册vs诱导陷阱无法判断          |
| H0944 | keep_but_flag                | medium     | 铃声订阅服务通知                                        |
| H1024 | keep_but_flag                | medium     | 免费内容链接，批量广告                                  |
| H0801 | keep_but_flag                | medium     | 贷款广告                                                |
| T3592 | keep_but_flag                | low        | 露骨成人热线                                            |
| T1363 | keep_but_flag                | medium     | 订阅欠费提醒，批量消息                                  |
| T0433 | keep_but_flag                | medium     | 铃声发货确认，广告尾款                                  |
| T3811 | keep_but_flag                | low        | 现金抽奖广告                                            |
| T4301 | keep_but_flag                | medium     | 拍卖提醒（与C部分单信号候选重复出现，提示数据去重问题） |
| T1427 | keep_but_flag                | medium     | WAP游戏广告                                             |
| T3796 | keep_but_flag                | medium     | 同T1427，重复文本                                       |
| T2658 | ambiguous_policy_case        | low        | 残缺片段像私人致谢，无法确证                            |
| T3123 | ambiguous_policy_case        | medium     | 图片链接——正规照片分享服务vs营销链接无法区分          |
| H0030 | ambiguous_policy_case        | medium     | 悬念式广告，但无价格/号码等硬证据                       |
| T1884 | keep_but_flag                | medium     | 铃声订阅广告（与C部分重复出现）                         |
| T1174 | should_fix                   | medium     | 内容是"我正在被spam骚扰"的吐槽，本身非招揽              |
| T2824 | keep_but_flag                | low        | 典型股票拉高出货spam                                    |
| T4097 | keep_but_flag                | low        | "账户对账单"经典spam开场                                |
| T0047 | keep_but_flag                | medium     | 体育问答订阅spam                                        |
| T0470 | false_positive_audit_finding | hig        | "Waiting for your call."毫无spam可能性                  |
| T0845 | keep_but_flag                | low        | 溢价号"猜猜谁喜欢你"骗局                                |
| T4033 | keep_but_flag                | low        | 订阅广告                                                |
| T0341 | keep_but_flag                | low        | 交友热线spam                                            |
| H0287 | keep_but_flag                | low        | 明确资费的成人聊天线                                    |
| T4431 | keep_but_flag                | low        | 同T3592模式                                             |
| T0255 | keep_but_flag                | medium     | 交友服务群发，模型本身未分歧只是邻居混杂                |



**H0935 / T0470 confidence 修正**

| ID    | decision                     | confidence | 理由                                       |
| ----- | ---------------------------- | ---------- | ------------------------------------------ |
| H0935 | false_positive_audit_finding | low        | 内容毫无可疑之处，检测算法误报，非真实问题 |
| T0470 | false_positive_audit_finding | low        | 同上                                       |

**A部分补齐的14条**

| ID    | decision              | confidence | 理由                                                                   |
| ----- | --------------------- | ---------- | ---------------------------------------------------------------------- |
| T2378 | should_fix            | high       | 纯段子，无招揽、无联系方式                                             |
| T2139 | ambiguous_policy_case | medium     | 调情式开场，无资费/号码等硬证据，私聊或聊天线服务都说得通              |
| T2710 | ambiguous_policy_case | medium     | 070号码无资费披露，与T3390用同一标准                                   |
| H0550 | ambiguous_policy_case | medium     | "ROMCAPspam"可能是真实占星spam文本残留，也可能是语料标注污染，无法确证 |
| H0896 | should_fix            | high       | 受害者求助语气，本身非招揽                                             |
| T2055 | keep_but_flag         | medium     | "brought to you by X Ltd"是批量广告典型footer，文本虽被截断            |
| H0143 | should_fix            | high       | 段子，无招揽                                                           |
| T0059 | should_fix            | high       | 段子，无招揽                                                           |
| T2232 | should_fix            | high       | 段子，无招揽                                                           |
| T0774 | ambiguous_policy_case | medium     | 文本截断，暗示成人内容但缺资费/号码硬证据                              |
| H0814 | keep_but_flag         | medium     | 竞猜回复格式是该语料典型溢价套路，但未显示价格，降级为medium           |
| T2755 | keep_but_flag         | high       | "one gbp/sms"是明确计费证据                                            |
| T0702 | ambiguous_policy_case | medium     | 索要地址/生日可疑，但无资费/号码硬证据，也可能是真实市调               |
| T0592 | keep_but_flag         | medium     | 伪装语音提醒的药品广告套路，但"call 123"无明确资费                     |

**其余按统一标准调整的条目**

| ID    | decision              | confidence | 理由                                                                                           |
| ----- | --------------------- | ---------- | ---------------------------------------------------------------------------------------------- |
| T3390 | ambiguous_policy_case | medium     | 070号码无资费披露，与T2710同标准                                                               |
| T1951 | ambiguous_policy_case | medium     | 个人网站分享vs陌生人推广，取决收发关系，无计费/商业证据（"1/1"是单条消息证据，非链式群发证据） |
| T1149 | should_fix            | high       | 英式冷笑话（无doubles/trebles的镖盘等于废物），无真实交易意图与联系方式                        |
| T1322 | should_fix            | medium     | 计费责任评论，无招揽，但"0A$NETWORKS"前缀含义不明确                                            |
| T2273 | ambiguous_policy_case | medium     | 真实商家（Interflora）促销，合法商业群发算不算spam是标注指南问题                               |
| T2229 | ambiguous_policy_case | medium     | 同上，Burger King真实商家促销                                                                  |
| T2793 | keep_but_flag         | medium     | 域名"Nikiyu4.net"暗示商业成人服务，但无明确价格，降级                                          |
| T3963 | keep_but_flag         | medium     | 承诺后续提供成人内容访问，但无资费披露，降级                                                   |
| T3864 | keep_but_flag         | medium     | 成人网站+账号密码是内容证据，但无价格，降级                                                    |
