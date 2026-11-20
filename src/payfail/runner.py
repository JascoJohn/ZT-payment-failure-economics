"""Entry point used by every scripts/NN_*.py file: run one stage and print what it did."""
from __future__ import annotations

import time

from .pipeline import ANALYSIS_CHAPTERS, CHAPTERS, chapter_dir, run_analysis_chapter


def main(code: str) -> dict:
    from .stages import STAGES
    t0 = time.time()
    name, _, what = CHAPTERS[code]
    print(f"[{code}] {what}")
    out = STAGES[code]() if code in STAGES else run_analysis_chapter(code)
    for k, v in out.items():
        print(f"      {k}: {v}")
    print(f"[{code}] done in {time.time() - t0:.0f}s -> {chapter_dir(code).relative_to(chapter_dir(code).parents[1])}/")
    return out


def stage_10() -> dict:
    """Merge the chapters' results, write results.json, render the report (PDF, HTML, Word) and the executive brief."""
    from .config import ROOT
    from .pipeline import OUT, full_results, write_results_json
    from .report import build_report
    res = full_results()
    write_results_json(res)
    rep = build_report(res, ROOT, OUT / "report")
    out = {"report": rep["pdf"].name if rep["pdf"] else "no PDF (Chrome or Edge not found)",
           "brief": rep["brief_pdf"].name if rep["brief_pdf"] else "no PDF",
           "contents passes": rep["passes"], "contents entries": sum(len(rep["entries"][k]) for k in rep["entries"])}
    from .readme import build_readme
    out["readme"] = build_readme(res, ROOT, rep).name
    try:
        from .docx_export import build_docx
        out["word"] = build_docx(res, ROOT, OUT / "report", rep).name
    except ModuleNotFoundError as e:
        if "docx_export" not in str(e):
            raise
        out["word"] = "not built yet"
    return out


def cli(code: str) -> int:
    """Entry for scripts 00, 09, 10 and 11."""
    t0 = time.time()
    if code == "10":
        out = stage_10()
    elif code == "09":
        import sys
        from .excel_stage import stage_09
        out = stage_09(recalc="--recalc" in sys.argv)
    elif code == "11":
        from .validate import run_validate
        out = run_validate()
    elif code == "00":
        from .envcheck import run_check
        out = run_check()
    else:
        out = main(code)
    if code != "00":
        for k, v in out.items():
            print(f"      {k}: {v}")
    print(f"[{code}] done in {time.time() - t0:.0f}s")
    return 0
