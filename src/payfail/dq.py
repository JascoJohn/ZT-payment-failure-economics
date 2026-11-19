"""Data-quality evidence for Appendix A and B: rate screens, legacy codes, and the reconciliation with the brief.

Nothing here changes an analytical result. `reconciliation` re-runs `prepare` once with the Sierra Leone
redenomination fix switched off, so the "before the SLL correction" figures in the report are computed, not typed.
"""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd

from .data import agg, prepare


def rate_screen(fx: pd.DataFrame, cfg: dict) -> dict[str, pd.DataFrame]:
    """The same three rate corrections as `data.prepare_rates`, listed day by day."""
    c = cfg["fx"]
    fx = fx.copy()
    fx["ccy"] = fx.currency.replace(cfg["data"]["currency_aliases"])
    bad = fx[fx.rate <= 0][["date", "currency", "ccy", "rate"]]
    fx = fx[fx.rate > 0].copy()
    fx["period"] = fx.date.dt.to_period("M").dt.to_timestamp()
    fx["rate_restated"] = fx.rate
    rescaled = []
    for fix in c["redenomination_fixes"]:
        m = (fx.ccy == fix["currency"]) & (fx.rate > fix["rate_above"])
        fx.loc[m, "rate_restated"] = fx.loc[m, "rate"] / fix["divide_by"]
        rescaled.append(fx[m][["date", "currency", "ccy", "rate", "rate_restated"]])
    r = fx.assign(rate=fx.rate_restated)
    med = r.groupby(["ccy", "period"]).rate.transform("median")
    spike = (r.rate / med > c["spike_ratio"]) | (r.rate / med < 1 / c["spike_ratio"])
    spikes = r[spike].assign(month_median=med[spike])[["date", "currency", "ccy", "rate", "month_median"]]
    sll = fx[fx.ccy == "SLL"].groupby("period").agg(days=("rate", "size"), raw_mean=("rate", "mean"),
                                                    restated_mean=("rate_restated", "mean")).reset_index()
    return {"bad": bad, "rescaled": pd.concat(rescaled) if rescaled else pd.DataFrame(), "spikes": spikes, "sll": sll}


def legacy_code_evidence(raw: dict, cfg: dict) -> pd.DataFrame:
    """Median local value per attempt for each legacy code against the code it is mapped to."""
    t = raw["transactions"].copy()
    t = t[t.total_count > 0]
    t["vpa"] = t.total_value / t.total_count
    rows = []
    for old, new in cfg["data"]["currency_aliases"].items():
        for code, role in [(old, "legacy code"), (new, "mapped to")]:
            d = t[t.currency == code]
            rows.append({"legacy_code": old, "mapped_to": new, "code": code, "role": role, "records": int(len(d)),
                         "median_value_per_attempt": float(d.vpa.median()) if len(d) else np.nan})
    return pd.DataFrame(rows)


def _pack(p, cfg: dict) -> dict:
    tx = p.tx
    m = agg(tx, "period")
    jan = pd.Timestamp(cfg["january"]["target"])
    below = m[m.fee_share < 0.78].fee_share
    return {"fees": float(tx.fee.sum()), "failed_fees": float(tx.f_fee.sum()), "fee_share": float(tx.f_fee.sum() / tx.fee.sum()),
            "count_rate": float(tx.f_att.sum() / tx.att.sum()),
            "jan_failed_fees": float(tx[tx.period == jan].f_fee.sum()),
            "jan_fee_share": float(m.fee_share[jan]), "jan_count_rate": float(m.fail_rate[jan]),
            "months_below_78": [{"month": pd.Timestamp(k).strftime("%b %Y"), "share": float(v)} for k, v in below.items()]}


def reconciliation(prep, cfg: dict, raw: dict) -> dict:
    """Report basis against the same data with the SLL redenomination fix switched off (the brief's basis)."""
    cfg2 = copy.deepcopy(cfg)
    cfg2["fx"]["redenomination_fixes"] = []
    prep2 = prepare(cfg2, raw)
    post, pre = _pack(prep, cfg), _pack(prep2, cfg)
    tx = prep.tx
    return {"report_basis": post, "no_sll_fix": pre,
            "sll_effect_failed_fees": pre["failed_fees"] - post["failed_fees"],
            "sll_effect_fees": pre["fees"] - post["fees"],
            "bank_transfer_record_share": float((tx.pt == "bank transfer").mean()),
            "bank_transfer_attempt_share": float(tx.loc[tx.pt == "bank transfer", "att"].sum() / tx.att.sum())}
