"""The sceptical-reviewer checks of stage 11 (audit items 1-8). Each finding is PASS, FAIL or FLAG; nothing is changed here."""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from . import textscan
from .config import ROOT
from .pipeline import OUT, load_figure_index

CONTENT = ROOT / "report" / "content"
TEXT_FILES = ["03_main_report.md", "01_summary.md", "02_at_a_glance.html", "brief.html", "00_cover.html"]
TOKEN = re.compile(r"\{\{(\w+)\}\}")


def _rel(a, b, tol=1e-7) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(b))


def _plain(html: str) -> str:
    from bs4 import BeautifulSoup
    s = BeautifulSoup(html, "html.parser")
    for t in s(["style", "script", "svg", "math"]):
        t.decompose()
    return re.sub(r"\s+", " ", s.get_text(" "))


def _sentences(text: str) -> list[str]:
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+(?=[A-Z$\d(*])", text) if len(x.strip()) > 20]


def _report_text(name: str) -> str:
    f = OUT / "report" / name
    return _plain(f.read_text(encoding="utf-8")) if f.exists() else ""


# --------------------------------------------------------------------------------------- item 1
def independent(au, res: dict, cfg: dict) -> None:
    from . import independent as ind
    S = "1. Independent recomputation (plain pandas from data/raw)"
    try:
        r = ind.compute(Path(cfg["_root"]) / cfg["data"]["workbook"])
    except Exception as e:                                            # pragma: no cover
        au.add(S, "Independent recomputation ran", False, f"{type(e).__name__}: {e}")
        return
    h = res["headline"]
    for k in ["records", "attempts", "failed", "records_translatable"]:
        au.add(S, f"Headline {k}", r[k] == h[k], f"independent {r[k]:,} vs pipeline {h[k]:,}")
    for k in ["fees", "failed_fees", "succ_fees", "fee_share", "count_rate"]:
        au.add(S, f"Headline {k}", _rel(r[k], h[k]), f"independent {r[k]:,.6f} vs pipeline {h[k]:,.6f}")
    b = res["bridge"].set_index("category").f_fee
    for a, k in [("Extreme", "Extreme-volume anomaly"), ("Escalation", "Escalation"), ("Remaining", "Remaining")]:
        au.add(S, f"Exposure bridge: {k}", _rel(r["bridge"][a], b[k]), f"independent ${r['bridge'][a]:,.2f} vs pipeline ${b[k]:,.2f}")
    au.add(S, "Extreme-volume observations and escalation account", r["extreme_observations"] == 20 and r["escalation_customers"] == [47087],
           f"{r['extreme_observations']} observations; escalation {r['escalation_customers']}")
    m = res["monthly"]
    au.add(S, "Monthly remaining-exposure failure range is 48-61%",
           round(r["remaining_rate_min"] * 100) == 48 and round(r["remaining_rate_max"] * 100) == 61 and _rel(r["remaining_rate_min"], m.count_rem.min())
           and _rel(r["remaining_rate_max"], m.count_rem.max()), f"independent {r['remaining_rate_min']:.4f}-{r['remaining_rate_max']:.4f}; pipeline {m.count_rem.min():.4f}-{m.count_rem.max():.4f}")
    heat = res["heat"].set_index(["country", "pt"]).fail_rate
    bad = [f"{k}" for k in r["rate_by_cell"] if k[1] in ("card", "mobilemoney") and not _rel(r["rate_by_cell"][k], heat[k])]
    n = sum(1 for k in r["rate_by_cell"] if k[1] in ("card", "mobilemoney"))
    au.add(S, "Card and mobile money failure rate by market", not bad, f"{n} market-channel cells compared" + (f"; differ: {bad}" if bad else ""))
    j, rj = res["january"], r["january"]
    comp = j["components"].set_index("component").usd
    pairs = [("Baseline", rj["baseline"], comp["Baseline"]), ("January", rj["january"], comp["January"]),
             ("Extreme-volume anomalies", rj["extreme"], comp["Extreme-volume anomalies"]), ("FX translation", rj["fx"], comp["FX translation"]),
             ("Volume", rj["Volume"], comp["Volume"]), ("Mix", rj["Mix"], comp["Mix"]), ("Failure rate", rj["Failure rate"], comp["Failure rate"]),
             ("Fee yield", rj["Fee yield"], comp["Fee yield"]), ("Entry/exit cells", rj["entry_exit"], comp["Entry/exit cells"])]
    bad = [f"{n_}: {a:,.2f} vs {b_:,.2f}" for n_, a, b_ in pairs if not _rel(a, b_, 1e-6)]
    au.add(S, "January bridge (baseline, anomalies, FX, four LMDI effects, entry/exit)", not bad, "; ".join(bad) or f"9 components agree; independent residual {rj['residual']:.2e}")
    rc = res["recovery"]
    base = rc["scenarios"].set_index("scenario").incremental_fees["Base"]
    au.add(S, "Base-case recovery", _rel(r["recovery"]["base"], base), f"independent ${r['recovery']['base']:,.2f} vs pipeline ${base:,.2f}")
    bx = rc["benchmark_ex_escalation"]
    au.add(S, "Benchmark sensitivity without account 47087 ($324.1K; Kenya mobile money 56.3% vs 68.6%)",
           _rel(r["recovery"]["ex_escalation"], bx["incremental"]) and round(r["recovery"]["ex_escalation"] / 1e3, 1) == 324.1
           and round(r["recovery"]["kenya_mm_ex"] * 100, 1) == 56.3 and round(r["recovery"]["kenya_mm"] * 100, 1) == 68.6,
           f"independent ${r['recovery']['ex_escalation']:,.2f}; Kenya {r['recovery']['kenya_mm_ex']:.1%} vs {r['recovery']['kenya_mm']:.1%}")
    cc, pc = r["cc"], res["customer_concentration"]
    au.add(S, "Customer concentration (5,108 with failed fees of 5,657; top 10 50.4%; top 1% = 51 customers, 70.4%)",
           cc["customers"] == pc["customers"] == 5108 and cc["transacting"] == 5657 and cc["top1pct_n"] == 51 and _rel(cc["top10"], pc["top10"])
           and _rel(cc["top1pct"], pc["top1pct"]) and round(cc["top10"] * 100, 1) == 50.4 and round(cc["top1pct"] * 100, 1) == 70.4,
           f"{cc['customers']:,} of {cc['transacting']:,}; top 10 {cc['top10']:.1%}; top 1% = {cc['top1pct_n']} customers, {cc['top1pct']:.1%}")
    # the thresholds typed into independent.py equal the assumptions file
    a, e = cfg["anomalies"]["relative"], cfg["anomalies"]["escalation"]
    same = (a["min_failed"], a["multiple_of_prior_median"], a["max_success_rate"], a["lookback_months"], e["min_failed"], e["max_success_rate"],
            cfg["fx"]["spike_ratio"]) == (ind.T["rel_min"], ind.T["rel_mult"], ind.T["rel_succ"], ind.T["lookback"], ind.T["esc_min"], ind.T["esc_succ"], ind.T["spike"])
    au.add(S, "Thresholds used by the independent check equal config/assumptions.yaml", same)


# --------------------------------------------------------------------------------------- item 2
def _num_value(lit: str) -> float | None:
    t = lit.replace("−", "-").replace("–", "-").replace(",", "").replace("$", "").strip()
    m = re.match(r"^-?\d+(\.\d+)?", t)
    if not m:
        return None
    v = float(m.group(0))
    return v / 100 if "%" in t else v


def _cfg_get(cfg, path: str):
    cur = cfg
    for p in path.split("."):
        cur = cur[int(p)] if isinstance(cur, list) else cur[p]
    return cur


def numbers_in_text(au, res: dict, cfg: dict, ctx: dict) -> None:
    S = "2. Every number in the text"
    allow = yaml.safe_load((CONTENT / "number_allowlist.yaml").read_text(encoding="utf-8"))
    pats = [(re.compile(p["re"]), p.get("near")) for p in allow.get("patterns", [])]
    lits = allow.get("literals", [])
    words = [re.compile(w, re.I) for w in allow.get("words", [])]
    # config cross-check of the allow-list
    bad_cfg = []
    for e in lits:
        if "config" in e:
            try:
                v, w = _cfg_get(cfg, e["config"]), _num_value(e["literal"]) * e.get("scale", 1)
                if v is None or w is None or not np.isclose(float(v), w, rtol=1e-9, atol=1e-9):
                    bad_cfg.append(f"{e['literal']} vs {e['config']}={v}")
            except Exception:
                bad_cfg.append(f"{e['literal']} ({e['config']} not found)")
    au.add(S, "Allow-listed thresholds equal config/assumptions.yaml", not bad_cfg, "; ".join(bad_cfg) or f"{sum('config' in e for e in lits)} thresholds checked")
    flagged = []
    for f in TEXT_FILES:
        for row in textscan.scan(CONTENT / f):
            lit = row["literal"].strip(" ,.;:")
            ctxt = row["context"]
            if row.get("words"):
                if any(w.search(lit) for w in words):
                    continue
                flagged.append(row)
                continue
            ok = any(p.match(lit) and (n is None or n in ctxt) for p, n in pats) or any(e["literal"] == lit and (e.get("near") is None or e["near"] in ctxt) for e in lits)
            if not ok:
                flagged.append(row)
    pd.DataFrame(flagged).to_csv(OUT / "audit_typed_numbers.csv", index=False)
    by_file = pd.Series([r["file"] for r in flagged]).value_counts().to_dict() if flagged else {}
    ex = "; ".join(f"{r['file']}:{r['line']} {r['literal']}" for r in flagged[:8])
    au.add(S, "No typed number outside the allow-list (computed numbers must be {{tokens}})", not flagged,
           f"{len(flagged)} typed numbers not on the allow-list {by_file}. Full list: outputs/audit_typed_numbers.csv. First: {ex}", flag=True)
    # tokens used in the text all resolve
    used = set()
    for f in TEXT_FILES:
        used |= set(TOKEN.findall((CONTENT / f).read_text(encoding="utf-8")))
    special = {k for k in used if k.startswith(("fig:", "tab:"))}
    missing = sorted(k for k in used - special if k not in ctx and not k.startswith("meta."))
    au.add(S, "Every {{token}} in the content resolves to a value", not missing, ", ".join(missing[:8]))
    # a token's rendered value against results.json (formatted independently of report.context)
    j = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    h = j["headline"]
    exp = {"failed_fees_m": f"${h['failed_fees'] / 1e6:,.2f}M", "fees_m": f"${h['fees'] / 1e6:,.2f}M", "attempts": f"{h['attempts']:,}",
           "failed": f"{h['failed']:,}", "count_rate": f"{h['count_rate'] * 100:.1f}%", "fee_share": f"{h['fee_share'] * 100:.1f}%",
           "records": f"{h['records']:,}", "records_tr": f"{h['records_translatable']:,}", "succ_fees_k": f"${h['succ_fees'] / 1e3:,.1f}K",
           "customers_failed": f"{j['customer_concentration']['customers']:,}", "top1pct_n": f"{j['customer_concentration']['top1pct_n']:,}",
           "top1pct": f"{j['customer_concentration']['top1pct'] * 100:.1f}%", "top10": f"{j['customer_concentration']['top10'] * 100:.1f}%"}
    bad = [f"{k}: {ctx.get(k)} vs {v}" for k, v in exp.items() if ctx.get(k) != v]
    au.add(S, "Key tokens agree with results.json (formatted independently)", not bad, "; ".join(bad) or f"{len(exp)} tokens agree")


# --------------------------------------------------------------------------------------- item 3
TERMS = [
    ("Extreme-volume anomalies", [r"(?<!extreme-volume )(?<!value )(?<!Extreme-volume )(?<!non-)\banomal(?:y|ies)\b(?! (?:in|of) the (?:supplied )?data)", r"\bextreme accounts?\b",
                                  r"\banomalous accounts?\b", r"\bextreme (?:account behaviour|customer-months|failure volumes)\b", r"\bnon-anomalous\b"]),
    ("The escalation account (47087)", [r"\bescalation accounts?\(s\)", r"\bescalating account\b", r"\bEscalation account\(s\)"]),
    ("Remaining exposure", [r"\bpersistent card failure\b", r"\bpersistent card-completion problem\b", r"\bremaining (?:problem|failed-fee exposure)\b", r"\bunderlying failure\b"]),
    ("Fees on failed transactions", [r"\bfees on failed payments\b", r"\bfailed-transaction fees\b", r"\bFees on failed payments\b", r"\blost revenue\b(?! or cash)"]),
    ("Successful-transaction fees", [r"\bfees on successful payments\b", r"\bfees earned on successful payments\b", r"\bsuccessful fees\b", r"\bsuccessful-transaction fee revenue\b",
                                     r"\bsuccessful-transaction fee\b(?! revenue)"]),
]


def terminology(au, res: dict, cfg: dict) -> None:
    S = "3. Terminology"
    corpus = {f: " ".join(l for _, l in textscan.clean_lines(CONTENT / f)) for f in TEXT_FILES}
    corpus["figure titles"] = " ".join(load_figure_index().title)
    src = (ROOT / "src" / "payfail" / "figures.py").read_text(encoding="utf-8")
    corpus["figures.py (titles, legends)"] = " ".join(re.findall(r'"([A-Z][^"]{12,})"', src))
    corpus["dashboard"] = (ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8")
    corpus["README.md"] = (ROOT / "README.md").read_text(encoding="utf-8")
    ex_file = OUT / "payment_failure_analysis.xlsx"
    for concept, pats in TERMS:
        hits = []
        for name, text in corpus.items():
            for p in pats:
                for m in re.finditer(p, text):
                    hits.append(f"{name}: '{text[max(0, m.start() - 25):m.end() + 20].strip()}'")
        au.add(S, f"One term for: {concept}", not hits, f"{len(hits)} variant uses. " + " | ".join(hits[:4]), flag=True)


# --------------------------------------------------------------------------------------- items 4 and 5
CUES = {"attempts": r"\battempts?\b|\bcount\b", "records": r"\brecords?\b", "fees": r"\bfees?\b|\bfee\b", "customers": r"\bcustomers?\b|\baccounts?\b",
        "translatable": r"translatable", "non-anomalous": r"non-anomalous|excluding|outside the", "all": r"\ball (?:records|activity)\b|whole period|overall"}


def denominators(au) -> None:
    S = "4. Denominators"
    text = _report_text("The_Economics_of_Payment_Failure.html")
    rows, unstated, mixed = [], [], []
    for s in _sentences(text):
        pcts = re.findall(r"\d+(?:\.\d+)?%", s)
        if not pcts or s.startswith(("Table ", "Figure ")) and len(s) < 60:
            continue
        cues = {k for k, p in CUES.items() if re.search(p, s, re.I)}
        rows.append({"sentence": s[:220], "percentages": len(pcts), "population_cues": ", ".join(sorted(cues))})
        if not cues:
            unstated.append(s[:140])
        if len(pcts) >= 2 and re.search(r"\b(?:against|versus|compared|than|from .* to)\b", s) and {"attempts", "customers", "fees"} <= cues:
            mixed.append(s[:160])
    pd.DataFrame(rows).to_csv(OUT / "audit_percentages.csv", index=False)
    au.add(S, "Every sentence with a percentage states or implies its population", not unstated,
           f"{len(rows)} sentences with a percentage; {len(unstated)} without any population cue (list in outputs/audit_percentages.csv): " + " | ".join(unstated[:3]), flag=True)
    au.add(S, "No comparison sets two different populations without saying so", not mixed, f"{len(mixed)} to read: " + " | ".join(mixed[:3]), flag=True)


def units(au, res: dict) -> None:
    S = "5. Units and periods"
    text = _report_text("The_Economics_of_Payment_Failure.html") + " " + _report_text("Executive_Brief.html")
    sus = []
    for s in _sentences(text):
        annual = re.search(r"\ba year\b|\bannual(?:ly| run-rate| equivalent)?\b|per year", s, re.I)
        period = re.search(r"\b28 months\b|over the period|whole period|28-month", s, re.I)
        cmp_ = re.search(r"\b(?:against|versus|compared|vs\.?|add|adds|than)\b", s, re.I)
        if annual and period and cmp_ and not re.search(r"annual equivalent|× ?12|12/28|from \$", s):
            sus.append(s[:170])
    au.add(S, "No sentence compares an annual figure with a 28-month figure", not sus, f"{len(sus)} to read: " + " | ".join(sus[:3]), flag=True)
    idx = load_figure_index()
    f22 = (ROOT / "src" / "payfail" / "figures.py").read_text(encoding="utf-8")
    ok = "annual equivalent" in f22 and "annual_actual = res[\"headline\"][\"succ_fees\"] * 12" in f22
    au.add(S, "Figure 14 reference line is the annual equivalent of successful-transaction fees (not the 28-month total)", ok)
    sc = res["recovery"]["scenarios"].set_index("scenario")
    n = len(res["monthly"])
    au.add(S, "Annual run-rate = 28-month total x 12/28", all(_rel(sc.annual[k], sc.incremental_fees[k] * 12 / n) for k in sc.index), f"{n} months")


# --------------------------------------------------------------------------------------- item 6
def claims(au, res: dict, prep) -> None:
    S = "6. Claims against the data"
    tx = prep.tx
    obs = res["anomalies"]["observations"]
    def add(name, ok, detail=""):
        au.add(S, name, bool(ok), detail)
    last = tx[tx.customer_id == 49957].period.max()
    add("Account 49957 recorded no activity after January 2024", last == pd.Timestamp("2024-01-01"), f"last month {last:%b %Y}")
    s = res["anomalies"]["escalation_series"].set_index("period")
    add("Account 47087: 199 failed attempts in October 2023", int(s.f_att[pd.Timestamp("2023-10-01")]) == 199, int(s.f_att[pd.Timestamp("2023-10-01")]))
    add("Account 47087: no more than 90 successes in any month", int(s.s_att.max()) <= 90, f"maximum {int(s.s_att.max())}")
    e47 = obs[obs.customer_id == 47087]
    add("Only account 47087's January 2024 observation crossed the relative rule", len(e47) == 1 and e47.iloc[0].period == pd.Timestamp("2024-01-01"), f"{len(e47)} observation(s)")
    t47 = tx[tx.customer_id == 47087]
    add("Account 47087 is a Kenyan merchant taking GHS mobile money", set(t47.country) == {"Kenya"} and (lambda d: d[d.ccy == "GHS"].att.sum() / d.att.sum())(t47[t47.pt == "mobilemoney"]) > 0.9,
        f"country {set(t47.country)}; GHS share of mobile money attempts {(lambda d: d[d.ccy == 'GHS'].att.sum() / d.att.sum())(t47[t47.pt == 'mobilemoney']):.0%}")
    nb47 = t47[~t47.extreme]
    mm, card = nb47[nb47.pt == "mobilemoney"].att.sum(), nb47[(nb47.pt == "card") & (nb47.ccy == "USD")].att.sum()
    add("Account 47087: more than 100,000 non-anomalous mobile money attempts and a few dozen USD card attempts", mm > 100_000 and 12 <= card <= 99, f"{mm:,} mobile money attempts; {card:,} USD card attempts")
    top4 = obs.head(4)
    add("Four largest extreme-volume account-months are all card, had no successes, and carry most of the anomaly exposure",
        (top4.pt == "card").all() and (top4.s_att == 0).all() and top4.f_fee.sum() / obs.f_fee.sum() > 0.5, f"{top4.f_fee.sum() / obs.f_fee.sum():.0%} of {len(obs)} observations' fees")
    early = obs[(obs.period >= "2022-01-01") & (obs.period <= "2023-07-01")]
    months_early = sorted(early.period.dt.strftime("%Y-%m").unique())
    later = obs[obs.period > "2023-12-01"]
    add("Extreme-volume observations in Feb and Apr 2024 and in six months between Jan 2022 and Jul 2023",
        len(months_early) == 6 and {"2024-02", "2024-04"} <= set(later.period.dt.strftime("%Y-%m")), f"early months {months_early}; later {sorted(set(later.period.dt.strftime('%Y-%m')))}")
    jan = tx[(tx.period == "2024-01-01")]
    for c in (51026, 49477):
        after = tx[(tx.customer_id == c) & (tx.period > "2024-01-01")].att
        add(f"Account {c} fell back to a handful of attempts after January", after.max() <= 50 if len(after) else True, f"max monthly attempts after January: {int(after.max()) if len(after) else 0}")
    add("Account 49957 produced an extreme-volume observation in December 2023", ((obs.customer_id == 49957) & (obs.period == "2023-12-01")).any())
    lp = res["laney"]
    sig = lp["signals"]
    for cell, month, share in [(("Kenya", "mobilemoney"), "2024-04", 0.90), (("Ghana", "card"), "2023-05", 0.87)]:
        r = sig[(sig.country == cell[0]) & (sig.pt == cell[1]) & (sig.period == month + "-01")]
        add(f"Laney signal {cell[0]} {cell[1]} {month}: largest customer's share about {share:.0%}", len(r) == 1 and abs(r.iloc[0].top_customer_share - share) < 0.006,
            f"{r.iloc[0].top_customer_share:.1%}" if len(r) else "no signal")
    pat = lp["patterns"].set_index(["country", "pt"])
    typed = {("Kenya", "card"): ("Structural", "Episodic"), ("Uganda", "card"): ("Structural", "Episodic"), ("Kenya", "mobilemoney"): ("Deteriorating", "Episodic"),
             ("Tanzania", "card"): ("Structural",), ("Ghana", "card"): ("Structural", "Deteriorating", "Episodic"), ("Uganda", "mobilemoney"): ("Episodic",),
             ("Kenya", "alternative channels"): ("Structural",), ("Tanzania", "mobilemoney"): (), ("Zambia", "mobilemoney"): (), ("Ghana", "mobilemoney"): ("Unstable",)}
    badf = [f"{k}: computed {pat.loc[k]["flags"]}" for k, v in typed.items() if set(x.strip() for x in pat.loc[k]["flags"].split(",")) != (set(v) if v else {"Stable"})]
    add("Pattern flags typed in the Laney table equal the computed flags", not badf, "; ".join(badf) or "10 cells agree")
    zc = lp["excluded"].set_index(["country", "pt"]).eligible_months.get(("Zambia", "card"))
    add("Zambia card has fewer than 12 eligible months (limitations)", zc is not None and zc < 12, f"{zc} eligible months")
    ten = res["customers"]["tenure"]
    fr = ten.fail_rate.values
    add("Failure is U-shaped across tenure", fr[0] > fr[1:3].min() and fr[-1] > fr[1:3].min(), "rates " + ", ".join(f"{x:.1%}" for x in fr))
    fs = ten.fee_share
    add("Failed-fee share across tenure bands is flat at 85-88%", round(fs.min() * 100) == 85 and round(fs.max() * 100) == 88, f"{fs.min():.1%}-{fs.max():.1%}")
    jn = res["january"]
    add("January: failure-rate effect is favourable (negative) and Uganda card improved", jn["lmdi"]["Failure rate"] < 0, f"effect ${jn['lmdi']['Failure rate']:,.0f}")
    cells = jn["cells"].set_index(["country", "pt"])
    add("January: Uganda card failure rate fell and Tanzania card fee per failed attempt rose",
        cells.loc[("Uganda", "card")].rate1 < cells.loc[("Uganda", "card")].rate0 and cells.loc[("Tanzania", "card")].yield1 > cells.loc[("Tanzania", "card")].yield0)
    # share of the fee-yield effect from Tanzania card
    L = lambda a, b: np.where(np.isclose(a, b), a, (a - b) / (np.log(a) - np.log(b)))
    w = L(cells.f_cc1.values, cells.f_cc0.values)
    fy = pd.Series(w * np.log((cells.f_cc1 / cells.f_att1) / (cells.f_cc0 / cells.f_att0)).values, index=cells.index)
    add("January: the fee-yield rise is almost all Tanzania card", fy[("Tanzania", "card")] / fy.sum() > 0.8, f"Tanzania card = {fy[('Tanzania', 'card')] / fy.sum():.0%} of the fee-yield effect")
    add("January: the translation effect is small relative to the rise", abs(jn["fx_effect"]) < 0.05 * (jn["january_all"] - jn["baseline_all"]), f"${jn['fx_effect']:,.0f} against a ${jn['january_all'] - jn['baseline_all']:,.0f} rise")
    me = res["fx"]["measures"]
    pct = (me.difference / me.constant).abs()
    add("Both measures shrink by about 6% in dollar terms at constant currency", all(5.5 <= x * 100 < 6.5 for x in pct), ", ".join(f"{x:.1%}" for x in pct))
    mon = res["monthly"].set_index("period")
    y22 = tx[(tx.category == "Remaining") & (tx.period.dt.year == 2022)]
    y24 = tx[(tx.category == "Remaining") & (tx.period.dt.year == 2024)]
    s22, s24 = y22.f_fee.sum() / y22.fee.sum(), y24.f_fee.sum() / y24.fee.sum()
    m22, m24 = mon.share_rem[mon.index.year == 2022].mean(), mon.share_rem[mon.index.year == 2024].mean()
    add("Failed-fee share of remaining exposure drifts from about 89% (2022) to about 79% (2024), as the average of the monthly shares in Figure 2",
        round(m22 * 100) == 89 and round(m24 * 100) == 79, f"monthly averages {m22:.1%} and {m24:.1%}")
    au.add(S, "The 89% and 79% are said to be monthly averages (they are not the pooled yearly shares)", False,
           f"The text gives 'about 89% in 2022 to about 79% in 2024' without saying they are averages of the monthly shares. The pooled shares are {s22:.1%} (2022) and {s24:.1%} (2024); only the monthly averages round to 89% and 79%", flag=True)
    mk = res["recovery"]["markets"].set_index("country")
    add("Tanzania ranks second in the base case despite fewer attempts than Uganda", mk.incremental_base.rank(ascending=False)["Tanzania"] == 2 and mk.att["Tanzania"] < mk.att["Uganda"])
    ch = res["channels"].set_index("pt")
    add("Bank transfer is the one reliable channel", ch.fail_rate["bank transfer"] == ch.fail_rate[ch.att > 1000].min(), f"{ch.fail_rate['bank transfer']:.1%}")
    cm = res["matrix"].set_index(["country", "pt"])
    add("Card is structural: card cells' typical month fails at 84-93%", True, "see Laney medians: " + ", ".join(f"{k[0]} {v:.0%}" for k, v in pat.median_rate.items() if k[1] == "card"))
    meds = [v for k, v in pat.median_rate.items() if k[1] == "card"]
    add("Card cells' median monthly failure range rounds to 84-93%", round(min(meds) * 100) == 84 and round(max(meds) * 100) == 93, f"{min(meds):.1%}-{max(meds):.1%}")
    sens = res["sensitivity"].set_index("treatment").fee_share
    add("Failed-fee share holds at 89-90% under every data and translation choice", round(sens.iloc[:4].min() * 100) == 89 and round(sens.iloc[:4].max() * 100) == 90, ", ".join(f"{v:.1%}" for v in sens.iloc[:4]))
    add("Removing the anomaly categories moves the share to 85%", round(sens.iloc[-1] * 100) == 85 or round(sens.iloc[-2] * 100) == 85, f"{sens.iloc[-2]:.1%} and {sens.iloc[-1]:.1%}")
    rec = res["reconciliation"]
    add("Months with a failed-fee share below 78%: two on the corrected basis, none before the correction",
        len(rec["report_basis"]["months_below_78"]) == 2 and len(rec["no_sll_fix"]["months_below_78"]) == 0,
        f"corrected {rec['report_basis']['months_below_78']}; before {rec['no_sll_fix']['months_below_78']}")
    # the typed 'before the SLL correction' figures against the computed sensitivity run
    nf = rec["no_sll_fix"]
    au.add(S, "Typed 'before the SLL correction' figures ($3,148,908; $2,842,692; $744,744) match the computed fix-off run",
           round(nf["fees"]) == 3_148_908 and round(nf["failed_fees"]) == 2_842_692 and round(nf["jan_failed_fees"]) == 744_744,
           f"fix-off run gives ${nf['fees']:,.0f}, ${nf['failed_fees']:,.0f}, ${nf['jan_failed_fees']:,.0f}. The typed figures also had the rate-spike screen switched off; the difference is ${nf['failed_fees'] - 2_842_692:,.0f} on failed fees", flag=True)
    au.add(S, "Typed '$63.3K' removed by the SLL correction matches the computed difference", round(rec["sll_effect_failed_fees"] / 1e3, 1) == 63.3,
           f"computed ${rec['sll_effect_failed_fees']:,.0f}", flag=True)
    v = tx[tx.flag_value & tx.failed].sort_values("val", ascending=False).head(1)
    add("Largest value anomaly is a failed NGN record of 2.36 trillion over 24 attempts with a fee of NGN 314",
        len(v) == 1 and v.iloc[0].ccy == "NGN" and round(v.iloc[0].total_value / 1e12, 2) == 2.36 and int(v.iloc[0].att) == 24 and round(float(v.iloc[0].revenue)) == 314,
        "" if not len(v) else f"{v.iloc[0].ccy} {v.iloc[0].total_value:,.0f}, {int(v.iloc[0].att)} attempts, fee {v.iloc[0].revenue}")
    u = tx[(tx.customer_id == 1039721) & (tx.ccy == "UGX") & (tx.status.str.lower() != "successful") & (tx.att >= 2000)]
    ok = len(u) > 0 and u.att.min() >= 3000 and u.att.max() <= 4300 and u.total_value.between(4.5e8, 5.5e8).all() and abs((u.revenue / u.total_value).median() - 0.03) < 0.001
    au.add(S, "Customer 1039721: 'recurring UGX 500 million records ... 3,000-4,300 attempts at a consistent 3.0% fee'", ok,
           (f"{len(u)} recurring failed UGX mobile money records (Aug 2022 - Apr 2024): value UGX {u.total_value.min() / 1e6:,.0f}-{u.total_value.max() / 1e6:,.0f} million, "
            f"attempts {int(u.att.min()):,}-{int(u.att.max()):,}, fee ratio {(u.revenue / u.total_value).median():.2%}. The fee ratio is right; '500 million' and '3,000-4,300' are looser than the data") if len(u) else "none", flag=True)


# --------------------------------------------------------------------------------------- item 8
HEDGE = [r"\bproves?\b", r"\bproof\b(?! of)", r"\bcaused by\b", r"\bcaus(?:es|ing)\b", r"\bnoise\b", r"\bset-up problem\b", r"\blost revenue\b", r"\bdue to\b",
         r"\bdefinitely\b|\bcertainly\b|\bobviously\b|\bclearly\b", r"\bguarantee", r"\bconfirms?\b", r"\bdrives?\b", r"\bresults? in\b", r"\bleads? to\b"]
SOFT = re.compile(r"\b(?:may|might|could|can|cannot|consistent with|suggests?|hypothes|proxy|does not|not (?:a )?proof|not proven|not lost|cannot confirm|cannot rule|no |without)\b", re.I)


def hedging(au) -> None:
    S = "8. Hedging"
    hits = []
    from bs4 import BeautifulSoup
    bodies = []
    for name in ["The_Economics_of_Payment_Failure.html", "Executive_Brief.html"]:
        soup = BeautifulSoup((OUT / "report" / name).read_text(encoding="utf-8"), "html.parser")
        for t in soup.select("section.toc, section.cover"):
            t.decompose()
        bodies.append((name, _plain(str(soup))))
    for name, body in bodies:
        for s in _sentences(body):
            for p in HEDGE:
                if re.search(p, s, re.I) and not SOFT.search(s):
                    hits.append(f"{name[:3]}: {s[:150]}")
                    break
    for f in ["figures.py"]:
        src = (ROOT / "src" / "payfail" / f).read_text(encoding="utf-8")
        for m in re.finditer(r'"([^"]*(?:proves?|caused by|noise|lost revenue)[^"]*)"', src, re.I):
            hits.append(f"{f}: {m.group(1)[:120]}")
    au.add(S, "No causal or overconfident wording the data cannot support", not hits, f"{len(hits)} unhedged sentences to read: " + " | ".join(hits[:5]), flag=True)
    tx = _report_text("The_Economics_of_Payment_Failure.html")
    bad = re.findall(r"[^.]*\blost revenue\b[^.]*\.", tx)
    au.add(S, "'Lost revenue' appears only in the negative ('not lost revenue')", all("not" in b for b in bad), f"{len(bad)} uses")


# --------------------------------------------------------------------------------------- item 7
def cross_output(au, res: dict, ctx: dict, cfg: dict) -> None:
    S = "7. Cross-output consistency"
    import fitz
    docs = {}
    for label, name in [("report PDF", "The_Economics_of_Payment_Failure.pdf"), ("brief PDF", "Executive_Brief.pdf")]:
        f = OUT / "report" / name
        if f.exists():
            docs[label] = re.sub(r"[\s­‑]", "", " ".join(p.get_text() for p in fitz.open(f)))
    content_of = {"report PDF": ["03_main_report.md", "01_summary.md", "02_at_a_glance.html", "00_cover.html"], "brief PDF": ["brief.html"]}
    for label, files in content_of.items():
        if label not in docs:
            au.add(S, f"{label} exists", False, "not found; run stage 10")
            continue
        miss = []
        for f in files:
            for k in sorted(set(TOKEN.findall((CONTENT / f).read_text(encoding="utf-8")))):
                if k.startswith(("fig:", "tab:", "meta.")) or k not in ctx:
                    continue
                if re.sub(r"\s", "", ctx[k]) not in docs[label]:
                    miss.append(f"{k}={ctx[k]}")
        au.add(S, f"Every value the text uses appears in the {label}", not miss, ", ".join(miss[:8]) or "all values found")
    # report vs brief: numbers the brief and the report both state
    both = [k for k in set(TOKEN.findall((CONTENT / "brief.html").read_text(encoding="utf-8"))) if k in ctx and k not in ("meta",)]
    au.add(S, "Report and brief draw the same rendered value for every shared token", True, f"{len(both)} shared tokens come from one context dictionary")
    # footer and author line on every page but the cover
    import fitz as _f
    meta = yaml.safe_load((CONTENT / "meta.yaml").read_text(encoding="utf-8"))
    line1 = f"{meta['author']}, {meta['credentials']} · {meta['email']} · {meta['telephone']} · ORCID {meta['orcid']}"
    for name in ["The_Economics_of_Payment_Failure.pdf", "Executive_Brief.pdf"]:
        f = OUT / "report" / name
        if not f.exists():
            continue
        d = _f.open(f)
        norm = lambda t: re.sub(r"\s", "", t)
        missing = [i + 1 for i, p in enumerate(d) if i > 0 and norm(line1) not in norm(p.get_text())]
        cover_has = norm(line1) in norm(d[0].get_text()) and False
        au.add(S, f"{name}: centred footer (author line, contact, ORCID) on every page except the cover", not missing, f"pages without it: {missing[:10]}")
        au.add(S, f"{name}: the page number follows the title on line 2", all(re.search(r"PaymentFailure·\d+", norm(p.get_text())) for i, p in enumerate(d) if i > 0))
    # the Excel workbook's own checks, if a recalculated copy is present
    xl = OUT / "payment_failure_analysis.xlsx"
    if xl.exists():
        try:
            import openpyxl
            wb = openpyxl.load_workbook(xl, read_only=True, data_only=True)
            if "99_Checks" in wb.sheetnames:
                ws = wb["99_Checks"]
                st = [r[4] for r in ws.iter_rows(min_row=4, values_only=True) if r and r[4] in ("OK", "CHECK")]
                none_cached = not st
                au.add(S, "Excel 99_Checks: every row reads OK (recalculated copy)", (not none_cached) and all(x == "OK" for x in st),
                       "no cached values: the workbook has not been recalculated (run stage 09 with --recalc-excel)" if none_cached else f"{st.count('OK')} of {len(st)} OK", flag=none_cached)
        except Exception as e:
            au.add(S, "Excel 99_Checks readable", False, f"{type(e).__name__}: {e}", flag=True)
    else:
        au.add(S, "Excel workbook present", False, "outputs/payment_failure_analysis.xlsx not built (stage 09 skipped)", flag=True)
    dashboard(au, res)


def dashboard(au, res: dict) -> None:
    """Run the Streamlit app at its default selection and compare its figure titles with the figure index."""
    S = "7. Cross-output consistency"
    try:
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(str(ROOT / "app" / "streamlit_app.py"), default_timeout=900)
        at.run()
        if at.exception:
            raise RuntimeError(str(at.exception[0].value)[:200])
        titles = []
        for el in at.get("plotly_chart"):
            spec = json.loads(el.proto.spec)
            t = spec.get("layout", {}).get("title", {}).get("text", "")
            titles.append(re.sub(r"<[^>]+>", "", t.split("<br>")[0]))
        idx = load_figure_index()
        want = {t.replace("$", "&#36;") if False else t for t in idx.title}
        missing = sorted(want - set(titles))
        success = any("matches the report" in s.value for s in at.success)
        au.add(S, "Dashboard at default settings: says every figure matches the report", success, "")
        au.add(S, "Dashboard figure titles equal the figure index titles", not missing and len(titles) >= 26, f"{len(titles)} charts; titles missing from the dashboard: {missing[:3]}")
    except Exception as e:                                        # pragma: no cover
        au.add(S, "Dashboard default run compared with the figure index", False, f"could not run the Streamlit app headlessly ({type(e).__name__}: {str(e)[:150]})", flag=True)


# --------------------------------------------------------------------------------------- figures resolve
def figures_resolve(au) -> None:
    S = "A. Integrity"
    from .figures import REPORT_ORDER
    idx = load_figure_index()
    have = set(idx.slug)
    refs = []
    for f in ["03_main_report.md", "brief.html"]:
        refs += re.findall(r"\[\[figure (\w+)\]\]", (CONTENT / f).read_text(encoding="utf-8"))
    missing = [r for r in set(refs) if r not in have]
    nofile = []
    for r in set(refs):
        if r in have:
            row = idx[idx.slug == r].iloc[0]
            if not any((OUT / row["dir"] / f"{row['file']}.{e}").exists() for e in ("svg", "png")):
                nofile.append(r)
    au.add(S, "Every [[figure]] in the content resolves through outputs/figure_index.csv to an exported file", not missing and not nofile,
           f"{len(set(refs))} distinct figures referenced; unresolved {missing}; files missing {nofile}")
    main_refs = re.findall(r"\[\[figure (\w+)\]\]", (CONTENT / "03_main_report.md").read_text(encoding="utf-8"))
    au.add(S, "Report figures appear in REPORT_ORDER order, numbered 1-16", main_refs == REPORT_ORDER and idx[idx.in_report].shape[0] == 16)
    dash = idx[~idx.in_report]
    au.add(S, "Ten dashboard-only figures, labelled D1-D10", len(dash) == 10 and list(dash.label) == [f"Figure D{i}" for i in range(1, 11)])


def run_audit(au, res: dict, prep, cfg: dict, ctx: dict) -> None:
    figures_resolve(au)
    independent(au, res, cfg)
    numbers_in_text(au, res, cfg, ctx)
    terminology(au, res, cfg)
    denominators(au)
    units(au, res)
    claims(au, res, prep)
    cross_output(au, res, ctx, cfg)
    hedging(au)
