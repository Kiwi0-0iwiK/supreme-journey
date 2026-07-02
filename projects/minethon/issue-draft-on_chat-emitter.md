# Issue — on_chat 收到 emitter 而不是 username

> 日期:2026-07-02
> 已送出：**https://github.com/Hack-the-SDGs/minethon/issues/26**
> 背景細節見 [debug-log-eventadaptor.md](debug-log-eventadaptor.md)

## 已確認事項（送出前的查證）

- mineflayer npm 最新穩定版：**4.37.1**（我們釘的是 4.37.0），`lib/plugins/chat.js` 的
  legacy chat pattern 註冊（`addChatPattern('chat', LEGACY_VANILLA_CHAT_REGEX, {deprecated:true})`）
  完全沒變，一樣只送 4 個真實參數。
- minethon GitHub `main` 分支目前的 `_normalize_handler`（`src/minethon/_bot_runtime.py`），
  跟本地裝的 0.3.6 版**逐字相同**——bug 在最新版依然存在。
- 搜過現有 12 個 open issue（含 #12、#13），沒有重複的回報。

## 標題

`EventAdaptor.on_chat receives the JS bot/emitter object as the first positional arg instead of username`

## 內文

### Environment
- minethon 0.3.6 (also reproduced on current `main`, `_normalize_handler` unchanged)
- mineflayer 4.37.0 (pinned), Node.js 22.23.0, Windows

### Repro
```python
from minethon import EventAdaptor, create_bot

bot = create_bot(host="localhost", username="pybot")

class Greeter(EventAdaptor):
    def on_chat(self, username, message, translate, json_msg, matches):
        print(f"username={username!r} message={message!r}")

bot.bind(Greeter())
bot.run_forever()
```
Have another player/bot send a chat message.

### Actual
`username` receives the raw JS `EventEmitter` (the bot instance itself), and every
following parameter shifts by one slot (`message` gets the real username, `translate`
gets the real message, etc.).

### Root cause
`_normalize_handler` (`_bot_runtime.py:141`) tries to strip a leading emitter arg via
two checks, both of which fail here:

- **Identity check** (`args[0] is emitter`): fails because the proxy object JSPyBridge
  hands back for `js_bot` on each call is not the same Python object identity as the
  `emitter` captured at `bind()` time.
- **Arity check** (`len(args) > slots`): for `chat`, mineflayer emits exactly 4 real
  args (confirmed in `lib/plugins/chat.js:85` — the legacy `LEGACY_VANILLA_CHAT_REGEX`
  has only 2 capture groups, so `matches` never materializes). With the emitter
  prepended, the raw arg count is `1 + 4 = 5`. A handler written against the "full"
  documented 5-param signature (`username, message, translate, json_msg, matches`)
  declares `slots = 5`. `5 > 5` is `False`, so the excess-arity fallback never fires
  either.

Both detection paths coincidentally fail at exactly the arg count this event produces,
so the leading emitter is never stripped.

### Workaround
Declare one extra unused leading parameter so the raw arg count is *less* than `slots`,
which triggers the tail-padding path instead of relying on the (broken) stripping logic:
```python
def on_chat(self, _leading, username, message, translate=None, json_msg=None, matches=None):
```
This only works because the "missing" `matches` argument happens to be the last one;
it would not help for an event whose missing/extra argument is in the middle of the
signature.

### Suggested direction
The current heuristic assumes "extra/missing args are always at the boundary," which
happens to break for `chat`. This isn't `chat`-specific — `_normalize_handler` is the
shared path for every `on_<event>` registered via `bot.bind()` (see
`_bot_runtime.py:341`), and it can only pad/truncate at the *tail*. If some other
event's declared type signature is missing an argument in the *middle* (not the last
one) rather than at the end, this same silent-misalignment bug would happen there too,
and the tail-padding trick wouldn't fix it — only shifting everything after the gap by
one, with no error raised. A per-event known-arity table (rather than runtime
identity/length guessing) would make this robust regardless of where the mismatch
falls, instead of relying on it coincidentally landing at the boundary.

## 送出後續

- [x] 使用者確認內容/語氣沒問題
- [x] 用 `gh issue create -R Hack-the-SDGs/minethon` 送出
- [x] 送出後把 issue 連結補回這份文件開頭
- [x] 私訊 owner 提醒
- [ ] 考慮做 PR 修正 `_normalize_handler`（下一步）
