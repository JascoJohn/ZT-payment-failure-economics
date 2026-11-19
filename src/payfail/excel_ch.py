"""Chapter sheets of the Excel workbook (03, 04, 08, 01E) and native charts for every report figure.

Each sheet follows the report: tables are numbered and captioned as in the report ("Table n. ..."), charts carry the
report's figure number and title (read from outputs/figure_index.csv, so they cannot drift from figures.py) and use the
same colours. Python-only items are written as values, labelled with the script that produced them, and carry a check row.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from openpyxl.chart import BarChart, BubbleChart, LineChart, Reference, ScatterChart, Series
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.marker import DataPoint
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Font, PatternFill

from .figures import ACCENT, ALT, ALT2, LIGHT, MUTED, label

NAVY, TEAL, AMBER, SAND = ACCENT.lstrip("#"), ALT.lstrip("#"), ALT2.lstrip("#"), MUTED.lstrip("#")
BRICK, GREEN, SKY = "B5543C", "2A7F7F", LIGHT.lstrip("#")
PYFILL = PatternFill("solid", fgColor="EDEAE0")
PYFONT = Font(name="Arial", italic=True, color="555555")


# --------------------------------------------------------------------------------------------- charts
def _ax(ch, xfmt=None, yfmt=None, ytitle=None, xtitle=None):
    ch.x_axis.delete = False
    ch.y_axis.delete = False
    if yfmt:
        ch.y_axis.number_format = yfmt
        ch.y_axis.numFmt.sourceLinked = False if ch.y_axis.numFmt is not None else None
    if xfmt:
        ch.x_axis.number_format = xfmt
    if ytitle:
        ch.y_axis.title = ytitle
    if xtitle:
        ch.x_axis.title = xtitle


def color_series(s, color, line=False):
    gp = s.graphicalProperties
    if line:
        gp.line.solidFill = color
        gp.line.width = 28000
    else:
        gp.solidFill = color
        gp.line.solidFill = color


def bar_chart(ws, title, cats, series, *, horizontal=False, stacked=False, yfmt=None, ytitle=None, point_colors=None, labels=False, w=20, h=9.5, legend=True, note=None):
    """series = [(Reference, title, colour or None for invisible)]. point_colors colours individual bars of the first visible series."""
    ch = BarChart()
    ch.type = "bar" if horizontal else "col"
    ch.title = title
    ch.title.overlay = False
    if stacked:
        ch.grouping, ch.overlap = "stacked", 100
    for ref, name, color in series:
        s = Series(ref, title=name)
        if color is None:
            s.graphicalProperties.noFill = True
            s.graphicalProperties.line.noFill = True
        else:
            color_series(s, color)
        ch.series.append(s)
    vis = [s for s, (_, _, c) in zip(ch.series, series) if c is not None]
    if point_colors and vis:
        for i, c in enumerate(point_colors):
            dp = DataPoint(idx=i)
            dp.graphicalProperties.solidFill = c
            dp.graphicalProperties.line.solidFill = c
            vis[0].dPt.append(dp)
    if labels and vis:
        vis[0].dLbls = DataLabelList()
        vis[0].dLbls.showVal = True
        for a in ("showSerName", "showCatName", "showLegendKey", "showPercent"):
            setattr(vis[0].dLbls, a, False)
    ch.set_categories(cats)
    _ax(ch, yfmt=yfmt, ytitle=ytitle, xtitle=note)
    ch.width, ch.height = w, h
    if not legend or len(vis) <= 1:
        ch.legend = None
    else:
        ch.legend.position = "b"
    return ch


def line_chart(ws, title, cats, series, *, yfmt=None, w=20, h=9.5):
    ch = LineChart()
    ch.title = title
    ch.title.overlay = False
    for ref, name, color in series:
        s = Series(ref, title=name)
        color_series(s, color, line=True)
        s.marker.symbol = "none"
        s.smooth = False
        ch.series.append(s)
    ch.set_categories(cats)
    _ax(ch, xfmt="mmm yy", yfmt=yfmt)
    ch.width, ch.height = w, h
    ch.legend.position = "b"
    return ch


def scatter_chart(ws, title, series, *, xlog=False, xfmt=None, yfmt=None, xtitle=None, ytitle=None, lines=False, w=20, h=10):
    """series = [(x Reference, y Reference, title, colour)]."""
    ch = ScatterChart()
    ch.title = title
    ch.title.overlay = False
    ch.style = 13
    for xr, yr, name, color in series:
        s = Series(yr, xr, title=name)
        s.marker.symbol = "circle"
        s.marker.size = 7
        s.marker.graphicalProperties.solidFill = color
        s.marker.graphicalProperties.line.solidFill = color
        if lines:
            s.graphicalProperties.line.solidFill = color
            s.graphicalProperties.line.width = 24000
        else:
            s.graphicalProperties.line.noFill = True
        ch.series.append(s)
    if xlog:
        ch.x_axis.scaling.logBase = 10
    ch.y_axis.crosses = "min"
    _ax(ch, xfmt=xfmt, yfmt=yfmt, xtitle=xtitle, ytitle=ytitle)
    ch.width, ch.height = w, h
    ch.legend.position = "b"
    return ch


def bubble_chart(ws, title, x, y, z, *, xlog=False, xfmt=None, yfmt=None, xtitle=None, ytitle=None, color=NAVY, w=20, h=10):
    ch = BubbleChart()
    ch.title = title
    ch.title.overlay = False
    ch.style = 18
    s = Series(values=y, xvalues=x, zvalues=z, title="Cells")
    s.graphicalProperties.solidFill = color
    ch.series.append(s)
    if xlog:
        ch.x_axis.scaling.logBase = 10
    ch.y_axis.crosses = "min"
    _ax(ch, xfmt=xfmt, yfmt=yfmt, xtitle=xtitle, ytitle=ytitle)
    ch.width, ch.height = w, h
    ch.legend = None
    return ch


# --------------------------------------------------------------------------------------------- writer
class Wr:
    """Appends rows to a write-only sheet while tracking the row number, so formulas and charts can refer to them."""

    def __init__(self, bk, name, widths=None, start=1):
        self.bk, self.name, self.ws, self.r = bk, name, bk.sheet(name), start - 1
        if widths:
            from .excel import _widths
            _widths(self.ws, widths)
        self.q = f"'{name}'!"

    def row(self, cells):
        self.ws.append(cells)
        self.r += 1
        return self.r

    def blank(self, n=1):
        for _ in range(n):
            self.row([])

    def text(self, t, font=None, note=False):
        from .excel import B_FONT, BOLD, NOTE, T_FONT, _c
        self.row([_c(self.ws, t, NOTE if note else (font or B_FONT))])

    def title(self, t):
        from .excel import T_FONT, _c
        self.row([_c(self.ws, t, T_FONT)])

    def caption(self, slug, extra=""):
        from .excel import BOLD, _c
        return self.row([_c(self.ws, self.bk.tcap(slug) + extra, BOLD)])

    def head(self, labels):
        from .excel import H_FILL, H_FONT, _c
        return self.row([_c(self.ws, x, H_FONT, fill=H_FILL) for x in labels])

    def pynote(self, script, what=""):
        from .excel import _c
        self.row([_c(self.ws, f"Values from Python, see {script}.{(' ' + what) if what else ''} The check row below ties them to the formulas.", PYFONT, fill=PYFILL)])

    def chart(self, ch, col, row, note=None):
        from .excel import NOTE, _c
        self.ws.add_chart(ch, f"{col}{row}")

    def pad_to(self, row):
        while self.r < row:
            self.row([])


def val(ws, v, fmt=None):
    """A value supplied by Python (grey italic on a shaded cell)."""
    from .excel import _c
    return _c(ws, v, PYFONT, fmt, PYFILL)


# --------------------------------------------------------------------------------------------- helpers on the book
def load_captions(root: Path) -> dict[str, str]:
    txt = (root / "report" / "content" / "03_main_report.md").read_text(encoding="utf-8")
    return {m.group(1): m.group(2).strip() for m in re.finditer(r"^::: table (\w+) \| (.+)$", txt, re.M)}


def static_table(root: Path, ctx: dict, slug: str) -> list[list[str]]:
    """A text table of the report (actions, triggers) with its numbers filled in, as rows of cells."""
    from .report import render
    txt = (root / "report" / "content" / "03_main_report.md").read_text(encoding="utf-8")
    m = re.search(rf"^::: table {slug} \|.*\n((?:\|.*\n)+)", txt, re.M)
    rows = []
    for ln in m.group(1).splitlines():
        if re.match(r"^\|\s*-{3}", ln):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        rows.append([re.sub(r"\*\*", "", render(re.sub(r"\{\{(fig|tab):\w+\}\}", "", c), ctx)) for c in cells])
    return rows
