# doc-pipeline

> Turn meeting transcripts into standardized documents with a provider-swappable LLM pipeline — switch Claude/Gemini with one env var, test fully offline with the built-in fake provider.

**開完會之後，把逐字稿變成一份格式一致的會議紀要 —— 用一行指令。**

會議紀錄這件事很煩：每個人寫的格式都不一樣、決議和待辦混在一起、
過兩週回頭看根本找不到當初決定了什麼。這個工具把逐字稿交給 AI，
按照固定模板整理成標準文件。

```sh
python3 docpipe.py run 週會逐字稿.md
# → out/週會逐字稿.meeting-minutes.md
```

<details>
<summary><b>實際產出長這樣（點開看）</b></summary>

```markdown
# 會議紀要 — 2026-09-08

## 摘要
確定匯出功能優先實現 CSV 格式本週上線，Excel 延至下迭代；
API 逾時問題已定位並修正連線池上限設定，今日部署。

## 決議
| # | 決議內容 | 負責人 | 期限 |
|---|---|---|---|
| 1 | 匯出功能優先實現 CSV，release note 說明後續 Excel 計劃 | Amy | 本週 |
| 2 | 連線池上限從 10 調整至 50 的修正部署到生產環境 | Cindy | 今日 |

## 待辦
- [ ] 新增 API 逾時告警機制（Cindy／本週）

## 未決事項
- 未提及
```

完整範例在 [`examples/out/`](examples/out/)。
</details>

## 四個設計決定，以及為什麼

| 決定 | 為什麼 |
|---|---|
| **換 AI 供應商只要改一個環境變數**<br>`LLM_PROVIDER=claude` / `gemini` | AI 模型一年換好幾輪，不該讓「換模型」變成「改程式」。這裡它是部署設定，不是程式碼 |
| **提示詞（prompt）存成獨立檔案**<br>`templates/*.md` | 想多一種文件類型？加一個 md 檔就好，不用碰程式。模板可以被 code review、可以看歷史版本 |
| **內建一個假的 AI（fake provider）** | 讓測試和 CI 完全離線、不花錢、不需金鑰；新使用者也能零成本先跑一遍看看 |
| **每份產出都留下溯源註記** | 檔尾記錄「哪個 AI、哪個模型、哪個模板、哪份來源、什麼時間」產生的 —— 文件才能被稽核 |

## 開始使用

```sh
# 1. 零金鑰試跑（用假 AI，離線，看看流程長怎樣）
LLM_PROVIDER=fake python3 docpipe.py run examples/sample-transcript.md

# 2. 正式使用（Claude）
#    macOS 的系統 Python 會拒絕直接 pip install（PEP 668），所以用虛擬環境
python3 -m venv .venv && .venv/bin/pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...        # 建議從 keychain 讀，別寫進檔案
.venv/bin/python docpipe.py run meeting.txt -t meeting-minutes -o out/

# 3. 想換 Gemini？只改環境變數，程式碼一行都不用動
.venv/bin/pip install google-genai
LLM_PROVIDER=gemini GEMINI_API_KEY=... .venv/bin/python docpipe.py run meeting.txt
```

```
docpipe list                       列出可用模板
docpipe run 檔案... [選項]
    -t 模板     預設 meeting-minutes
    -o 目錄     輸出位置，預設 out/
    --model     指定模型（如 claude-haiku-4-5）
    --docx      同時輸出 Word 檔
```

## 內建模板

- **`meeting-minutes` 會議紀要** — 摘要／討論事項／決議表／待辦／未決事項
- **`decision-log` 決策紀錄** — 背景／考慮過的選項／決定／理由／影響（ADR 格式）

要新增自己的模板：在 `templates/` 放一個 md 檔，用 `{transcript}`（逐字稿）
和 `{today}`（今天日期）當佔位符即可。

## 怎麼知道產出品質好不好？

AI 產出最怕「看起來很順、其實在瞎掰」。所以這個專案附了一套品質基準：

```sh
python3 eval/run_eval.py               # 產出 → 檢查 → 評分 → eval/results.md
python3 eval/run_eval.py --structural  # 只跑機械式檢查（CI 用，離線免費）
```

- **4 份刻意設計的逐字稿**：正常會議／完全沒有結論的會議／有爭執但未定案／資訊很少
- **兩層把關**：格式完整性用程式碼硬性檢查（缺段落、佔位符沒替換就是不合格）；
  內容品質交給另一個 AI 依 [rubric](eval/rubric.md) 打分（忠實性、決議待辦有沒有分清楚、缺漏處理、可讀性）

最新一次實測結果（Claude Haiku）在 [`eval/results.md`](eval/results.md) ——
包含一個還沒解決的弱點：**沒有結論的會議，AI 有時會自己生出決議**（4/8 分）。
留在那裡，是因為看得見的缺點才有機會修。

## 自動化

- **GitHub Actions**：每次 push 用假 AI 跑測試（離線、免金鑰、零成本）
- **排程產文**：[`examples/gitlab-ci.example.yml`](examples/gitlab-ci.example.yml) ——
  在 CI 設好變數，排程時間到就自動把新逐字稿轉成文件

## 測試

```sh
python3 test_docpipe.py   # 離線，不需金鑰也不需安裝任何套件
```

## 隱私

一律使用付費層 API（Claude API／Gemini 付費層預設不拿你的資料訓練模型）。
敏感逐字稿請先自行去識別化再送出。

MIT License
