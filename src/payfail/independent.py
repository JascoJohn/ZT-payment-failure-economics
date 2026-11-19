"""Independent recomputation of the headline results, straight from data/raw with plain pandas.

This module deliberately imports nothing from `payfail`: it re-implements the written method (Appendix A and the
assumptions file) from scratch, with the thresholds typed in below, so that a bug in the pipeline cannot also be
in the check. `audit.py` compares its output with results.json and the chapter tables.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Thresholds typed here on purpose (they are compared with config/assumptions.yaml by the audit).
T = dict(alias={"GHC": "GHS", "ZMK": "ZMW", "XAF/CFA": "XAF", "CFA": "XAF"}, country_alias={"Tanzania, United Republic Of": "Tanzania"},
         sll_above=0.001, sll_div=1000, spike=5, rel_min=1000, rel_mult=50, rel_succ=0.05, lookback=6,
         esc_min=5000, esc_succ=0.05, base_year=2022, jan="2024-01-01", base_start="2023-07-01", base_end="2023-12-01",
         min_succ_local_fee=100)


def compute(workbook: Path) -> dict:
    raw = pd.read_excel(workbook, sheet_name=None)
    tx, cu, fx = raw["transactions"].copy(), raw["customer_details"].copy(), raw["exchange_rates"].copy()

    # ---- exchange rates: legacy codes, drop non-positive, SLL restatement, spike screen, daily mean, monthly mean
    fx["ccy"] = fx["currency"].replace(T["alias"])
    fx = fx[fx["rate"] > 0].copy()
    m = (fx.ccy == "SLL") & (fx.rate > T["sll_above"])
    fx.loc[m, "rate"] = fx.loc[m, "rate"] / T["sll_div"]
    fx["month"] = fx["date"].values.astype("datetime64[M]")
    med = fx.groupby(["ccy", "month"])["rate"].transform("median")
    ratio = fx["rate"] / med
    fx = fx[~((ratio > T["spike"]) | (ratio < 1 / T["spike"]))]
    daily = fx.groupby(["date", "ccy"], as_index=False)["rate"].mean()
    daily["month"] = daily["date"].values.astype("datetime64[M]")
    monthly = daily.groupby(["month", "ccy"])["rate"].mean().rename("r").reset_index()
    base = daily[daily["date"].dt.year == T["base_year"]].groupby("ccy")["rate"].mean()
    base["USD"] = 1.0
    months = sorted(tx["period"].unique())
    monthly = pd.concat([monthly[monthly.ccy != "USD"], pd.DataFrame({"month": months, "ccy": "USD", "r": 1.0})], ignore_index=True)

    # ---- transactions
    tx["ccy"] = tx["currency"].replace(T["alias"])
    tx = tx.merge(monthly, left_on=["period", "ccy"], right_on=["month", "ccy"], how="left")
    tx["ok"] = tx["r"].notna()
    rev = tx["revenue"].fillna(0.0)
    tx["fee"] = (rev * tx["r"]).fillna(0.0)
    tx["fee_cc"] = np.where(tx.ok, rev * tx["ccy"].map(base).fillna(tx["r"]), 0.0)
    tx["failed"] = tx["status"].str.lower() != "successful"
    tx["att"] = tx["total_count"]
    tx["f_att"] = np.where(tx.failed, tx.att, 0)
    tx["s_att"] = tx.att - tx.f_att
    tx["f_fee"] = np.where(tx.failed, tx.fee, 0.0)
    tx["f_fee_cc"] = np.where(tx.failed, tx.fee_cc, 0.0)
    cu["country"] = cu["country_description"].replace(T["country_alias"])
    tx = tx.merge(cu[["customer_id", "country"]], on="customer_id", how="left")
    tx["pt"] = tx["paymenttype"]

    out = {"records": len(tx), "attempts": int(tx.att.sum()), "failed": int(tx.f_att.sum()), "fees": tx.fee.sum(),
           "failed_fees": tx.f_fee.sum(), "succ_fees": tx.fee.sum() - tx.f_fee.sum(), "records_translatable": int(tx.ok.sum())}
    out["fee_share"] = out["failed_fees"] / out["fees"]
    out["count_rate"] = out["failed"] / out["attempts"]

    # ---- anomaly rules at customer x payment type x month
    g = tx.groupby(["customer_id", "pt", "period"]).agg(att=("att", "sum"), f=("f_att", "sum"), s=("s_att", "sum"), ff=("f_fee", "sum")).reset_index()
    grid = g.pivot_table(index=["customer_id", "pt"], columns="period", values="att", aggfunc="sum", fill_value=0).reindex(columns=months, fill_value=0)
    prior = {}
    arr = grid.values
    for j, mth in enumerate(months):
        window = arr[:, max(0, j - T["lookback"]):j]
        pm = np.median(window, axis=1) if window.shape[1] else np.zeros(len(grid))
        for key, v in zip(grid.index, pm):
            prior[(key[0], key[1], mth)] = v
    g["prior"] = [prior.get((c, p, m_), 0.0) for c, p, m_ in zip(g.customer_id, g.pt, g.period)]
    g["succ_rate"] = g.s / g.att
    g["extreme"] = (g.f >= T["rel_min"]) & (g.att > T["rel_mult"] * g.prior.clip(lower=1)) & (g.succ_rate < T["rel_succ"])
    trig = (~g.extreme) & (g.f >= T["esc_min"]) & (g.succ_rate < T["esc_succ"])
    esc = sorted(g.loc[trig, "customer_id"].unique().tolist())
    g["cat"] = np.where(g.extreme, "Extreme", np.where(g.customer_id.isin(esc), "Escalation", "Remaining"))
    tx = tx.merge(g[["customer_id", "pt", "period", "extreme", "cat"]], on=["customer_id", "pt", "period"], how="left")
    out["escalation_customers"] = esc
    out["bridge"] = {k: float(tx.loc[tx.cat == k, "f_fee"].sum()) for k in ["Extreme", "Escalation", "Remaining"]}
    out["extreme_observations"] = int(g.extreme.sum())
    rem = tx[tx.cat == "Remaining"].groupby("period")[["f_att", "att"]].sum()
    mr = rem.f_att / rem.att
    out["remaining_rate_min"], out["remaining_rate_max"] = float(mr.min()), float(mr.max())

    # ---- failure rate by market and payment type (all records)
    h = tx.groupby(["country", "pt"])[["f_att", "att"]].sum()
    out["rate_by_cell"] = (h.f_att / h.att).to_dict()

    # ---- customer concentration (customers with failed fees)
    cf = tx.groupby("customer_id").f_fee.sum()
    top = cf[cf > 0].sort_values(ascending=False)
    n1 = max(1, round(len(top) * 0.01))
    out["cc"] = {"customers": len(top), "transacting": len(cf), "top10": float(top.head(10).sum() / top.sum()), "top1pct_n": n1,
                 "top1pct": float(top.head(n1).sum() / top.sum())}

    # ---- January bridge
    nb = tx[~tx.extreme]
    jan, bs, be = pd.Timestamp(T["jan"]), pd.Timestamp(T["base_start"]), pd.Timestamp(T["base_end"])
    inb = lambda d: (d.period >= bs) & (d.period <= be)
    n = len(pd.date_range(bs, be, freq="MS"))
    b_all, j_all = tx[inb(tx)].f_fee.sum() / n, tx[tx.period == jan].f_fee.sum()
    b_ex, j_ex = tx[tx.extreme & inb(tx)].f_fee.sum() / n, tx[tx.extreme & (tx.period == jan)].f_fee.sum()
    b_nb, j_nb = nb[inb(nb)].f_fee.sum() / n, nb[nb.period == jan].f_fee.sum()
    b_cc, j_cc = nb[inb(nb)].f_fee_cc.sum() / n, nb[nb.period == jan].f_fee_cc.sum()
    fxe = (j_nb - j_cc) - (b_nb - b_cc)
    cells = lambda d, k: d[d.ok].groupby(["country", "pt"]).agg(att=("att", "sum"), f=("f_att", "sum"), c=("f_fee_cc", "sum")) / k
    c = cells(nb[inb(nb)], n).join(cells(nb[nb.period == jan], 1), lsuffix="0", rsuffix="1", how="outer").fillna(0)
    both = c[(c.c0 > 0) & (c.c1 > 0)]

    def lm(a, b):
        return np.where(np.isclose(a, b), a, (a - b) / (np.log(a) - np.log(b)))
    w = lm(both.c1.values, both.c0.values)
    N0, N1 = both.att0.sum(), both.att1.sum()
    lm_eff = {"Volume": (w * np.log(N1 / N0)).sum(),
              "Mix": (w * np.log((both.att1 / N1) / (both.att0 / N0))).sum(),
              "Failure rate": (w * np.log((both.f1 / both.att1) / (both.f0 / both.att0))).sum(),
              "Fee yield": (w * np.log((both.c1 / both.f1) / (both.c0 / both.f0))).sum()}
    ee = (c.c1.sum() - c.c0.sum()) - (both.c1.sum() - both.c0.sum())
    out["january"] = {"baseline": b_all, "january": j_all, "extreme": j_ex - b_ex, "fx": fxe, **{k: float(v) for k, v in lm_eff.items()},
                      "entry_exit": float(ee), "residual": float(j_all - b_all - (j_ex - b_ex) - fxe - sum(lm_eff.values()) - ee)}

    # ---- recovery: USD card, non-anomalous
    def recovery(frame):
        uc = frame[(frame.ccy == "USD") & (frame.pt == "card")]
        t = uc.groupby("country").agg(att=("att", "sum"), f=("f_att", "sum"), s=("s_att", "sum"), fee=("fee", "sum"), ff=("f_fee", "sum"))
        t["rate"] = t.f / t.att
        sfee = t.fee - t.ff
        overall = sfee.sum() / t.s.sum()
        t["fps"] = np.where(t.s >= T["min_succ_local_fee"], sfee / t.s.replace(0, np.nan), overall)
        return t
    t = recovery(nb)

    def base_case(t, mm_frame):
        mm = mm_frame[mm_frame.pt == "mobilemoney"].groupby("country")[["f_att", "att"]].sum()
        mmr = (mm.f_att / mm.att).reindex(t.index)
        add = (t.att * (t.rate - mmr).clip(lower=0)).fillna(0)
        return float((add * t.fps).sum()), float(add.sum()), mmr
    inc, add, mmr = base_case(t, nb)
    inc_x, _, mmr_x = base_case(t, nb[~nb.customer_id.isin(esc)])
    out["recovery"] = {"base": inc, "base_additional": add, "ex_escalation": inc_x, "kenya_mm": float(mmr["Kenya"]),
                       "kenya_mm_ex": float(mmr_x["Kenya"])}
    return out
