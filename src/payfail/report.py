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
             fee_per_failed=d2(h["failed_fees"] / h["failed"]))

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
             bank_fpf=d2(ch.f_fee["bank transfer"] / ch.f_att["bank transfer"]),
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
             mm_max=p0(mm.fail_rate.max()), kenya_card_all=m2(kc_all.f_fee))

    dr = res["drivers"].set_index(["country", "pt"])
    tot_att = dr.att.sum()
    for (cn, pt), key in [(("Kenya", "card"), "kc"), (("Kenya", "mobilemoney"), "km"), (("Uganda", "card"), "uc"),
                          (("Tanzania", "card"), "tc"), (("Ghana", "card"), "gc"), (("Uganda", "mobilemoney"), "um")]:
        r = dr.loc[(cn, pt)]
        c[f"dr_{key}_sa"] = p1(r.att / tot_att)
        c[f"dr_{key}_fr"] = p1(r.fail_rate)
        c[f"dr_{key}_fpf"] = d2(r.f_fee / r.f_att)
        c[f"dr_{key}_ff"] = k1(r.f_fee)
    c["kenya_card_extreme"] = k0(kc_all.f_fee - dr.loc[("Kenya", "card")].f_fee)
    c["dr_all_fr"] = p1(dr.f_att.sum() / tot_att)
    c["dr_all_fpf"] = d2(dr.f_fee.sum() / dr.f_att.sum())
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
             an_obs=i0(len(o)), an_cust=i0(o.customer_id.nunique()))
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
    from .figures import REPORT_ORDER, label
    figs = {slug: label(slug).split()[1] for slug in REPORT_ORDER}
    tabs: dict[str, int] = {}
    for t in texts:
        for line in t.splitlines():
            m = TABLE_RE.match(line.strip())
            if m and m.group(1) not in tabs:
                tabs[m.group(1)] = len(tabs) + 1
    return figs, tabs


def _figure_file(slug: str, fig_dir: Path) -> str:
    hits = sorted(fig_dir.glob(f"fig*_{slug}.svg")) or sorted(fig_dir.glob(f"fig*_{slug}.png"))
    if not hits:
        raise FileNotFoundError(f"No exported figure for '{slug}' in {fig_dir}; run the figures stage first.")
    return hits[0].name


def md_to_html(md: str, fig_dir: Path, fig_rel: str, figs: dict, tabs: dict) -> str:
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
            out += ["", f'<figure class="chart"><img src="{fig_rel}/{_figure_file(slug, fig_dir)}" alt="Figure {figs[slug]}"></figure>', ""]
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
            out += ["", f'<div class="tbl"><p class="caption"><span class="lab">Table {tabs[slug]}.</span> {cap}</p>{tbl}{src}</div>', ""]
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
    return str(soup)


def _fill(template: str, ctx: dict, meta: dict) -> str:
    template = re.sub(r"\{\{meta\.(\w+)\}\}", lambda m: _html.escape(str(meta.get(m.group(1), ""))), template)
    return render(template, ctx)


def _page(title: str, css_rel: str, body: str) -> str:
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>{_html.escape(title)}</title>'
            f'<link rel="stylesheet" href="{css_rel}/report.css"></head><body>{body}</body></html>')


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


def build_report(res: dict, root: Path, fig_dir: Path, out_dir: Path) -> dict:
    """Full report and executive brief: HTML and PDF in out_dir."""
    import yaml
    content = root / "report" / "content"
    meta = yaml.safe_load((content / "meta.yaml").read_text(encoding="utf-8"))
    ctx = context(res)
    out_dir.mkdir(parents=True, exist_ok=True)
    css_rel = Path("../../report/assets").as_posix()
    fig_rel = Path("../figures").as_posix()
    summary = (content / "01_summary.md").read_text(encoding="utf-8")
    main = (content / "03_main_report.md").read_text(encoding="utf-8")
    figs, tabs = numbering([main])
    body = (_fill((content / "00_cover.html").read_text(encoding="utf-8"), ctx, meta)
            + '<section class="front">' + md_to_html(_fill(summary, ctx, meta), fig_dir, fig_rel, figs, tabs) + "</section>"
            + _fill((content / "02_at_a_glance.html").read_text(encoding="utf-8"), ctx, meta)
            + '<main class="main">' + md_to_html(render(main, ctx), fig_dir, fig_rel, figs, tabs) + "</main>")
    full = out_dir / "The_Economics_of_Payment_Failure.html"
    full.write_text(_page(meta["title"], css_rel, body), encoding="utf-8")
    brief_body = _fill((content / "brief.html").read_text(encoding="utf-8"), ctx, meta)
    brief_body = re.sub(r"\[\[figure (\w+)\]\]", lambda m: f'<figure class="chart"><img src="{fig_rel}/{_figure_file(m.group(1), fig_dir)}"></figure>', brief_body)
    brief = out_dir / "Executive_Brief.html"
    brief.write_text(_page(meta["title"] + " - Executive brief", css_rel, '<div class="brief">' + brief_body + "</div>"), encoding="utf-8")
    return {"html": full, "pdf": print_pdf(full, full.with_suffix(".pdf")),
            "brief_html": brief, "brief_pdf": print_pdf(brief, brief.with_suffix(".pdf"))}
