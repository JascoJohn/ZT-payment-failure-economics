"""Stage 00: is this machine ready, and what does each stage do?"""
from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

from .config import ROOT, load_config
from .pipeline import CHAPTERS, ORDER, SCRIPTS


def _font_found() -> bool:
    try:
        from matplotlib import font_manager
        if any(f.name.startswith("Source Sans 3") for f in font_manager.fontManager.ttflist):
            return True
    except Exception:
        pass
    return any(Path(d).glob("SourceSans3*") for d in [Path.home() / "AppData/Local/Microsoft/Windows/Fonts", Path("C:/Windows/Fonts"),
                                                      Path.home() / "Library/Fonts", Path("/Library/Fonts"), Path.home() / ".fonts",
                                                      Path("/usr/share/fonts")] if d.exists())


def run_check() -> dict:
    ok = True

    def line(name, good, detail="", required=True):
        nonlocal ok
        mark = "ok  " if good else ("MISSING" if required else "optional")
        ok &= good or not required
        print(f"  [{mark:<8}] {name}{(': ' + detail) if detail else ''}")
    print("[00] Environment")
    line("Python 3.11 or later", sys.version_info >= (3, 11), sys.version.split()[0])
    for mod, req in [("pandas", True), ("numpy", True), ("plotly", True), ("streamlit", True), ("openpyxl", True), ("yaml", True),
                     ("kaleido", True), ("markdown", True), ("bs4", True), ("latex2mathml", True), ("fitz", True), ("docx", True),
                     ("pytest", False), ("matplotlib", False)]:
        try:
            m = importlib.import_module(mod)
            line(f"package {mod}", True, getattr(m, "__version__", ""), req)
        except Exception:
            line(f"package {mod}", False, "pip install -r requirements-dev.txt", req)
    from .report import find_browser
    b = find_browser()
    line("Chrome or Edge (figures and PDF)", bool(b), b or "install Chrome or Edge")
    line("Source Sans 3 font", _font_found(), "install report/assets/fonts/SourceSans3[wght].ttf so figures match the report font", False)
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    line("LibreOffice (optional: Excel recalculation)", bool(soffice), soffice or "not found; on Windows, Excel can recalculate instead", False)
    cfg = load_config()
    wb = Path(cfg["_root"]) / cfg["data"]["workbook"]
    line("Raw workbook", wb.exists(), str(wb.relative_to(ROOT)) if wb.exists() else "data/raw/ZT_EA_Regional_Data.xlsx is missing")
    print("\nWhat each stage does (run order; 01E runs after 01G because it reports on what 01F and 01G produce):")
    names = {"00": "Checks the environment and prints this list", "09": "Builds the Excel workbook",
             "10": "Renders the report (PDF, HTML, Word) and the executive brief", "11": "Integrity checks, independent recomputation, audit report"}
    for code in ORDER:
        print(f"  {code:<4}scripts/{SCRIPTS[code]:<34}{names.get(code) or CHAPTERS[code][2]}")
    if not ok:
        raise SystemExit("\nFix the items marked MISSING, then run again.")
    print("\nReady. Run: python run_pipeline.py")
    return {}
