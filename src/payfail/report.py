r"""Render the full report and the executive brief (HTML, then PDF through Chrome or Edge).

Content lives in report/content/ as Markdown and HTML that anyone can edit:
  meta.yaml              title, author, contact and links on the cover
  00_cover.html          page 1
  01_summary.md          page 2, the written executive summary
  02_at_a_glance.html    page 3, the one-page infographic
  03_main_report.md      page 4 onwards
  brief.html             the 5-page executive brief
Styling lives in report/assets/report.css. Editing text or styles never touches the analysis.

Conventions inside the content files
  {{key}}                a number from the pipeline (see `context`)
  {{fig:slug}}           "Figure n" for a figure; {{tab:slug}} "Table n" for a table
  [[figure slug]]        place a pipeline figure (the same one the dashboard shows)
  ::: table slug | Caption     followed by a Markdown table: a numbered table
  Source: ...            directly under a table: its source line
  $$ LaTeX $$            a displayed formula (rendered as MathML); \( LaTeX \) inline
  *[Observed]*           an evidence label
  > text                 a call-out box
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

# ------------------------------------------------------------------------------- formatting


def k1(v):
    return f"${v / 1e3:,.1f}K"


def k0(v):
    return f"${v / 1e3:,.0f}K"


def m2(v):
    return f"${v / 1e6:,.2f}M"


def d0(v):
    return f"${v:,.0f}"


def d2(v):
    return f"${v:,.2f}"


def p1(v):
    return f"{v * 100:.1f}%"


def p0(v):
    return f"{v * 100:.0f}%"


def i0(v):
    return f"{int(round(v)):,}"


def pp(v):
    return f"{v * 100:.1f}"


def sk1(v):
    return ("+" if v >= 0 else "−") + k1(abs(v))


def sd0(v):
    return ("+" if v >= 0 else "−") + d0(abs(v))


CH = {"card": "card", "mobilemoney": "mobile money", "alternative channels": "alternative channels"}
_W = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
      "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]


def words(n, cap=False):
    """A small whole number in words ('six'); halves as 'three and a half'."""
    n2 = round(n * 2) / 2
    w = _W[int(n2)] + (" and a half" if n2 % 1 else "")
    return w.capitalize() if cap else w


def month_list(sig):
    """'Dec 2023 (70%), Jan 2024 (58%)' from a cell's control-chart signals, or an em dash."""
    if sig is None or len(sig) == 0:
        return "\u2014"
    return ", ".join(f"{pd.Timestamp(r.period):%b %Y} ({r.top_customer_share * 100:.0f}%)" for r in sig.itertuples())


def context(res: dict) -> dict[str, str]:
    """Every templated number, formatted exactly as the report prints it."""
    c: dict[str, str] = {}
    h, st, v = res["headline"], res["stats"], res["value"]
    c.update(failed_fees_m=m2(h["failed_fees"]), fees_m=m2(h["fees"]), succ_fees_k0=k0(h["succ_fees"]),
             succ_fees_k=k1(h["succ_fees"]), failed_fees_k=k1(h["failed_fees"]), failed_fees_d=d0(h["failed_fees"]),
             fees_d=d0(h["fees"]), attempts=i0(h["attempts"]), failed=i0(h["failed"]), count_rate=p1(h["count_rate"]),
             fee_share=p1(h["fee_share"]), records=i0(h["records"]), records_tr=i0(h["records_translatable"]),
             attempts_tr=i0(h["attempts_translatable"]), untr_records=i0(st["untranslatable_records"]),
             untr_ccy=i0(st["untranslatable_currencies"]), untr_att=i0(st["untranslatable_attempts"]),
             flag_fee_ratio=i0(st["flag_fee_ratio"]), fee_exceeds_value=i0(st["fee_exceeds_value"]),
             flag_missing=i0(st["flag_missing_fee"]), flag_value=i0(st["flag_value"]),
             flag_value_bn=f"${st['flag_value_usd'] / 1e9:.2f}bn", value_total_bn=f"${st['value_total_usd'] / 1e9:.2f}bn",
             flag_value_fees=k0(st["flag_value_fees"]), stale=i0(st["stale_customer_dates"]),
             stale_share=p0(st["stale_customer_dates"] / st["transacting_customers"]), spike_days=i0(st["spike_days_dropped"]),
             failed_value_share=p1(v["failed_value_share"]), avg_failed_value=d2(v["avg_failed_value"]),
             avg_success_value=d2(v["avg_success_value"]), value_ratio=f"{v['avg_failed_value'] / v['avg_success_value']:.1f}×",
             failed_intensity=f"{v['failed_fee_intensity'] * 100:.2f}%", success_intensity=f"{v['success_fee_intensity'] * 100:.2f}%",
             fee_per_failed=d2(h["failed_fees"] / h["failed"]), rec_failed=i0(h["failed_records"]), rec_success=i0(h["successful_records"]))

    b = res["bridge"].set_index("category")
    ex, es, rm = (b.loc[k] for k in ["Extreme-volume anomaly", "Escalation", "Remaining"])
    tot = b.f_fee.sum()
    c.update(ex_k=k1(ex.f_fee), es_k=k1(es.f_fee), rm_k=k1(rm.f_fee), ex_share=p1(ex.share), es_share=p1(es.share),
             rm_share=p1(rm.share), ex_fatt=i0(ex.f_att), es_fatt=i0(es.f_att), rm_fatt=i0(rm.f_att),
             ex_d=d0(ex.f_fee), es_d=d0(es.f_fee), rm_d=d0(rm.f_fee), anom_m=m2(ex.f_fee + es.f_fee),
             anom_share=p1((ex.f_fee + es.f_fee) / tot), rm_m=m2(rm.f_fee),
             bridge_rounded=k1(sum(round(x / 100) * 100 for x in b.f_fee)))

    # concentration
    ch = res["channels"].set_index("pt")
    cc = res["customer_concentration"]
    cur = res["currencies"].set_index("ccy")
    sec = res["sectors"].set_index("sector")
    c.update(card_share=p0(ch.share_of_failed_fees["card"]), bank_rate=p1(ch.fail_rate["bank transfer"]),
             bank_att_share=p1(ch.att["bank transfer"] / ch.att.sum()),
             bank_fpf=d2(ch.fee_per_failed_attempt["bank transfer"]),
             usd_share0=p0(cur.share_of_failed_fees["USD"]), usd_share=p1(cur.share_of_failed_fees["USD"]),
             usd_rate=p1(cur.fail_rate["USD"]), usd_ff=k1(cur.f_fee["USD"]), ghs_ff=k1(cur.f_fee["GHS"]), ugx_ff=k1(cur.f_fee["UGX"]),
             top10_0=p0(cc["top10"]), top10=p1(cc["top10"]), top1pct=p1(cc["top1pct"]), top1pct_n=i0(cc["top1pct_n"]),
             top10_ex=p1(cc["top10_ex_extreme"]), customers=i0(cc["customers"]),
             ecom_ff=k1(sec.f_fee["eCommerce"]),
             travel_fpf=d2(sec.f_fee["Travel_and_Hospitality"] / sec.f_att["Travel_and_Hospitality"]))
    heat = res["heat"].set_index(["country", "pt"])
    card = heat.xs("card", level="pt")
    mm = heat.xs("mobilemoney", level="pt")
    kc_all = heat.loc[("Kenya", "card")]
    c.update(card_min=p0(card.fail_rate.min()), card_max=p0(card.fail_rate.max()), mm_min=p0(mm.fail_rate.min()),
             mm_max=p0(mm.fail_rate.max()), kenya_card_all=m2(kc_all.f_fee), mm_min_ctry=mm.fail_rate.idxmin(), mm_max_ctry=mm.fail_rate.idxmax(),
             n_markets_words=words(len(card)))

    dr = res["drivers"].set_index(["country", "pt"])
    tot_att = dr.att.sum()
    for (cn, pt), key in [(("Kenya", "card"), "kc"), (("Kenya", "mobilemoney"), "km"), (("Uganda", "card"), "uc"),
                          (("Tanzania", "card"), "tc"), (("Ghana", "card"), "gc"), (("Uganda", "mobilemoney"), "um")]:
        r = dr.loc[(cn, pt)]
        c[f"dr_{key}_sa"] = p1(r.att / tot_att)
        c[f"dr_{key}_fr"] = p1(r.fail_rate)
        c[f"dr_{key}_fpf"] = d2(r.fee_per_failed_attempt)
        c[f"dr_{key}_ff"] = k1(r.f_fee)
    c["kenya_card_extreme"] = k0(kc_all.f_fee - dr.loc[("Kenya", "card")].f_fee)
    c["dr_all_fr"] = p1(dr.f_att.sum() / tot_att)
    c["dr_all_fpf"] = d2(dr.f_fee.sum() / dr.f_att_ok.sum())
    c["tc_yield_x"] = f"{dr.loc[('Tanzania', 'card')].fee_per_failed_attempt / (dr.f_fee.sum() / dr.f_att_ok.sum()):.0f}\u00d7"
    c["tc_vs_kc_words"] = words(dr.loc[("Tanzania", "card")].fee_per_failed_attempt / dr.loc[("Kenya", "card")].fee_per_failed_attempt)
    c["dr_all_ff"] = k1(dr.f_fee.sum())

    q = res["quintile_versions"]
    names = {"All translatable records": "qa", "Excluding extreme-volume anomalies": "qe", "Excluding escalation account(s)": "qs",
             "Excluding value anomalies": "qv", "All three exclusions": "q3"}
    for ver, key in names.items():
        mmr = q[(q.version == ver) & (q.pt == "mobilemoney")].iloc[0]
        cr = q[(q.version == ver) & (q.pt == "card")].iloc[0]
        c.update({f"{key}_m5": p1(mmr.q5_fail_rate), f"{key}_m14": p1(mmr.q1_4_fail_rate), f"{key}_mf": k1(mmr.q5_failed_fees),
                  f"{key}_ml": p0(mmr.q5_largest_customer_share), f"{key}_c": f"{p1(cr.q5_fail_rate)} / {p1(cr.q1_4_fail_rate)}"})
    qq = res["quintiles"]
    qm, qc = qq[qq.pt == "mobilemoney"], qq[qq.pt == "card"]
    c.update(q_card_min=p0(qc.fail_rate.min()), q_card_max=p0(qc.fail_rate.max()),
             q_mm_lo=p0(qm[qm.quintile < 5].fail_rate.min()), q_mm_hi=p0(qm[qm.quintile < 5].fail_rate.max()),
             q_mm_5=p0(qm[qm.quintile == 5].fail_rate.iloc[0]),
             q3_m5_0=p0(q[(q.version == "All three exclusions") & (q.pt == "mobilemoney")].q5_fail_rate.iloc[0]),
             q3_m14_0=p0(q[(q.version == "All three exclusions") & (q.pt == "mobilemoney")].q1_4_fail_rate.iloc[0]))
    qa_f = q[(q.version == "All translatable records") & (q.pt == "mobilemoney")].q5_failed_fees.iloc[0]
    qs_f = q[(q.version == "Excluding escalation account(s)") & (q.pt == "mobilemoney")].q5_failed_fees.iloc[0]
    c["q_esc_k"] = k0(qa_f - qs_f)

    # anomalies
    an = res["anomalies"]
    o = an["observations"]
    for k_, r in enumerate(o.head(5).itertuples()):
        c[f"an{k_}_f"], c[f"an{k_}_s"], c[f"an{k_}_ff"] = i0(r.f_att), i0(r.s_att), k1(r.f_fee)
        c[f"an{k_}_m"] = f"{r.prior_med:g}"
    rest = o.iloc[5:]
    c.update(an_rest_n=i0(len(rest)), an_rest_f=i0(rest.f_att.sum()), an_rest_ff=k1(rest.f_fee.sum()),
             an_obs=i0(len(o)), an_obs_words=words(len(o), True), an_cust=i0(o.customer_id.nunique()))
    sens = an["sensitivity"].set_index("thresholds")
    c.update(an_strict=p1(sens.share["strict"]), an_agreed=p1(sens.share["agreed"]), an_loose=p1(sens.share["loose"]))
    es_ = an["escalation_series"].set_index("period")
    c.update(esc_oct=i0(es_.f_att.get(pd.Timestamp("2023-10-01"), 0)), esc_jan=i0(es_.f_att.get(pd.Timestamp("2024-01-01"), 0)),
             esc_apr=i0(es_.f_att.get(pd.Timestamp("2024-04-01"), 0)))

    hm = res["hard_mixed"]["totals"].set_index("class")
    for cls, key in [("Extreme-volume anomaly", "hx"), ("Hard", "hh"), ("Mixed", "hm")]:
        r = hm.loc[cls]
        c.update({f"{key}_o": i0(r.observations), f"{key}_f": i0(r.f_att), f"{key}_fs": p1(r.share_f_att),
                  f"{key}_ff": k1(r.f_fee), f"{key}_ffs": p1(r.share_f_fee)})
    bc = res["hard_mixed"]["by_channel"].set_index("pt")
    c.update(hard_card=p0(bc.hard_share["card"]), hard_mm=p0(bc.hard_share["mobilemoney"]))

    cu = res["customers"]
    pe, la = cu["persistence"], cu["lapse"]
    c.update(pers_elig=i0(pe["eligible"]), pers_n=i0(pe["persistent"]), pers_pct=p0(pe["persistent"] / pe["eligible"]),
             pers_fatt=p1(pe["share_f_att"]), pers_ffee=p1(pe["share_f_fee"]), one_off=i0(pe["one_off_elevated"]),
             pers_m=m2(pe["persistent_f_fee"]), lapse_p=p0(pe["lapse_persistent"]), lapse_o=p0(pe["lapse_other"]),
             lapsed=i0(la["lapsed"]), active_before=i0(la["active_before"]), lapse_rate=p0(la["lapse_rate"]),
             lapse_cr_l=p1(la["count_rate_lapsed"]), lapse_cr_r=p1(la["count_rate_retained"]),
             lapse_fs_l=p1(la["fee_share_lapsed"]), lapse_fs_r=p1(la["fee_share_retained"]))
    for k_, r in enumerate(cu["tenure"].itertuples()):
        c.update({f"ten{k_}_cr": p1(r.fail_rate), f"ten{k_}_fs": p1(r.fee_share), f"ten{k_}_sh": p1(r.share_of_failed_fees)})

    lp = res["laney"]
    pt_ = lp["patterns"]
    for r in pt_.itertuples():
        key = f"lp_{r.country}_{r.pt}".replace(" ", "_")
        c.update({f"{key}_n": i0(r.eligible_months), f"{key}_med": p1(r.median_rate), f"{key}_f6": p1(r.first6), f"{key}_l6": p1(r.last6)})
    c.update(lp_cells=i0(len(pt_)), lp_tests=i0(lp["tests"]), lp_exc_share=p1(lp["excluded_share"]),
             lp_exc_n=i0(len(lp["excluded"])), lp_sig=i0(len(lp["signals"])), lp_sig_share=p1(len(lp["signals"]) / lp["tests"]),
             lp_sz_min=f"{pt_.sigma_z.min():.1f}", lp_sz_max=f"{pt_.sigma_z.max():.1f}")
    ex1 = lp["excluded"].iloc[0]
    c.update(lp_exc_top=k1(ex1.f_fee), lp_exc_top_n=i0(ex1.eligible_months))

    j = res["january"]
    cm = j["components"].set_index("component").usd
    rise = j["january_all"] - j["baseline_all"]
    c.update(jan_base_d=d0(j["baseline_all"]), jan_d=d0(j["january_all"]), jan_base_k=k1(j["baseline_all"]),
             jan_k=k1(j["january_all"]), jan_ex_d=sd0(cm["Extreme-volume anomalies"]), jan_ex_k=k1(cm["Extreme-volume anomalies"]),
             jan_ex_share=p0(cm["Extreme-volume anomalies"] / rise), jan_ex_jan_d=d0(j["january_extreme"]),
             jan_ex_jan_k=k1(j["january_extreme"]), jan_ex_base_d=d0(j["baseline_extreme"]), jan_ex_base_k=k1(j["baseline_extreme"]),
             jan_nb0=d0(j["baseline_nonanomalous"]), jan_nb1=d0(j["january_nonanomalous"]),
             jan_nb_chg=sd0(j["january_nonanomalous"] - j["baseline_nonanomalous"]), jan_fx=sd0(j["fx_effect"]),
             jan_vol=sd0(cm["Volume"]), jan_mix=sd0(cm["Mix"]), jan_fr=sd0(cm["Failure rate"]), jan_fy=sd0(cm["Fee yield"]),
             jan_ee=sd0(cm["Entry/exit cells"]), jan_vol_k=k1(cm["Volume"]), jan_fy_k=k1(cm["Fee yield"]),
             jan_top3=k1(j["top3_card_accounts"]), jan_fs1=p1(j["fee_share_nonanomalous_jan"]),
             jan_fs0=p1(j["fee_share_nonanomalous_base"]), jan_cr1=p1(j["count_rate_nonanomalous_jan"]),
             jan_cells_out=i0(j["cells_total"] - j["cells_used"]), jan_cells=i0(j["cells_total"]))
    for x in ["Volume", "Mix", "Failure rate", "Fee yield", "Entry/exit cells"]:
        pass
    cl = j["cells"].set_index(["country", "pt"])
    if ("Uganda", "card") in cl.index:
        c.update(jan_ug_r0=p1(cl.loc[("Uganda", "card")].rate0), jan_ug_r1=p1(cl.loc[("Uganda", "card")].rate1))
    if ("Tanzania", "card") in cl.index:
        c.update(jan_tz_y0=d2(cl.loc[("Tanzania", "card")].yield0), jan_tz_y1=d2(cl.loc[("Tanzania", "card")].yield1))

    fx = res["fx"]
    loc_eff = fx["local_reported"] - fx["local_constant"]
    bcy = fx["by_currency"].set_index("ccy")
    by = fx["by_year"].set_index("year")
    me = fx["measures"].set_index("measure")
    c.update(fx_local_eff=k1(abs(loc_eff)), fx_local_pct=("−" if loc_eff < 0 else "+") + p1(abs(loc_eff / fx["local_constant"])),
             fx_ghs_share=p0(bcy.effect["GHS"] / bcy.effect.sum()), fx_local_share=p1(fx["local_share_of_fees"]),
             fx_flag_avg=k1(fx["flagged_avg"]), fx_flag_end=k1(fx["flagged_end"]),
             fx_flag_pct=("−" if fx["flagged_end"] < fx["flagged_avg"] else "+") + p1(abs(fx["flagged_end"] / fx["flagged_avg"] - 1)),
             fx_me_ff=k1(fx["failed_fees_month_end"]),
             fx_me_pct=("−" if fx["failed_fees_month_end"] < h["failed_fees"] else "+") + p1(abs(fx["failed_fees_month_end"] / h["failed_fees"] - 1)))
    for y in by.index:
        e = by.loc[y]
        c[f"fx_y{y}"] = ("−" if e.effect < 0 else "+") + k1(abs(e.effect))
        c[f"fx_y{y}_p"] = ("−" if e.effect < 0 else "+") + p1(abs(e.effect / e.constant))
    for m_, key in [("Fees on failed transactions", "ff"), ("Successful-transaction fees", "sf")]:
        r = me.loc[m_]
        c.update({f"fx_{key}_r": k1(r.reported), f"fx_{key}_c": k1(r.constant),
                  f"fx_{key}_d": ("−" if r.difference < 0 else "+") + k1(abs(r.difference)),
                  f"fx_{key}_p": ("−" if r.difference < 0 else "+") + p1(abs(r.difference / r.constant))})
    for r in fx["ias_screen"].itertuples():
        c.update({f"ias_{r.ccy}_n": i0(r.months_above), f"ias_{r.ccy}_avg": p1(r.avg_range), f"ias_{r.ccy}_max": p1(r.max_range)})

    rc = res["recovery"]
    sc = rc["scenarios"].set_index("scenario")
    mk = rc["markets"].set_index("country")
    for s_, key in [("Conservative", "con"), ("Base", "base"), ("Optimistic", "opt")]:
        r = sc.loc[s_]
        c.update({f"rc_{key}_add": i0(r.additional_successes), f"rc_{key}_k": k1(r.incremental_fees),
                  f"rc_{key}_k0": k0(r.incremental_fees), f"rc_{key}_ann": k1(r.annual), f"rc_{key}_ann0": k0(r.annual),
                  f"rc_{key}_sr": p1(r.share_of_recorded_fees), f"rc_{key}_sa": p1(r.share_of_addressable)})
    pri = ["Kenya", "Tanzania", "Uganda"]
    c.update(rc_base_vs_succ=p0(sc.incremental_fees["Base"] / h["succ_fees"]), rc_pri_k0=k0(mk.loc[pri].incremental_base.sum()),
             rc_addr=k1(rc["addressable_f_fee"]), rc_addr_share=p1(rc["addressable_f_fee"] / res["drivers"].f_fee.sum()),
             rc_tot_att=i0(rc["total_att"]), rc_tot_fatt=i0(rc["addressable_f_att"]),
             rc_tot_rate=p1(rc["addressable_f_att"] / rc["total_att"]), rc_be=d2(rc["breakeven"]),
             rc_fps_min=d2(mk.fee_per_success.min()), rc_fps_max=d2(mk.fee_per_success.max()))
    for cn in mk.index:
        r = mk.loc[cn]
        key = f"rm_{cn}"
        c.update({f"{key}_a": i0(r.att), f"{key}_f": i0(r.f_att), f"{key}_r": p1(r.rate), f"{key}_t": p1(r.mm_rate),
                  f"{key}_pp": pp(r.reduction_base), f"{key}_add": i0(r.additional_base), f"{key}_fps": d2(r.fee_per_success),
                  f"{key}_inc": k1(r.incremental_base)})
    g = rc["gap"].set_index("country")
    for cn in g.index:
        r = g.loc[cn]
        c.update({f"gap_{cn}_ca": p1(r.card_all), f"gap_{cn}_ma": p1(r.mm_all), f"gap_{cn}_ga": pp(r.card_all - r.mm_all),
                  f"gap_{cn}_cs": p1(r.card_same), f"gap_{cn}_ms": p1(r.mm_same), f"gap_{cn}_gs": pp(r.card_same - r.mm_same),
                  f"gap_{cn}_n": i0(r.customers)})
    gt = rc["gap_totals"]
    ga, gs = gt["card_all"] - gt["mm_all"], gt["card_same"] - gt["mm_same"]
    c.update(gap_ca=p1(gt["card_all"]), gap_ma=p1(gt["mm_all"]), gap_ga=pp(ga), gap_cs=p1(gt["card_same"]), gap_ms=p1(gt["mm_same"]),
             gap_gs=pp(gs), gap_n=i0(gt["customers"]), gap_narrow=pp(ga - gs), gap_narrow_pct=p0((ga - gs) / ga),
             gap_gs0=f"{gs * 100:.0f}", rc_same=k1(rc["same_customer"]["incremental"]),
             rc_same_share=p1(rc["same_customer"]["card_att_share"]), rc_same_top=p1(rc["same_customer"]["top_customer_share"]),
             rc_off_n=i0(rc["offset"]["removed"]), rc_off_share=p1(rc["offset"]["removed_share"]), rc_off=k1(rc["offset"]["incremental"]))
    bx = rc["benchmark_ex_escalation"]
    gx_all = gt["card_all"] - bx["mm_all"]
    gx_same = bx["same_card"] - bx["same_mm"]
    kx = bx["same_rates"].loc["Kenya"] if "Kenya" in bx["same_rates"].index else None
    c.update(bx_kenya_mm=p1(bx["mm_rate"]["Kenya"]), bx_inc=k1(bx["incremental"]), bx_inc0=k0(bx["incremental"]),
             bx_kenya_inc=k1(bx["by_market"]["Kenya"]), bx_mm_all=p1(bx["mm_all"]), bx_gap_all=pp(gx_all),
             bx_same_mm=p1(bx["same_mm"]), bx_gap_same=pp(gx_same), bx_gap_same0=f"{gx_same * 100:.0f}",
             bx_same_n=i0(bx["same_customers"]), bx_same_inc=k1(bx["same_incremental"]),
             bx_kenya_gap_same=pp(kx.card_rate - kx.mm_rate) if kx is not None else "\u2014",
             bx_uplift=p0(bx["incremental"] / sc.incremental_fees["Base"] - 1),
             succ_annual=k1(h["succ_fees"] * 12 / len(res["monthly"])),
             rc_base_vs_succ_ann=p0(sc.annual["Base"] / (h["succ_fees"] * 12 / len(res["monthly"]))))
    card_us = mk.rate
    c.update(usd_card_min=p0(card_us.min()), usd_card_max=p0(card_us.max()),
             mm_mk_min=p0(mk.mm_rate.min()), mm_mk_max=p0(mk.mm_rate.max()))
    for r in rc["contribution"].itertuples():
        c[f"contrib_{int(round(r.cost_ratio * 100))}"] = k1(r.contribution) if r.contribution > 0 else "$0"

    mx = res["matrix"].set_index(["country", "pt"])
    for (cn, pt), key in [(("Kenya", "card"), "kc"), (("Uganda", "card"), "uc"), (("Tanzania", "card"), "tc"),
                          (("Kenya", "mobilemoney"), "km"), (("Ghana", "card"), "gc"), (("Uganda", "mobilemoney"), "um"),
                          (("Zambia", "card"), "zc")]:
        r = mx.loc[(cn, pt)]
        c.update({f"mx_{key}_fr": p1(r.fail_rate), f"mx_{key}_ff": k1(r.f_fee), f"mx_{key}_fv": f"${r.failed_value / 1e6:.1f}M",
                  f"mx_{key}_ip": k1(r.internal_potential),
                  f"mx_{key}_cp": k1(r.cross_channel_potential) if pd.notna(r.cross_channel_potential) else "—",
                  f"mx_{key}_top": p0(r.top_customer_share)})
    ua = mx.loc[("Uganda", "alternative channels")]
    c.update(mx_ua_fr=p0(ua.fail_rate), mx_ua_ff=k0(ua.f_fee))

    se = res["sensitivity"].set_index("treatment")
    for t_, key in [("Excluding value anomalies and untranslatable records", "sv"), ("Month-end rates", "sm"),
                    ("2022 constant currency", "sc"), ("Excluding extreme-volume anomalies", "sx"),
                    ("Also excluding escalation account(s)", "se")]:
        r = se.loc[t_]
        c.update({f"{key}_ff": k1(r.f_fee), f"{key}_fs": p1(r.fee_share), f"{key}_cr": p1(r.count_rate)})
    c["rm_cr"] = p1(se.count_rate["Also excluding escalation account(s)"])
    c["rm_fs"] = p1(se.fee_share["Also excluding escalation account(s)"])
    m = res["monthly"]
    rng = lambda a, b_: f"{a * 100:.0f}\u2013{b_ * 100:.0f}%"
    c.update(rem_range=rng(m.count_rem.min(), m.count_rem.max()), card_range=rng(card.fail_rate.min(), card.fail_rate.max()),
             usd_card_range=rng(card_us.min(), card_us.max()), mm_mk_range=rng(mk.mm_rate.min(), mk.mm_rate.max()),
             q_card_range=rng(qc.fail_rate.min(), qc.fail_rate.max()),
             q_mm_range=rng(qm[qm.quintile < 5].fail_rate.min(), qm[qm.quintile < 5].fail_rate.max()))
    rx = res["remaining_mix"]
    c.update(rm_card_share=p0(rx["card"] / rx["total"]), rm_card_m=m2(rx["card"]), rm_usdcard_share=p0(rx["usd_card"] / rx["total"]),
             rm_usdcard_m=m2(rx["usd_card"]), rm_mm_share=p0(rx["mobilemoney"] / rx["total"]))
    c.update(customers_failed=i0(cc["customers"]), customers_transacting=i0(cc.get("customers_transacting", cc["customers"])),
             an_accounts=i0(res["anomalies"]["observations"].customer_id.nunique()),
             fx_sf_abs=k1(abs(res["fx"]["measures"].set_index("measure").difference["Successful-transaction fees"])))
    cn_ = res["countries"].set_index("country")
    c.update(attempts_short=f"{h['attempts'] / 1e6:.2f}M", anom_pct_w=f"{(ex.f_fee + es.f_fee) / tot * 100:.1f}%",
             rm_pct_w=f"{rm.f_fee / tot * 100:.1f}%",
             rem_range_words=f"{m.count_rem.min() * 100:.0f}% and {m.count_rem.max() * 100:.0f}%",
             kenya_fs=p1(cn_.fee_share["Kenya"]), card_fs=p1(ch.fee_share["card"]), mm_fs=p1(ch.fee_share["mobilemoney"]),
             bank_fs=p1(ch.fee_share["bank transfer"]), mm_share=p0(ch.share_of_failed_fees["mobilemoney"]),
             nm=i0(len(m)), jan_cells_out_n=i0(j["cells_total"] - j["cells_used"]))
    c.update(rem_min=p0(m.count_rem.min()), rem_max=p0(m.count_rem.max()),
             rem_succ_month=k1((res["bridge"].f_fee.sum() * 0 + (h["succ_fees"])) / len(m)))
    # ---- numbers the text used to type (stage 11 flags any that come back)
    n_mo = len(m)
    c.update(fs_rem_2022=p0(m.set_index("period").share_rem[pd.DatetimeIndex(m.period).year == 2022].mean()),
             fs_rem_2024=p0(m.set_index("period").share_rem[pd.DatetimeIndex(m.period).year == 2024].mean()))
    esc_s = res["anomalies"]["escalation_series"]
    ep = res["anomalies"]["escalation_profile"]
    c.update(esc_smax=i0(esc_s.s_att.max()), esc_mm_att=i0(ep["mobilemoney_attempts"]), esc_card_att=i0(ep["usd_card_attempts"]),
             an_top_n_words=words(res["anomalies"]["top_n"], True), an_top_n_words_l=words(res["anomalies"]["top_n"]),
             jan_card_n_words=words(res["january"]["top_n_card"]), anom_in_n_words=f"{words(round((ex.f_fee + es.f_fee) / tot * 5), True)} in five")
    ob = res["anomalies"]["observations"]
    early = ob[(ob.period >= "2022-01-01") & (ob.period <= "2023-07-01")]
    c["an_early_words"] = words(early.period.nunique())
    ten = res["customers"]["tenure"]
    c["ten_fs_range"] = f"{ten.fee_share.min() * 100:.0f}\u2013{ten.fee_share.max() * 100:.0f}%"
    c["lp_cells_words"] = words(len(pt_), True)
    sg = res["laney"]["signals"]
    for r in pt_.itertuples():
        key = f"lp_{r.country}_{r.pt}".replace(" ", "_")
        c[f"{key}_flags"] = r.flags.capitalize()
        c[f"{key}_sig"] = month_list(sg[(sg.country == r.country) & (sg.pt == r.pt)])
    sk = sg[(sg.country == "Kenya") & (sg.pt == "mobilemoney")].sort_values("period").iloc[-1]
    sgc = sg[(sg.country == "Ghana") & (sg.pt == "card")].sort_values("period").iloc[0]
    c.update(lp_km_last_share=p0(sk.top_customer_share), lp_gc_share=p0(sgc.top_customer_share),
             lp_km_last_month=f"{pd.Timestamp(sk.period):%B}", lp_gc_month=f"{pd.Timestamp(sgc.period):%B %Y}")
    cardmed = pt_[pt_.pt == "card"].median_rate
    c["lp_card_med_range"] = f"{cardmed.min() * 100:.0f}\u2013{cardmed.max() * 100:.0f}%"
    me2 = res["fx"]["measures"]
    c["fx_mean_pct"] = p0(abs((me2.difference / me2.constant).mean()))
    sv = res["sensitivity"].set_index("treatment").fee_share
    c.update(sens_fs_range=f"{sv.iloc[:4].min() * 100:.0f}\u2013{sv.iloc[:4].max() * 100:.0f}%", sens_fs_anom=p0(sv.iloc[-1]))
    ex_ = res.get("examples")
    if ex_:
        lg, rcg = ex_["largest"], ex_["recurring"]
        c.update(va_value=f"{lg['value'] / 1e12:.2f} trillion", va_ccy=lg["ccy"], va_att=i0(lg["attempts"]), va_fee=i0(lg["fee"]),
                 va_ug_n=i0(rcg["records"]), va_ug_value=f"{rcg['value_min'] / 1e6:,.0f}\u2013{rcg['value_max'] / 1e6:,.0f} million",
                 va_ug_att=f"{rcg['att_min']:,}\u2013{rcg['att_max']:,}", va_ug_fee=f"{rcg['fee_ratio'] * 100:.1f}%", va_ug_cust=str(rcg["customer"]))
    # lapse caveat
    la_ = res["customers"]["lapse"]
    c.update(lapse_few_pct=p0(la_["few_months_share"]), lapse_gap3_pct=p0(la_["gap3_share"]))
    # recovery: legitimate rejections, resampling interval, range across choices, pilot targets
    rcv = res["recovery"]
    nr, iv, bxx = rcv["no_rejections"], rcv["interval"], rcv["benchmark_ex_escalation"]
    vals = [sc.incremental_fees["Base"], bxx["incremental"], rcv["same_customer"]["incremental"], bxx["same_incremental"], rcv["offset"]["incremental"], nr["incremental"]]
    c.update(rc_nr_k=k1(nr["incremental"]), rc_nr_k0=k0(nr["incremental"]), rc_nr_share=p0(nr["share_of_failed_attempts"]), rc_nr_n=i0(nr["customer_months"]),
             rc_ci_lo=k0(iv["low"]), rc_ci_med=k0(iv["median"]), rc_ci_hi=k0(iv["high"]), rc_ci_level=p0(iv["level"]), rc_ci_reps=i0(iv["replicates"]), rc_ci_seed=str(iv["seed"]), tz_top_share=p0(rcv["tanzania_concentration"]["top_share"]), tz_card_customers=i0(rcv["tanzania_concentration"]["customers"]),
             tz_top_n_words=words(rcv["tanzania_concentration"]["top_n"]),
             rc_rng_lo=k0(min(vals)), rc_rng_hi=k0(max(vals)))
    for cn in ["Kenya", "Tanzania", "Uganda"]:
        rr_ = mk.loc[cn]
        c.update({f"pl_{cn}_from": p1(rr_.rate), f"pl_{cn}_to": p1(rr_.best_window)})
    rc_ = res.get("reconciliation")
    if rc_:                                    # report basis against the same data with the SLL fix switched off (stage 01E)
        a_, b_ = rc_["report_basis"], rc_["no_sll_fix"]
        lo = lambda x: ", ".join(f"{m['month']} {m['share'] * 100:.1f}%" for m in x["months_below_78"]) or "none"
        c.update(pre_fees_d=d0(b_["fees"]), pre_ff_d=d0(b_["failed_fees"]), pre_ff_k=k1(b_["failed_fees"]), pre_fs=p1(b_["fee_share"]),
                 pre_jan_d=d0(b_["jan_failed_fees"]), sll_effect_k=k1(rc_["sll_effect_failed_fees"]),
                 jan_cr=p1(a_["jan_count_rate"]), jan_fs_all=p1(a_["jan_fee_share"]),
                 lo78_n=i0(len(a_["months_below_78"])), lo78_list=lo(a_), lo78_n_pre=i0(len(b_["months_below_78"])), lo78_list_pre=lo(b_),
                 bank_rec_share=p1(rc_["bank_transfer_record_share"]))
    return c


# ------------------------------------------------------------------------------- rendering

TOKEN = re.compile(r"\{\{(\w+)\}\}")


def render(template: str, ctx: dict) -> str:
    missing = sorted({k for k in TOKEN.findall(template) if k not in ctx})
    if missing:
        raise KeyError(f"Template keys with no value: {missing}")
    return TOKEN.sub(lambda m_: ctx[m_.group(1)], template)


# ------------------------------------------------------------------------------- HTML rendering
import html as _html  # noqa: E402
import shutil  # noqa: E402

TABLE_RE = re.compile(r"^::: table (\w+) \| (.+)$")
NUMERIC = re.compile(r"^[\s*]*[−+\-–]?\$?[\d][\d,.]*\s?(%|K|M|bn|×|pp)?(\s*\([^)]*\))?[\s*]*$|^[\s*]*[—–-][\s*]*$")


def _math(tex: str, display: bool) -> str:
    from latex2mathml.converter import convert
    return convert(tex.strip(), display="block" if display else "inline")


def numbering(texts: list[str]) -> tuple[dict, dict]:
    """Figure and table numbers in order of first appearance across the given texts."""
    from .figindex import report_numbers
    figs = report_numbers()                  # read from outputs/figure_index.csv, the one figure index
    tabs: dict[str, int] = {}
    for t in texts:
        for line in t.splitlines():
            m = TABLE_RE.match(line.strip())
            if m and m.group(1) not in tabs:
                tabs[m.group(1)] = len(tabs) + 1
    return figs, tabs


def md_to_html(md: str, resolve, figs: dict, tabs: dict, idp: str = "sec-") -> str:
    """`resolve(slug)` gives the figure file's URL relative to the HTML page (found through outputs/figure_index.csv)."""
    import markdown
    from bs4 import BeautifulSoup

    from .figures import REPORT_ORDER
    md = re.sub(r"\{\{fig:(\w+)\}\}", lambda m: f"Figure {figs[m.group(1)]}", md)
    md = re.sub(r"\{\{tab:(\w+)\}\}", lambda m: f"Table {tabs[m.group(1)]}", md)
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if s.startswith("[[figure "):
            slug = s[len("[[figure "):-2].strip()
            if slug not in REPORT_ORDER:
                raise KeyError(f"Figure '{slug}' is not in REPORT_ORDER (figures.py).")
            out += ["", f'<figure class="chart" id="fig-{slug}"><img src="{resolve(slug)}" alt="Figure {figs[slug]}"></figure>', ""]
        elif TABLE_RE.match(s):
            slug, cap = TABLE_RE.match(s).groups()
            i += 1
            body = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                body.append(lines[i]); i += 1
            src = ""
            if i < len(lines) and lines[i].strip().startswith(("Source:", "Note:", "Flags:")):
                src = f'<p class="src">{_html.escape(lines[i].strip())}</p>'; i += 1
            tbl = markdown.markdown("\n".join(body), extensions=["tables"])
            out += ["", f'<div class="tbl" id="tab-{slug}"><p class="caption"><span class="lab">Table {tabs[slug]}.</span> {cap}</p>{tbl}{src}</div>', ""]
            continue
        elif s.startswith("$$"):
            tex = s[2:]
            while not tex.rstrip().endswith("$$"):
                i += 1; tex += " " + lines[i].strip()
            parts = [t for t in re.split(r"\\qquad", tex.rstrip()[:-2]) if t.strip().strip(",")]
            maths = "".join(_math(t.strip().rstrip(","), True) for t in parts)
            out += ["", f'<div class="eq">{maths}</div>', ""]
        else:
            out.append(ln)
        i += 1
    md = "\n".join(out)
    md = re.sub(r"\\\((.+?)\\\)", lambda m: _math(m.group(1), False), md)
    md = re.sub(r"\*\\?\[([^\]*]+?)\\?\]\*", lambda m: f'<span class="tag">{m.group(1)}</span>', md)
    html = markdown.markdown(md, extensions=["tables", "sane_lists", "md_in_html"])
    soup = BeautifulSoup(html, "html.parser")
    for bq in soup.find_all("blockquote"):
        bq.name = "div"; bq["class"] = "callout"
    for h in soup.find_all("h2"):
        m = re.match(r"^(\d+\.|Appendix [A-Z]\.)\s*(.*)$", h.get_text())
        if m:
            h["class"] = "section appendix" if m.group(1).startswith("Appendix") else "section"
            h.clear()
            num = soup.new_tag("span", attrs={"class": "num"}); num.string = m.group(1)
            h.append(num); h.append(m.group(2))
    sec, sub = None, 0
    for h in soup.find_all(["h2", "h3"]):
        if h.name == "h2":
            m = re.match(r"^(\d+)\.|^Appendix ([A-Z])\.", h.get_text().strip())
            sec, sub = ((m.group(1) or m.group(2)) if m else None), 0
        elif sec:
            sub += 1
            num = soup.new_tag("span", attrs={"class": "subnum"}); num.string = f"{sec}.{sub} "
            h.insert(0, num)
    for t in soup.find_all("table"):
        rows = t.find_all("tr")
        if rows and len(rows[0].find_all(["td", "th"])) >= 8:
            t["class"] = "wide"
        body = [r for r in rows if r.find("td")]
        ncol = max((len(r.find_all(["td", "th"])) for r in rows), default=0)
        for c in range(ncol):
            cells = [r.find_all("td")[c] for r in body if len(r.find_all("td")) > c]
            filled = [x for x in cells if x.get_text().strip()]
            if filled and all(NUMERIC.match(x.get_text()) for x in filled) and any(re.search(r"\d", x.get_text()) for x in filled):
                for x in cells:
                    x["class"] = "num"
                th = t.find_all("th")
                if len(th) > c:
                    th[c]["class"] = "num"
        for r in body:
            first = r.find("td")
            if first and first.find("strong") and first.get_text().strip().lower().startswith(("total", "all ")):
                r["class"] = "total"
    for k, h in enumerate(soup.find_all(["h2", "h3"]), start=1):
        h["id"] = f"{idp}{k}"
    from .flow import mark_long_tables, place_figures
    place_figures(soup, figs)
    mark_long_tables(soup)
    return str(soup)


def _wrap(soup, first, *rest):
    w = soup.new_tag("div", attrs={"class": "keep"})
    first.insert_before(w)
    w.append(first.extract())
    for r in rest:
        w.append(r.extract())
    return w


def _keep_together(soup) -> None:
    """A figure stays with the sentence that discusses it, and a table with the sentence that introduces it."""
    for fig in soup.find_all("figure", class_="chart"):
        nxt = fig.find_next_sibling()
        if nxt is not None and nxt.name == "p" and "keep" not in (fig.parent.get("class") or []):
            _wrap(soup, fig, nxt)
    for t in soup.find_all("div", class_="tbl"):
        prv = t.find_previous_sibling()
        if prv is None or prv.name != "p":
            continue
        if prv.parent is not None and "keep" in (prv.parent.get("class") or []):
            continue
        _wrap(soup, prv, t)
    # a paragraph already grouped with a figure that is also followed by a table: extend that group
    for t in soup.find_all("div", class_="tbl"):
        prv = t.find_previous_sibling()
        if prv is not None and "keep" in (prv.get("class") or []) and t.parent is not prv:
            prv.append(t.extract())


def _fill(template: str, ctx: dict, meta: dict) -> str:
    template = re.sub(r"\{\{meta\.(\w+)\}\}", lambda m: _html.escape(str(meta.get(m.group(1), ""))), template)
    return render(template, ctx)


def _css_str(t: str) -> str:
    return t.replace("\\", "\\\\").replace('"', '\\"')


def footer_css(meta: dict) -> str:
    """Centred two-line footer on every page except the cover, built from meta.yaml."""
    l1 = f"{meta['author_line']} · {meta['email']} · {meta['telephone']} · ORCID {meta['orcid']}"
    l2 = f"{meta['title']} · "
    nl = chr(92) + "A"          # CSS escape for a line break inside content:
    return ("<style>@page { @bottom-center { content: \"" + _css_str(l1) + "\" \"" + nl + "\" \"" + _css_str(l2) + "\" counter(page);"
            " white-space: pre; text-align: center; font: 7.6pt/1.5 \"Source Sans 3\", sans-serif; color: #6B6860; } }"
            " @page cover { @bottom-center { content: none; } }</style>")


def _page(title: str, css_rel: str, body: str, meta: dict | None = None) -> str:
    extra = footer_css(meta) if meta else ""
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>{_html.escape(title)}</title>'
            f'<link rel="stylesheet" href="{css_rel}/report.css">{extra}</head><body>{body}</body></html>')


def find_browser() -> str | None:
    """Chrome, Chromium or Edge (all Chromium) for printing to PDF."""
    for name in ["google-chrome", "chrome", "chromium", "chromium-browser", "msedge", "microsoft-edge"]:
        if shutil.which(name):
            return shutil.which(name)
    for p in [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]:
        if Path(p).exists():
            return p
    return None


def print_pdf(html_path: Path, pdf_path: Path) -> Path | None:
    exe = find_browser()
    if not exe:
        return None
    subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer", "--allow-file-access-from-files",
                    "--run-all-compositor-stages-before-draw", "--virtual-time-budget=20000",
                    f"--print-to-pdf={pdf_path.resolve()}", html_path.resolve().as_uri()],
                   check=True, capture_output=True, timeout=300)
    return pdf_path


def author_line(meta: dict) -> str:
    return f"{meta['author']}, {meta['credentials']}" if meta.get("credentials") else meta["author"]


def collect_entries(main_html: str, fig_titles: dict) -> dict:
    """Headings, figures and tables of the main report in reading order, for the contents and the two lists."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(main_html, "html.parser")
    out = {"contents": [], "figures": [], "tables": []}
    for el in soup.find_all(["h2", "h3", "figure", "div"]):
        if el.name == "h2" and el.get("id"):
            num = el.find("span", class_="num")
            text = (num.get_text() + " " if num else "") + el.get_text()[len(num.get_text()) if num else 0:].strip()
            out["contents"].append({"id": el["id"], "level": 1, "text": text.strip()})
        elif el.name == "h3" and el.get("id"):
            sub = el.find("span", class_="subnum")
            text = el.get_text().strip()
            out["contents"].append({"id": el["id"], "level": 2, "text": text if sub else text})
        elif el.name == "figure" and el.get("id"):
            slug = el["id"][len("fig-"):]
            out["figures"].append({"id": el["id"], "level": 1, "text": fig_titles.get(slug, slug)})
        elif el.name == "div" and "tbl" in (el.get("class") or []):
            cap = el.find("p", class_="caption")
            out["tables"].append({"id": el["id"], "level": 1, "text": " ".join(cap.get_text().split())})
    return out


def _toc_section(title: str, entries: list, pages: dict | None, cls: str) -> str:
    li = []
    for e in entries:
        pg = pages.get(e["id"], "00") if pages else "00"
        li.append(f'<li class="l{e["level"]}"><a href="#{e["id"]}"><span class="t">{_html.escape(e["text"])}</span>'
                  f'<span class="dots"></span><span class="pg">{pg}</span></a></li>')
    return f'<section class="toc {cls}"><h2 class="toc-title">{title}</h2><ul class="toc-list">{"".join(li)}</ul></section>'


def read_pages(pdf: Path, ids: list[str]) -> dict[str, int]:
    """Page (1-based) of every contents target, read from the PDF's internal links (Chrome writes them as named destinations)."""
    import fitz
    doc = fitz.open(pdf)
    got: dict[str, int] = {}
    for page in doc:
        for l in page.get_links():
            if l.get("nameddest"):
                got[l["nameddest"]] = l["page"] + 1
    missing = [i for i in ids if i not in got]
    if missing:
        raise RuntimeError(f"No target page found in the PDF for: {missing[:5]}")
    return {i: got[i] for i in ids}


def build_report(res: dict, root: Path, out_dir: Path) -> dict:
    """Full report (HTML, PDF with contents and lists of figures and tables) and the executive brief."""
    import os

    import yaml

    from .figures import label
    from .pipeline import figure_file, load_figure_index
    content = root / "report" / "content"
    meta = yaml.safe_load((content / "meta.yaml").read_text(encoding="utf-8"))
    meta["author_line"] = author_line(meta)
    ctx = context(res)
    out_dir.mkdir(parents=True, exist_ok=True)
    css_rel = os.path.relpath(root / "report" / "assets", out_dir).replace("\\", "/")
    resolve = lambda slug: os.path.relpath(figure_file(slug), out_dir).replace("\\", "/")
    idx = load_figure_index()
    fig_titles = dict(zip(idx.slug, idx.title))
    summary = (content / "01_summary.md").read_text(encoding="utf-8")
    main = (content / "03_main_report.md").read_text(encoding="utf-8")
    figs, tabs = numbering([main])
    front = md_to_html(_fill(summary, ctx, meta), resolve, figs, tabs, idp="front-")
    main_html = md_to_html(render(main, ctx), resolve, figs, tabs)
    entries = collect_entries(main_html, fig_titles)
    flat = entries["contents"] + entries["figures"] + entries["tables"]

    def compose(pages: dict | None, main_part: str) -> str:
        toc = (_toc_section("Contents", entries["contents"], pages, "c-contents")
               + _toc_section("List of figures", entries["figures"], pages, "c-figures")
               + _toc_section("List of tables", entries["tables"], pages, "c-tables"))
        body = (_fill((content / "00_cover.html").read_text(encoding="utf-8"), ctx, meta)
                + '<section class="front">' + front + "</section>"
                + _fill((content / "02_at_a_glance.html").read_text(encoding="utf-8"), ctx, meta)
                + toc + '<main class="main">' + main_part + "</main>")
        return _page(meta["title"], css_rel, body, meta)

    from .flow import apply_state, plan
    full = out_dir / "The_Economics_of_Payment_Failure.html"
    state = {"scale": {}, "pull": {}}
    fig_files = {slug: figure_file(slug) for slug in figs}
    flow_log: list[str] = []
    pages, passes, pdf = None, 0, None
    while True:
        passes += 1
        full.write_text(compose(pages, apply_state(main_html, state)), encoding="utf-8")
        pdf = print_pdf(full, full.with_suffix(".pdf"))
        if pdf is None:
            break
        new = read_pages(pdf, [e["id"] for e in flat])
        chapter_pages = {new[e["id"]] for e in entries["contents"] if e["level"] == 1}
        changes = plan(state, main_html, pdf, chapter_pages, fig_files) if passes < 10 else []
        flow_log += [f"pass {passes}: {c}" for c in changes]
        if not changes and new == pages:
            break
        if passes >= 14:
            raise RuntimeError("The page flow and the contents page numbers do not settle after 14 passes")
        pages = new
    brief_body = _fill((content / "brief.html").read_text(encoding="utf-8"), ctx, {**meta, "author": meta["author_line"]})
    brief_body = re.sub(r"\[\[figure (\w+)\]\]", lambda m: f'<figure class="chart"><img src="{resolve(m.group(1))}"></figure>', brief_body)
    brief = out_dir / "Executive_Brief.html"
    brief.write_text(_page(meta["title"] + " - Executive brief", css_rel, '<div class="brief">' + brief_body + "</div>", meta), encoding="utf-8")
    brief_pdf = print_pdf(brief, brief.with_suffix(".pdf"))
    import json
    (out_dir / "contents.json").write_text(json.dumps({"passes": passes, "pages": pages, "flow": flow_log, "state": state, **entries}, indent=1), encoding="utf-8")
    return {"html": full, "pdf": pdf, "brief_html": brief, "brief_pdf": brief_pdf, "entries": entries, "pages": pages,
            "meta": meta, "passes": passes, "figures": figs, "tables": tabs}
