"""README.md: written from report/content/readme.md with the same tokens as the report, so every figure in it comes from results.json.

Stage 10 calls build_readme() after the report and brief are printed (the page numbers of the sections come from the printed PDF).
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import yaml

from .report import context, render

REPORT_PDF = "outputs/report/The_Economics_of_Payment_Failure.pdf"
BRIEF_PDF = "outputs/report/Executive_Brief.pdf"
WORKBOOK = "outputs/payment_failure_analysis.xlsx"
KEY_VISUALS = ["bridge", "heatmap", "scenarios", "matrix"]          # exposure bridge, card failure by market, base case, prioritisation matrix


def _page_of(entries: list, pages: dict, starts: str, contains: bool = False) -> str:
    for e in entries:
        if (starts in e["text"]) if contains else e["text"].startswith(starts):
            return str(pages.get(e["id"], ""))
    return ""


def n_checks_from_last_audit(root: Path) -> str:
    f = root / "outputs" / "audit_report.md"
    if f.exists():
        m = re.search(r"(\d+) checks:", f.read_text(encoding="utf-8")[:300])
        if m:
            return m.group(1)
    return "0"


def tokens(res: dict, root: Path, rep: dict) -> dict:
    ctx = context(res)
    meta = rep["meta"]
    cont, pages = rep["entries"]["contents"], rep["pages"] or {}
    idx = pd.read_csv(root / "outputs" / "figure_index.csv").set_index("slug")
    import pymupdf
    n_rep = pymupdf.open(root / REPORT_PDF).page_count if (root / REPORT_PDF).exists() else 0
    n_brief = pymupdf.open(root / BRIEF_PDF).page_count if (root / BRIEF_PDF).exists() else 0
    wb = root / WORKBOOK
    t = dict(ctx)
    t.update(version=str(meta.get("version", "")), meta_title=meta["title"], meta_subtitle=meta["subtitle"], meta_date=meta["date"], meta_prepared_for=meta["prepared_for"],
             meta_year=re.search(r"\d{4}", meta["date"]).group(0), meta_email=meta["email"], meta_orcid=meta["orcid"], source_code=meta["source_code"], dashboard=meta["dashboard"],
             rel_report=REPORT_PDF, rel_brief=BRIEF_PDF, rel_xlsx=WORKBOOK, rep_pages=str(n_rep), brief_pages=str(n_brief),
             wb_mb=str(int(round(wb.stat().st_size / 1e6))) if wb.exists() else "0", n_checks=n_checks_from_last_audit(root))
    for n in range(2, 9):
        t[f"pg{n}"] = _page_of(cont, pages, f"{n}.")
    t["pgA"] = _page_of(cont, pages, "Appendix A")
    t["pgPilot"] = _page_of(cont, pages, "A 90-day pilot", contains=True)
    for i, slug in enumerate(KEY_VISUALS, start=1):
        r = idx.loc[slug]
        t[f"vis{i}_path"] = f"outputs/{r['dir']}/{r['file']}.png"
        t[f"vis{i}_title"] = r["title"]
    return t


def build_readme(res: dict, root: Path, rep: dict) -> Path:
    tpl = (root / "report" / "content" / "readme.md").read_text(encoding="utf-8")
    meta = rep["meta"]
    rep = {**rep, "meta": {**yaml.safe_load((root / "report" / "content" / "meta.yaml").read_text(encoding="utf-8")), **meta}}
    out = root / "README.md"
    out.write_text(render(tpl, tokens(res, root, rep)), encoding="utf-8")
    return out
