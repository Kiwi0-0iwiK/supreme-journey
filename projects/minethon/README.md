# Minethon - Minecraft Bot

> 狀態：🟡 進行中
> 開始日期：2026-07-02

## 目標

搞懂 [Hack-the-SDGs/minethon](https://github.com/Hack-the-SDGs/minethon) 這個 repo 在做什麼，
並學習用 Python 透過 mineflayer SDK（經由 JSPyBridge）操控 Minecraft bot。

## 進度

- [x] 讀懂 minethon repo 架構與目的
- [ ] 學 Python mineflayer SDK
- [x] 學 JSPyBridge（Python ↔ JS 橋接原理）——追 emitter 位移 bug 時順便搞懂的
- [x] 跑起第一個能動的 bot
- [x] 貢獻回上游 repo（issue + PR，含審查往返）

## 筆記 / 想法

- 環境卡點：PATH 被 hermes 安裝器塞的 venv 劫持、minethon 需要 Python 3.14+（用 `uv` 自動解決）、MC server 需要 Java 25+（用 Prism Launcher 內建的 JRE）
- minethon 綁定的 mineflayer 版本目前只支援到 MC **1.21.11**，太新的伺服器版本（如 26.2）會出現 `No data available` 錯誤
- 本地測試伺服器記得 `online-mode=false`，不然假帳號連不進去
- **dig 偵錯戰記（2026-07-02）**：bot 揮手但方塊不破——真凶是 vanilla `spawn-protection`，完整排錯過程見 [debug-log-dig.md](debug-log-dig.md)（已修復，main.py 正常運作）
- **EventAdaptor 學習 + on_chat bug（2026-07-02，草稿）**：`on_chat` 收到的第一個參數其實是 bot 自己（emitter），不是 username——minethon 自己的 bug，最新版依然存在。過程見 [debug-log-eventadaptor.md](debug-log-eventadaptor.md)（草稿，待整理），issue 已送出見 [issue-draft-on_chat-emitter.md](issue-draft-on_chat-emitter.md)（[#26](https://github.com/Hack-the-SDGs/minethon/issues/26)）
- **PR 已送出、審查中**：全事件稽查後確認 `chat`／`whisper`／`resourcePack` 三個都中同款 bug，改用查表機制修正，內容見 [pr-draft-real-argc-table.md](pr-draft-real-argc-table.md)（[#27](https://github.com/Hack-the-SDGs/minethon/pull/27)）。收到 `greptile-apps[bot]` 兩則審查意見（缺 whisper 測試、查表失敗要有退路）已修正推上去，過程中也學到一個判斷準則：猶豫要不要多寫防禦性程式碼時，先問有沒有原始碼證據支持，沒有就先不寫（呼應 `AGENTS.md` 的 Source-Verified 原則）
- 程式碼位置：`D:\AIWorkplace\An_Cl\minethon\`（clone 下來的，跟 knowledge-base 分開）

## 相關資源

- https://github.com/Hack-the-SDGs/minethon
