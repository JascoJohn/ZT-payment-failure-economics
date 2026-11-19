"""The 26 report figures, built once with Plotly.

The same functions feed the static report (exported to PNG) and the Streamlit dashboard
(interactive, recomputed on filtered data). Titles are computed from the data, so a figure
can never disagree with the numbers behind it.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Report palette: navy, teal and amber on warm paper. The report CSS uses the same values.
ACCENT, MUTED, ALT, ALT2, GOOD, BAD = "#1F3A5F", "#C9C2B3", "#2A7F7F", "#D99A1E", "#2A7F7F", "#B5543C"
LIGHT, PAPER = "#8FAFCB", "#FAF7F0"
GRID, TEXT, SUB = "#E4DDCD", "#23272F", "#6B6860"
FONT = '"Source Sans 3", "Source Sans Pro", "Segoe UI", Arial, sans-serif'
SOURCE = "Source: ZT East Africa supplied dataset; author's calculations."
CH = {"card": "Card", "mobilemoney": "Mobile money", "alternative channels": "Alternative channels",
      "bank transfer": "Bank transfer", "account": "Account", "pay with wallet": "Pay with wallet", "enaira": "eNaira"}


def _k(v):
    return f"${v / 1e3:,.1f}K"


def _style(fig: go.Figure, title: str, subtitle: str = "", height: int = 460, note: str = SOURCE) -> go.Figure:
    named = [t for t in fig.data if getattr(t, "showlegend", None) is not False and getattr(t, "name", None)]
    legend = len(named) > 1
    top = 128 if legend else 96
    fig.update_layout(
        template="plotly_white", height=height, paper_bgcolor=PAPER, plot_bgcolor=PAPER, margin=dict(l=80, r=40, t=top, b=84),
        title=dict(text=f"<b>{title}</b><br><span style='font-size:13px;color:{SUB}'>{subtitle}</span>",
                   x=0.01, xanchor="left", xref="container", y=1 - 20 / height, yref="container", yanchor="top",
                   font=dict(size=17, color=TEXT)),
        font=dict(family=FONT, size=13, color=TEXT),
        legend=dict(orientation="h", x=0.01, xanchor="left", y=1 - 72 / height, yref="container", yanchor="top"),
        showlegend=legend)
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    plot_h = max(height - top - 84, 1)
    fig.add_annotation(text=note, xref="paper", yref="paper", x=0, y=-64 / plot_h, showarrow=False,
                       font=dict(size=10, color=SUB), xanchor="left", yanchor="top")
    return fig


# 1 ---------------------------------------------------------------------------------------------
def fig01_kpis(res, **_):
    h = res["headline"]
    tiles = [("Payment attempts", f"{h['attempts'] / 1e6:.2f}M", "Jan 2022 – Apr 2024"),
             ("Failed by count", f"{h['count_rate']:.1%}", f"{h['failed']:,} attempts"),
             ("Fees on failed payments", f"${h['failed_fees'] / 1e6:.2f}M", "Recorded amounts, not cash"),
             ("Successful-transaction fees", f"${h['succ_fees'] / 1e3:,.0f}K", "Recorded amounts, not cash")]
    fig = go.Figure()
    for i, (lab, val, sub) in enumerate(tiles):
        x0 = i / 4
        fig.add_shape(type="rect", xref="paper", yref="paper", x0=x0 + .005, x1=x0 + .24, y0=0, y1=1, line=dict(color=GRID), fillcolor=PAPER)
        fig.add_annotation(text=f"<b>{val}</b>", xref="paper", yref="paper", x=x0 + .02, y=.72, showarrow=False, xanchor="left", font=dict(size=28))
        fig.add_annotation(text=lab, xref="paper", yref="paper", x=x0 + .02, y=.38, showarrow=False, xanchor="left", font=dict(size=13))
        fig.add_annotation(text=sub, xref="paper", yref="paper", x=x0 + .02, y=.16, showarrow=False, xanchor="left", font=dict(size=11, color=SUB))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
    return _style(fig, "Figure 1. Headline figures, Jan 2022 – Apr 2024", "Attempts use all records; USD measures use translatable records", 300)


# 2 ---------------------------------------------------------------------------------------------
def fig02_bridge(res, **_):
    b = res["bridge"].set_index("category")
    total = b.f_fee.sum()
    ex, es, rm = b.loc["Extreme-volume anomaly", "f_fee"], b.loc["Escalation", "f_fee"], b.loc["Remaining", "f_fee"]
    fig = go.Figure(go.Waterfall(
        x=["All failed-transaction fees", "Extreme-volume anomalies", "Escalation account(s)", "Remaining exposure"],
        measure=["absolute", "relative", "relative", "total"], y=[total, -ex, -es, 0],
        text=[_k(total), f"−{_k(ex)} ({ex / total:.1%})", f"−{_k(es)} ({es / total:.1%})", f"{_k(rm)} ({rm / total:.1%})"],
        textposition="outside", connector=dict(line=dict(color=MUTED, dash="dot")),
        decreasing=dict(marker=dict(color=ALT)), totals=dict(marker=dict(color=ACCENT)), increasing=dict(marker=dict(color=MUTED))))
    fig.update_yaxes(title="USD", tickformat="$,.0f", range=[0, total * 1.15])
    return _style(fig, f"Figure 2. {(ex + es) / total:.1%} of the exposure sits in exceptional account behaviour",
                  "Fees on failed transactions; mutually exclusive categories, reconciled on unrounded values")


# 3 ---------------------------------------------------------------------------------------------
def fig03_trend(res, **_):
    m = res["monthly"]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=.08,
                        subplot_titles=("Count failure rate", "Failed-fee share"))
    for row, (a, r) in enumerate([("count_all", "count_rem"), ("share_all", "share_rem")], start=1):
        fig.add_trace(go.Scatter(x=m.period, y=m[a], name="All records", line=dict(color=MUTED, width=2), showlegend=row == 1), row, 1)
        fig.add_trace(go.Scatter(x=m.period, y=m[r], name="Excluding extreme-volume anomalies and the escalation account", line=dict(color=ACCENT, width=3), showlegend=row == 1), row, 1)
    for d in ["2024-01-01", "2024-04-01"]:
        fig.add_vline(x=pd.Timestamp(d).timestamp() * 1000, line=dict(color=SUB, dash="dot"))
    fig.update_yaxes(tickformat=".0%")
    lo, hi = m.count_rem.min(), m.count_rem.max()
    return _style(fig, "Figure 3. Strip out the anomalies and failure is persistent but steady",
                  f"Monthly; excluding anomalies the count failure rate stays between {lo:.0%} and {hi:.0%}", 560)


# 4 ---------------------------------------------------------------------------------------------
def fig04_composition(res, **_):
    m = res["monthly"]
    fig = go.Figure()
    for col, name, color in [("fees_remaining", "Remaining", MUTED), ("fees_escalation", "Escalation account(s)", LIGHT),
                             ("fees_extreme", "Extreme-volume anomalies", ACCENT)]:
        fig.add_trace(go.Bar(x=m.period, y=m[col], name=name, marker_color=color))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title="USD", tickformat="$,.0f")
    return _style(fig, "Figure 4. Two anomaly types drive the Dec 2023 – Apr 2024 surge",
                  "Monthly fees on failed transactions by exposure category")


# 5 ---------------------------------------------------------------------------------------------
def fig05_value(res, **_):
    v = res["value"]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Average value per attempt (USD)", "Fee as % of value"))
    fig.add_trace(go.Bar(x=["Failed", "Successful"], y=[v["avg_failed_value"], v["avg_success_value"]], marker_color=[ACCENT, MUTED],
                         text=[f"${v['avg_failed_value']:.2f}", f"${v['avg_success_value']:.2f}"], textposition="outside", showlegend=False), 1, 1)
    fig.add_trace(go.Bar(x=["Failed", "Successful"], y=[v["failed_fee_intensity"], v["success_fee_intensity"]], marker_color=[ACCENT, MUTED],
                         text=[f"{v['failed_fee_intensity']:.2%}", f"{v['success_fee_intensity']:.2%}"], textposition="outside", showlegend=False), 1, 2)
    fig.update_yaxes(tickformat=".1%", row=1, col=2)
    ratio = v["avg_failed_value"] / v["avg_success_value"]
    return _style(fig, f"Figure 5. Failed attempts are {ratio:.1f}× larger, but carry similar fee rates",
                  "Translatable records excluding value anomalies")


# 6 ---------------------------------------------------------------------------------------------
def fig06_channels(res, **_):
    c = res["channels"]
    c = c[c.f_fee >= 100].sort_values("f_fee")
    fig = go.Figure(go.Bar(y=[CH.get(p, p) for p in c.pt], x=c.f_fee, orientation="h",
                           marker_color=[ACCENT if p == "card" else MUTED for p in c.pt],
                           text=[f"{_k(f)} · {s:.1%} of total · {r:.1%} fail" for f, s, r in zip(c.f_fee, c.share_of_failed_fees, c.fail_rate)],
                           textposition="outside", showlegend=False))
    fig.update_xaxes(title="Fees on failed transactions (USD)", tickformat="$,.0f", range=[0, c.f_fee.max() * 1.5])
    top = c.set_index("pt").share_of_failed_fees.get("card", np.nan)
    return _style(fig, f"Figure 6. Card payments hold {top:.0%} of fees on failed transactions",
                  "By payment type; labels show amount, share of total and count failure rate")


# 7 ---------------------------------------------------------------------------------------------
def fig07_heatmap(res, **_):
    h = res["heat"]
    h = h[h.pt.isin(["card", "mobilemoney", "alternative channels", "bank transfer"])]
    rows = [c for c in ["Kenya", "Uganda", "Tanzania", "Ghana", "Zambia"] if c in set(h.country)]
    cols = [p for p in ["card", "mobilemoney", "alternative channels", "bank transfer"] if p in set(h.pt)]
    z = h.pivot(index="country", columns="pt", values="fail_rate").reindex(index=rows, columns=cols)
    f = h.pivot(index="country", columns="pt", values="f_fee").reindex(index=rows, columns=cols)
    text = [[f"{z.iloc[i, j]:.1%}<br>{_k(f.iloc[i, j])}" if pd.notna(z.iloc[i, j]) else "" for j in range(len(cols))] for i in range(len(rows))]
    fig = go.Figure(go.Heatmap(z=z.values, x=[CH[c] for c in cols], y=rows, text=text, texttemplate="%{text}",
                               colorscale=[[0, "#F3EEE2"], [1, "#4A6F94"]], zmin=0, zmax=1, colorbar=dict(title="Failure", tickformat=".0%")))
    fig.update_yaxes(autorange="reversed")
    card = z.get("card")
    sub = "Shade = count failure rate; cell text adds fees on failed transactions (a different measure)"
    title = f"Figure 7. Card fails at {card.min():.0%}–{card.max():.0%} in every market" if card is not None else "Figure 7. Failure by market and channel"
    return _style(fig, title, sub, 480)


# 8 ---------------------------------------------------------------------------------------------
def fig08_pareto(res, **_):
    p = res["pareto"]
    fig = go.Figure()
    for s, color in [("All records", ACCENT), ("Excluding extreme-volume anomalies", MUTED)]:
        d = p[p.series == s]
        fig.add_trace(go.Scatter(x=d.pct_customers, y=d.cum_share / 100, name=s, mode="lines+markers", line=dict(color=color, width=3)))
    n = int(p.n.iloc[0])
    for k, lab in [(10, "Top 10"), (max(1, round(n * .01)), "Top 1%")]:
        fig.add_vline(x=k / n * 100, line=dict(color=SUB, dash="dot"), annotation_text=lab, annotation_position="bottom right")
    fig.update_xaxes(type="log", title="Share of customers, ranked by failed fees (log scale)", ticksuffix="%")
    fig.update_yaxes(tickformat=".0%", title="Cumulative share of failed fees")
    t10 = res["customer_concentration"]["top10"]
    return _style(fig, f"Figure 8. The top 10 of {n:,} customers with failed fees hold {t10:.0%} of it", "Cumulative concentration")


# 9 ---------------------------------------------------------------------------------------------
def fig09_drivers(res, **_):
    d = res["drivers"]
    d = d[d.f_fee > 5000]
    fig = go.Figure(go.Scatter(
        x=d.share_of_attempts, y=d.fail_rate, mode="markers+text", text=[f"{c} {CH.get(p, p).lower()}" if f >= 15000 else "" for c, p, f in zip(d.country, d.pt, d.f_fee)],
        hovertext=[f"{c} {CH.get(p, p).lower()}" for c, p in zip(d.country, d.pt)], textposition="top center", marker=dict(size=np.sqrt(d.f_fee) / np.sqrt(d.f_fee.max()) * 70 + 6,
                                               color=[ACCENT if p == "card" else MUTED for p in d.pt], opacity=.65, line=dict(color=PAPER)),
        customdata=d.f_fee, hovertemplate="%{hovertext}<br>%{x:.1%} of attempts<br>%{y:.1%} failed<br>$%{customdata:,.0f} failed fees<extra></extra>",
        showlegend=False))
    fig.update_xaxes(type="log", tickformat=".1%", title="Share of non-anomalous attempts (log scale)",
                     tickvals=[.002, .005, .01, .02, .05, .1, .2, .5])
    fig.update_yaxes(tickformat=".0%", title="Count failure rate")
    return _style(fig, "Figure 9. Card: high failure, small volume; Uganda mobile money: scale",
                  "Bubble area = non-anomalous fees on failed transactions; cells above $15K labelled (all cells over $5K shown)", 520)


# 10 --------------------------------------------------------------------------------------------
def fig10_quintiles(res, **_):
    q = res["quintiles"]
    fig = go.Figure()
    for pt, color in [("card", MUTED), ("mobilemoney", ACCENT)]:
        d = q[q.pt == pt]
        fig.add_trace(go.Bar(x=[f"Q{i}" for i in d.quintile], y=d.fail_rate, name=CH[pt], marker_color=color,
                             text=[f"{r:.1%}" for r in d.fail_rate], textposition="outside"))
    fig.update_yaxes(tickformat=".0%", range=[0, 1.1], title="Count failure rate")
    return _style(fig, "Figure 10. Mobile money fails mainly on high-value records; card at every size",
                  "Quintiles of average value per aggregated record (not individual transactions); value anomalies excluded")


# 11 --------------------------------------------------------------------------------------------
def fig11_anomalies(res, **_):
    o = res["anomalies"]["observations"].copy()
    o["label"] = [f"{c} · {r} {CH.get(p, p).lower()} · {pd.Timestamp(m):%b %Y}" for c, r, p, m in zip(o.customer_id, o.country, o.pt, o.period)]
    top, rest = o.head(5), o.iloc[5:]
    if len(rest):
        top = pd.concat([top, pd.DataFrame([{"label": f"Other {len(rest)} observations", "f_att": rest.f_att.sum(), "f_fee": rest.f_fee.sum()}])])
    top = top.iloc[::-1]
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, subplot_titles=("Failed attempts", "Fees on failed transactions"))
    fig.add_trace(go.Bar(y=top.label, x=top.f_att, orientation="h", marker_color=MUTED, text=[f"{v:,.0f}" for v in top.f_att], textposition="outside", showlegend=False), 1, 1)
    fig.add_trace(go.Bar(y=top.label, x=top.f_fee, orientation="h", marker_color=ACCENT, text=[_k(v) for v in top.f_fee], textposition="outside", showlegend=False), 1, 2)
    fig.update_xaxes(range=[0, top.f_att.max() * 1.3], row=1, col=1)
    fig.update_xaxes(range=[0, top.f_fee.max() * 1.35], row=1, col=2)
    s4 = o.head(4).f_fee.sum()
    return _style(fig, f"Figure 11. The four largest account-months carry {_k(s4)} of {_k(o.f_fee.sum())} anomaly exposure",
                  "Extreme-volume anomaly proxies; the data cannot show automation or card testing", 480)


# 12 --------------------------------------------------------------------------------------------
def fig12_escalation(res, **_):
    s = res["anomalies"]["escalation_series"]
    s = s[s.period >= s.period.max() - pd.DateOffset(months=6)]
    ids = ", ".join(str(c) for c in res["anomalies"]["escalation_customers"])
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("Failed attempts", "Fees on failed transactions (USD)"))
    fig.add_trace(go.Scatter(x=s.period, y=s.f_att, mode="lines+markers+text", text=[f"{v:,.0f}" for v in s.f_att], textposition="top center",
                             line=dict(color=ACCENT, width=3), showlegend=False), 1, 1)
    fig.add_trace(go.Bar(x=s.period, y=s.f_fee, marker_color=ACCENT, text=[_k(v) for v in s.f_fee], textposition="outside", showlegend=False), 2, 1)
    fig.update_yaxes(range=[0, s.f_att.max() * 1.3], row=1, col=1)
    fig.update_yaxes(range=[0, s.f_fee.max() * 1.3], row=2, col=1)
    peak = s.loc[s.f_att.idxmax()]
    return _style(fig, f"Figure 12. One account escalated to {peak.f_att:,.0f} failed attempts in {pd.Timestamp(peak.period):%B %Y}",
                  f"Escalation account(s) {ids}; a single-account series, not a market trend", 540)


# 13 --------------------------------------------------------------------------------------------
def fig13_hard_mixed(res, **_):
    b = res["hard_mixed"]["by_channel"]
    b = b[b.pt.isin(["card", "mobilemoney", "alternative channels"])]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=[CH[p] for p in b.pt], x=b.Hard, name="Hard (no successes that month)", orientation="h", marker_color=ACCENT))
    fig.add_trace(go.Bar(y=[CH[p] for p in b.pt], x=b.Mixed, name="Mixed", orientation="h", marker_color=LIGHT,
                         text=[f"{s:.0%} hard · anomalies shown separately: {_k(a)}" for s, a in zip(b.hard_share, b.anomalies)], textposition="outside"))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(categoryorder="array", categoryarray=[CH[p] for p in ["alternative channels", "mobilemoney", "card"]])
    fig.update_xaxes(tickformat="$,.0f", title="Non-anomalous fees on failed transactions", range=[0, (b.Hard + b.Mixed).max() * 1.9])
    card = b.set_index("pt").hard_share.get("card", np.nan)
    return _style(fig, f"Figure 13. {card:.0%} of card exposure comes from months with no card success",
                  "Hard / mixed are proxies; the data cannot show causes")


# 14 --------------------------------------------------------------------------------------------
def fig14_persistence(res, **_):
    p = res["customers"]["persistence"]
    lab = [f"Persistent ({p['persistent']:,})", f"Other eligible ({p['eligible'] - p['persistent']:,})"]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Failed-fee share", "End-period lapse rate"))
    fig.add_trace(go.Bar(x=lab, y=[p["fee_share_persistent"], p["fee_share_other"]], marker_color=[ACCENT, MUTED],
                         text=[f"{v:.1%}" for v in [p["fee_share_persistent"], p["fee_share_other"]]], textposition="outside", showlegend=False), 1, 1)
    fig.add_trace(go.Bar(x=lab, y=[p["lapse_persistent"], p["lapse_other"]], marker_color=[ACCENT, MUTED],
                         text=[f"{v:.1%}" for v in [p["lapse_persistent"], p["lapse_other"]]], textposition="outside", showlegend=False), 1, 2)
    fig.update_yaxes(tickformat=".0%", range=[0, 1.1])
    return _style(fig, "Figure 14. Persistent customers lose more fee value to failure and lapse more",
                  "Customers with 6+ active months, excluding anomalies; associations, not causal effects")


# 15 --------------------------------------------------------------------------------------------
def fig15_patterns(res, **_):
    pt = res["laney"]["patterns"]
    flags = ["structural", "deteriorating", "episodic", "unstable", "stable"]
    ylab = [f"{c} {CH.get(p, p).lower()}" for c, p in zip(pt.country, pt.pt)]
    fig = go.Figure()
    for j, f in enumerate(flags):
        on = pt[f"flag_{f}"].astype(bool).values
        fig.add_trace(go.Scatter(x=[f.title()] * len(pt), y=ylab, mode="markers", showlegend=False,
                                 marker=dict(size=16, color=[ACCENT if v else "white" for v in on], line=dict(color=ACCENT if True else GRID, width=1))))
    fig.add_trace(go.Scatter(x=["Laney signals"] * len(pt), y=ylab, mode="text", text=pt.signals.astype(str), showlegend=False, textfont=dict(size=14)))
    fig.update_yaxes(autorange="reversed")
    return _style(fig, "Figure 15. Card cells are structural; flags overlap",
                  "Filled = flag applies. Screening flags are diagnostic, not proof", 520)


# 16 --------------------------------------------------------------------------------------------
def fig16_january(res, **_):
    c = res["january"]["components"]
    meas = ["absolute"] + ["relative"] * (len(c) - 2) + ["total"]
    y = list(c.usd[:-1]) + [0]
    names = [n.replace(" ", "<br>", 1) if len(n) > 10 else n for n in c.component]
    fig = go.Figure(go.Waterfall(x=names, measure=meas, y=y, text=[_k(v) if i in (0, len(c) - 1) else f"{v / 1e3:+,.1f}K" for i, v in enumerate(c.usd)],
                                 textposition="outside", increasing=dict(marker=dict(color=BAD)), decreasing=dict(marker=dict(color=GOOD)),
                                 totals=dict(marker=dict(color=MUTED)), connector=dict(line=dict(color=MUTED, dash="dot"))))
    fig.update_yaxes(tickformat="$,.0f", range=[0, c.usd.iloc[-1] * 1.15])
    j = res["january"]
    share = (j["january_extreme"] - j["baseline_extreme"]) / (j["january_all"] - j["baseline_all"])
    return _style(fig, f"Figure 16. Anomalies explain {share:.0%} of January's rise in failed-transaction fees",
                  "Baseline = Jul–Dec 2023 monthly average; red raises, green lowers failed fees")


# 17 --------------------------------------------------------------------------------------------
def fig17_lmdi(res, **_):
    j = res["january"]
    items = [("FX translation", j["fx_effect"]), *j["lmdi"].items(), ("Entry/exit cells", j["entry_exit"])]
    total = sum(v for _, v in items)
    fig = go.Figure(go.Bar(y=[k for k, _ in items][::-1], x=[v for _, v in items][::-1], orientation="h",
                           marker_color=[BAD if v > 0 else GOOD for _, v in items][::-1],
                           text=[f"{v / 1e3:+,.1f}K" for _, v in items][::-1], textposition="outside", showlegend=False))
    fig.add_vline(x=0, line=dict(color=SUB))
    fig.update_xaxes(tickformat="$,.0f")
    return _style(fig, "Figure 17. Outside anomalies, volume and fee yield drove January",
                  f"Components sum to the non-anomalous change of {total / 1e3:+,.1f}K; residual {j['residual']:.2f}")


# 18 --------------------------------------------------------------------------------------------
def fig18_fx_currency(res, **_):
    b = res["fx"]["by_currency"]
    main = ["GHS", "NGN", "KES", "TZS", "UGX", "ZMW"]
    d = b[b.ccy.isin(main)].copy()
    other = b[~b.ccy.isin(main)].effect.sum()
    d = pd.concat([d, pd.DataFrame([{"ccy": "All other", "effect": other, "depreciation": np.nan}])])
    d = d.iloc[::-1]
    fig = go.Figure(go.Bar(y=d.ccy, x=d.effect, orientation="h", marker_color=[ACCENT if c == "GHS" else MUTED for c in d.ccy],
                           text=[f"{v / 1e3:+,.1f}K" + (f" ({dp:+.1%} vs USD)" if pd.notna(dp) else "") for v, dp in zip(d.effect, d.depreciation)],
                           textposition="outside", showlegend=False))
    fig.add_vline(x=0, line=dict(color=SUB))
    fig.update_xaxes(tickformat="$,.0f", title="Reported less 2022-constant-currency fees", range=[d.effect.min() * 1.45, max(d.effect.max(), 0) + abs(d.effect.min()) * .05])
    ghs = b.set_index("ccy").effect.get("GHS", 0) / b.effect.sum()
    return _style(fig, f"Figure 18. The Ghanaian cedi drives {ghs:.0%} of the translation effect",
                  "Translation effect on local-currency fees vs 2022 average rates; not realised FX gains or losses")


# 19 --------------------------------------------------------------------------------------------
def fig19_reported_constant(res, **_):
    m = res["fx"]["measures"]
    fig = make_subplots(rows=1, cols=2, subplot_titles=list(m.measure))
    for i, r in enumerate(m.itertuples(), start=1):
        fig.add_trace(go.Bar(x=["Reported", "2022 constant currency"], y=[r.reported, r.constant], marker_color=[ACCENT, MUTED],
                             text=[_k(r.reported), _k(r.constant)], textposition="outside", showlegend=False), 1, i)
    fig.update_yaxes(tickformat="$,.0f")
    pct = (m.difference / m.constant).mean()
    return _style(fig, f"Figure 19. Depreciation trims both measures by about {abs(pct):.0%} in USD terms",
                  "Translation differences only; not realised FX gains or losses")


# 20 --------------------------------------------------------------------------------------------
def fig20_ias_screen(res, **_):
    s = res["fx"]["ias_screen"].iloc[::-1]
    fig = go.Figure(go.Scatter(x=s.months_above, y=s.ccy, mode="markers+text", text=[f"{n} (avg range {a:.1%})" for n, a in zip(s.months_above, s.avg_range)],
                               textposition="middle right", marker=dict(size=16, color=[ACCENT if n >= 7 else MUTED for n in s.months_above]), showlegend=False))
    fig.update_xaxes(range=[-1, 28], title="Currency-months (of 28) above the 10% high–low screen")
    return _style(fig, "Figure 20. Naira and cedi months most often fail the average-rate screen",
                  "The 10% screen is this report's diagnostic threshold, not an IAS 21 rule")


# 21 --------------------------------------------------------------------------------------------
def fig21_recovery_market(res, **_):
    m = res["recovery"]["markets"].sort_values("incremental_base")
    pri = {"Kenya", "Tanzania", "Uganda"}
    fig = go.Figure(go.Bar(y=m.country, x=m.incremental_base, orientation="h", marker_color=[ACCENT if c in pri else MUTED for c in m.country],
                           text=[_k(v) for v in m.incremental_base], textposition="outside", showlegend=False))
    fig.update_xaxes(tickformat="$,.0f", title="Base-case incremental successful-transaction fee revenue", range=[0, m.incremental_base.max() * 1.15])
    tot, p3 = m.incremental_base.sum(), m[m.country.isin(pri)].incremental_base.sum()
    return _style(fig, f"Figure 21. Kenya, Tanzania and Uganda hold {_k(p3)} of the {_k(tot)} base case",
                  "USD card, excluding anomalies; conditional estimate before processing costs")


# 22 --------------------------------------------------------------------------------------------
def fig22_scenarios(res, **_):
    s = res["recovery"]["scenarios"]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Additional successful payments", "Incremental fee revenue (annual run-rate)"))
    colors = [MUTED, ACCENT, MUTED]
    fig.add_trace(go.Bar(x=s.scenario, y=s.additional_successes, marker_color=colors, text=[f"{v:,.0f}" for v in s.additional_successes],
                         textposition="outside", showlegend=False), 1, 1)
    fig.add_trace(go.Bar(x=s.scenario, y=s.incremental_fees, marker_color=colors, text=[f"{_k(v)} ({_k(a)}/yr)" for v, a in zip(s.incremental_fees, s.annual)],
                         textposition="outside", showlegend=False), 1, 2)
    annual_actual = res["headline"]["succ_fees"] * 12 / len(res["monthly"])
    fig.add_hline(y=annual_actual, line=dict(color=SUB, dash="dot"), row=1, col=2)
    fig.update_yaxes(tickformat="$,.0f", row=1, col=2)
    base = s.set_index("scenario").loc["Base"]
    return _style(fig, f"Figure 22. Base case: {base.additional_successes:,.0f} more successful card payments, worth {_k(base.incremental_fees)}",
                  f"Scenarios, not forecasts; annual = 28-month total × 12/28; dotted line = actual successful-transaction fees, annual equivalent ({_k(annual_actual)} a year)")


# 23 --------------------------------------------------------------------------------------------
def fig23_costs(res, **_):
    c = res["recovery"]["contribution"]
    fig = go.Figure(go.Bar(x=[f"{r:.0%} cost" for r in c.cost_ratio], y=c.contribution, marker_color=[ACCENT if abs(r - .6) < 1e-9 else MUTED for r in c.cost_ratio],
                           text=[_k(v) for v in c.contribution], textposition="outside", showlegend=False))
    fig.update_yaxes(tickformat="$,.0f", title="Fee revenue remaining, 28 months")
    be = res["recovery"]["breakeven"]
    return _style(fig, f"Figure 23. At an assumed 60% processing cost, {_k(c.set_index('cost_ratio').contribution.get(0.6, np.nan))} of base-case fee revenue remains",
                  f"Fee revenue remaining after assumed processing costs; other operating costs not included; break-even ${be:.2f} per additional success")


# 24 --------------------------------------------------------------------------------------------
def fig24_matrix(res, prep=None, **_):
    m = res["matrix"]
    esc = res["anomalies"]["escalation_customers"]
    colors = {"Prioritise": ACCENT, "Investigate root cause": ALT2, "Contain escalation account": ALT, "Monitor": MUTED}
    fig = go.Figure()
    for act, color in colors.items():
        d = m[m.action == act]
        if d.empty:
            continue
        fig.add_trace(go.Scatter(x=d.f_fee, y=d.fail_rate, mode="markers+text", name=act,
                                 text=[f"{c} {CH.get(p, p).lower()}" if f > 50000 else "" for c, p, f in zip(d.country, d.pt, d.f_fee)],
                                 textposition=["bottom center" if f == m.f_fee.max() else "middle left" for f in d.f_fee],
                                 marker=dict(size=np.sqrt(d.internal_potential.clip(lower=0)) / np.sqrt(max(m.internal_potential.max(), 1)) * 60 + 8,
                                             color=color, opacity=.65, line=dict(color=PAPER)),
                                 customdata=np.stack([d.internal_potential, d.diagnostic_confidence], axis=1),
                                 hovertemplate="%{text}<br>$%{x:,.0f} failed fees<br>%{y:.1%} failed<br>internal potential $%{customdata[0]:,.0f}<br>diagnostic: %{customdata[1]}<extra></extra>"))
    if esc and prep is not None:
        e = prep.tx[prep.tx.customer_id.isin(esc) & ~prep.tx.extreme]
        fig.add_trace(go.Scatter(x=[e.f_fee.sum()], y=[e.f_att.sum() / e.att.sum()], mode="markers+text", name="Escalation account (contain)",
                                 text=[f"Account {', '.join(map(str, esc))} (escalation)"], textposition="top left",
                                 marker=dict(symbol="diamond", size=16, color=ALT)))
    fig.update_xaxes(type="log", tickformat="$,.0f", title="Non-anomalous fees on failed transactions (log scale)")
    fig.update_yaxes(tickformat=".0%", title="Count failure rate")
    return _style(fig, "Figure 24. Card cells: largest exposure, high failure, most recoverable fees",
                  "Bubble area = internal recoverable fees (cell's own best 3-month rate)", 560)


# 25 --------------------------------------------------------------------------------------------
def fig25_roadmap(res, **_):
    rec = res["recovery"]["markets"].set_index("country").rate
    pers = res["customers"]["persistence"]["persistent"]
    rows = [["1. Contain anomalies", "To be assigned", "Deploy relative and absolute account alerts; review flagged observations and escalation account(s)",
             "Extreme failed-attempt observations a month", "Weekly"],
            ["2. USD card completion: Kenya, Tanzania, Uganda", "To be assigned", "Diagnose zero-success merchant-months: acceptance, routing, currency set-up",
             "USD card failure vs baseline (" + ", ".join(f"{c} {rec.get(c, np.nan):.1%}" for c in ["Kenya", "Tanzania", "Uganda"]) + ")", "Monthly"],
            ["3. Persistent customers and high-value mobile money", "To be assigned", f"Review the {pers:,} persistent accounts; investigate the mobile money Q5 result",
             "Persistent-customer failed fees; mobile money Q5 failure rate", "Monthly / quarterly"]]
    fig = go.Figure(go.Table(columnwidth=[1.4, .8, 2, 1.6, .8],
                             header=dict(values=["Workstream", "Owner", "First action", "KPI", "Review"], fill_color="#EFE9DC", align="left", font=dict(size=12)),
                             cells=dict(values=list(map(list, zip(*rows))), align="left", height=48, fill_color=PAPER, font=dict(size=12))))
    fig = _style(fig, "Figure 25. Three workstreams: contain, fix card, manage persistent accounts", "Owners to be assigned by the team", 440,
                 note="Source: author's recommendations.")
    fig.update_layout(showlegend=False)
    return fig


# 26 --------------------------------------------------------------------------------------------
def fig26_flow(res, prep=None, **_):
    h, s = res["headline"], res["stats"]
    boxes = [(.3, .88, f"All records: {h['records']:,} records, {h['attempts']:,} attempts", "Every count-based measure"),
             (.12, .62, f"No exchange rate: {s['untranslatable_records']} records", f"{s['untranslatable_currencies']} currencies, {s['untranslatable_attempts']} attempts: counts only"),
             (.62, .62, f"Translatable: {h['records_translatable']:,} records, {h['attempts_translatable']:,} attempts",
              f"SLL rates restated; {s['spike_days_dropped']} spike days dropped"),
             (.25, .34, "Fee measures: all translatable records", f"{s['flag_fee_ratio']} fee-ratio + {s['flag_missing_fee']} missing-fee flags kept"),
             (.75, .34, "Value measures", f"{s['flag_value']} value anomalies (${s['flag_value_usd'] / 1e9:.2f}bn) excluded"),
             (.25, .08, f"${h['fees'] / 1e6:.2f}M recorded fees", f"${h['failed_fees'] / 1e6:.2f}M on failed transactions ({h['fee_share']:.1%})"),
             (.75, .08, f"${res['value']['value'] / 1e6:.1f}M transaction value", f"{res['value']['failed_value_share']:.1%} failed-value share")]
    fig = go.Figure()
    for x, y, a, b in boxes:
        fig.add_shape(type="rect", x0=x - .22, x1=x + .22, y0=y - .08, y1=y + .08, line=dict(color=SUB), fillcolor=PAPER)
        fig.add_annotation(x=x, y=y + .025, text=f"<b>{a}</b>", showarrow=False, font=dict(size=12))
        fig.add_annotation(x=x, y=y - .035, text=b, showarrow=False, font=dict(size=11, color=SUB))
    for (x0, y0), (x1, y1) in [((.3, .8), (.12, .7)), ((.3, .8), (.62, .7)), ((.62, .54), (.25, .42)), ((.62, .54), (.75, .42)),
                               ((.25, .26), (.25, .16)), ((.75, .26), (.75, .16))]:
        fig.add_annotation(x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y", arrowhead=2, arrowcolor=SUB, text="")
    fig.update_xaxes(visible=False, range=[-.12, 1.0]); fig.update_yaxes(visible=False, range=[-.02, 1.0])
    fig = _style(fig, "Figure 26. Two populations: counts use every record, dollars translatable ones", "Data populations and analytical filters", 560)
    fig.update_layout(showlegend=False)
    return fig


FIGURES = [
    (1, "kpis", "Executive summary", fig01_kpis), (2, "bridge", "Executive summary", fig02_bridge),
    (3, "trend", "2. Scale", fig03_trend), (4, "composition", "2. Scale", fig04_composition), (5, "value", "2. Scale", fig05_value),
    (6, "channels", "3. Concentration", fig06_channels), (7, "heatmap", "3. Concentration", fig07_heatmap),
    (8, "pareto", "3. Concentration", fig08_pareto), (9, "drivers", "3. Concentration", fig09_drivers),
    (10, "quintiles", "3. Concentration", fig10_quintiles),
    (11, "anomalies", "4. Diagnostics", fig11_anomalies), (12, "escalation", "4. Diagnostics", fig12_escalation),
    (13, "hard_mixed", "4. Diagnostics", fig13_hard_mixed), (14, "persistence", "4. Diagnostics", fig14_persistence),
    (15, "patterns", "4. Diagnostics", fig15_patterns),
    (16, "january", "5. January 2024", fig16_january), (17, "lmdi", "5. January 2024", fig17_lmdi),
    (18, "fx_currency", "6. Foreign exchange", fig18_fx_currency), (19, "reported_constant", "6. Foreign exchange", fig19_reported_constant),
    (20, "ias_screen", "6. Foreign exchange", fig20_ias_screen),
    (21, "recovery_market", "7. Recovery", fig21_recovery_market), (22, "scenarios", "7. Recovery", fig22_scenarios),
    (23, "costs", "7. Recovery", fig23_costs),
    (24, "matrix", "8. Recommendations", fig24_matrix), (25, "roadmap", "8. Recommendations", fig25_roadmap),
    (26, "flow", "Appendix A", fig26_flow),
]

# Figures in the written report, in reading order; they are numbered 1..n in this order.
# Every other figure appears only in the dashboard, labelled D1, D2, ... (same functions, same look).
REPORT_ORDER = ["bridge", "trend", "channels", "heatmap", "pareto", "drivers", "quintiles", "escalation",
                "hard_mixed", "january", "lmdi", "fx_currency", "recovery_market", "scenarios", "matrix", "flow"]
DASHBOARD_ONLY = [slug for _, slug, _, _ in FIGURES if slug not in REPORT_ORDER]
SECTION = {slug: sec for _, slug, sec, _ in FIGURES}


def label(slug: str) -> str:
    """The figure's number as printed: 'Figure 4' in the report, 'Figure D2' for dashboard-only figures."""
    if slug in REPORT_ORDER:
        return f"Figure {REPORT_ORDER.index(slug) + 1}"
    return f"Figure D{DASHBOARD_ONLY.index(slug) + 1}"


def build_all(res, prep=None) -> dict[str, go.Figure]:
    """Every figure, keyed by slug, titled with its report or dashboard number."""
    import re
    out = {}
    for n, slug, _, fn in FIGURES:
        try:
            fig = fn(res, prep=prep)
            fig.layout.title.text = re.sub(r"Figure \d+\.", label(slug) + ".", fig.layout.title.text, count=1)
            out[slug] = fig
        except Exception as e:  # a filtered subset may lack the data for a figure
            fig = go.Figure()
            fig.add_annotation(text=f"{label(slug)} not available for this selection ({type(e).__name__})", showarrow=False)
            fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
            out[slug] = fig
    return out
