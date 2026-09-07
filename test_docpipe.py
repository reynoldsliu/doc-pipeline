"""docpipe 自我測試：LLM_PROVIDER=fake，全程離線。執行：python3 test_docpipe.py"""
import os
import sys
import shutil
import tempfile
from pathlib import Path

os.environ["LLM_PROVIDER"] = "fake"
import docpipe


def main():
    # 模板列表
    ts = docpipe.list_templates()
    assert "meeting-minutes" in ts and "decision-log" in ts, ts

    # 模板渲染：佔位符必須被替換
    r = docpipe.render("meeting-minutes", "TRANSCRIPT_BODY")
    assert "TRANSCRIPT_BODY" in r and "{transcript}" not in r and "{today}" not in r

    # 未知模板：清楚報錯
    try:
        docpipe.render("nope", "x")
        raise AssertionError("unknown template should exit")
    except SystemExit as e:
        assert "nope" in str(e)

    # 未知 provider：清楚報錯
    os.environ["LLM_PROVIDER"] = "nope"
    try:
        docpipe.get_provider()
        raise AssertionError("unknown provider should exit")
    except SystemExit:
        pass
    os.environ["LLM_PROVIDER"] = "fake"

    # end-to-end：fake provider 產檔 + 溯源 footer
    tmp = Path(tempfile.mkdtemp())
    try:
        src = tmp / "m.md"
        src.write_text("Amy：測試逐字稿。", encoding="utf-8")
        written = docpipe.run([str(src)], "meeting-minutes", str(tmp / "out"), False, None)
        assert written[0].name == "m.meeting-minutes.md"
        body = written[0].read_text(encoding="utf-8")
        assert "fake provider" in body
        assert "<!-- docpipe: provider=fake" in body and "template=meeting-minutes" in body

        # docx：有裝 python-docx 才測，沒裝跳過（不是失敗）
        try:
            import docx  # noqa: F401
            docpipe.md_to_docx("# 標題\n- 項目\n內文", tmp / "t.docx")
            assert (tmp / "t.docx").exists()
        except ImportError:
            print("skip: python-docx 未安裝，略過 docx 測試")
    finally:
        shutil.rmtree(tmp)

    # eval 結構檢查器
    sys.path.insert(0, str(Path(__file__).parent / "eval"))
    from run_eval import check_structure
    good = ("# 會議紀要 — x\n## 摘要\n## 討論事項\n## 決議\n|a|b|\n## 待辦\n"
            "## 未決事項\n<!-- docpipe: x -->")
    assert check_structure(good) == [], check_structure(good)
    bad = "# 會議紀要\n## 摘要\n{today}"
    probs = check_structure(bad)
    assert any("決議" in x for x in probs) and any("佔位符" in x for x in probs)
    print("OK: all docpipe tests passed")


if __name__ == "__main__":
    main()
