# 多模型協作 — 讓不同 AI 互相審查

> 狀態：已定型，持續補充
> 起點：2026-07-07（探索）→ 2026-08-15（在真實專案跑過四輪後收斂成筆記）

原本的問題很單純：**能不能讓不同的 model 一起工作，而不是每次只問一個？** 具體想試兩件事——同時開多個 Claude subagent 分別用不同 model，以及把 OpenAI 的 Codex 串進同一個流程。

後來在一個私人的 Go + SQLite 專案上實際跑了四輪（schema 設計一輪、程式碼三輪），所以下面不只是設置教學，也包含真的跑過之後才知道的事。

## 結論先講

**價值不在「多一個 model 幫你寫」，在「多一個不同家族的 model 幫你挑錯」。**

同一個問題丟給同家族的兩個 model，盲點高度重疊；丟給不同家族（Claude vs OpenAI）才會出現真正獨立的第二意見。而最有說服力的訊號是——**兩邊各自獨立跑，卻抓到高度重疊的問題**。當 Codex 跟 Claude 互不知情地都指向同一個地方，那個地方幾乎確定有問題，這比任何一邊單獨的信心分數都可靠。

四輪下來抓到的，都是那種「能跑、測起來也正常，但邏輯上有洞」的問題：連線池後面的 pragma 作用範圍、狀態機的競態、錯誤分類 fail-open。這類問題單靠自己讀或跑測試很難發現。

## 怎麼串起來

### 多個 Claude model 平行工作

**不需要裝任何東西。** Claude 的 Agent tool 本身就能指定 model，把同一個任務丟給不同 model 的 subagent 平行跑，各自回報結果直接比較。

### 串 OpenAI Codex

1. 裝 Codex CLI：`npm install -g @openai/codex`（需要夠新的 Node，v22 可以）
2. `codex login` 用 ChatGPT 帳號登入，`codex login status` 確認
3. 官方有出 Claude Code 的 plugin：[openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc)，提供 `/codex:review`、`/codex:rescue`（直接委派任務動手做）、`/codex:transfer`（把目前 session 轉成 Codex thread）等指令

**不靠 plugin 也行**，CLI 本身就有非互動模式，可以直接用 Bash 呼叫，不依賴 slash command 有沒有被載入：

```bash
codex exec -m <model> "prompt"      # 非互動執行
codex review --uncommitted          # 審查目前未提交的變更
codex review --base main            # 跟 base branch 比較
```

### 環境落差：plugin 指令不是到處都能用

Plugin 的 slash command 在 VSCode extension 裡會顯示「no matching commands」，**只有 standalone `claude` CLI 認得**。而且在 VSCode 裡跑 `/plugin marketplace add ...` 會說「isn't available in this environment」，但檢查 `~/.claude/plugins/installed_plugins.json` 會發現 plugin **其實已經裝好而且 enabled** ——訊息會騙人，要去看實際狀態。

影響不大：開一個 terminal 跑 `claude` 就有完整指令，或者乾脆直接請 Claude 用 Bash 呼叫 `codex exec`，效果等價，只是少了背景任務追蹤的 UX。

## 真的跑過才知道的事

### Codex 的沙盒可能寫不了檔案，要有取件的替代路徑

在我這台 Windows 機器上，即使明確指定 `--sandbox workspace-write`，實際還是會被**強制降級成 read-only**（用 `codex doctor` 和直接測試都確認過，不是設定寫錯）。結果就是 Codex 每次都沒辦法自己把 review 寫成檔案。

解法是**直接查詢原始輸出再手動轉存**（`codex-companion.mjs result <job-id>`）。曾經試過另一條路——請 Codex 自己把全文口述一遍讓我抄——結果被 Codex 自己的安全判斷擋下來了。所以取原始輸出這條路徑更可靠。

Claude 這邊因為在自己的 session 裡有寫入權限，可以直接產出 review 檔案，不需要這個步驟。**跨工具協作時，「產出物怎麼落地」要單獨想過，不要假設對方跟你有一樣的權限。**

### 讓別的 session 做實測前，先確認 port 沒被佔用

有一次審查方為了驗證結論，真的打了 HTTP request 去測——結果撞上我當時還開著的本機 dev server，把裡面的測試資料弄亂了。那個資料庫本來就是拋棄式的，刪掉重建就沒事，沒有實質損失，但這是個很好的提醒：

**「唯讀審查」跟「會動手實測的審查」是兩件事。** 放手讓另一個 session 做實測之前，先確認它要用的 port／資料庫／檔案不會跟你手上正在跑的東西撞到，或者直接要求它換一個 port。

### review gate 不要隨便開

plugin 有個 `review gate` 選項（`/codex:setup --enable-review-gate`），會在 Claude 每次要結束回應前先跑一次 Codex review。官方自己就警告可能造成 Claude/Codex 互相 review 的循環，很燒 usage。想清楚再開。

### 什麼時候值得動用

不是每件事都需要兩個 model。實際用下來的分界：

- **值得**：schema／架構這種一次性、之後改起來很痛的決策；剛寫完一大片還沒有測試覆蓋的程式碼
- **不值得**：日常小改、UI 調整、已經有測試守著的重構——多一輪審查的成本高過收穫

## 順手整理的：官方 plugin 清單

Anthropic 官方作者的 plugin 相對安全穩定，跟這個主題比較相關的：

- `code-review` / `pr-review-toolkit` — 多 agent code review，有信心分數過濾誤報
- `learning-output-style` — 互動學習模式，關鍵決策點會要求你自己貢獻程式碼，不會整段幫你寫完
- `frontend-design` — 做有質感、不落俗套的前端 UI
- `security-guidance` — 對產出的程式碼做安全掃描（injection／XSS／寫死密鑰等）
- `commit-commands` — commit / push / PR 標準化流程
- `session-report` — 產生本機 session 使用狀況的 HTML 報告
- `pyright-lsp`（Python）、`typescript-lsp`（JS/TS）
- `mcp-server-dev` / `plugin-dev` — 想深入這整個主題可以看

完整清單在 `~/.claude/plugins/marketplaces/claude-plugins-official/.claude-plugin/marketplace.json`，搜尋 `"name": "Anthropic"` 可以撈出全部。

## 之後可以再看的

- 目前的交叉驗證都是**人在中間轉手**（我把 A 的結論貼給 B）。有沒有辦法讓兩邊直接對話、自己收斂到共識，而不是每輪都要我轉述？
- 三個以上的 model 一起審會不會出現「多數決」的錯覺——兩個同家族的 model 犯同樣的錯，看起來卻像是互相佐證
