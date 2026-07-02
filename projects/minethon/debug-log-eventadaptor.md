# EventAdaptor 學習 + 偵錯戰記（草稿，尚未整理完）

> 日期:2026-07-02
> 狀態:**草稿**——內容是照對話順序記的，之後有空要重新編排成更精簡的版本
> 環境:minethon 0.3.6 / mineflayer 4.37.0 / JSPyBridge (`javascript` pip 套件) / Node.js 22.23.0 / Windows

## 背景:什麼是 EventAdaptor

跟之前用的 `bot.dig()`、`bot.move_forward()` 這種「指令式」（你主動呼叫、等結果，是「拉」）不一樣，
`EventAdaptor` 是「事件式」（先寫好「如果 X 發生就做 Y」，程式交出控制權給 `bot.run_forever()`，
遊戲世界主動通知你，是「推」）。

`EventAdaptor` 本身（`src/minethon/_handlers.py:62`）只是一個全部方法都是空殼（`pass`）的基底類別，
由 `scripts/generate_stubs.py` 從 mineflayer 的事件清單自動生成。
`bot.bind(你的實例)`（`_bot_runtime.py:313`）會掃過所有 `on_<event>` 方法，
只挑出「你真的覆寫過」的（跟空殼比對函式身份），把它們跟底層 JS 的 EventEmitter 掛鉤。

## Bug 1（自己的失誤）:條件寫反

第一次寫：
```python
def on_chat(self, username, message,*_):
    if username != bot.username:   # 應該是 ==
        return
    if message == "quit":
        bot.quit("bye")
```
邏輯反了：`!=` 代表「只要不是 bot 自己講話就跳過」，結果變成永遠不會處理玩家自己打的訊息。
改成 `==`（跳過 bot 自己講的話，處理其他人的話）後，`quit` 依然沒反應——代表還有第二層問題。

## Bug 2（minethon 本身的真實 bug）:emitter 物件卡進第一個參數

### 症狀

加了偵錯 print 後發現，`on_chat` 收到的 `username` 根本不是字串，而是一整包 JS 的 `EventEmitter`
物件（就是 bot 自己）。所有參數往後推了一格，`quit` 判斷式永遠比對不到正確字串。

### 排查過程

1. 懷疑是不是背景程序沒關乾淨——用 `ps -W` 找到真正的 Windows PID（跟 Cygwin/MSYS 的 `ps -W`
   第一欄不是同一組編號，要用 `Get-Process` 對照的 `Id` 欄位才抓得到真正能 `Stop-Process` 的 PID）。
2. 寫了一個「探針 bot」（另開一支 script，用不同帳號連進同一個伺服器，主動送出 chat "quit"），
   搭配主角 bot 一起跑，這樣不用手動在遊戲裡打字，也能重現/驗證。
3. 中途遇到一個無關的干擾:Windows 終端機用 cp1252 編碼，印不出某些 emoji（例如 uv 自己印的 🐍），
   導致 JSPyBridge 讀 log 的背景執行緒（`com_io`）crash。設 `PYTHONUTF8=1` / `PYTHONIOENCODING=utf-8`
   排除這個雜訊,才能專心看真正的 bug。
4. 確認即使把簽名改成 README 教的完整版 `def on_chat(self, username, message, translate, json_msg, matches)`
   （5 個參數），emitter 還是卡在第一格,證明不是 `*_` 這個寫法本身的問題,問題更根本。

### 根本原因:`_normalize_handler` 的兩個偵測法都失效

檔案位置：`src/minethon/_bot_runtime.py:141`。這個函式想要「剝掉」JSPyBridge 塞在最前面的
emitter 參數，用兩種方式判斷要不要剝：

- **身份比對**（`args[0] is emitter`）：失敗，因為 JSPyBridge 每次給的 proxy 物件是新複製品，
  不是同一個 Python 記憶體實例（`is` 比對的是「同一張紙」不是「內容相同」）。
- **數量比對**（`len(args) > slots`，且只在沒用 `*args` 收尾時才檢查）：也失敗。
  去讀 mineflayer 原始碼 `lib/plugins/chat.js:85` 證實：`chat` 事件透過
  `LEGACY_VANILLA_CHAT_REGEX`（只有 2 個捕獲群組）驅動，**永遠、固定只送 4 個真實參數**
  （username, message, translate, 原始訊息物件），型別宣告上寫的第 5 個 `matches` 根本不存在。
  加上 emitter，箱子大小 = 1+4 = 5，剛好等於你宣告 5 個參數的 `slots`。
  `5 > 5` 是 `False`，數量比對永遠不會觸發。

兩種偵測法剛好都在這個特定的參數數量組合下失效，emitter 就這樣直接卡進了 `username` 位置。

### 確認不是版本問題

- mineflayer npm 上最新穩定版是 **4.37.1**（我們釘的是 4.37.0），`chat.js` 那段程式碼完全沒變。
- minethon GitHub `main` 分支目前的 `_normalize_handler`，跟我們裝的 0.3.6 版**逐字相同**。
- 結論：**現在最新版依然有這個 bug**，不是舊版遺留、也不是我們裝壞了環境。

### Workaround

不要依賴自動偵測，自己在簽名最前面多開一個「垃圾桶」參數位置：
```python
def on_chat(self, _leading, username, message, translate=None, json_msg=None, matches=None):
```
因為宣告的參數數（6）比箱子實際大小（5）多，Python 會自動在**箱子尾巴**補一個 `None` 湊數，
emitter 自然落在 `_leading`（丟掉不用），其餘位置正確對齊。

**這個 workaround 的限制**：只有在「缺的/多的東西剛好在最尾端」時才有效。
如果哪個事件缺的是中間那個參數,這招完全救不了——`_normalize_handler` 只會截斷/填補尾巴，
沒有「指定第幾個位置該是什麼」的能力。真遇到這種狀況只能：
① 去改 minethon 原始碼、幫每個事件寫死正確的參數數量對照表，或
② 繞過 `bot.bind()`，自己直接對 JS 的事件掛原始 handler，手動處理。

## 順便學到的:Python / Node.js / JSPyBridge 到底是什麼關係

用 `ps -W` 實際觀察跑腳本時的系統程序，證實：`uv run python xxx.py` 執行後，
背地裡真的另外啟動了一個獨立的 **`node.exe`** process（時間戳跟 Python 那兩個一致）。

- **Python**：你寫的邏輯（`bot.dig()`、`on_chat` 這些）活在這裡，完全不懂 JavaScript。
- **Node.js**（獨立的 process）：`mineflayer` 是純 JS 套件，真正的網路連線、封包收發、
  事件判斷全部發生在這個獨立的程序裡，Python 自己什麼都不知道。
- **JSPyBridge**：在兩個獨立 process 之間開一條管道（stdin/stdout），定義一套訊息協定，
  讓兩邊可以互相「叫對方做事」或「通知對方發生了什麼事」。

終端機那些 `[JSE]` 開頭的行，就是 Node.js 那個獨立 process 自己印的東西，
被 JSPyBridge 轉播進 Python 這邊的終端機。

### 「拉」不是只有一種形式

- **單純一問一答**：`bot.chat(...)`、`bot.dig()` 內部的每一步——Python 問一次，Node 回一次。
- **問到滿意為止（輪詢）**：`bot.move_forward(3)` 內部（`_commands.py:361`）是不斷迴圈問
  Node「你現在座標多少」，問到走了 3 格才停，背後可能是幾十次過橋，不是一來一回。
- **拉的外殼包著推的引擎**：`bot.wait_spawn()`（`_commands.py:204`）看似「問一次等答案」，
  實際上是內部建立一個純 Python 的 `threading.Event`，註冊一個「推」型的一次性事件監聽
  （`Once(self._js, "spawn")`），等 Node 那邊真的 spawn 了才主動通知回來，喚醒卡住的 Python 執行緒。

`get_pos()`（`_commands.py:259`）也提醒了一件事：讀 JS 物件的屬性（`.entity`、`.position`、
`.x`/`.y`/`.z`）**每一次都要過橋**，不是本地讀變數，代表輪詢迴圈裡頻繁讀取座標是有真實
效能代價的（不是免費操作）。

## 全事件稽查（2026-07-02，為了規劃 PR 而做）

`chat` 這個 bug 回報出去後（[issue #26](https://github.com/Hack-the-SDGs/minethon/issues/26)），
想知道 `EventAdaptor` 其他 96 個事件是不是也有同款地雷，逐一比對「mineflayer 真實送幾個參數」
vs「minethon 宣告的 slots 數」：

- 寫腳本抓 97 個事件 → 75 個能用字面字串在 mineflayer 原始碼直接找到 `emit()`，
  22 個是動態組出事件名稱（`chat` 就是其中之一）
- 第一版腳本用簡單正則抓參數，會被巢狀函式呼叫（例如 `parseTitle(packet.text)`）騙到、漏算，
  導致 `note_heard`、`title` 兩個假警報——改用真正的括號配對重寫才修掉
- 22 個動態事件全部手動追進原始碼確認

**結論：97 個裡確認 3 個真的中獎，都是同一個模式（真實參數 + 1 個 emitter 剛好等於宣告的 slots）：**

| 事件 | 真實參數 | 宣告 slots | 成因 |
|---|---|---|---|
| `chat` | 4 | 5 | legacy `addChatPattern(..., {deprecated:true})` |
| `whisper` | 4 | 5 | 跟 chat 同一條程式碼路徑，同款病 |
| `resource_pack` | 2 | 3 | `resource_pack.js` 三個呼叫點都固定送 2 個 |

其餘：`block_update`/`chunk_column_load`/`chunk_column_unload`（世界事件轉發）、
11 個 entity 狀態/動畫事件、5 個 pathfinder 事件——全部安全，真實參數+1 明顯小於宣告 slots，
裁切機制正常運作。`unmatched_message` 在原始碼裡完全找不到對應 `emit()`，可能型別宣告了但沒實作。

## 額外發現:`*_`（varargs）寫法會讓兩條舊判斷同時失效

修好 `chat` 之後拿 `examples/bot01/EventAdaptor.py` 實測，該檔案的 `on_chat` 是這樣寫的：

```python
def on_chat(self, username, message, *_):
```

追進舊版 `_normalize_handler` 才發現：`arity_excess = not accepts_varargs and len(args) > slots`
這一行，只要 handler 用了 `*_`（`accepts_varargs = True`），`not accepts_varargs` 就鎖死在
`False`，**整個 `arity_excess` 永遠不會是 `True`，跟箱子裡實際塞了幾個東西完全無關**。再加上身份比對
（`args[0] is emitter`）本來就永遠失敗，代表：**只要 handler 用 `*_` 這種很常見的「接住其餘參數」寫法，
剝除 emitter 這件事無論如何都不會發生**——不是「剛好某個事件的參數數字撞上邊界」才會中獎，是這個寫法
本身直接讓兩條舊判斷路徑同時失效，範圍比原本以為的 3 個邊界巧合案例還要廣（理論上對其餘 94 個事件，
只要使用者用 `*_`，一樣會遇到同樣的繞過問題，只是還沒一一驗證）。

用這個檔案代入舊邏輯手動算過：`username` 會收到 emitter（不是玩家名），`message` 會收到**玩家的帳號
名稱**（不是聊天內容）——所以舊版這支範例其實只有在**發訊息的玩家帳號本身叫 "quit"** 時才會觸發離開，
打字打「quit」這個詞完全沒用。修完 `_normalize_handler`、改用查表判斷之後，因為新邏輯完全不看
`accepts_varargs`，`*_` 寫法也能正確運作，測試打字「quit」bot 正確離開，驗證通過。

這個發現讓「用查表取代猜測」的方向更有說服力——猜測邏輯的失效範圍比原本描述的還廣。

## PR 送出與審查（2026-07-02）

修正做成 `_REAL_ARGC` 查表機制，PR 送到 `Hack-the-SDGs/minethon` 的 `dev` 分支：
[#27](https://github.com/Hack-the-SDGs/minethon/pull/27)。完整的修正內容、查證過程、
跟 `greptile-apps[bot]` 審查往返（`whisper` 缺測試、查表失敗要有退路）、以及事後自己多想
的一個顧慮（最後靠 `AGENTS.md` 的 Source-Verified 原則想清楚不用寫防禦性程式碼），
細節都記在 [pr-draft-real-argc-table.md](pr-draft-real-argc-table.md)，不重複記在這裡。

## 待辦（草稿收尾前要做的事）

- [ ] 把「Bug 1」跟「Bug 2」的敘述再精簡一次，跟 `debug-log-dig.md` 的格式對齊
- [ ] 決定要不要把「Python/Node/JSPyBridge 關係」這段抽出來獨立成一份概念筆記（因為以後應該還會用到）
- [x] 回報上游的 issue：[#26](https://github.com/Hack-the-SDGs/minethon/issues/26)
- [x] 規劃並送出 PR：[#27](https://github.com/Hack-the-SDGs/minethon/pull/27)（把 `_normalize_handler`
      從「猜測式」改成「查表式」，涵蓋 chat/whisper/resource_pack 三個已知案例）
- [ ] 決定要不要另外開 Windows 路徑問題那個 issue（`generate_stubs.py` 在 Windows 上會壞，已發現但暫緩處理）
