# PR — 用 `_REAL_ARGC` 查表取代猜測式 emitter 剝除

> 日期:2026-07-02
> 已送出：**https://github.com/Hack-the-SDGs/minethon/pull/27**
> 目標分支: **`dev`**（照 README「貢獻」章節規定，不是 `main`）
> 來源分支: 從自己 fork（`Kiwi0-0iwiK/minethon`）的 `fix/chat-emitter-arity` 推上去
> 背景細節見 [debug-log-eventadaptor.md](debug-log-eventadaptor.md)、[issue-draft-on_chat-emitter.md](issue-draft-on_chat-emitter.md)

## 送出前的查證/準備

- 對 `Hack-the-SDGs/minethon` 只有 READ 權限，已 fork 到 `Kiwi0-0iwiK/minethon`
- `dev` 落後 `main` 25 個 commit，但要改的 `_normalize_handler` 在兩邊**逐字相同**，
  從 `origin/dev` 開分支不會有衝突風險
- 讀過 `AGENTS.md`：改動完全落在既有設計意圖內（"bridge 層必須處理 JSPyBridge 可選的
  emitter 注入，以及 runtime 少於 d.ts 宣告參數的情況"），沒有引入新架構
- 跑過 `./scripts/format.sh --check` 的各步驟（`ruff format --check`、`ruff check`、
  `pyright`、`pytest -m "not integration"`）——全部通過。步驟 1/6（stub 產生 /
  `check_stubs.py`）在這台 Windows 機器上因為 pre-existing、無關的路徑問題跑不動
  （細節見下方 PR 內文的 Testing 段落），已在本地暫時修過又復原，確認不影響本次改動

## 標題

`fix(events): stop guessing whether to strip the injected emitter arg`

## 內文

### What

Fixes #26 — `chat`, `whisper`, and `resourcePack` handlers registered via
`EventAdaptor` received the JS bot/emitter object as their first argument
instead of the real data, silently shifting every subsequent argument by one.

### Root cause

`_normalize_handler`'s emitter-stripping logic relied on two heuristics that
both happen to fail for these three events:

- proxy-identity (`args[0] is emitter`) — JSPyBridge hands back a freshly
  constructed proxy for the emitter on every call (`javascript/pyi.py:222`),
  so identity never matches the proxy captured at `bind()` time
- arity excess (`len(args) > slots`) — fails whenever the real arg count + 1
  (emitter) happens to equal the handler's declared slot count (`chat`/
  `whisper`: 4 real args + 1 = 5, matching a fully-declared 5-slot handler;
  `resourcePack`: 2 real args + 1 = 3, matching its 3-slot handler), *and* is
  bypassed entirely by any handler using a trailing `*_` catch-all, since
  `not accepts_varargs` short-circuits to `False` regardless of arg count

Both are guesses based on how the *user* happened to declare their handler,
not on what mineflayer actually sends.

### Fix

Added `_REAL_ARGC`, a small table of real arg counts verified by hand
against mineflayer's source (`lib/plugins/chat.js:85`,
`lib/plugins/resource_pack.js`). When an event's real arg count is known,
`_normalize_handler` strips the emitter based on that fact
(`len(args) == real_argc + 1`) instead of guessing — this works regardless
of how the user's handler is declared, including the `*_` catch-all case.
Events not yet in the table keep today's heuristic unchanged, so this is
purely additive for the other ~94 events.

**Known, out-of-scope limitation**: `resourcePack`'s argument *order* isn't
stable across mineflayer's own call sites (`resource_pack.js` sometimes
emits `(url, uuid)`, sometimes `(uuid, url)`, sometimes `(url, hash)`
depending on server-support branching) — that's a separate mineflayer-level
quirk this table doesn't (and can't) fix; it only guarantees "how many," not
"which means what."

### Testing

Ran everything the repo's checklist covers that's actually runnable on
Windows:

- `ruff format --check`, `ruff check` — clean
- `pyright src/` — 0 errors
- `pytest -m "not integration"` — all passing, plus 4 new unit tests in
  `tests/unit/test_normalize_handler_real_argc.py` covering: the `chat`
  boundary case, the `resourcePack` boundary case, the `*_` varargs bypass,
  and a regression guard confirming events absent from `_REAL_ARGC` keep
  today's behavior untouched
- Live end-to-end check against a local vanilla server for `chat` and
  `whisper` (both now resolve `username`/`message` correctly with the
  textbook 5-arg signature, no workaround needed)

**Not run**: stub regeneration (`generate_stubs.py`) and its drift gate
(`check_stubs.py`). On this Windows environment, `_find_runtime_node_modules`
never resolves the pinned runtime install — its glob only matches the POSIX
venv layout (`.venv/lib/pythonX.Y/...`), not Windows' (`.venv/Lib/...`) —
so step 1/6 fails before reaching anything this PR touches. This looks
pre-existing and platform-specific (guessing the project's usually developed
on Mac/Linux), unrelated to this change — `_bot_runtime.py` doesn't touch
`bot.pyi`/`_events.py`/`_handlers.py` generation at all, so there's no reason
to expect step 1/6 to behave differently here versus on `dev` without this
patch. Happy to open that as a separate issue if useful.

## 送出後續

- [x] 使用者確認內容/語氣沒問題
- [x] 只 commit `src/minethon/_bot_runtime.py` + `tests/unit/test_normalize_handler_real_argc.py`
      （`examples/bot01/` 是個人練習用，已加進 `.git/info/exclude` 本地忽略，不進 PR）
- [x] commit message 對齊專案的 conventional commits 風格
- [x] push 到 fork（`Kiwi0-0iwiK/minethon` 的 `fix/chat-emitter-arity` 分支）
- [x] 用 `gh pr create --base dev` 從 fork 送出：[#27](https://github.com/Hack-the-SDGs/minethon/pull/27)
- [ ] 決定要不要另外開 Windows 路徑問題那個 issue（先前決定暫緩，視這次 PR 反應而定）

## PR 審查往返（`greptile-apps[bot]`，2026-07-02）

repo 有掛自動審查 bot，PR 一送出很快就收到兩則 P2 意見：

1. **`whisper` 缺專屬測試**——`_REAL_ARGC["whisper"]` 走的是跟 `chat` 一模一樣的邊界巧合，
   但測試檔案只釘住了 `chat`。就算邏輯完全一樣，`whisper` 這一筆表格資料本身沒有被單獨驗證，
   如果之後被打錯（例如大小寫、數字），只要 `chat` 的測試還過，這個錯誤不會被抓到。
   → 補了 `test_normalize_handler_real_argc_table_covers_whisper`，內容跟 `chat` 版本幾乎相同，
   刻意分開寫兩份（而不是用 `pytest.mark.parametrize` 合併），為了清楚證明兩筆資料都有各自驗證過。

2. **查表比對失敗時沒有退路**——原本的寫法是「事件在表格裡就完全相信表格，比對失敗就什麼都不做」，
   如果表格數字之後過時（例如 mineflayer 改版），會比完全沒有這張表還糟（舊的猜測邏輯至少還有機會
   猜對）。→ 改成「查表比對優先，但比對失敗（不管是不在表格裡、還是在表格裡但數字對不上）一律退回
   舊邏輯」，並加測試 `test_normalize_handler_falls_back_to_heuristic_when_real_argc_table_is_stale`
   直接證明退路真的會被觸發。

### 順便記一筆:自己多想的一個顧慮

看完意見 2 的修法後，突然想到「如果不是差 1 個，是寫表格的人不小心多打/少打 2 個怎麼辦」，
往下追問才發現這個顧慮其實包含兩種完全不同的情境：

- **表格數字本身打錯**（例如該寫 4 卻寫成 6 或 2）——這個其實已經被意見 2 的修法自動涵蓋了，
  因為判斷是「完全比對」（`len(args) == real_argc + 1`），差 1 個還是差 2 個都一樣過不了比對，
  一樣會退回舊邏輯，不需要額外處理。
- **emitter 真的一次塞 2 個東西進來**（不是表格寫錯，是實際行為變了）——這個才是真正新的、
  更根本的情境，但追下去發現這其實是整個 `_normalize_handler` 從一開始就有的假設
  （`args = args[1:]` 永遠只切一個，新舊邏輯共用同一行），不是這次加表格才引入的限制，而且
  稽查全部 97 個事件時完全沒看過這種情況發生過。

最後沒有為這個情境寫防禦性程式碼，理由是 `AGENTS.md` 明講的 **Source-Verified 原則**：
所有設計決策要有原始碼依據，沒證據支持的假設情境不該預先寫程式碼去防——反過來也適用在「不該為
沒證據的假設過度設計」。這是這次意外學到的一個判斷準則：**遇到「要不要多寫一層防禦」的猶豫時，
先問「有沒有實際證據支持這個情境會發生」，沒有的話就先不要寫**，而不是單純「感覺比較保險」就加。
- [x] `Fixes #26` 已寫進 PR 內文，issue 會自動雙向連結，不用手動處理
