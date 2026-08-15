# Superpowers 研究 — agentic skills 框架與開發方法論

> 狀態：🟡 進行中
> 開始日期：2026-08-15

## 目標

搞懂 [obra/superpowers](https://github.com/obra/superpowers) 這個 repo 在做什麼，
評估它對「我跟 Claude 的日常合作方式」有沒有實際幫助——哪些該直接裝來用、
哪些只值得偷觀念、哪些對我的使用情境是過重的。

## 進度

- [x] 第一輪 repo 掃描（README、目錄結構、核心 skill 內容）
- [x] 用 `writing-skills` 的方法測自己的 `/kb-push`：**RED 階段完成**（見下方實測）
- [x] GREEN 階段：照 RED 的結果重寫 `kb-push`，驗證通過
- [x] REFACTOR：找到一個漏洞、補掉、重測通過，新版已部署
- [x] 實際安裝 superpowers（v6.3.0），量 context 成本——**結果推翻了原本的疑慮，見下方**
- [ ] 決定要不要納入常態工作流，以及要納入哪幾個部分

## 這個 repo 是什麼

作者 Jesse Vincent（obra）。自稱「An agentic skills framework & software development
methodology that works.」——重點是後半：它不只是一包工具，是一套**強制的軟體開發流程**。

- 2025-10-09 開張，2026-01-15 進入 Anthropic 官方 Claude Code marketplace
- MIT 授權，目前約 27 萬星（4 月時約 13.7 萬，成長很快），是星數最多的 Claude Code skills repo
- 支援 14+ 種 agent／IDE：Claude Code、Cursor、Codex、Gemini CLI、OpenCode、Devin、Kimi…
  root 底下就是一堆 `.claude-plugin/`、`.codex-plugin/`、`.cursor-plugin/`、`.hermes-plugin/` 平行存在

安裝（Claude Code）：

```
/plugin install superpowers@claude-plugins-official
```

### 目錄結構

```
superpowers/
├── skills/          ← 核心，14 個 skill，每個一個資料夾 + SKILL.md
├── hooks/           ← session-start hook（開場就把方法論塞進 context）
├── scripts/         ← task-brief、review-package 等給 subagent 用的工具
├── docs/            ← 各平台安裝說明
├── tests/           ← skill 的評測 harness
├── AGENTS.md / CLAUDE.md / GEMINI.md
└── .{claude,codex,cursor,devin,hermes,kimi}-plugin/
```

### 14 個 skill

| 類別 | Skills |
|------|--------|
| 流程主幹 | brainstorming、writing-plans、executing-plans、subagent-driven-development |
| 品質 | test-driven-development、verification-before-completion |
| 除錯 | systematic-debugging |
| 審查 | requesting-code-review、receiving-code-review |
| 併行 | dispatching-parallel-agents |
| 基礎設施 | using-git-worktrees、finishing-a-development-branch |
| Meta | writing-skills、using-superpowers |

### 主張的流程

1. **Brainstorming** — 動手前先問清楚需求，把設計攤出來給人類確認
2. **Git worktree** — 設計通過後開隔離的工作區與分支
3. **Writing plans** — 拆成 2–5 分鐘一個的任務，寫明檔案路徑與驗證方式
4. **Subagent-driven development** — 每個任務派一個乾淨 context 的 subagent，做完過審查關卡
5. **TDD** — RED-GREEN-REFACTOR，測試先寫
6. **Code review** — 對著 plan 的規格審
7. **Finishing branch** — 決定 merge 還是開 PR

設計哲學四句：Test-Driven Development、Systematic over ad-hoc、
Complexity reduction、Evidence over claims。README 自己強調
「Mandatory workflows, not suggestions」——這些是規則不是建議。

## 幾個看下來覺得有料的 skill

### brainstorming

硬性規定：**人類批准設計意圖之前不准動手實作**。這道關卡不隨任務大小放寬，
只有產出物的厚度會變。它把任務分三條路徑：

- **Spike**（可行性問題）→ 講 2–3 句要怎麼探、批准、去查、回報。不寫設計文件，寫的東西都算丟棄品
- **Bounded**（既有流程的小範圍改動）→ 問清楚、在對話裡給短設計、停下來等明確批准、再實作
- **Architectural**（新專案／重構子系統）→ 完整流程：探索脈絡、釐清問題、給 2–3 個方案比較、
  分段設計逐段批准、寫成 spec 文件、自審、使用者審查關卡，然後才進 writing-plans

有一句講得挺準：「簡單任務正是沒被檢驗的假設最容易造成白工的地方。」
還有一條防鑽漏洞條款：**如果你是為了少做事才選比較輕的路徑，那就代表你該選重的那條。**

### systematic-debugging

「NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST」，四個強制階段：
根因調查 → 模式分析（找到能運作的類似程式碼，逐項比對差異）→ 假設與測試（一次只改一個地方）
→ 實作（先寫失敗測試）。附紅旗清單：說「大概是 X」但沒證據、連兩次修不好還在試、
同時改多個地方——都要立刻停。還有一條：**修了 3 次還沒好，就該回頭質疑架構本身。**

這幾乎就是我在 minethon 那幾支 debug log 裡自己摸索出來的做法，只是它寫成了檢查表。

### subagent-driven-development

整個 repo 裡最複雜、也最值得偷的一份。重點機制：

- **每個任務給乾淨 context**：subagent 只拿到任務簡報、前面任務的介面、全域限制，
  不繼承整段對話歷史（避免 context 污染）
- **審查即控制**：實作完必派 reviewer，不能用 implementer 的自我審查代替
- **Ledger（帳本）**：每個決策、每輪修正都寫進檔案。它明講這是為了**撐過 context 壓縮**——
  壓縮之後要相信 ledger + `git log`，不要相信記憶
- **Rulings over stalls**：plan 有歧義時控制端自己裁決、記進帳本、繼續跑，
  只有四種情況才停下來問人（破壞性操作、資安相關、worktree 外的副作用、plan 爛到每條路都是猜）
- **修正迴圈**：第 1–3 輪叫原本的 implementer 修，第 4–5 輪換更強的模型並告知前面失敗過；
  第 5 輪還沒解決就逐項裁決（reviewer 判斷錯／真的有問題但不致命／關鍵）
- **控制端不准自己動手修**——自己改就繞過了審查
- **明確指定模型**：機械性任務用最便宜的、整合任務用中間的、架構設計用最強的。
  它提醒不指定就會繼承 session 預設，通常是最貴的那個

### writing-skills

寫 skill 本身的方法論，對我之後做 slash command / skill 直接有用：

- frontmatter 的 `description` 要用第三人稱、以 "Use when..." 開頭，**只描述觸發條件與症狀，不要摘要流程**。
  它舉了個實例：description 寫「tasks 之間做 code review」害 agent 只做了一次審查，
  因為 agent 照著 description 的捷徑走，沒去讀 skill 內文（內文寫的是兩階段）
- 用 RED-GREEN-REFACTOR 開發 skill：先在**沒有 skill** 的情況下跑壓力情境、記錄它怎麼失敗，
  再寫最小的 skill 針對那些失敗，然後找新的鑽漏洞方式再補。
  「如果你沒看過 agent 在沒有這個 skill 時失敗，你就不知道這個 skill 教的是不是對的東西。」
- token 預算：開場流程 <150 字、常駐 skill <200 字、其他 <500 字
- 紀律型 skill 要明確堵死每個鑽漏洞的說法（附 rationalization table）

## 對我們合作的評估（第一輪，未實測）

**可能直接有用的：**

- `systematic-debugging` 的四階段跟紅旗清單——minethon 那幾支 debug log 就是這個形狀，
  拿現成檢查表比每次重新摸索划算
- `writing-skills`——剛做完 `/kb-push`，之後還想做更多 slash command，這份是現成的方法論，
  尤其「description 只寫觸發條件」跟「沒看過 agent 失敗就不知道 skill 對不對」兩條
- `brainstorming` 的三條路徑分類——「動手前先確認設計」這件事，在某個先把 schema 攤開討論
  才動手的專案上已經吃過甜頭，但目前是靠我每次口頭要求，不是靠制度
- `subagent-driven-development` 的 ledger 觀念——長 session 被壓縮之後靠檔案而不是靠記憶恢復，
  這對我那種一個專案跨很多 session 的做法特別對症

**跟現有做法重疊／要比較的：**

- 我已經有 [多模型協作筆記](../../learning/notes/multi-model-workflow.md)，
  用 Claude ↔ Codex 互相交叉驗證。superpowers 的 review gate 是**同一個問題的另一種解法**：
  它用「同模型但乾淨 context 的 reviewer + 明確的模型分級」，我用「不同廠商的模型互審」。
  這兩個不衝突，但要想清楚各自擋得住什麼——跨廠商擋的是同一模型的系統性盲點，
  乾淨 context 擋的是被前文帶偏。值得寫成筆記的一段比較
- 我原本就想研究「多 agent 編排」這個題目（Hermes 那一系），跟這個高度重疊，
  而且 repo 裡真的有 `.hermes-plugin/`。或許可以合併成同一條線來研究

**疑慮／可能不適合的：**

- 整套流程假設「有測試、有 git worktree、有 CI 心態」。我現在很多工作是知識庫寫作、
  repo 閱讀、環境排錯——這些跑不進 TDD 的框
- 「Mandatory workflows」對小任務（改一行、查一個 API）是明顯過重的，
  brainstorming 自己也說批准關卡不隨任務大小放寬。要看實際用起來煩不煩
- ~~session-start hook 會在每次開場就吃掉一段 context，成本要實測~~
  → **實測後撤回，見下方「安裝與 context 成本」。猜錯了。**
- 334 個 open issue（相對 27 萬星），更新很勤但也代表還在動，介面可能會變

## 實測：拿 writing-skills 的 RED 階段測 `/kb-push`（2026-08-15）

第一個真正跑過的實驗。測的不是 superpowers 本身好不好用，而是它的核心主張——
**「你沒看過 agent 在沒有這個 skill 時失敗，你就不知道這個 skill 教的是不是對的東西」**
——套在我自己寫的東西上，會不會真的翻出東西。

### 設計

受測對象：`~/.claude/commands/kb-push.md`（76 行，憑想像預防出來的，從沒驗證過）。

方法：派一個乾淨 context 的 subagent，給它真實情境（知識庫剛加了新專案、要推上 GitHub），
禁止它執行任何會改變狀態的指令，也禁止它讀 `kb-push.md`。要它產出完整執行計畫，
外加一份**來源自述**——逐項標明每條規則是讀到的、被塞進 context 的、還是自己猜的。

問的其實不是「沒有 kb-push 會怎樣」，而是更精確的：
**`kb-push` 比「`knowledge-base/CLAUDE.md` + 記憶檔」多給了什麼？**
因為那兩個來源本來就寫了一半以上的流程。

### 兩個插曲，都值得記

**第一次跑失敗了。** 我沒禁止它讀 `commands/` 目錄，它自己找到 `kb-push.md` 全文讀完，
整份計畫照抄。基線變成了「用了 skill 只是換個方式叫出來」。
——我設計了一個實驗、很有把握、然後它悄悄地沒在測我以為在測的東西。
這正好就是 RED 紀律要防的那種失敗，只是這次發生在我自己身上。

**第二次想把檔案暫時改名，被權限分類器擋下來**（`mv` 跟 `Rename-Item` 都不給碰 `~/.claude/`）。
改成「不動檔案、明確禁止讀取」，效果幾乎等價——要測的是內容，
它知道「有這麼一個指令存在」不會讓它學到裡面寫什麼。

### 結果

| 預測 | 結果 |
|------|------|
| 兩個 remote／subtree／commit 訊息慣例 → 會過 | ✅ 全過，來源自述直指 CLAUDE.md 與記憶檔 |
| 裝置名用環境變數不寫死 → 會過 | ✅ 過 |
| 外洩檢查 → 會漏 | ⚠️ 沒漏掉「該做這件事」，但**重新發明了整套內容** |
| 推 subtree 前的 tree hash 比對 → 會漏 | ⚠️ 沒用那個方法，換了個更簡單的，也對 |

**決定性的一項是外洩檢查。**

基線 agent 從記憶檔知道「該有一道外洩檢查」，但看不到內容，
於是自己組了一套關鍵字清單（真實個資、`C:\Users\`、`token`／`ghp_`／`sk-`、機構名稱…），
看起來相當完整。它的結論是「本次檢查通過，無需停」。

但第一次那個讀過 `kb-push.md` 的 agent，抓到了這份 README 裡有一句**指名引用了一個私人專案**——
依據是 `kb-push.md` 裡那條「`public/` 裡的文件如果引用了私人專案，必須是不指名的通用寫法」。

**同一個檔案、同一個問題：有 skill 的抓到，沒有的放行。**
而這條規則不在 CLAUDE.md、也不在記憶檔，只存在於那 76 行。
自己重新發明的清單想不到它，因為它防的不是關鍵字，是**引用關係**——
關鍵字掃描天生看不見這種東西。（那句話已依此修掉。）

反過來，tree hash 那三行看起來**不是獨有價值**：基線改用
`git diff --name-only HEAD~1 HEAD -- public` 一行解決，而且天然落在 commit 之後，
不會踩到「commit 前比對會得到誤導結論」那個坑。

> ⚠️ **這個結論後來被推翻了，見文末「後續修正」。** 基線那行只在「一次一個 commit」的前提下等價，
> 而那個前提對實際用法不成立。

### 附帶收穫：基線補了兩個 kb-push 沒有的東西

- **push 前先確認有沒有落後遠端**（用 `git ls-remote` 比對，落後就停下來問、不自己 pull／rebase）。
  `kb-push.md` 完全沒有這段，遠端跑在前面時只會在 push 那步直接炸掉
- **推完做唯讀驗證**，比對兩邊 hash 確認真的上去了

它自己在來源自述裡誠實標了這兩條是「純屬我自己加的，本地無任何依據」。但它們是對的。
（另外它為了守「不改狀態」，刻意避開 `git fetch`——因為會寫 remote-tracking ref——
改用 `git ls-remote`。這個分寸拿捏得挺細。）

### 對 GREEN 階段的結論

76 行大致可以這樣分類：

| 分類 | 內容 |
|------|------|
| **獨有價值，留下並強化** | 外洩檢查的具體內容，特別是「引用私人專案要不指名」與「不要自己決定應該還好」 |
| **與 CLAUDE.md／記憶重複，刪** | 兩個 remote 說明、subtree 指令、commit 訊息格式、裝置名用環境變數、`git add .`、不要 force |
| ~~**可被取代，簡化**~~ | ~~tree hash 三連 → 換成一行 `git diff --name-only`~~ ⚠️ 後來證明是錯的，見文末 |
| **缺，要補** | push 前的 ahead/behind 檢查 |

刪掉重複的那一大塊之後，應該塞得進 writing-skills 的 500 字預算。

### 對這套方法論本身的評價（第一次有實測依據）

**RED-first 是真的有用。** 我原本對 `kb-push` 的預測四項只對了兩項，
而且對「哪一部分才是它真正的價值」判斷錯了——我以為是流程完整度，
實際上流程完整度 CLAUDE.md 就給了，真正無可取代的是那條防引用關係的規則。
沒跑這個測試，重寫時我很可能把它當成細節刪掉。

**成本**：兩次 subagent 合計約 11.6 萬 token、20 次工具呼叫、7 分鐘。
換來一個具體且有佐證的改寫方向。對「值不值得」這個問題，這次的答案是值得——
但這是一個已經寫好、有明確懷疑對象的東西；對還沒寫的 skill 要不要每次都跑 RED，還不知道。

## 安裝與 context 成本（2026-08-15）

```
claude plugin install superpowers@claude-plugins-official
```

marketplace（`claude-plugins-official`）本來就已設定，一行裝完，scope 是 user，版本 6.3.0。
裝完要重開 Claude Code 才會載入。

`claude plugin details superpowers` 直接給了 context 成本估算：

```
Hooks (1)  SessionStart  (harness-only — no model context cost)

Projected token cost
  Always-on:   ~465 tok   added to every session
```

| 項目 | always-on | on-invoke |
|------|-----------|-----------|
| subagent-driven-development | ~30 | ~8.4k |
| writing-skills | ~30 | ~6.8k |
| brainstorming | ~50 | ~4k |
| systematic-debugging | ~30 | ~2.4k |
| test-driven-development | ~20 | ~2.3k |
| finishing-a-development-branch | ~30 | ~2k |
| using-git-worktrees | ~50 | ~1.7k |
| writing-plans | ~20 | ~1.8k |
| dispatching-parallel-agents | ~30 | ~1.5k |
| receiving-code-review | ~50 | ~1.5k |
| verification-before-completion | ~50 | ~870 |
| using-superpowers | ~40 | ~760 |
| requesting-code-review | ~30 | ~730 |
| executing-plans | ~30 | ~560 |

**我先前的疑慮是錯的。** 我原本擔心 session-start hook 每次開場就吃 context——
實際上那個 hook 標明是 `harness-only`，模型完全看不到，14 個 skill 加起來的常駐成本只有約 **465 token**。
以一個 200k 的 context window 來算是 0.2%，等於免費。

真正的成本在 **on-invoke**：skill 每次觸發才付。而且分佈很不平均——
`subagent-driven-development` 一次 8.4k、`writing-skills` 6.8k，
另一端 `executing-plans` 只要 560。

所以成本模型不是「裝了就變重」，而是「**用哪個才變重**」。
這反而讓「先裝著、只挑幾個用」變成完全合理的策略——
原本我以為要在「整套接受」跟「不裝」之間二選一。

順帶一提，`claude plugin details` 這個指令本身值得記住，
評估任何 plugin 該不該裝的時候都可以先用它看帳。

## GREEN 與 REFACTOR：真的用 `writing-skills` 重寫 `/kb-push`（2026-08-15）

裝好之後叫出真正的 `writing-skills`（on-invoke 約 6.8k token），照它重寫。

### 它當場否定了我原本的設計

真正的 skill 內容裡有一節 **Match the Form to the Failure**，是我先前只讀網頁摘要時沒看到的：

| Baseline failure | Right form | Wrong form |
|---|---|---|
| 在壓力下跳過／違反規則（知道卻不做） | 禁令 + rationalization 表 + 紅旗清單 | 軟性建議 |
| 有照做，但產出形狀不對 | 正面的 recipe／contract：直接規定產出**是什麼** | 禁令清單 |
| **從已經在產出的東西裡漏掉必要元素** | **結構性：在它要填的模板裡開一個 REQUIRED 欄位** | **模板附近的散文提醒** |
| 行為該視條件而定 | 綁在可觀察條件上的 conditional | 無條件規則 + 例外條款 |

我們的 RED 結果正落在第三列：基線 agent **有做**外洩檢查，只是自組的清單漏掉「引用關係」這個維度。
而我原本規劃的 GREEN 是「把那條規則留下並寫得更用力」——正是它標成 Wrong form 的那一欄。

它還有一條我也沒讀到的：**「能用 regex／驗證強制的就自動化，文件留給判斷題」**。
外洩檢查裡 grep `token`／`ghp_`／`C:\Users\` 那些是機械式的，真正的判斷題只有「引用關係」跟「放錯位置」，
所以字數該花在後者。

依這兩條重寫：**把外洩檢查改成一張必填的表**，一個檔案一列，三個具名欄位，
其中「指名引用私人專案」那欄明確要求**寫出你檢查了哪幾句在講其他專案、以及它們指不指名**。

### 我的字數預測又錯了

|  | 行 | 字元 |
|---|---|---|
| 舊 | 76 | 3453 |
| 新 | 48 | 2994 |

只縮 13%，不是我預期的「刪掉一大塊」。刪掉的 CLAUDE.md 重複內容，
幾乎被新增的結構化表格與欄位說明吃掉了。（`wc -w` 對中文無意義，中文沒空格，只能看字元數。）

### GREEN 驗證

原本那個真實的外洩案例已經被修掉了，所以建了 fixture：把知識庫複製到 scratchpad，
在副本裡把那句指名的話還原、並把這份 README 退回 RED 當時的版本（否則 agent 會讀到實驗說明而作弊）。
同一份檔案、同一個問題的 A/B 對照。

| | 結論 |
|---|---|
| RED（無指令） | 自組關鍵字清單 →「本次檢查通過，無需停」 |
| GREEN（新指令） | **抓到 L136–137，停在第 2 步，拒絕自行判斷或自行修改** |

那個必填欄位確實逼出了**逐句列舉**——它把 6 處提及其他專案的句子全部點名判定了一遍。
結構性欄位比散文提醒有效，這一點在這個案例上成立。

三個附帶收穫：

- 它也把「backlog 裡的 Hermes 研究」那句標成同性質問題——獨立確認了我先前憑判斷去軟化的決定
- **它發現一件我跟 RED agent 都沒看到的事**：`public/README.md` 講同一個私人專案時用的是不指名的
  「a real SQLite-backed service」。所以 repo 裡本來就有去識別化的先例，新檔是**破壞既有標準**，不只是單獨犯規
- 正確地把根 `README.md` 排除在表外（不在 `public/` 底下）

### REFACTOR：找到一個漏洞

它在「個資」欄遇到被研究的開源 repo 作者署名——一個真實姓名——自己判定
「屬公開作者署名，不構成外洩」然後填了「無」。判斷是對的，
但規則寫的是「任何一欄不是『無』就停下來」加「不要自己決定應該還好」，
它等於**安靜地把規則收窄了才通過**。規則寫太寬，agent 就會自己去談邊界。

修法不是加例外條款（skill 明說 exemption clause 不會 scope，
「不適用於 X」照樣會壓抑 X），而是**把欄位範圍正面定義窄**：
「檢查的是**使用者這一側**的東西……被引用的公開作品其作者署名屬於引用來源的一部分，不在本欄範圍」。

重測結果：

| 檢查點 | 結果 |
|---|---|
| 還抓得到原本那句嗎 | ✅ 抓到，一樣停在第 2 步 |
| 作者署名那個漏洞 | ✅ 補掉——這次寫「屬引用來源、**不在本欄範圍**」，是引用規則，不是現編理由 |
| 意外 | 那條 backlog 引用從敘述裡的附註升級成明確待決項；還正確判掉「token 預算」是關鍵字誤擊 |

新版已部署到 `~/.claude/commands/kb-push.md`。

### 誠實的方法論缺口

GREEN 和 REFACTOR 各只跑了 **n=1**。skill 自己寫「Single samples lie」，
建議 5+ reps 並要人工讀過每一個命中。沒跑到那個量。
所以「結構性欄位比散文提醒有效」目前是**有證據**，不是**已證實**。
決定不追 5 reps：這是給一個人用的指令，不是要發佈的 skill，n=1 對這個用途夠了。

### 對整套方法論的評價（跑完一輪完整循環後）

**RED-first 值得。** 兩次預測我都錯得有意義：
第一次錯在「哪一部分才是它真正的價值」（以為是流程完整度，其實流程完整度 CLAUDE.md 就給了），
第二次錯在「重寫後會大幅變短」（實際只縮 13%）。這兩個錯誤沒有測試都會變成錯誤的成品。

**Match the Form to the Failure 是意外的收穫。** 我本來以為 writing-skills 的價值在
「description 怎麼寫」，結果那條對手動叫用的 slash command 幾乎沒用；
真正改變設計的是失敗類型 → 表達形式的對應表。**先分類失敗、再選形式**這個順序可以直接套到別的地方。

**成本**：RED 兩次 + GREEN + REFACTOR 共四次 subagent，約 22.5 萬 token、約 12 分鐘，
加上 `writing-skills` 本身 6.8k。換到一個經過驗證的指令、和兩個可遷移的觀念。

### 後續修正：n=1 的基線真的會騙人

部署後才發現新版有個我自己引入的 bug。判斷要不要推公開 repo，我採用了基線 agent 的寫法：

```powershell
git diff --name-only HEAD~1 HEAD -- public
```

這行假設**這次推送只有一個 commit**。但實際用法是累積好幾個 commit 才推一次，
所以「最後一個 commit 有沒有動到 `public/`」根本不是正確的問題。

直接在 fixture 上實測（不用 subagent，這是機械問題不是行為問題）：
做兩個 commit，`public/` 的變動放在第一個、根 `README.md` 放在第二個。

| 方法 | 判定 | 對錯 |
|------|------|------|
| `git diff --name-only HEAD~1 HEAD -- public` | 空輸出 → 不用推 | ❌ 錯，`public/` 明明變了 |
| tree 比對（`public/main^{tree}` vs `HEAD:public`） | 兩個 hash 不同 → 要推 | ✅ 對 |

**所以原本那三行 tree hash 才是對的**，它問的是「公開 repo 的內容跟本地的 `public/` 一不一樣」，
跟中間隔了幾個 commit 完全無關。已改回 tree 比對，並把「這個比對要在 commit 之後跑」
寫成明確的條件（那是它唯一真正的坑），另加一行擋住未來想再簡化的念頭。

這件事本身就是「Single samples lie」的實例。基線 agent 只跑了一次、只面對一個 commit 的情境，
它的解法在那個情境下完全正確，我就照收了——但它從來沒被多 commit 的情境考驗過。
**n=1 的基線給的是「在我測的那個情境下對」，不是「對」。**

順帶一個分辨：git 是確定性的，同樣輸入必然同樣輸出，所以這次的實測 n=1 就夠。
LLM 行為是隨機的，n=1 只能算證據。同樣是「跑一次」，證據強度差很多。

**還沒測到的部分**：兩輪 fixture 驗證都因為踩到刻意留的外洩問題而停在第 2 步，
所以第 3 步（commit 與推送）的**行為**一次都沒被 agent 實際走過，只有指令本身被機械驗證過。

## 下一步

1. 先只裝來讀，不改工作流；在一個小題目（例如 gtnh-stargate-calc 的重構）上跑一次完整流程
2. 觀察三件事：context 開銷、強制關卡會不會擋路、產出品質有沒有真的變好
3. 把 `subagent-driven-development` 的 ledger 觀念單獨抽出來試——這個不用裝整包也能用
4. 讀 `tests/` 的評測 harness，看他怎麼「測試一個 skill 有沒有效」

## 相關資源

- 主 repo：https://github.com/obra/superpowers
- 社群可編輯的 skill 集：https://github.com/obra/superpowers-skills
- 實驗性 skill：https://github.com/obra/superpowers-lab
- 自家 marketplace：https://github.com/obra/superpowers-marketplace
- 針對 Claude Code 開發的分支：https://github.com/obra/superpowers-developing-for-claude-code
