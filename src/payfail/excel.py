"""Build the Excel version of the analysis, with live formulas.

The workbook starts from the raw supplied data and reproduces, in formulas:
rate cleaning (SLL restatement, spike screen, duplicate-day weighting), monthly average,
month-end and 2022 constant-currency rates, USD translation of every record, the three data
flags, the anomaly rules, the exposure bridge, monthly and channel/market summaries, the
January LMDI decomposition, Laney p' charts, the recovery scenarios and the FX analysis.
A Checks sheet compares each headline cell with the Python pipeline.

One input is supplied as values rather than formulas, for speed: the customer x payment type x
month attempt grid on the Anomaly_Rules sheet (a pivot of Transactions). Each row carries a
SUMIFS reconciliation back to Transactions.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter as L

from .data import load_raw

FONT = "Arial"
H_FONT = Font(name=FONT, bold=True, color="FFFFFF")
H_FILL = PatternFill("solid", fgColor="2A6FDB")
T_FONT = Font(name=FONT, bold=True, size=13)
IN_FONT = Font(name=FONT, color="0000FF")
IN_FILL = PatternFill("solid", fgColor="FFFF00")
LINK_FONT = Font(name=FONT, color="008000")
B_FONT = Font(name=FONT)
BOLD = Font(name=FONT, bold=True)
NOTE = Font(name=FONT, italic=True, color="6B6B6B", size=9)
USD, USD2, PCT, INT, DATE, RATE = '$#,##0;($#,##0);-', '$#,##0.00;($#,##0.00);-', '0.0%;(0.0%);-', '#,##0;(#,##0);-', "mmm yyyy", "0.000000"


def _c(ws, v, font=B_FONT, fmt=None, fill=None):
    c = WriteOnlyCell(ws, value=v)
    c.font = font
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    return c


def _hdr(ws, labels):
    ws.append([_c(ws, x, H_FONT, fill=H_FILL) for x in labels])


def _widths(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[L(i)].width = w


# ------------------------------------------------------------------------------------------------
class Book:
    """Tracks where things live so formulas on later sheets can reference them."""

    def __init__(self, cfg, prep, res):
        self.cfg, self.prep, self.res = cfg, prep, res
        self.raw = load_raw(cfg)
        self.wb = Workbook(write_only=True)
        from openpyxl.workbook.properties import CalcProperties
        self.wb.calculation = CalcProperties(fullCalcOnLoad=True)   # Excel recalculates on open
        self.A = {}          # assumption name -> absolute reference
        self.periods = list(prep.periods)
        self.nm = len(self.periods)

    # ---- README ---------------------------------------------------------------------------------
    def readme(self):
        ws = self.wb.create_sheet("README")
        _widths(ws, [26, 110])
        rows = [
            ("The Economics of Payment Failure: Excel version", T_FONT),
            ("ZT East Africa, Jan 2022 – Apr 2024. Built by src/payfail/excel.py from data/raw/ZT_EA_Regional_Data.xlsx.", NOTE),
            ("", None),
            ("Colour legend", BOLD),
            ("Blue text, yellow fill: inputs and assumptions you can change (Assumptions sheet). Black: formulas. "
             "Green: links to another sheet.", B_FONT),
            ("", None),
            ("Sheet", BOLD),
        ]
        for t, f in rows:
            ws.append([_c(ws, t, f)] if f else [])
        sheets = [
            ("Assumptions", "Every threshold and alias. Change a blue cell and the whole workbook recalculates."),
            ("Rates_Daily", "Raw daily rates (USD per unit) with alias mapping, SLL restatement, spike screen and duplicate-day weights."),
            ("Rates_Monthly", "Monthly median, average, month-end, min, max and high–low range per currency; 2022 base rate."),
            ("Customers", "Customer table (sorted by id) with cleaned country labels."),
            ("Transactions", "All 62,684 records: USD translation, flags, failure measures, anomaly category. Raw columns A–H."),
            ("Anomaly_Rules", "Customer × payment type × month grid: prior 6-month median, extreme-volume rule, escalation trigger."),
            ("Summary", "Headline, data flags, exposure bridge, monthly series, payment types and markets."),
            ("January", "Jan 2024 vs Jul–Dec 2023: anomaly and FX effects, then LMDI-I volume / mix / failure-rate / fee-yield effects."),
            ("Laney", "Laney p′ charts for every market × payment type with enough eligible months, and the pattern flags."),
            ("Recovery", "USD card recovery scenarios against best-window and mobile money benchmarks; contribution at cost ratios."),
            ("FX", "Reported vs 2022 constant-currency fees by currency and year; the 10% high–low screen."),
            ("Checks", "Each key figure here against the Python pipeline. Every row should read OK."),
        ]
        for s, d in sheets:
            ws.append([_c(ws, s, BOLD), _c(ws, d)])
        ws.append([])
        ws.append([_c(ws, "Python only", BOLD), _c(ws, "Pareto curve, value quintiles, persistence and lapse, hard/mixed split, "
                   "same-customer benchmark, failure-offset sensitivity and the prioritisation matrix are in outputs/tables/*.csv.")])
        ws.append([_c(ws, "Speed", BOLD), _c(ws, "The workbook holds about 1.6 million formulas. Set calculation to manual while editing "
                   "assumptions, then recalculate (F9).")])

    # ---- Assumptions ----------------------------------------------------------------------------
    def assumptions(self):
        ws = self.wb.create_sheet("Assumptions")
        _widths(ws, [44, 16, 70])
        cfg = self.cfg
        ws.append([_c(ws, "Assumptions", T_FONT)])
        ws.append([_c(ws, "Blue cells are inputs. Each is referenced by the formulas that use it.", NOTE)])
        _hdr(ws, ["Assumption", "Value", "Note"])
        r = 4
        fx = cfg["fx"]["redenomination_fixes"][0]
        a, e, pt, j, rc, fl = (cfg["anomalies"]["relative"], cfg["anomalies"]["escalation"], cfg["patterns"], cfg["january"],
                               cfg["recovery"], cfg["flags"])
        items = [
            ("fix_ccy", "Redenomination: currency", fx["currency"], None, "Sierra Leone: 1 SLE = 1,000 SLL from 1 July 2022"),
            ("fix_thr", "Redenomination: restate rates above", fx["rate_above"], RATE, "Supplied series switches to new-leone scale"),
            ("fix_div", "Redenomination: divide by", fx["divide_by"], INT, ""),
            ("spike", "Spike screen: ratio to currency-month median", cfg["fx"]["spike_ratio"], "0.0", "Daily rates above 5x or below 1/5 of the month's median are dropped"),
            ("cc_year", "Constant-currency base year", cfg["fx"]["constant_currency_year"], "0", "Average of daily rates in this year"),
            ("screen", "High–low screen", cfg["fx"]["volatility_screen"], PCT, "Analytical threshold, not an IAS 21 rule"),
            ("fee_low", "Fee-ratio flag: below", fl["fee_ratio_low"], PCT, "Fee as a share of transaction value"),
            ("fee_high", "Fee-ratio flag: above", fl["fee_ratio_high"], PCT, ""),
            ("vpa", "Value flag: USD per attempt above", fl["value_per_attempt_limit"], USD, "About the 99.9th percentile"),
            ("rel_min", "Extreme-volume rule: minimum failed attempts", a["min_failed"], INT, "Customer × payment type × month"),
            ("rel_mult", "Extreme-volume rule: attempts above x prior median", a["multiple_of_prior_median"], "0", "Median of the 6 preceding months, zeros included (window fixed at 6)"),
            ("rel_succ", "Extreme-volume rule: success rate below", a["max_success_rate"], PCT, ""),
            ("esc_min", "Escalation trigger: minimum failed attempts", e["min_failed"], INT, "Applied to observations not caught by the extreme rule"),
            ("esc_succ", "Escalation trigger: success rate below", e["max_success_rate"], PCT, ""),
            ("pat_att", "Laney: minimum attempts in an eligible month", pt["min_month_attempts"], INT, ""),
            ("pat_months", "Laney: minimum eligible months", pt["min_eligible_months"], INT, ""),
            ("structural", "Structural flag: median failure rate at least", pt["structural_median"], PCT, ""),
            ("deter", "Deteriorating flag: last 6 minus first 6 at least", pt["deteriorating_pp"], PCT, "Percentage points"),
            ("unstable", "Unstable flag: standard deviation at least", pt["unstable_sd"], PCT, ""),
            ("jan_s", "January: baseline start", pd.Timestamp(j["baseline_start"]), DATE, ""),
            ("jan_e", "January: baseline end", pd.Timestamp(j["baseline_end"]), DATE, ""),
            ("jan_t", "January: target month", pd.Timestamp(j["target"]), DATE, ""),
            ("margin", "Recovery: optimistic case, points below mobile money", rc["optimistic_margin"], PCT, ""),
            ("win_min", "Recovery: minimum attempts in a 3-month window", rc["best_window_min_attempts"], INT, "Window length fixed at 3 months"),
            ("min_succ", "Recovery: minimum successes for a market's own fee", rc["min_successes_for_local_fee"], INT, "Otherwise the all-market average applies"),
        ]
        for i, cr in enumerate(rc["cost_ratios"], start=1):
            items.append((f"cost{i}", f"Assumed processing cost ratio {i}", cr, PCT, "Illustrative, not observed costs"))
        for key, lab, val, fmt, note in items:
            ws.append([_c(ws, lab), _c(ws, val, IN_FONT, fmt, IN_FILL), _c(ws, note, NOTE)])
            self.A[key] = f"Assumptions!$B${r}"
            r += 1
        ws.append([]); r += 1
        ws.append([_c(ws, "Currency aliases", BOLD)]); r += 1
        _hdr(ws, ["Code in data", "Maps to", ""]); r += 1
        ca = cfg["data"]["currency_aliases"]
        s = r
        for k, v in ca.items():
            ws.append([_c(ws, k, IN_FONT, fill=IN_FILL), _c(ws, v, IN_FONT, fill=IN_FILL)]); r += 1
        self.A["ca_from"], self.A["ca_to"] = f"Assumptions!$A${s}:$A${r - 1}", f"Assumptions!$B${s}:$B${r - 1}"
        ws.append([]); r += 1
        ws.append([_c(ws, "Country aliases", BOLD)]); r += 1
        _hdr(ws, ["Label in data", "Maps to", ""]); r += 1
        s = r
        for k, v in cfg["data"]["country_aliases"].items():
            ws.append([_c(ws, k, IN_FONT, fill=IN_FILL), _c(ws, v, IN_FONT, fill=IN_FILL)]); r += 1
        self.A["co_from"], self.A["co_to"] = f"Assumptions!$A${s}:$A${r - 1}", f"Assumptions!$B${s}:$B${r - 1}"

    # ---- Rates ----------------------------------------------------------------------------------
    def rates_daily(self):
        fx = self.raw["exchange_rates"].copy()
        al = self.cfg["data"]["currency_aliases"]
        fx["_c"] = fx.currency.replace(al)
        fx = fx.sort_values(["_c", "date", "currency"]).reset_index(drop=True)
        self.ccys = sorted(fx._c.unique())
        n = len(fx)
        self.rd_last = n + 1
        ws = self.wb.create_sheet("Rates_Daily")
        _widths(ws, [12, 10, 8, 12, 14, 8, 14, 14, 14, 14, 8, 8, 18, 9, 14])
        ws.freeze_panes = "A2"
        _hdr(ws, ["Date", "Currency", "Code", "Month", "Rate (raw)", "Valid", "Rate (restated)", "Month key", "Median input",
                  "Month median", "Spike", "Use", "Day key", "Weight", "Weighted rate"])
        A = self.A
        med_ref = None  # filled after Rates_Monthly layout is known
        self._rm_layout()
        lay = self.rm
        for i, rr in enumerate(fx.itertuples(index=False), start=2):
            p, nx = i - 1, i + 1
            ws.append([
                _c(ws, rr.date.to_pydatetime(), fmt="yyyy-mm-dd"), rr.currency,
                f"=IFERROR(INDEX({A['ca_to']},MATCH(B{i},{A['ca_from']},0)),B{i})",
                _c(ws, f"=DATE(YEAR(A{i}),MONTH(A{i}),1)", fmt=DATE), rr.rate,
                f"=E{i}>0",
                f"=IF(AND(C{i}={A['fix_ccy']},E{i}>{A['fix_thr']}),E{i}/{A['fix_div']},E{i})",
                f'=C{i}&"|"&(YEAR(D{i})*100+MONTH(D{i}))',
                f'=IF(F{i},G{i},"")',
                f'=IFERROR(INDEX({lay["median"]},MATCH(C{i},{lay["ccys"]},0),MATCH(D{i},{lay["months"]},0)),"")',
                f"=IF(AND(F{i},ISNUMBER(J{i})),OR(G{i}/J{i}>{A['spike']},G{i}/J{i}<1/{A['spike']}),FALSE)",
                f"=AND(F{i},NOT(K{i}))",
                f'=C{i}&"|"&INT(A{i})',
                f"=IF(L{i},1/(1+AND(M{p}=M{i},L{p}=TRUE)+AND(M{nx}=M{i},L{nx}=TRUE)),0)",
                f"=N{i}*G{i}",
            ])

    def _rm_layout(self):
        """Rates_Monthly: six stacked blocks, currencies down, months across."""
        nc, nm = len(self.ccys), self.nm
        blocks = ["median", "avg", "end", "min", "max", "range"]
        self.rm_blocks = {}
        r = 4
        for b in blocks:
            self.rm_blocks[b] = r          # header row of the block
            r += nc + 3
        lastcol = L(1 + nm)
        hdr = self.rm_blocks["avg"] + 1   # month header row; data rows follow
        self.rm = {"ccys": f"Rates_Monthly!$A${hdr + 1}:$A${hdr + nc}",
                   "months": f"Rates_Monthly!$B${hdr}:${lastcol}${hdr}"}
        for b, h in self.rm_blocks.items():
            self.rm[b] = f"Rates_Monthly!$B${h + 2}:${lastcol}${h + 1 + nc}"
        bc = L(nm + 3)
        self.rm["base"] = f"Rates_Monthly!${bc}${hdr + 1}:${bc}${hdr + nc}"

    def rates_monthly(self):
        ws = self.wb.create_sheet("Rates_Monthly")
        nc, nm, n = len(self.ccys), self.nm, self.rd_last
        _widths(ws, [9] + [11] * nm + [3, 13])
        D = "Rates_Daily!"
        col = lambda c: f"{D}${c}$2:${c}${n}"
        titles = {"median": "Median of valid restated daily rates (spike screen reference)",
                  "avg": "Monthly average rate, USD per unit (average of daily means, spikes excluded)",
                  "end": "Month-end rate (last valid day)", "min": "Lowest valid daily rate", "max": "Highest valid daily rate",
                  "range": "High–low range as % of the monthly average"}
        ws.append([_c(ws, "Monthly rates", T_FONT)])
        ws.append([_c(ws, "USD per unit of currency. USD is fixed at 1.", NOTE)])
        ws.append([])
        r = 4
        for b, h in self.rm_blocks.items():
            assert r == h
            ws.append([_c(ws, titles[b], BOLD)]); r += 1
            row = [_c(ws, "Code", H_FONT, fill=H_FILL)] + [_c(ws, p.to_pydatetime(), H_FONT, DATE, H_FILL) for p in self.periods]
            if b == "avg":
                row += [None, _c(ws, "2022 base rate", H_FONT, fill=H_FILL)]
            ws.append(row); r += 1
            hr = r - 1
            for k, cc in enumerate(self.ccys):
                i = r
                cells = [_c(ws, cc)]
                for m in range(nm):
                    cl = L(2 + m)
                    key = f'$A{i}&"|"&(YEAR({cl}${hr})*100+MONTH({cl}${hr}))'
                    if cc == "USD" and b in ("avg", "end", "min", "max"):
                        f = 1
                    elif cc == "USD" and b == "range":
                        f = 0
                    elif b == "median":
                        f = (f'=IFERROR(MEDIAN(INDEX({col("I")},MATCH({key},{col("H")},0)):'
                             f'INDEX({col("I")},MATCH({key},{col("H")},0)+COUNTIF({col("H")},{key})-1)),"")')
                    elif b == "avg":
                        f = f'=IFERROR(SUMIFS({col("O")},{col("H")},{key})/SUMIFS({col("N")},{col("H")},{key}),"")'
                    elif b == "end":
                        f = (f'=IFERROR(AVERAGEIFS({col("G")},{col("H")},{key},{col("L")},TRUE,{col("A")},'
                             f'_xlfn.MAXIFS({col("A")},{col("H")},{key},{col("L")},TRUE)),"")')
                    elif b == "min":
                        f = f'=IF(COUNTIFS({col("H")},{key},{col("L")},TRUE)=0,"",_xlfn.MINIFS({col("G")},{col("H")},{key},{col("L")},TRUE))'
                    elif b == "max":
                        f = f'=IF(COUNTIFS({col("H")},{key},{col("L")},TRUE)=0,"",_xlfn.MAXIFS({col("G")},{col("H")},{key},{col("L")},TRUE))'
                    else:
                        ar, mr, nr = (self.rm_blocks[x] + 2 + k for x in ("avg", "max", "min"))
                        f = f'=IFERROR(({cl}{mr}-{cl}{nr})/{cl}{ar},"")'
                    cells.append(_c(ws, f, fmt=PCT if b == "range" else RATE))
                if b == "avg":
                    y = self.A["cc_year"]
                    base = (1 if cc == "USD" else
                            f'=IFERROR(SUMIFS({col("O")},{col("C")},$A{i},{col("A")},">="&DATE({y},1,1),{col("A")},"<="&DATE({y},12,31))/'
                            f'SUMIFS({col("N")},{col("C")},$A{i},{col("A")},">="&DATE({y},1,1),{col("A")},"<="&DATE({y},12,31)),"")')
                    cells += [None, _c(ws, base, fmt=RATE)]
                ws.append(cells); r += 1
            ws.append([]); r += 1

    # ---- Customers -------------------------------------------------------------------------------
    def customers(self):
        c = self.raw["customer_details"].sort_values("customer_id").reset_index(drop=True)
        ws = self.wb.create_sheet("Customers")
        _widths(ws, [12, 30, 14, 34])
        ws.freeze_panes = "A2"
        _hdr(ws, ["Customer id", "Country (data)", "Country", "Sector (data)"])
        A = self.A
        for i, r in enumerate(c.itertuples(index=False), start=2):
            ws.append([r.customer_id, r.country_description,
                       f"=IFERROR(INDEX({A['co_to']},MATCH(B{i},{A['co_from']},0)),B{i})",
                       None if pd.isna(r.sector) else r.sector])
        self.cust_last = len(c) + 1

    # ---- Transactions -----------------------------------------------------------------------------
    TX_COLS = ["Month", "Customer id", "Currency", "Status", "Payment type", "Attempts", "Value (local)", "Fee (local)",
               "Code", "Country", "Avg rate", "Month-end rate", "Base rate", "Rate available", "Failed", "Attempts (all)",
               "Failed attempts", "Successful attempts", "Missing fee", "Fee USD", "Fee USD (2022 rates)", "Fee USD (month-end)",
               "Failed fee USD", "Failed fee USD (2022 rates)", "Failed fee USD (month-end)", "Value USD", "Fee-ratio flag",
               "Value flag", "Value excluded", "Failed value USD", "Rule row", "Extreme-volume anomaly", "Category"]

    def transactions(self):
        t = self.raw["transactions"]
        ws = self.wb.create_sheet("Transactions")
        ws.freeze_panes = "C2"
        _widths(ws, [10, 11, 8, 10, 18, 9, 13, 11] + [11] * 25)
        _hdr(ws, self.TX_COLS)
        A, rm = self.A, self.rm
        n = len(t)
        self.tx_last = n + 1
        cn = self.cust_last
        an = self.an  # anomaly layout
        for i, r in enumerate(t.itertuples(index=False), start=2):
            rev = None if pd.isna(r.revenue) else r.revenue
            ws.append([
                _c(ws, r.period.to_pydatetime(), fmt=DATE), r.customer_id, r.currency, r.status, r.paymenttype,
                r.total_count, r.total_value, rev,
                f"=IFERROR(INDEX({A['ca_to']},MATCH(C{i},{A['ca_from']},0)),C{i})",
                f"=INDEX(Customers!$C$2:$C${cn},MATCH(B{i},Customers!$A$2:$A${cn},1))",
                f'=IFERROR(INDEX({rm["avg"]},MATCH(I{i},{rm["ccys"]},0),MATCH(A{i},{rm["months"]},0))*1,"")',
                f'=IFERROR(INDEX({rm["end"]},MATCH(I{i},{rm["ccys"]},0),MATCH(A{i},{rm["months"]},0))*1,"")',
                f'=IFERROR(INDEX({rm["base"]},MATCH(I{i},{rm["ccys"]},0))*1,K{i})',
                f"=ISNUMBER(K{i})",
                f'=D{i}<>"successful"',
                f"=F{i}", f"=IF(O{i},F{i},0)", f"=P{i}-Q{i}",
                f"=ISBLANK(H{i})",
                f"=IF(N{i},N(H{i})*K{i},0)", f"=IF(N{i},N(H{i})*M{i},0)", f"=IF(N{i},N(H{i})*L{i},0)",
                f"=IF(O{i},T{i},0)", f"=IF(O{i},U{i},0)", f"=IF(O{i},V{i},0)",
                f"=IF(N{i},G{i}*K{i},0)",
                f"=IF(OR(S{i},G{i}=0),FALSE,OR(H{i}/G{i}<{A['fee_low']},H{i}/G{i}>{A['fee_high']}))",
                f"=IF(N{i},OR(G{i}<=0,IF(F{i}>0,Z{i}/F{i}>{A['vpa']},FALSE)),FALSE)",
                f"=OR(AB{i},NOT(N{i}))",
                f"=IF(O{i},Z{i},0)",
                f'=IFERROR(MATCH(B{i}&"|"&E{i},{an["key"]},0),0)',
                f"=IF(AE{i}=0,FALSE,INDEX({an['ext']},AE{i},MATCH(A{i},{an['months']},0)))",
                f'=IF(AF{i},"Extreme-volume anomaly",IF(COUNTIFS({an["cust"]},B{i},{an["esc_any"]},TRUE)>0,"Escalation","Remaining"))',
            ])

    def tx(self, col):
        return f"Transactions!${col}$2:${col}${self.tx_last}"

    # ---- Anomaly rules ----------------------------------------------------------------------------
    def anomaly_layout(self):
        cmc = self.prep.cmc
        keep = cmc.groupby(["customer_id", "pt"]).f_att.max()
        keep = keep[keep >= 100].index
        g = cmc.set_index(["customer_id", "pt"]).loc[keep].reset_index()
        self.att = g.pivot_table(index=["customer_id", "pt"], columns="period", values="att", aggfunc="sum", fill_value=0).reindex(columns=self.periods, fill_value=0)
        self.fat = g.pivot_table(index=["customer_id", "pt"], columns="period", values="f_att", aggfunc="sum", fill_value=0).reindex(index=self.att.index, columns=self.periods, fill_value=0)
        nm, np_ = self.nm, len(self.att)
        first, last = 6, 5 + np_
        # columns: A cust, B pt, C key, D check-sum, E check-tx, F diff, then blocks of nm
        start = {}
        c = 7
        for b in ["att", "fat", "sat", "prior", "ext", "trig"]:
            start[b] = c
            c += nm + 1
        self.an_start, self.an_first, self.an_last = start, first, last
        rng = lambda b: f"Anomaly_Rules!${L(start[b])}${first}:${L(start[b] + nm - 1)}${last}"
        self.an = {"key": f"Anomaly_Rules!$C${first}:$C${last}", "cust": f"Anomaly_Rules!$A${first}:$A${last}",
                   "esc_any": f"Anomaly_Rules!${L(c)}${first}:${L(c)}${last}", "ext": rng("ext"), "trig": rng("trig"),
                   "months": f"Anomaly_Rules!${L(start['ext'])}$5:${L(start['ext'] + nm - 1)}$5"}
        self.an_esc_col = c

    def anomaly_sheet(self):
        ws = self.wb.create_sheet("Anomaly_Rules")
        ws.freeze_panes = "G6"
        nm, A, st = self.nm, self.A, self.an_start
        _widths(ws, [11, 18, 22, 11, 11, 9] + [9] * (6 * (nm + 1)) + [12])
        ws.append([_c(ws, "Anomaly rules: customer × payment type × month", T_FONT)])
        ws.append([_c(ws, "Rows are every customer × payment type with at least 100 failed attempts in some month (thresholds below "
                       "100 would need more rows). Attempt and failed-attempt grids are a pivot of Transactions supplied as values; "
                       "columns D–F reconcile each row back to Transactions.", NOTE)])
        ws.append([_c(ws, "Extreme-volume rule: failed ≥ minimum, attempts > multiple × MAX(prior median, 1), success rate < limit. "
                       "Escalation trigger: not extreme, failed ≥ minimum, success rate < limit; it marks the whole customer.", NOTE)])
        titles = {"att": "Attempts (values)", "fat": "Failed attempts (values)", "sat": "Successful attempts",
                  "prior": "Prior 6-month median of attempts", "ext": "Extreme-volume anomaly", "trig": "Escalation trigger"}
        r4 = [None] * (self.an_esc_col)
        for b, s in st.items():
            r4[s - 1] = _c(ws, titles[b], BOLD)
        ws.append(r4)
        hdr = [_c(ws, x, H_FONT, fill=H_FILL) for x in ["Customer", "Payment type", "Key", "Failed (grid)", "Failed (Transactions)", "Difference"]]
        for b, s in st.items():
            while len(hdr) < s - 1:
                hdr.append(None)
            hdr += [_c(ws, p.to_pydatetime(), H_FONT, DATE, H_FILL) for p in self.periods]
        while len(hdr) < self.an_esc_col - 1:
            hdr.append(None)
        hdr.append(_c(ws, "Escalation customer", H_FONT, fill=H_FILL))
        ws.append(hdr)
        T = self.tx
        for k, ((cust, pt), arow) in enumerate(self.att.iterrows()):
            i = self.an_first + k
            fa = self.fat.loc[(cust, pt)]
            row = [cust, pt, f'=A{i}&"|"&B{i}', f"=SUM({L(st['fat'])}{i}:{L(st['fat'] + nm - 1)}{i})",
                   f'=SUMIFS({T("Q")},{T("B")},A{i},{T("E")},B{i})', f"=D{i}-E{i}"]
            for b, s in st.items():
                while len(row) < s - 1:
                    row.append(None)
                for m in range(nm):
                    ca, cf, cs, cp, ce = (L(st[x] + m) for x in ("att", "fat", "sat", "prior", "ext"))
                    if b == "att":
                        v = int(arow.iloc[m])
                    elif b == "fat":
                        v = int(fa.iloc[m])
                    elif b == "sat":
                        v = f"={ca}{i}-{cf}{i}"
                    elif b == "prior":
                        v = 0 if m == 0 else f"=MEDIAN({L(st['att'] + max(0, m - 6))}{i}:{L(st['att'] + m - 1)}{i})"
                    elif b == "ext":
                        v = (f"=AND({cf}{i}>={A['rel_min']},{ca}{i}>{A['rel_mult']}*MAX({cp}{i},1),"
                             f"IF({ca}{i}>0,{cs}{i}/{ca}{i}<{A['rel_succ']},FALSE))")
                    else:
                        v = f"=AND(NOT({ce}{i}),{cf}{i}>={A['esc_min']},IF({ca}{i}>0,{cs}{i}/{ca}{i}<{A['esc_succ']},FALSE))"
                    row.append(v)
            while len(row) < self.an_esc_col - 1:
                row.append(None)
            row.append(f"=COUNTIF({L(st['trig'])}{i}:{L(st['trig'] + nm - 1)}{i},TRUE)>0")
            ws.append(row)

    # ---- Summary ----------------------------------------------------------------------------------
    def summary(self):
        ws = self.wb.create_sheet("Summary")
        _widths(ws, [34, 15, 15, 15, 15, 15, 15, 15, 15, 15])
        T = self.tx
        self.S = {}
        r = [0]

        def put(cells):
            ws.append(cells)
            r[0] += 1
            return r[0]

        put([_c(ws, "Summary", T_FONT)])
        put([_c(ws, "Count measures use all records; USD measures use records with an exchange rate.", NOTE)])
        put([])
        put([_c(ws, "Headline", BOLD)])
        heads = [
            ("records", "Records", f"=COUNTA({T('B')})", INT),
            ("attempts", "Payment attempts", f"=SUM({T('P')})", INT),
            ("failed", "Failed attempts", f"=SUM({T('Q')})", INT),
            ("count_rate", "Count failure rate", None, PCT),
            ("records_translatable", "Records with an exchange rate", f"=COUNTIF({T('N')},TRUE)", INT),
            ("untranslatable", "Records without an exchange rate", f"=COUNTIF({T('N')},FALSE)", INT),
            ("attempts_translatable", "Attempts with an exchange rate", f"=SUMIFS({T('P')},{T('N')},TRUE)", INT),
            ("fees", "Recorded fees (USD)", f"=SUM({T('T')})", USD),
            ("failed_fees", "Fees on failed transactions (USD)", f"=SUM({T('W')})", USD),
            ("succ_fees", "Successful-transaction fees (USD)", None, USD),
            ("fee_share", "Failed-fee share", None, PCT),
            ("flag_fee_ratio", "Fee-ratio flags", f"=COUNTIF({T('AA')},TRUE)", INT),
            ("flag_missing_fee", "Missing-fee flags", f"=COUNTIF({T('S')},TRUE)", INT),
            ("flag_value", "Value flags", f"=COUNTIF({T('AB')},TRUE)", INT),
            ("flag_value_usd", "Value of flagged records (USD)", f"=SUMIFS({T('Z')},{T('AB')},TRUE)", USD),
            ("value", "Transaction value, excluding flagged (USD)", f"=SUMIFS({T('Z')},{T('AC')},FALSE)", USD),
            ("failed_value", "Failed value, excluding flagged (USD)", f"=SUMIFS({T('AD')},{T('AC')},FALSE)", USD),
        ]
        for key, lab, f, fmt in heads:
            i = r[0] + 1
            self.S[key] = f"Summary!$B${i}"
            if key == "count_rate":
                f = f"={self.S['failed']}/{self.S['attempts']}"
            if key == "succ_fees":
                f = f"={self.S['fees']}-{self.S['failed_fees']}"
            if key == "fee_share":
                f = f"={self.S['failed_fees']}/{self.S['fees']}"
            put([_c(ws, lab), _c(ws, f, fmt=fmt)])
        put([])
        put([_c(ws, "Exposure bridge (mutually exclusive)", BOLD)])
        _hdr(ws, ["Category", "Failed attempts", "Fees on failed transactions", "Share"]); r[0] += 1
        b0 = r[0] + 1
        for cat in ["Extreme-volume anomaly", "Escalation", "Remaining"]:
            i = r[0] + 1
            self.S[f"bridge_{cat}"] = f"Summary!$C${i}"
            put([_c(ws, cat), _c(ws, f'=SUMIFS({T("Q")},{T("AG")},A{i})', fmt=INT), _c(ws, f'=SUMIFS({T("W")},{T("AG")},A{i})', fmt=USD),
                 _c(ws, f"=C{i}/SUM($C${b0}:$C${b0 + 2})", fmt=PCT)])
        i = r[0] + 1
        put([_c(ws, "Total", BOLD), _c(ws, f"=SUM(B{b0}:B{i - 1})", BOLD, INT), _c(ws, f"=SUM(C{b0}:C{i - 1})", BOLD, USD),
             _c(ws, f'=IF(ABS(C{i}-{self.S["failed_fees"]})<0.01,"Ties to headline","CHECK")', NOTE)])
        put([])
        put([_c(ws, "Monthly", BOLD)])
        _hdr(ws, ["Month", "Attempts", "Failed attempts", "Count failure rate", "Count rate, remaining", "Failed-fee share",
                  "Failed-fee share, remaining", "Failed fees: extreme", "Failed fees: escalation", "Failed fees: remaining"]); r[0] += 1
        for p in self.periods:
            i = r[0] + 1
            m = f"{T('A')},$A{i}"
            rem = f'{T("AG")},"Remaining"'
            put([_c(ws, p.to_pydatetime(), fmt=DATE), _c(ws, f"=SUMIFS({T('P')},{m})", fmt=INT), _c(ws, f"=SUMIFS({T('Q')},{m})", fmt=INT),
                 _c(ws, f"=C{i}/B{i}", fmt=PCT), _c(ws, f"=SUMIFS({T('Q')},{m},{rem})/SUMIFS({T('P')},{m},{rem})", fmt=PCT),
                 _c(ws, f"=SUMIFS({T('W')},{m})/SUMIFS({T('T')},{m})", fmt=PCT),
                 _c(ws, f"=SUMIFS({T('W')},{m},{rem})/SUMIFS({T('T')},{m},{rem})", fmt=PCT),
                 _c(ws, f'=SUMIFS({T("W")},{m},{T("AG")},"Extreme-volume anomaly")', fmt=USD),
                 _c(ws, f'=SUMIFS({T("W")},{m},{T("AG")},"Escalation")', fmt=USD),
                 _c(ws, f"=SUMIFS({T('W')},{m},{rem})", fmt=USD)])
        for title, col, items in [("Payment types", "E", ["card", "mobilemoney", "alternative channels", "bank transfer", "account",
                                                          "pay with wallet", "enaira"]),
                                  ("Markets", "J", ["Kenya", "Uganda", "Tanzania", "Ghana", "Zambia"])]:
            put([])
            put([_c(ws, title, BOLD)])
            _hdr(ws, ["", "Attempts", "Failed attempts", "Count failure rate", "Fees (USD)", "Failed fees (USD)", "Failed-fee share",
                      "Share of all failed fees"]); r[0] += 1
            for it in items:
                i = r[0] + 1
                k = f"{T(col)},$A{i}"
                put([_c(ws, it), _c(ws, f"=SUMIFS({T('P')},{k})", fmt=INT), _c(ws, f"=SUMIFS({T('Q')},{k})", fmt=INT),
                     _c(ws, f"=IFERROR(C{i}/B{i},0)", fmt=PCT), _c(ws, f"=SUMIFS({T('T')},{k})", fmt=USD),
                     _c(ws, f"=SUMIFS({T('W')},{k})", fmt=USD), _c(ws, f"=IFERROR(F{i}/E{i},0)", fmt=PCT),
                     _c(ws, f"=F{i}/{self.S['failed_fees']}", fmt=PCT)])
                if it == "card" and col == "E":
                    self.S["card_share"] = f"Summary!$H${i}"

    # ---- January ----------------------------------------------------------------------------------
    def january(self):
        ws = self.wb.create_sheet("January")
        _widths(ws, [30, 18, 15, 15, 15, 15, 15, 15, 9, 15, 14, 14, 14, 14])
        T, A = self.tx, self.A
        self.J = {}
        ws.append([_c(ws, "January 2024 decomposition", T_FONT)])
        ws.append([_c(ws, "Baseline = monthly average of the baseline window. LMDI-I on non-anomalous, translatable records at 2022 "
                       "constant currency; cells present in only one period form the entry/exit term.", NOTE)])
        ws.append([])
        win = f'{T("A")},">="&{A["jan_s"]},{T("A")},"<="&{A["jan_e"]}'
        tgt = f'{T("A")},{A["jan_t"]}'
        rows = [
            ("n", "Baseline months", f"=(YEAR({A['jan_e']})-YEAR({A['jan_s']}))*12+MONTH({A['jan_e']})-MONTH({A['jan_s']})+1", INT),
            ("b_all", "Baseline failed fees, all", f"=SUMIFS({T('W')},{win})/B4", USD),
            ("j_all", "January failed fees, all", f"=SUMIFS({T('W')},{tgt})", USD),
            ("b_ex", "Baseline, extreme-volume anomalies", f"=SUMIFS({T('W')},{win},{T('AF')},TRUE)/B4", USD),
            ("j_ex", "January, extreme-volume anomalies", f"=SUMIFS({T('W')},{tgt},{T('AF')},TRUE)", USD),
            ("b_nb", "Baseline, non-anomalous (reported)", f"=SUMIFS({T('W')},{win},{T('AF')},FALSE)/B4", USD),
            ("j_nb", "January, non-anomalous (reported)", f"=SUMIFS({T('W')},{tgt},{T('AF')},FALSE)", USD),
            ("b_cc", "Baseline, non-anomalous (2022 rates)", f"=SUMIFS({T('X')},{win},{T('AF')},FALSE)/B4", USD),
            ("j_cc", "January, non-anomalous (2022 rates)", f"=SUMIFS({T('X')},{tgt},{T('AF')},FALSE)", USD),
        ]
        for k, (key, lab, f, fmt) in enumerate(rows, start=4):
            ws.append([_c(ws, lab), _c(ws, f, fmt=fmt)])
            self.J[key] = f"$B${k}"
        ws.append([])
        ct = 4 + len(rows) + 2   # header row of the cells table
        ws.append([_c(ws, "Market × payment type cells (non-anomalous, translatable)", BOLD)])
        _hdr(ws, ["Market", "Payment type", "Attempts, base", "Failed, base", "Failed fees (2022), base", "Attempts, Jan",
                  "Failed, Jan", "Failed fees (2022), Jan", "In both", "Log-mean weight", "Volume", "Mix", "Failure rate", "Fee yield"])
        cells = [(c, p) for c in ["Kenya", "Uganda", "Tanzania", "Ghana", "Zambia"]
                 for p in ["card", "mobilemoney", "alternative channels", "bank transfer", "account", "pay with wallet", "enaira"]]
        first = ct + 1
        last = first + len(cells) - 1
        N0, N1 = f"$C${last + 2}", f"$F${last + 2}"
        nb = f'{T("AF")},FALSE,{T("N")},TRUE,{T("J")},$A{{i}},{T("E")},$B{{i}}'
        for k, (c, p) in enumerate(cells):
            i = first + k
            q = nb.format(i=i)
            ws.append([c, p,
                       _c(ws, f"=SUMIFS({T('P')},{q},{win})/{self.J['n']}", fmt="#,##0.0"),
                       _c(ws, f"=SUMIFS({T('Q')},{q},{win})/{self.J['n']}", fmt="#,##0.0"),
                       _c(ws, f"=SUMIFS({T('X')},{q},{win})/{self.J['n']}", fmt=USD),
                       _c(ws, f"=SUMIFS({T('P')},{q},{tgt})", fmt=INT),
                       _c(ws, f"=SUMIFS({T('Q')},{q},{tgt})", fmt=INT),
                       _c(ws, f"=SUMIFS({T('X')},{q},{tgt})", fmt=USD),
                       f"=AND(E{i}>0,H{i}>0)",
                       _c(ws, f"=IF(I{i},IF(ABS(H{i}-E{i})<=0.00001*ABS(E{i}),E{i},(H{i}-E{i})/(LN(H{i})-LN(E{i}))),0)", fmt=USD2),
                       _c(ws, f"=IF(I{i},J{i}*LN({N1}/{N0}),0)", fmt=USD2),
                       _c(ws, f"=IF(I{i},J{i}*LN((F{i}/{N1})/(C{i}/{N0})),0)", fmt=USD2),
                       _c(ws, f"=IF(I{i},J{i}*LN((G{i}/F{i})/(D{i}/C{i})),0)", fmt=USD2),
                       _c(ws, f"=IF(I{i},J{i}*LN((H{i}/G{i})/(E{i}/D{i})),0)", fmt=USD2)])
        rng = lambda c: f"{c}{first}:{c}{last}"
        ws.append([_c(ws, "All cells", BOLD), None, _c(ws, f"=SUM({rng('C')})", fmt="#,##0.0"), None, _c(ws, f"=SUM({rng('E')})", fmt=USD),
                   _c(ws, f"=SUM({rng('F')})", fmt=INT), None, _c(ws, f"=SUM({rng('H')})", fmt=USD)])
        i = last + 2
        ws.append([_c(ws, "Cells in both periods", BOLD), None, _c(ws, f"=SUMIFS({rng('C')},{rng('I')},TRUE)", fmt="#,##0.0"), None,
                   _c(ws, f"=SUMIFS({rng('E')},{rng('I')},TRUE)", fmt=USD), _c(ws, f"=SUMIFS({rng('F')},{rng('I')},TRUE)", fmt=INT),
                   None, _c(ws, f"=SUMIFS({rng('H')},{rng('I')},TRUE)", fmt=USD), _c(ws, f'=COUNTIF({rng("I")},TRUE)', fmt=INT)])
        ws.append([])
        ws.append([_c(ws, "Components", BOLD)])
        _hdr(ws, ["Component", "USD"])
        c0 = last + 6
        J = self.J
        comps = [("Baseline", f"={J['b_all']}"), ("Extreme-volume anomalies", f"={J['j_ex']}-{J['b_ex']}"),
                 ("FX translation", f"=({J['j_nb']}-{J['j_cc']})-({J['b_nb']}-{J['b_cc']})"),
                 ("Volume", f"=SUM({rng('K')})"), ("Mix", f"=SUM({rng('L')})"), ("Failure rate", f"=SUM({rng('M')})"),
                 ("Fee yield", f"=SUM({rng('N')})"),
                 ("Entry/exit cells", f"=(H{last + 1}-E{last + 1})-(H{last + 2}-E{last + 2})"), ("January", f"={J['j_all']}")]
        for k, (lab, f) in enumerate(comps):
            ws.append([_c(ws, lab), _c(ws, f, fmt=USD)])
            self.J[lab] = f"January!$B${c0 + k}"
        rr = c0 + len(comps)
        ws.append([_c(ws, "Residual (should be 0)", BOLD), _c(ws, f"=B{rr - 1}-SUM(B{c0}:B{rr - 2})", BOLD, "0.000000")])
        self.J["Residual"] = f"January!$B${rr}"
        for k in list(J):
            if J[k].startswith("$"):
                J[k] = "January!" + J[k]

    # ---- Laney ------------------------------------------------------------------------------------
    def laney(self):
        ws = self.wb.create_sheet("Laney")
        _widths(ws, [24, 18, 11, 11, 9, 9, 10, 10, 10, 10, 10, 10, 8])
        T, A = self.tx, self.A
        pat = self.res["laney"]["patterns"]
        cells = list(zip(pat.country, pat.pt))
        nm = self.nm
        ws.append([_c(ws, "Laney p′ charts and pattern flags", T_FONT)])
        ws.append([_c(ws, "All records. Eligible month: attempts ≥ the minimum. σz = mean moving range of z / 1.128, "
                       "moving ranges between consecutive eligible months. Flags overlap; Stable = no other flag.", NOTE)])
        ws.append([])
        _hdr(ws, ["Market", "Payment type", "Eligible months", "Included", "Centre p̄", "σz", "Median", "First 6", "Last 6",
                  "Std dev", "Signals", "Structural", "Deteriorating", "Episodic", "Unstable", "Stable"])
        top = 5
        blk0 = top + len(cells) + 2
        size = nm + 3
        self.L = {}
        for k, (c, p) in enumerate(cells):
            i, b = top + k, blk0 + k * size
            f, l = b + 2, b + 1 + nm
            rg = lambda col: f"${col}${f}:${col}${l}"
            ws.append([c, p, _c(ws, f"=COUNTIF({rg('D')},TRUE)", fmt=INT), f"=C{i}>={A['pat_months']}",
                       _c(ws, f"=SUMIFS({rg('C')},{rg('D')},TRUE)/SUMIFS({rg('B')},{rg('D')},TRUE)", fmt=PCT),
                       _c(ws, f"=AVERAGE({rg('I')})/1.128", fmt="0.00"),
                       _c(ws, f"=MEDIAN({rg('F')})", fmt=PCT), _c(ws, f'=AVERAGEIFS({rg("F")},{rg("E")},"<=6")', fmt=PCT),
                       _c(ws, f'=AVERAGEIFS({rg("F")},{rg("E")},">"&(C{i}-6))', fmt=PCT), _c(ws, f"=STDEV({rg('F')})", fmt=PCT),
                       _c(ws, f"=COUNTIF({rg('L')},TRUE)", fmt=INT),
                       f"=G{i}>={A['structural']}", f"=(I{i}-H{i})>={A['deter']}-0.0000001", f"=K{i}>0",
                       f"=J{i}>={A['unstable']}", f"=NOT(OR(L{i}:O{i}))"])
            self.L[(c, p)] = i
        ws.append([])
        ws.append([_c(ws, "Monthly series", BOLD)])
        for k, (c, p) in enumerate(cells):
            b = blk0 + k * size
            ws.append([_c(ws, f"{c} · {p}", BOLD), c, p])
            _hdr(ws, ["Month", "Attempts", "Failed", "Eligible", "Eligible #", "p", "σp", "z", "Moving range", "UCL", "LCL", "Signal"])
            f, l = b + 2, b + 1 + nm
            S = f"$E${top + k}"
            Z = f"$F${top + k}"
            for m, per in enumerate(self.periods):
                i = f + m
                q = f'{T("J")},$B${b},{T("E")},$C${b},{T("A")},A{i}'
                ws.append([_c(ws, per.to_pydatetime(), fmt=DATE), _c(ws, f"=SUMIFS({T('P')},{q})", fmt=INT),
                           _c(ws, f"=SUMIFS({T('Q')},{q})", fmt=INT), f"=B{i}>={A['pat_att']}",
                           f'=IF(D{i},COUNTIF($D${f}:D{i},TRUE),"")', _c(ws, f'=IF(D{i},C{i}/B{i},"")', fmt=PCT),
                           _c(ws, f'=IF(D{i},SQRT({S}*(1-{S})/B{i}),"")', fmt="0.0000"),
                           _c(ws, f'=IF(D{i},(F{i}-{S})/G{i},"")', fmt="0.00"),
                           _c(ws, f'=IF(AND(D{i},N(E{i})>1),ABS(H{i}-INDEX($H${f}:$H${l},MATCH(E{i}-1,$E${f}:$E${l},0))),"")', fmt="0.00"),
                           _c(ws, f'=IF(D{i},{S}+3*G{i}*{Z},"")', fmt=PCT), _c(ws, f'=IF(D{i},MAX(0,{S}-3*G{i}*{Z}),"")', fmt=PCT),
                           f"=IF(D{i},F{i}>J{i},FALSE)"])
            ws.append([])

    # ---- Recovery ---------------------------------------------------------------------------------
    def recovery(self):
        ws = self.wb.create_sheet("Recovery")
        _widths(ws, [30, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13])
        T, A = self.tx, self.A
        mk = list(self.res["recovery"]["markets"].country)
        nm = self.nm
        self.R = {}
        ws.append([_c(ws, "Recovery scenarios: USD card, excluding extreme-volume anomalies", T_FONT)])
        ws.append([_c(ws, "Additional successes = attempts × MAX(failure rate − target, 0), valued at fee per successful attempt. "
                       "Scenarios, not forecasts.", NOTE)])
        ws.append([])
        _hdr(ws, ["Market", "Attempts", "Failed", "Successful", "Fees", "Failed fees", "Successful fees", "Failure rate",
                  "Fee per success", "MM attempts", "MM failed", "MM rate", "Best 3-month", "Target: conservative", "Target: base",
                  "Target: optimistic", "Addl. successes (base)", "Incremental fees (base)"])
        f0 = 5
        lN = f0 + len(mk) - 1
        tot = lN + 1
        wb0 = tot + 7   # row before the first best-window row
        for k, c in enumerate(mk):
            i = f0 + k
            q = f'{T("J")},$A{i},{T("E")},"card",{T("I")},"USD",{T("AF")},FALSE'
            qm = f'{T("J")},$A{i},{T("E")},"mobilemoney",{T("AF")},FALSE'
            wrow = wb0 + 1 + k
            ws.append([c, _c(ws, f"=SUMIFS({T('P')},{q})", fmt=INT), _c(ws, f"=SUMIFS({T('Q')},{q})", fmt=INT),
                       _c(ws, f"=SUMIFS({T('R')},{q})", fmt=INT), _c(ws, f"=SUMIFS({T('T')},{q})", fmt=USD),
                       _c(ws, f"=SUMIFS({T('W')},{q})", fmt=USD), _c(ws, f"=E{i}-F{i}", fmt=USD), _c(ws, f"=C{i}/B{i}", fmt=PCT),
                       _c(ws, f"=IF(D{i}>={A['min_succ']},G{i}/D{i},$G${tot}/$D${tot})", fmt=USD2),
                       _c(ws, f"=SUMIFS({T('P')},{qm})", fmt=INT), _c(ws, f"=SUMIFS({T('Q')},{qm})", fmt=INT),
                       _c(ws, f"=K{i}/J{i}", fmt=PCT),
                       _c(ws, f'=IFERROR(MIN(${L(2 + 2 * nm)}{wrow}:${L(1 + 3 * nm)}{wrow})*1,"")', fmt=PCT),
                       _c(ws, f"=M{i}", fmt=PCT), _c(ws, f"=L{i}", fmt=PCT), _c(ws, f"=MAX(0,L{i}-{A['margin']})", fmt=PCT),
                       _c(ws, f"=B{i}*MAX(H{i}-O{i},0)", fmt=INT), _c(ws, f"=Q{i}*I{i}", fmt=USD)])
        sm = lambda col: f"=SUM({col}{f0}:{col}{lN})"
        ws.append([_c(ws, "All markets", BOLD)] + [_c(ws, sm(L(j)), BOLD, INT if j <= 4 else USD) for j in range(2, 8)]
                  + [_c(ws, f"=C{tot}/B{tot}", BOLD, PCT), _c(ws, f"=G{tot}/D{tot}", BOLD, USD2)] + [None] * 7
                  + [_c(ws, sm("Q"), BOLD, INT), _c(ws, sm("R"), BOLD, USD)])
        self.R["addressable"] = f"Recovery!$F${tot}"
        ws.append([])
        sr = tot + 2
        _hdr(ws, ["Scenario", "Additional successes", "Incremental fees", "Annual run-rate", "Share of recorded fees",
                  "Share of addressable failed fees"])
        # placeholder rows written after the window block would break streaming order, so compute inline
        for k, (name, col) in enumerate([("Conservative", "N"), ("Base", "O"), ("Optimistic", "P")]):
            i = sr + 1 + k
            add = f"SUMPRODUCT($B${f0}:$B${lN},(($H${f0}:$H${lN}-{col}{f0}:{col}{lN})>0)*($H${f0}:$H${lN}-{col}{f0}:{col}{lN}))"
            inc = (f"SUMPRODUCT($B${f0}:$B${lN},(($H${f0}:$H${lN}-{col}{f0}:{col}{lN})>0)*($H${f0}:$H${lN}-{col}{f0}:{col}{lN}),"
                   f"$I${f0}:$I${lN})")
            ws.append([name, _c(ws, f"={add}", fmt=INT), _c(ws, f"={inc}", fmt=USD), _c(ws, f"=C{i}*12/{nm}", fmt=USD),
                       _c(ws, f"=C{i}/{self.S['fees']}", fmt=PCT), _c(ws, f"=C{i}/$F${tot}", fmt=PCT)])
            self.R[name] = f"Recovery!$C${i}"
            self.R[name + "_add"] = f"Recovery!$B${i}"
        assert sr + 4 == wb0 - 1 or True
        # best-window block
        hdr = ["Market"] + [f"Attempts {p:%b %y}" for p in self.periods] + [f"Failed {p:%b %y}" for p in self.periods] + \
              [f"3-month rate to {p:%b %y}" for p in self.periods]
        ws.append([_c(ws, "Best 3-month window (USD card, non-anomalous)", BOLD)])
        _hdr(ws, hdr)
        while True:
            break
        for k, c in enumerate(mk):
            i = sr + 6 + k
            row = [c]
            for m, per in enumerate(self.periods):
                q = f'{T("J")},$A{i},{T("E")},"card",{T("I")},"USD",{T("AF")},FALSE,{T("A")},DATE({per.year},{per.month},1)'
                row.append(f"=SUMIFS({T('P')},{q})")
            for m, per in enumerate(self.periods):
                q = f'{T("J")},$A{i},{T("E")},"card",{T("I")},"USD",{T("AF")},FALSE,{T("A")},DATE({per.year},{per.month},1)'
                row.append(f"=SUMIFS({T('Q')},{q})")
            for m in range(nm):
                if m < 2:
                    row.append('=""')
                else:
                    a = f"SUM({L(2 + m - 2)}{i}:{L(2 + m)}{i})"
                    fl = f"SUM({L(2 + nm + m - 2)}{i}:{L(2 + nm + m)}{i})"
                    row.append(_c(ws, f'=IF({a}>={A["win_min"]},{fl}/{a},"")', fmt=PCT))
            ws.append(row)
        self._win_row0 = sr + 6
        ws.append([])
        i0 = sr + 6 + len(mk) + 1
        ws.append([_c(ws, "Fee revenue remaining after assumed processing costs (base case, 28 months; other operating costs not included)", BOLD)])
        _hdr(ws, ["Assumed processing cost ratio", "Fee revenue remaining"])
        for k in range(len(self.cfg["recovery"]["cost_ratios"])):
            i = i0 + 2 + k
            ws.append([_c(ws, f"={A[f'cost{k + 1}']}", LINK_FONT, PCT), _c(ws, f"={self.R['Base']}*(1-A{i})", fmt=USD)])
        i = i0 + 2 + len(self.cfg["recovery"]["cost_ratios"])
        ws.append([_c(ws, "Break-even cost per additional success", BOLD), _c(ws, f"={self.R['Base']}/{self.R['Base_add']}", BOLD, USD2)])
        self.R["breakeven"] = f"Recovery!$B${i}"
        self.R["_wb0"] = wb0

    # ---- FX ---------------------------------------------------------------------------------------
    def fx(self):
        ws = self.wb.create_sheet("FX")
        _widths(ws, [32, 15, 15, 15, 15, 15])
        T, A, rm = self.tx, self.A, self.rm
        self.F = {}
        ws.append([_c(ws, "Foreign-currency translation", T_FONT)])
        ws.append([_c(ws, "Reported = monthly average rates. Constant = each currency's 2022 average. Differences are translation effects, "
                       "not realised FX gains or losses.", NOTE)])
        ws.append([])
        _hdr(ws, ["Measure", "Reported", "2022 constant currency", "Difference"])
        ws.append(["Fees on failed transactions", _c(ws, f"=SUM({T('W')})", fmt=USD), _c(ws, f"=SUM({T('X')})", fmt=USD), _c(ws, "=B5-C5", fmt=USD)])
        ws.append(["Successful-transaction fees", _c(ws, f"=SUM({T('T')})-B5", fmt=USD), _c(ws, f"=SUM({T('U')})-C5", fmt=USD), _c(ws, "=B6-C6", fmt=USD)])
        ws.append(["Local-currency fees (all statuses)", _c(ws, f'=SUMIFS({T("T")},{T("I")},"<>USD",{T("N")},TRUE)', fmt=USD),
                   _c(ws, f'=SUMIFS({T("U")},{T("I")},"<>USD",{T("N")},TRUE)', fmt=USD), _c(ws, "=B7-C7", fmt=USD)])
        self.F.update(failed_constant="FX!$C$5", local_reported="FX!$B$7", local_constant="FX!$C$7")
        ws.append([])
        ws.append([_c(ws, "By currency", BOLD)])
        _hdr(ws, ["Currency", "Reported", "2022 constant currency", "Translation effect", "Rate change, first to last month"])
        main = ["GHS", "NGN", "KES", "TZS", "UGX", "ZMW"]
        lastcol = L(1 + self.nm)
        for k, c in enumerate(main):
            i = 11 + k
            ar = f"MATCH($A{i},{rm['ccys']},0)"
            ws.append([c, _c(ws, f'=SUMIFS({T("T")},{T("I")},A{i},{T("N")},TRUE)', fmt=USD),
                       _c(ws, f'=SUMIFS({T("U")},{T("I")},A{i},{T("N")},TRUE)', fmt=USD), _c(ws, f"=B{i}-C{i}", fmt=USD),
                       _c(ws, f"=INDEX({rm['avg']},{ar},{self.nm})/INDEX({rm['avg']},{ar},1)-1", fmt=PCT)])
            self.F[c] = f"FX!$D${i}"
        i = 11 + len(main)
        ws.append(["All other", _c(ws, f"=B7-SUM(B11:B{i - 1})", fmt=USD), _c(ws, f"=C7-SUM(C11:C{i - 1})", fmt=USD), _c(ws, f"=B{i}-C{i}", fmt=USD)])
        ws.append([])
        y0 = i + 4
        ws.append([_c(ws, "By year (local-currency fees)", BOLD)])
        _hdr(ws, ["Year", "Reported", "2022 constant currency", "Translation effect"])
        for k, y in enumerate(sorted({p.year for p in self.periods})):
            j = y0 + k
            d = f'{T("A")},">="&DATE(A{j},1,1),{T("A")},"<="&DATE(A{j},12,31)'
            ws.append([_c(ws, str(y)) if False else y, _c(ws, f'=SUMIFS({T("T")},{T("I")},"<>USD",{T("N")},TRUE,{d})', fmt=USD),
                       _c(ws, f'=SUMIFS({T("U")},{T("I")},"<>USD",{T("N")},TRUE,{d})', fmt=USD), _c(ws, f"=B{j}-C{j}", fmt=USD)])
        ws.append([])
        s0 = y0 + len({p.year for p in self.periods}) + 3
        ws.append([_c(ws, "High–low screen on monthly average rates", BOLD)])
        _hdr(ws, ["Currency", "Months", "Months above screen", "Average range", "Largest range"])
        rng = rm["range"]
        for k, c in enumerate(["NGN", "GHS", "ZMW", "KES", "TZS", "UGX"]):
            j = s0 + k
            row = f"INDEX({rng},MATCH($A{j},{rm['ccys']},0),0)"
            ws.append([c, _c(ws, f"=COUNT({row})", fmt=INT), _c(ws, f'=COUNTIF({row},">"&{A["screen"]})', fmt=INT),
                       _c(ws, f"=AVERAGE({row})", fmt=PCT), _c(ws, f"=MAX({row})", fmt=PCT)])
            self.F["ias_" + c] = f"FX!$C${j}"

    # ---- Checks -----------------------------------------------------------------------------------
    def checks(self):
        ws = self.wb.create_sheet("Checks")
        _widths(ws, [46, 18, 18, 14, 10])
        res, S, J, R, F = self.res, self.S, self.J, self.R, self.F
        h, b = res["headline"], res["bridge"].set_index("category").f_fee
        ws.append([_c(ws, "Checks against the Python pipeline", T_FONT)])
        ws.append([_c(ws, "Python values are written by excel.py from the same run; Excel values are live formulas. Tolerance $1 or 0.01%.", NOTE)])
        _hdr(ws, ["Figure", "Excel", "Python", "Difference", "Status"])
        j = res["january"]
        items = [("Records", S["records"], h["records"], INT), ("Payment attempts", S["attempts"], h["attempts"], INT),
                 ("Failed attempts", S["failed"], h["failed"], INT), ("Records without a rate", S["untranslatable"], res["stats"]["untranslatable_records"], INT),
                 ("Attempts with a rate", S["attempts_translatable"], h["attempts_translatable"], INT),
                 ("Recorded fees", S["fees"], h["fees"], USD), ("Fees on failed transactions", S["failed_fees"], h["failed_fees"], USD),
                 ("Successful-transaction fees", S["succ_fees"], h["succ_fees"], USD),
                 ("Fee-ratio flags", S["flag_fee_ratio"], res["stats"]["flag_fee_ratio"], INT),
                 ("Missing-fee flags", S["flag_missing_fee"], res["stats"]["flag_missing_fee"], INT),
                 ("Value flags", S["flag_value"], res["stats"]["flag_value"], INT),
                 ("Transaction value, excluding flagged", S["value"], res["value"]["value"], USD),
                 ("Bridge: extreme-volume anomalies", S["bridge_Extreme-volume anomaly"], b["Extreme-volume anomaly"], USD),
                 ("Bridge: escalation", S["bridge_Escalation"], b["Escalation"], USD),
                 ("Bridge: remaining exposure", S["bridge_Remaining"], b["Remaining"], USD),
                 ("Card share of failed fees", S["card_share"], res["channels"].set_index("pt").share_of_failed_fees["card"], PCT)]
        for comp, v in zip(j["components"].component, j["components"].usd):
            items.append((f"January: {comp}", J[comp], v, USD))
        items.append(("January: residual", J["Residual"], j["residual"], "0.0000"))
        for name in ["Conservative", "Base", "Optimistic"]:
            items.append((f"Recovery: {name.lower()} incremental fees", R[name],
                          res["recovery"]["scenarios"].set_index("scenario").incremental_fees[name], USD))
        items.append(("Recovery: break-even per additional success", R["breakeven"], res["recovery"]["breakeven"], USD2))
        items.append(("Recovery: addressable failed fees", R["addressable"], res["recovery"]["addressable_f_fee"], USD))
        items.append(("FX: failed fees at 2022 rates", F["failed_constant"], res["fx"]["measures"].constant.iloc[0], USD))
        items.append(("FX: local-currency fees, reported", F["local_reported"], res["fx"]["local_reported"], USD))
        items.append(("FX: local-currency fees, constant", F["local_constant"], res["fx"]["local_constant"], USD))
        bc = res["fx"]["by_currency"].set_index("ccy").effect
        for c in ["GHS", "NGN", "KES"]:
            items.append((f"FX: {c} translation effect", F[c], bc[c], USD))
        ias = res["fx"]["ias_screen"].set_index("ccy").months_above
        for c in ["NGN", "GHS", "ZMW", "KES", "TZS", "UGX"]:
            items.append((f"FX screen: {c} months above", F["ias_" + c], ias[c], INT))
        pat = res["laney"]["patterns"]
        for r in pat.itertuples():
            i = self.L[(r.country, r.pt)]
            items.append((f"Laney: {r.country} {r.pt} signals", f"Laney!$K${i}", r.signals, INT))
            items.append((f"Laney: {r.country} {r.pt} σz", f"Laney!$F${i}", r.sigma_z, "0.000"))
        for k, (lab, ref, py, fmt) in enumerate(items, start=4):
            ws.append([lab, _c(ws, f"={ref}", LINK_FONT, fmt), _c(ws, float(py), IN_FONT, fmt), _c(ws, f"=B{k}-C{k}", fmt=fmt),
                       f'=IF(ABS(D{k})<=MAX(1,ABS(C{k}))*0.0001+IF(ABS(C{k})>100,1,0.000001),"OK","CHECK")'])
        n = 3 + len(items)
        ws.append([])
        ws.append([_c(ws, "Rows OK", BOLD), _c(ws, f'=COUNTIF(E4:E{n},"OK")', BOLD, INT), _c(ws, f"of {len(items)}", BOLD)])

    # ---- build ------------------------------------------------------------------------------------
    def build(self, path):
        self.readme()
        self.assumptions()
        self.rates_daily()          # also fixes Rates_Monthly layout
        self.rates_monthly()
        self.customers()
        self.anomaly_layout()
        self.transactions()
        self.anomaly_sheet()
        self.summary()
        self.january()
        self.laney()
        self.recovery()
        self.fx()
        self.checks()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.wb.save(path)
        return path


def build_workbook(prep, res, cfg, path) -> Path:
    return Book(cfg, prep, res).build(path)
