"""Rebuild every output from the raw workbook.

    python run_all.py                 # figures, tables, results.json, report (docx + pdf), Excel workbook
    python run_all.py --skip-excel    # faster: everything except the Excel workbook
    python run_all.py --recalc-excel  # also recalculate the workbook with LibreOffice (about 8 minutes)

All thresholds come from config/assumptions.yaml.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from payfail import analyse, load_config, prepare  # noqa: E402
from payfail.figures import FIGURES, build_all  # noqa: E402

OUT = ROOT / "outputs"


def _jsonable(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (pd.Timestamp,)):
        return o.strftime("%Y-%m-%d")
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    return o


def write_tables(res: dict) -> dict:
    """Every DataFrame in the results goes to outputs/tables; every scalar to results.json."""
    tdir = OUT / "tables"
    tdir.mkdir(parents=True, exist_ok=True)
    scalars = {}

    def walk(d, prefix):
        out = {}
        for k, v in d.items():
            name = f"{prefix}{k}"
            if isinstance(v, pd.DataFrame):
                v.to_csv(tdir / f"{name}.csv", index=False)
            elif isinstance(v, dict):
                out[k] = walk(v, f"{name}__")
            elif isinstance(v, pd.Series):
                v.to_csv(tdir / f"{name}.csv")
            else:
                out[k] = _jsonable(v)
        return out

    scalars = walk(res, "")
    (OUT / "results.json").write_text(json.dumps(scalars, indent=2), encoding="utf-8")
    return scalars


def write_figures(res, prep) -> None:
    """PNG + HTML for every figure; SVG (report size) for the figures used in the report."""
    import plotly.io as pio
    from payfail.figures import FIGURES, REPORT_ORDER, label
    pio.defaults.mathjax = None
    fdir = OUT / "figures"
    fdir.mkdir(parents=True, exist_ok=True)
    for old in fdir.glob("fig*"):
        old.unlink()
    figs = build_all(res, prep)
    rows = []
    for _, slug, section, _ in FIGURES:
        fig, lab = figs[slug], label(slug)
        stem = f"{lab.split()[1].lower().zfill(2) if lab.split()[1].isdigit() else lab.split()[1].lower()}_{slug}"
        h = fig.layout.height or 460
        fig.write_image(fdir / f"fig{stem}.png", width=1100, height=h, scale=2)
        fig.write_html(fdir / f"fig{stem}.html", include_plotlyjs="cdn")
        if slug in REPORT_ORDER:
            fig.write_image(fdir / f"fig{stem}.svg", width=860, height=round(h * 0.86))
        rows.append({"label": lab, "slug": slug, "section": section, "in_report": slug in REPORT_ORDER,
                     "title": fig.layout.title.text.split("<br>")[0].replace("<b>", "").replace("</b>", ""), "file": f"fig{stem}"})
    pd.DataFrame(rows).to_csv(fdir / "index.csv", index=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-excel", action="store_true")
    ap.add_argument("--recalc-excel", action="store_true")
    ap.add_argument("--skip-figures", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    cfg = load_config()
    print("1/5 preparing data …"); prep = prepare(cfg)
    print("2/5 running analysis …"); res = analyse(prep, cfg)
    print("3/5 writing tables and results.json …"); write_tables(res)
    if not a.skip_figures:
        print("4/5 drawing the figures …"); write_figures(res, prep)
    from payfail.report import build_report
    print("5/5 writing the report …")
    rep = build_report(res, ROOT, OUT / "figures", OUT / "report")
    print("    ", rep["html"].name, "|", rep["pdf"].name if rep["pdf"] else "no PDF (Chrome or Edge not found)",
          "|", rep["brief_pdf"].name if rep["brief_pdf"] else "")
    if not a.skip_excel:
        from payfail.excel import build_workbook
        xl = OUT / "payment_failure_analysis.xlsx"
        print("    building the Excel workbook …"); build_workbook(prep, res, cfg, xl)
        if a.recalc_excel and shutil.which("soffice"):
            print("    recalculating it with LibreOffice (several minutes) …")
            subprocess.run([sys.executable, str(ROOT / "tools" / "recalc_excel.py"), str(xl)], check=False)
    h = res["headline"]
    print(f"Done in {time.time() - t0:.0f}s. Failed-transaction fees ${h['failed_fees']:,.0f} "
          f"({h['fee_share']:.1%}); count failure rate {h['count_rate']:.1%}.")


if __name__ == "__main__":
    main()
