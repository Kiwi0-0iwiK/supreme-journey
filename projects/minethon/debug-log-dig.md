# Dig 偵錯戰記 — bot 揮手但方塊不破

> 日期:2026-07-02
> 環境:minethon 0.3.6 / mineflayer 4.37.0 / Minecraft server 1.21.11 (vanilla, localhost)
> 結局:**不是程式 bug,是 vanilla 出生點保護(spawn-protection)靜默拒絕非 OP 玩家的破壞動作**

## 症狀

- `bot.dig()` 正常回傳方塊資訊(座標 + 名稱),無任何錯誤
- 遊戲裡看得到 bot 揮手動畫
- 但方塊沒有裂痕、沒有被破壞
- 伺服器 console 完全正常,無警告

## 排錯過程(逐層排除法)

### 第 1 層:Python 端有沒有等結果?

讀 minethon `_commands.py` 和 mineflayer `lib/plugins/digging.js` 原始碼,發現關鍵設計:
mineflayer 送出「開始挖掘」封包後自己起本地計時器,時間到就送「挖掘完成」封包,
**然後直接把自己記憶中的世界該格改成空氣**(`_updateBlockState(pos, 0)`),
這個本地修改觸發事件讓 dig 的 Promise「成功」resolve。

→ **整條成功路徑不需要伺服器同意。本地狀態不可信。**

### 第 2 層:封包有沒有送出去?

用 `$env:DEBUG = "minecraft-protocol"` 抓封包 log(node-minecraft-protocol 認這個環境變數)。

- 兩個 `block_dig` 封包(status 0 開始 / status 2 完成)都有送出,間隔符合方塊硬度計時
- 但伺服器**零回應**:沒有 `block_changed_ack`(1.19+ 伺服器對每個挖掘動作必回),
  沒有 `block_change` 糾正封包

→ 嫌疑縮小到「伺服器不認/不理這個封包」。

### 第 3 層:封包格式錯了嗎?(兩個假設都被排除)

**假設 A:缺 sequence 欄位。** 1.21.11 協定的 `block_dig` 有 4 個欄位,
mineflayer 只填 3 個,`sequence` 被序列化器補 0(vanilla 客戶端是從 1 遞增)。
驗證:寫純 Node 腳本(繞過 Python/JSPyBridge 排除變因)攔截 `client.write`
注入遞增 sequence → **依然沉默,排除**。

**假設 B:minecraft-data 的封包 ID 對照表過時。**
minecraft.wiki 查到 1.21.9/1.21.10 = 協定 773,1.21.11 = 774,協定確實變過,
而 minecraft-data 的 1.21.11 表跟 1.21.9 一模一樣,嫌疑很大。
驗證:**不用翻 wiki——server.jar 自己能吐出官方封包表**:

```powershell
java -DbundlerMainClass=net.minecraft.data.Main -jar minecraft_server.jar --reports
# 輸出在 generated/reports/packets.json
```

對照結果 `player_action = 0x28` 與 minecraft-data 完全一致 → **排除**。

### 轉折:換角度想

封包正確、送達、被解析(沒被踢線),伺服器卻「選擇」不理——
那不是技術故障,是**規則拒絕**。想到 vanilla 有個很安靜的機制:

- `server.properties`:`spawn-protection=16`(出生點 16 格內非 OP 不能破壞方塊,拒絕時**只記 debug 層級**,console 看不到)
- `ops.json`:自己的遊戲帳號是 OP → 手動挖從來沒事,完全沒察覺保護存在
- 歷次 bot 測試座標全部在出生點 16 格內

### 第 4 層:對照實驗定罪

讓 bot 走 35 格再挖,然後**用全新連線重新讀 chunk** 驗證真實方塊狀態
(不能信原連線的本地世界,見第 1 層):

| 位置 | 距出生點 | 結果 |
|------|---------|------|
| (4, 64, -4) | ~9 格 | 拒絕,方塊還在 |
| (6, 64, 30) | ~30 格 | **成功,真的變 air** |

同一套程式碼,只差距離。證畢。

## 修復

`server.properties` 改 `spawn-protection=0`,**先關伺服器再改**(伺服器關閉時會把記憶體中的設定寫回,開著改會被覆蓋),重啟後生效。

## 通用教訓

1. **「沒有錯誤訊息」本身就是線索**——真正的故障通常會噴錯,靜默失敗往往是某個規則/權限在攔。
2. **本地狀態可以說謊**——mineflayer 的 dig 成功不代表伺服器接受;驗證要用全新連線重讀,或監聽伺服器 ack。
3. **懷疑資料表錯誤時找權威來源**——官方 jar 的 data generator 比任何 wiki 準。
4. **排除變因要一層一層來**——純 Node 腳本繞過 Python 層,一次只驗證一個假設。
5. 過時的 GitHub issue 不能直接套用——issue #13 用的是 2026-04-13 重寫前的舊 async API,程式碼路徑完全不同。

## 雜項備忘

- PowerShell 5.1 的 `*>` 重導向寫出 UTF-16 檔案,Git Bash 的 grep 讀不了(ripgrep 可以)
- 腳本結束時的 `Exception in thread Thread-1 (com_io)` 是 JSPyBridge 關管道的無害雜訊
- `Remove-Item Env:DEBUG` 記得清,不然之後每次跑 bot 都噴封包 log
