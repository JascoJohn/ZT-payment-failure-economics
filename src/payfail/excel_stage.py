"""Stage 09: build the Excel workbook and, if asked, recalculate it and read back the checks."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from .config import ROOT
from .pipeline import INTER, OUT, full_results, load_prep


def _recalc_workbook(path: Path) -> dict:
    """LibreOffice if installed (tools/recalc_excel.py), otherwise Microsoft Excel on Windows (tools/recalc_excel.ps1)."""
    report = INTER / "recalc_report.json"
    if shutil.which("soffice") or shutil.which("libreoffice"):
        subprocess.run([sys.executable, str(ROOT / "tools" / "recalc_excel.py"), str(path)], check=False)
        return {"engine": "LibreOffice"}
    if sys.platform == "win32":
        p = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "tools" / "recalc_excel.ps1"),
                            "-Path", str(path), "-Out", str(report)], capture_output=True, text=True)
        if p.returncode == 0 and report.exists():
            return json.loads(report.read_text(encoding="utf-8-sig"))
        return {"engine": "Microsoft Excel", "failed": (p.stderr or p.stdout)[-300:]}
    return {"engine": "none available: install LibreOffice, or open the file in Excel (it recalculates on opening)"}


def read_checks(path: Path) -> tuple[int, int]:
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["99_Checks"]
    st = [r[4] for r in ws.iter_rows(min_row=4, values_only=True) if r and r[4] in ("OK", "CHECK")]
    wb.close()
    return st.count("OK"), len(st)


def stage_09(recalc: bool = False) -> dict:
    from .excel import build_workbook
    cfg, prep = load_prep()
    res = full_results(prep)
    xl = OUT / "payment_failure_analysis.xlsx"
    t = time.time()
    build_workbook(prep, res, cfg, xl)
    out = {"workbook": f"{xl.relative_to(ROOT)} ({xl.stat().st_size / 1e6:.0f} MB)", "build seconds": round(time.time() - t)}
    if recalc:
        info = recalc_fn(xl)
        out["recalculated with"] = info.get("engine")
        if "errors" in info:
            out["formula errors"] = sum(info["errors"].values())
            out["recalc seconds"] = info.get("seconds")
        if "failed" in info:
            out["recalc failed"] = info["failed"]
        try:
            ok, n = read_checks(xl)
            out["99_Checks"] = f"{ok} of {n} OK"
        except Exception as e:
            out["99_Checks"] = f"unreadable ({type(e).__name__})"
    else:
        out["note"] = "not recalculated; Excel recalculates it on opening. Use --recalc-excel to recalculate and verify."
    return out


recalc_fn = _recalc_workbook
