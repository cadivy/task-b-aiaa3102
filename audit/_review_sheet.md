# 人工裁定评审表（B：目标 4 + 6）

对每条填 decision。四个合法值：`should_fix` / `keep_but_flag` / `ambiguous_policy_case` / `false_positive_audit_finding`

置信度：`high` / `medium` / `low`。记得 high 要留额度。


---

## A 部分：label_error 候选（signal_count >= 2，共 70 条，下列 top 45）

信号列含义：W=word模型反对 C=char模型反对 N=近邻反对


### T2378  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WCN` (3/3) | 反对强度 0.992 | word_p_spam 0.009 char_p_spam 0.008
- 近邻反对占比 1.00 | 最近反对邻居 T1203 (sim 0.328)
- 邻居标签: `ham|ham|ham|ham|ham`

> Do you ever notice that when you're driving, anyone going slower than you is an idiot and everyone driving faster than you is a maniac?

**decision:** ___  **confidence:** ___  **理由:** ___


### T2139  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WCN` (3/3) | 反对强度 0.987 | word_p_spam 0.016 char_p_spam 0.011
- 近邻反对占比 1.00 | 最近反对邻居 T3992 (sim 0.343)
- 邻居标签: `ham|ham|ham|ham|ham`

> Hello darling how are you today? I would love to have a chat, why dont you tell me what you look like and what you are in to sexy?

**decision:** ___  **confidence:** ___  **理由:** ___


### T2710  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WCN` (3/3) | 反对强度 0.951 | word_p_spam 0.071 char_p_spam 0.026
- 近邻反对占比 1.00 | 最近反对邻居 T1892 (sim 0.353)
- 邻居标签: `ham|ham|ham|ham|ham`

> Sorry I missed your call let's talk when you have the time. I'm on 07090201529

**decision:** ___  **confidence:** ___  **理由:** ___


### H0550  [heldout]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WCN` (3/3) | 反对强度 0.928 | word_p_spam 0.081 char_p_spam 0.063
- 近邻反对占比 1.00 | 最近反对邻居 T0664 (sim 0.324)
- 邻居标签: `ham|ham|ham|ham|ham`

> ROMCAPspam Everyone around should be responding well to your presence since you are so warm and outgoing. You are bringing in a real breath of sunshine.

**decision:** ___  **confidence:** ___  **理由:** ___


### H0896  [heldout]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WCN` (3/3) | 反对强度 0.916 | word_p_spam 0.105 char_p_spam 0.063
- 近邻反对占比 1.00 | 最近反对邻居 H0978 (sim 0.319)
- 邻居标签: `ham|ham|ham|ham|ham`

> Money i have won wining number 946 wot do i do next

**decision:** ___  **confidence:** ___  **理由:** ___


### T2055  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WCN` (3/3) | 反对强度 0.878 | word_p_spam 0.136 char_p_spam 0.109
- 近邻反对占比 1.00 | 最近反对邻居 T3751 (sim 0.301)
- 邻居标签: `ham|ham|ham|ham|ham`

> This message is brought to you by GMW Ltd. and is not connected to the

**decision:** ___  **confidence:** ___  **理由:** ___


### H0143  [heldout]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.982 | word_p_spam 0.017 char_p_spam 0.019
- 近邻反对占比 1.00 | 最近反对邻居 T3740 (sim 0.204)
- 邻居标签: `ham|ham|ham|ham|ham`

> Do you realize that in about 40 years, we'll have thousands of old ladies running around with tattoos?

**decision:** ___  **confidence:** ___  **理由:** ___


### T0059  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.965 | word_p_spam 0.037 char_p_spam 0.032
- 近邻反对占比 1.00 | 最近反对邻居 T2587 (sim 0.287)
- 邻居标签: `ham|ham|ham|ham|ham`

> Did you hear about the new "Divorce Barbie"? It comes with all of Ken's stuff!

**decision:** ___  **confidence:** ___  **理由:** ___


### T2232  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.963 | word_p_spam 0.051 char_p_spam 0.024
- 近邻反对占比 1.00 | 最近反对邻居 T1184 (sim 0.244)
- 邻居标签: `ham|ham|ham|ham|ham`

> How come it takes so little time for a child who is afraid of the dark to become a teenager who wants to stay out all night?

**decision:** ___  **confidence:** ___  **理由:** ___


### T0774  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WCN` (3/3) | 反对强度 0.798 | word_p_spam 0.191 char_p_spam 0.213
- 近邻反对占比 0.81 | 最近反对邻居 T0470 (sim 0.354)
- 邻居标签: `ham|ham|spam|ham|ham`

> Filthy stories and GIRLS waiting for your

**decision:** ___  **confidence:** ___  **理由:** ___


### H0814  [heldout]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.955 | word_p_spam 0.027 char_p_spam 0.064
- 近邻反对占比 1.00 | 最近反对邻居 T0229 (sim 0.189)
- 邻居标签: `ham|ham|ham|ham|ham`

> In The Simpsons Movie released in July 2007 name the band that died at the start of the film? A-Green Day, B-Blue Day, C-Red Day. (Send A, B or C)

**decision:** ___  **confidence:** ___  **理由:** ___


### T2755  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.953 | word_p_spam 0.047 char_p_spam 0.046
- 近邻反对占比 1.00 | 最近反对邻居 T0262 (sim 0.206)
- 邻居标签: `ham|ham|ham|ham|ham`

> LIFE has never been this much fun and great until you came in. You made it truly special for me. I won't forget you! enjoy @ one gbp/sms

**decision:** ___  **confidence:** ___  **理由:** ___


### T0702  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.953 | word_p_spam 0.051 char_p_spam 0.043
- 近邻反对占比 1.00 | 最近反对邻居 T3660 (sim 0.235)
- 邻居标签: `ham|ham|ham|ham|ham`

> Hello. We need some posh birds and chaps to user trial prods for champneys. Can i put you down? I need your address and dob asap. Ta r

**decision:** ___  **confidence:** ___  **理由:** ___


### T0592  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WCN` (3/3) | 反对强度 0.741 | word_p_spam 0.282 char_p_spam 0.236
- 近邻反对占比 1.00 | 最近反对邻居 H1061 (sim 0.300)
- 邻居标签: `ham|ham|ham|ham|ham`

> Email AlertFrom: Jeri StewartSize: 2KBSubject: Low-cost prescripiton drvgsTo listen to email call 123

**decision:** ___  **confidence:** ___  **理由:** ___


### H0330  [heldout]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WCN` (3/3) | 反对强度 0.738 | word_p_spam 0.304 char_p_spam 0.220
- 近邻反对占比 1.00 | 最近反对邻居 T2235 (sim 0.408)
- 邻居标签: `ham|ham|ham|ham|ham`

> Monthly password for wap. mobsi.com is 391784. Use your wap phone not PC.

**decision:** ___  **confidence:** ___  **理由:** ___


### T3272  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.913 | word_p_spam 0.107 char_p_spam 0.068
- 近邻反对占比 1.00 | 最近反对邻居 T0525 (sim 0.231)
- 邻居标签: `ham|ham|ham|ham|ham`

> TBS/PERSOLVO. been chasing us since Sept for£38 definitely not paying now thanks to your information. We will ignore them. Kath. Manchester.

**decision:** ___  **confidence:** ___  **理由:** ___


### T3390  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WCN` (3/3) | 反对强度 0.772 | word_p_spam 0.172 char_p_spam 0.284
- 近邻反对占比 0.63 | 最近反对邻居 T2698 (sim 0.358)
- 邻居标签: `ham|spam|ham|spam|ham`

> Missed call alert. These numbers called but left no message. 07008009200

**decision:** ___  **confidence:** ___  **理由:** ___


### T1798  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.930 | word_p_spam 0.037 char_p_spam 0.103
- 近邻反对占比 0.81 | 最近反对邻居 T2774 (sim 0.208)
- 邻居标签: `ham|ham|ham|spam|ham`

> Hi ya babe x u 4goten bout me?' scammers getting smart..Though this is a regular vodafone no, if you respond you get further prem rate msg/subscription. Other nos used also. Beware!

**decision:** ___  **confidence:** ___  **理由:** ___


### T1505  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.951 | word_p_spam 0.072 char_p_spam 0.025
- 近邻反对占比 0.63 | 最近反对邻居 T4408 (sim 0.223)
- 邻居标签: `ham|ham|spam|ham|spam`

> Would you like to see my XXX pics they are so hot they were nearly banned in the uk!

**decision:** ___  **confidence:** ___  **理由:** ___


### T4358  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.871 | word_p_spam 0.104 char_p_spam 0.153
- 近邻反对占比 1.00 | 最近反对邻居 T2691 (sim 0.215)
- 邻居标签: `ham|ham|ham|ham|ham`

> Latest News! Police station toilet stolen, cops have nothing to go on!

**decision:** ___  **confidence:** ___  **理由:** ___


### T3105  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.910 | word_p_spam 0.076 char_p_spam 0.103
- 近邻反对占比 0.78 | 最近反对邻居 T2027 (sim 0.215)
- 邻居标签: `spam|ham|ham|ham|ham`

> Oh my god! I've found your number again! I'm so glad, text me back xafter this msgs cst std ntwk chg £1.50

**decision:** ___  **confidence:** ___  **理由:** ___


### T2793  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.963 | word_p_spam 0.034 char_p_spam 0.040
- 近邻反对占比 0.50 | 最近反对邻居 T2312 (sim 0.225)
- 邻居标签: `spam|spam|ham|ham|ham`

> Not heard from U4 a while. Call me now am here all night with just my knickers on. Make me beg for it like U did last time 01223585236 XX Luv Nikiyu4.net

**decision:** ___  **confidence:** ___  **理由:** ___


### T4296  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.856 | word_p_spam 0.120 char_p_spam 0.167
- 近邻反对占比 1.00 | 最近反对邻居 T3751 (sim 0.276)
- 邻居标签: `ham|ham|ham|ham|ham`

> dating:i have had two of these. Only started after i sent a text to talk sport radio last week. Any connection do you think or coincidence?

**decision:** ___  **confidence:** ___  **理由:** ___


### T3963  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.893 | word_p_spam 0.112 char_p_spam 0.101
- 近邻反对占比 0.81 | 最近反对邻居 T4428 (sim 0.267)
- 邻居标签: `ham|ham|spam|ham|ham`

> Hi this is Amy, we will be sending you a free phone number in a couple of days, which will give you an access to all the adult parties...

**decision:** ___  **confidence:** ___  **理由:** ___


### T1926  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.897 | word_p_spam 0.053 char_p_spam 0.153
- 近邻反对占比 0.79 | 最近反对邻居 H0090 (sim 0.170)
- 邻居标签: `spam|ham|ham|ham|ham`

> Babe: U want me dont u baby! Im nasty and have a thing 4 filthyguys. Fancy a rude time with a sexy bitch. How about we go slo n hard! Txt XXX SLO(4msgs)

**decision:** ___  **confidence:** ___  **理由:** ___


### T2229  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.826 | word_p_spam 0.162 char_p_spam 0.186
- 近邻反对占比 1.00 | 最近反对邻居 T0052 (sim 0.239)
- 邻居标签: `ham|ham|ham|ham|ham`

> Burger King - Wanna play footy at a top stadium? Get 2 Burger King before 1st Sept and go Large or Super with Coca-Cola and walk out a winner

**decision:** ___  **confidence:** ___  **理由:** ___


### T1149  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.906 | word_p_spam 0.069 char_p_spam 0.120
- 近邻反对占比 0.56 | 最近反对邻居 T3400 (sim 0.188)
- 邻居标签: `spam|ham|ham|spam|ham`

> For sale - arsenal dartboard. Good condition but no doubles or trebles!

**decision:** ___  **confidence:** ___  **理由:** ___


### T2847  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.799 | word_p_spam 0.248 char_p_spam 0.155
- 近邻反对占比 1.00 | 最近反对邻居 T4248 (sim 0.195)
- 邻居标签: `ham|ham|ham|ham|ham`

> Xmas & New Years Eve tickets are now on sale from the club, during the day from 10am till 8pm, and on Thurs, Fri & Sat night this week. They're selling fast!

**decision:** ___  **confidence:** ___  **理由:** ___


### T1322  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.797 | word_p_spam 0.233 char_p_spam 0.172
- 近邻反对占比 1.00 | 最近反对邻居 T4087 (sim 0.203)
- 邻居标签: `ham|ham|ham|ham|ham`

> 0A$NETWORKS allow companies to bill for SMS, so they are responsible for their "suppliers", just as a shop has to give a guarantee on what they sell. B. G.

**decision:** ___  **confidence:** ___  **理由:** ___


### T1951  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.796 | word_p_spam 0.323 char_p_spam 0.086
- 近邻反对占比 1.00 | 最近反对邻居 T1445 (sim 0.278)
- 邻居标签: `ham|ham|ham|ham|ham`

> Guess who am I?This is the first time I created a web page WWW.ASJESUS.COM read all I wrote. I'm waiting for your opinions. I want to be your friend 1/1

**decision:** ___  **confidence:** ___  **理由:** ___


### T2521  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.790 | word_p_spam 0.124 char_p_spam 0.295
- 近邻反对占比 0.80 | 最近反对邻居 T0562 (sim 0.240)
- 邻居标签: `ham|ham|spam|ham|ham`

> LookAtMe!: Thanks for your purchase of a video clip from LookAtMe!, you've been charged 35p. Think you can do better? Why not send a video in a MMSto 32323.

**decision:** ___  **confidence:** ___  **理由:** ___


### T2273  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.744 | word_p_spam 0.238 char_p_spam 0.274
- 近邻反对占比 1.00 | 最近反对邻居 T3570 (sim 0.280)
- 邻居标签: `ham|ham|ham|ham|ham`

> INTERFLORA - It's not too late to order Interflora flowers for christmas call 0800 505060 to place your order before Midnight tomorrow.

**decision:** ___  **confidence:** ___  **理由:** ___


### T4433  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.743 | word_p_spam 0.064 char_p_spam 0.449
- 近邻反对占比 1.00 | 最近反对邻居 T1049 (sim 0.149)
- 邻居标签: `ham|ham|ham|ham|ham`

> ASKED 3MOBILE IF 0870 CHATLINES INCLU IN FREE MINS. INDIA CUST SERVs SED YES. L8ER GOT MEGA BILL. 3 DONT GIV A SHIT. BAILIFF DUE IN DAYS. I O £250 3 WANT £800

**decision:** ___  **confidence:** ___  **理由:** ___


### T3864  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.812 | word_p_spam 0.195 char_p_spam 0.182
- 近邻反对占比 0.64 | 最近反对邻居 T0693 (sim 0.239)
- 邻居标签: `ham|ham|ham|spam|spam`

> Check Out Choose Your Babe Videos @ sms.shsex.netUN fgkslpoPW fgkslpo

**decision:** ___  **confidence:** ___  **理由:** ___


### T3947  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.724 | word_p_spam 0.341 char_p_spam 0.212
- 近邻反对占比 1.00 | 最近反对邻居 T2323 (sim 0.103)
- 邻居标签: `ham|ham|ham|ham|ham`

> Got what it takes 2 take part in the WRC Rally in Oz? U can with Lucozade Energy! Text RALLY LE to 61200 (25p), see packs or lucozade.co.uk/wrc & itcould be u!

**decision:** ___  **confidence:** ___  **理由:** ___


### T0948  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.724 | word_p_spam 0.341 char_p_spam 0.212
- 近邻反对占比 1.00 | 最近反对邻居 T2323 (sim 0.103)
- 邻居标签: `ham|ham|ham|ham|ham`

> Got what it takes 2 take part in the WRC Rally in Oz? U can with Lucozade Energy! Text RALLY LE to 61200 (25p), see packs or lucozade.co.uk/wrc & itcould be u!

**decision:** ___  **confidence:** ___  **理由:** ___


### T3981  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.717 | word_p_spam 0.376 char_p_spam 0.189
- 近邻反对占比 1.00 | 最近反对邻居 T2611 (sim 0.198)
- 邻居标签: `ham|ham|ham|ham|ham`

> You can donate £2.50 to UNICEF's Asian Tsunami disaster support fund by texting DONATE to 864233. £2.50 will be added to your next bill

**decision:** ___  **confidence:** ___  **理由:** ___


### T2172  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.813 | word_p_spam 0.166 char_p_spam 0.209
- 近邻反对占比 0.48 | 最近反对邻居 T0929 (sim 0.231)
- 邻居标签: `spam|ham|ham|ham|ham`

> FROM 88066 LOST £12 HELP

**decision:** ___  **confidence:** ___  **理由:** ___


### T1811  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.827 | word_p_spam 0.173 char_p_spam 0.173
- 近邻反对占比 0.41 | 最近反对邻居 T0929 (sim 0.170)
- 邻居标签: `spam|ham|ham|ham|ham`

> 88066 FROM 88066 LOST 3POUND HELP

**decision:** ___  **confidence:** ___  **理由:** ___


### T3015  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.900 | word_p_spam 0.047 char_p_spam 0.152
- 近邻反对占比 0.00 | 最近反对邻居  (sim 0.000)
- 邻居标签: `spam|spam|spam|spam|spam`

> 2/2 146tf150p

**decision:** ___  **confidence:** ___  **理由:** ___


### T3461  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.688 | word_p_spam 0.296 char_p_spam 0.329
- 近邻反对占比 1.00 | 最近反对邻居 T3117 (sim 0.275)
- 邻居标签: `ham|ham|ham|ham|ham`

> thesmszone.com lets you send free anonymous and masked messages..im sending this message from there..do you see the potential for abuse???

**decision:** ___  **confidence:** ___  **理由:** ___


### T1557  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.723 | word_p_spam 0.324 char_p_spam 0.230
- 近邻反对占比 0.62 | 最近反对邻居 T0363 (sim 0.203)
- 邻居标签: `ham|ham|spam|ham|spam`

> More people are dogging in your area now. Call 09090204448 and join like minded guys. Why not arrange 1 yourself. There's 1 this evening. A£1.50 minAPN LS278BB

**decision:** ___  **confidence:** ___  **理由:** ___


### T0006  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.727 | word_p_spam 0.216 char_p_spam 0.331
- 近邻反对占比 0.59 | 最近反对邻居 T1593 (sim 0.173)
- 邻居标签: `spam|ham|ham|spam|ham`

> FreeMsg Hey there darling it's been 3 week's now and no word back! I'd like some fun you up for it still? Tb ok! XxX std chgs to send, £1.50 to rcv

**decision:** ___  **confidence:** ___  **理由:** ___


### T3202  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.828 | word_p_spam 0.049 char_p_spam 0.296
- 近邻反对占比 0.00 | 最近反对邻居  (sim 0.000)
- 邻居标签: `spam|spam|spam|spam|spam`

> ringtoneking 84484

**decision:** ___  **confidence:** ___  **理由:** ___


### T3926  [train]  公开标签=**spam** → 模型主张 **ham**
- 信号 `WC-` (2/3) | 反对强度 0.664 | word_p_spam 0.297 char_p_spam 0.375
- 近邻反对占比 0.81 | 最近反对邻居 T1544 (sim 0.201)
- 邻居标签: `ham|ham|ham|spam|ham`

> Warner Village 83118 C Colin Farrell in SWAT this wkend @Warner Village & get 1 free med. Popcorn!Just show msg+ticket@kiosk.Valid 4-7/12. C t&c @kiosk. Reply SONY 4 mre film offers

**decision:** ___  **confidence:** ___  **理由:** ___


---

## B 部分：ambiguous 候选（共 177 条，下列 top 35）

提醒：模糊 ≠ 低置信度。要挑「两种标签都讲得通」的，并**刻意留 1-2 条**概率骑在 0.5 但内容明显普通的，标为 `false_positive_audit_finding`。


### H0935  [heldout]  公开标签=**ham**
- 模型分歧 True | 距边界 0.019 | 邻居混杂度 0.96 | ambiguity_score 1.748
- word_p_spam 0.435 char_p_spam 0.527 | 邻居标签 `ham|spam|ham|spam|spam`

> I liked the new mobile

**decision:** ___  **confidence:** ___  **理由:** ___


### T0935  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.007 | 邻居混杂度 0.85 | ambiguity_score 1.724
- word_p_spam 0.443 char_p_spam 0.542 | 邻居标签 `spam|ham|ham|spam|ham`

> 1000's of girls many local 2 u who r virgins 2 this & r ready 2 4fil ur every sexual need. Can u 4fil theirs? text CUTE to 69911(£1.50p. m)

**decision:** ___  **confidence:** ___  **理由:** ___


### T3511  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.002 | 邻居混杂度 0.77 | ambiguity_score 1.701
- word_p_spam 0.554 char_p_spam 0.441 | 邻居标签 `spam|ham|ham|ham|ham`

> Ur balance is now £600. Next question: Complete the landmark, Big, A. Bob, B. Barry or C. Ben ?. Text A, B or C to 83738. Good luck!

**decision:** ___  **confidence:** ___  **理由:** ___


### T0660  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.019 | 邻居混杂度 0.77 | ambiguity_score 1.672
- word_p_spam 0.600 char_p_spam 0.362 | 邻居标签 `spam|ham|spam|ham|spam`

> U were outbid by simonwatson5120 on the Shinco DVD Plyr. 2 bid again, visit sms. ac/smsrewards 2 end bid notifications, reply END OUT

**decision:** ___  **confidence:** ___  **理由:** ___


### H0146  [heldout]  公开标签=**spam**
- 模型分歧 True | 距边界 0.023 | 邻居混杂度 0.77 | ambiguity_score 1.661
- word_p_spam 0.601 char_p_spam 0.445 | 邻居标签 `ham|spam|ham|ham|spam`

> Romantic Paris. 2 nights, 2 flights from £79 Book now 4 next year. Call 08704439680Ts&Cs apply.

**decision:** ___  **confidence:** ___  **理由:** ___


### T0712  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.016 | 邻居混杂度 0.70 | ambiguity_score 1.650
- word_p_spam 0.615 char_p_spam 0.354 | 邻居标签 `spam|spam|spam|ham|ham`

> Reminder: You have not downloaded the content you have already paid for. Goto http://doit. mymoby. tv/ to collect your content.

**decision:** ___  **confidence:** ___  **理由:** ___


### H0151  [heldout]  公开标签=**spam**
- 模型分歧 True | 距边界 0.035 | 邻居混杂度 0.75 | ambiguity_score 1.629
- word_p_spam 0.562 char_p_spam 0.367 | 邻居标签 `spam|ham|ham|ham|ham`

> Ever thought about living a good life with a perfect partner? Just txt back NAME and AGE to join the mobile community. (100p/SMS)

**decision:** ___  **confidence:** ___  **理由:** ___


### T2259  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.052 | 邻居混杂度 0.74 | ambiguity_score 1.594
- word_p_spam 0.470 char_p_spam 0.633 | 邻居标签 `spam|ham|ham|spam|spam`

> FreeMsg>FAV XMAS TONES!Reply REAL

**decision:** ___  **confidence:** ___  **理由:** ___


### H0181  [heldout]  公开标签=**spam**
- 模型分歧 True | 距边界 0.035 | 邻居混杂度 0.65 | ambiguity_score 1.590
- word_p_spam 0.594 char_p_spam 0.475 | 邻居标签 `spam|ham|ham|ham|ham`

> How about getting in touch with folks waiting for company? Just txt back your NAME and AGE to opt in! Enjoy the community (150p/SMS)

**decision:** ___  **confidence:** ___  **理由:** ___


### T2758  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.006 | 邻居混杂度 0.50 | ambiguity_score 1.589
- word_p_spam 0.489 char_p_spam 0.523 | 邻居标签 `spam|ham|ham|ham|ham`

> Welcome! Please reply with your AGE and GENDER to begin. e.g 24M

**decision:** ___  **confidence:** ___  **理由:** ___


### H0944  [heldout]  公开标签=**spam**
- 模型分歧 True | 距边界 0.005 | 邻居混杂度 0.43 | ambiguity_score 1.561
- word_p_spam 0.504 char_p_spam 0.485 | 邻居标签 `spam|ham|spam|spam|spam`

> Your weekly Cool-Mob tones are ready to download !This weeks new Tones include: 1) Crazy Frog-AXEL F>>> 2) Akon-Lonely>>> 3) Black Eyed-Dont P >>>More info in n

**decision:** ___  **confidence:** ___  **理由:** ___


### H1024  [heldout]  公开标签=**spam**
- 模型分歧 True | 距边界 0.020 | 邻居混杂度 0.46 | ambiguity_score 1.542
- word_p_spam 0.675 char_p_spam 0.366 | 邻居标签 `ham|spam|spam|spam|spam`

> TheMob>Hit the link to get a premium Pink Panther game, the new no. 1 from Sugababes, a crazy Zebra animation or a badass Hoody wallpaper-all 4 FREE!

**decision:** ___  **confidence:** ___  **理由:** ___


### H0801  [heldout]  公开标签=**spam**
- 模型分歧 True | 距边界 0.010 | 邻居混杂度 0.33 | ambiguity_score 1.513
- word_p_spam 0.537 char_p_spam 0.483 | 邻居标签 `spam|spam|spam|ham|spam`

> Loans for any purpose even if you have Bad Credit! Tenants Welcome. Call NoWorriesLoans.com on 08717111821

**decision:** ___  **confidence:** ___  **理由:** ___


### T3592  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.029 | 邻居混杂度 0.42 | ambiguity_score 1.509
- word_p_spam 0.389 char_p_spam 0.553 | 邻居标签 `spam|ham|ham|spam|spam`

> Want explicit SEX in 30 secs? Ring 02073162414 now! Costs 20p/min

**decision:** ___  **confidence:** ___  **理由:** ___


### T1363  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.107 | 邻居混杂度 0.79 | ambiguity_score 1.502
- word_p_spam 0.496 char_p_spam 0.718 | 邻居标签 `spam|spam|ham|ham|spam`

> Free msg. Sorry, a service you ordered from 81303 could not be delivered as you do not have sufficient credit. Please top up to receive the service.

**decision:** ___  **confidence:** ___  **理由:** ___


### T0433  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.047 | 邻居混杂度 0.45 | ambiguity_score 1.487
- word_p_spam 0.252 char_p_spam 0.654 | 邻居标签 `ham|spam|spam|spam|spam`

> You will recieve your tone within the next 24hrs. For Terms and conditions please see Channel U Teletext Pg 750

**decision:** ___  **confidence:** ___  **理由:** ___


### T3811  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.036 | 邻居混杂度 0.38 | ambiguity_score 1.479
- word_p_spam 0.711 char_p_spam 0.362 | 邻居标签 `ham|ham|spam|ham|ham`

> Cashbin.co.uk (Get lots of cash this weekend!) www.cashbin.co.uk Dear Welcome to the weekend We have got our biggest and best EVER cash give away!! These..

**decision:** ___  **confidence:** ___  **理由:** ___


### T4301  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.102 | 邻居混杂度 0.68 | ambiguity_score 1.468
- word_p_spam 0.291 char_p_spam 0.506 | 邻居标签 `spam|spam|ham|ham|spam`

> The current leading bid is 151. To pause this auction send OUT. Customer Care: 08718726270

**decision:** ___  **confidence:** ___  **理由:** ___


### T1427  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.083 | 邻居混杂度 0.58 | ambiguity_score 1.465
- word_p_spam 0.726 char_p_spam 0.441 | 邻居标签 `spam|spam|ham|ham|spam`

> Buy Space Invaders 4 a chance 2 win orig Arcade Game console. Press 0 for Games Arcade (std WAP charge) See o2.co.uk/games 4 Terms + settings. No purchase

**decision:** ___  **confidence:** ___  **理由:** ___


### T3796  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.083 | 邻居混杂度 0.58 | ambiguity_score 1.465
- word_p_spam 0.726 char_p_spam 0.441 | 邻居标签 `spam|spam|ham|ham|spam`

> Buy Space Invaders 4 a chance 2 win orig Arcade Game console. Press 0 for Games Arcade (std WAP charge) See o2.co.uk/games 4 Terms + settings. No purchase

**decision:** ___  **confidence:** ___  **理由:** ___


### T2658  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.026 | 邻居混杂度 0.29 | ambiguity_score 1.463
- word_p_spam 0.814 char_p_spam 0.134 | 邻居标签 `ham|ham|ham|spam|ham`

> RCT' THNQ Adrian for U text. Rgds Vatian

**decision:** ___  **confidence:** ___  **理由:** ___


### T3123  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.057 | 邻居混杂度 0.38 | ambiguity_score 1.439
- word_p_spam 0.694 char_p_spam 0.419 | 邻居标签 `spam|spam|spam|spam|ham`

> A link to your picture has been sent. You can also use http://alto18.co.uk/wave/wave.asp?o=44345

**decision:** ___  **confidence:** ___  **理由:** ___


### H0030  [heldout]  公开标签=**spam**
- 模型分歧 True | 距边界 0.066 | 邻居混杂度 0.42 | ambiguity_score 1.435
- word_p_spam 0.763 char_p_spam 0.370 | 邻居标签 `ham|spam|ham|ham|ham`

> Are you unique enough? Find out from 30th August. www.areyouunique.co.uk

**decision:** ___  **confidence:** ___  **理由:** ___


### T1884  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.140 | 邻居混杂度 0.75 | ambiguity_score 1.419
- word_p_spam 0.191 char_p_spam 0.529 | 邻居标签 `ham|ham|spam|spam|ham`

> Download as many ringtones as u like no restrictions, 1000s 2 choose. U can even send 2 yr buddys. Txt Sir to 80082 £3 

**decision:** ___  **confidence:** ___  **理由:** ___


### T1174  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.071 | 邻居混杂度 0.40 | ambiguity_score 1.417
- word_p_spam 0.241 char_p_spam 0.618 | 邻居标签 `spam|spam|ham|spam|spam`

> Bought one ringtone and now getting texts costing 3 pound offering more tones etc

**decision:** ___  **confidence:** ___  **理由:** ___


### T2824  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.036 | 邻居混杂度 0.15 | ambiguity_score 1.389
- word_p_spam 0.504 char_p_spam 0.424 | 邻居标签 `spam|spam|spam|spam|ham`

> Dorothy@kiefer.com (Bank of Granite issues Strong-Buy) EXPLOSIVE PICK FOR OUR MEMBERS *****UP OVER 300% *********** Nasdaq Symbol CDGT That is a $5.00 per..

**decision:** ___  **confidence:** ___  **理由:** ___


### T4097  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.013 | 邻居混杂度 0.00 | ambiguity_score 1.373
- word_p_spam 0.501 char_p_spam 0.472 | 邻居标签 `spam|spam|spam|spam|spam`

> PRIVATE! Your 2003 Account Statement for 078

**decision:** ___  **confidence:** ___  **理由:** ___


### T0047  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.014 | 邻居混杂度 0.00 | ambiguity_score 1.371
- word_p_spam 0.622 char_p_spam 0.349 | 邻居标签 `ham|ham|ham|ham|ham`

> SMS. ac Sptv: The New Jersey Devils and the Detroit Red Wings play Ice Hockey. Correct or Incorrect? End? Reply END SPTV

**decision:** ___  **confidence:** ___  **理由:** ___


### T0470  [train]  公开标签=**ham**
- 模型分歧 True | 距边界 0.019 | 邻居混杂度 0.00 | ambiguity_score 1.363
- word_p_spam 0.689 char_p_spam 0.349 | 邻居标签 `ham|ham|ham|ham|ham`

> Waiting for your call.

**decision:** ___  **confidence:** ___  **理由:** ___


### T0845  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.025 | 邻居混杂度 0.00 | ambiguity_score 1.349
- word_p_spam 0.373 char_p_spam 0.577 | 邻居标签 `spam|spam|spam|spam|spam`

> We know someone who you know that fancies you. Call 09058097218 to find out who. POBox 6, LS15HB 150p

**decision:** ___  **confidence:** ___  **理由:** ___


### T4033  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.026 | 邻居混杂度 0.00 | ambiguity_score 1.348
- word_p_spam 0.578 char_p_spam 0.473 | 邻居标签 `ham|ham|ham|ham|ham`

> You won't believe it but it's true. It's Incredible Txts! Reply G now to learn truly amazing things that will blow your mind. From O2FWD only 18p/txt

**decision:** ___  **confidence:** ___  **理由:** ___


### T0341  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.028 | 邻居混杂度 0.00 | ambiguity_score 1.344
- word_p_spam 0.409 char_p_spam 0.648 | 邻居标签 `spam|spam|spam|spam|spam`

> 100 dating service cal;l 09064012103 box334sk38ch

**decision:** ___  **confidence:** ___  **理由:** ___


### H0287  [heldout]  公开标签=**spam**
- 模型分歧 True | 距边界 0.041 | 邻居混杂度 0.00 | ambiguity_score 1.318
- word_p_spam 0.305 char_p_spam 0.613 | 邻居标签 `spam|spam|spam|spam|spam`

> CLAIRE here am havin borin time & am now alone U wanna cum over 2nite? Chat now 09099725823 hope 2 C U Luv CLAIRE xx Calls£1/minmoremobsEMSPOBox45PO139WA

**decision:** ___  **confidence:** ___  **理由:** ___


### T4431  [train]  公开标签=**spam**
- 模型分歧 True | 距边界 0.124 | 邻居混杂度 0.39 | ambiguity_score 1.307
- word_p_spam 0.495 char_p_spam 0.752 | 邻居标签 `spam|ham|ham|spam|spam`

> Want explicit SEX in 30 secs? Ring 02073162414 now! Costs 20p/min Gsex POBOX 2667 WC1N 3XX

**decision:** ___  **confidence:** ___  **理由:** ___


### T0255  [train]  公开标签=**spam**
- 模型分歧 False | 距边界 0.025 | 邻居混杂度 0.87 | ambiguity_score 1.297
- word_p_spam 0.481 char_p_spam 0.470 | 邻居标签 `spam|spam|ham|ham|ham`

> SMS. ac Blind Date 4U!: Rodds1 is 21/m from Aberdeen, United Kingdom. Check Him out http://img. sms. ac/W/icmb3cktz8r7!-4 no Blind Dates send HIDE

**decision:** ___  **confidence:** ___  **理由:** ___


---

## C 部分：单信号 watchlist（3 条）—— 写「被拒候选」用


### T1799 [train] 标签=spam | 反对强度 0.650

> Back 2 work 2morro half term over! Can U C me 2nite 4 some sexy passion B4 I have 2 go back? Chat NOW 09099726481 Luv DENA Calls £1/minMobsmoreLKPOBOX177HP51FL


### T1884 [train] 标签=spam | 反对强度 0.640

> Download as many ringtones as u like no restrictions, 1000s 2 choose. U can even send 2 yr buddys. Txt Sir to 80082 £3 


### T4301 [train] 标签=spam | 反对强度 0.602

> The current leading bid is 151. To pause this auction send OUT. Customer Care: 08718726270
