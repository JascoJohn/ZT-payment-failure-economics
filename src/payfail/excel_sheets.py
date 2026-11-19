"""Builders for the chapter sheets 03, 04 and 08, the data-quality sheet 01E, and the charts added to 02, 05, 06 and 07."""
from __future__ import annotations

import numpy as np
import pandas as pd
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.chart import Reference

from .excel import BOLD, INT, LINK_FONT, NOTE, PCT, USD, USD2, IN_FILL, IN_FONT, _c
from .excel_ch import (AMBER, BRICK, GREEN, NAVY, SAND, SKY, TEAL, Wr, bar_chart, bubble_chart, line_chart, scatter_chart, static_table, val)
from .excel_ch import PYFILL, PYFONT
from .figures import label

PTS = ["card", "mobilemoney", "alternative channels", "bank transfer"]
CNT = ["Kenya", "Uganda", "Tanzania", "Ghana", "Zambia"]
PT_ALL = ["card", "mobilemoney", "alternative channels", "bank transfer", "account", "pay with wallet", "enaira"]


def ref(ws, col, r1, r2=None):
    return Reference(ws, min_col=col, min_row=r1, max_row=r2 if r2 is not None else r1)


# ============================================================================================ 03 Concentration
def build_conc(bk) -> dict:
    res, T, S = bk.res, bk.tx, bk.S
    w = Wr(bk, "03_Concentration", [36, 16, 16, 16, 16, 16, 16, 16, 16, 16])
    ws = w.ws
    P = {}
    w.title("03_Concentration. Where failure concentrates")
    w.text("Count measures use all records; USD measures use records with an exchange rate. Charts sit to the right of each table.", note=True)
    w.blank()
    # ---- payment types and markets
    for title, col, items, key in [("By payment type", "E", PT_ALL, "pt"), ("By market", "J", CNT, "mk")]:
        w.row([_c(ws, title, BOLD)])
        w.head(["", "Attempts", "Failed attempts", "Count failure rate", "Fees (USD)", "Failed fees (USD)", "Failed-fee share", "Share of all failed fees"])
        first = w.r + 1
        for it in items:
            i = w.r + 1
            k = f"{T(col)},$A{i}"
            w.row([_c(ws, it), _c(ws, f"=SUMIFS({T('P')},{k})", fmt=INT), _c(ws, f"=SUMIFS({T('Q')},{k})", fmt=INT), _c(ws, f"=IFERROR(C{i}/B{i},0)", fmt=PCT),
                   _c(ws, f"=SUMIFS({T('T')},{k})", fmt=USD), _c(ws, f"=SUMIFS({T('W')},{k})", fmt=USD), _c(ws, f"=IFERROR(F{i}/E{i},0)", fmt=PCT),
                   _c(ws, f"=F{i}/{S['failed_fees']}", fmt=PCT)])
            if key == "pt" and it == "card":
                P["card_share"] = f"{w.q}$H${i}"
        P[key + "_first"], P[key + "_last"] = first, w.r
        if key == "pt":
            ch = bar_chart(ws, bk.ftitle("channels"), ref(ws, 1, first, first + 5), [(ref(ws, 6, first, first + 5), "Fees on failed transactions", NAVY)],
                           horizontal=True, yfmt="$#,##0", point_colors=[NAVY] + [SAND] * 5, labels=True)
            w.chart(ch, "J", first - 2)
            w.blank(10)
        w.blank()
    # ---- Figure 4 heat map as a conditionally formatted table
    w.row([_c(ws, bk.ftitle("heatmap") + "  [Excel form: a conditionally formatted table; Excel has no heat-map chart]", BOLD)])
    w.head(["Count failure rate", "card", "mobilemoney", "alternative channels", "bank transfer"])
    h0 = w.r + 1
    for cn in CNT:
        i = w.r + 1
        w.row([_c(ws, cn)] + [_c(ws, f"=IFERROR(SUMIFS({T('Q')},{T('J')},$A{i},{T('E')},{chr(66 + j)}${h0 - 1})/SUMIFS({T('P')},{T('J')},$A{i},{T('E')},{chr(66 + j)}${h0 - 1}),\"\")", fmt=PCT) for j in range(4)])
    ws.conditional_formatting.add(f"B{h0}:E{w.r}", ColorScaleRule(start_type="num", start_value=0, start_color="F3EEE2", end_type="num", end_value=1, end_color="4A6F94"))
    P["heat"] = (h0, w.r)
    w.blank()
    w.head(["Fees on failed transactions (USD)", "card", "mobilemoney", "alternative channels", "bank transfer"])
    for cn in CNT:
        i = w.r + 1
        w.row([_c(ws, cn)] + [_c(ws, f"=SUMIFS({T('W')},{T('J')},$A{i},{T('E')},{chr(66 + j)}${h0 - 1})", fmt=USD) for j in range(4)])
    w.blank()
    # ---- currencies
    cur = res["currencies"].head(8)
    w.row([_c(ws, "By currency (largest eight by fees on failed transactions)", BOLD)])
    w.head(["Currency", "Attempts", "Failed attempts", "Count failure rate", "Fees (USD)", "Failed fees (USD)", "Failed-fee share", "Share of all failed fees"])
    for cc in cur.ccy:
        i = w.r + 1
        k = f"{T('I')},$A{i}"
        w.row([_c(ws, cc, IN_FONT, fill=IN_FILL), _c(ws, f"=SUMIFS({T('P')},{k})", fmt=INT), _c(ws, f"=SUMIFS({T('Q')},{k})", fmt=INT), _c(ws, f"=IFERROR(C{i}/B{i},0)", fmt=PCT),
               _c(ws, f"=SUMIFS({T('T')},{k})", fmt=USD), _c(ws, f"=SUMIFS({T('W')},{k})", fmt=USD), _c(ws, f"=IFERROR(F{i}/E{i},0)", fmt=PCT),
               _c(ws, f"=F{i}/{S['failed_fees']}", fmt=PCT)])
    w.blank()
    # ---- sector (values from Python)
    sec = res["sectors"]
    w.row([_c(ws, "By sector", BOLD)])
    w.pynote("scripts/03_concentration.py", "Sector comes from the customer table's sector label; customers without one are the 'Unlabelled sector' row.")
    w.head(["Sector", "Attempts", "Failed attempts", "Count failure rate", "Fees (USD)", "Failed fees (USD)", "Failed-fee share"])
    s0 = w.r + 1
    for r in sec.itertuples():
        w.row([_c(ws, r.sector), val(ws, int(r.att), INT), val(ws, int(r.f_att), INT), val(ws, float(r.fail_rate), PCT), val(ws, float(r.fee), USD),
               val(ws, float(r.f_fee), USD), val(ws, float(r.fee_share), PCT)])
    i = w.r + 1
    w.row([_c(ws, "Check: sector failed fees less headline", BOLD), None, None, None, None,
           _c(ws, f"=SUM(F{s0}:F{w.r})-{S['failed_fees']}", fmt=USD2), _c(ws, f'=IF(ABS(F{i})<1,"OK","CHECK")', BOLD)])
    P["sector_check"] = f"{w.q}$G${i}"
    w.blank()
    # ---- Table 3 drivers
    w.caption("drivers")
    dr = static_table(bk.root, bk.ctx, "drivers")
    w.text("Fee per failed attempt = fees on failed transactions / failed attempts, both on records with an exchange rate.", note=True)
    w.head(["Cell", "Share of attempts", "Failure rate", "Fee per failed attempt", "Fees on failed transactions", "Dominant driver"])
    d0 = w.r + 1
    cells = [("Kenya", "card"), ("Kenya", "mobilemoney"), ("Uganda", "card"), ("Tanzania", "card"), ("Ghana", "card"), ("Uganda", "mobilemoney")]
    nbq = f"{T('AF')},FALSE"
    for (cn, pt), row in zip(cells, dr[1:7]):
        i = w.r + 1
        q = f'{T("J")},"{cn}",{T("E")},"{pt}",{nbq}'
        w.row([_c(ws, f"{cn} {'mobile money' if pt == 'mobilemoney' else pt}"), _c(ws, f"=SUMIFS({T('P')},{q})/SUMIFS({T('P')},{nbq})", fmt=PCT),
               _c(ws, f"=SUMIFS({T('Q')},{q})/SUMIFS({T('P')},{q})", fmt=PCT),
               _c(ws, f"=SUMIFS({T('W')},{q},{T('N')},TRUE)/SUMIFS({T('Q')},{q},{T('N')},TRUE)", fmt=USD2),
               _c(ws, f"=SUMIFS({T('W')},{q})", fmt=USD), _c(ws, row[-1])])
        P.setdefault("drv", {})[(cn, pt)] = i
    i = w.r + 1
    w.row([_c(ws, "All cells", BOLD), _c(ws, 1, BOLD, PCT), _c(ws, f"=SUMIFS({T('Q')},{nbq})/SUMIFS({T('P')},{nbq})", BOLD, PCT),
           _c(ws, f"=SUMIFS({T('W')},{nbq},{T('N')},TRUE)/SUMIFS({T('Q')},{nbq},{T('N')},TRUE)", BOLD, USD2), _c(ws, f"=SUMIFS({T('W')},{nbq})", BOLD, USD)])
    P["drv_all"] = i
    ch = bubble_chart(ws, bk.ftitle("drivers"), ref(ws, 2, d0, d0 + 5), ref(ws, 3, d0, d0 + 5),
                      ref(ws, 5, d0, d0 + 5), xlog=True, xfmt="0.0%", yfmt="0%", xtitle="Share of non-anomalous attempts (log scale)", ytitle="Count failure rate")
    w.chart(ch, "H", d0 - 2)
    w.blank(12)
    # ---- Figure 5 Pareto
    pa = res["pareto"]
    w.row([_c(ws, bk.ftitle("pareto"), BOLD)])
    w.text("Customers ranked by fees on failed transactions. Cumulative share = fees of the k largest customers / all fees. Helper list from row %d." % 200, note=True)
    w.head(["Rank k", "Share of customers", "Cumulative share (all records)", "Rank k (excl. extreme-volume anomalies)", "Share of customers", "Cumulative share (excl.)"])
    HELP0 = 201
    n_all = len(bk.cust_fail)
    rngA, rngB = f"$B${HELP0}:$B${HELP0 + n_all - 1}", f"$C${HELP0}:$C${HELP0 + n_all - 1}"
    p1 = pa[pa.series == "All records"].reset_index(drop=True)
    p2 = pa[pa.series != "All records"].reset_index(drop=True)
    pr0 = w.r + 1
    for k in range(max(len(p1), len(p2))):
        i = w.r + 1
        row = []
        for p, rng in ((p1, rngA), (p2, rngB)):
            if k < len(p):
                row += [_c(ws, int(p["rank"][k]), IN_FONT, INT, IN_FILL), _c(ws, f'=A{i}/COUNTIF({rng},">0")' if rng == rngA else f'=D{i}/COUNTIF({rng},">0")', fmt="0.00%"),
                        _c(ws, f'=SUMIF({rng},">="&LARGE({rng},{"A" if rng == rngA else "D"}{i}))/SUM({rng})', fmt="0.0%")]
            else:
                row += [None, None, None]
        w.row(row)
    pr1 = w.r
    P["pareto"] = (pr0, pr1)
    P["pareto_rank10"] = pr0 + [int(x) for x in p1["rank"]].index(10)
    top1 = int(res["customer_concentration"]["top1pct_n"])
    P["pareto_top1"] = pr0 + [int(x) for x in p1["rank"]].index(top1)
    w.row([_c(ws, "Customers with failed fees"), _c(ws, f'=COUNTIF({rngA},">0")', fmt=INT)])
    P["n_cust"] = f"{w.q}$B${w.r}"
    w.row([_c(ws, "Customers who transacted"), val(ws, int(res["customer_concentration"]["customers_transacting"]), INT)])
    ch = scatter_chart(ws, bk.ftitle("pareto"), [(ref(ws, 2, pr0, pr1), ref(ws, 3, pr0, pr1), "All records", NAVY),
                       (ref(ws, 5, pr0, pr0 + len(p2) - 1), ref(ws, 6, pr0, pr0 + len(p2) - 1), "Excluding extreme-volume anomalies", SAND)],
                       xlog=True, xfmt="0.0%", yfmt="0%", xtitle="Share of customers (log scale)", ytitle="Cumulative share of failed fees", lines=True)
    w.chart(ch, "H", pr0 - 3)
    w.blank(8)
    # ---- Table 4 quintiles and Figure 7
    w.caption("quintiles")
    w.pynote("scripts/03_concentration.py", "Quintiles of average value per aggregated record need a per-record ranking.")
    qv = res["quintile_versions"]
    names = ["All translatable records", "Excluding extreme-volume anomalies", "Excluding escalation account(s)", "Excluding value anomalies", "All three exclusions"]
    w.head(["Version", "Mobile money Q5 failure", "Mobile money Q1–Q4 failure", "Mobile money Q5 failed fees", "Largest customer's share of Q5 failed fees",
            "Card Q5 failure", "Card Q1–Q4 failure"])
    for nme in names:
        m = qv[(qv.version == nme) & (qv.pt == "mobilemoney")].iloc[0]
        c = qv[(qv.version == nme) & (qv.pt == "card")].iloc[0]
        w.row([_c(ws, nme), val(ws, float(m.q5_fail_rate), PCT), val(ws, float(m.q1_4_fail_rate), PCT), val(ws, float(m.q5_failed_fees), USD),
               val(ws, float(m.q5_largest_customer_share), PCT), val(ws, float(c.q5_fail_rate), PCT), val(ws, float(c.q1_4_fail_rate), PCT)])
    w.blank()
    q = res["quintiles"]
    w.row([_c(ws, "Failure rate by size quintile (value anomalies excluded)", BOLD)])
    w.head(["Quintile", "Card", "Mobile money", "Card attempts", "Mobile money attempts"])
    q0 = w.r + 1
    for k in range(1, 6):
        c, m = q[(q.pt == "card") & (q.quintile == k)].iloc[0], q[(q.pt == "mobilemoney") & (q.quintile == k)].iloc[0]
        w.row([_c(ws, f"Q{k}"), val(ws, float(c.fail_rate), PCT), val(ws, float(m.fail_rate), PCT), val(ws, int(c.att), INT), val(ws, int(m.att), INT)])
    q1 = w.r
    i = w.r + 1
    w.row([_c(ws, "Check: attempts in the quintiles less attempts in the transaction rows", BOLD), None, None,
           _c(ws, f'=SUM(D{q0}:D{q1})-SUMIFS({T("P")},{T("E")},"card",{T("AC")},FALSE,{T("Z")},">0")', fmt=INT),
           _c(ws, f'=SUM(E{q0}:E{q1})-SUMIFS({T("P")},{T("E")},"mobilemoney",{T("AC")},FALSE,{T("Z")},">0")', fmt=INT), _c(ws, f'=IF(AND(D{i}=0,E{i}=0),"OK","CHECK")', BOLD)])
    P["q_check"] = f"{w.q}$F${i}"
    ch = bar_chart(ws, bk.ftitle("quintiles"), ref(ws, 1, q0, q1), [(ref(ws, 2, q0, q1), "Card", SAND), (ref(ws, 3, q0, q1), "Mobile money", NAVY)], yfmt="0%", labels=True)
    w.chart(ch, "H", q0 - 4)
    w.pad_to(HELP0 - 3)
    # ---- helper list for the Pareto (bottom of the sheet)
    w.row([_c(ws, "Helper: fees on failed transactions by customer (customers with failed fees)", BOLD)])
    w.head(["Customer id", "All records", "Excluding extreme-volume anomalies"])
    assert w.r == HELP0 - 1, (w.r, HELP0)
    for k, cid in enumerate(bk.cust_fail):
        i = HELP0 + k
        w.row([_c(ws, int(cid), IN_FONT, fill=IN_FILL), _c(ws, f"=SUMIFS({T('W')},{T('B')},A{i})", fmt=USD), _c(ws, f"=SUMIFS({T('W')},{T('B')},A{i},{T('AF')},FALSE)", fmt=USD)])
    return P


# ============================================================================================ 04 Diagnostics
def build_diag(bk) -> dict:
    res, T, S = bk.res, bk.tx, bk.S
    w = Wr(bk, "04_Diagnostics", [40, 16, 16, 16, 16, 16, 16, 16, 18])
    ws = w.ws
    P = {}
    an = res["anomalies"]
    w.title("04_Diagnostics. Failure diagnostics")
    w.text("The data has no failure codes, so this sheet classifies patterns rather than causes. 04_Laney holds the control charts.", note=True)
    w.blank()
    # ---- Table 5
    w.caption("anomalies")
    w.pynote("scripts/04_diagnostics.py", "Largest extreme-volume anomaly observations; the rule itself runs in 01G_Anomaly_Rules.")
    obs = an["observations"]
    w.head(["Account", "Market", "Channel", "Month", "Failed attempts", "Successes", "Prior six-month median", "Fees on failed transactions"])
    o0 = w.r + 1
    for r in obs.head(5).itertuples():
        w.row([val(ws, int(r.customer_id)), val(ws, r.country), val(ws, r.pt), val(ws, r.period.to_pydatetime(), "mmm yyyy"), val(ws, int(r.f_att), INT), val(ws, int(r.s_att), INT),
               val(ws, float(r.prior_med), "0.0"), val(ws, float(r.f_fee), USD)])
    rest = obs.iloc[5:]
    w.row([val(ws, f"Other {len(rest)} observations"), None, None, None, val(ws, int(rest.f_att.sum()), INT), None, None, val(ws, float(rest.f_fee.sum()), USD)])
    o1 = w.r
    i = w.r + 1
    w.row([_c(ws, "Check: observations and fees against the rule grid", BOLD), None, None, None, None, None,
           _c(ws, f"=COUNTIF({bk.an['ext']},TRUE)-{len(obs)}", fmt=INT), _c(ws, f"=SUM(H{o0}:H{o1})-SUMIFS({T('W')},{T('AF')},TRUE)", fmt=USD2)])
    w.row([None, None, None, None, None, None, _c(ws, f'=IF(AND(G{i}=0,ABS(H{i})<1),"OK","CHECK")', BOLD)])
    P["anom_check"] = f"{w.q}$G${i + 1}"
    w.blank()
    sens = an["sensitivity"].set_index("thresholds")
    w.row([_c(ws, "Sensitivity of the anomaly share to the thresholds", BOLD)])
    w.head(["Thresholds", "Observations", "Customers", "Fees on failed transactions", "Share of failed fees"])
    for nm in ["loose", "agreed", "strict"]:
        i = w.r + 1
        if nm == "agreed":
            w.row([_c(ws, "agreed (formulas)"), _c(ws, f"=COUNTIF({bk.an['ext']},TRUE)", fmt=INT), val(ws, int(sens.customers[nm]), INT),
                   _c(ws, f"=SUMIFS({T('W')},{T('AF')},TRUE)", fmt=USD), _c(ws, f"=D{i}/{S['failed_fees']}", fmt=PCT)])
        else:
            w.row([val(ws, f"{nm} (values from scripts/04_diagnostics.py)"), val(ws, int(sens.observations[nm]), INT), val(ws, int(sens.customers[nm]), INT),
                   val(ws, float(sens.f_fee[nm]), USD), val(ws, float(sens.share[nm]), PCT)])
    w.blank()
    # ---- Figure 8 escalation series
    esc = int(bk.prep.stats["escalation_customers"][0])
    w.row([_c(ws, bk.ftitle("escalation"), BOLD)])
    w.row([_c(ws, "Escalation account"), _c(ws, esc, IN_FONT, fill=IN_FILL)])
    ea = f"$B${w.r}"
    w.head(["Month", "Failed attempts", "Successful attempts", "Fees on failed transactions"])
    e0 = w.r + 1
    for p in bk.periods[-7:]:
        i = w.r + 1
        m = f"{T('B')},{ea},{T('A')},$A{i}"
        w.row([_c(ws, p.to_pydatetime(), fmt="mmm yyyy"), _c(ws, f"=SUMIFS({T('Q')},{m})", fmt=INT), _c(ws, f"=SUMIFS({T('R')},{m})", fmt=INT), _c(ws, f"=SUMIFS({T('W')},{m})", fmt=USD)])
    e1 = w.r
    P["esc_last"] = f"{w.q}$B${e1}"
    ch = bar_chart(ws, bk.ftitle("escalation") + " [failed attempts]", ref(ws, 1, e0, e1), [(ref(ws, 2, e0, e1), "Failed attempts", NAVY)], labels=True, legend=False, h=8)
    w.chart(ch, "G", e0 - 2)
    w.blank(8)
    # ---- Table 6 hard / mixed
    hm = res["hard_mixed"]
    w.caption("hardmixed")
    w.pynote("scripts/04_diagnostics.py", "Hard = a customer-month-channel with failures and no successes; mixed = both.")
    w.head(["Classification", "Customer-month-channels", "Failed attempts", "Share", "Fees on failed transactions", "Share"])
    h0 = w.r + 1
    for cls in ["Extreme-volume anomaly", "Hard", "Mixed"]:
        r = hm["totals"].set_index("class").loc[cls]
        w.row([_c(ws, {"Hard": "Hard: no successes that month", "Mixed": "Mixed: successes and failures"}.get(cls, cls)), val(ws, int(r.observations), INT), val(ws, int(r.f_att), INT),
               val(ws, float(r.share_f_att), PCT), val(ws, float(r.f_fee), USD), val(ws, float(r.share_f_fee), PCT)])
    i = w.r + 1
    w.row([_c(ws, "Check: classes less headline fees on failed transactions", BOLD), None, None, None, _c(ws, f"=SUM(E{h0}:E{w.r})-{S['failed_fees']}", fmt=USD2), _c(ws, f'=IF(ABS(E{i})<1,"OK","CHECK")', BOLD)])
    P["hm_check"] = f"{w.q}$F${i}"
    w.blank()
    bc = hm["by_channel"]
    bc = bc[bc.pt.isin(["card", "mobilemoney", "alternative channels"])]
    w.head(["Channel", "Hard", "Mixed", "Hard share", "Extreme-volume anomalies (shown separately)"])
    b0 = w.r + 1
    for r in bc.itertuples():
        w.row([_c(ws, {"card": "Card", "mobilemoney": "Mobile money", "alternative channels": "Alternative channels"}[r.pt]), val(ws, float(r.Hard), USD), val(ws, float(r.Mixed), USD),
               val(ws, float(r.hard_share), PCT), val(ws, float(r.anomalies), USD)])
    b1 = w.r
    ch = bar_chart(ws, bk.ftitle("hard_mixed"), ref(ws, 1, b0, b1), [(ref(ws, 2, b0, b1), "Hard (no successes that month)", NAVY), (ref(ws, 3, b0, b1), "Mixed", SKY)],
                   horizontal=True, stacked=True, yfmt="$#,##0", h=8)
    w.chart(ch, "G", b0 - 8)
    w.blank(4)
    # ---- persistence, tenure, lapse (values)
    cu = res["customers"]
    pe, la = cu["persistence"], cu["lapse"]
    w.row([_c(ws, "Persistent customers and lapse", BOLD)])
    w.pynote("scripts/04_diagnostics.py", "Needs a customer × month table.")
    w.head(["Measure", "Persistent", "Other eligible"])
    w.row([_c(ws, "Customers with at least six active months"), val(ws, int(pe["persistent"]), INT), val(ws, int(pe["eligible"] - pe["persistent"]), INT)])
    w.row([_c(ws, "Failed-fee share"), val(ws, float(pe["fee_share_persistent"]), PCT), val(ws, float(pe["fee_share_other"]), PCT)])
    w.row([_c(ws, "End-period lapse rate"), val(ws, float(pe["lapse_persistent"]), PCT), val(ws, float(pe["lapse_other"]), PCT)])
    w.row([_c(ws, "Persistent customers' share of failed attempts / failed fees (non-anomalous)"), val(ws, float(pe["share_f_att"]), PCT), val(ws, float(pe["share_f_fee"]), PCT)])
    w.blank()
    w.caption("tenure")
    w.pynote("scripts/04_diagnostics.py", "Tenure = months between sign-up and the month of attempt.")
    w.head(["Tenure", "Attempts", "Failed attempts", "Count failure rate", "Fees (USD)", "Failed fees (USD)", "Failed-fee share", "Share of failed fees"])
    t0 = w.r + 1
    for r in cu["tenure"].itertuples():
        w.row([_c(ws, str(r.band)), val(ws, int(r.att), INT), val(ws, int(r.f_att), INT), val(ws, float(r.fail_rate), PCT), val(ws, float(r.fee), USD), val(ws, float(r.f_fee), USD),
               val(ws, float(r.fee_share), PCT), val(ws, float(r.share_of_failed_fees), PCT)])
    i = w.r + 1
    w.row([_c(ws, "Check: tenure failed fees less non-anomalous failed fees (differences are records with no sign-up date)", BOLD), None, None, None, None,
           _c(ws, f"=SUM(F{t0}:F{w.r})-SUMIFS({T('W')},{T('AF')},FALSE)", fmt=USD2)])
    P["tenure_diff"] = f"{w.q}$F${i}"
    w.blank()
    w.row([_c(ws, f"Lapse: {int(la['lapsed']):,} of {int(la['active_before']):,} customers active before February 2024 made no attempts in February–April 2024 ({la['lapse_rate']:.0%}). Values from Python."), None], )
    w.blank()
    # ---- Table 8 Laney flags (formulas linking to 04_Laney)
    w.caption("laney")
    w.head(["Cell", "Eligible months", "Median monthly failure", "First 6 months", "Last 6 months", "Flags", "Months above the control limit"])
    pat = res["laney"]["patterns"]
    for r in pat.itertuples():
        li = bk.L[(r.country, r.pt)]
        Lq = "'04_Laney'!"
        flags = '&'.join([f'IF({Lq}{c}{li},"{n}, ","")' for c, n in zip("LMNO", ["Structural", "Deteriorating", "Episodic", "Unstable"])])
        w.row([_c(ws, f"{r.country} {'mobile money' if r.pt == 'mobilemoney' else r.pt}"), _c(ws, f"={Lq}C{li}", LINK_FONT, INT), _c(ws, f"={Lq}G{li}", LINK_FONT, PCT),
               _c(ws, f"={Lq}H{li}", LINK_FONT, PCT), _c(ws, f"={Lq}I{li}", LINK_FONT, PCT),
               _c(ws, f'=IF({Lq}P{li},"Stable",LEFT({flags},LEN({flags})-2))', LINK_FONT), _c(ws, f"={Lq}K{li}", LINK_FONT, INT)])
    P["laney_end"] = w.r
    return P


# ============================================================================================ 08 Recommendations
def build_recs(bk) -> dict:
    res, T = bk.res, bk.tx
    w = Wr(bk, "08_Recommendations", [34, 14, 18, 16, 16, 18, 26, 16, 34, 26])
    ws = w.ws
    P = {}
    w.title("08_Recommendations. Management recommendations")
    w.text("The matrix sets transparent criteria side by side rather than combining them into a weighted score.", note=True)
    w.blank()
    w.caption("matrix")
    w.pynote("scripts/08_recommendations.py", "Internal potential uses each cell's own best three-month rate; the persistence and confidence columns come from the control charts.")
    m = res["matrix"]
    w.head(["Cell", "Failure rate", "Fees on failed transactions", "Failed value", "Internal potential", "Cross-channel potential", "Persistence", "Data confidence",
            "Diagnostic confidence", "Action"])
    m0 = w.r + 1
    for r in m.itertuples():
        w.row([val(ws, f"{r.country} {'mobile money' if r.pt == 'mobilemoney' else r.pt}"), val(ws, float(r.fail_rate), PCT), val(ws, float(r.f_fee), USD), val(ws, float(r.failed_value), USD),
               val(ws, float(r.internal_potential), USD), val(ws, None if pd.isna(r.cross_channel_potential) else float(r.cross_channel_potential), USD),
               val(ws, r.persistence), val(ws, r.data_confidence), val(ws, r.diagnostic_confidence), val(ws, r.action)])
    m1 = w.r
    i = w.r + 1
    w.row([_c(ws, "Check: matrix failed fees less non-anomalous fees on failed transactions in the same cells", BOLD), None,
           _c(ws, f"=SUM(C{m0}:C{m1})-SUMIFS({T('W')},{T('AF')},FALSE)", fmt=USD2), None, None, None, None, None, None, _c(ws, f'=IF(ABS(C{i})<=0.001*SUM(C{m0}:C{m1}),"OK","CHECK (cells under $1,000 are not listed)")', BOLD)])
    P["matrix_check"] = f"{w.q}$J${i}"
    # Figure 15 scatter by action
    w.blank()
    w.row([_c(ws, bk.ftitle("matrix") + "  [Excel form: scatter; bubble sizes are not drawn]", BOLD)])
    acts = [("Prioritise", NAVY), ("Investigate root cause", AMBER), ("Contain escalation account", TEAL), ("Monitor", SAND)]
    series = []
    w.head(["Action", "Fees on failed transactions", "Failure rate"])
    for act, col in acts:
        d = m[m.action == act]
        if d.empty:
            continue
        a0 = w.r + 1
        for r in d.itertuples():
            w.row([val(ws, f"{act}: {r.country} {r.pt}"), val(ws, float(r.f_fee), USD), val(ws, float(r.fail_rate), PCT)])
        series.append((ref(ws, 2, a0, w.r), ref(ws, 3, a0, w.r), act, col))
    ch = scatter_chart(ws, bk.ftitle("matrix"), series, xlog=True, xfmt="$#,##0", yfmt="0%", xtitle="Non-anomalous fees on failed transactions (log scale)", ytitle="Count failure rate")
    w.chart(ch, "E", w.r - len(m) - 12)
    w.blank(14)
    for slug, hdr in [("actions", None), ("triggers", None)]:
        w.caption(slug)
        rows = static_table(bk.root, bk.ctx, slug)
        w.head(rows[0])
        for r in rows[1:]:
            w.row([_c(ws, x) for x in r])
        w.blank()
    w.row([_c(ws, bk.ftitle("roadmap") + "  [Excel form: a table]", BOLD)])
    from .figures import fig25_roadmap
    f = fig25_roadmap(res)
    hdr = list(f.data[0].header.values)
    cells = [list(c) for c in f.data[0].cells.values]
    w.head(hdr)
    for k in range(len(cells[0])):
        w.row([_c(ws, cells[j][k]) for j in range(len(cells))])
    return P


# ============================================================================================ 01E Data quality
def build_dq(bk) -> dict:
    res, T, S, st = bk.res, bk.tx, bk.S, bk.prep.stats
    w = Wr(bk, "01E_Data_Quality", [44, 18, 18, 18, 18, 30])
    ws = w.ws
    P = {}
    rec = res["reconciliation"]
    w.title("01E_Data_Quality. Appendix A and B: data and methodology")
    w.text("Formulas read the transaction rows (01G) and the rate tables (01F). Rows marked as values come from the Python run that switches the SLL fix off (scripts/01E_data_quality.py).", note=True)
    w.blank()
    w.caption("populations")
    w.head(["Population", "Records", "Attempts", "Used for"])
    w.row([_c(ws, "All records"), _c(ws, f"={S['records']}", LINK_FONT, INT), _c(ws, f"={S['attempts']}", LINK_FONT, INT), _c(ws, "Every count measure")])
    w.row([_c(ws, "Translatable records"), _c(ws, f"={S['records_translatable']}", LINK_FONT, INT), _c(ws, f"={S['attempts_translatable']}", LINK_FONT, INT), _c(ws, "Every dollar measure")])
    w.row([_c(ws, "Records without an exchange rate"), _c(ws, f"={S['untranslatable']}", LINK_FONT, INT), _c(ws, f"={S['attempts']}-{S['attempts_translatable']}", fmt=INT), _c(ws, "Counts only")])
    w.blank()
    w.caption("flags")
    w.head(["Flag", "Records", "Value (USD)", "Rule"])
    w.row([_c(ws, "Fee-ratio anomaly"), _c(ws, f"={S['flag_fee_ratio']}", LINK_FONT, INT), None, _c(ws, "Fee below 0.5% or above 20% of transaction value")])
    w.row([_c(ws, "Missing fee"), _c(ws, f"={S['flag_missing_fee']}", LINK_FONT, INT), None, _c(ws, "No fee recorded: zero in fee sums, kept in counts")])
    w.row([_c(ws, "Transaction-value anomaly"), _c(ws, f"={S['flag_value']}", LINK_FONT, INT), _c(ws, f"={S['flag_value_usd']}", LINK_FONT, USD), _c(ws, "Value above the per-attempt limit, or zero or negative")])
    w.row([_c(ws, "Reported value of translatable records"), None, _c(ws, f"=SUMIFS({T('Z')},{T('N')},TRUE)", fmt=USD)])
    w.row([_c(ws, "Records where the fee exceeds the value"), _c(ws, f'=SUMPRODUCT(ISNUMBER({T("H")})*({T("G")}>0)*({T("H")}>{T("G")}))', fmt=INT)])
    w.blank()
    # untranslatable by currency
    un = res["stats"]
    tx = bk.prep.tx
    unt = tx[~tx.fx_ok].groupby("ccy").att.sum().sort_values(ascending=False)
    w.row([_c(ws, "Records without an exchange rate, by currency code", BOLD)])
    w.head(["Currency", "Records", "Attempts"])
    u0 = w.r + 1
    for cc in unt.index:
        i = w.r + 1
        w.row([_c(ws, cc, IN_FONT, fill=IN_FILL), _c(ws, f'=COUNTIFS({T("I")},A{i},{T("N")},FALSE)', fmt=INT), _c(ws, f'=SUMIFS({T("P")},{T("I")},A{i},{T("N")},FALSE)', fmt=INT)])
    i = w.r + 1
    w.row([_c(ws, "Total (check against the table above)", BOLD), _c(ws, f"=SUM(B{u0}:B{w.r})", BOLD, INT), _c(ws, f"=SUM(C{u0}:C{w.r})", BOLD, INT),
           _c(ws, f'=IF(B{i}={S["untranslatable"]},"OK","CHECK")', BOLD)])
    P["untr_check"] = f"{w.q}$D${i}"
    w.blank()
    # rate screens from 01F
    R = lambda c: f"'01F_Rates'!${c}${bk.rd_first}:${c}${bk.rd_last}"
    w.row([_c(ws, "Exchange-rate corrections (counted in the 01F_Rates daily table)", BOLD)])
    w.row([_c(ws, "Non-positive daily rates dropped"), _c(ws, f"=COUNTIF({R('F')},FALSE)", fmt=INT)])
    w.row([_c(ws, "SLL days restated (divided by 1,000)"), _c(ws, f'=COUNTIFS({R("C")},"SLL",{R("E")},">"&{bk.A["fix_thr"]})', fmt=INT)])
    w.row([_c(ws, "Spike days dropped"), _c(ws, f"=COUNTIF({R('K')},TRUE)", fmt=INT)])
    sp = [c for c in st["spike_currencies"]]
    for cc in sp:
        i = w.r + 1
        w.row([_c(ws, f"   of which {cc}"), _c(ws, f'=COUNTIFS({R("C")},"{cc}",{R("K")},TRUE)', fmt=INT)])
    P["spike_total"] = f"{w.q}$B${w.r - len(sp)}"
    w.blank()
    w.row([_c(ws, "Sierra Leone leone: monthly average of the daily rate, raw and restated (USD per SLL)", BOLD)])
    w.head(["Month", "Raw series", "Restated"])
    for p in bk.periods:
        i = w.r + 1
        w.row([_c(ws, p.to_pydatetime(), fmt="mmm yyyy"), _c(ws, f'=IFERROR(AVERAGEIFS({R("E")},{R("C")},"SLL",{R("D")},$A{i},{R("F")},TRUE),"")', fmt="0.00000000"),
               _c(ws, f'=IFERROR(AVERAGEIFS({R("G")},{R("C")},"SLL",{R("D")},$A{i},{R("F")},TRUE),"")', fmt="0.00000000")])
    w.blank()
    w.row([_c(ws, "Legacy currency codes mapped (records in the supplied data)", BOLD)])
    w.head(["Code in data", "Maps to", "Records"])
    for old, new in bk.cfg["data"]["currency_aliases"].items():
        i = w.r + 1
        w.row([_c(ws, old, IN_FONT, fill=IN_FILL), _c(ws, new), _c(ws, f"=COUNTIF('01B_Raw_Transactions'!$C$2:$C${bk.tx_last},A{i})", fmt=INT)])
    w.blank()
    # Table 21 reconciliation
    w.caption("brief")
    w.head(["Measure", "Brief (as quoted)", "Recalculated", "Before SLL correction (values)", "Population", "Status"])
    b, a = rec["no_sll_fix"], rec["report_basis"]
    jan = f"'02_Scale'!"
    mrow0 = bk.mrow0
    ws_row = lambda s: s
    jn = f"{T('A')},{bk.A['jan_t']}"
    w.row([_c(ws, "Transaction attempts"), _c(ws, "1.65M", IN_FONT, fill=IN_FILL), _c(ws, f"={S['attempts']}", LINK_FONT, INT), None, _c(ws, "All records"), _c(ws, "Reconciles")])
    w.row([_c(ws, "Failed attempts"), _c(ws, "1.02M (62%)", IN_FONT, fill=IN_FILL), _c(ws, f"={S['failed']}", LINK_FONT, INT), None, _c(ws, "All records"), _c(ws, "Reconciles")])
    w.row([_c(ws, "Count failure rate"), _c(ws, "62%", IN_FONT, fill=IN_FILL), _c(ws, f"={S['count_rate']}", LINK_FONT, PCT), val(ws, float(b["count_rate"]), PCT), _c(ws, "All records"), _c(ws, "Reconciles")])
    w.row([_c(ws, "Recorded fee revenue"), _c(ws, "$3.15M", IN_FONT, fill=IN_FILL), _c(ws, f"={S['fees']}", LINK_FONT, USD), val(ws, float(b["fees"]), USD), _c(ws, "Translatable"), _c(ws, "Brief includes the SLL error")])
    ffr = w.r + 1
    w.row([_c(ws, "Fees on failed transactions"), _c(ws, "$2.85M (90%)", IN_FONT, fill=IN_FILL), _c(ws, f"={S['failed_fees']}", LINK_FONT, USD), val(ws, float(b["failed_fees"]), USD), _c(ws, "Translatable"), _c(ws, "Brief includes the SLL error")])
    w.row([_c(ws, "Failed-fee share"), _c(ws, "90%", IN_FONT, fill=IN_FILL), _c(ws, f"={S['fee_share']}", LINK_FONT, PCT), val(ws, float(b["fee_share"]), PCT), _c(ws, "Translatable"), _c(ws, "")])
    w.row([_c(ws, "January 2024 failure rate by count"), _c(ws, "97%", IN_FONT, fill=IN_FILL), _c(ws, f"=SUMIFS({T('Q')},{jn})/SUMIFS({T('P')},{jn})", fmt=PCT), val(ws, float(b["jan_count_rate"]), PCT), _c(ws, "All records"), _c(ws, "Brief reports the failed-fee share")])
    w.row([_c(ws, "January 2024 failed-fee share"), _c(ws, "97%", IN_FONT, fill=IN_FILL), _c(ws, f"=SUMIFS({T('W')},{jn})/SUMIFS({T('T')},{jn})", fmt=PCT), val(ws, float(b["jan_fee_share"]), PCT), _c(ws, "Translatable"), _c(ws, "")])
    w.row([_c(ws, "January 2024 failed fees"), _c(ws, "Over $745K", IN_FONT, fill=IN_FILL), _c(ws, f"=SUMIFS({T('W')},{jn})", fmt=USD), val(ws, float(b["jan_failed_fees"]), USD), _c(ws, "Translatable"), _c(ws, "Overstated")])
    w.row([_c(ws, "Months with a failed-fee share below 78%"), _c(ws, "None", IN_FONT, fill=IN_FILL), _c(ws, f"=COUNTIF('02_Scale'!$F${bk.mrow0}:$F${bk.mrow0 + bk.nm - 1},\"<0.78\")", fmt=INT),
           val(ws, len(b["months_below_78"]), INT), _c(ws, "Translatable"), _c(ws, "Holds only before the correction")])
    for pt, br in [("card", "94%"), ("mobilemoney", "77%"), ("bank transfer", "3%")]:
        w.row([_c(ws, f"Failed-fee share: {pt}"), _c(ws, br, IN_FONT, fill=IN_FILL), _c(ws, f'=SUMIFS({T("W")},{T("E")},"{pt}")/SUMIFS({T("T")},{T("E")},"{pt}")', fmt=PCT), None, _c(ws, "Translatable"), _c(ws, "Reconciles")])
    w.row([_c(ws, "Bank transfer share of attempts"), _c(ws, "2%", IN_FONT, fill=IN_FILL), _c(ws, f'=SUMIFS({T("P")},{T("E")},"bank transfer")/{S["attempts"]}', fmt=PCT), None, _c(ws, "All records"), _c(ws, "Brief counts records")])
    w.row([_c(ws, "Bank transfer share of records"), None, _c(ws, f'=COUNTIF({T("E")},"bank transfer")/{S["records"]}', fmt=PCT), None, _c(ws, "All records"), _c(ws, "")])
    w.row([_c(ws, "Kenya failed-fee share"), _c(ws, "93%", IN_FONT, fill=IN_FILL), _c(ws, f'=SUMIFS({T("W")},{T("J")},"Kenya")/SUMIFS({T("T")},{T("J")},"Kenya")', fmt=PCT), None, _c(ws, "Translatable"), _c(ws, "Reconciles")])
    w.row([_c(ws, "Failed fees removed by the SLL correction"), None, _c(ws, f"=D{ffr}-C{ffr}", fmt=USD), None, None, _c(ws, "Brief basis less report basis")])
    w.blank()
    # Table 23 sensitivity
    w.caption("sensitivity")
    w.head(["Treatment", "Fees on failed transactions", "Failed-fee share", "Count failure rate"])
    s0 = w.r + 1
    w.row([_c(ws, "Report basis (SLL corrected, monthly-average rates)"), _c(ws, f"={S['failed_fees']}", LINK_FONT, USD), _c(ws, f"={S['fee_share']}", LINK_FONT, PCT), _c(ws, f"={S['count_rate']}", LINK_FONT, PCT)])
    w.row([val(ws, "Before the SLL correction (as in the brief; values from scripts/01E_data_quality.py)"), val(ws, float(b["failed_fees"]), USD), val(ws, float(b["fee_share"]), PCT), val(ws, float(b["count_rate"]), PCT)])
    w.row([_c(ws, "Alternative: value-anomaly and untranslatable records also excluded from fees"), _c(ws, f"=SUMIFS({T('W')},{T('AC')},FALSE)", fmt=USD),
           _c(ws, f"=SUMIFS({T('W')},{T('AC')},FALSE)/SUMIFS({T('T')},{T('AC')},FALSE)", fmt=PCT), _c(ws, f"=SUMIFS({T('Q')},{T('AC')},FALSE)/SUMIFS({T('P')},{T('AC')},FALSE)", fmt=PCT)])
    w.row([_c(ws, "Month-end rates"), _c(ws, f"=SUM({T('Y')})", fmt=USD), _c(ws, f"=SUM({T('Y')})/SUM({T('V')})", fmt=PCT), _c(ws, f"={S['count_rate']}", fmt=PCT)])
    w.row([_c(ws, "2022 constant currency"), _c(ws, f"=SUM({T('X')})", fmt=USD), _c(ws, f"=SUM({T('X')})/SUM({T('U')})", fmt=PCT), _c(ws, f"={S['count_rate']}", fmt=PCT)])
    w.row([_c(ws, "Excluding extreme-volume anomalies"), _c(ws, f"=SUMIFS({T('W')},{T('AF')},FALSE)", fmt=USD), _c(ws, f"=SUMIFS({T('W')},{T('AF')},FALSE)/SUMIFS({T('T')},{T('AF')},FALSE)", fmt=PCT),
           _c(ws, f"=SUMIFS({T('Q')},{T('AF')},FALSE)/SUMIFS({T('P')},{T('AF')},FALSE)", fmt=PCT)])
    w.row([_c(ws, "Also excluding the escalation account"), _c(ws, f'=SUMIFS({T("W")},{T("AG")},"Remaining")', fmt=USD), _c(ws, f'=SUMIFS({T("W")},{T("AG")},"Remaining")/SUMIFS({T("T")},{T("AG")},"Remaining")', fmt=PCT),
           _c(ws, f'=SUMIFS({T("Q")},{T("AG")},"Remaining")/SUMIFS({T("P")},{T("AG")},"Remaining")', fmt=PCT)])
    P["sens_first"] = s0
    return P


# ============================================================================================ charts on existing sheets
def charts_scale(bk, rows: dict) -> None:
    ws = bk.sheet("02_Scale")
    m0, m1 = rows["month"]
    c1 = line_chart(ws, bk.ftitle("trend") + " [count failure rate]", ref(ws, 1, m0, m1), [(ref(ws, 4, m0, m1), "All records", SAND), (ref(ws, 5, m0, m1), "Excluding extreme-volume anomalies and the escalation account", NAVY)], yfmt="0%")
    ws.add_chart(c1, "L4")
    c2 = line_chart(ws, bk.ftitle("trend") + " [failed-fee share]", ref(ws, 1, m0, m1), [(ref(ws, 6, m0, m1), "All records", SAND), (ref(ws, 7, m0, m1), "Excluding extreme-volume anomalies and the escalation account", NAVY)], yfmt="0%")
    ws.add_chart(c2, "L24")
    c3 = bar_chart(ws, bk.ftitle("composition"), ref(ws, 1, m0, m1), [(ref(ws, 10, m0, m1), "Remaining", SAND), (ref(ws, 9, m0, m1), "Escalation account(s)", SKY), (ref(ws, 8, m0, m1), "Extreme-volume anomalies", NAVY)],
                   stacked=True, yfmt="$#,##0")
    ws.add_chart(c3, "L44")
    b0 = rows["wf"]
    c4 = bar_chart(ws, bk.ftitle("bridge"), ref(ws, 1, b0, b0 + 3), [(ref(ws, 2, b0, b0 + 3), "Base", None), (ref(ws, 3, b0, b0 + 3), "Fees on failed transactions", NAVY)],
                   yfmt="$#,##0", stacked=True, point_colors=[NAVY, AMBER, AMBER, NAVY], labels=True, legend=False, note="Excel form of the waterfall: stacked columns with an invisible base")
    ws.add_chart(c4, "L64")
    v0 = rows["value"]
    c5 = bar_chart(ws, bk.ftitle("value") + " [average value per attempt]", ref(ws, 1, v0, v0 + 1), [(ref(ws, 2, v0, v0 + 1), "USD per attempt", NAVY)], point_colors=[NAVY, SAND], labels=True, legend=False, yfmt="$#,##0", h=8)
    ws.add_chart(c5, "L84")


def charts_jan(bk, comp_first: int, n_comp: int) -> None:
    ws = bk.sheet("05_January")
    wf = bk.jan_wf
    c = bar_chart(ws, bk.ftitle("january"), ref(ws, 1, wf, wf + n_comp - 1),
                  [(ref(ws, 2, wf, wf + n_comp - 1), "Base", None), (ref(ws, 3, wf, wf + n_comp - 1), "Amount", NAVY)], yfmt="$#,##0", stacked=True, point_colors=bk.jan_colors, labels=True, legend=False, note="Excel form of the waterfall: stacked columns with an invisible base; red raises, green lowers failed fees")
    ws.add_chart(c, "L4")
    c2 = bar_chart(ws, bk.ftitle("lmdi"), ref(ws, 1, comp_first + 2, comp_first + 7), [(ref(ws, 2, comp_first + 2, comp_first + 7), "Effect on failed fees", NAVY)], horizontal=True, yfmt="$#,##0",
                   point_colors=bk.lmdi_colors, labels=True, legend=False, h=8)
    ws.add_chart(c2, "L26")


def charts_fx(bk, by_ccy: tuple[int, int], meas: tuple[int, int], screen: tuple[int, int]) -> None:
    ws = bk.sheet("06_FX")
    a, b = by_ccy
    c = bar_chart(ws, bk.ftitle("fx_currency"), ref(ws, 1, a, b), [(ref(ws, 4, a, b), "Reported less 2022-constant-currency fees", NAVY)], horizontal=True, yfmt="$#,##0", labels=True, legend=False,
                  point_colors=[NAVY] + [SAND] * (b - a))
    ws.add_chart(c, "H4")
    m0, m1 = meas
    c2 = bar_chart(ws, "Reported against 2022 constant-currency fees [dashboard " + label("reported_constant") + "]", ref(ws, 1, m0, m1),
                   [(ref(ws, 2, m0, m1), "Reported", NAVY), (ref(ws, 3, m0, m1), "2022 constant currency", SAND)], yfmt="$#,##0", labels=True)
    ws.add_chart(c2, "H24")
    s0, s1 = screen
    c3 = bar_chart(ws, bk.ftitle("ias_screen"), ref(ws, 1, s0, s1), [(ref(ws, 3, s0, s1), "Months above the 10% screen", NAVY)], horizontal=True, labels=True, legend=False, h=8)
    ws.add_chart(c3, "H42")


def charts_rec(bk, mk: tuple[int, int], sc: tuple[int, int], cost: tuple[int, int]) -> None:
    ws = bk.sheet("07_Recovery")
    a, b = mk
    c = bar_chart(ws, bk.ftitle("recovery_market"), ref(ws, 1, a, b), [(ref(ws, 18, a, b), "Base-case incremental fees", NAVY)], horizontal=True, yfmt="$#,##0", labels=True, legend=False)
    ws.add_chart(c, "T4")
    s0, s1 = sc
    c2 = bar_chart(ws, bk.ftitle("scenarios") + " [additional successful payments]", ref(ws, 1, s0, s1), [(ref(ws, 2, s0, s1), "Additional successes", NAVY)], labels=True, legend=False,
                   point_colors=[SAND, NAVY, SAND], h=8)
    ws.add_chart(c2, "T24")
    c3 = bar_chart(ws, bk.ftitle("scenarios") + " [incremental fees, 28 months and annual run-rate]", ref(ws, 1, s0, s1), [(ref(ws, 3, s0, s1), "Incremental fees, 28 months", NAVY), (ref(ws, 4, s0, s1), "Annual run-rate", SAND)],
                   yfmt="$#,##0", labels=True, h=8)
    ws.add_chart(c3, "T42")
    k0, k1 = cost
    c4 = bar_chart(ws, bk.ftitle("costs"), ref(ws, 1, k0, k1), [(ref(ws, 2, k0, k1), "Fee revenue remaining", NAVY)], yfmt="$#,##0", labels=True, legend=False, h=8)
    ws.add_chart(c4, "T60")
