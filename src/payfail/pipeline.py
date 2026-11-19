"""Plumbing shared by the numbered stage scripts in scripts/.

Layout of outputs/
    intermediate/            prepared data and per-chapter results (a cache, safe to delete; stage 01G rebuilds it)
    <number>_<name>/         one folder per chapter: tables/ (CSV) and figures/ (PNG, SVG, HTML)
    figure_index.csv         the one figure index that the report, dashboard checks and Doc sync read
    results.json             every scalar result, merged from the chapters
    report/                  PDF, HTML and Word report; executive brief
    payment_failure_analysis.xlsx
"""
from __future__ import annotations

import json
import pickle
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .analysis import BLOCK_CHAPTER, BLOCK_ORDER, analyse
from .config import ROOT, load_config
from .data import Prepared, load_raw, prepare
from .figures import FIG_CHAPTER, REPORT_ORDER, SECTION, build_figures, figure_stem, label, plain_title

OUT = ROOT / "outputs"
INTER = OUT / "intermediate"

# code: (folder name, Excel sheet suffix, one-line description)
CHAPTERS = {
    "01A": ("assumptions", "Assumptions", "Loads and validates config/assumptions.yaml"),
    "01B": ("raw_transactions", "Raw_Transactions", "Loads the transactions sheet unchanged; record and attempt counts"),
    "01C": ("raw_customers", "Raw_Customers", "Loads customers; country and sector aliases; stale-date check"),
    "01D": ("raw_rates", "Raw_Rates", "Loads daily exchange rates unchanged"),
    "01E": ("data_quality", "Data_Quality", "The three flags, untranslatable records, SLL evidence, spike days, legacy codes, "
                                            "reconciliation with the brief, headline sensitivity"),
    "01F": ("rates", "Rates", "SLL restatement, spike screen, monthly average / month-end / 2022 base rates"),
    "01G": ("transactions", "Transactions", "USD translation of every record, flags, anomaly rules, exposure category"),
    "02": ("scale", "Scale", "Headline, exposure bridge, monthly series, three perspectives"),
    "03": ("concentration", "Concentration", "Payment type, market, currency, sector, Pareto, drivers, quintiles"),
    "04": ("diagnostics", "Diagnostics", "Anomaly tables and sensitivity, escalation, hard/mixed, persistence, tenure, lapse, Laney"),
    "05": ("january", "January", "January bridge and LMDI"),
    "06": ("fx", "FX", "Constant currency, by currency and year, volatility screen, month-end sensitivity"),
    "07": ("recovery", "Recovery", "Benchmark gap, scenarios, sensitivities, fee revenue remaining, break-even"),
    "08": ("recommendations", "Recommendations", "Prioritisation matrix, actions, monitoring triggers"),
}
SCRIPTS = {"00": "00_readme_and_environment.py", "09": "09_excel_workbook.py", "10": "10_report.py", "11": "11_validate.py"}
SCRIPTS.update({k: f"{k}_{v[0]}.py" for k, v in CHAPTERS.items()})
# 01E reports on flags and rates that 01F and 01G produce, so it runs after them. The numbering is unchanged.
ORDER = ["00", "01A", "01B", "01C", "01D", "01F", "01G", "01E", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11"]
ANALYSIS_CHAPTERS = ["02", "03", "04", "05", "06", "07", "08"]
# Blocks a chapter's figures need from other chapters (computed on the fly, not written to this chapter)
EXTRA_BLOCKS = {"01G": ["headline", "value"], "07": ["headline", "monthly"], "08": ["anomalies", "recovery", "customers"]}


def chapter_dir(code: str) -> Path:
    return OUT / f"{code}_{CHAPTERS[code][0]}"


def sheet_name(code: str) -> str:
    return f"{code}_{CHAPTERS[code][1]}"


def jsonable(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, pd.Timestamp):
        return o.strftime("%Y-%m-%d")
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    return o


def write_tables(res: dict, tdir: Path) -> dict:
    """Every DataFrame in `res` goes to tdir as CSV; everything else is returned as JSON-ready scalars."""
    tdir.mkdir(parents=True, exist_ok=True)

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
                out[k] = jsonable(v)
        return out
    return walk(res, "")


# ------------------------------------------------------------------------------------ caches
def get_raw(cfg: dict) -> dict:
    """The raw workbook's sheets, cached after the first read (reading the .xlsx takes about 20 seconds)."""
    pkl, src = INTER / "raw.pkl", Path(cfg["_root"]) / cfg["data"]["workbook"]
    if pkl.exists() and pkl.stat().st_mtime > src.stat().st_mtime:
        return pd.read_pickle(pkl)
    raw = load_raw(cfg)
    INTER.mkdir(parents=True, exist_ok=True)
    pd.to_pickle(raw, pkl)
    return raw


def save_prep(prep: Prepared) -> None:
    INTER.mkdir(parents=True, exist_ok=True)
    with open(INTER / "prepared.pkl", "wb") as fh:
        pickle.dump(prep, fh, protocol=pickle.HIGHEST_PROTOCOL)


def load_prep() -> tuple[dict, Prepared]:
    f = INTER / "prepared.pkl"
    if not f.exists():
        raise SystemExit("outputs/intermediate/prepared.pkl is missing. Run stage 01G first: python scripts/01G_transactions.py")
    with open(f, "rb") as fh:
        prep = pickle.load(fh)
    prep.tx.attrs["escalation_customers"] = prep.stats["escalation_customers"]
    return load_config(), prep


def save_res(code: str, res: dict) -> None:
    INTER.mkdir(parents=True, exist_ok=True)
    with open(INTER / f"res_{code}.pkl", "wb") as fh:
        pickle.dump(res, fh, protocol=pickle.HIGHEST_PROTOCOL)


def load_res(code: str) -> dict:
    f = INTER / f"res_{code}.pkl"
    if not f.exists():
        raise SystemExit(f"Results for stage {code} are missing. Run: python scripts/{SCRIPTS[code]}")
    with open(f, "rb") as fh:
        return pickle.load(fh)


def full_results(prep: Prepared | None = None) -> dict:
    """Every chapter's results merged into the single dict the report, Excel and validation read."""
    if prep is None:
        _, prep = load_prep()
    parts: dict = {}
    for code in ANALYSIS_CHAPTERS + ["01E"]:
        parts.update(load_res(code))
    res = {"stats": prep.stats}
    for k in BLOCK_ORDER:
        res[k] = parts[k]
    for k, v in parts.items():
        res.setdefault(k, v)            # extra blocks, e.g. the SLL-off reconciliation
    return res


def write_results_json(res: dict) -> dict:
    """outputs/results.json: every scalar (tables are CSV files in the chapter folders)."""
    scalars = {}
    for k, v in res.items():
        if isinstance(v, dict):
            scalars[k] = _scalars(v)
        elif isinstance(v, (pd.DataFrame, pd.Series)):
            continue
        else:
            scalars[k] = jsonable(v)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(scalars, indent=2), encoding="utf-8")
    return scalars


def _scalars(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, (pd.DataFrame, pd.Series)):
            continue
        out[k] = _scalars(v) if isinstance(v, dict) else jsonable(v)
    return out


# ------------------------------------------------------------------------------------ figures
_TEXT_KEYS = {"text", "name", "ticktext", "values", "hovertext"}


def _esc(v):
    if isinstance(v, str):
        return v.replace("$", "&#36;")
    if isinstance(v, (list, tuple, np.ndarray)):
        return [_esc(x) for x in v]
    return v


def _walk_escape(o, under_text: bool = False):
    if isinstance(o, dict):
        return {k: (_walk_escape(v, True) if k in _TEXT_KEYS else _walk_escape(v, under_text and k in ("cells", "header", "font"))) for k, v in o.items()}
    if isinstance(o, (list, tuple, np.ndarray)) and under_text:
        return [_walk_escape(x, True) for x in o]
    if isinstance(o, str) and under_text:
        return _esc(o)
    if isinstance(o, (list, tuple)):
        return [_walk_escape(x, under_text) for x in o]
    return o


def static_safe(fig):
    """A copy of the figure whose text cannot be read as LaTeX: Kaleido (as of 1.5) typesets any text holding two
    dollar signs as maths, which garbled titles such as "cells above $15K ... over $5K". The dollar sign is written
    as an HTML entity; tick formats are untouched."""
    import plotly.graph_objects as go
    d = fig.to_plotly_json()
    for k in ("layout", "data"):
        d[k] = _walk_escape(d[k], False) if k == "layout" else [_walk_escape(t, False) for t in d[k]]
    return go.Figure(d)


def write_figures(figs: dict, code: str) -> list[dict]:
    """PNG + HTML for every figure; SVG (report size) for the figures used in the report. Returns index rows."""
    import plotly.io as pio
    pio.defaults.mathjax = None
    fdir = chapter_dir(code) / "figures"
    fdir.mkdir(parents=True, exist_ok=True)
    for old in fdir.glob("fig*"):
        old.unlink()
    rows = []
    for slug, fig in figs.items():
        stem = figure_stem(slug)
        h = fig.layout.height or 460
        safe = static_safe(fig)
        safe.write_image(fdir / f"{stem}.png", width=1100, height=h, scale=2)
        fig.write_html(fdir / f"{stem}.html", include_plotlyjs="cdn")
        if slug in REPORT_ORDER:
            safe.write_image(fdir / f"{stem}.svg", width=860, height=round(h * 0.86))
        rows.append({"label": label(slug), "slug": slug, "section": SECTION[slug], "chapter": code, "in_report": slug in REPORT_ORDER,
                     "title": plain_title(fig), "file": stem, "dir": f"{chapter_dir(code).name}/figures"})
    pd.DataFrame(rows).to_csv(fdir / "index.csv", index=False)
    return rows


def rebuild_figure_index() -> pd.DataFrame:
    """Merge the chapters' indexes into outputs/figure_index.csv: report figures 1-16 first, then D1-D10."""
    parts = [pd.read_csv(f) for f in sorted(OUT.glob("*/figures/index.csv"))]
    idx = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    if len(idx):
        from .figures import DASHBOARD_ONLY
        rank = {s_: i for i, s_ in enumerate(REPORT_ORDER)}
        rank.update({s_: 100 + i for i, s_ in enumerate(DASHBOARD_ONLY)})
        idx = idx.assign(_k=idx.slug.map(rank)).sort_values("_k").drop(columns="_k")
        idx.to_csv(OUT / "figure_index.csv", index=False)
    return idx


def load_figure_index() -> pd.DataFrame:
    f = OUT / "figure_index.csv"
    if not f.exists():
        raise FileNotFoundError("outputs/figure_index.csv is missing; run the chapter stages (02-08, 01G) first.")
    return pd.read_csv(f)


def figure_file(slug: str, ext_order=("svg", "png")) -> Path:
    """Path of a figure's exported file, found through the one figure index."""
    idx = load_figure_index()
    hit = idx[idx.slug == slug]
    if hit.empty:
        raise KeyError(f"Figure '{slug}' is not in outputs/figure_index.csv")
    r = hit.iloc[0]
    for ext in ext_order:
        p = OUT / r["dir"] / f"{r['file']}.{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(f"No exported file for figure '{slug}' in {OUT / r['dir']}")


# ------------------------------------------------------------------------------------ chapter runner
def run_analysis_chapter(code: str) -> dict:
    """Stages 02-08 (and the figure of 01G): analyse the chapter's blocks, write tables and figures."""
    t0 = time.time()
    cfg, prep = load_prep()
    own = [b for b, c in BLOCK_CHAPTER.items() if c == code]
    res = analyse(prep, cfg, only=own + EXTRA_BLOCKS.get(code, []))
    mine = {k: res[k] for k in own if k in res}
    cdir = chapter_dir(code)
    tdir = cdir / "tables"
    if tdir.exists():
        for old in tdir.glob("*.csv"):
            old.unlink()
    scalars = write_tables(mine, tdir) if mine else {}
    if mine:
        save_res(code, mine)
        (cdir / "results.json").write_text(json.dumps(scalars, indent=2), encoding="utf-8")
    slugs = [s for s, c in FIG_CHAPTER.items() if c == code]
    rows = write_figures(build_figures(res, prep, slugs), code) if slugs else []
    rebuild_figure_index()
    return {"tables": len(list(tdir.glob("*.csv"))), "figures": len(rows), "seconds": time.time() - t0}
