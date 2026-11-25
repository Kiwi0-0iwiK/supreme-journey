# Graphify — 把程式碼庫變成「可查詢的知識圖譜」，給 coding agent 當長期記憶

> Repo：[Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) · 類型：agent skill／程式碼索引
> 證據強度：🟡 只讀文件（README 經 WebFetch 摘要；ARCHITECTURE.md 與目錄清單直接從 GitHub API 讀），沒安裝 · 看過日期：2026-10-20
> 結論：觀望 — 概念有用，但目前沒有大型程式碼庫卡在「agent 讀不完」；數字都是作者自己的 benchmark，沒人替我驗過

## 這是什麼

一個 Python 套件加一個 `/graphify` skill。它掃描資料夾（程式碼、文件、PDF、SQL schema、設定檔、甚至影音），
建出一張**知識圖譜**（節點＝函式／類別／概念，邊＝呼叫／import／繼承…），存成檔案，之後 agent 問問題時先查圖，
而不是一直 grep 然後整檔讀進 context。目的是省 token、讓 agent 對大型程式碼庫有「結構感」。

最特別的設計選擇：**程式碼部分完全不用 LLM**，用 tree-sitter 在本機做 AST 解析（確定性、零 token 成本）；
只有文件／PDF／圖片這類非程式碼內容才送去 LLM 抽概念。而且**刻意不用向量資料庫**，
用「每條邊都有理由」換掉「語意相似度搜尋」。

| 項目 | 內容 |
|---|---|
| 作者／組織 | Graphify Labs（README 自稱 Y Combinator S26，**未獨立查證**） |
| 建立 / 最後 push | 2026-04-03 / 2026-10-16（GitHub API，2026-10-20） |
| 星數 / fork | 129,310 / 12,470（2026-10-20，GitHub API） |
| Open issue（含 PR） | 1,567（GitHub API 的數字把 PR 一起算；README 頁面顯示 712 issue + 855 PR，加起來吻合） |
| 授權 | Apache-2.0（API 回報）；README 稱 Apache-2.0 與 MIT 雙授權，根目錄確實有 `LICENSE-MIT` |
| 語言 / 技術棧 | Python 3.10+、tree-sitter、NetworkX、Leiden 社群偵測、faster-whisper（影音轉錄，選配） |
| 預設分支 | `v8`（不是 main） |

## 結構

處理流程（取自 `ARCHITECTURE.md`，這份是直接讀的，不是摘要）：

```
detect → extract → build → cluster → analyze → report → export
掃描檔案   抽節點與邊   組成圖    分社群     找重點節點等   產報告    輸出各格式
```

| 階段 | 做什麼 |
|---|---|
| extract | 程式碼走 tree-sitter（約 40 種語言）；文件／PDF／圖片走 LLM（可選 Claude、OpenAI、Gemini、Ollama 本機等） |
| build / cluster | 組成 NetworkX 圖，用 Leiden 演算法自動分「社群」（功能群組） |
| analyze | 找 god node（連線最多的核心概念）、意外連結、import 循環、圖的前後差異 |
| export | `graph.json`（可查詢本體）、`graph.html`（互動視覺化）、`GRAPH_REPORT.md`、Obsidian vault、SVG、GraphML、Neo4j Cypher、Mermaid 呼叫流程圖、每個社群一篇的 wiki |
| serve | MCP server（需另裝 `graphifyy[mcp]`），讓 agent 用工具呼叫的方式查圖 |

**每條邊有信心標籤**：`EXTRACTED`（原始碼明寫，如 import）、`INFERRED`（合理推論，如二次掃描的呼叫圖）、
`AMBIGUOUS`（不確定，標在報告裡請人看）。這是它跟一般 RAG 最大的差別——你看得到「這條關係是讀出來的還是猜的」。

另有快取（只重算改過的檔案）、`watch`（檔案變動自動重建）、git hook、`.graphifyrc` 設定檔（宣告 `.inc` 這類模稜兩可的副檔名要當哪種語言）。
商業版 Graphify Cloud 是託管版（monorepo、Sentry／Jira 連接器），開源版不含。

## 怎麼用

README 給的最小流程：

```bash
uv tool install graphifyy      # 注意套件名是 graphifyy（兩個 y）
graphify install               # 偵測你用哪個 agent，自動註冊 skill／hook
/graphify .                    # 在 agent 裡對當前資料夾建圖
```

之後：

| 指令 | 用途 |
|---|---|
| `graphify query "<問題>"` | 用自然語言問圖 |
| `graphify path "A" "B"` | 找兩個概念之間的最短關聯路徑 |
| `graphify explain "概念"` | 看某個節點的詳細資訊 |
| `graphify prs` | PR 儀表板，看每個 PR 對圖的影響 |

支援 20 幾種 agent（Claude Code、Cursor、Codex、Gemini CLI、Copilot、Aider…）。
Claude Code 與 Gemini CLI 是用 **hook** 做「always-on」——提醒 agent 先查圖再 grep；其他平台是寫入常駐的指令檔。

## 跟我的關係

**推測的部分都標了「推測」。**

- **最可能有用的場景**：我手上多模組、持續長大的後端專案，當 agent 要改一個牽涉很多檔案的功能時，
  先看圖能快速知道「改這裡會影響誰」。（推測：專案規模大概還沒到非用不可。）
- **Obsidian／wiki 匯出**：跟我的 knowledge-base 概念接近，但我的筆記是手寫的、有證據強度標記，
  自動生成的 wiki 不會有這種「我實際驗過沒」的資訊，**不適合取代**，頂多當第一次進陌生 repo 的導覽。
- **跟 superpowers 的關係**：superpowers 補的是「怎麼做事」，graphify 補的是「對程式碼庫的記憶」，兩者不衝突。
  但同 [Repo 閱讀筆記總覽](README.md) 的判準：Claude Code 本身已有 Grep／Glob／Explore agent，
  graphify 補的是**它在大型 repo 上效率不夠**的那塊，而不是完全缺的能力——價值取決於 repo 夠不夠大。
- **要注意的風險**：
  1. `graphify install` 會寫 hook 與 skill 進 agent 設定，等於新增一份影響行為的指令，裝前要讀過（同 Agent-Reach 的教訓）
  2. 文件／PDF／圖片會送給 LLM；**含真實個資的資料夾絕對不能對它跑**——程式碼本身是本機處理，但 docs 部分不是
  3. `.graphifyrc`、快取、`graphify-out/` 輸出都會落在專案資料夾，要記得加進 `.gitignore`

## 證據與限制

- **實際做過的**：直接用 GitHub API 取得 repo 統計、頂層目錄、`graphify/` 套件的模組清單，並讀了 `ARCHITECTURE.md` 前 120 行。
- **沒做、只是讀到的**：
  - **沒安裝、沒跑過**，不知道在 Windows 上實際行為（README 說支援，有 `skill-windows.md`，但我沒驗）
  - 「省約 80% token」「LOCOMO recall@10 0.497」「LongMemEval 76%」「ERPNext 82.0% vs grep 70.8%」**全是作者自己的 benchmark**，
    我沒有重現，也沒看他們的測試方法原始碼。尤其「80%」是行銷數字，實際會因 repo 與問題類型差很多
  - 「無遙測」「程式碼不外傳」是 README 的說法，沒讀原始碼驗證
- **資料取得方式的可信度**：README 內容（功能列表、benchmark、授權雙授權、YC 身分）是 WebFetch 小模型摘要，**可能有遺漏或轉述誤差**；
  ARCHITECTURE.md 與 API 數字是直接讀的，可信度較高。
- **一個值得懷疑的點**：12.9 萬星的專案在 6 個月內長出來（2026-04 建立），數量級異常，
  可能是真的爆紅，也可能含大量非自然星數。**這是觀察不是結論**，我沒有查星數來源。

## 下一步

- [ ] 如果要試：先在一個**不含個資的小專案**（例如 gtnh-calc）跑 `/graphify .`，
      只看 `GRAPH_REPORT.md` 的 god node 跟實際認知對不對得上，再決定要不要常駐
- [ ] 試之前先讀 `graphify install` 對 Claude Code 寫了什麼 hook（`graphify/hooks.py`、`graphify/always_on`）
- [ ] 想驗 token 省多少：同一個問題，有圖／沒圖各問一次，比較 context 用量，不要信 80%
- [ ] 之後專案大到 agent 常常找錯地方，再回頭評估

## 相關

- [Repo 閱讀筆記總覽](README.md)
- [Agent-Reach](agent-reach.md) — 同樣是「給 agent 裝 skill 的工具」，審查時同樣要注意 skill 的觸發範圍與安裝會寫哪些設定
- [HyperFrames](hyperframes.md)
