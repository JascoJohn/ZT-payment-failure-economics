"""Interactive dashboard: the same 26 figures as the report, recomputed on the selection.

Run locally:   streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from payfail import analyse, load_config, prepare  # noqa: E402
from payfail.figures import FIGURES, REPORT_ORDER, build_all, label  # noqa: E402

st.set_page_config(page_title="The Economics of Payment Failure", layout="wide")

BASE = load_config()


# ---- cached pipeline ----------------------------------------------------------------------------
@st.cache_resource(show_spinner="Preparing data (rates, flags, anomaly rules)…")
def get_prep(rel_min: int, rel_mult: float, rel_succ: float, esc_min: int, esc_succ: float):
    cfg = copy.deepcopy(BASE)
    cfg["anomalies"]["relative"].update(min_failed=rel_min, multiple_of_prior_median=rel_mult, max_success_rate=rel_succ)
    cfg["anomalies"]["escalation"].update(min_failed=esc_min, max_success_rate=esc_succ)
    return cfg, prepare(cfg)


@st.cache_resource(show_spinner="Running the analysis on your selection…", max_entries=24)
def get_results(prep_key: tuple, start, end, countries: tuple, channels: tuple, ccys: tuple, exclude: str, margin: float):
    cfg, prep = get_prep(*prep_key)
    cfg = copy.deepcopy(cfg)
    cfg["recovery"]["optimistic_margin"] = margin
    tx = prep.tx
    m = (tx.period >= pd.Timestamp(start)) & (tx.period <= pd.Timestamp(end))
    if countries:
        m &= tx.country.isin(countries)
    if channels:
        m &= tx.pt.isin(channels)
    if ccys:
        m &= tx.ccy.isin(ccys)
    if exclude == "Extreme-volume anomalies":
        m &= ~tx.extreme
    elif exclude == "Anomalies and escalation":
        m &= tx.category.eq("Remaining")
    sub = tx[m].copy()
    res = analyse(prep, cfg, sub)
    return res, build_all(res, prep), len(sub)


# ---- sidebar ------------------------------------------------------------------------------------
_, prep0 = get_prep(1000, 50.0, 0.05, 5000, 0.05)
periods = sorted(prep0.tx.period.unique())
st.sidebar.title("Selection")
p0, p1 = st.sidebar.select_slider("Period", options=periods, value=(periods[0], periods[-1]),
                                  format_func=lambda d: pd.Timestamp(d).strftime("%b %Y"))
countries = st.sidebar.multiselect("Markets", sorted(prep0.tx.country.dropna().unique()))
channels = st.sidebar.multiselect("Payment types", sorted(prep0.tx.pt.dropna().unique()))
top_ccy = prep0.tx.groupby("ccy").att.sum().sort_values(ascending=False).index.tolist()
ccys = st.sidebar.multiselect("Currencies", top_ccy)
exclude = st.sidebar.radio("Exclude", ["Nothing", "Extreme-volume anomalies", "Anomalies and escalation"])

with st.sidebar.expander("Anomaly rules"):
    rel_min = st.number_input("Relative rule: minimum failed attempts", 100, 10000, 1000, 100)
    rel_mult = st.number_input("Relative rule: multiple of prior 6-month median", 5.0, 500.0, 50.0, 5.0)
    rel_succ = st.slider("Relative rule: maximum success rate", 0.0, 0.2, 0.05, 0.01)
    esc_min = st.number_input("Escalation trigger: minimum failed attempts", 500, 50000, 5000, 500)
    esc_succ = st.slider("Escalation trigger: maximum success rate", 0.0, 0.2, 0.05, 0.01)
with st.sidebar.expander("Recovery scenario"):
    margin = st.slider("Optimistic case: points below mobile money failure rate", 0.0, 0.3, 0.10, 0.01)

prep_key = (int(rel_min), float(rel_mult), float(rel_succ), int(esc_min), float(esc_succ))
res, figs, n = get_results(prep_key, p0, p1, tuple(countries), tuple(channels), tuple(ccys), exclude, float(margin))

# ---- body ---------------------------------------------------------------------------------------
st.title("The Economics of Payment Failure")
st.caption("ZT East Africa, Jan 2022 – Apr 2024. The figures are the report's figures, recomputed on the selection. "
           "Recorded fee amounts, not cash; translation effects, not realised FX gains or losses.")
default = (p0 == periods[0] and p1 == periods[-1] and not countries and not channels and not ccys
           and exclude == "Nothing" and prep_key == (1000, 50.0, 0.05, 5000, 0.05) and abs(margin - .10) < 1e-9)
if default:
    st.success("Default selection: every figure matches the report.")
else:
    st.info(f"Custom selection: {n:,} records. Figures that need data outside the selection show a notice.")

sections = list(dict.fromkeys(s for _, _, s, _ in FIGURES))
for tab, sec in zip(st.tabs(sections), sections):
    with tab:
        for _, slug, s, _ in FIGURES:
            if s == sec:
                if slug not in REPORT_ORDER:
                    st.caption(f"{label(slug)} is in the dashboard only; the report gives these numbers in a table.")
                st.plotly_chart(figs[slug], width="stretch", key=f"fig_{slug}")

with st.expander("Download the selection's tables"):
    for k in ["bridge", "monthly", "channels", "countries", "heat", "drivers", "matrix"]:
        v = res.get(k)
        if isinstance(v, pd.DataFrame):
            st.download_button(f"{k}.csv", v.to_csv(index=False).encode(), f"{k}.csv", "text/csv", key=f"dl_{k}")
