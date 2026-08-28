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

## 現代 Go 的寫法整理（1.18 → 1.27）

> 來源：JetBrains 的 [go-modern-guidelines](https://github.com/JetBrains/go-modern-guidelines)，54 條「舊寫法 → 新寫法」對照。
> 這一節跟上面那節性質不同：上面是我自己撞出來的，這一節是**讀過但還沒全部用上**的。所以整理的重點刻意不放在「新語法長怎樣」——那查文件就有——而是放在**舊寫法到底會出什麼事**。不知道它解掉什麼問題的話，這種清單就只是在背 API 名字。

**先記一個共通前提**：Go 有一批改動不是「換了新 toolchain 就生效」，而是看 `go.mod` 裡那行 `go 1.xx`。迴圈變數語意（1.22）、`for i := range n`（1.22）、ticker 的 GC 行為（1.23）都屬於這種。所以就算裝了 1.24 的編譯器，只要 `go.mod` 還寫著 `go 1.21`，**舊行為會原封不動保留**。這是刻意的相容性設計（不然升級編譯器會靜靜改掉舊程式的語意），但也代表「我裝的版本夠新所以應該有」這個推論是錯的。要用新語意就得一起改 `go.mod` 那行。

### 錯誤處理

這組解的是同一件事：**錯誤在傳遞過程中被包裝過，就認不出來了**。這類 bug 沒有編譯錯誤、沒有 panic，只有「明明該進那個 if 卻沒進去」。

#### `errors.Is` 取代 `==`（1.13）

前面 fail-closed 那條已經在用 `errors.Is` 了，這裡補的是「為什麼不能用 `==`」。

sentinel error 是 `errors.New` 建出來的**指標**，`err == target` 比的是「是不是同一個物件」。只要中間有任何一層做過 `fmt.Errorf("...: %w", err)`，回傳的就是一個**新的** `*fmt.wrapError`，指標不同，`==` 直接 false：

```go
var ErrNotFound = errors.New("not found")

func fetchUser(id int) (*User, error) {
    u, err := queryUser(id)   // 這裡回 ErrNotFound
    if err != nil {
        return nil, fmt.Errorf("fetchUser %d: %w", id, err)  // 包了一層
    }
    return u, nil
}

// 呼叫端
_, err := fetchUser(7)
if err == ErrNotFound {
    // 永遠不會進來 —— err 是 *fmt.wrapError，不是 ErrNotFound 本人
}
if errors.Is(err, ErrNotFound) {
    // 這個會進來：errors.Is 沿著 Unwrap() 一路往下比
}
```

真正陰險的是**時間差**：一開始 `==` 可能是對的（沒人包裝），跑了半年都沒事；某天有人為了補上下文而加了一個 `%w`，遠處那個 `if` 就靜靜失效了。改動的人不會意識到自己弄壞了什麼，因為那行 `if` 不在他改的檔案裡。

`errors.Is` 除了走 `Unwrap()` 鏈，也會呼叫錯誤自己實作的 `Is(error) bool`，所以像 `os.ErrNotExist` 這種「多個底層錯誤都算同一類」的情況也涵蓋得到。

**代價**：`errors.Is` 是迴圈走訪，不是常數時間的指標比較。實務上這點成本毫無意義（鏈深度通常個位數），所以沒有理由為了效能用 `==`。

#### `errors.Join` 合併多個錯誤（1.20）

要回報「兩件事都錯了」時，舊寫法通常長這樣：

```go
return fmt.Errorf("%v; %w", errClose, errFlush)
```

問題在 `%v`：`errClose` 被**攤平成字串**了。訊息裡看得到它，但 `errors.Is(err, ErrDiskFull)` 對它完全無效——只有掛在 `%w` 上的那一個還追得回去。於是變成「錯誤訊息裡明明寫著 disk full，程式卻判斷不出來」。

```go
func closeAll(files []*os.File) error {
    var errs error
    for _, f := range files {
        errs = errors.Join(errs, f.Close())
    }
    return errs   // 全部都 nil 的話回 nil，不用自己判斷
}
```

`errors.Join` 會**保留每一個**錯誤，`errors.Is` / `errors.As` 會走訪整棵樹。兩個好用的性質：傳進去全是 nil 就回 nil（所以上面那個累積寫法不用先檢查）；`Error()` 的輸出是用換行接起來的，不是分號。

Go 1.20 之後 `fmt.Errorf` 也允許多個 `%w`，效果類似，但那是要順便寫一段自訂訊息時才用；單純合併用 `errors.Join` 意圖比較清楚。

#### `errors.AsType[T]`（1.26）

`errors.As` 的介面一直很彆扭：要先宣告一個變數，再把**指標的指標**傳進去。

```go
// 舊寫法
var pathErr *os.PathError
if errors.As(err, &pathErr) {
    log.Println(pathErr.Path)
}

// 1.26
if pathErr, ok := errors.AsType[*os.PathError](err); ok {
    log.Println(pathErr.Path)
}
```

差別不只是短。`errors.As` 的 target 型別是 `any`，傳錯東西（例如少一個 `&`）**編譯得過，執行時 panic**。泛型版把型別檢查提前到編譯期，順便把變數作用域收進 `if` 裡，不會外洩到後面的程式碼。

### 迴圈、迭代器與泛型

#### 迴圈變數共享：Go 1.22 以前的經典陷阱

這條值得多花篇幅，因為它是 Go 早年**最常見的一個 bug**，而且新舊版本的行為差異是靜默的。

Go 1.22 之前，`for _, item := range items` 裡的 `item` 是**整個迴圈共用的一個變數**，每次迭代只是覆寫它的值。所以：

```go
// Go 1.21 以前的語意（go.mod 寫 go 1.21 也一樣）
for _, item := range items {
    go func() {
        process(item)   // 讀到的是「迴圈跑到哪就是哪」的 item
    }()
}
```

goroutine 不會馬上執行，等它們排到 CPU 時，主迴圈很可能已經跑完了——於是三個 goroutine 全部處理**最後一個** item，前面的完全沒被處理。而且這是**競態**，不是穩定的錯：資料少、機器慢的時候可能剛好對；上了負載才開始漏。

同樣的坑在取位址時也成立：

```go
var selected []*Item
for _, item := range items {
    if item.Enabled {
        selected = append(selected, &item)   // 每次都是同一個位址
    }
}
// 舊語意下：selected 裡每個指標都指向同一個變數，內容全是最後一筆
```

當年的解法是那句看起來像廢話的自我賦值：

```go
for _, item := range items {
    item := item      // 開一個只屬於這次迭代的新變數
    go func() { process(item) }()
}
```

Go 1.22 把語意改成**每次迭代各自擁有一份變數**，上面兩段都直接正確，`item := item` 變成純粹的雜訊，可以刪掉。

要注意的邊界：

- **看 `go.mod`，不是看編譯器**。`go 1.21` 的模組拿 1.24 的編譯器編，還是舊語意。這也是 `item := item` 不能無腦刪的原因——先確認那行寫多少。
- `&item` 拿到的是**這次迭代那份複本**的位址，不是切片元素本身的位址。要改到原本的切片元素，得寫 `&items[i]`。這點新舊版本都一樣，1.22 沒有改變它。
- 這條只解決「變數被共用」，**不解決 data race**。多個 goroutine 同時寫同一個 map 或 slice 照樣會炸，那是另一回事。

#### `for i := range n`（1.22）

```go
for i := 0; i < n; i++ { ... }   // 舊
for i := range n { ... }         // 1.22
```

純粹是可讀性，沒有機制上的差別。只在「從 0 開始、每次 +1、上界固定」時能用；起點不是 0、步進不是 1、或上界在迴圈中會變，還是得寫傳統三段式。

#### 迭代器 `iter.Seq`（1.23 / 1.24）

Go 1.23 讓 `range` 可以吃函式型別的迭代器，標準庫跟著補了一批。核心動機是**不要為了「走一遍」而先配置一整個容器**。

```go
// 舊：為了排序而先做一個 slice
keys := make([]string, 0, len(m))
for k := range m {
    keys = append(keys, k)
}
sort.Strings(keys)

// 1.23
keys := slices.Sorted(maps.Keys(m))
```

`maps.Keys(m)` 回傳的是**迭代器**，不是 slice；`slices.Sorted` 把它收集起來並排序。如果只是要走一遍、不需要 slice，直接 `for k := range maps.Keys(m)` 就好，一個配置都不用。

字串切割也有對應的（1.24）：

```go
for part := range strings.SplitSeq(s, ",") {   // 不會先配出 []string
    process(part)
}
```

**一個很容易中的雷**：`golang.org/x/exp/maps.Keys` 回傳的是 `[]K`（slice），標準庫 `maps.Keys` 回傳的是 `iter.Seq[K]`（迭代器）。**同名、不同回傳型別**。從舊文章或舊專案抄程式碼過來、把 import 換成標準庫版本，就會編譯失敗或語意跑掉。

**代價**：迭代器只能走一次，不能取 `len`、不能索引。真的需要隨機存取就老實用 `slices.Collect` 收成 slice——這時它跟手寫 append 迴圈沒有效能差別，只是寫法乾淨。

#### 泛型方法（**需要 Go 1.27**）

1.27 之前，方法**不能有自己的型別參數**，所以「這個操作明明屬於這個型別」的東西只能被迫寫成 package-level 函式：

```go
type Set[T comparable] map[T]struct{}

// 1.27 之前只能這樣
func MapSet[T comparable, U any](s Set[T], f func(T) U) []U { ... }
names := MapSet(users, func(u User) string { return u.Name })

// 1.27
func (s Set[T]) Map[U any](f func(T) U) []U { ... }
names := users.Map(func(u User) string { return u.Name })
```

問題不只是難看：package-level 泛型函式會**污染套件命名空間**，而且無法從型別本身被發現（打 `users.` 不會跳出來）。

邊界：帶型別參數的方法在抽象化上仍有限制（interface 沒辦法表達「一個帶額外型別參數的方法」），所以真的要用 interface 抽象時還是得回到 package-level 函式。實際限制以該版本的 release notes 為準。

#### `reflect.TypeFor[T]()`（1.22）

```go
typ := reflect.TypeOf((*T)(nil)).Elem()   // 舊：用 nil 指標繞路
typ := reflect.TypeFor[T]()               // 1.22
```

舊寫法要繞 nil 指標，是因為 `reflect.TypeOf` 吃的是**值**，而 interface 型別沒辦法直接給一個值。純可讀性的改善，但這種「只有寫過的人才知道為什麼」的咒語，能消掉就消掉。

### 切片與 map 的標準庫工具

這組大部分是「手寫迴圈 → 標準庫一行」，本身沒什麼陷阱。但其中三、四條牽涉到**底層陣列共享**，那才是會咬人的部分。

#### 直接對照就好的（都是 1.21）

| 舊寫法 | 新寫法 |
|---|---|
| 手寫搜尋迴圈 | `slices.Contains(s, v)` / `slices.Index(s, v)` / `slices.IndexFunc(s, f)` |
| 手寫比大小的 if | `min(a, b)` / `max(a, b)`（內建） |
| 手寫掃描找極值 | `slices.Max(s)` / `slices.Min(s)` |
| 手寫首尾交換迴圈 | `slices.Reverse(s)` |
| `for k := range m { delete(m, k) }` | `clear(m)`（內建） |
| 手寫複製 map 的迴圈 | `maps.Clone(src)` |
| `for k, v := range src { dst[k] = v }` | `maps.Copy(dst, src)` |
| 手寫條件 delete 迴圈 | `maps.DeleteFunc(m, f)` |
| `sort.Strings` / `sort.Ints` | `slices.Sort(s)` |

幾個小注意：`slices.Index` 找不到回 `-1`（不是 0，也不是 panic）。`clear` 用在 slice 上是**把元素歸零**，長度和容量都不變，跟 `s = s[:0]` 完全是兩件事。`min` / `max` 用在浮點數時，只要有一個是 NaN 結果就是 NaN——這是刻意的，但拿來清資料時會被嚇到。

還有：`slices.Contains` / `slices.Index` 是**線性掃描**。一行取代五行很爽，但如果是在迴圈裡反覆查同一個 slice，那就是 O(n²)，該換成 `map[T]struct{}` 當 set。標準庫給的是寫法上的簡化，不是資料結構上的。

#### `slices.Clip`：擋掉 append 寫進別人的陣列

這條解的是 Go 一個真正的地雷。slice 是 `{指標, len, cap}`，切一個子 slice 出來時**底層陣列是共用的**，而且 cap 會一路延伸到原陣列尾端。所以對子 slice 做 append，只要 cap 還有空間，就會直接**覆寫原 slice 後面的元素**：

```go
base := []int{1, 2, 3, 4, 5}
head := base[:2]          // len=2, cap=5 ← cap 是 5 不是 2
head = append(head, 99)
// base 現在是 [1 2 99 4 5] —— base[2] 被改掉了
```

這種 bug 特別難查，因為出問題的是「另一個變數」，而且只在 cap 剛好還有餘裕時才發生：資料量小的時候好好的，換一組資料就爆。

`slices.Clip` 把 cap 砍到等於 len，之後任何 append 都一定重新配置，不會踩到別人：

```go
head := slices.Clip(base[:2])   // 舊寫法：base[:2:2]
head = append(head, 99)         // base 不受影響
```

舊寫法 `s[:len(s):len(s)]` 那個三索引切片語法本身就不好讀，`Clip` 至少把意圖寫出來了。**要把 slice 交給外部函式、或存進結構體長期持有時，Clip 一下**。

順帶一提，這也是為什麼有 `slices.Clone` / `bytes.Clone`：

```go
copied := append([]T(nil), values...)   // 舊，看得懂但要想一下
copied := slices.Clone(values)          // 1.21
```

注意是**淺**複製——元素如果是指標或含指標的 struct，複製出來的還是指向同一批物件。

#### `slices.Compact` 只吃「連續」重複

```go
values = slices.Compact(values)
```

名字叫 Compact 很容易誤會成「去重」。它只移除**相鄰**的重複值，所以 `[1, 2, 1]` 進去還是 `[1, 2, 1]`。要真的去重必須**先排序**（或先用其他方式把相同值聚在一起）。

它是**就地**操作、回傳新長度的 slice，原本的變數要接回去。另外 Go 1.22 起，`Compact` / `Delete` / `Insert` / `Replace` 這幾個會把被丟棄的尾端清成零值——這件事有意義：不清的話，尾巴殘留的指標會讓已經「刪掉」的物件無法被 GC 回收。

#### `slices.SortFunc` 取代 `sort.Slice`

```go
// 舊
sort.Slice(items, func(i, j int) bool {
    return items[i].CreatedAt.Before(items[j].CreatedAt)
})

// 1.21
slices.SortFunc(items, func(a, b Item) int {
    return a.CreatedAt.Compare(b.CreatedAt)
})
```

`sort.Slice` 的問題有兩層。可讀性上，比較函式拿到的是**索引**，要自己 `items[i]` 索引回去——閉包捕捉的是 `items` 這個**變數**，所以萬一在別處重新賦值 `items`，比較函式看到的就是另一個 slice 了。效能上，`sort.Slice` 是**透過 reflect 做元素交換**的，泛型版直接對具體型別操作，沒有這層開銷。

比較器從 `bool`（小於）改成 `int`（三向：負 / 0 / 正），因為排序演算法其實需要知道「相等」。數值和字串直接用 `cmp.Compare(a.X, b.X)` 就好。

**代價**：`slices.Sort` / `SortFunc` **不是穩定排序**，相等元素的原有順序會被打亂。需要穩定就用 `slices.SortStableFunc`。

#### `cmp.Or` 不會短路（1.22）

```go
name := cmp.Or(os.Getenv("APP_NAME"), "default")
```

取第一個非零值，比 `if name == "" { name = ... }` 順眼。但有個明確的坑：**所有參數都會先被求值**，這是普通的函式呼叫，不是 `||`。

```go
// 不要這樣寫：即使環境變數有值，loadFromDisk() 照樣會被執行
cfg := cmp.Or(os.Getenv("CFG"), loadFromDisk())
```

只在參數都是便宜、無副作用的取值時用它。

### 字串處理

這組的共同主題是：**「先找位置、再自己切」這種兩步驟寫法，很容易在邊界上算錯**。

#### `strings.Cut` 家族（1.18 / 1.20 / 1.27）

```go
// 舊：三個容易寫錯的地方 —— 忘記檢查 -1、切片邊界、分隔符長度
i := strings.Index(s, ":")
if i < 0 {
    return "", "", false
}
key, value := s[:i], s[i+1:]

// 1.18
key, value, found := strings.Cut(s, ":")
```

`i+1` 那個 `1` 是「分隔符長度」寫死的。分隔符如果改成 `"=>"` 就得寫 `i+2`，改的時候很容易忘記同步，結果多切或少切一個字元。`Cut` 把這件事包起來，順便強迫你處理 `found`。

同系列：

- `strings.CutPrefix` / `CutSuffix`（1.20）——取代「`HasPrefix` 判斷完再 `TrimPrefix`」，同一個條件不用寫兩次（寫兩次就有機會不一致）。
- `strings.CutLast` / `bytes.CutLast`（**需要 Go 1.27**）——從最後一個分隔符切，取代 `LastIndex` + 手動切片。切副檔名、切路徑最後一段常用。
- `bytes.Cut`（1.18）——`[]byte` 版本，行為一致。

#### `strings.Clone`：子字串會把整個大字串釘住（1.20）

這條是真正的記憶體問題，不是風格問題。Go 的字串切片**不複製資料**，`big[10:20]` 只是一個指向同一塊記憶體的新 header。所以：

```go
data := readWholeFile()          // 假設 50 MB
id := data[100:136]              // 只要 36 bytes
cache[key] = id                  // 但那 50 MB 因此永遠回收不掉
```

只要那 36 bytes 還被引用，背後 50 MB 的底層陣列就不能被 GC。程式看起來只留了一小段，記憶體卻降不下來。

```go
cache[key] = strings.Clone(id)   // 強制複製一份，大的那塊就能回收了
```

舊招數是 `string([]byte(s))`（繞一圈強迫複製），`strings.Clone` 把意圖直接寫出來。`bytes.Clone` 同理。

**代價**：這是額外的配置。只在「**留小段、丟大塊**」的情境下有意義；短生命週期的子字串無腦 Clone 反而是浪費。

#### `fmt.Appendf`（1.19）

```go
buf = append(buf, []byte(fmt.Sprintf("x=%d", x))...)   // 舊：多配一個 string
buf = fmt.Appendf(buf, "x=%d", x)                      // 1.19
```

`Sprintf` 產生的那個中間字串完全是丟掉的。在累積 `[]byte` 的迴圈裡這是實打實的配置節省；只呼叫一兩次就沒差。

### 並行與同步

我目前還沒有真的需要並行的場景，但這幾條的「舊寫法問題」很典型，先記著。

#### 型別化的 atomic（1.19）

```go
// 舊
var enabled int32
atomic.StoreInt32(&enabled, 1)
if atomic.LoadInt32(&enabled) != 0 { run() }

// 1.19
var enabled atomic.Bool
enabled.Store(true)
if enabled.Load() { run() }
```

舊 API 的問題不只是醜。它是**一組作用在普通變數上的函式**，所以編譯器完全阻止不了你在別的地方直接寫 `enabled = 1`——一次非原子存取就毀掉整個保證，而且沒有任何警告。型別化版本把值包在 struct 裡，只能透過 `Load` / `Store` / `CompareAndSwap` 存取，繞不過去。

還解掉一個惡名昭彰的坑：舊的 `atomic.AddInt64` 在 **32 位元平台**上要求運算元 8-byte 對齊，而 struct 欄位的對齊取決於前面欄位怎麼排——排錯了就在 32 位元上 panic，在 64 位元上完全正常，只有換平台才會發現。`atomic.Int64` 內建對齊處理，這個雷消失了。

`atomic.Pointer[T]` 也取代了以前要動用 `unsafe.Pointer` 的寫法。

#### `wg.Go`（**需要 Go 1.25**）

```go
// 舊
var wg sync.WaitGroup
for _, item := range items {
    wg.Add(1)
    go func() {
        defer wg.Done()
        process(item)
    }()
}
wg.Wait()

// 1.25
var wg sync.WaitGroup
for _, item := range items {
    wg.Go(func() { process(item) })
}
wg.Wait()
```

`Add` / `Done` 必須成對，這是**執行期才會發現**的約定：漏了 `Done`，`Wait()` 永遠卡住（死結）；`Add` 放錯位置（例如放進 goroutine 裡面），`Wait()` 可能在 goroutine 還沒開始就返回。`wg.Go` 把配對關進 API 裡，寫不錯。

#### `sync.OnceFunc` / `sync.OnceValue`（1.21）

```go
// 舊
var once sync.Once
var conf *Config
getConfig := func() *Config {
    once.Do(func() { conf = loadConfig() })
    return conf
}

// 1.21
getConfig := sync.OnceValue(func() *Config { return loadConfig() })
```

舊寫法需要三個東西（once、結果變數、getter），而那個結果變數在語法上是**裸露**的——任何人都能直接讀它，而且在初始化完成前讀到的是 nil，沒有東西擋著。`OnceValue` 把結果封在閉包裡，唯一的出口就是那個函式。

**要記住的行為**：如果 `f` panic 了，之後每次呼叫都會用**同一個 panic 值再 panic 一次**，不會重試。所以拿它包「可能失敗但重試會成功」的初始化（例如連外部服務）是不對的。

#### context 的取消原因（1.20 / 1.21）

`ctx.Err()` 只有兩個值：`context.Canceled` 和 `context.DeadlineExceeded`。也就是說，被取消時你只知道「有人取消了」或「逾時了」，**不知道為什麼**。系統一大，這個資訊量就不夠除錯。

```go
// 1.20
ctx, cancel := context.WithCancelCause(parent)
cancel(fmt.Errorf("upstream returned 503"))
// 下游：
if ctx.Err() != nil {
    log.Println(context.Cause(ctx))   // 拿得到真正的原因
}

// 1.21：逾時也能帶原因
ctx, cancel := context.WithTimeoutCause(parent, 5*time.Second, errDBSlow)
defer cancel()
```

`context.AfterFunc`（1.21）則是取代這個常見的樣板：

```go
// 舊：為了等一個 channel 而開一整條 goroutine
go func() {
    <-ctx.Done()
    cleanup()
}()

// 1.21
stop := context.AfterFunc(ctx, cleanup)
defer stop()
```

差別是：舊寫法**每個 cleanup 都要一條 goroutine 一直卡在那裡**，而且沒辦法取消註冊——工作提早正常完成了，那條 goroutine 還是會等到 ctx 結束才收工。`AfterFunc` 回傳的 `stop` 讓你撤銷，回傳值告訴你有沒有來得及撤銷。

這組對 graceful shutdown 應該蠻有用的，等真的寫到再回來看。

#### `time.Tick` 的舊禁忌解除了（1.23）

以前 `time.Tick` 是明文不建議用的：它回傳 channel 但不給你 ticker 本體，**沒辦法 Stop**，於是 ticker 永遠不會被 GC 回收，等於洩漏。所以標準寫法一律是 `NewTicker` + `defer Stop()`。

Go 1.23 讓沒有人引用的 ticker 可以被 GC 回收，所以「跑到程式結束為止」的輪詢迴圈可以直接寫：

```go
for range time.Tick(time.Second) {
    poll()
}
```

**但**：需要 `Stop()` 或 `Reset()` 的還是得用 `time.NewTicker`。另外這個行為改變一樣**綁 `go.mod` 版本**，`go` 那行低於 1.23 的模組維持舊行為。

### 測試與 benchmark（1.24）

這區我還沒開始寫，但兩條都直接影響「測試怎麼起手」，先記下來。

```go
// 舊
func TestFoo(t *testing.T) {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()
    result := doSomething(ctx)
}

// 1.24
func TestFoo(t *testing.T) {
    ctx := t.Context()
    result := doSomething(ctx)
}
```

`t.Context()` 給的 context 綁定測試生命週期，測試結束時自動取消。舊寫法忘了 `defer cancel()` 的話，測試裡起的背景工作會**活過測試本身**，在後續測試裡繼續跑——這是「單獨跑會過、整包跑會偶爾失敗」的經典來源之一。

benchmark：

```go
// 舊
func BenchmarkFoo(b *testing.B) {
    setup()                          // 會被重跑很多次
    for i := 0; i < b.N; i++ { doWork() }
}

// 1.24
func BenchmarkFoo(b *testing.B) {
    setup()                          // 只跑一次
    for b.Loop() { doWork() }
}
```

`b.N` 那套的機制是：testing 會**整個 benchmark 函式重跑好幾遍**，每次給不同的 `b.N` 來校準時間。所以迴圈外的 setup 也跟著重跑，得自己用 `b.ResetTimer()` 之類的手段排除。`b.Loop()` 把迭代控制收進迴圈條件裡，函式本體只跑一次，計時也處理好了。它另外還會防止編譯器把「結果沒被使用」的呼叫最佳化掉——那是舊 benchmark 另一個會得到假數據的陷阱。

### JSON 與序列化

#### `omitzero` 補上 `omitempty` 的破口（1.24）

`omitempty` 的判斷條件是寫死的一組「JSON 意義上的空值」：`false`、`0`、`""`、nil 指標、nil interface、長度 0 的 array / slice / map。**它不看 struct**——所以：

```go
type Entry struct {
    ExpiresAt time.Time `json:"expiresAt,omitempty"`
}
// 即使 ExpiresAt 是零值，還是會輸出 "expiresAt":"0001-01-01T00:00:00Z"
```

`time.Time` 是 struct，`omitempty` 對它毫無作用。很多人第一次遇到都以為是 tag 打錯了。

`omitzero`（1.24）判斷的是「是不是該型別的零值」（並且會呼叫型別自己的 `IsZero()`），所以 `time.Time{}` 正確被省略。

兩者**不是誰取代誰**，差異在 slice / map：

| | `nil` slice | `[]string{}`（空但非 nil） |
|---|---|---|
| `omitempty` | 省略 | 省略 |
| `omitzero` | 省略 | **保留**（輸出 `[]`） |

所以規則是：**bool / 數值 / struct / `time.Time` 用 `omitzero`；字串、slice、map 維持 `omitempty`**，除非你刻意要區分「空陣列」和「沒有這個欄位」。

#### `encoding/json/v2`（**需要 Go 1.27**）

v2 換掉了一批 v1 的預設行為，方向是「更嚴格、更符合其他語言的預期」：

- 拒絕不合法的 UTF-8（v1 會靜靜換成替代字元）
- 拒絕重複的物件鍵（v1 是後蓋前，這其實是安全問題——不同語言的解析器可能取到不同的值）
- nil slice 編成 `[]` 而不是 `null`，nil map 編成 `{}` 而不是 `null`

最後一條就是 v1 最常被抱怨的地方：Go 的 nil slice 和空 slice 在語意上是同一件事，編出來卻一個是 `null` 一個是 `[]`，前端得同時處理兩種。

```go
type Pet struct {
    Name      string
    Nicknames []string
}
json.Marshal(Pet{Name: "Remi"})
// v1: {"Name":"Remi","Nicknames":null}
// v2: {"Name":"Remi","Nicknames":[]}
```

**這一條的重點其實是「不要動舊程式」**。import 從 `encoding/json` 換成 `encoding/json/v2` 會**編譯通過**，但送出去的 JSON 變了——已經在跑的客戶端可能因此壞掉，而且沒有任何編譯期訊號。真要遷移的話，順序是：先用 `jsonv1.DefaultOptionsV1()` 保持原本的輸出、把測試補起來，再一項一項把相容選項拿掉（後面的選項會蓋掉前面的）。

新程式碼直接用 v2。另外 v2 在早期版本是藏在 `GOEXPERIMENT` 後面的實驗性功能，能不能直接用要看手上版本的 release notes。

### HTTP 與其他雜項

#### `ServeMux` 的方法與路徑參數（1.22）

這條對「用標準庫寫小服務」最實際。1.22 之前 `net/http` 的 mux 只能比對路徑前綴，方法判斷和路徑參數都得自己來：

```go
// 舊
mux.HandleFunc("/api/users/", func(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodGet {
        http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
        return
    }
    id := strings.TrimPrefix(r.URL.Path, "/api/users/")
    handleUser(w, r, id)
})

// 1.22
mux.HandleFunc("GET /api/users/{id}", func(w http.ResponseWriter, r *http.Request) {
    handleUser(w, r, r.PathValue("id"))
})
```

舊寫法的問題是每個 handler 開頭都要抄一段一模一樣的方法檢查和 `TrimPrefix`，而且 `TrimPrefix` 完全不驗證——`/api/users/1/extra` 會得到 `id = "1/extra"`，然後你就開始在 handler 裡自己切字串。這也是大家跑去裝第三方 router 的主因。

新語法還有幾個好用的地方：註冊了 `GET /x` 之後，其他方法打過來 mux 會**自動回 405 並帶 `Allow` header**；`{id...}` 匹配剩下的整段路徑；`/x/{$}` 表示只精確匹配 `/x`，不吃子路徑。

**代價**：pattern 衝突（兩條規則誰都不比誰更明確）會在**註冊時直接 panic**。這其實是好事——啟動就爆，總比執行期路由到錯的 handler 好——但如果路由是動態組出來的，就要小心會不會在啟動時炸掉。

#### 剩下的小條目

這幾條都是一眼就懂的替換，記個名字就好：

| 版本 | 舊 | 新 | 為什麼 |
|---|---|---|---|
| 1.0 | `time.Now().Sub(start)` | `time.Since(start)` | 純可讀性 |
| 1.8 | `deadline.Sub(time.Now())` | `time.Until(deadline)` | 同上，而且方向不容易寫反 |
| 1.18 | `interface{}` | `any` | 同一個東西的別名，新程式碼統一用 `any` |
| 1.26 | 自寫 `func Ptr[T any](v T) *T`，或只為了取位址而開的臨時變數 | `new(30)`、`new(true)` | `new` 現在吃**值**，不只是型別 |
| 1.27 | 手動逐欄複製 `url.URL` | `base.Clone()` / `values.Clone()` | 手動複製會漏欄位，或共用到底層 slice |
| 1.27 | `github.com/google/uuid` | 標準庫的 uuid 套件 | 少一個相依；只有需要標準 API 以外的行為時才留第三方 |

`new(value)`（1.26）那條跟我現在的程式碼有直接關係——上面 `*string` 當 nullable 欄位那段，以前得先開一個臨時變數才能取位址，或者自己寫一個 `Ptr()` 泛型函式。1.26 之後直接：

```go
cfg := Config{
    Timeout: new(30),      // *int
    Debug:   new(true),    // *bool
}
```

還有 **promoted field literals**（需要 Go 1.27）：嵌入 struct 的欄位可以在外層 literal 直接寫，不用再構造一次內層 struct。

```go
type AuditInfo struct{ CreatedBy, UpdatedBy string }
type Document struct {
    AuditInfo
    Name string
}

// 1.27 之前
doc := Document{AuditInfo: AuditInfo{CreatedBy: "alice", UpdatedBy: "alice"}, Name: "report.pdf"}
// 1.27
doc := Document{CreatedBy: "alice", UpdatedBy: "alice", Name: "report.pdf"}
```

限制：不能在同一個 literal 裡同時寫提升欄位和那個嵌入欄位本身，指標嵌入（`*AuditInfo`）也不支援。

### 版本速查

手上的 Go 版本決定能用哪些。`go version` 看 toolchain，但**語意類的改動是看 `go.mod` 那行 `go 1.xx`**。

| 版本 | 這一版解鎖了什麼 |
|---|---|
| 1.13 | `errors.Is` / `errors.As`、`%w` |
| 1.18 | 泛型、`any`、`strings.Cut` / `bytes.Cut` |
| 1.19 | 型別化 atomic、`fmt.Appendf` |
| 1.20 | `errors.Join`、`strings.Clone` / `bytes.Clone`、`CutPrefix` / `CutSuffix`、`WithCancelCause` |
| 1.21 | `slices` / `maps` / `cmp` 三個套件、內建 `min` / `max` / `clear`、`sync.OnceFunc` / `OnceValue`、`context.AfterFunc` |
| 1.22 | **迴圈變數改成每次迭代獨立**、`for i := range n`、`cmp.Or`、`reflect.TypeFor`、ServeMux 新 pattern |
| 1.23 | 迭代器（`iter.Seq`、`maps.Keys` / `Values`、`slices.Collect` / `Sorted`）、`time.Tick` 可被 GC |
| 1.24 | `omitzero`、`t.Context()`、`b.Loop()`、`SplitSeq` / `FieldsSeq` |
| 1.25 | `wg.Go` |
| 1.26 | `errors.AsType[T]`、`new(value)` |
| 1.27 | 泛型方法、`encoding/json/v2`、提升欄位 literal、`strings.CutLast`、標準庫 uuid、`url.Clone` |

大部分「一行取代五行」的東西集中在 1.21，所以只要環境有 1.21 以上，這份清單裡的實用部分就吃掉大半了。

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
- [JetBrains / go-modern-guidelines](https://github.com/JetBrains/go-modern-guidelines) — 54 條「舊寫法 → 新寫法」對照，上面那一節就是讀它整理的
