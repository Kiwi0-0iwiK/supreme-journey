# Repo 閱讀筆記

> 最後更新：2026-11-25

看別人的 GitHub repo 之後留下的紀錄。每個 repo 一份筆記，這份負責索引與比較。
目的不是複述 README，而是回答三件事：**它是什麼、跟我有沒有關係、我到底查到了多深。**

## 已看過的 repo

| Repo | 類型 | 證據強度 | 結論 | 筆記 |
|---|---|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | agent harness | 🟢 已安裝實測 | **採用**，當主幹 | [superpowers](../../projects/agent-harness-study/superpowers.md) |
| [affaan-m/ECC](https://github.com/affaan-m/ECC) | agent harness | 🟡 只讀文件 | **部分採用**，不整包裝，只單獨讀 3 份 skill | [ecc](../../projects/agent-harness-study/ecc.md) |
| [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) | 網路抓取 | 🟡 只讀文件與部分原始碼 | **不裝**，跟 Claude Code 內建能力重複 | [agent-reach](agent-reach.md) |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | 影片生成 | 🟡 只讀文件 | **觀望**，沒有現成需求，FFmpeg 也還沒裝 | [hyperframes](hyperframes.md) |
| [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | 程式碼索引／agent skill | 🟡 只讀文件（README 為 WebFetch 摘要） | **觀望**，概念有用但 benchmark 是作者自己的、專案規模還不需要 | [graphify](graphify.md) |
| [amosblomqvist/learnharness](https://github.com/amosblomqvist/learnharness) | 學習 app（AI 家教） | 🟡 讀文件＋部分原始碼（WebFetch 轉述）＋ GitHub API | **觀望**，教學流程設計值得參考，但沒裝過、專案才 40 天 | [learnharness](learnharness.md) |
| [GoogleChrome/modern-web-guidance](https://github.com/GoogleChrome/modern-web-guidance) | 前端 skill／知識庫 | 🟢 跑過 CLI＋A／B 盲測各一次（沒全域安裝） | **部分採用**，多抓約 12 項前端語意／可及性問題，但 token +63%、抓不到安全與資料問題；不全域安裝 | [modern-web-guidance](modern-web-guidance.md) |

**證據強度要放在最前面**，原因跟 [agent harness 研究](../../projects/agent-harness-study/README.md)一樣：
讀過文件的印象和裝起來量過的數字不是同一個等級，隔幾個月回來看會把兩者當成同等可信。

| 標記 | 意義 |
|---|---|
| 🟢 | 已安裝並實測，有自己量到的數字或做過的對照 |
| 🟡 | 只讀文件／原始碼，沒有安裝。注明讀了哪些、是逐行讀還是 WebFetch 摘要 |
| ⚪ | 只看過概述或標題，連 README 都沒讀完 |

## 待看

- [Sui-IB/InternalBeyond](https://github.com/Sui-IB/InternalBeyond) — 純好奇，還沒讀過（來自主索引的 Backlog）

## 統一格式

新的筆記複製 [_template.md](_template.md)。固定的部分：

1. **標題**：`<名稱> — <一句話>`
2. **三行檔頭**：Repo／類型、證據強度／看過日期、結論
3. **固定章節**：這是什麼 → 結構 → 怎麼用 → 跟我的關係 → 證據與限制 → 下一步 → 相關

規則：

- **星數等會變的數字要附取得日期與來源**（GitHub API 或 WebFetch，兩者可信度不同）
- **推測要標成推測**，讀到的和推論的分開寫
- 「證據與限制」要寫清楚**沒做**什麼，不只寫做了什麼
- 研究變得很深（有實驗、有多份子筆記）就升級成 `projects/` 底下的獨立專案，
  這裡只留索引那一行。superpowers 和 ECC 就是這樣，所以它們的筆記不在這個資料夾

## 這幾個 repo 放在一起看

四個都是「給 coding agent 加東西」，但補的位置不同：

| | 補什麼 | 為什麼值不值得 |
|---|---|---|
| superpowers | **怎麼做事**（流程約束） | 方法論那層，Claude Code 本身不會自帶，價值最高 |
| ECC | 大量領域知識與規範 | 領域 skill 綁作者的技術棧，可攜性差 |
| HyperFrames | **新能力**（出影片）＋ 教它怎麼用的 skill | agent 原本做不到的事，有需求時才有價值 |
| Agent-Reach | **本來就有的能力**（上網） | Claude Code 已內建，重複 |
| modern-web-guidance | **模型自己補不了的知識**（前端新寫法，訓練資料偏舊） | 缺口是真的；盲測中效果集中在前端語意與可及性，安全與資料問題靠逐行讀碼（2026-11-25，各一次） |

判準：**補的如果是 agent 原本缺的東西才值得裝；補的是它已經有的，只會增加 context 成本和第三方依賴。**
（這是四份筆記看完後的歸納，樣本只有四個，當成目前的暫定看法。）
