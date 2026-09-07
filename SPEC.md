# SPEC — doc-pipeline

版本基準：v0.1。本文件定義範圍與驗收；程式碼為實作細節的最終依據。

## 目標
把會議逐字稿轉成標準化文件，且 LLM 供應商可在部署層抽換。

## 範圍
- 輸入：UTF-8 逐字稿（txt/md），一次多檔
- 模板：`templates/*.md`，佔位符 `{transcript}`、`{today}`
- Provider：claude（anthropic SDK, streaming）、gemini（google-genai）、fake（離線）
- 輸出：`out/<stem>.<template>.md` + 溯源 footer；`--docx` 另出簡化版 Word

## 非範圍（YAGNI）
- 錄音轉文字（使用者自備逐字稿）
- 文件品質評分、多輪修訂
- Web UI

## 驗收
1. `LLM_PROVIDER=fake python3 test_docpipe.py` 全數通過（離線）
2. fake provider 跑 `run` 可產檔且含溯源 footer
3. 換 provider 不需改任何程式碼
