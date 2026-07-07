# Minethon - Minecraft Bot

> 狀態：🟡 進行中
> 開始日期：2026-07-02

## 目標

搞懂 [Hack-the-SDGs/minethon](https://github.com/Hack-the-SDGs/minethon) 這個 repo 在做什麼，
並學習用 Python 透過 mineflayer SDK（經由 JSPyBridge）操控 Minecraft bot。

## 進度

- [x] 讀懂 minethon repo 架構與目的
- [ ] 學 Python mineflayer SDK（進行中：pathfinder / 背包物品 / 方塊放置 / 戰鬥四個角落跑過一輪，見下方 2026-07-07 筆記；合成/容器/交易/騎乘等還沒碰，見「下一步」清單）
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
- **待查 bug 筆記（2026-07-07）**：學 pathfinder 時掛 `on_path_update` 偷看內部路徑資料，`path.path`（點屬性）直接 `AttributeError`——runtime 傳來的其實是 Python `dict`，不是 `bot.pyi` 宣告的那種可點屬性物件。查過 `mineflayer-pathfinder` 的 `index.d.ts`，`PartiallyComputedPath` 是用 TS `interface` 宣告（不是 `class`），推測凡是 payload 型別在 d.ts 裡是 `interface` 的事件，過橋後大概率都是 dict 不是 proxy——跟 `chat`/`whisper`/`resourcePack` 那次 emitter 位移是同等級的系統性落差，但病灶不同（interface vs class，不是 emitter 注入）。只影響「監聽這幾個事件並想點屬性存取」的用法，`goto`/`setGoal` 這些核心移動 API 完全不受影響。還沒做全事件稽查，之後有空再確認影響範圍、決定要不要送 issue。
- **待查 bug 筆記（2026-07-07）：`bot.pathfinder.goto()` 沒設 timeout 會用 JSPyBridge 預設的 10 秒**——`goto`（跟其他沒被 `_commands.py` 包過、直接呼叫 raw JS proxy 的方法）繼承 `javascript` 套件 `Proxy.__call__` 的預設 `timeout=10`（秒），走稍遠一點（40 格）就直接 `Exception: Call to 'goto' timed out`，要手動 `goto(goal, timeout=120)` 才夠。
- **待查 bug 筆記（2026-07-07）：`placeBlock` 在有薄雪層（`snow`,非完整方塊）的地面上，座標算法會對不上**——`mineflayer` 的 `place_block.js` 用 `referenceBlock.position.plus(faceVector)` 天真地「猜」放置後會變化的座標,再死等那個精確座標的 `blockUpdate` 事件；地面被雪層佔住時,猜的座標常常跟實際變化的座標對不上,導致明明伺服器端可能已經真的放置成功（物品確實從物品欄消失）,客戶端卻永遠等不到對應事件、5 秒後穩定 timeout。換到乾淨地面（無雪）測試,`placeBlock` 完全正常。還沒去讀 mineflayer 原始碼確認雪層情境下實際變化的座標長怎樣,只是強關聯,不是證實。
- **重要待查 bug（2026-07-07）：`bot.dig()`（`_commands.py:484`）沒有覆寫 JSPyBridge 預設的 10 秒呼叫逾時,徒手挖硬方塊（石頭等）容易直接被打斷**——`self._js.dig(block)` 是裸 proxy 呼叫,同樣繼承預設 `timeout=10`。徒手挖石頭這類方塊,實際挖掘時間本來就常常超過 10 秒,一超過,JSPyBridge 直接對這次呼叫判定逾時、拋例外、腳本結束、bot 斷線——而且**斷線會真的打斷還在進行中的挖掘**,不是通知延遲的假警報,實測物品欄最後是空的,代表方塊真的沒挖成功。這個問題比另外兩個嚴重,因為 `dig()` 是特地設計給初學者「不用管 bridge 細節」的核心指令,卻沒處理這個最基本的長時間動作情境——之後應該考慮送 issue/PR，讓 `_commands.py` 對這幾個已知會長時間跑的動作（`dig`/`place`/`craft`/`fish` 等)明確傳更長的 `timeout`，而不是依賴 JSPyBridge 的通用預設值。已用下界合金鎬對照驗證：換成秒挖的工具後同一種方塊（`stone`）挖掘完全正常、無 timeout,證實純粹是「徒手挖太慢超過 10 秒」的因果關係，不是其他隱藏因素。

## 下一步 / 還沒碰過的角落（2026-07-07 整理）

還沒摸過的 mineflayer/minethon API 角落，之後想繼續學或找題目時可以從這裡挑：

- **合成（crafting）**：`bot.craft`、`recipesFor`/`recipesAll`——完全沒碰過，是「打造完整生存流程」的關鍵一塊
- **容器/箱子**：`openContainer`/`openChest`/`transfer`/`putAway`——今天只碰了玩家自己的 `bot.inventory`，箱子存取、跟其他容器互動沒試過
- **村民交易**：`openVillager`/`trade`——inbox 原本清單「實體互動」裡提過的「交易」還沒做，今天只做了戰鬥那半邊
- **騎乘**：`mount`/`dismount`/`moveVehicle`——實體互動的另一半，騎船/騎馬之類
- **更細緻的移動控制**：不透過 pathfinder，直接用 `setControlState`（潛行/疾走/跳躍）手動控制,體會跟 pathfinder 自動規劃的差異
- **盾牌/弓箭等更豐富的戰鬥動作**：`activateItem`（拉弓/舉盾）+ `deactivateItem`,今天只做了近戰 `attack`
- **告示牌/書本**：`updateSign`、`writeBook`/`signBook`
- **附魔台/鐵砧**：`openEnchantmentTable`/`openAnvil`
- **世界/區塊 API**：`bot.world`、`waitForChunksToLoad`，今天都只是間接碰到（pathfinder 的 `chunk_loaded` 事件），沒直接玩過

## 已知 bug 的後續（承上面「問題」筆記）

- 4 筆待查 bug（`dig`/`goto` 逾時、`placeBlock` 雪地座標、`path_update` dict）都還停在「發現」階段，沒有一個真的送 issue/PR——如果還要繼續深挖 minethon，這是現成的、已經有紮實佐證的題目，不用重新找 bug
- `debug-log-dig.md`／`debug-log-eventadaptor.md` 裡各留了一個「先擱著」的小尾巴（Windows 路徑問題的 issue 要不要開）也還沒決定

## 可能的專案方向（如果想做點更完整的東西）

- 串起今天學的東西做一個「自動打怪機」：`GoalFollow` 追蹤 + 血量事件判斷要不要撤退 + 死亡後自動找下一隻
- 「自動蓋房子」：`placeBlock`/`GoalPlaceBlock` + 合成，從採集到搭建走一輪完整流程
- 跟村民做簡單的自動交易迴圈，練 `trade`/容器 API

## 相關資源

- https://github.com/Hack-the-SDGs/minethon
