"""Checks on the printed report: does anything split across pages, does every chapter start a page,
and where are the large gaps? Used by stage 11 and for diagnosing the layout."""
from __future__ import annotations

import re
from pathlib import Path

import fitz
from bs4 import BeautifulSoup

FOOT_PT = 23 * 72 / 25.4        # bottom margin holding the footer
TOP_PT = 19 * 72 / 25.4


def _norm(t: str) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", t).lower()


def _page_texts(doc) -> list[str]:
    return [_norm(p.get_text()) for p in doc]


def _locate(snippet: str, texts: list[str], start: int, end_side: bool = False) -> int | None:
    """First page (0-based) at or after `start` whose text contains the snippet."""
    if len(snippet) < 8:
        return None
    for i in range(start, len(texts)):
        if snippet in texts[i]:
            return i
    return None


def check_layout(html_path: Path, pdf_path: Path, contents: dict | None = None, min_fill: float = 0.62) -> dict:
    """Returns {'pages', 'splits', 'chapter_starts', 'gaps', 'fill'}."""
    doc = fitz.open(pdf_path)
    texts = _page_texts(doc)
    soup = BeautifulSoup(Path(html_path).read_text(encoding="utf-8"), "html.parser")
    main = soup.find("main") or soup
    chapter_pages = set()
    if contents:
        pg = contents.get("pages") or {}
        chapter_pages = {pg.get(e["id"]) for e in contents.get("contents", []) if e["level"] == 1}
    body_start = (min(p for p in chapter_pages if p) - 1) if chapter_pages else 0      # skip the contents lists
    splits, cursor = [], body_start
    span: dict[int, tuple[int, int]] = {}                 # element -> (first page, last page), 0-based

    def snippets(el):
        if el.name in ("p", "li"):
            full = _norm(el.get_text())
            return (full[:28], full[-28:]) if len(full) >= 24 else None
        if el.name == "table":
            rows = el.find_all("tr")
            cells = [c for c in rows[-1].find_all(["td", "th"]) if len(_norm(c.get_text())) >= 6] if rows else []
            return (None, _norm(cells[-1].get_text())[-28:]) if cells else None
        return None

    for el in main.find_all(["p", "li", "table"]):
        if el.name != "table" and el.find_parent("table") is not None:
            continue
        sn = snippets(el)
        if sn is None:
            continue
        a_, b_ = sn
        pa = _locate(a_, texts, max(cursor - 1, body_start)) if a_ else cursor
        if pa is None:
            continue
        pb = _locate(b_, texts, pa)
        cursor = pa
        pb = pa if pb is None else pb
        span[id(el)] = (pa, pb)
        if pb != pa and el.name != "table":
            splits.append({"kind": el.name, "pages": (pa + 1, pb + 1), "text": el.get_text()[:70].strip()})
    for g in main.find_all(True, class_=re.compile(r"^(keep|tbl)$")):
        members = [e for e in g.find_all(["p", "table"]) if id(e) in span and (e.name != "table" or True)]
        if len(members) < 2:
            continue
        first, last = span[id(members[0])][0], span[id(members[-1])][1]
        if first != last:
            splits.append({"kind": "group " + "/".join(m.name for m in members[:4]), "pages": (first + 1, last + 1),
                           "text": members[0].get_text()[:60].strip()})
    fills, gaps = [], []
    for i, page in enumerate(doc):
        h = page.rect.height
        bottoms = [b[3] for b in page.get_text("blocks") if b[3] < h - FOOT_PT + 2]
        bottoms += [d["bbox"][3] for d in page.get_text("dict")["blocks"] if d.get("type") == 1 and d["bbox"][3] < h - FOOT_PT + 2]
        low = max(bottoms, default=TOP_PT)
        fill = (low - TOP_PT) / (h - FOOT_PT - TOP_PT)
        fills.append(round(fill, 2))
        nxt_is_chapter = (i + 2) in chapter_pages
        if fill < min_fill and not nxt_is_chapter and i >= body_start and (i + 2) <= doc.page_count:
            gaps.append({"page": i + 1, "fill": round(fill, 2), "next_starts": texts[i + 1][:40] if i + 1 < len(texts) else ""})
    starts_ok = []
    for pno in sorted(p for p in chapter_pages if p):
        top = [b for b in doc[pno - 1].get_text("blocks") if b[1] < TOP_PT + 60]
        starts_ok.append({"page": pno, "at_top": bool(top)})
    return {"pages": doc.page_count, "splits": splits, "chapter_pages": sorted(p for p in chapter_pages if p),
            "gaps": gaps, "fill": fills}
