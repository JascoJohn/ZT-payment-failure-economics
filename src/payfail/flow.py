"""Page flow for the printed report, in the manner of Word or LaTeX.

Chrome paginates; this module reads the result back from the PDF and adjusts the HTML for another print:

* a figure is placed after the paragraph that first refers to it, so the text always refers to a figure before it or on its page;
* a figure or table that moves to the next page and leaves the page before it under 70% full is first scaled down
  (a figure, to no less than 80% of its height); if it still does not fit, the paragraphs that follow it in the same
  subsection move up in front of it to fill the gap;
* tables of more than 12 rows may run over a page (header row repeated, no row split); shorter ones stay whole.

The rules that every chapter starts a page and that no paragraph splits across pages are untouched (they are in report.css).
"""
from __future__ import annotations

import re
from pathlib import Path

import fitz
from bs4 import BeautifulSoup

PAGE_H = 841.92
TOP = 19 * 72 / 25.4
LIMIT = PAGE_H - 21 * 72 / 25.4            # bottom of the text area
CONTENT_W = (210 - 36) * 72 / 25.4
FOOT_Y = LIMIT + 2
AT_TOP = 70                                  # an element this close to the top margin starts its page
FILL_TRIGGER = 0.70
MIN_SCALE = 0.80


def _norm(t: str) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", t).lower()


# ------------------------------------------------------------------------------------------ HTML side
def place_figures(soup, figs: dict) -> None:
    """Move each figure to just after the first paragraph (in its subsection) that refers to it."""
    for fig in list(soup.find_all("figure", class_="chart")):
        slug = fig.get("id", "")[len("fig-"):]
        num = figs.get(slug)
        if num is None:
            continue
        pat = re.compile(rf"\bFigure {re.escape(str(num))}\b")
        # already after its first reference?
        prev = fig.find_previous_sibling()
        while prev is not None and prev.name not in ("h2", "h3"):
            if pat.search(prev.get_text()):
                break
            prev = prev.find_previous_sibling()
        else:
            prev = None
        if prev is not None and prev.name not in ("h2", "h3"):
            continue
        nxt, anchor = fig.find_next_sibling(), None
        while nxt is not None and nxt.name not in ("h2", "h3", "figure"):
            if pat.search(nxt.get_text()):
                anchor = nxt
                break
            nxt = nxt.find_next_sibling()
        if anchor is not None:
            anchor.insert_after(fig.extract())


def mark_long_tables(soup, limit: int = 12) -> None:
    for t in soup.find_all("div", class_="tbl"):
        rows = t.find("table").find_all("tr") if t.find("table") else []
        if len([r for r in rows if r.find("td")]) > limit:
            t["class"] = (t.get("class") or []) + ["long"]


def eligible_followers(el) -> list:
    """Blocks after `el` in its subsection that may move up in front of it: paragraphs and lists."""
    out = []
    n = el.find_next_sibling()
    while n is not None and n.name in ("p", "ul", "ol"):
        out.append(n)
        n = n.find_next_sibling()
    return out


def apply_state(main_html: str, state: dict) -> str:
    soup = BeautifulSoup(main_html, "html.parser")
    for fig in soup.find_all("figure", class_="chart"):
        sc = state["scale"].get(fig.get("id"), 1.0)
        img = fig.find("img")
        if sc < 1.0 and img is not None:
            img["style"] = f"width:{sc * 100:.1f}%;margin:0 auto"
    for tid, k in state["pull"].items():
        el = soup.find(id=tid)
        if el is None or not k:
            continue
        for f in eligible_followers(el)[:k]:
            el.insert_before(f.extract())
    return str(soup)


# ------------------------------------------------------------------------------------------ PDF side
def read_dests(pdf: Path) -> dict[str, tuple[int, float]]:
    """id -> (page 1-based, distance from the top of the page in points) for every contents target."""
    doc = fitz.open(pdf)
    out = {}
    for page in doc:
        for l in page.get_links():
            n = l.get("nameddest")
            if n and n not in out:
                tgt = doc[l["page"]]
                out[n] = (l["page"] + 1, float(tgt.rect.height - l["to"].y) if l.get("to") is not None else 0.0)
    return out


def page_bottoms(doc) -> list[float]:
    """Lowest text on each page above the footer."""
    res = []
    for page in doc:
        ys = [b[3] for b in page.get_text("blocks") if b[3] < FOOT_Y and b[1] > TOP - 10]
        res.append(max(ys, default=TOP))
    return res


def fill(bottom: float) -> float:
    return max(0.0, min(1.0, (bottom - TOP) / (LIMIT - TOP)))


def figure_height(path: Path) -> float:
    """Printed height of a figure at full content width, with its margins."""
    txt = path.read_text(encoding="utf-8", errors="ignore")[:600] if path.suffix == ".svg" else ""
    m = re.search(r'width="([\d.]+)(?:px)?"\s+height="([\d.]+)', txt) or re.search(r'viewBox="[\d.]+ [\d.]+ ([\d.]+) ([\d.]+)"', txt)
    if m:
        return CONTENT_W * float(m.group(2)) / float(m.group(1)) + 14
    return 260.0


def block_height(doc, el, from_page: int) -> float | None:
    """Printed height of a paragraph or list found on page `from_page` or later (1-based), from the PDF text blocks."""
    t = _norm(el.get_text())
    if len(t) < 20:
        return None
    first, last = t[:26], t[-26:]
    for pno in range(from_page - 1, doc.page_count):
        blocks = [(b[1], b[3], _norm(b[4])) for b in doc[pno].get_text("blocks")]
        y0 = next((b[0] for b in blocks if first in b[2]), None)
        if y0 is None:
            continue
        y1 = next((b[1] for b in reversed(blocks) if last in b[2]), None)
        if y1 is not None and y1 >= y0:
            return y1 - y0
    return None


def plan(state: dict, base_html: str, pdf: Path, chapter_pages: set[int], fig_files: dict[str, Path]) -> list[str]:
    """Look at the printed pages and adjust `state`; returns a description of each change (empty when nothing is left to do)."""
    soup = BeautifulSoup(base_html, "html.parser")
    doc = fitz.open(pdf)
    dests = read_dests(pdf)
    bottoms = page_bottoms(doc)
    changes = []
    for el in soup.find_all(["figure", "div"]):
        if el.name == "div" and "tbl" not in (el.get("class") or []):
            continue
        if el.name == "figure" and "chart" not in (el.get("class") or []):
            continue
        tid = el.get("id")
        if tid not in dests:
            continue
        p, top = dests[tid]
        unit = el
        prev = el.find_previous_sibling()
        if prev is not None and prev.name in ("h2", "h3") and prev.get("id") in dests:     # a heading sits in front: judge the page by it
            p, top = dests[prev.get("id")]
        if top > AT_TOP or p in chapter_pages or p < 2:
            continue
        q = p - 1
        if q in chapter_pages and False:
            continue
        if fill(bottoms[q - 1]) >= FILL_TRIGGER:
            continue
        free = LIMIT - bottoms[q - 1] - 6
        is_fig = el.name == "figure"
        sc = state["scale"].get(tid, 1.0)
        if is_fig and sc >= 1.0:
            h = figure_height(fig_files[tid[len("fig-"):]])
            if free >= MIN_SCALE * h:
                state["scale"][tid] = max(MIN_SCALE, min(1.0, int(free / h * 100) / 100))
                changes.append(f"{tid}: scaled to {state['scale'][tid]:.0%} to fill page {q} ({fill(bottoms[q - 1]):.0%} full)")
                continue
        k0 = state["pull"].get(tid, 0)
        followers = eligible_followers(el)[k0:]
        k = 0
        for f in followers:
            h = block_height(doc, f, p)
            if h is None or h + 8 > free:
                break
            free -= h + 8
            k += 1
        if k:
            state["pull"][tid] = k0 + k
            changes.append(f"{tid}: {k} following block(s) moved up to fill page {q} ({fill(bottoms[q - 1]):.0%} full)")
    return changes
