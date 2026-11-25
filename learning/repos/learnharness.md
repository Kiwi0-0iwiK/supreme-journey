# LearnHarness — 用 AI agent 一步一步教你難懂東西的桌面／網頁學習 app

> Repo：[amosblomqvist/learnharness](https://github.com/amosblomqvist/learnharness) · 類型：學習 app（不是 coding agent 的外掛）
> 證據強度：🟡 讀了文件與部分原始碼（README、docs、prompt 片段、核心模組，皆經 WebFetch 小模型轉述；統計數字來自 GitHub API），沒安裝、沒執行 · 看過日期：2026-11-25
> 結論：觀望 — 設計想法（先量理解程度、再排學習路徑、每步一個檢查）值得學，但專案才 40 天、版本 0.7.0，我沒裝過，也沒有立刻要用它學的主題

## 這是什麼

名字裡有 harness，但**跟 superpowers／ECC 那類「給 coding agent 加東西」的 harness 不是同一種**。
它是一個完整的 app（Next.js 網頁＋Electron 桌面版），拿 AI agent 當**家教**：
先問你問題、量出你現在懂到哪（current understanding），再規劃一條到你目標（goal）的路，然後一步一步教，
每一步教完立刻出題檢查，沒懂就先修復再往下。這裡的「harness」指的是包住模型的那層教學流程與工具。

核心理念（取自 `docs/teaching-methodology.md`，作者自稱是 owner theory）：
**成功的標準是目標對學習者來說「顯然為真」，而不是學會背出來。** 理解被當成一張「命題與推理連結」的圖。

README 描述的四步迴圈：

| 步驟 | 做什麼 |
|---|---|
| Measure | 用答案、信心程度、你的思考過程，找出你在每個相依概念上卡在哪 |
| Plan | 建出從起點到目標的相依地圖，使用者看得到、也會隨進度調整 |
| Teach | 逐步進行：先預測、再解釋、再檢查；誤解先修再往上蓋 |
| Practice | 另開 session，用變化過的題目練習，提示會調整 |

| 項目 | 內容 |
|---|---|
| 作者／組織 | amosblomqvist（個人帳號；README 稱自己是 owner-led 專案） |
| 建立 / 最後 push | 2026-10-16 / 2026-11-21（GitHub API，2026-11-25） |
| 星數 / fork | 12,204 / 1,554（GitHub API，2026-11-25） |
| Open issue（含 PR） | 642（API 數字，PR 一起算） |
| 授權 | AGPL-3.0（API 與 package.json 一致） |
| 語言 / 技術棧 | TypeScript 9.7MB、JavaScript 1.5MB、Python 0.1MB（GitHub API）；Next.js 16 + React 19 + Electron |
| 版本 | 0.7.0（package.json，WebFetch 摘要） |
| 網站 | learnharness.ai |

## 結構

頂層資料夾：`app/`（頁面與 HTTP 路由）、`components/`（UI）、`src/`（`server/`、`agent/`、`core/`、`store/`）、
`electron/`、`plugins/`、`examples/plugins/`、`skills/`、`docs/`、`tests/`。
`AGENTS.md` 是給開發用 agent 的規則，沒有 CLAUDE.md。

**三個 agent，接力教學**（`docs/architecture.md`）：

| Agent | 工具 | 任務 |
|---|---|---|
| Prober（探測） | `probe`／`recall`、`ask_user_question`、`probe_done` | 問出你現在的理解；`probe_done` 成功後交棒 |
| Teacher（教學） | `quiz`／`explain`、`ask_user_question`、`plan_init`、`show_image` | 排計畫並逐步教，輸出會標註對應計畫節點 |
| Practitioner（練習） | `problem`、`conclude` | 出練習題，同時只允許一題進行中 |

幾個值得記的設計：

- **每一「回合」重建一個新 agent**：從存好的對話紀錄還原，一回合可以有多次模型呼叫與工具執行；system prompt 不存檔。
- **問題工具在伺服器端先回傳一個「終止用的佔位結果」**，等你真的作答，答案才當 tool result 回來。選擇題的洗牌與批改在瀏覽器做。
- **學習計畫是一張驗證過的 Mermaid DAG**，可用 `plan_init` 重排。方法論文件強調計畫是「地圖不是路」，節點不該變成課程章節。
- **背景工作**（網路研究、PDF、demo、視覺化）寫成 job 記錄，由 worker 跑，結果再「steer」回還活著的 agent 或喚醒閒置的 session。
- **知識圖譜存命題與推理鏈，不存「精熟度分數」**。建構是事後做的：extractor 提出命題 → identity auditor 判斷哪些是同一個 → 確定性的 merger 合併。
  分群靠「來源溯源」，不靠 embedding 或 Louvain。
- **全部是 JSON／JSONL 檔，沒有資料庫**：`chats/*.json`、`jobs/*.json`、`graph/{nodes,chains,sessions,coverage}.jsonl`、`settings.json`；API 金鑰另放 `auth.json`。
  資料根目錄由 `LH_DATA_DIR` 決定（預設 `data/`）。
- **Agent runtime 不是 Vercel AI SDK**，是 `@earendil-works/pi-agent-core`／`pi-ai`（版本釘在 1.5.2）；MCP SDK 用在 Claude Code 橋接。

**外掛系統**（`docs/plugin-architecture.md`）：外掛是「受信任的本機程式碼」，同時擴充後端與前端。官方內建四個：
Flashcards、Coding Questions、Drawing Pad、Rich Code Blocks。可新增工具、題型、渲染器。預設停用，改了要重啟，沒有市集、沒有沙箱。

**`skills/learnharness/SKILL.md`**：一個**給外部 agent 用的唯讀 skill**，只用 Python 標準庫，能列出你的學習 session、讀對話、查知識圖譜。
用途是讓別的 agent（例如 Claude Code）分析你學了什麼。它自己規定不准寫入資料、不准讀 `auth.json`。

## 運作細節（讀了部分原始碼之後）

> 這一節來自 `src/agent/`、`src/server/`、`src/store/`、`src/core/` 的原始碼，**經 WebFetch 小模型讀取後轉述**，
> 沒有自己逐行讀，也沒執行過。標「文件說」的是只看到註解或文件、沒在程式裡對到的。

### 1. 其實只有一個 agent，每次請求換一套設定

「三個 agent」是比喻。**沒有三個常駐的東西**：每次瀏覽器 POST `/api/chat`，伺服器都重新建一個 Pi `Agent`，
對話紀錄的訊息陣列就是它的全部狀態。選哪一套：

```
record.kind === "practice"        → practice agent
否則 hasProbeDone(訊息)=true       → teacher
否則                               → prober
```

所以「交棒」其實是：prober 呼叫 `probe_done`，**訊息裡出現了這個成功的 tool call，下一次請求就自動變成 teacher**。
`probe_done` 還會檢查「沒有未回答的問題」「還沒結束過」才放行，通過後送一個 steer 讓 teacher 的第一回合自動開始。

system prompt 是把一堆**數字開頭的 .md 片段**用 `---` 接起來（`README.md` 不會進去），
片段在 `src/agent/prompts/{prober,teacher,practice,shared}/`。使用者可以在設定裡覆寫。

| 角色 | 組成 |
|---|---|
| prober | `system-prompt.md` ＋ `prober/10-probe-doctrine.md` ＋ shared |
| teacher | `system-prompt.md` ＋ `teacher/`（05 方法、10 規劃、20 教學、28 預測、30 出題原則、40 jobs、50 demo、55 圖片）＋ shared |
| practice | `practice/00-base.md`＋`10-doctrine.md`（約 14.8 KB）＋ shared 的一部分，**沒有教學底稿** |

（片段實際的拼接順序，三處文件寫法互相矛盾，真正的順序在 `prompt-segments.ts`，沒讀到。）

### 2. Prober 怎麼探你的程度

規則來自 `10-probe-doctrine.md`（約 4 KB，是 prober 唯一的片段）：

- 目標是**建立你的理解模型**，不是考你記得什麼；先用 `ask_user_question` 弄清楚你要學什麼。
- 先看知識圖譜（`list_sessions`／`list_propositions`），**已經扎實的區塊不重問**。
- 出短而具體的題目，挑「不同心智模型會給出不同預測」的題；一題可以同時測好幾條線。
- **像二分搜尋**：從高處開始，答錯往下縮；答得有道理就大跳一步。
- **沒有題數上限**，證據夠 teacher 排計畫就收，呼叫 `probe_done` 一次、不能留未答的題。
- 選擇題會自動多一個「我不知道」選項。

### 3. Teacher 的教學迴圈

- 兩個原則（`05-method.md`）：從**不可再推的事實**開始；每一步都問「我怎麼可能自己發現這個」，讓事實像被發現的而不是被宣布的。
- 先 `plan_init` 送一段 Mermaid（`graph TD`）當地圖；**用文字＋地圖呈現給你，等你確認才開始教**；
  你的理解跟地圖不符時用 `plan_init` 整張重寫。
- **每個 `quiz`／`explain` 工具呼叫都必須帶 `nodeId`（對應計畫節點）和 `type`**；`nodeId` 對不上現有計畫會被拒絕並列出合法 id。
  UI 上的「目前在哪個節點」就是從這些呼叫反推的，不是另外存的進度。
- 一步一個事實，每步選蘇格拉底式（你推得出來時的預設）或講述式。順序是 **predict → 教這一步 → check → 答錯先修復**：
  - `predict`：教之前出，**展開、擋住後面的內容**，教學內容會回頭解答它
  - `check`：教完出，**收在「Check your understanding」後面**
- 出題原則（`30-question-principles.md`）：要能從 session 內容回答、不能只是背誦、偏好應用題；
  選擇題的錯誤選項要各對應一種錯誤心智模型；**一次答案是訊號不是判決**。
- 沒有固定題數：每步都有 check，predict 可選。
- 名稱撞車：`explain` 既是工具名稱（自由回答版的 quiz，設定 `tools.explain` 開了才取代 quiz），也是 prompt 裡「講解」的動詞。
  所以 README 的「predict → explain → check」，prompt 實際寫的是 predict → teach → check。

### 4. Practice：另一套理論

- 工具只有 `problem`、`conclude`；**同時只能有一題**，由 `PracticeGate.problemActive` 擋。
- `conclude` 要填：`outcome`（solved／solvedWithHints／movedOn／surrendered，dismissed 是系統合成的）、`verdict`、
  提示階梯 `rung`（R0 到 R5）、`missClass`（cue／discrimination／execution／careless／structural）、`retest`。
- 理論取向（`10-doctrine.md`）：提取練習、三種模式（recall、discrimination、composition）、
  提示一次升一階、答案是看你的**操作**而不是打分、整場節奏「暖身 → 交錯 → 以重測收尾」。
- 沒有 predict／check 迴圈；是「出題 → 你的思考紀錄 → 判定 → conclude」。

### 5. 一則使用者訊息的一生

```
瀏覽器 POST /api/chat {chatId, input}
  → parseChatInput 驗證（text／answer／continue／retry／steer 等事件）
  → 閘門：有沒有設模型、有沒有金鑰、要不要先壓縮歷史（ensureCompacted，可能要等）
  → beginTurn：同一個 chat 已有回合在跑 → 409
  → 先寫入磁碟（saveMessages，write-ahead），再開始回合
  → 用訊息陣列重建 Agent，runPiTurn 在背景跑
  → POST 立刻回 {ok:true} 就關閉
瀏覽器另外接一條 SSE 串流看事件（agent_start、message_update…）
回合結束 → persistTurn、記用量、必要時觸發圖譜抽取、結算 steer、背景壓縮
```

重點：**POST 本身不串流**，串流是另一個連線；關掉畫面**不會中止回合**，只是少了一個觀眾。
`message_update` 事件最多每 100 ms 合併送一次。

兩個「投影」：`toLlmMessages` 是唯一給模型看的出口（去掉內部欄位、把標記轉成 user 訊息、套用壓縮截斷、
補上被中斷的 tool result）；**`projectView` 在我讀到的檔案裡找不到**，UI 端的投影我沒確認，這個名字是文件說的。

### 6. 出題與作答：tool call 是怎麼被「暫停」的

這是設計裡最巧的一段：

1. 模型呼叫 `quiz`，伺服器回一個**只存在記憶體的 placeholder**，並讓這個回合**終止**（`terminate`＋`finishTurn`）。
   所以**題目一定要放在同一則訊息的文字之後**。
2. 紀錄裡這個 tool call **沒有 result**，`hasUnresolvedQuestion` 變 true；此時背景喚醒都不會跑。
3. 你作答，POST `{type:"answer", toolCallId, answer}`；伺服器核對 `toolCallId` 跟懸而未決的那題一致，
   才補上一則 `ToolResultMessage`。**模型看到的內容是 `compactAnswerForModel(answer)`，完整評分資料另存 `details`。**
4. 這時紀錄是完整的（呼叫＋結果），再重建 Agent 跑下一回合。
5. 同時有多題未答：先存答案，**最後一題答完才開一個回合**。
6. 你按「略過」（dismiss）：產生 `dismissed:true` 的結果，**不開回合**。

換句話說，LLM 的 tool call 協定被拿來當「等人類回答」的機制，答案就是遲到的 tool result。

### 7. 背景工作（research／pdf／demo／visual）

- 工具先建 `jobs/job_xxx.json`（狀態 running），用 `toolCallId` 去重，**立刻回「Dispatched」給模型**，然後背景跑。
- `runner.ts` 依種類選引擎；research 會在 `os.tmpdir()` 開 `lh-research-` 暫存資料夾，跑完刪。
- 完成後 `finishJob` 把 `delivery` 設成 pending，再把結果包成 steer 送回去：
  - **你的回合還在跑**：`agent.steer()` 直接插進同一個 run 的回合邊界
  - **沒在跑**：等 750 ms 閒置，再用「steers」輸入開一個新回合；撞到 409 就退避重試（0.5、1、2、5 秒，**之後固定 5 秒、沒有次數上限**）
- 崩潰復原：`recoverStaleJobs()` 由 `/api/jobs` 的 GET 觸發（30 秒節流），把 pending 的送達補上、把沒結果的 running job 重跑。
  **沒人輪詢的話就不會復原。**

### 8. 知識圖譜怎麼長出來

- **誰觸發**：回合結束時，若抽取功能開著且不是 practice，就 `triggerExtraction`；同時只能跑一個（single-flight）。
- **只看 teacher 的文字**：extractor 看到的是 `TEACHER [messageId] 文字`，**你的回答、思考、quiz 區塊都排除**。
  所以圖譜記的是「教過什麼」，不是「你答對了什麼」。
- **哪些訊息要處理**：對每則 teacher 訊息算 `sha256(JSON.stringify([role, viewLines]))`，不在 `coverage.jsonl` 的就是未處理；
  把連續未處理的訊息在 **4096 token 預算內**分批（一則訊息不會被切開）。改了一則訊息只會重開那一則。
- **extractor**（一個 LLM）：目標是挖出核心概念與推導；一次 `submit_findings` 交出 `{propositions, chains}`。
  規則：命題要是**真的、關於世界的、獨立可讀的**（不能寫「老師說」）；chain 是「前提**合起來**蘊含結論」，敘事順序不算；
  已有的命題用 id 引用不重述。送出時有 schema 與錨點檢查，不過就叫模型重來。
- **auditor**（另一個 LLM）：**看不到原文**，只看 findings 加每條 5 個排名的候選舊節點（詞重疊排序），輸出 `{id, linkTo}`。
  判準是「同一個知識點的不同說法」，同主題不算。**身分判斷完全靠 LLM，沒有確定性的名稱或語句比對。**
- **merger**（確定性程式）：`linkTo` 指向舊節點 → 在 `nodes.jsonl` 追加同 id 一行（別名與來源合併）；否則新建 `n_` 加 12 位十六進位 id。
  chain 去重、去掉「前提＝結論」、再跑 `simplifyChains`（前提是舊 chain 的子集就是多餘；被祖先覆蓋的前提也多餘）。
- **查詢**：圖是讀取時把檔案合併出來的；**邊不存**，由 chain 推導（單前提＝一條箭頭，多前提＝一個「蘊含節點」）。
  分群用「節點誕生的 session」，沒有 embedding。prober 可以用 `list_sessions`／`list_propositions` 查圖，**但只看得到名稱和日期，看不到命題內容**。
- 「筆記匯入」是另一條路：沒有指紋，**每次都整份重跑**。

資料模型（`contracts/graph.ts`）：節點 `{id, name, statement, aliases, createdAt, provenance[]}`，
`statement` 才是身分錨點；chain `{id, premises[], conclusion, createdAt, provenance[]}`；
`provenance` 是 `{chatId, messageId}` 的清單。

### 9. 計畫的驗證

兩層。`parseMermaidPlan`（手寫的 Mermaid 子集解析器）一次收集所有錯誤並附行號：
- 表頭要 `graph|flowchart` 加方向；id 只能是小寫英數用 `-`／`_` 連接（slug）
- 認 `id`、`id[標題]`、`id("標題")`，箭頭 `-->`／`==>`／`-.->`，可串成 `a --> b --> c`
- 自我迴圈、subgraph、style、class 都拒絕
然後 `createTree` 檢查重複 id、未知端點、重複邊、**環**。

計畫有沒有 5–15 個節點：工具描述寫 5–15，prompt 寫「沒有大小上限」，**程式只要求至少 1 個**。
舊節點的 id 在重寫後要不要保留，**只是 prompt 規則，程式不檢查**。

### 10. 儲存：更正我前面講的

- 檔案是**原子寫入**：寫到 `<檔名>.tmp-<uuid>`、`fsync`、再 `rename` 蓋過去，Windows 上遇到檔案被占用還會重試約 100 ms。
  所以一般中斷不會留下半截的檔。**我先前說「整檔覆寫，寫到一半被中斷單一檔案也可能半截」不準確。**
- 例外：chat 的寫入設了 `allowInPlaceFallback: true`——rename 一直失敗時**改成原地寫入，這時不是原子的**，
  中斷會把檔案截斷。`getChat` 遇到解析失敗就回 `null`，那個 chat 在側邊欄就**悄悄消失**，沒有自動復原。
- **沒有檔案鎖，儲存層也沒有排隊**。同行程內靠的是「讀-改-寫的區段都是同步的、中間沒有 `await`」，
  所以 Node 單執行緒下不會交錯。**跨行程才會互相覆蓋**（最後寫入者勝）。我先前說「同一行程內有排隊機制」不準確，實際是靠同步。
- 記憶體裡有不少狀態掛在 `globalThis`（回合紀錄、steer 登錄、live agent、回合存活狀態），**伺服器重啟就沒了**。
- 效能：`listChats` 每次把所有 chat 檔完整解析；圖片以 base64 內嵌在 chat JSON，檔案會變很大。

### 11. 讀到的奇怪處（作者自己的程式碼註解互相矛盾）

- 一些檔頭註解還在講已被移除的「follows／supports 邊」「understanding 層」「context injection」，跟現在程式行為不符。
- 「append-only」不全然：`simplifyChains` 會重寫 `chains.jsonl`。
- practice 的「`conclude` 後暫停」只是 prompt 要求，程式只會把 `problemActive` 設回 false，**同一回合照樣能再出下一題**；
  檔頭註解甚至寫「同一個回覆可以揭曉＋出下一題」，跟 doctrine 相反。
- 知識圖譜的 extractor 是「完全信任」的：只檢查格式與錨點，**命題真不真沒人查**。

## 怎麼用

兩種：

1. **直接用**：到 releases 下載。macOS 簽章過的 DMG、Windows x64 安裝檔（**未簽章**，會有 SmartScreen 警告）、Linux AppImage／deb，都有應用內更新。
2. **從原始碼跑**（README）：

```bash
npm ci
npm run plugins:setup
npm run dev        # http://localhost:3000
npm test           # 用 fixture 與假的 provider，不打真的模型
```

**模型來源**有四種：各家 API 金鑰、桌面版支援的訂閱連線、**你本機裝的 Claude Code CLI**、自訂 OpenAI 相容端點（含本機模型伺服器）。
網路研究與語音聽寫要另外的金鑰（Tavily／Brave／Exa／Firecrawl／Ollama search）。

**用 Claude Code CLI 當模型提供者**（`docs/claude-code.md`）有幾個細節：預設關閉；最低版本 2.1.259；
每次呼叫是不經 shell 的子行程、在空的暫存資料夾，CLI 自己的工具／hook／斜線指令／權限提示都關掉，
LearnHarness 自己的工具透過一個有 token 保護的 loopback MCP 橋接給它。
費用顯示成「CLI billing」，不換算美元。

資料與隱私：對話、圖譜、設定、金鑰都以**明文檔案存本機**；模型、網路研究、聽寫會連外部服務。system prompt 看得到也能改。
定價立場：無訂閱、無加價，未來若收費是為了託管金鑰之類的便利。

## 跟我的關係

**以下都是推測，我沒裝過。**

- **名字混淆要記一筆**：我之前的 [agent harness 研究](../../projects/agent-harness-study/README.md)看的是「補強 coding agent」的工具；
  這個是**學習產品**，補的不是 agent 缺的能力，而是「學習者缺的家教流程」。放進 [Repo 閱讀筆記總覽](README.md)
  那個「補 agent 缺的才值得裝」的判準並不適用，要換成「它教得比我自己看書／問 Claude 好嗎」。
- **最有參考價值的是方法論，不是程式**：「先量起點與目標」「一個推理步驟配一個檢查」「失敗先修復」「計畫是地圖不是路」，
  我自己用 Claude 學東西（例如 GTNH 配方鏈、不熟的領域規則）時可以手動套用，不需要裝這個 app。
- **知識圖譜存「命題＋推理鏈」而非精熟度**，跟我 knowledge-base 的做法（手寫筆記、標證據強度）理念相近：都在避免「假裝知道」。
  但它是 AI 事後抽取，我的筆記是人驗過才寫，**可信度不同**，不能互相取代。
- **SKILL.md 那個唯讀設計**是個漂亮的先例：把「資料格式文件＋唯讀腳本」打包成 skill，讓別的 agent 能分析資料又不會寫壞它。
  之後自己做類似東西（把某個專案的資料包成讓 agent 唯讀查詢的 skill）可以參考。**含真實個資的資料不要這樣餵給雲端模型。**
- **適不適合我**：我是 learn-by-doing 型，這個 app 的流程偏「被問、答、被檢查」，（推測）對純理論主題比較合適，
  對「邊做邊學」的專案（我大部分的學習）幫助可能有限。

## 證據與限制

- **實際做過的**：用 GitHub API 取得統計與語言比例；請 WebFetch 讀 README、`AGENTS.md`、`docs/` 目錄清單與下列 6 份檔案：
  `architecture.md`、`teaching-methodology.md`、`plugin-architecture.md`、`claude-code.md`、`skills/learnharness/SKILL.md`、`package.json`。
- **沒做、只是讀到的**：
  - **沒安裝、沒跑過**，教學品質完全不知道。`npm test` 用假 provider，作者自己也寫「不證明教學品質」
  - **原始碼只讀了一部分，而且是經 WebFetch 小模型轉述**：讀了 `teacher-agent.ts`、`tools.ts`、`chat-handler.ts`、`jobs.ts`、`store/atomic-write.ts`、
    `store/chats.ts`、`core/graph.ts`、`core/coverage.ts`、`mermaid-plan.ts`，以及 prober／teacher／practice 的部分 prompt 片段；
    `extraction.ts` 與 `native-messages.ts` 都只有前半是原文，後半是摘要
  - **「運作細節」那節沒讀到的**：`prompt-segments.ts`（prompt 拼接順序）、`turn-service.ts`、`turn-liveness.ts`、
    `compaction.ts`（歷史壓縮）、`plan-tree.ts` 與 `plan_init` 的實作、`probeDoneInputSchema`、`ask_user_question` 的工具定義檔
    （找不到，只在註解裡看到名稱）、SSE 串流的 GET 路由、`projectView`（找不到）、`teacher/40-jobs.md`／`50-demos.md`／`55-images.md`、
    `shared/` 底下全部、`claude-code/` 資料夾、practice 怎麼挑命題（`practice-problems.ts`）
  - `docs/` 其他檔案沒讀（`development.md`、`plugin-authoring.md`、`custom-providers.md`、flashcards 兩份、`references/data-format.md` 等）；`src/agent/prompts/` 的實際 prompt 也沒看
  - 教學理論**沒有任何實證依據**（文件自己承認是 owner theory、判準「顯然為真」是主觀的）
- **文件自己承認的限制**（值得原樣記下）：
  - 儲存是同步檔案寫入（暫存檔＋rename，大多是原子的），但**多檔操作沒有交易、沒有跨行程鎖**；要求「每個資料／金鑰設定檔只跑一個 server」
    （細節見「運作細節」第 10 節，包含我前面誤述的兩處更正）
  - 外掛與 Claude Code 路徑是「受信任」不是沙箱；檔案工具預設可讀伺服器使用者的家目錄，敏感路徑防護只看路徑不看內容
  - Claude Code 提供者的「指令隔離」在最低版本上**作者自己說沒做過執行期驗證**，managed settings 可能蓋過
  - 不保證「只用訂閱額度」，也不是 OS 沙箱或 provider 政策認證
- **資料取得方式的可信度**：所有文件內容都是 WebFetch 小模型摘要，可能有遺漏與轉述誤差；GitHub API 數字可信度較高。
  README 的「Languages」「最後 commit」區塊 WebFetch 沒抓到，語言比例改以 API 為準。
- **一個值得懷疑的點（觀察，不是結論）**：2026-10-16 建立，40 天內 1,319 個 commit（WebFetch 讀到的頁面數字）、1.2 萬星、
  近 650 個 open issue／PR。速度很快，可能是作者大量用 AI 開發加上真的爆紅；我沒查星數來源，也沒看 commit 品質。
  `AGENTS.md` 寫「所有設計決定屬於人類，有歧義就一次問一個問題、先拿到核准的計畫再實作」，
  至少說明作者有意識地約束自己的開發 agent。
- **授權注意**：AGPL-3.0，如果要改了拿去提供服務（含網路服務）就要開源，自己用沒影響。

## 下一步

- [ ] 如果想試：先看 `docs/getting-started.md` 與 `docs/custom-providers.md`，用**自己的 API 金鑰或本機模型**，別用 Claude Code CLI 模式（它的指令隔離沒驗證過）
- [ ] 挑一個**不含個資**、我真的想學的理論型主題（例如某個演算法或統計概念）跑一輪，看 Prober 問出來的起點準不準
- [ ] 想了解教學流程就讀 `src/agent/prompts/` 與 `teaching-methodology.md`，不一定要裝
- [ ] 若要裝：先讀 `electron/` 的更新與 guard、`auth.json` 的存放位置，確認金鑰不會被別的程式讀到（資料全是明文）
- [ ] 過一兩個月再回頭看星數與 issue 是否穩定，再決定值不值得投入

## 相關

- [Repo 閱讀筆記總覽](README.md)
- [Graphify](graphify.md) — 另一個「把東西變知識圖譜」的專案，但是給程式碼庫、不用 LLM 做 AST；這裡的圖譜是對「人的理解」建模
- [agent harness 研究](../../projects/agent-harness-study/README.md) — 名字相近但性質不同，見上面「跟我的關係」第一點
