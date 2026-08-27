# ECC 研究 — 「agent harness 效能最佳化系統」

> 隸屬：[Agent harness 框架研究](README.md) · 狀態：🟡 初步調查 · 開始日期：2026-08-27

> ⚠️ **證據強度：只讀過文件，沒安裝、沒實測。**
> 這份的依據是 GitHub API 的 metadata、`README.md`、`the-shortform-guide.md`，
> 加上從 286 個 skill 裡抽讀的 5 份 `SKILL.md` 全文。
> 對照組 [superpowers.md](superpowers.md) 背後是四輪 subagent 實驗、A/B fixture 對照、
> 以及 `claude plugin details` 量到的真實 context 數字。
> **兩份文件的結論不是同一個強度。** 下面凡是推算而非量測的地方都標了 ⚠️。

## 目標

搞清楚 [affaan-m/ECC](https://github.com/affaan-m/ECC) 跟 superpowers 是不是同一類東西，
以及在已經有 superpowers 當主幹的前提下，它有沒有值得單獨拿走的部分。

## 進度

- [x] repo metadata、README、shortform guide、目錄樹掃描
- [x] 抽讀 5 份 SKILL.md 全文，對照 superpowers 實測過的四個 skill
- [x] 量 always-on 成本（2026-08-27，用校準法直接算，不必安裝——**原本的推算低估了一倍**）
- [x] 掃過 `tdd-workflow` / `golang-testing` / `healthcare-*` 的章節結構
- [ ] 用 `claude plugin details ecc@ecc` 做一次直接量測，驗證校準法
- [ ] 把 `tdd-workflow` 那份完整讀完，跟 superpowers 的 TDD skill 逐條對照
- [ ] 決定要不要在某個專案上實測任何一份

## 這個 repo 是什麼

作者 affaan-m。自稱 "The agent harness performance optimization system"。
標語是 **"Optimize the context window. Persist everything else."**，
主流程寫成 `plan → test → implement → review → verify → remember → improve`。

| | ECC | superpowers（對照） |
|---|---|---|
| 建立 | 2026-01-18 | 2025-10-09 |
| 星數 / fork | 243,653 / 36,843 | 278,464 / 24,928 |
| Repo 大小 | ~47.8 MB | ~4.4 MB |
| 授權 | MIT | MIT |
| Skills | **286** | 14 |
| Agents | 68 | — |
| Legacy 指令 shim | 94 | — |
| 開放 issue | 182 | ~334 |

（數字為 2026-08-27 由 GitHub API 取得。）

286 份 `SKILL.md` 內文合計 **2.58 MB**，平均每份 9.0 KB，最大 30.6 KB。

### 目錄結構

```
ECC/
├── skills/                ← 286 個
├── agents/                ← 68 個
├── commands/              ← 94 個相容 shim
├── rules/                 ← 各語言 / 專案規範
├── hooks/                 ← runtime 自動化
├── mcp-configs/  scaffolds/  workflows/  research/  ecc2/
└── .{claude,codex,cursor,gemini,zed,opencode,kimi,pi,trae,...}/
```

安裝（Claude Code）：

```
/plugin marketplace add https://github.com/affaan-m/ECC
/plugin install ecc@ecc
```

另有 `install.sh --profile [minimal|core|full] --target [harness]` 供其他 harness 使用。

## 對照：superpowers 實測過的四個 skill，ECC 有沒有

這是判斷「是不是同類東西」最直接的切法——拿[已經跑過實驗的那幾個](superpowers.md)去對。

| superpowers | ECC 的對應 | 差別 |
|---|---|---|
| `writing-skills`（實測評價最高的一個） | ❌ **沒有** | 最接近的 `skill-comply` 是**事後合規檢測**——自動生成三種嚴格度的情境、跑 agent、量它有沒有照做、回報 compliance rate。那是 QA，不是寫作方法論。ECC 沒有「Match the Form to the Failure」「description 只寫觸發條件」「沒看過 agent 失敗就不知道教對沒」這一層 |
| `brainstorming`（人類批准關卡） | ⚠️ `blueprint`，**哲學相反** | frontmatter 寫明五階段 Research → Design → Draft → Review → Register，**沒有人類檢查點**；adversarial review 由「最強模型的 sub-agent」執行。它有排除條款（單一 PR、少於 3 次工具呼叫、使用者說 "just do it" 不觸發），但那是規模過濾，不是 spike/bounded/architectural 那種路徑分類 |
| `test-driven-development` | ✅ `tdd-workflow`，**客觀上更硬** | 21.5 KB（superpowers 那份 on-invoke 才 2.3k）。RED 必須是**真的編譯或執行過**才算數（「只寫了測試但沒編譯執行不算 RED」）、GREEN 要重跑同一個 target 確認、**80% coverage 量化門檻**、RED/GREEN/refactor 各一個 commit 且要驗證能從 `HEAD` reach 得到（防之後 squash 把證據弄丟）、最後產出一份給 reviewer 看的 TDD Evidence Report |
| `subagent-driven-development` 的 ledger | ⚠️ 名字像，東西不是 | `recursive-decision-ledger`（2.5 KB）的觸發條件是「重複 rollout、標記決策過程、高維搜尋、隨機最佳化、局部最佳解探索、集成比較」——是**決策品質**的帳本，不是實作編排的帳本。它有一句不錯的：「recursive confidence is not approval」。實作編排的對應其實是 `team-agent-orchestration` / `orch-pipeline` / `council-multi-model` |
| `systematic-debugging` | ❌ 沒有直接對應 | 有 `/build-fix` 指令與 `orch-fix-defect`，但沒有那套「NO FIXES WITHOUT ROOT CAUSE」四階段 + 紅旗清單 |

**一句話總結**：方法論的**執行層**（TDD、verification）ECC 有，而且做得比較細；
方法論的**元層**（怎麼寫 skill、怎麼在動手前逼出設計）ECC 沒有，或換成了自動化。

### 品質不齊，要一份一份看

ECC 的 skill frontmatter 有 `metadata.origin` 欄位，值有 `ECC` 也有 `community`。
`blueprint` 是 `community`，`tdd-workflow` 和 `recursive-decision-ledger` 是 `ECC`。
286 份不是同一套標準寫出來的，**不能整包當成同一個品質**。

## 它真正多出來的：領域 skill

286 份裡絕大多數不是方法論，是**具體領域的 pattern 庫**。這是 superpowers 完全沒有的一層——
superpowers 只管「怎麼做事」，不管「這個領域長什麼樣」。

其中跟手上專案對得上的幾群：

| 群 | Skills |
|---|---|
| 醫療資訊系統 | `healthcare-emr-patterns`、`healthcare-cdss-patterns`、`healthcare-phi-compliance`、`hipaa-compliance`、`healthcare-eval-harness` |
| Go / 資料庫 | `golang-patterns`、`golang-testing`、`postgres-patterns`、`database-migrations`、`contract-first`、`api-design` |
| 自架 sandbox / 家用網路 | `homelab-network-setup`、`homelab-pihole-dns`、`homelab-vlan-segmentation`、`homelab-wireguard-vpn`、`homelab-network-readiness` |
| Context 管理 | `context-budget`、`token-budget-advisor`、`strategic-compact` |
| 多模型 | `council`、`council-multi-model` |

最後一項跟[多模型協作筆記](../../learning/notes/multi-model-workflow.md)是同一個題目，
之後要繼續寫那條線的話可以拿它當對照組。

## Context 成本（2026-08-27 量測）

**不必安裝就能量。** always-on 成本的內容就是每個 skill 的 `name` + `description`，
兩邊都是本機可讀的檔案，所以拿 superpowers 已知的實測值當校準基準即可：

| 校準 | 值 |
|---|---|
| superpowers 14 個 skill 的 name+description | 2,154 字元 |
| 對應的實測 always-on（`claude plugin details`） | 465 token |
| → 校準比率 | **4.63 chars/token** |

把同一把尺套到 ECC：

| | 項目數 | frontmatter 字元 | ≈ always-on token |
|---|---|---|---|
| `skills/` | 286 | 85,464 | **18,450** |
| `agents/` | 68 | 15,188 | 3,279 |
| `commands/` | 94 | 10,787 | 2,329 |
| 合計 | 448 | 111,439 | **24,057** |

**光 skills 就 18.5k**，200k window 的 9.2%；superpowers 是 0.23%。**差約 40 倍。**

### 原本的推算錯了，而且低估一倍

第一版寫的是「9–12k、約 20 倍」，錯在假設每個 skill 的描述長度跟 superpowers 差不多
（33 tok/skill）。實際上 **ECC 的描述平均 299 字元，是 superpowers（154）的兩倍**——
因為很多份把 `TRIGGER when: … DO NOT TRIGGER when: …` 整段寫進 description 裡。
所以是 286 × 65 tok，不是 286 × 33。

⚠️ 這仍是**校準推算**而非直接量測，兩個假設沒驗證：
Claude Code 對兩個 plugin 的 catalog 廣播格式是否相同、`agents/` 與 `commands/` 是否也計入常駐。
要收掉這兩個假設得真的裝一次跑 `claude plugin details ecc@ecc`。
但即使只算 skills 那一列，數量級已經足以支撐結論。

ECC 自己在 README 承認「plugin 會把整個 catalog 廣播給模型」，
才提供了 `--profile minimal|core|full` 與 `--with capability:...` 讓人選裝。

## 初步判斷

**不整包裝。** 三個理由：

1. **會跟 superpowers 在同一條流程上打架。** plan / TDD / code-review 三個位置雙方都想接管，
   skill description 語意高度重疊，同時啟用會出現「該叫誰的」歧義。
2. **`blueprint` 拿掉了人類批准關卡**，而那正是 superpowers 主幹流程裡已經確認有價值的東西
   ——[Pi 那一輪](superpowers.md)的結論是「強制關卡的價值跟犯錯成本成正比」，方向不合。
3. **成本推算差一個數量級**，而 286 份的邊際效用對單人專案很低。

**但有幾份值得單獨讀**（讀原始檔就好，不必裝 plugin，也就不必付那 18.5k）：

| 檔案 | 大小 | 為什麼 |
|---|---|---|
| `skills/golang-testing/SKILL.md` | 16.7 KB | table-driven tests、subtests、golden files、interface mocking、fuzzing、race detector、coverage。**Go 原生**，牙醫系統寫測試時直接可用 |
| ~~`skills/healthcare-phi-compliance/SKILL.md`~~ | 5.7 KB | ⚠️ **實際讀完後撤回，見下節。** 大半是輸出衛生，schema 的部分綁死 Postgres/Supabase |
| `skills/healthcare-emr-patterns/SKILL.md` | 6.7 KB | ⚠️ 逐行讀過，見下節。整份只有 **Locked Encounter Pattern** 與 **Accessibility** 兩節可用，但那兩節確實有料 |
| `skills/tdd-workflow/SKILL.md` | 21.5 KB | ⚠️ **修正先前的判斷**：這份是 **JS/TS 生態**的（Jest/Vitest/Bun/Playwright，mock 是 Supabase/Redis/OpenAI）。可遷移的只有那幾條紀律（RED 有效性判準、git checkpoint、Evidence Report），大約五分之一；Go 專案該讀的是 `golang-testing` |

⚠️ `hipaa-compliance` 不建議照搬——HIPAA 是美國法規，台灣的診所適用的是個資法。

## 逐行檢查一份的結果：`healthcare-phi-compliance`（2026-08-27）

上面那張表最初把這份列為「schema 層、趁 schema 沒定案讀最划算」。
**實際讀完後這個判斷錯了**，而且錯得有代表性，值得單獨記。

我原本只掃了章節標題（Data Classification / RLS / Audit Trail / Common Leak Vectors /
Schema Tagging / Deployment Checklist），看起來一半以上是 schema 層的。
讀內容之後的實際分佈：

| 分類 | 內容 | 份量 |
|---|---|---|
| **輸出衛生**（別把病人資料印出去） | Common Leak Vectors 六條、Deployment Checklist 前五項、3 個 Example 裡的 2 個 | 主體 |
| **schema 層** | audit_log 的 append-only policy、`AuditEntry.action` enum、`COMMENT ON COLUMN` 標記 | 3 處 |

而那 3 處拿去對牙醫系統的技術棧（**Go + SQLite + 單一執行檔，Windows 10 為底線**）：

| | 適用？ |
|---|---|
| Row-Level Security | ❌ SQLite 沒有 RLS；`auth.uid()` 還是 Supabase 專屬。**這節是文件裡份量最大的 schema 部分** |
| `COMMENT ON COLUMN` 標記 | ❌ SQLite 沒有 COMMENT 語法 |
| multi-facility isolation | ❌ 單一診所，沒這個問題 |
| audit log append-only | ⚠️ 觀念可用，但得在應用層做，不是 DB policy |
| `AuditEntry.action` 含 `print` / `export` | ✅ **唯一真正的收穫** |

最後一項是整份唯一「自己重新發明想不到」的維度：多數人設計 audit 只想到 CRUD，
把**列印**與**匯出**也當成必須記錄的動作，是診所實務才會想到的
——病歷被印出來帶走是真實的外洩途徑。

**5.7 KB 讀完，換到兩條觀念。**

### 可以推廣的結論

**ECC 的領域 skill 帶著作者的技術棧一起寫死。**
這份的 `metadata.origin` 是一家實際的醫院，內容自然長成 Supabase + Postgres + TypeScript 的形狀。
它不是技術中立的 pattern，是某個具體系統的做法整理。

對照組：`golang-testing` 掃過一遍，純標準庫（`testing`、`httptest`、`encoding/json`），
唯一的 "Postgres" 只是 interface mocking 範例裡的 struct 名字。**它可攜。**

差別在於單位：**以語言為單位的 skill 可攜，以領域為單位的 skill 不可攜**
——領域 skill 的作者必然是在某個具體系統裡寫出來的，棧會跟著跑進來。
286 份裡領域 skill 佔絕大多數，這條會反覆遇到。

## 逐行檢查第二份：`healthcare-emr-patterns`（2026-08-27）

命中率比上一份好，但好的地方跟預期的不同。

| 章節 | 對牙醫系統 |
|---|---|
| Patient Safety First | ➖ 原則宣示，等於沒說 |
| Single-Page Encounter Flow | ❌ **是一般醫科／醫院的形狀**（主訴 → 病史 → 理學檢查 → 生命徵象 → 診斷 → 用藥 → 檢驗 → 計畫）。牙科的 encounter 核心是**牙位圖 + 逐顆牙的診療項目 + 健保申報代碼**，這份從頭到尾沒提到牙位 |
| Smart Template System | ❌ TypeScript interface + UI chips，範例是「胸痛」 |
| Medication Safety Pattern | ❌ 藥物交互作用 CDSS 是醫院規模的東西，需要藥品資料庫。牙科開藥種類極少（抗生素、止痛藥、局麻） |
| **Locked Encounter Pattern** | ✅ **可用，而且是 schema 層** |
| UI Patterns（vitals / lab / 處方 PDF） | ❌ NEWS2、qSOFA 是敗血症與病情惡化評分，跟牙科無關 |
| **Accessibility for Healthcare** | ✅ **可用，而且是非顯然的** |
| Anti-Patterns | ⚠️ 一半是前面幾節的反面重述，其中「不得編輯已簽署的 encounter」「臨床資料一定要有 audit trail」是 schema 層的重申 |

### 兩節有料的

**Locked Encounter Pattern** —— encounter 一旦簽署就不能改，只能加 addendum
（一筆獨立的關聯記錄），原始與 addendum 兩者都出現在病人時間軸上，
audit 記錄誰簽的、何時簽的、有哪些 addendum。

這一節跟 RLS 那節的關鍵差別：**它是技術中立的**。它講的是資料模型的形狀，不是某個 DB 的語法，
所以 SQLite 完全做得到。而且時機正好——schema v0.2 還在等醫師審閱，
「病歷簽署後能不能改」是 schema 決定，牽涉健保申報後的修改在法規上的意涵，
定案後再改成本高得多。

**Accessibility for Healthcare** —— 這節是整份第二個「自己重新發明想不到」的地方：

- 4.5:1 最低對比，因為**診間光線條件差異大**
- 44×44px 的最小點擊區，因為**戴手套操作**
- 不能只用顏色表示狀態，因為**可能有色盲的醫師**
- 臨床警示不得用會自動消失的 toast，必須主動確認

這四條都不是從「無障礙規範」推得出來的，是從**在診間工作**推出來的。
牙醫診間同樣戴手套、同樣光線條件特殊，所以直接適用。

### 對「領域 skill 不可攜」那條的補充

上一份得到的結論是領域 skill 綁技術棧。這份顯示還綁**次專科**：
它是一般醫科／住院醫療的形狀，對牙科來說 encounter 的骨架整個不同。
`healthcare-` 這個前綴涵蓋的範圍比它實際能服務的範圍大得多。

### 兩份合起來的實際收穫

| 份 | 大小 | 淨收穫 |
|---|---|---|
| `healthcare-phi-compliance` | 5.7 KB | audit 的 `action` 要含 `print`／`export` |
| `healthcare-emr-patterns` | 6.7 KB | Locked Encounter 的資料模型形狀；四條診間導向的無障礙要求 |

共 12.4 KB 讀完，換到三塊可用的東西，**全部都是「執業者知識」，沒有一塊是技術 pattern**。
技術 pattern 那部分要不是綁死別人的棧，就是我本來就會。

這跟 `/kb-push` 那次的結論同形：真正無可取代的不是流程完整度，
是那條想不到的規則。**這兩份 skill 的價值也集中在少數幾條實務知識上，密度很低但不是零。**

### 順帶的方法論收穫

這次的淘汰只花了「讀 5.7 KB + 對照自己的技術棧」，**不需要派 subagent 跑 RED 對照**。
先前規劃的實驗設計（乾淨 context 審一次 vs 讀過 skill 審一次）在這裡是過重的
——當一份 skill 的假設跟你的棧不合時，讀完就淘汰得掉，不必動用行為實驗。

**RED 對照該留給「假設相容、但不知道有沒有用」的情況。**
判斷順序應該是：先看技術棧合不合 → 再看內容是不是輸出衛生那種通識 → 都過了才值得跑 RED。

## 相關資源

- 主 repo：https://github.com/affaan-m/ECC
- 中文 README：`README.zh-CN.md`（repo 內）
- 長篇指南：`the-longform-guide.md`、`the-shortform-guide.md`、`the-security-guide.md`（repo 內）
