# Agent harness 框架研究

> 狀態：🟡 進行中 · 開始日期：2026-08-15

把「跑 agent 的整套執行環境」當成一個持續的研究主題，一個 repo 一份筆記，
這份總覽負責橫向比較與選用結論。

## 為什麼叫 harness 而不叫 skills

一開始的切入點是 Claude Code 的 skill 框架，但這個範疇很快就不夠用了：
ECC 除了 skill 還有 agents、hooks、memory vault、跨 harness 移植層；
而下一步想做的事情是**在自架的 Linux sandbox 上直接跑別的 agent 框架**
（OpenHands、aider、opencode、Hermes 那一類自帶 runtime 的），那些根本不是 skill 包。

所以收錄標準訂寬一點：**任何「決定 agent 怎麼工作」的那一層**都算——
skill 集、工作流方法論、多 agent 編排器、自架 runtime。

## 收錄的 repo

| 筆記 | Repo | 是什麼 | 證據強度 |
|---|---|---|---|
| [superpowers](superpowers.md) | [obra/superpowers](https://github.com/obra/superpowers) | 強制流程的開發方法論 + 14 個 skill | 🟢 **已安裝實測**：四輪 subagent 實驗、A/B fixture 對照、context 成本實際量測、一次完整主幹流程實戰 |
| [ECC](ecc.md) | [affaan-m/ECC](https://github.com/affaan-m/ECC) | 286 skill + 68 agent 的大型發行版 | 🟡 **只讀過文件**：metadata + README + 抽讀 5 份 SKILL.md |

⚠️ **證據強度這一欄是刻意放在最前面的。** 兩份筆記的結論不是同一個等級——
一份背後有實驗，一份只是讀完文件的印象。不標清楚的話，過幾個月回來看會把兩者當同等強度，
而這正好是 superpowers 那輪學到的教訓（「n=1 的基線真的會騙人」）。

## 橫向比較

比較的軸是**已經驗證過的那幾個維度**，不是把功能清單並排。

### 一、Context 成本模型

superpowers 實測的結論是：成本不在「裝了就變重」，而在「**用哪個才變重**」。
14 個 skill 常駐只吃 465 token（0.2% 的 200k window，等於免費），
真正的錢付在 on-invoke，而且分佈極不平均——`subagent-driven-development` 一次 8.4k，
`executing-plans` 只要 560。這讓「先裝著、只挑幾個用」變成完全合理的策略。

ECC 打破的正是這個模型：286 個 skill 的描述全部進 always-on。
2026-08-27 量出來是 **18,450 token**（拿 superpowers 的實測值 465 tok 校準出 4.63 chars/token，
再套到 ECC 的 frontmatter 字元數）——200k window 的 9.2%，是 superpowers 的 **40 倍**。
把 `agents/` 和 `commands/` 也算進去是 24k。

當 catalog 大到一個程度，「裝了就變重」會重新成立。**這是兩者最實質的架構差異**，
不是內容多寡的問題。細節與方法見 [ecc.md](ecc.md)。

### 二、關卡由誰把守

| | superpowers | ECC |
|---|---|---|
| 動手前 | **人類批准設計意圖**，硬性關卡，不隨任務大小放寬 | `blueprint` 五階段自動跑完，adversarial review 由「最強模型的 sub-agent」執行 |
| 實作中 | RED-GREEN-REFACTOR，紅旗清單擋鑽漏洞 | `tdd-workflow`：RED 必須真的編譯執行過、80% coverage 量化門檻、commit 可 reach 性檢查 |
| 實作後 | 乾淨 context 的 reviewer，implementer 不得自審 | Evidence Report + `security-review` / `delivery-gate` |

在 Pi 那一輪得到的判斷是「**強制關卡的價值跟犯錯成本成正比**」——
低成本任務上覺得囉嗦的東西，在硬體重灌那種做錯要整輪重來的任務上剛好。
ECC 把最前面那道關卡自動化掉了，等於押注「模型審模型夠好」。這個假設還沒被測過。

反過來說，ECC 的實作中關卡**比 superpowers 具體**（「只寫了測試但沒編譯執行不算 RED」
這種話 superpowers 沒寫死）。兩邊不是同一個方向的嚴格。

### 三、方法論層 vs 領域層

superpowers 只有方法論——怎麼做事，不管領域。
ECC 兩層都有，但**元層是缺的**：它沒有「怎麼寫一個 skill」的方法論
（`skill-comply` 是事後合規檢測，不是寫作指南），
卻有大量領域 pattern 庫（醫療資訊系統、各語言、家用網路、context 管理）。

這剛好互補而不是重疊：**方法論那層兩邊搶同一個位置，領域那層只有 ECC 有。**

### 四、生態位

| | superpowers | ECC |
|---|---|---|
| 適合 | 一個人／小團隊，想把「怎麼做事」制度化 | 多語言多 harness 的團隊，需要統一規範與現成領域知識 |
| 賣點 | 少而狠，靠約束力 | 多而全，靠覆蓋率 |
| 品質一致性 | 14 份同一人寫，密度均勻 | `metadata.origin` 有 `ECC` 也有 `community`，要一份一份看 |

## 目前的選用結論

**主幹留 superpowers，ECC 不整包裝。**

理由三個：兩者會在 plan / TDD / code-review 三個位置打架；
ECC 的 `blueprint` 拿掉了已經確認有價值的人類關卡；成本推算差一個數量級，
而 286 份的邊際效用對單人專案很低。

**但從 ECC 單獨拿幾份讀**（讀原始檔，不裝 plugin，也就不必付那 18.5k）：
`golang-testing`、`healthcare-phi-compliance`、`healthcare-emr-patterns`。
清單與理由見 [ecc.md](ecc.md)。

成本那一項已經量過了，結論反而更硬。內容品質也有了兩個逐行讀完的樣本
（`healthcare-phi-compliance`、`healthcare-emr-patterns`，共 12.4 KB）：

**淨收穫是三條實務知識，零條技術 pattern。** 技術 pattern 那部分要不是綁死作者的棧
（RLS／Supabase／TypeScript，對 Go + SQLite 用不上），就是本來就會的通識。
真正有價值的是 audit 要記錄「列印」與「匯出」、encounter 簽署後只能加 addendum、
以及四條從「戴手套在診間工作」推出來的無障礙要求。

由此得到一條可推廣的判準：**以語言為單位的 skill 可攜，以領域為單位的 skill 不可攜**——
領域 skill 的作者必然是在某個具體系統裡寫出來的，技術棧會跟著跑進來，
而且還會綁**次專科**（那兩份是一般醫科／住院醫療的形狀，牙科的 encounter 骨架完全不同）。
286 份裡領域 skill 佔絕大多數。細節見 [ecc.md](ecc.md)。

## 下一步

1. ~~量 ECC 的真實 always-on 成本~~ ✅ 2026-08-27 完成：18.5k（skills）／24k（含 agents+commands），
   原本的推算低估一倍，見 [ecc.md](ecc.md)
2. `tdd-workflow` 完整讀完，跟 superpowers 的 TDD skill 逐條對照——這是唯一兩邊都有、
   可以直接比內容的 skill（但要留意它是 JS/TS 生態的）
3. superpowers 那邊還欠的實測：低成本任務的過重程度對照、`subagent-driven-development` 的 ledger
   （見 [superpowers.md](superpowers.md) 的「下一步」）
4. 自架 sandbox 上跑第三個框架——收錄範圍從「Claude Code 的 skill 包」擴到「自帶 runtime 的 agent 框架」

## 相關

- [多模型協作筆記](../../learning/notes/multi-model-workflow.md) — 「讓不同廠商的模型互審」
  是跟這裡的 review gate **同一個問題的另一種解法**：跨廠商擋的是同一模型的系統性盲點，
  乾淨 context 擋的是被前文帶偏
