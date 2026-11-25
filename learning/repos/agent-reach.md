# Agent-Reach — 給 agent 的「上網工具箱」，其實是一份路由說明書

> Repo：[Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) · 類型：網路抓取／搜尋
> 證據強度：🟡 只讀文件與部分原始碼（透過 WebFetch 摘要，非逐行），沒安裝 · 看過日期：2026-10-05
> 結論：不裝 — Claude Code 已有 WebSearch／WebFetch／Chrome 擴充；真正多出來的只有 YouTube 字幕和中文平台

## 這是什麼

一個命令列工具 `agent-reach`，把各平台的抓取工具包成同一個介面，讓 agent 不必一個個去申請 API key。
每個平台有「主要方案 + 備援」，前一個失敗就換下一個；`agent-reach doctor` 診斷哪些管道目前可用。

| 項目 | 內容 |
|---|---|
| 作者 | Panniantong |
| 建立 / 最後 push | 2026-02-24 / 2026-09-15 |
| 星數 / fork | 91,925 / 8,067（2026-10-06，GitHub API） |
| 授權 | MIT |
| 開放 issue | 213 |

## 結構

依使用門檻分三類：

| 門檻 | 平台 |
|---|---|
| 免設定 | 一般網頁（Jina Reader）、YouTube 字幕（yt-dlp）、RSS、GitHub（`gh`）、B 站 |
| 要 cookie／登入 | Twitter/X、Reddit、小紅書、Facebook/Instagram、LinkedIn |
| 要 API key | 全網語意搜尋（Exa，有免費額度） |

**實質內容**：免設定那一欄其實全是現成工具——`mcporter` 打 Exa、`curl r.jina.ai`、`gh`、`yt-dlp`、
B 站直接打網頁 API。它沒有自己的抓取技術，價值在於「一份教 agent 怎麼挑工具、失敗怎麼重試的路由表」加一個 `doctor`。

## 怎麼用

官方做法是把 `install.md` 的網址丟給 agent 讓它照著裝。預設是安全檢查模式（只檢查缺什麼），
加 `--system` 才會真的裝依賴與寫設定，`--dry-run` 可預覽，`agent-reach uninstall` 可移除。
需要 Python 3.10+，部分管道另需 Node.js、`gh`、`mcporter`。

## 跟我的關係

| 需求 | Claude Code 已經有的 |
|---|---|
| 搜尋 | WebSearch |
| 抓網頁 | WebFetch |
| 要登入或 JS 的頁面 | 內建瀏覽器、Chrome 擴充（用真實登入狀態） |
| GitHub | `gh` |

所以新增價值只剩 YouTube 字幕、B 站與中文平台——而中文平台是風險最高的部分
（要 cookie、有封號風險、靠逆向 API 隨時可能失效）。
它的設計對象是**沒有瀏覽器、沒有內建搜尋的 agent**（OpenClaw 那類跑在 VPS／Docker 的），
對那些 agent 是補齊基本功能；對 Claude Code 是重複。

審查時發現的幾個要注意的點：

1. **SKILL.md 的觸發條件太強**：description 寫 `MUST USE when user wants to research/search/look up anything on the internet`。
   裝了之後每次查東西都會被導向它，搜尋內容送去 Exa、網頁經過 `r.jina.ai`，都是第三方
2. **會寫進 `~/.claude/skills/`**：等於新增一份影響 agent 行為的指令，裝前要先讀過
3. **Windows 不是它的主場**：`--system` 的依賴安裝只有 `apt-get` 與 `brew`；指令是 Unix 風格（`/tmp/`、`curl -c`）
4. **`--system` 會做全域修改**：`npm install -g undici`、`npm install -g mcporter`、寫 `~/.config/ytdlp/config`
5. B 站的 yt-dlp 路徑文件自己承認已被 412 封鎖，靠模擬 User-Agent 打網頁 API

## 證據與限制

- **讀過的**：README、`install.md`、`pyproject.toml`、`cli.py`、`cookie_extract.py`、SKILL.md
- **可信度**：全部經 WebFetch 的小模型摘要，**不是逐行讀原始碼**。「沒有遙測」「`install` 不會自動讀瀏覽器 cookie」
  這類結論來自程式碼註解與摘要，沒有自己驗證；「憑證不外傳」是作者的說法
- **沒做的**：沒安裝、沒在 Windows 上跑過 `doctor`；「Python 部分應該能跑」是推論

## 下一步

- [ ] 如果只想要 YouTube 字幕：直接 `pipx install yt-dlp` 就夠，不需要整套
- [ ] 之後真的需要小紅書、雪球這類平台時再回頭評估；那時要用專用小號，不要用主帳號
- [ ] 若仍想試：只 `pipx install` 本體、不加 `--system`、不註冊 skill（或把 description 改成只在明說「用 agent-reach」時觸發），
      再跑 `agent-reach doctor` 看 Windows 上哪些管道可用

## 相關

- [Repo 閱讀筆記總覽](README.md)
- [HyperFrames](hyperframes.md) — 同樣是「給 agent 加能力」，但那邊補的是 agent 本來做不到的事（出影片）
