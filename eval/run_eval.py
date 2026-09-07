#!/usr/bin/env python3
"""doc-pipeline eval：對 eval/transcripts/ 逐一產出 → 結構檢查（確定性）→ LLM judge 評分。

  python3 eval/run_eval.py                 # 產出 + 結構檢查 + judge（需 provider 金鑰）
  python3 eval/run_eval.py --structural    # 只跑產出 + 結構檢查（fake provider 也能跑通管線）

結果寫入 eval/results.md。judge 與產出走同一個 provider 抽象（LLM_PROVIDER）。
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import docpipe  # noqa: E402

REQUIRED_SECTIONS = ["# 會議紀要", "## 摘要", "## 討論事項", "## 決議", "## 待辦", "## 未決事項"]

JUDGE_PROMPT = """你是嚴格的文件品質評審。依 rubric 對「產出」評分，證據必須來自「逐字稿」。
四個維度各 0-2 分：faithfulness（忠實性）、separation（決議/待辦區分）、
missing（缺漏處理：沒提到的欄位應寫「未提及」）、readability（可讀性）。
只輸出一行 JSON，格式：
{{"faithfulness": n, "separation": n, "missing": n, "readability": n, "note": "一句話講最大缺點"}}

=== 逐字稿 ===
{transcript}

=== 產出 ===
{output}
"""


def check_structure(md: str) -> list[str]:
    """確定性檢查：模板結構是否被遵守。回傳缺失清單（空=通過）。"""
    problems = [f"缺少段落 {s}" for s in REQUIRED_SECTIONS if s not in md]
    if "{transcript}" in md or "{today}" in md:
        problems.append("佔位符未被替換")
    if "<!-- docpipe:" not in md:
        problems.append("缺少溯源 footer")
    if "## 決議" in md and "|" not in md.split("## 決議")[1].split("##")[0]:
        problems.append("決議段落缺少表格")
    return problems


def judge(transcript: str, output: str) -> dict:
    raw = docpipe.get_provider().generate(JUDGE_PROMPT.format(transcript=transcript, output=output))
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return {"error": f"judge 未回傳 JSON：{raw[:80]}"}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"error": f"judge JSON 解析失敗：{m.group(0)[:80]}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--structural", action="store_true", help="跳過 LLM judge")
    args = ap.parse_args()

    outdir = ROOT / "eval" / "out"
    rows, all_pass = [], True
    for src in sorted((ROOT / "eval" / "transcripts").glob("*.md")):
        dest = docpipe.run([str(src)], "meeting-minutes", str(outdir), False, None)[0]
        md = dest.read_text(encoding="utf-8")
        problems = check_structure(md)
        structural = "✅" if not problems else "❌ " + "；".join(problems)
        if problems:
            all_pass = False
        score = ""
        if not args.structural:
            s = judge(src.read_text(encoding="utf-8"), md)
            score = s.get("error") or (
                f'{s["faithfulness"] + s["separation"] + s["missing"] + s["readability"]}/8 — {s.get("note", "")}')
        rows.append(f"| {src.name} | {structural} | {score} |")
        print(f"{src.name}: structure={structural} {score}")

    provider = docpipe.get_provider()
    report = (f"# Eval 結果\n\n執行：{datetime.datetime.now().isoformat(timespec='seconds')}"
              f"｜provider={provider.name}｜model={provider.model}\n\n"
              "評分標準見 [rubric.md](rubric.md)；結構檢查為確定性、judge 為 LLM 評分。\n\n"
              "| 逐字稿 | 結構檢查 | judge（/8） |\n|---|---|---|\n" + "\n".join(rows) + "\n")
    (ROOT / "eval" / "results.md").write_text(report, encoding="utf-8")
    print(f"\n→ eval/results.md（structural {'all pass' if all_pass else 'HAS FAILURES'}）")
    return 0 if (all_pass or provider.name == "fake") else 1


if __name__ == "__main__":
    sys.exit(main())
