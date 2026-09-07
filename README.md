# doc-pipeline

> Turn meeting transcripts into standardized documents with a provider-swappable LLM pipeline — switch Claude/Gemini with one env var, test fully offline with the built-in fake provider.

會議逐字稿 → 標準化文件（會議紀要、決策紀錄）的 LLM pipeline。
把「開完會後人工整理一小時」變成一行指令，且不被任何一家 LLM 綁死。

## 設計決策

| 決策 | 理由 |
|---|---|
| **Provider 用環境變數抽換**（`LLM_PROVIDER=claude\|gemini\|fake`） | 換模型供應商是資料維護，不是程式變更 —— 同一套 pipeline 在 CI 變數層切換 |
| **Prompt 模板是資料**（`templates/*.md`） | 新增文件類型＝加一個 md 檔，不動程式；模板可 review、可版控 |
| **內建 fake provider** | 測試與 CI 完全離線；新使用者零金鑰就能試跑整條 pipeline |
| **每份產出帶溯源 footer** | provider／model／模板／來源檔／時間戳寫進檔尾註解 —— 文件可稽核 |
| **資料隱私** | 一律使用付費層 API（Claude API／Gemini 付費層預設不以資料訓練）；敏感逐字稿先自行去識別化 |

## 快速開始

```sh
# 零金鑰試跑（fake provider，離線）
LLM_PROVIDER=fake python3 docpipe.py run examples/sample-transcript.md

# 正式使用（Claude）
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python3 docpipe.py run meeting.txt -t meeting-minutes -o out/

# 換成 Gemini：只改環境變數
pip install google-genai
LLM_PROVIDER=gemini GEMINI_API_KEY=... python3 docpipe.py run meeting.txt
```

```
用法：
  docpipe list                          列出可用模板
  docpipe run FILE... [-t 模板] [-o 目錄] [--model 模型] [--docx]
```

## 架構

```
逐字稿(txt/md) ─→ templates/<name>.md 渲染 ─→ Provider（env 選擇）─→ out/<檔名>.<模板>.md
                  {transcript} {today}         claude │ gemini │ fake      └─ 溯源 footer
                                                                          └─ --docx 另出 Word
```

## 模板

- `meeting-minutes` — 會議紀要：摘要／討論／決議表／待辦／未決事項
- `decision-log` — ADR 風格決策紀錄：背景／選項／決定／理由／影響

新增模板：在 `templates/` 放一個 md 檔，用 `{transcript}` 與 `{today}` 佔位符即可。

## CI 整合

- GitHub Actions：`.github/workflows/ci.yml` 以 fake provider 跑測試（零金鑰、零成本）
- GitLab CI 排程產文範例：`examples/gitlab-ci.example.yml` —— 在 CI 變數設定 `LLM_PROVIDER` 與金鑰，
  排程觸發即自動把新逐字稿轉成文件並存為 artifact

## Eval：產出品質可驗證

`eval/` 是這條 pipeline 的品質基準：4 份設計過的逐字稿（正常／無決策／有衝突未決／資訊稀疏）
+ [rubric](eval/rubric.md)（結構、忠實性、決議/待辦區分、缺漏處理、可讀性）。

```sh
python3 eval/run_eval.py               # 產出 → 確定性結構檢查 → LLM judge 評分 → eval/results.md
python3 eval/run_eval.py --structural  # 只跑確定性檢查（CI 用，離線）
```

結構完整性用程式把關、語意品質用 LLM judge 依 rubric 打分 ——
驗證成本必須低於生產成本，pipeline 才有資格自動化。

## 測試

```sh
python3 test_docpipe.py   # 離線，不需任何金鑰
```
