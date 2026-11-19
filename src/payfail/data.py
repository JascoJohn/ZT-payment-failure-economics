"""Load the supplied workbook, translate to USD, flag data-quality issues and classify anomalies.

Everything downstream works from the `Prepared` object returned by `prepare()`:
one row per customer x month x currency x payment type x status, with USD fees,
data-quality flags and the anomaly category attached.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class Prepared:
    tx: pd.DataFrame            # transaction records with USD measures, flags and anomaly category
    cust: pd.DataFrame          # customer table (cleaned labels)
    rates_daily: pd.DataFrame   # cleaned daily rates (USD per unit)
    rates_monthly: pd.DataFrame # monthly average / month-end / range per currency
    base_rates: pd.Series       # constant-currency base rate per currency
    cmc: pd.DataFrame           # customer x payment type x month table with anomaly flags
    periods: list
    stats: dict = field(default_factory=dict)


def load_raw(cfg: dict) -> dict[str, pd.DataFrame]:
    path = Path(cfg["_root"]) / cfg["data"]["workbook"]
    return pd.read_excel(path, sheet_name=None)


def agg(df: pd.DataFrame, by) -> pd.DataFrame:
    """Standard aggregation: attempts, failures, fees and the two core rates."""
    a = df.groupby(by, observed=True).agg(att=("att", "sum"), f_att=("f_att", "sum"),
                                          fee=("fee", "sum"), f_fee=("f_fee", "sum"))
    a["fail_rate"] = a.f_att / a.att
    a["fee_share"] = a.f_fee / a.fee
    return a


def prepare_rates(fx: pd.DataFrame, cfg: dict, periods: list) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, dict]:
    c = cfg["fx"]
    fx = fx.copy()
    fx["ccy"] = fx.currency.replace(cfg["data"]["currency_aliases"])
    stats = {"bad_rate_days_dropped": int((fx.rate <= 0).sum())}
    fx = fx[fx.rate > 0].copy()
    fx["period"] = fx.date.dt.to_period("M").dt.to_timestamp()

    stats["redenomination_days_rescaled"] = {}
    for fix in c["redenomination_fixes"]:
        m = (fx.ccy == fix["currency"]) & (fx.rate > fix["rate_above"])
        fx.loc[m, "rate"] = fx.loc[m, "rate"] / fix["divide_by"]
        stats["redenomination_days_rescaled"][fix["currency"]] = int(m.sum())

    med = fx.groupby(["ccy", "period"]).rate.transform("median")
    spike = (fx.rate / med > c["spike_ratio"]) | (fx.rate / med < 1 / c["spike_ratio"])
    stats["spike_days_dropped"] = int(spike.sum())
    stats["spike_currencies"] = sorted(fx.loc[spike, "ccy"].unique().tolist())
    fx = fx[~spike]

    daily = fx.groupby(["date", "period", "ccy"], as_index=False).rate.mean()
    g = daily.sort_values("date").groupby(["period", "ccy"]).rate
    monthly = pd.DataFrame({"r_avg": g.mean(), "r_end": g.last(), "r_min": g.min(),
                            "r_max": g.max(), "ndays": g.count()}).reset_index()
    monthly["range_pct"] = (monthly.r_max - monthly.r_min) / monthly.r_avg
    monthly = monthly[monthly.ccy != "USD"]
    usd = pd.DataFrame({"period": periods, "ccy": "USD", "r_avg": 1.0, "r_end": 1.0,
                        "r_min": 1.0, "r_max": 1.0, "ndays": 0, "range_pct": 0.0})
    monthly = pd.concat([monthly, usd], ignore_index=True)

    base = daily[daily.date.dt.year == c["constant_currency_year"]].groupby("ccy").rate.mean()
    base = pd.concat([base.drop("USD", errors="ignore"), pd.Series({"USD": 1.0})]).rename("r_cc")
    return daily, monthly, base, stats


def classify_anomalies(tx: pd.DataFrame, periods: list, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Relative extreme-volume rule plus absolute escalation trigger, at customer x payment type x month."""
    a = cfg["anomalies"]
    cmc = tx.groupby(["customer_id", "pt", "period"]).agg(
        att=("att", "sum"), f_att=("f_att", "sum"), s_att=("s_att", "sum"),
        f_fee=("f_fee", "sum"), fee=("fee", "sum")).reset_index()
    piv = cmc.pivot_table(index=["customer_id", "pt"], columns="period", values="att",
                          aggfunc="sum", fill_value=0).reindex(columns=periods, fill_value=0)
    lb = a["relative"]["lookback_months"]
    prior = piv.T.rolling(lb, min_periods=1).median().shift(1).T  # median of the preceding months, zeros included
    prior = prior.stack().rename("prior_med").reset_index()
    cmc = cmc.merge(prior, on=["customer_id", "pt", "period"], how="left")
    cmc["prior_med"] = cmc.prior_med.fillna(0)
    cmc["succ_rate"] = cmc.s_att / cmc.att

    def rule(r):
        return ((cmc.f_att >= r["min_failed"]) & (cmc.att > r["multiple_of_prior_median"] * cmc.prior_med.clip(lower=1))
                & (cmc.succ_rate < r["max_success_rate"]))

    cmc["extreme"] = rule(a["relative"])
    for name, r in a["sensitivity"].items():
        cmc[f"extreme_{name}"] = rule(r)
    e = a["escalation"]
    trig = (~cmc.extreme) & (cmc.f_att >= e["min_failed"]) & (cmc.succ_rate < e["max_success_rate"])
    esc_customers = sorted(cmc.loc[trig, "customer_id"].unique().tolist())
    cmc["escalation_trigger"] = trig
    cmc["category"] = np.where(cmc.extreme, "Extreme-volume anomaly",
                               np.where(cmc.customer_id.isin(esc_customers), "Escalation", "Remaining"))
    tx = tx.merge(cmc[["customer_id", "pt", "period", "extreme", "category"]], on=["customer_id", "pt", "period"], how="left")
    tx.attrs["escalation_customers"] = esc_customers
    return tx, cmc


def prepare(cfg: dict, raw: dict | None = None) -> Prepared:
    raw = raw or load_raw(cfg)
    tx = raw["transactions"].copy()
    cust = raw["customer_details"].copy()
    periods = sorted(tx.period.unique())

    daily, monthly, base, stats = prepare_rates(raw["exchange_rates"], cfg, periods)

    tx["ccy"] = tx.currency.replace(cfg["data"]["currency_aliases"])
    tx = tx.merge(monthly[["period", "ccy", "r_avg", "r_end", "range_pct"]], on=["period", "ccy"], how="left")
    tx["r_cc"] = tx.ccy.map(base)
    tx["fx_ok"] = tx.r_avg.notna()
    stats.update(records=int(len(tx)), untranslatable_records=int((~tx.fx_ok).sum()),
                 untranslatable_currencies=int(tx.loc[~tx.fx_ok, "ccy"].nunique()),
                 untranslatable_attempts=int(tx.loc[~tx.fx_ok, "total_count"].sum()))

    f = cfg["flags"]
    tx["flag_missing_fee"] = tx.revenue.isna()
    ratio = tx.revenue / tx.total_value.replace(0, np.nan)
    tx["revenue"] = tx.revenue.fillna(0.0)
    tx["failed"] = tx.status.str.lower().ne("successful")
    tx["att"] = tx.total_count
    tx["f_att"] = np.where(tx.failed, tx.att, 0)
    tx["s_att"] = tx.att - tx.f_att
    tx["fee"] = (tx.revenue * tx.r_avg).fillna(0.0)
    tx["fee_end"] = (tx.revenue * tx.r_end).fillna(0.0)
    tx["fee_cc"] = np.where(tx.fx_ok, tx.revenue * tx.r_cc.fillna(tx.r_avg), 0.0)  # same population as reported fees
    tx["val"] = tx.total_value * tx.r_avg
    tx["flag_fee_ratio"] = ~tx.flag_missing_fee & ((ratio < f["fee_ratio_low"]) | (ratio > f["fee_ratio_high"]))
    tx["vpa_usd"] = tx.val / tx.att
    tx["flag_value"] = tx.fx_ok & ((tx.vpa_usd > f["value_per_attempt_limit"]) | (tx.total_value <= 0))
    tx["value_excluded"] = tx.flag_value | ~tx.fx_ok
    tx["f_fee"] = np.where(tx.failed, tx.fee, 0.0)
    tx["f_fee_cc"] = np.where(tx.failed, tx.fee_cc, 0.0)
    tx["f_fee_end"] = np.where(tx.failed, tx.fee_end, 0.0)
    tx["f_val"] = np.where(tx.failed, tx.val, 0.0)
    stats.update(flag_fee_ratio=int(tx.flag_fee_ratio.sum()), flag_missing_fee=int(tx.flag_missing_fee.sum()),
                 flag_value=int(tx.flag_value.sum()), fee_exceeds_value=int((ratio > 1).sum()),
                 flag_value_usd=float(tx.loc[tx.flag_value, "val"].sum()),
                 flag_value_fees=float(tx.loc[tx.flag_value, "fee"].sum()),
                 value_total_usd=float(tx.loc[tx.fx_ok, "val"].sum()))

    d = cfg["data"]
    cust["sector"] = cust.sector.replace(d["sector_aliases"])
    cust["country"] = cust.country_description.replace(d["country_aliases"])
    tx = tx.merge(cust[["customer_id", "country", "sector", "sign_up_date"]], on="customer_id", how="left")
    tx["pt"] = tx.paymenttype

    tx, cmc = classify_anomalies(tx, periods, cfg)
    stats["escalation_customers"] = tx.attrs["escalation_customers"]
    last_obs = tx.groupby("customer_id").period.max()
    snap = cust.set_index("customer_id").last_tx_date.dt.to_period("M").dt.to_timestamp().reindex(last_obs.index)
    stats["stale_customer_dates"] = int((last_obs > snap).sum())
    stats["transacting_customers"] = int(last_obs.size)
    return Prepared(tx=tx, cust=cust, rates_daily=daily, rates_monthly=monthly, base_rates=base,
                    cmc=cmc, periods=periods, stats=stats)
