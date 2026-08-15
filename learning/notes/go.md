# Go 學習

> 狀態：使用中（邊做邊學）
> 動機：想寫一個能在老舊 Windows 電腦上「複製過去就能跑」的小型服務，不想在對方機器上裝執行環境

## 為什麼是 Go

需求是一個跑在單機、用 SQLite 存資料、開瀏覽器介面操作的小服務，而部署對象是一台不歸我管、也不方便安裝東西的舊電腦。Go 編譯出**單一靜態執行檔**這點直接解決了整個維護負擔——沒有 runtime、沒有 `pip install`、沒有版本衝突，複製一個 `.exe` 過去就會動。這是選它最主要的理由，語言本身漂不漂亮反而是其次。

實際寫下來，Go 的「無聊」是優點：語法少到幾天就能讀懂別人的程式碼，`if err != nil` 雖然囉嗦但看得出每一條錯誤路徑往哪走。

## 真的踩到才學會的東西

下面每一條都是實作中被 bug 或 code review 抓出來的，不是從教學文抄的。

### `*sql.DB` 是連線池，不是一條連線

這是我目前為止踩過**最有價值**的一個。直覺上 `sql.Open()` 回傳的東西「就是資料庫連線」，所以要設定 SQLite 的 pragma（例如打開外鍵約束）時，很自然會寫成開完之後 `Exec("PRAGMA foreign_keys = ON")`。

**這是錯的。** `*sql.DB` 是一個連線**池**，`Exec` 只會跑在池子當下隨便挑的那一條連線上。之後的查詢可能拿到另一條完全沒設過 pragma 的連線——於是外鍵約束時靈時不靈，而 SQLite 預設外鍵是**關閉**的，所以失效的那一半會安靜地接受孤兒資料，不報錯。

正確做法是把 pragma 寫進 DSN，讓驅動每開一條新連線都自動套用：

```go
dsn := fmt.Sprintf("file:%s?_pragma=busy_timeout(5000)&_pragma=foreign_keys(1)&_pragma=journal_mode(WAL)", path)
conn, err := sql.Open("sqlite", dsn)
```

推廣出去的教訓：**看到一個型別叫 `DB` 不代表它是一條連線**，任何「設定一次就以為之後都有效」的狀態，在連線池後面都要重新想一遍。

### `//go:embed` — 單一執行檔的關鍵

前端的 HTML/CSS/JS、還有 SQL migration 檔案，全部用 `//go:embed` 塞進執行檔裡，所以真的只需要複製一個 `.exe`：

```go
//go:embed web
var webFiles embed.FS

//go:embed migrations/*.up.sql
var migrationFiles embed.FS
```

注意 `//go:embed` 是**註解形式的編譯指令**，跟一般註解長得一樣但有作用，而且必須緊貼在變數宣告的上一行、中間不能空行。第一次寫的時候很難相信「一行註解」會改變編譯結果。

### 錯誤分類要 fail-closed，不要靠推論

一開始判斷「這個錯誤該回 400 還是 500」的寫法是消去法：不是 sqlite 錯誤、也不是 not found，那大概就是使用者輸入有問題吧 → 回 400 並把錯誤訊息原文吐給前端。

review 抓到這是 **fail-open**：以後只要有人加了一條新的內部錯誤路徑，它就會被誤判成使用者錯誤，把內部細節直接回給呼叫端。

改成 sentinel error + `%w` 包裝，只有**刻意標記過**的才算使用者錯誤，其他一律落到 500：

```go
var ErrValidation = errors.New("invalid input")

func validationErrorf(format string, args ...any) error {
    return fmt.Errorf("%w: "+format, append([]any{ErrValidation}, args...)...)
}

// 呼叫端：
if errors.Is(err, ErrValidation) { /* 400 */ } else { /* 500 */ }
```

`%w` 是「包裝」動詞（wrap），跟 `%v` 的差別在於它保留原始錯誤讓 `errors.Is` / `errors.As` 之後還追得回去。這是 Go 錯誤處理的核心機制，值得早點搞懂。

### check-then-act 的競態，用 SQL 自己解掉

「先查狀態，通過就寫入」這種寫法在多請求下會出事：查完到寫入之間，狀態可能被別的請求改掉，寫入照樣落地。

Go 這邊不一定要開交易，把守衛條件直接寫進 SQL、讓檢查跟寫入變成同一個原子操作就好，再用 `RowsAffected() == 0` 判斷「沒中」：

```go
res, err := db.Exec(`UPDATE ... WHERE id = ? AND status = 'draft'`, id)
n, _ := res.RowsAffected()
if n == 0 {
    // 補一次 SELECT，區分「不存在」還是「狀態不對」，才有像樣的錯誤訊息
}
```

但要注意這招**只在守衛條件同方向時安全**。如果守衛的是一個「一旦成立就不會再變回去」的狀態（吸收態），先查再寫其實沒問題；如果守衛的是一個**隨時可能消失**的狀態，就一定要用上面這種原子寫法。同一份程式碼裡兩種情境併存過，差點照抄錯邊。

### `*string` 當 nullable 欄位，空字串要正規化成 nil

Go 沒有內建 optional，資料庫的 nullable 欄位慣例上用指標型別表示。但 JSON 傳進來的空字串 `""` 跟「沒有值」是兩回事——`""` 存進去會佔掉唯一索引的位置，而 `NULL` 不會。所以要有一個轉換：

```go
func nilIfEmpty(s *string) *string {
    if s != nil && *s == "" {
        return nil
    }
    return s
}
```

這條在「有唯一索引、但允許多筆沒有值」的欄位上是關鍵，忘了寫就會出現「第二筆沒填身分證的資料存不進去」這種怪 bug。

### `defer` 的執行時機

`defer conn.Close()` 是在**函式返回時**執行，不是離開區塊時。在 `main` 裡很直觀，但在迴圈裡 `defer` 會一路累積到函式結束才一起跑——手寫交易的 rollback 時要特別小心，我目前是明確在每個錯誤分支呼叫 `tx.Rollback()`，而不是靠 defer。

## 環境雜記（Windows）

- 用 `winget install GoLang.Go` 裝
- **裝完之後同一個終端機/工具 session 抓不到新的 PATH**（背後是常駐 process，環境變數是啟動時快照的）。要嘛手動刷新 `$env:Path`，要嘛先用絕對路徑 `"C:\Program Files\Go\bin\go.exe"` 撐過去
- SQLite 驅動用 `modernc.org/sqlite`（純 Go 實作），不需要 CGO、不用裝 C 編譯器，交叉編譯也不會爆炸——這對「單一執行檔」的目標很重要，用 `mattn/go-sqlite3` 就會被 CGO 綁住

## 還沒碰過的

- 測試（`testing` / `httptest`）——目前整個專案零測試，是明確的下一步
- goroutine / channel 的實際應用（只知道概念，還沒有需要並行的場景）
- graceful shutdown（`signal.NotifyContext` + `srv.Shutdown`）
- 泛型

## 學習資源

- [Effective Go](https://go.dev/doc/effective_go) — 官方的慣例說明，比語法教學有用
- [Go by Example](https://gobyexample.com/) — 查「這個東西怎麼寫」很快
- `go doc <package>` — 離線查標準庫，比開瀏覽器快
