"""Stages 01A-01G: loading, checking and preparing the data. Each function writes its tables to
outputs/<number>_<name>/tables/ and returns a short summary dict that the stage script prints."""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import dq
from .analysis import analyse
from .config import load_config
from .data import agg, prepare, prepare_rates
from .pipeline import (INTER, chapter_dir, get_raw, jsonable, load_prep, rebuild_figure_index, run_analysis_chapter, save_prep,
                       save_res, write_tables)


def _out(code: str, name: str, df: pd.DataFrame) -> None:
    d = chapter_dir(code) / "tables"
    d.mkdir(parents=True, exist_ok=True)
    df.to_csv(d / f"{name}.csv", index=False)


def _flatten(d: dict, prefix: str = "") -> list[tuple[str, object]]:
    rows = []
    for k, v in d.items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict):
            rows += _flatten(v, f"{prefix}{k}.")
        else:
            rows.append((f"{prefix}{k}", json.dumps(v, default=str) if isinstance(v, list) else v))
    return rows


# ------------------------------------------------------------------------------------------ 01A
def stage_01A() -> dict:
    cfg = load_config()
    a, e, fl, fx, j, rc, cu, pt = (cfg["anomalies"]["relative"], cfg["anomalies"]["escalation"], cfg["flags"], cfg["fx"],
                                   cfg["january"], cfg["recovery"], cfg["customers"], cfg["patterns"])
    sens = cfg["anomalies"]["sensitivity"]
    checks = [
        ("Raw workbook path exists", (Path(cfg["_root"]) / cfg["data"]["workbook"]).exists()),
        ("Spike ratio is above 1", fx["spike_ratio"] > 1),
        ("Constant-currency year is a calendar year", 2000 <= fx["constant_currency_year"] <= 2100),
        ("Volatility screen between 0 and 1", 0 < fx["volatility_screen"] < 1),
        ("Fee-ratio limits ordered (low < high)", 0 < fl["fee_ratio_low"] < fl["fee_ratio_high"] < 1),
        ("Value-per-attempt limit is positive", fl["value_per_attempt_limit"] > 0),
        ("Redenomination fixes name a currency and a divisor",
         all({"currency", "rate_above", "divide_by"} <= set(f) and f["divide_by"] > 0 for f in fx["redenomination_fixes"])),
        ("Relative rule: minimum failed attempts, multiple and look-back are positive",
         a["min_failed"] > 0 and a["multiple_of_prior_median"] > 0 and a["lookback_months"] >= 1),
        ("Success-rate limits lie between 0 and 1", all(0 <= x <= 1 for x in [a["max_success_rate"], e["max_success_rate"]])),
        ("Loose < agreed < strict thresholds",
         sens["loose"]["min_failed"] < a["min_failed"] < sens["strict"]["min_failed"]
         and sens["loose"]["multiple_of_prior_median"] < a["multiple_of_prior_median"] < sens["strict"]["multiple_of_prior_median"]
         and sens["loose"]["max_success_rate"] > a["max_success_rate"] > sens["strict"]["max_success_rate"]),
        ("January baseline precedes the target month",
         pd.Timestamp(j["baseline_start"]) <= pd.Timestamp(j["baseline_end"]) < pd.Timestamp(j["target"])),
        ("Cost ratios are between 0 and 1 and increasing",
         all(0 <= x <= 1 for x in rc["cost_ratios"]) and rc["cost_ratios"] == sorted(rc["cost_ratios"])),
        ("Optimistic margin between 0 and 1", 0 <= rc["optimistic_margin"] < 1),
        ("Tenure bands are increasing", cu["tenure_bands"] == sorted(cu["tenure_bands"])),
        ("Pattern thresholds are valid", pt["min_eligible_months"] <= 28 and pt["high_confidence_months"] >= pt["min_eligible_months"]),
    ]
    df = pd.DataFrame(checks, columns=["check", "passed"])
    _out("01A", "validation", df)
    _out("01A", "assumptions", pd.DataFrame(_flatten(cfg), columns=["assumption", "value"]))
    bad = df[~df.passed]
    if len(bad):
        raise SystemExit("assumptions.yaml failed validation:\n  " + "\n  ".join(bad.check))
    return {"checks passed": f"{len(df)}/{len(df)}", "assumptions": len(_flatten(cfg))}


# ------------------------------------------------------------------------------------------ 01B-01D
def stage_01B() -> dict:
    cfg = load_config()
    raw = get_raw(cfg)
    t = raw["transactions"]
    _out("01B", "sheets", pd.DataFrame([{"sheet": k, "rows": len(v), "columns": len(v.columns)} for k, v in raw.items()]))
    _out("01B", "columns", pd.DataFrame({"column": t.columns, "dtype": [str(x) for x in t.dtypes], "missing": t.isna().sum().values}))
    for col, name in [("status", "records_by_status"), ("paymenttype", "records_by_payment_type"),
                      ("currency", "records_by_currency"), ("period", "records_by_month")]:
        g = t.groupby(col).agg(records=("total_count", "size"), attempts=("total_count", "sum")).reset_index()
        _out("01B", name, g)
    return {"records": f"{len(t):,}", "attempts": f"{int(t.total_count.sum()):,}",
            "months": t.period.nunique(), "customers": t.customer_id.nunique()}


def stage_01C() -> dict:
    cfg = load_config()
    raw = get_raw(cfg)
    c, t, d = raw["customer_details"], raw["transactions"], cfg["data"]
    ctry = c.country_description.value_counts().rename_axis("label_in_data").reset_index(name="customers")
    ctry["mapped_to"] = ctry.label_in_data.replace(d["country_aliases"])
    sect = c.sector.value_counts(dropna=False).rename_axis("label_in_data").reset_index(name="customers")
    sect["mapped_to"] = sect.label_in_data.replace(d["sector_aliases"])
    _out("01C", "country_labels", ctry)
    _out("01C", "sector_labels", sect)
    last_obs = t.groupby("customer_id").period.max()
    snap = c.set_index("customer_id").last_tx_date.dt.to_period("M").dt.to_timestamp().reindex(last_obs.index)
    stale = pd.DataFrame({"last_observed": last_obs, "table_last_tx_month": snap})
    stale["stale"] = stale.last_observed > stale.table_last_tx_month
    _out("01C", "stale_dates", stale.reset_index())
    return {"customers": f"{len(c):,}", "transacting customers": f"{len(last_obs):,}", "stale last-transaction dates": int(stale.stale.sum()),
            "country labels mapped": int((ctry.label_in_data != ctry.mapped_to).sum())}


def stage_01D() -> dict:
    cfg = load_config()
    raw = get_raw(cfg)
    fx = raw["exchange_rates"]
    g = fx.groupby("currency").agg(days=("rate", "size"), first_date=("date", "min"), last_date=("date", "max"),
                                   min_rate=("rate", "min"), max_rate=("rate", "max")).reset_index()
    g["mapped_to"] = g.currency.replace(cfg["data"]["currency_aliases"])
    _out("01D", "rates_by_currency", g)
    _out("01D", "non_positive_rates", fx[fx.rate <= 0])
    return {"rate rows": f"{len(fx):,}", "currency codes": fx.currency.nunique(), "non-positive rates": int((fx.rate <= 0).sum()),
            "from": f"{fx.date.min():%Y-%m-%d}", "to": f"{fx.date.max():%Y-%m-%d}"}


# ------------------------------------------------------------------------------------------ 01F
def stage_01F() -> dict:
    cfg = load_config()
    raw = get_raw(cfg)
    periods = sorted(raw["transactions"].period.unique())
    daily, monthly, base, stats = prepare_rates(raw["exchange_rates"], cfg, periods)
    scr = dq.rate_screen(raw["exchange_rates"], cfg)
    _out("01F", "rates_monthly", monthly)
    _out("01F", "base_rates_2022", base.rename_axis("ccy").reset_index())
    _out("01F", "rates_daily_clean", daily)
    _out("01F", "sll_restated_days", scr["rescaled"])
    _out("01F", "spike_days_dropped", scr["spikes"])
    _out("01F", "sll_monthly_before_after", scr["sll"])
    assert len(scr["spikes"]) == stats["spike_days_dropped"], "spike list disagrees with prepare_rates"
    return {"SLL days restated": stats["redenomination_days_rescaled"].get("SLL"), "spike days dropped": stats["spike_days_dropped"],
            "spike currencies": ", ".join(stats["spike_currencies"]), "currencies with a monthly rate": monthly.ccy.nunique()}


# ------------------------------------------------------------------------------------------ 01G
def stage_01G() -> dict:
    t0 = time.time()
    cfg = load_config()
    prep = prepare(cfg, get_raw(cfg))
    save_prep(prep)
    tx = prep.tx
    _out("01G", "population_summary", pd.DataFrame([
        {"measure": "Records", "value": len(tx)}, {"measure": "Records with an exchange rate", "value": int(tx.fx_ok.sum())},
        {"measure": "Records without an exchange rate", "value": int((~tx.fx_ok).sum())},
        {"measure": "Fee-ratio flags", "value": int(tx.flag_fee_ratio.sum())}, {"measure": "Missing-fee flags", "value": int(tx.flag_missing_fee.sum())},
        {"measure": "Value flags", "value": int(tx.flag_value.sum())}]))
    cat = tx.groupby("category").agg(records=("att", "size"), attempts=("att", "sum"), failed_fees=("f_fee", "sum")).reset_index()
    _out("01G", "exposure_category", cat)
    _out("01G", "anomaly_rule_cells", prep.cmc[prep.cmc.extreme | prep.cmc.escalation_trigger])
    extra = run_analysis_chapter("01G")
    return {"records": f"{len(tx):,}", "translatable": f"{int(tx.fx_ok.sum()):,}",
            "escalation account(s)": ", ".join(map(str, prep.stats["escalation_customers"])),
            "extreme-volume observations": int(prep.cmc.extreme.sum()), "figures": extra["figures"],
            "seconds": round(time.time() - t0)}


# ------------------------------------------------------------------------------------------ 01E
def stage_01E() -> dict:
    cfg, prep = load_prep()
    raw = get_raw(cfg)
    tx, st = prep.tx, prep.stats
    flags = pd.DataFrame([
        {"flag": "Fee-ratio anomaly", "records": st["flag_fee_ratio"], "note": f"{st['fee_exceeds_value']} of them have a fee above the value"},
        {"flag": "Missing fee", "records": st["flag_missing_fee"], "note": "zero in fee sums; kept in counts"},
        {"flag": "Transaction-value anomaly", "records": st["flag_value"], "note": f"value ${st['flag_value_usd']:,.0f}; excluded from value measures only"}])
    _out("01E", "flags", flags)
    un = tx[~tx.fx_ok].groupby("ccy").agg(records=("att", "size"), attempts=("att", "sum")).reset_index().sort_values("attempts", ascending=False)
    _out("01E", "untranslatable_records", un)
    scr = dq.rate_screen(raw["exchange_rates"], cfg)
    _out("01E", "sll_evidence", scr["sll"])
    _out("01E", "spike_days", scr["spikes"])
    _out("01E", "legacy_codes", dq.legacy_code_evidence(raw, cfg))
    _out("01E", "value_anomalies", tx[tx.flag_value][["period", "customer_id", "ccy", "pt", "status", "att", "total_value", "revenue", "val"]]
         .sort_values("val", ascending=False))
    rec = dq.reconciliation(prep, cfg, raw)
    sens = analyse(prep, cfg, only=["sensitivity"])["sensitivity"]
    res = {"sensitivity": sens, "reconciliation": rec, "examples": dq.value_examples(prep)}
    save_res("01E", res)
    scal = write_tables(res, chapter_dir("01E") / "tables")
    (chapter_dir("01E") / "results.json").write_text(json.dumps(scal, indent=2), encoding="utf-8")
    rb, ns = rec["report_basis"], rec["no_sll_fix"]
    return {"untranslatable records": int((~tx.fx_ok).sum()), "failed fees, report basis": f"${rb['failed_fees']:,.0f}",
            "failed fees, no SLL fix": f"${ns['failed_fees']:,.0f}", "SLL effect": f"${rec['sll_effect_failed_fees']:,.0f}"}


STAGES = {"01A": stage_01A, "01B": stage_01B, "01C": stage_01C, "01D": stage_01D, "01E": stage_01E, "01F": stage_01F, "01G": stage_01G}
