"""All measures used in the report, dashboard and workbook.

`analyse(prep, cfg)` returns a dict of scalars and DataFrames. Each block is independent and
guarded, so the dashboard can rerun it on a filtered subset (a market, a channel, a period)
without failing when a block has no data.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import Prepared, agg


def _safe(fn):
    def wrap(*a, **k):
        try:
            return fn(*a, **k)
        except (KeyError, ValueError, IndexError, ZeroDivisionError):
            return None
    wrap.__name__ = fn.__name__
    return wrap


TOP_N_OBSERVATIONS = 4        # "the four largest account-months" (Figure 11 and Section 4.1)
TOP_N_TANZANIA = 3            # "three of 127 Tanzanian USD card customers" (Section 7.3)
TOP_N_JAN_CARD = 3            # "the three January card accounts" (Section 5)


# --------------------------------------------------------------------------- headline
def headline(tx: pd.DataFrame) -> dict:
    t = agg(tx.assign(_k=1), "_k").iloc[0]
    fxok = tx[tx.fx_ok]
    return {"records": int(len(tx)), "attempts": int(t.att), "failed": int(t.f_att), "count_rate": t.fail_rate,
            "attempts_translatable": int(fxok.att.sum()), "records_translatable": int(len(fxok)),
            "fees": t.fee, "failed_fees": t.f_fee, "fee_share": t.fee_share, "succ_fees": t.fee - t.f_fee,
            "customers_with_failed_fees": int((tx.groupby("customer_id").f_fee.sum() > 0).sum()),
            "failed_records": int(tx.failed.sum()), "successful_records": int((~tx.failed).sum())}


def bridge(tx: pd.DataFrame) -> pd.DataFrame:
    order = ["Extreme-volume anomaly", "Escalation", "Remaining"]
    b = tx.groupby("category").agg(f_att=("f_att", "sum"), f_fee=("f_fee", "sum")).reindex(order).fillna(0)
    b["share"] = b.f_fee / b.f_fee.sum()
    return b.reset_index()


def monthly(tx: pd.DataFrame) -> pd.DataFrame:
    rem = tx[tx.category == "Remaining"]
    a, r = agg(tx, "period"), agg(rem, "period")
    comp = tx.groupby(["period", "category"]).f_fee.sum().unstack(fill_value=0)
    m = pd.DataFrame({"count_all": a.fail_rate, "count_rem": r.fail_rate, "share_all": a.fee_share,
                      "share_rem": r.fee_share, "failed_fees": a.f_fee, "attempts": a.att})
    for c, k in [("Remaining", "fees_remaining"), ("Extreme-volume anomaly", "fees_extreme"), ("Escalation", "fees_escalation")]:
        m[k] = comp[c] if c in comp else 0.0
    return m.reset_index()


# --------------------------------------------------------------------------- value and concentration
def value_block(df: pd.DataFrame) -> dict:
    s, f = df[~df.failed], df[df.failed]
    return {"value": df.val.sum(), "failed_value": f.val.sum(), "failed_value_share": f.val.sum() / df.val.sum(),
            "avg_failed_value": f.val.sum() / f.att.sum(), "avg_success_value": s.val.sum() / s.att.sum(),
            "failed_fee_intensity": f.fee.sum() / f.val.sum(), "success_fee_intensity": s.fee.sum() / s.val.sum()}


def concentration(tx: pd.DataFrame, by) -> pd.DataFrame:
    a = agg(tx, by)
    ok = tx[tx.fx_ok].groupby(by, observed=True)
    a["fee_per_failed_attempt"] = ok.f_fee.sum() / ok.f_att.sum()
    a["share_of_failed_fees"] = a.f_fee / tx.f_fee.sum()
    v = tx[~tx.value_excluded].groupby(by, observed=True).agg(val=("val", "sum"), f_val=("f_val", "sum"))
    a["failed_value"] = v.f_val
    return a.sort_values("f_fee", ascending=False).reset_index()


def pareto(tx: pd.DataFrame) -> pd.DataFrame:
    out = []
    for label, df in [("All records", tx), ("Excluding extreme-volume anomalies", tx[~tx.extreme])]:
        s = df.groupby("customer_id").f_fee.sum().sort_values(ascending=False)
        s = s[s > 0]
        if s.empty:
            continue
        c = s.cumsum() / s.sum()
        n = len(s)
        ks = sorted({1, 2, 3, 5, 10, 20, 30, max(1, round(n * 0.01)), 100, 200, 300, 500, 750, 1000, 1500, 2000, 3000, n})
        out += [{"series": label, "rank": k, "pct_customers": k / n * 100, "cum_share": float(c.iloc[k - 1]) * 100, "n": n}
                for k in ks if k <= n]
    return pd.DataFrame(out)


def drivers(tx: pd.DataFrame) -> pd.DataFrame:
    nb = tx[~tx.extreme]
    c = agg(nb, ["country", "pt"])
    c["share_of_attempts"] = c.att / c.att.sum()
    ok = nb[nb.fx_ok].groupby(["country", "pt"])
    c["f_att_ok"] = ok.f_att.sum()                       # failed attempts of translatable records: the denominator of the fee per failed attempt
    c["fee_per_failed_attempt"] = ok.f_fee.sum() / ok.f_att.sum()
    return c.sort_values("f_fee", ascending=False).reset_index()


def quintiles(tx: pd.DataFrame) -> pd.DataFrame:
    q = tx[~tx.value_excluded & tx.pt.isin(["card", "mobilemoney"]) & (tx.val > 0)].copy()
    q["avg_value"] = q.val / q.att
    q["quintile"] = q.groupby("pt").avg_value.transform(
        lambda s: pd.qcut(s.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int))
    g = q.groupby(["pt", "quintile"]).agg(floor=("avg_value", "min"), att=("att", "sum"), f_att=("f_att", "sum"),
                                         fee=("fee", "sum"), f_fee=("f_fee", "sum"))
    g["fail_rate"] = g.f_att / g.att
    g["fee_share"] = g.f_fee / g.fee
    return g.reset_index()


def quintile_versions(tx: pd.DataFrame) -> pd.DataFrame:
    esc = set(tx.attrs.get("escalation_customers", []))
    versions = [("All translatable records", tx), ("Excluding extreme-volume anomalies", tx[~tx.extreme]),
                ("Excluding escalation account(s)", tx[~tx.customer_id.isin(esc)]),
                ("Excluding value anomalies", tx[~tx.flag_value]),
                ("All three exclusions", tx[(tx.category == "Remaining") & ~tx.flag_value])]
    rows = []
    for label, df in versions:
        q = df[df.fx_ok & df.pt.isin(["card", "mobilemoney"]) & (df.val > 0)].copy()
        q["avg_value"] = q.val / q.att
        q["quintile"] = q.groupby("pt").avg_value.transform(
            lambda s: pd.qcut(s.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int))
        for p, d in q.groupby("pt"):
            top, rest = d[d.quintile == 5], d[d.quintile < 5]
            rows.append({"version": label, "pt": p, "q5_fail_rate": top.f_att.sum() / top.att.sum(),
                         "q1_4_fail_rate": rest.f_att.sum() / rest.att.sum(), "q5_failed_fees": top.f_fee.sum(),
                         "q5_largest_customer_share": top.groupby("customer_id").f_fee.sum().max() / max(top.f_fee.sum(), 1e-9)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- diagnostics
def anomaly_tables(prep: Prepared, tx: pd.DataFrame, cfg: dict) -> dict:
    cmc = prep.cmc[prep.cmc.set_index(["customer_id", "pt", "period"]).index.isin(
        tx.set_index(["customer_id", "pt", "period"]).index)]
    total = tx.f_fee.sum()
    obs = cmc[cmc.extreme].merge(prep.cust[["customer_id", "country"]], on="customer_id", how="left")
    obs = obs.sort_values("f_fee", ascending=False)[["customer_id", "country", "pt", "period", "f_att", "s_att", "prior_med", "f_fee"]]
    sens = []
    for name, col in [("loose", "extreme_loose"), ("agreed", "extreme"), ("strict", "extreme_strict")]:
        b = cmc[cmc[col]]
        sens.append({"thresholds": name, "observations": int(len(b)), "customers": int(b.customer_id.nunique()),
                     "f_fee": b.f_fee.sum(), "share": b.f_fee.sum() / total})
    esc = sorted(set(prep.stats["escalation_customers"]) & set(tx.customer_id))
    esc_series = (tx[tx.customer_id.isin(esc)].groupby("period").agg(f_att=("f_att", "sum"), s_att=("s_att", "sum"),
                                                                     f_fee=("f_fee", "sum")).reset_index())
    nb_esc = tx[tx.customer_id.isin(esc) & ~tx.extreme]
    profile = {"mobilemoney_attempts": int(nb_esc[nb_esc.pt == "mobilemoney"].att.sum()),
               "usd_card_attempts": int(nb_esc[(nb_esc.pt == "card") & (nb_esc.ccy == "USD")].att.sum()),
               "mobilemoney_ghs_share": float(nb_esc[(nb_esc.pt == "mobilemoney") & (nb_esc.ccy == "GHS")].att.sum() / max(nb_esc[nb_esc.pt == "mobilemoney"].att.sum(), 1))}
    return {"observations": obs.reset_index(drop=True), "sensitivity": pd.DataFrame(sens),
            "escalation_customers": esc, "escalation_series": esc_series, "escalation_profile": profile, "top_n": TOP_N_OBSERVATIONS}


def hard_mixed(prep: Prepared, tx: pd.DataFrame) -> dict:
    cmc = prep.cmc.merge(tx[["customer_id", "pt", "period"]].drop_duplicates(), on=["customer_id", "pt", "period"])
    c2 = cmc[~cmc.extreme & (cmc.f_att > 0)].copy()
    c2["class"] = np.where(c2.s_att == 0, "Hard", "Mixed")
    tot = c2.groupby("class").agg(observations=("att", "size"), f_att=("f_att", "sum"), f_fee=("f_fee", "sum"))
    ex = cmc[cmc.extreme]
    tot.loc["Extreme-volume anomaly"] = [len(ex), ex.f_att.sum(), ex.f_fee.sum()]
    tot["share_f_att"] = tot.f_att / tx.f_att.sum()
    tot["share_f_fee"] = tot.f_fee / tx.f_fee.sum()
    by_pt = c2.groupby(["pt", "class"]).f_fee.sum().unstack(fill_value=0)
    by_pt["anomalies"] = ex.groupby("pt").f_fee.sum()
    by_pt = by_pt.fillna(0)
    by_pt["hard_share"] = by_pt.get("Hard", 0) / (by_pt.get("Hard", 0) + by_pt.get("Mixed", 0))
    return {"totals": tot.reset_index().rename(columns={"index": "class"}), "by_channel": by_pt.reset_index()}


def customers(tx: pd.DataFrame, cfg: dict) -> dict:
    c = cfg["customers"]
    nb = tx[~tx.extreme]
    cm = nb.groupby(["customer_id", "period"]).agg(att=("att", "sum"), f_att=("f_att", "sum"), f_fee=("f_fee", "sum")).reset_index()
    cm["elevated"] = cm.f_att / cm.att >= c["elevated_rate"]
    pc = cm.groupby("customer_id").agg(months=("period", "nunique"), elevated=("elevated", "sum"),
                                       f_att=("f_att", "sum"), f_fee=("f_fee", "sum"))
    pc["eligible"] = pc.months >= c["min_active_months"]
    pc["persistent"] = pc.eligible & (pc.elevated / pc.months >= c["persistent_share_of_months"])

    start = pd.Timestamp(c["lapse_window_start"])
    seen = tx.groupby("customer_id").period.agg(["min", "max"])
    pre = seen[seen["min"] < start]
    lapsed = set(pre[pre["max"] < start].index)
    hist = agg(nb[nb.period < start].assign(lapsed=lambda d: d.customer_id.isin(lapsed)), "lapsed")

    grp = nb.merge(pc[["persistent", "eligible"]].reset_index(), on="customer_id")
    grp = grp[grp.eligible]
    g2 = agg(grp, "persistent")
    elig = pc[pc.eligible]
    persist = {
        "eligible": int(pc.eligible.sum()), "persistent": int(pc.persistent.sum()),
        "share_f_att": pc.loc[pc.persistent, "f_att"].sum() / pc.f_att.sum(),
        "share_f_fee": pc.loc[pc.persistent, "f_fee"].sum() / pc.f_fee.sum(),
        "persistent_f_fee": pc.loc[pc.persistent, "f_fee"].sum(),
        "one_off_elevated": int(((pc.elevated >= 1) & ~pc.persistent).sum()),
        "fee_share_persistent": g2.loc[True, "fee_share"] if True in g2.index else np.nan,
        "fee_share_other": g2.loc[False, "fee_share"] if False in g2.index else np.nan,
        "lapse_persistent": elig[elig.persistent].index.isin(lapsed).mean(),
        "lapse_other": elig[~elig.persistent].index.isin(lapsed).mean(),
    }
    su = nb.sign_up_date.dt.to_period("M").dt.to_timestamp()
    ten = (nb.period.dt.year - su.dt.year) * 12 + (nb.period.dt.month - su.dt.month)
    band = pd.cut(ten, c["tenure_bands"], labels=["0-3 months", "4-12 months", "13-24 months", "25+ months"])
    tb = agg(nb.assign(band=band), "band")
    tb["share_of_failed_fees"] = tb.f_fee / tb.f_fee.sum()
    lapse = {"active_before": int(len(pre)), "lapsed": int(len(lapsed)), "lapse_rate": len(lapsed) / max(len(pre), 1),
             "count_rate_lapsed": hist.loc[True, "fail_rate"] if True in hist.index else np.nan,
             "count_rate_retained": hist.loc[False, "fail_rate"] if False in hist.index else np.nan,
             "fee_share_lapsed": hist.loc[True, "fee_share"] if True in hist.index else np.nan,
             "fee_share_retained": hist.loc[False, "fee_share"] if False in hist.index else np.nan}
    # who is counted as lapsed: how many were active in only one or two months, and how many had an earlier gap of three months or more
    months_act = tx[tx.customer_id.isin(lapsed)].groupby("customer_id").period.nunique()

    def longest_gap(p):
        q = sorted(p.unique())
        pos = [(x.year - q[0].year) * 12 + x.month - q[0].month for x in q]
        return max((b - a - 1 for a, b in zip(pos, pos[1:])), default=0)
    gaps = tx[tx.customer_id.isin(lapsed)].groupby("customer_id").period.apply(longest_gap)
    lapse["few_months_share"] = float((months_act <= 2).mean()) if len(months_act) else np.nan
    lapse["few_months_n"] = int((months_act <= 2).sum())
    lapse["gap3_share"] = float((gaps >= 3).mean()) if len(gaps) else np.nan
    lapse["gap3_n"] = int((gaps >= 3).sum())
    return {"persistence": persist, "tenure": tb.reset_index(), "lapse": lapse, "table": pc.reset_index()}


def laney_patterns(tx: pd.DataFrame, cfg: dict) -> dict:
    p = cfg["patterns"]
    cm = tx.groupby(["country", "pt", "period"]).agg(att=("att", "sum"), f_att=("f_att", "sum"), f_fee=("f_fee", "sum")).reset_index()
    cm["p"] = cm.f_att / cm.att
    top = tx.groupby(["country", "pt", "period", "customer_id"]).f_att.sum().reset_index()
    br = top.groupby(["country", "pt", "period"]).f_att.agg(["max", "sum"]).reset_index()
    br["top_customer_share"] = br["max"] / br["sum"].replace(0, np.nan)
    cm = cm.merge(br[["country", "pt", "period", "top_customer_share"]], on=["country", "pt", "period"], how="left")
    rows, excluded, signals, series = [], [], [], []
    for (c, pt), d in cm.groupby(["country", "pt"]):
        d = d.sort_values("period")
        e = d[d.att >= p["min_month_attempts"]].copy()
        base = {"country": c, "pt": pt, "att": int(d.att.sum()), "f_fee": d.f_fee.sum(), "eligible_months": int(len(e))}
        if len(e) < p["min_eligible_months"]:
            excluded.append(base)
            continue
        pbar = e.f_att.sum() / e.att.sum()
        sig = np.sqrt(pbar * (1 - pbar) / e.att)
        z = (e.p - pbar) / sig
        sz = np.abs(np.diff(z.values)).mean() / 1.128
        e["centre"], e["ucl"], e["lcl"] = pbar, pbar + 3 * sig * sz, (pbar - 3 * sig * sz).clip(lower=0)
        out = e[e.p > e.ucl]
        first6, last6 = e.p.iloc[:6].mean(), e.p.iloc[-6:].mean()
        flags = {"Structural": e.p.median() >= p["structural_median"],
                 "Deteriorating": (last6 - first6) >= p["deteriorating_pp"],
                 "Episodic": len(out) > 0, "Unstable": e.p.std() >= p["unstable_sd"]}
        fl = [k for k, v in flags.items() if v] or ["Stable"]
        rows.append({**base, "median_rate": e.p.median(), "first6": first6, "last6": last6, "sd": e.p.std(),
                     "sigma_z": sz, "signals": int(len(out)), "flags": ", ".join(fl), "primary": fl[0],
                     **{f"flag_{k.lower()}": v for k, v in flags.items()}, "flag_stable": fl == ["Stable"]})
        signals += [{"country": c, "pt": pt, "period": r.period, "rate": r.p, "ucl": r.ucl,
                     "top_customer_share": r.top_customer_share, "f_fee": r.f_fee} for r in out.itertuples()]
        series.append(e.assign(country=c, pt=pt)[["country", "pt", "period", "att", "p", "centre", "ucl", "lcl"]])
    pat = pd.DataFrame(rows).sort_values("f_fee", ascending=False) if rows else pd.DataFrame()
    exc = pd.DataFrame(excluded).sort_values("f_fee", ascending=False) if excluded else pd.DataFrame()
    return {"patterns": pat, "excluded": exc, "signals": pd.DataFrame(signals),
            "series": pd.concat(series) if series else pd.DataFrame(),
            "tests": int(sum(r["eligible_months"] for r in rows)),
            "excluded_share": exc.f_fee.sum() / tx.f_fee.sum() if len(exc) else 0.0}


# --------------------------------------------------------------------------- January LMDI
def _logmean(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (a - b) / (np.log(a) - np.log(b))
    return np.where(np.isclose(a, b), a, out)


def january(tx: pd.DataFrame, cfg: dict) -> dict:
    j = cfg["january"]
    basep = pd.date_range(j["baseline_start"], j["baseline_end"], freq="MS")
    tgt = pd.Timestamp(j["target"])
    n = len(basep)
    nb = tx[~tx.extreme]

    def avg(df, col, mask):
        return df.loc[mask(df), col].sum()
    inb = lambda d: d.period.isin(basep)
    ist = lambda d: d.period == tgt
    b_all, j_all = avg(tx, "f_fee", inb) / n, avg(tx, "f_fee", ist)
    b_ex = tx[tx.extreme & tx.period.isin(basep)].f_fee.sum() / n
    j_ex = tx[tx.extreme & (tx.period == tgt)].f_fee.sum()
    b_nb, j_nb = avg(nb, "f_fee", inb) / n, avg(nb, "f_fee", ist)
    b_cc, j_cc = avg(nb, "f_fee_cc", inb) / n, avg(nb, "f_fee_cc", ist)
    fx_effect = (j_nb - j_cc) - (b_nb - b_cc)

    def cells(df, mask, k):
        d = df[mask(df) & df.fx_ok]
        return d.groupby(["country", "pt"]).agg(att=("att", "sum"), f_att=("f_att", "sum"), f_cc=("f_fee_cc", "sum")) / k
    c = cells(nb, inb, n).join(cells(nb, ist, 1), lsuffix="0", rsuffix="1", how="outer").fillna(0)
    both = c[(c.f_cc0 > 0) & (c.f_cc1 > 0)].copy()
    N0, N1 = both.att0.sum(), both.att1.sum()
    w = _logmean(both.f_cc1, both.f_cc0)
    eff = {"Volume": float((w * np.log(N1 / N0)).sum()),
           "Mix": float((w * np.log((both.att1 / N1) / (both.att0 / N0))).sum()),
           "Failure rate": float((w * np.log((both.f_att1 / both.att1) / (both.f_att0 / both.att0))).sum()),
           "Fee yield": float((w * np.log((both.f_cc1 / both.f_att1) / (both.f_cc0 / both.f_att0))).sum())}
    entry_exit = float((c.f_cc1.sum() - c.f_cc0.sum()) - (both.f_cc1.sum() - both.f_cc0.sum()))
    comp = pd.DataFrame([("Baseline", b_all), ("Extreme-volume anomalies", j_ex - b_ex), ("FX translation", fx_effect),
                         *eff.items(), ("Entry/exit cells", entry_exit), ("January", j_all)], columns=["component", "usd"])
    cells_tbl = both.assign(rate0=both.f_att0 / both.att0, rate1=both.f_att1 / both.att1,
                            yield0=both.f_cc0 / both.f_att0, yield1=both.f_cc1 / both.f_att1).reset_index()
    jan_anoms = tx[tx.extreme & (tx.period == tgt)].groupby(["customer_id", "pt"]).f_fee.sum().sort_values(ascending=False)
    return {"components": comp, "baseline_all": b_all, "january_all": j_all, "baseline_extreme": b_ex, "january_extreme": j_ex,
            "baseline_nonanomalous": b_nb, "january_nonanomalous": j_nb, "fx_effect": fx_effect, "lmdi": eff,
            "entry_exit": entry_exit, "cells_used": int(len(both)), "cells_total": int(len(c)),
            "residual": float(j_all - b_all - (j_ex - b_ex) - fx_effect - sum(eff.values()) - entry_exit),
            "top_n_card": TOP_N_JAN_CARD, "top3_card_accounts": float(jan_anoms.xs("card", level="pt").head(TOP_N_JAN_CARD).sum()) if "card" in jan_anoms.index.get_level_values("pt") else 0.0,
            "fee_share_nonanomalous_jan": nb[nb.period == tgt].f_fee.sum() / nb[nb.period == tgt].fee.sum(),
            "fee_share_nonanomalous_base": nb[nb.period.isin(basep)].f_fee.sum() / nb[nb.period.isin(basep)].fee.sum(),
            "count_rate_nonanomalous_jan": nb[nb.period == tgt].f_att.sum() / nb[nb.period == tgt].att.sum(),
            "cells": cells_tbl}


# --------------------------------------------------------------------------- FX
def fx_analysis(prep: Prepared, tx: pd.DataFrame, cfg: dict) -> dict:
    lc = tx[(tx.ccy != "USD") & tx.fx_ok]
    by_year = lc.assign(year=lc.period.dt.year).groupby("year").agg(reported=("fee", "sum"), constant=("fee_cc", "sum"))
    by_year["effect"] = by_year.reported - by_year.constant
    by_ccy = lc.groupby("ccy").agg(reported=("fee", "sum"), constant=("fee_cc", "sum"))
    by_ccy["effect"] = by_ccy.reported - by_ccy.constant
    mr = prep.rates_monthly
    first = mr[mr.period == mr.period.min()].set_index("ccy").r_avg
    last = mr[mr.period == mr.period.max()].set_index("ccy").r_avg
    by_ccy["depreciation"] = (last / first - 1).reindex(by_ccy.index)
    by_ccy = by_ccy.sort_values("effect")
    measures = pd.DataFrame({"measure": ["Fees on failed transactions", "Successful-transaction fees"],
                             "reported": [tx.f_fee.sum(), tx.fee.sum() - tx.f_fee.sum()],
                             "constant": [tx.f_fee_cc.sum(), tx.fee_cc.sum() - tx.f_fee_cc.sum()]})
    measures["difference"] = measures.reported - measures.constant
    scr = cfg["fx"]["volatility_screen"]
    main = ["NGN", "GHS", "ZMW", "KES", "TZS", "UGX"]
    m = mr[mr.ccy.isin(main)]
    ias = m.groupby("ccy").agg(months=("period", "size"), months_above=("range_pct", lambda s: int((s > scr).sum())),
                               avg_range=("range_pct", "mean"), max_range=("range_pct", "max")).reindex(main).reset_index()
    flagged = tx.range_pct > scr
    return {"by_year": by_year.reset_index(), "by_currency": by_ccy.reset_index(), "measures": measures,
            "local_reported": lc.fee.sum(), "local_constant": lc.fee_cc.sum(),
            "local_share_of_fees": lc.fee.sum() / tx.fee.sum(), "ias_screen": ias,
            "flagged_avg": tx.loc[flagged, "fee"].sum(), "flagged_end": tx.loc[flagged, "fee_end"].sum(),
            "failed_fees_month_end": tx.f_fee_end.sum()}


# --------------------------------------------------------------------------- recovery and prioritisation
def _best_window(df: pd.DataFrame, periods, k: int, min_att: int) -> float:
    d = df.groupby("period")[["att", "f_att"]].sum().reindex(periods, fill_value=0)
    ra, rf = d.att.rolling(k).sum(), d.f_att.rolling(k).sum()
    ok = ra >= min_att
    return float((rf[ok] / ra[ok]).min()) if ok.any() else np.nan


def bootstrap_interval(uc: pd.DataFrame, nb: pd.DataFrame, r: dict, point: float) -> dict:
    """Customer-resampling interval for the base case. Within each market, customers (those with USD card or mobile money
    activity) are drawn with replacement, and the base case is recomputed from the resampled card and mobile money totals,
    fee per successful payment included. Fixed seed; settings in config recovery.bootstrap."""
    b = r.get("bootstrap", {"replicates": 1000, "seed": 2026, "interval": 0.90})
    card = uc.groupby(["country", "customer_id"]).agg(att=("att", "sum"), f=("f_att", "sum"), s=("s_att", "sum"), fee=("fee", "sum"), ff=("f_fee", "sum"))
    mmx = nb[nb.pt == "mobilemoney"].groupby(["country", "customer_id"]).agg(att=("att", "sum"), f=("f_att", "sum"))
    markets = sorted(card.index.get_level_values(0).unique())
    cg = {k: card.xs(k, level=0) for k in markets}
    mg = {k: mmx.xs(k, level=0) for k in markets if k in mmx.index.get_level_values(0)}
    ids = {k: np.union1d(cg[k].index.values, mg[k].index.values if k in mg else []) for k in markets}
    rng = np.random.default_rng(b["seed"])
    out, tz_share = [], []
    for _ in range(int(b["replicates"])):
        crow, mrow = [], []
        for k in markets:
            pick = rng.choice(ids[k], len(ids[k]), replace=True)
            crow.append(cg[k].reindex(pick).dropna().assign(country=k))
            if k in mg:
                mrow.append(mg[k].reindex(pick).dropna().assign(country=k))
        C = pd.concat(crow).groupby("country")[["att", "f", "s", "fee", "ff"]].sum()
        M = pd.concat(mrow).groupby("country")[["att", "f"]].sum()
        sfee = C.fee - C.ff
        overall = sfee.sum() / C.s.sum()
        fps = np.where(C.s >= r["min_successes_for_local_fee"], sfee / C.s.replace(0, np.nan), overall)
        mm_rate = (M.f / M.att).reindex(C.index)
        add = (C.att * (C.f / C.att - mm_rate).clip(lower=0)).fillna(0)
        out.append(float((add * fps).sum()))
    a = np.array(out)
    lo, hi = (1 - b["interval"]) / 2 * 100, (1 + b["interval"]) / 2 * 100
    return {"low": float(np.percentile(a, lo)), "median": float(np.percentile(a, 50)), "high": float(np.percentile(a, hi)),
            "replicates": int(b["replicates"]), "seed": int(b["seed"]), "level": float(b["interval"]), "point": float(point),
            "customers": {k: int(len(ids[k])) for k in markets}}


def recovery(prep: Prepared, tx: pd.DataFrame, cfg: dict) -> dict:
    r = cfg["recovery"]
    nb = tx[~tx.extreme]
    uc = nb[(nb.ccy == "USD") & (nb.pt == "card")]
    mm = agg(nb[nb.pt == "mobilemoney"], "country")
    t = uc.groupby("country").agg(att=("att", "sum"), f_att=("f_att", "sum"), s_att=("s_att", "sum"),
                                  fee=("fee", "sum"), f_fee=("f_fee", "sum"))
    t["s_fee"] = t.fee - t.f_fee
    t["rate"] = t.f_att / t.att
    overall = t.s_fee.sum() / t.s_att.sum()
    t["fee_per_success"] = np.where(t.s_att >= r["min_successes_for_local_fee"], t.s_fee / t.s_att.replace(0, np.nan), overall)
    t["best_window"] = [_best_window(uc[uc.country == c], prep.periods, r["best_window_months"], r["best_window_min_attempts"]) for c in t.index]
    t["mm_rate"] = mm.fail_rate.reindex(t.index)

    def run(target):
        add = (t.att * (t.rate - target.reindex(t.index)).clip(lower=0)).fillna(0)
        return add, add * t.fee_per_success
    targets = {"Conservative": t.best_window, "Base": t.mm_rate, "Optimistic": (t.mm_rate - r["optimistic_margin"]).clip(lower=0)}
    scen, by_mkt = [], {}
    for name, tgt in targets.items():
        add, rec = run(tgt)
        by_mkt[name] = rec
        scen.append({"scenario": name, "additional_successes": add.sum(), "incremental_fees": rec.sum(),
                     "annual": rec.sum() * 12 / len(prep.periods), "share_of_recorded_fees": rec.sum() / tx.fee.sum(),
                     "share_of_addressable": rec.sum() / t.f_fee.sum()})
    t["target_base"] = t.mm_rate
    t["reduction_base"] = (t.rate - t.mm_rate).clip(lower=0)
    t["additional_base"], t["incremental_base"] = run(t.mm_rate)

    # same-customer comparison
    nbc = nb.assign(is_card=(nb.pt == "card") & (nb.ccy == "USD"), is_mm=nb.pt == "mobilemoney")
    g = nbc.groupby(["customer_id", "country"])
    cc = pd.DataFrame({"card_att": g.apply(lambda d: d.loc[d.is_card, "att"].sum(), include_groups=False),
                       "card_f": g.apply(lambda d: d.loc[d.is_card, "f_att"].sum(), include_groups=False),
                       "mm_att": g.apply(lambda d: d.loc[d.is_mm, "att"].sum(), include_groups=False),
                       "mm_f": g.apply(lambda d: d.loc[d.is_mm, "f_att"].sum(), include_groups=False)})
    dual = cc[(cc.card_att > 0) & (cc.mm_att > 0)].reset_index()
    dc = dual.groupby("country")[["card_att", "card_f", "mm_att", "mm_f"]].sum()
    dc["card_rate"], dc["mm_rate"] = dc.card_f / dc.card_att, dc.mm_f / dc.mm_att
    dc["customers"] = dual.groupby("country").size()
    gap = pd.DataFrame({"card_all": t.rate, "mm_all": t.mm_rate}).join(dc[["card_rate", "mm_rate", "customers"]].rename(
        columns={"card_rate": "card_same", "mm_rate": "mm_same"}))
    _, rec_same = run(dc.mm_rate)

    # benchmark sensitivity: mobile money rates without the escalation account(s), which sit in the benchmark
    esc = list(prep.stats.get("escalation_customers", []))
    mm_x = agg(nb[(nb.pt == "mobilemoney") & ~nb.customer_id.isin(esc)], "country").fail_rate.reindex(t.index)
    add_x, rec_x = run(mm_x)
    dual_x = dual[~dual.customer_id.isin(esc)]
    dcx = dual_x.groupby("country")[["card_att", "card_f", "mm_att", "mm_f"]].sum()
    dcx["card_rate"], dcx["mm_rate"] = dcx.card_f / dcx.card_att, dcx.mm_f / dcx.mm_att
    _, rec_same_x = run(dcx.mm_rate)
    mm_rows_x = nb[(nb.pt == "mobilemoney") & ~nb.customer_id.isin(esc) & nb.country.isin(t.index)]
    bench_x = {"accounts": esc, "mm_rate": mm_x, "incremental": rec_x.sum(), "by_market": rec_x, "additional": add_x.sum(),
               "mm_all": mm_rows_x.f_att.sum() / mm_rows_x.att.sum(),
               "same_card": dcx.card_f.sum() / dcx.card_att.sum(), "same_mm": dcx.mm_f.sum() / dcx.mm_att.sum(),
               "same_customers": int(len(dual_x)), "same_rates": dcx[["card_rate", "mm_rate"]], "same_incremental": rec_same_x.sum()}

    # same-month failure offset (mechanical upper bound)
    ucm = uc.groupby(["customer_id", "period", "country"]).agg(f_att=("f_att", "sum"), s_att=("s_att", "sum")).reset_index()
    ucm["offset"] = np.minimum(ucm.f_att, ucm.s_att)
    off = ucm.groupby("country").offset.sum().reindex(t.index, fill_value=0)
    adj_att, adj_rate = t.att - off, (t.f_att - off) / (t.att - off)
    rec_off = ((adj_att * (adj_rate - t.mm_rate).clip(lower=0)).fillna(0) * t.fee_per_success).sum()

    # sensitivity: some zero-success USD card customer-months may be correct rejections (including card testing), so leave them out
    cm_ = uc.groupby(["customer_id", "period", "country"]).agg(att=("att", "sum"), f=("f_att", "sum"), s=("s_att", "sum")).reset_index()
    keep_ = cm_[cm_.s > 0].groupby("country")[["att", "f"]].sum().reindex(t.index)
    add_h = (keep_.att * (keep_.f / keep_.att - t.mm_rate).clip(lower=0)).fillna(0)
    no_rej = {"incremental": float((add_h * t.fee_per_success).sum()), "additional": float(add_h.sum()),
              "share_of_failed_attempts": float(cm_[cm_.s == 0].f.sum() / cm_.f.sum()), "customer_months": int((cm_.s == 0).sum()),
              "failed_attempts": int(cm_[cm_.s == 0].f.sum())}
    tzc = uc[uc.country == "Tanzania"].groupby("customer_id").agg(fee=("fee", "sum"), ff=("f_fee", "sum"))
    tzs = (tzc.fee - tzc.ff).sort_values(ascending=False)
    tz_conc = {"customers": int(len(tzs)), "top_n": TOP_N_TANZANIA, "top_share": float(tzs.head(TOP_N_TANZANIA).sum() / tzs.sum())}
    base = by_mkt["Base"].sum()
    interval = bootstrap_interval(uc, nb, r, base)
    return {"markets": t.reset_index(), "scenarios": pd.DataFrame(scen), "by_market": pd.DataFrame(by_mkt).reset_index(),
            "addressable_f_fee": t.f_fee.sum(), "addressable_f_att": int(t.f_att.sum()), "total_att": int(t.att.sum()),
            "fee_per_success_overall": overall, "breakeven": base / max(t.additional_base.sum(), 1),
            "gap": gap.reset_index(),
            "gap_totals": {"card_all": t.f_att.sum() / t.att.sum(), "mm_all": mm.loc[t.index].f_att.sum() / mm.loc[t.index].att.sum(),
                           "card_same": dc.card_f.sum() / dc.card_att.sum(), "mm_same": dc.mm_f.sum() / dc.mm_att.sum(),
                           "customers": int(len(dual))},
            "same_customer": {"incremental": rec_same.sum(), "card_att_share": dual.card_att.sum() / t.att.sum(),
                              "top_customer_share": dual.card_att.max() / dual.card_att.sum()},
            "offset": {"removed": int(off.sum()), "removed_share": off.sum() / t.f_att.sum(), "incremental": rec_off},
            "benchmark_ex_escalation": bench_x, "no_rejections": no_rej, "interval": interval,
            "tanzania_concentration": tz_conc,
            "contribution": pd.DataFrame({"cost_ratio": r["cost_ratios"], "contribution": [base * (1 - c) for c in r["cost_ratios"]]})}


def prioritisation(prep: Prepared, tx: pd.DataFrame, cfg: dict, patterns: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
    r, p = cfg["recovery"], cfg["patterns"]
    esc = set(prep.stats["escalation_customers"])
    nb = tx[~tx.extreme]
    cells = agg(nb, ["country", "pt"])
    cells["failed_value"] = nb[~nb.value_excluded].groupby(["country", "pt"]).f_val.sum()
    sfee = (cells.fee - cells.f_fee) / (cells.att - cells.f_att).replace(0, np.nan)
    mm = agg(nb[nb.pt == "mobilemoney"], "country").fail_rate
    pat = patterns.set_index(["country", "pt"]) if len(patterns) else pd.DataFrame()
    top = nb[nb.fx_ok].groupby(["country", "pt", "customer_id"]).f_fee.sum()
    topshare = top.groupby(level=[0, 1]).max() / top.groupby(level=[0, 1]).sum()
    fxcov = nb.assign(ok_att=np.where(nb.fx_ok, nb.att, 0)).groupby(["country", "pt"]).agg(o=("ok_att", "sum"), a=("att", "sum"))
    rows = []
    for (c, pt), d in cells[cells.f_fee > 1000].sort_values("f_fee", ascending=False).iterrows():
        sub = nb[(nb.country == c) & (nb.pt == pt)]
        best = _best_window(sub, prep.periods, r["best_window_months"], r["best_window_min_attempts"])
        internal = max(d.fail_rate - best, 0) * d.att * sfee.loc[(c, pt)] if not np.isnan(best) else 0.0
        cross = max(d.fail_rate - mm.get(c, np.nan), 0) * d.att * sfee.loc[(c, pt)] if pt == "card" and c in mm.index else np.nan
        pr = pat.loc[(c, pt)] if (c, pt) in pat.index else None
        months = int(pr["eligible_months"]) if pr is not None else 0
        cov = fxcov.loc[(c, pt), "o"] / fxcov.loc[(c, pt), "a"]
        data_conf = "High" if months >= p["high_confidence_months"] and cov >= 0.99 else ("Medium" if months >= p["min_eligible_months"] else "Low")
        ts = float(topshare.get((c, pt), np.nan))
        sig = signals[(signals.country == c) & (signals.pt == pt)] if len(signals) else signals
        if ts > 0.5:
            diag = "Low: one customer holds most of it"
        elif pr is not None and pr["primary"] == "Episodic" and len(sig) and (sig.top_customer_share < 0.5).all() and pr["median_rate"] < 0.5:
            diag = "Low: signals near the limit"
        elif pr is not None and months >= p["high_confidence_months"] and "Structural" in pr["flags"]:
            diag = "High"
        else:
            diag = "Medium"
        if pt == "card" and diag == "High" and d.f_fee >= 150_000 and internal >= 15_000:
            action = "Prioritise"
        elif pt == "card" and pr is not None and "Structural" in pr["flags"] and d.f_fee >= 150_000:
            action = "Prioritise" if internal >= 15_000 else "Investigate root cause"
        elif ts > 0.5 and len(set(top.loc[(c, pt)].sort_values().index[-1:]) & esc):
            action = "Contain escalation account"
        else:
            action = "Monitor"
        rows.append({"country": c, "pt": pt, "fail_rate": d.fail_rate, "f_fee": d.f_fee, "att": d.att,
                     "failed_value": d.failed_value, "internal_potential": internal, "cross_channel_potential": cross,
                     "persistence": pr["flags"] if pr is not None else "Too little data", "data_confidence": data_conf,
                     "diagnostic_confidence": diag, "top_customer_share": ts, "action": action})
    return pd.DataFrame(rows)


def sensitivity(tx: pd.DataFrame) -> pd.DataFrame:
    def h(df, col="fee", fcol="f_fee"):
        return {"f_fee": df[fcol].sum(), "fee_share": df[fcol].sum() / df[col].sum(), "count_rate": df.f_att.sum() / df.att.sum()}
    rows = [("Report basis", h(tx)), ("Excluding value anomalies and untranslatable records", h(tx[~tx.value_excluded])),
            ("Month-end rates", h(tx, "fee_end", "f_fee_end")), ("2022 constant currency", h(tx, "fee_cc", "f_fee_cc")),
            ("Excluding extreme-volume anomalies", h(tx[~tx.extreme])),
            ("Also excluding escalation account(s)", h(tx[tx.category == "Remaining"]))]
    return pd.DataFrame([{"treatment": k, **v} for k, v in rows])


# --------------------------------------------------------------------------- orchestration
def remaining_mix(tx: pd.DataFrame) -> dict:
    rem = tx[tx.category == "Remaining"]
    return {"total": rem.f_fee.sum(), "card": rem.loc[rem.pt == "card", "f_fee"].sum(),
            "usd_card": rem.loc[(rem.pt == "card") & (rem.ccy == "USD"), "f_fee"].sum(),
            "mobilemoney": rem.loc[rem.pt == "mobilemoney", "f_fee"].sum()}


def customer_concentration(tx: pd.DataFrame) -> dict:
    nb = tx[~tx.extreme]
    allc = tx.groupby("customer_id").f_fee.sum()
    top = allc[allc > 0].sort_values(ascending=False)          # ranked population: customers with failed fees
    topn = nb.groupby("customer_id").f_fee.sum().sort_values(ascending=False)
    n1 = max(1, round(len(top) * 0.01))
    return {"customers": int(len(top)), "customers_transacting": int(len(allc)),
            "top10": top.head(10).sum() / top.sum(),
            "top1pct_n": n1, "top1pct": top.head(n1).sum() / top.sum(),
            "top10_ex_extreme": topn.head(10).sum() / topn.sum()}


# Which chapter owns each block. Chapter scripts (scripts/02_scale.py ...) run only their own blocks.
# "01E" is Data quality and sensitivity (Appendix B); the SLL-off reconciliation lives in payfail.dq.
BLOCK_CHAPTER = {
    "headline": "02", "bridge": "02", "monthly": "02", "value": "02", "remaining_mix": "02",
    "channels": "03", "countries": "03", "currencies": "03", "sectors": "03", "heat": "03", "pareto": "03",
    "drivers": "03", "quintiles": "03", "quintile_versions": "03", "customer_concentration": "03",
    "anomalies": "04", "hard_mixed": "04", "customers": "04", "laney": "04",
    "january": "05", "fx": "06", "recovery": "07", "matrix": "08", "sensitivity": "01E",
}
BLOCK_DEPS = {"matrix": ["laney"]}          # blocks another block needs as input
BLOCK_ORDER = ["headline", "bridge", "monthly", "value", "channels", "countries", "currencies", "sectors", "heat",
               "pareto", "drivers", "quintiles", "quintile_versions", "anomalies", "hard_mixed", "customers", "laney",
               "january", "fx", "recovery", "sensitivity", "matrix", "remaining_mix", "customer_concentration"]


def analyse(prep: Prepared, cfg: dict, tx: pd.DataFrame | None = None, only=None) -> dict:
    """Run every block (or just those named in `only`, plus their inputs).
    Pass `tx` (a filtered copy of prep.tx) to analyse a subset."""
    tx = prep.tx if tx is None else tx
    tx.attrs["escalation_customers"] = prep.stats["escalation_customers"]
    want = None
    if only is not None:
        want = set(only)
        for b in list(want):
            want.update(BLOCK_DEPS.get(b, []))
    res = {"stats": prep.stats}
    fns = {
        "headline": lambda: headline(tx), "bridge": lambda: bridge(tx), "monthly": lambda: monthly(tx),
        "value": lambda: value_block(tx[~tx.value_excluded]),
        "channels": lambda: concentration(tx, "pt"), "countries": lambda: concentration(tx, "country"),
        "currencies": lambda: concentration(tx, "ccy"), "sectors": lambda: concentration(tx.assign(sector=tx.sector.fillna("Unlabelled sector")), "sector"),
        "heat": lambda: agg(tx, ["country", "pt"]).reset_index(),
        "pareto": lambda: pareto(tx), "drivers": lambda: drivers(tx),
        "quintiles": lambda: quintiles(tx), "quintile_versions": lambda: quintile_versions(tx),
        "anomalies": lambda: anomaly_tables(prep, tx, cfg), "hard_mixed": lambda: hard_mixed(prep, tx),
        "customers": lambda: customers(tx, cfg), "laney": lambda: laney_patterns(tx, cfg),
        "january": lambda: january(tx, cfg), "fx": lambda: fx_analysis(prep, tx, cfg),
        "recovery": lambda: recovery(prep, tx, cfg), "sensitivity": lambda: sensitivity(tx),
        "remaining_mix": lambda: remaining_mix(tx), "customer_concentration": lambda: customer_concentration(tx),
    }
    for k in BLOCK_ORDER:
        if want is not None and k not in want:
            continue
        if k == "matrix":
            lp = res.get("laney") or {"patterns": pd.DataFrame(), "signals": pd.DataFrame()}
            res[k] = _safe(prioritisation)(prep, tx, cfg, lp["patterns"], lp["signals"])
        else:
            res[k] = _safe(fns[k])()
    return res
