# HyperFrames — 用 HTML 寫影片、給 agent 用的渲染框架

> Repo：[heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) · 類型：影片生成
> 證據強度：🟡 只讀文件（README、`AGENTS.md`、`hyperframes-core` 的 SKILL.md），沒安裝、沒渲染過 · 看過日期：2026-10-06
> 結論：觀望 — 設計得很扎實，但目前沒有要做的影片；真有需求時先試 `/pr-to-video`

## 這是什麼

一個把 **HTML + CSS + 媒體 + 可 seek 的動畫** 渲染成**確定性 MP4** 的開源框架。
標語是 "Write HTML. Render video. Built for agents."

賣點不在渲染本身，在於**它是為 coding agent 設計的**：agent 不用學 React 或影片剪輯軟體，
只要會寫 HTML，加上 repo 內附的 21 個 skill 教它完整的製作流程（規劃 → 寫 HTML → 接動畫 → lint → 預覽 → 渲染）。

| 項目 | 內容 |
|---|---|
| 作者／組織 | HeyGen（做 AI 數位人影片的公司） |
| 建立 / 最後 push | 2026-03-10 / 2026-10-06（看過當天還有 push，最新 release v0.8.135，仍在 0.x） |
| 星數 / fork | 57,350 / 5,132（2026-10-06，GitHub API） |
| 授權 | Apache-2.0 |
| 語言 / 技術棧 | TypeScript、Bun、無頭 Chrome（Puppeteer）＋ FFmpeg；需要 Node 22+ |
| 開放 issue | 177 |

## 結構

**14 個套件**（`packages/`），分層大致是：

| 層 | 套件 |
|---|---|
| 使用者入口 | `cli`（`npx hyperframes ...`）、`studio` + `studio-server`（瀏覽器剪輯介面） |
| 核心 | `core`（型別、解析、runtime）、`parsers`、`lint`、`player` |
| 渲染 | `engine`（無頭 Chrome 逐幀擷取 + FFmpeg）、`producer`（完整管線，含音訊混合） |
| 雲端渲染 | `aws-lambda`、`gcp-cloud-run`（examples 另有 `k8s-jobs`） |
| 其他 | `sdk`、`sdk-playground`、`shader-transitions` |

repo 根目錄同時放著 `.claude-plugin/`、`.codex-plugin/`、`.cursor-plugin/`、`gemini-extension.json`，
跟 [superpowers](../../projects/agent-harness-study/superpowers.md) 一樣是多 agent 平行打包。

### 核心概念：composition 契約

一個 composition 就是一份 HTML：

- 用 `data-*` 屬性宣告時序（`data-start`、`data-duration`、`data-track-index`），元素加 `class="clip"`
- 動畫 runtime 必須**可 seek**：每個 composition 只註冊**一條暫停的 GSAP timeline**，
  放在 `window.__timelines["<id>"]`，渲染器逐幀 seek 過去截圖
- 媒體（`<video>`／`<audio>`）的播放由框架接管，不能自己控制
- **確定性規則**：不能用即時時鐘、未設種子的 `Math.random`、網路請求；
  渲染長度以根節點的 `data-duration` 為準，不是 timeline 長度

「相同輸入 → 相同影片」就是靠這組限制換來的。

### 21 個 skill

| 類別 | 內容 |
|---|---|
| Router | `/hyperframes`：先讀這個，它確認需求，再分流到對應 workflow |
| 創作 workflow（10） | `product-launch-video`（網站 → 宣傳片）、`faceless-explainer`、`pr-to-video`（GitHub PR → 說明影片）、`embedded-captions`、`talking-head-recut`、`motion-graphics`、`music-to-video`、`slideshow`、`general-video`、`remotion-to-hyperframes`（從 Remotion 移植） |
| 領域 skill（9） | `core`、`animation`、`keyframes`、`creative`、`media-use`、`cli`、`audio`、`registry`、`figma` |

設計上的細節：**核心 skill 先裝，創作 workflow 要用時才由 router 按需安裝**，
避免一次把 21 個全塞進 context。這跟 superpowers 實測出來的「常駐成本要壓低」是同一個考量。

另有 `frame.md`：把網頁用的 `design.md` 設計規範「翻譯」成適合影片畫面的版本（字級、構圖、品牌色）。

## 怎麼用

```bash
# 不透過 agent，手動
npx hyperframes init my-video
cd my-video
npx hyperframes preview     # 瀏覽器預覽，有熱重載
npx hyperframes render      # 輸出 MP4

# 透過 Claude Code
claude plugin marketplace add heygen-com/hyperframes
claude plugin install hyperframes@hyperframes
# 之後用 /hyperframes:hyperframes
```

驗收指令：`npx hyperframes check`（lint、runtime、版面、動態、對比度五類檢查，要 0 findings）。

## 跟我的關係

- **目前沒有明確需求**，所以不裝。這份是「知道有這個東西」的紀錄。
- 可能用得到的場景（⚠️ 推測，沒驗證過）：
  - `/pr-to-video`：把牙醫系統或 minethon 的 PR 做成說明影片。它靠 `gh` CLI 讀 PR，這個環境本來就有
  - `product-launch-video`：做作品集裡專案的展示片
- 環境檢查：Node 是 v22.23.2，符合；**FFmpeg 沒裝**（`ffmpeg` 找不到指令），要試之前得先裝。
- 它的 `AGENTS.md` 很值得抄的一點：**把「踩過的坑」放在 skill 最前面**
  （例如 `gsap_css_transform_conflict`、`<audio>` 沒有 id 渲染出來會是靜音），而且每一條都對應一個 lint 規則。
  「文件裡的禁令同時是自動檢查」是比純文字規範可靠得多的做法。

## 證據與限制

- **做過的**：用 `gh api` 取得 metadata（星數、授權、建立日、最新 release）和 `packages/`、`skills/` 目錄清單；
  讀完 README 前 200 行、`AGENTS.md` 前 60 行、`hyperframes-core/SKILL.md` 前 120 行
- **沒做的**：沒安裝、沒渲染過任何影片、沒讀 `engine`／`producer` 的原始碼，
  所以「確定性」這個核心宣稱是**文件說的，不是我驗證的**
- 一開始的概覽是 WebFetch 小模型摘要，數字後來都用 `gh api` 重新核對過；
  摘要裡寫的「5,279 commits」和「tldraw、TanStack 採用」我沒核對，這份筆記沒有採用
- 還在 0.x 版、release 頻繁（看過當天剛出 v0.8.135），API 可能還會變

## 下一步

- [ ] 想試的時候先 `winget install ffmpeg`（或同類），再 `npx hyperframes init` 跑一次官方範例，
      驗證「同樣輸入渲染兩次，輸出是否逐位元相同」
- [ ] 讀 `packages/engine` 的逐幀擷取流程，看確定性是怎麼保證的
- [ ] 對照 Remotion（React 版的同類東西），它專門做了 `remotion-to-hyperframes` 移植，可見是直接對標

## 相關

- [Repo 閱讀筆記總覽](README.md)
- [superpowers](../../projects/agent-harness-study/superpowers.md) — 同樣是 skill 多平台打包、同樣在乎 context 成本
- [Agent-Reach](agent-reach.md) — 同類型「給 agent 加能力」的 repo，但那邊的結論是不值得裝
