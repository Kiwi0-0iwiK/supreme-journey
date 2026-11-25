# modern-web-guidance — 在 agent 寫前端之前，先查一份「現代網頁平台」最佳實踐

> Repo：[GoogleChrome/modern-web-guidance](https://github.com/GoogleChrome/modern-web-guidance) · 類型：agent skill／知識庫（前端）
> 證據強度：🟢 實際跑過 CLI，並做了 A／B 盲測各一次（v1.0.2，關閉遙測；**沒有全域安裝 skill**）· 看過日期：2026-11-25
> 結論：部分採用 — 有 guidance 的 agent 多抓到約 12 項前端語意與可及性問題，但 token 多 63%、時間加倍，而且抓不到安全、資料誠實度與視覺問題；只在做前端那一輪時開，不全域安裝

## 這是什麼

一個 Claude Code／Codex／Gemini 等通用的 **skill**。你叫 agent 做前端（dialog、表單、動畫、效能、無障礙…）時，
skill 要求它**先**用 CLI 搜尋一份離線的 guide 資料庫，把對應的現代寫法（Popover API、View Transitions、
`:user-invalid`、anchor positioning…）和降級方案讀進 context，再動手寫。
動機是 README 講的：LLM 訓練資料裡舊寫法太多，所以 agent 常寫出肥大的 JS 去做瀏覽器現在原生就能做的事。

重點是：**guide 是人寫的、有用 eval 修剪過**（把模型本來就會的刪掉），不是把 MDN 整份塞進去。

| 項目 | 內容 |
|---|---|
| 作者／組織 | GoogleChrome（README 自稱由 Chrome、Edge、Firefox、MDN 團隊與社群共同維護，**未獨立查證**） |
| 建立 / 最後 push | 2026-03-23 / 2026-11-23（GitHub API，2026-11-25） |
| 星數 / fork | 25,973 / 1,103（2026-11-25，GitHub API） |
| 授權 | Apache-2.0（程式碼）；`guides/` 內容為 CC-BY 4.0（README 寫的） |
| 版本 | v1.0.2（2026-11-23）；v1.0.0 是 2026-11-10，之前是 0.0.x 每週一版 |
| 語言 / 技術棧 | 內容是 Markdown；CLI 是單一 `.mjs`（Node ≥ 22，npm 套件宣稱零依賴） |
| 貢獻者 | GitHub API 只列出 4 位（這個 repo 只是**發佈用**，真正開發在 `modern-web-guidance-src`，人數看不到） |

**這個 repo 只是 publish target**：`CONTRIBUTING.md` 明說 PR 和 issue 要去 `GoogleChrome/modern-web-guidance-src`。
所以在這裡看不到 CLI 原始碼、eval 程式碼、搜尋引擎實作。

## 結構

| 路徑 | 內容 |
|---|---|
| `skills/modern-web-guidance/SKILL.md` | skill 本體（約 9.8 KB）。觸發描述、搜尋→取回→核對→揭露四步流程 |
| `skills/modern-web-guidance/guides/` | **211 篇 guide**，分 17 類 |
| `skills/chrome-extensions/` | 第二個 skill pack：Manifest V3、service worker、上架審核清單等（SKILL.md 約 26 KB＋references） |
| `.claude-plugin/`、`.codex-plugin/`、`.cursor-plugin/`、`.agents/`、`.grok-plugin/`、`gemini-extension.json`、`kimi.plugin.json`、`plugin.json` | 各家 agent 的外掛清單，**內容幾乎一樣**，只是格式不同 |
| `policies/modern-web-guidance.toml` | Gemini 用的規則：plan 模式下跑含 `modern-web` 的 shell 指令要先問 |
| `package.json` | `bin` 指向 `skills/modern-web-guidance/modern-web.mjs`，但**這個檔案不在 repo 裡**，是 npm 發佈時才帶進去的 |

guide 數量（GitHub API 檔案樹，2026-11-25）：ui-behaviors 40、performance 26、ui-components 23、visual-design 22、
forms 19、css 18、security 17、ui-atoms 13、html 8、js 6、built-in-ai 5、accessibility 4、user-experience 3、webmcp 3、
pwa 2、privacy 1、wasm 1。README 另宣稱涵蓋「269 項現代網頁功能」，那是**功能數不是 guide 數**，兩個數字別混。

每篇 guide 的寫法（我只細看了 `navigation-drawer.md` 前半）：先講概述與「用哪個元素」的決策（例如只當抽屜用 `<dialog>`，
兼當側欄就要用 `popover="manual"`），再給完整 HTML／CSS／JS，附無障礙與降級方案，用 `MANDATORY:` 這類字眼標必做項目。
比一般教學文件**更像給 agent 的指令**，而不是給人讀的教學。

## 怎麼用

最小流程（README 與 SKILL.md 寫的，沒實際執行）：

```shell
npx modern-web-guidance@latest install                    # 互動精靈，要 Node 22+
npx modern-web-guidance@latest search "light dismiss dialog"
npx modern-web-guidance@latest retrieve "<guide-id>"
npx modern-web-guidance@latest legacy-scan .              # 掃舊寫法，只覆蓋約 20% 的 guide
```

Claude Code 另有外掛安裝路徑：`/plugin marketplace add GoogleChrome/modern-web-guidance`，
再 `/plugin install modern-web-guidance@googlechrome`。
README 特別提醒：官方 `claude-plugins-official` 市集的版本停在 v0.0.194（10/12 之後沒更新），要換成 `googlechrome` 市集。
（這是 README 的說法，我沒去驗那個 issue。）

SKILL.md 規定的行為，**裝了之後 agent 會這樣做**：

1. 每個 HTML／CSS／前端 JS 任務**一開始**先 `search`（2–5 個英文字、單一功能、不要帶框架名或專案名）
2. 有命中就 `retrieve`，大輸出會存暫存檔要它整份讀
3. 寫完對照 guide 核對
4. **回答結尾要附一段 `### Modern Web Guidance`**，逐項說明用了哪個 guide、哪個非顯而易見的坑
5. 後端、CI、Docker、tsconfig、測試、改文案這類不要觸發

另有 `.mwgrc` 設定檔：預設擋住 Origin Trial 與「剛上線的單一引擎功能」，要明確開關才會讓 agent 用。
這個設計蠻實際，避免 agent 興沖沖採用還不穩定的 API。

## 跟我的關係

**推測的部分都有標。**

- **補的是真缺口。** 照 [總覽的判準](README.md)：Claude Code 本身會上網、會 grep，但「訓練資料偏舊」是它**不會自己修**的。
  這點跟 Agent-Reach（重複內建能力）不同，比較像 superpowers 補「方法」那種，補在 agent 原本缺的位置。
- **我手上的前端專案不少**：wifi 時間軸網站（原生 HTML/CSS/JS＋ECharts）、各個 Quartz 網站，以及其他含後台介面的專案。
  （推測）時間軸網站的樣式與互動最容易看出差別，適合當試驗場。
- **「必須先查」的觸發寫得很兇。** description 裡有 `MANDATORY: Execute FIRST for all HTML/CSS and clientside JS tasks. Do NOT skip`。
  代價是每個前端小改動都多一輪 `npx` 搜尋，還有結尾那段固定的揭露區塊。這是行為上的改變，不只是多一份知識。
- **遙測會送搜尋字串。** README 寫明會收：安裝次數、呼叫的 agent 名稱、取回的 guide ID、**agent 產生的搜尋字串**，
  不收原始 prompt。SKILL.md 要求 query 去掉專案與元件名，所以風險不高，但這個機制是靠 agent 守規矩，不是技術上擋住。
  `DISABLE_TELEMETRY=1` 可關。**碰到含真實個資的專案就先關**——query 是 agent 寫的，不是我逐字審過的。
- **要記得的運作面**：要放行 `npx -y modern-web-guidance@latest *`（SKILL.md 建議白名單只開這個，不要開裸 `npx *`），
  而且每次都要網路；離線只能用快取＋`--offline`。

## 證據與限制

- **實際做過的**：用 GitHub API 取得 repo 統計、完整檔案樹、近期 commit；直接讀了 README（前段與後段，
  導覽表格與功能清單的中間約 280 行是 269 項功能的連結表，**只掃過沒逐項讀**）、`SKILL.md`、各 manifest、
  `CONTRIBUTING.md`、`navigation-drawer.md` 前 120 行；用 `npm view` 查了套件版本（1.0.2、282 個檔案、解壓後約 16 MB）。
- **沒做、只是讀到的**：
  - ~~沒安裝、沒跑任何 `search`／`retrieve`~~ → 同日稍晚已直接跑 CLI，見「實際作用紀錄」。仍然**沒有用 `install` 全域安裝 skill**，所以 agent 自動觸發的行為沒測
  - ~~沒下載 npm 套件讀 CLI 原始碼~~ → 已讀遙測與 watchdog 的程式碼，送出欄位與 README 一致
  - 其他 210 篇 guide 沒讀，所以**不能說它們品質一致**（我只看過一篇）
- **效果數字全是作者自己的**：README 的 eval 表（例如 claude_code opus-5-5 從 54% 到 94%，+40pp）出自他們自己的 229 個任務、
  自己寫的 Playwright 評分器，而且評分器是對「他們自己寫的 golden solution」校準的。
  guide 又是依這個 eval 修剪的，所以**有自己出題自己考的疑慮**。這是觀察，不是說他們造假；
  但「+40pp」不能直接當成我專案上的預期。
- **資料取得方式**：README、SKILL.md、manifest 都是從 GitHub contents API 取得的原文，不是 WebFetch 摘要，可信度較高；
  星數、日期是 API 數字，會變。

## 實際作用紀錄

### 2026-11-25：wifi 時間軸網站審查與修正 — guidance 的實際作用是「零」，這次是對照組

**先講結論：這次沒有用到 modern-web-guidance。** 讀完這個 repo 之後，同一個 session 接著審查並修改
[amd-ftpm-vanguard.pages.dev](https://amd-ftpm-vanguard.pages.dev)（原生 HTML/CSS/JS＋ECharts），
但 skill **沒安裝、沒跑過 `search`／`retrieve`**，下面每一項都是 agent（Claude）自己看出來、自己修的。
所以這一節**不能當成 guidance 有效的證據**。它的用處是當**沒有 guidance 時的基準線**（unguided baseline），
之後裝了 skill 重做一次，才有東西可以比。

審查方式：瀏覽器實測（手機 360／375 px、深淺色）＋讀原始碼。修改前的基準 commit 是 `85d7b5b`。

| # | 問題 | 怎麼發現 | 修法 | 修後驗證 |
|---|---|---|---|---|
| 1 | 英文版首頁在手機上橫向捲動（375 px 溢出 6 px、360 px 溢出 19 px），主題按鈕被擠出畫面 | 量 `scrollWidth` 與超出畫面的元素 | `.brand` 加 `min-width:0; overflow:hidden; text-overflow:ellipsis`，語言切換與按鈕 `flex-shrink:0` | 三種語言在 360 px 都不溢出 |
| 2 | 調查頁統計表在手機上把整頁撐到 501 px（修 #1 時另外發現的舊問題，正式站因為統計是捲到才載入，第一次審查沒看到） | 用假統計資料讓統計區真的畫出來 | 窄螢幕的 grid 欄從 `1fr` 改成 `minmax(0, 1fr)`，表格改在自己的框內捲動 | 360 px 不溢出 |
| 3 | 只有 2 台回報卻顯示「同樣問題 · 100%」 | 讀首頁數字與 `home.js`、`app.js` 的統計邏輯 | 少於 10 台只顯示「2/2」不換算百分比；統計說明三語都加上「自願分享、無法逐台驗證」 | 假資料 2 台與 12 台各測一次 |
| 4 | 文案說得比證據滿：首頁說晶片「會出錯一次」（像是所有 AMD 都會）、「大部分電腦沒有症狀」、「不用擔心封號」 | 對照實際只有 2 台資料 | 改成「可能會出錯、出錯不一定有症狀」；封號 FAQ 改成「想不到理由，但無法替 Riot 保證」；三語＋HTML meta 一起改 | `node tests/run.mjs` 三語欄位一致 |
| 5 | 淺色模式對比不足：橘色標題與 kicker 2.9:1、灰色小字 3.8:1 | 用 JS 算前景／背景的對比 | 新增文字專用的 `--c-tpm-text`（淺色 `#b23c0a`、深色 `#e0632f`），圖表仍用原本的 `--c-tpm`；淺色 `--text-3` 調成 `#67665f` | 淺色最差 4.57:1（漸層最深處），深色最低 4.97:1 |

**跟 guidance 有沒有關係（推測，沒驗證）**：從檔名看，guides 裡有幾篇可能涵蓋這些問題，
例如 `css/css-layout.md`、`ui-atoms/single-line-overflow.md`、`ui-atoms/responsive-table.md`（#1、#2），
`visual-design/color.md`、`visual-design/dark-mode.md`、`accessibility/accessibility.md`（#5）。
**這些 guide 我一篇都沒讀**，只是依名稱推測；#3、#4 是資料誠實度與文案問題，本來就不在前端 API 的範圍，
預期 guidance 幫不上。

**這次 unguided 沒抓到、留著的問題**（之後比對時看 guidance 會不會提）：圖表沒有文字替代（`role="img"` 卻沒有 `aria-label`）、
外部 Google Fonts 與「匿名」的隱私說法衝突、沒有 CSP、帶指紋的靜態檔沒設長快取、手機上的總覽圖難讀、英文使用者的連結預覽是中文。

### 2026-11-25（同一天稍晚）：實際跑 CLI，對照上面的基準線

**做法**：`npm pack modern-web-guidance@1.0.2` 解到暫存資料夾，先讀遙測程式碼，再用 `DISABLE_TELEMETRY=1` 直接執行 CLI。
網站用 `git clone` 另外取出修改前的 `85d7b5b`，不動正在部署的那份。**沒有用 `install` 裝成全域 skill**，
因為 SKILL.md 寫著每個前端任務「MANDATORY」先查，裝了會影響所有 session，包括同時在跑的網站 session。

**遙測（讀原始碼確認，不再只是 README 的說法）**：

- `DISABLE_TELEMETRY` 設成 `1` 或 `true` 時，連背景程序都不會啟動（`modern-web.mjs` 的 `isTelemetryEnabled`）
- 沒關的話，會開一個獨立的 watchdog 程序，送到 `https://play.googleapis.com/log`（Google Clearcut，log_source 2921），
  內容是：搜尋字串與結果 ID、取回的 guide ID、作業系統、版本、agent 名稱（`@vercel/detect-agent` 偵測）、分級後的延遲。
  沒看到送出檔案內容或路徑。`legacy-scan` 只回報指令類型與成功與否
- `legacy-scan.mjs`（5 MB）裡的 CDN 網址是偵測用的比對字串，沒有對外連線

**`legacy-scan`（0.6 秒，15 個檔案，52 條規則）抓到 3 項，跟基準線的 5 項零重疊**：

| guide | 位置 | 評估 |
|---|---|---|
| `custom-text-decorations` | `style.css` 的 `.src-link a` 用 `border-bottom` 做虛線底線 | 可改 `text-decoration` + `text-underline-offset`。但它是 `inline-flex`，依 guide 自己的排除規則可能算誤判 |
| `dynamic-sibling-animations` | `.viz.st-7 .fb:nth-of-type(2)` 等逐一設 `animation-delay` | 可改 `sibling-index()`，但瀏覽器支援還不普及，要留原本的寫法當備援，價值低 |
| `js` | `app.js` 的 `box.innerHTML = ''` | 改 `replaceChildren()`，小但正確，之後若加 Trusted Types 會用到 |

三項都是「寫法現代化」，不是使用者會遇到的問題。

**`search`／`retrieve`（每次約 0.5 秒）對照基準線**：

| 基準線的問題 | 搜尋命中 | guidance 怎麼說 | 跟我的修法比 |
|---|---|---|---|
| #1 標頭溢出 | `single-line-overflow`、`form-factor-adaptation`、`css-layout` | 彈性項目預設不縮到內容以下，`overflow: hidden` 就能讓它縮；**要在 320 px 也不溢出**（WCAG 1.4.10）；觸控裝置看不到被截掉的字，要另外提供完整文字 | 修法一致。**補漏**：我只測到 360 px。補測 320 px 也沒溢出，但三種語言的品牌名都會被截掉（英文只剩 114/190 px），觸控使用者沒辦法看到全名 |
| #2 統計表溢出 | `responsive-table`、`form-factor-adaptation` | 表格可以在自己的框內橫向捲動，但**那個框要 `tabindex="0"`、`role="region"`、有名稱**，鍵盤才捲得動 | 修法一致。**補漏**：320 px 下有 6 個可橫向捲動的框（4 個表格、範例輸出、指令），全都沒有這三樣。新版 Chrome 會自動讓捲動框可以聚焦（我的記憶，這次沒驗證），但名稱與 role 還是缺 |
| #3 小樣本百分比 | 無（搜「display statistics percentage」只回不相關的 guide） | — | 預期之內：這是資料誠實度，不是網頁 API |
| #4 文案過度宣稱 | 無 | — | 同上 |
| #5 淺色對比 | `color`、`dark-mode` | 一般文字 4.5:1、大字 3:1；`dark-mode` 的範例本來就把 `--color-brand` 和 `--color-brand-text` 分開 | 修法一致（我也是拆出 `--c-tpm-text`）。另外提到：可用 `light-dark()` 免去兩份重複的深色區塊；沒處理 Forced Colors（Windows 高對比）模式 |

**基準線沒處理的 6 項，guidance 都有具體做法**：圖表用 `<figure>`／`<figcaption>` 或 `aria-describedby` 加文字說明，並提供資料表當替代（`accessibility`）；
字型自架並裁子集（`performance`），第三方資源要列入隱私稽核（`privacy`）；CSP 用 nonce／hash 加 `frame-ancestors 'none'`，再考慮 Trusted Types（`security`，篇幅大、要分階段）；
帶指紋的靜態檔用快取優先（`performance`）。

**成本**：這次取回 11 篇 guide 共約 194 KB（粗估 5 萬 token）。`accessibility` 一篇就 52 KB。
SKILL.md 要求「大輸出要整份讀」，全域安裝後每個前端任務都會吃掉這種量級的 context。

**結論：有區別，但跟 README 的「+40pp」不是同一種。**

- 5 個主要問題沒有一個是 guidance 先抓到的。`legacy-scan` 完全沒碰到它們，兩個資料誠實度問題本來就不在範圍內
- 價值在**補漏與給具體修法**：320 px 的標準、捲動框的鍵盤可及性、圖表替代文字的做法，這些我第一輪沒做到或只知道「有問題」、不知道該怎麼修
- 它證實我的三個修法是主流做法，這也有用：少一個「我的修法對不對」的疑問
- **限制**：這次是我已經知道答案之後再去查，不是盲測。裝了 skill 的 agent 會不會自己「發現」這些問題，還是沒驗證

### 2026-11-25（第三輪）：盲測，A／B 兩組對照

**設計**：

- 開兩個沒看過這段對話的 subagent，同模型（Opus 5.5）、同一段指令：「review 這個網站，找出應該修改的地方，然後直接修改你認為值得修的」
- 兩組各拿一份 `85d7b5b` 的副本：用 `git archive` 取出、重新 `git init`，看不到之後的修正 commit；兩組都被要求不能讀 `D:\AIWorkplace`
- 兩組都不能用瀏覽器：瀏覽器窗格只有一個，平行跑會互相干擾
- **A 組**多一段：讀本機的 SKILL.md 並照流程做，CLI 用 `node …/modern-web.mjs`，強制 `DISABLE_TELEMETRY=1`。**B 組**沒有

**成本**（task 通知裡的數字）：

| | B 無 guidance | A 有 guidance |
|---|---|---|
| token | 22.9 萬 | 37.4 萬（+63%） |
| 工具呼叫 | 76 | 128 |
| 時間 | 8.7 分 | 17.7 分 |
| 修改 | 1 個 commit，12 檔，+102／−49 | 5 個 commit，17 檔，+303／−105 |
| 測試 | 32 → 35 項 | 32 → 37 項 |

**對照基準線（第一輪，我＋瀏覽器）的 11 項**（用 diff 確認，不只看它們的報告）：

| 基準線的問題 | 我 | B | A |
|---|---|---|---|
| 英文標頭溢出 | 修 | 修 | 修 |
| 統計表手機溢出 | 修 | — | — |
| 小樣本 100% | 修 | — | — |
| 文案過度宣稱 | 修 | — | — |
| 淺色對比 | 修 | — | — |
| 圖表沒有名稱 | 發現 | — | 修 |
| 外部字型與隱私 | 發現 | — | 查過，認為不用改 |
| CSP | 發現 | — | 部分（加了 `frame-ancestors`、`object-src`、`base-uri`，沒加 `script-src`） |
| 捲動框鍵盤可及 | guidance 補 | — | 部分（`<pre>` 有，表格沒有） |
| 靜態檔快取、手機總覽圖、英文連結預覽 | 發現 | — | — |

**兩個 agent 都抓到、我第一輪漏掉的**：

- **調查頁的 XSS**（嚴重）：拖進來的結果檔裡，`verdict` 和每場的時間沒有跳脫就進 `innerHTML`／圖表 tooltip（`app.js` 的 `renderMine` 與 `chart-mine`）。做一個惡意 txt 騙人拖進來，就能在網站上跑 script，例如把下載按鈕換掉。我第一輪說「沒找到 XSS」是錯的：我只檢查了統計 API 那條路，沒檢查「使用者自己拖進來的檔案」這條路。兩組修法相同，都已用 diff 確認
- 手機上調查頁回不到首頁（導覽列整排被 `display:none`）
- 網頁、伺服器、腳本三邊的中位數算法不同
- 主題要等頁尾 JS 才套用，會閃一下
- 分享 API 的 32 KB 上限，用分塊傳送可以繞過
- `stamp-assets.py` 在 Windows 寫出 CRLF，指紋跟實際內容對不上

**只有 B 抓到的**（後端與資料一致性）：

- 限流用的 IP 雜湊鹽寫死在公開原始碼，IPv4 可以全部試一遍反推出 IP
- 網頁顯示結果檔自己寫的判定，伺服器卻重算，兩邊會不一致（A 看到了，但判斷是設計選擇，沒修）
- 伺服器沒擋「出錯場次 > 能判斷場次」
- 網址 hash 有壞掉的 `%xx` 時首頁會整頁空白

**只有 A 抓到的**（A 自己說大多是 guide 帶出來的，前端語意與可及性為主）：

- 缺 `<meta name="color-scheme">`，根層級寫死 `color-scheme: light`
- 大圖 lightbox 不能用鍵盤開、沒名稱、沒關閉鈕
- 縮圖沒寫寬高，捲動時版面被往下推：這就是 DEVELOPMENT.md 裡「捲完再對齊一次」那個繞法要處理的根本原因
- 進度條改原生 `<progress>`；切換按鈕補 `aria-pressed`；拖放框改原生 input
- 複製失敗也顯示「已複製」；捲動容器切掉焦點外框
- 加了不會弄壞頁面的安全標頭

**結論**：

1. **guidance 有效，效果集中在前端語意與可及性**：A 比 B 多抓了約 12 項，大多屬於這一類，修法也比較貼近標準寫法（`closedby`、`<progress>`、popover 選單）
2. **代價**：token 多 63%、時間是兩倍
3. **它不能取代其他角度**：
   - 兩組都沒抓到我用瀏覽器看出來的對比、溢出、資料誠實度、文案問題
   - 最嚴重的 XSS 兩組都抓到了，所以那是「逐行讀程式碼」的功勞，不是 guidance
   - A 漏掉了 B 抓到的鹽寫死。是不是因為注意力被 guidance 分走，樣本只有一次，**這是推測**
4. **最好的組合**：瀏覽器實測一輪（看得到的問題）＋逐行讀程式碼一輪（安全與資料流）＋需要時開 guidance 做前端語意那一輪。三輪各抓到別人沒抓到的東西

**這次的限制**：

- 每組只跑一次，同模型也有隨機性
- A 是被指示照 SKILL.md 做，不是 skill 自己觸發
- 兩組都不能用瀏覽器，跟基準線的條件不同
- 「哪些是因為 guide 才發現」是 A 的自我回報

兩組的修正匯出成 patch，放在 `An_Cl/blind-review-patches/`（不在知識庫裡）。

**兩組 patch 最後怎麼用**（2026-11-25 已部署）：網站的 session 沒有整包套，而是逐項挑選、手動合併：

- XSS：在讀檔時整理欄位型別（verdict 只收四種已知值），顯示前再過濾一次，tooltip 跳脫。正式站拖進惡意檔，script 沒有執行
- 採用 B 的：網頁判定用目前規則重算、限流改用祕密鹽、伺服器擋「出錯比可判斷多」、hash 解碼防呆、重選同檔、手機保留回首頁、首次繪製前套用主題、stamp-assets 固定 LF
- 採用 A 的：邊讀邊數的請求大小上限（含 delete）、「你的結果」中位數跟腳本一致、安全標頭、鍵盤可開的大圖、`aria-pressed`、複製失敗不再顯示已複製
- 沒採用的：A 的彈出選單（改用 B 的最小版）、A 的主題同步行為、原生檔案欄位與 `<progress>`（可有可無，先不做）

兩組各自抓到的東西最後都有用上，這也支持上面「多個角度互補」的結論。

## 下一步

- [x] ~~盲測~~：已完成，見上面第三輪
- [x] ~~網站要先修 XSS~~：已修並部署（2026-11-25），正式站實測過
- [x] ~~網站後續~~：第二輪三項在 `8ca65cc`，兩組 patch 的挑選項目在之後的 5 個 commit，一起部署
- [ ] 想知道「裝了會不會自己觸發」：在不重要的專案裡用 project 範圍安裝一次，觀察 agent 什麼時候會主動去查
- [x] ~~試之前先讀遙測程式碼~~：已讀，見上面
- [x] ~~試用期間設 `DISABLE_TELEMETRY=1`~~：這次全程都有設
- [ ] 試用場景選 wifi 時間軸網站：同一個前端小改動，有裝／沒裝各做一次，比較程式碼差異與多花的時間，不要信 +40pp
- [ ] 如果採用：想清楚要不要接受「每個前端任務都先搜尋」與結尾揭露區塊，不想要的話改 SKILL.md 的觸發描述前要先評估
- [ ] 含真實個資的專案不要啟用，或確認關閉遙測並限制 query 內容

## 相關

- [Repo 閱讀筆記總覽](README.md)
- [Graphify](graphify.md) — 同樣是「補 agent 在某一塊的不足」的 skill，同樣是作者自己的 benchmark，審查心態一樣
- [Agent-Reach](agent-reach.md) — 反例：補的是 agent 本來就有的能力
