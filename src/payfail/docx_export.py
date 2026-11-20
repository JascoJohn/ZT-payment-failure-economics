"""Word version of the report, built from the HTML that the PDF is printed from, so the two share content.

The PDF is the master: edits made in Word do not flow back into the pipeline. The Word copy has the same headings and
numbers, a table-of-contents field and two list fields (figures, tables), the same figures (PNG), plain tables (rules,
no fills), formulas as Word equations (through Office's MML2OMML.XSL when Office is installed, otherwise as images
rendered from the LaTeX), justified text and the same footer. The at-a-glance infographic page is left out.
"""
from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Mm, Pt, RGBColor

NAVY = RGBColor(0x1F, 0x3A, 0x5F)
CREAM = "FAF7F0"
MML2OMML_CANDIDATES = [r"C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL",
                       r"C:\Program Files (x86)\Microsoft Office\root\Office16\MML2OMML.XSL",
                       r"C:\Program Files\Microsoft Office\Office16\MML2OMML.XSL"]


def body_font() -> str:
    """Source Sans 3 if it is installed on this machine, otherwise Calibri."""
    try:
        from matplotlib import font_manager
        names = {f.name for f in font_manager.fontManager.ttflist}
        if any(n.startswith("Source Sans 3") for n in names):
            return "Source Sans 3"
    except Exception:
        pass
    return "Calibri"


def _xsl():
    from lxml import etree
    for p in MML2OMML_CANDIDATES:
        if Path(p).exists():
            return etree.XSLT(etree.parse(p))
    return None


# ----------------------------------------------------------------------------------------------- low-level helpers
def _fld(par, instr: str, result: str, bold=False):
    """A simple complex field (begin, instruction, separate, cached result, end) inside one paragraph."""
    def run(child):
        r = OxmlElement("w:r")
        r.append(child)
        par._p.append(r)
        return r
    b = OxmlElement("w:fldChar"); b.set(qn("w:fldCharType"), "begin"); run(b)
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = f" {instr} "; run(it)
    s = OxmlElement("w:fldChar"); s.set(qn("w:fldCharType"), "separate"); run(s)
    t = par.add_run(result)
    t.bold = bold
    e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), "end"); run(e)


def _border(cell_or_par_pr, **edges):
    b = OxmlElement("w:pBdr") if cell_or_par_pr.tag == qn("w:pPr") else OxmlElement("w:tcBorders")
    for edge, (sz, color) in edges.items():
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:space"), "4" if b.tag == qn("w:pBdr") else "0")
        e.set(qn("w:color"), color)
        b.append(e)
    cell_or_par_pr.append(b)


def _style_fonts(doc: Document, font: str) -> None:
    st = doc.styles
    for name, size, bold, color in [("Normal", 10.5, False, None), ("Heading 1", 18, True, NAVY), ("Heading 2", 13.5, True, NAVY),
                                    ("Heading 3", 11.5, True, NAVY), ("Caption", 9.5, True, NAVY), ("List Bullet", 10.5, False, None),
                                    ("List Number", 10.5, False, None), ("Title", 30, True, NAVY)]:
        s = st[name]
        s.font.name = font
        s.font.size = Pt(size)
        s.font.bold = bold
        if color is not None:
            s.font.color.rgb = color
        rpr = s.element.get_or_add_rPr()
        rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts"); rpr.append(rf)
        for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rf.set(qn(a), font)
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
            if rf.get(qn(a)) is not None:
                del rf.attrib[qn(a)]
    st["Normal"].paragraph_format.space_after = Pt(6)
    st["Normal"].paragraph_format.line_spacing = 1.12


def _footer(section, meta: dict, font: str) -> None:
    section.different_first_page_header_footer = False         # the cover is a section of its own and has no footer
    f = section.footer
    f.is_linked_to_previous = False
    p1 = f.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p1.add_run(f"{meta['author_line']} · {meta['email']} · {meta['telephone']} · ORCID {meta['orcid']}")
    r.font.size = Pt(7.5); r.font.color.rgb = RGBColor(0x6B, 0x68, 0x60)
    p2 = f.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p2.add_run(f"{meta['title']} · ")
    r.font.size = Pt(7.5); r.font.color.rgb = RGBColor(0x6B, 0x68, 0x60)
    _fld(p2, "PAGE", "2")
    for run in p2.runs[1:]:
        run.font.size = Pt(7.5)


# ----------------------------------------------------------------------------------------------- inline content
class Builder:
    def __init__(self, doc, font, xslt, tmp: Path, fig_png):
        self.doc, self.font, self.xslt, self.tmp, self.fig_png = doc, font, xslt, tmp, fig_png
        self.n_eq = 0
        self.fig_n = self.tab_n = 0
        self.compact = False
        self.no_break_next = False

    def math_el(self, par, math_tag, display: bool) -> bool:
        """Insert a MathML element as a Word equation; False if no converter is available."""
        if self.xslt is None:
            return False
        from lxml import etree
        ml = str(math_tag)
        if "xmlns" not in ml.split(">", 1)[0]:
            ml = ml.replace("<math", '<math xmlns="http://www.w3.org/1998/Math/MathML"', 1)
        try:
            omml = self.xslt(etree.fromstring(ml.encode("utf-8")))
        except Exception:
            return False
        root = omml.getroot()
        xml = etree.tostring(root).decode()
        el = parse_xml(xml.replace("<m:oMath ", "<m:oMath " + nsdecls("w") + " ", 1) if "xmlns:w" not in xml else xml)
        if display:
            wrap = OxmlElement("m:oMathPara")
            wrap.append(el)
            par._p.append(wrap)
        else:
            par._p.append(el)
        return True

    def math_image(self, par, tex: str, display: bool) -> None:
        """Fallback when Office's converter is not installed: the LaTeX as a picture (matplotlib mathtext)."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        self.n_eq += 1
        path = self.tmp / f"eq{self.n_eq}.png"
        fig = plt.figure(figsize=(0.01, 0.01))
        fig.text(0, 0, f"${tex}$", fontsize=13 if display else 11)
        try:
            fig.savefig(path, dpi=200, bbox_inches="tight", pad_inches=0.04, transparent=True)
            par.add_run().add_picture(str(path), height=Inches(0.28 if display else 0.18))
        except Exception:
            par.add_run(tex)
        finally:
            plt.close(fig)

    def inline(self, par, node, bold=False, italic=False, size=None):
        for ch in node.children:
            if isinstance(ch, NavigableString):
                txt = str(ch).replace("\n", " ")
                if txt:
                    r = par.add_run(txt)
                    r.bold, r.italic = bold or None, italic or None
                    if size:
                        r.font.size = Pt(size)
                continue
            n = ch.name
            if n in ("strong", "b"):
                self.inline(par, ch, True, italic, size)
            elif n in ("em", "i"):
                self.inline(par, ch, bold, True, size)
            elif n == "math":
                if not self.math_el(par, ch, False):
                    par.add_run(ch.get_text()).italic = True
            elif n == "span" and "tag" in (ch.get("class") or []):
                r = par.add_run(ch.get_text().upper()); r.bold = True; r.font.size = Pt(8); r.font.color.rgb = RGBColor(0x2A, 0x7F, 0x7F)
            elif n == "br":
                par.add_run().add_break()
            elif n in ("span", "a", "code", "sup", "sub"):
                self.inline(par, ch, bold, italic, size)
            else:
                self.inline(par, ch, bold, italic, size)

    def para(self, node, style=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=None):
        p = self.doc.add_paragraph(style=style)
        p.alignment = align
        if self.compact:                       # the executive summary has to fit page 2
            size = size or 9.3
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.04
        self.inline(p, node, size=size)
        return p

    # ---- blocks
    def table(self, div):
        t = div.find("table")
        cap = div.find("p", class_="caption")
        self.tab_n += 1
        txt = " ".join(cap.get_text().split())
        label_part = re.match(r"^(Table \d+\.)\s*(.*)$", txt)
        c = self.doc.add_paragraph(style="Caption")
        c.paragraph_format.keep_with_next = True
        c.add_run("Table ")
        _fld(c, r"SEQ Table \* ARABIC", str(self.tab_n))
        c.add_run(". " + (label_part.group(2) if label_part else txt))
        rows = t.find_all("tr")
        ncol = max(len(r.find_all(["td", "th"])) for r in rows)
        wide = ncol >= 8
        tbl = self.doc.add_table(rows=len(rows), cols=ncol)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = True
        fsz = 7 if wide else 8.5
        for i, r in enumerate(rows):
            for j, cell in enumerate(r.find_all(["td", "th"])):
                wc = tbl.cell(i, j)
                wc.text = ""
                p = wc.paragraphs[0]
                p.paragraph_format.space_after = Pt(1)
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if "num" in (cell.get("class") or []) else WD_ALIGN_PARAGRAPH.LEFT
                self.inline(p, cell, bold=(cell.name == "th" or r.get("class") == ["total"]), size=fsz)
                tcpr = wc._tc.get_or_add_tcPr()
                edges = {}
                if i == 0:
                    edges.update(top=(10, "1F3A5F"), bottom=(6, "1F3A5F"))
                if i == len(rows) - 1:
                    edges.update(bottom=(10, "1F3A5F"))
                if 0 < i < len(rows) - 1:
                    edges.update(bottom=(2, "BBBBBB"))
                if edges:
                    _border(tcpr, **edges)
            if i == 0:
                trpr = tbl.rows[0]._tr.get_or_add_trPr()
                h = OxmlElement("w:tblHeader"); trpr.append(h)
            cs = OxmlElement("w:cantSplit"); tbl.rows[i]._tr.get_or_add_trPr().append(cs)
        src = div.find("p", class_="src")
        if src:
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            self.inline(p, src, size=7.5)
        else:
            self.doc.add_paragraph()

    def figure(self, fig, title: str):
        slug = fig["id"][len("fig-"):]
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(str(self.fig_png(slug)), width=Inches(6.3))
        self.fig_n += 1
        c = self.doc.add_paragraph(style="Caption")
        c.paragraph_format.keep_with_next = True
        c.add_run("Figure ")
        _fld(c, r"SEQ Figure \* ARABIC", str(self.fig_n))
        c.add_run(". " + re.sub(r"^Figure \d+\.\s*", "", title))

    def equation(self, div):
        for m in div.find_all("math"):
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if not self.math_el(p, m, True):
                ann = m.find("annotation")
                self.math_image(p, ann.get_text() if ann else m.get_text(), True)

    def callout(self, div):
        for ch in div.find_all("p"):
            p = self.para(ch, align=WD_ALIGN_PARAGRAPH.LEFT)
            p.paragraph_format.left_indent = Inches(0.2)
            _border(p._p.get_or_add_pPr(), left=(18, "2A7F7F"))

    def walk(self, container, titles: dict, pending_headings: list):
        for el in container.children:
            if isinstance(el, NavigableString) or el.name is None:
                continue
            cls = el.get("class") or []
            n = el.name
            if n == "h2":
                h = self.doc.add_heading(level=1)
                h.paragraph_format.page_break_before = not self.no_break_next
                self.no_break_next = False
                num = el.find("span", class_="num")
                text = el.get_text().strip()
                h.add_run((num.get_text() + " " + text[len(num.get_text()):].strip()) if num else text)
                pending_headings.append(("h", 1, h.text))
            elif n == "h3":
                h = self.doc.add_heading(level=2)
                h.add_run(" ".join(el.get_text().split()))
                pending_headings.append(("h", 2, h.text))
            elif n == "h4":
                h = self.doc.add_heading(level=3)
                h.add_run(" ".join(el.get_text().split()))
                if self.compact:
                    h.paragraph_format.space_before, h.paragraph_format.space_after = Pt(5), Pt(1)
                    for r_ in h.runs:
                        r_.font.size = Pt(10.2)
            elif n == "p":
                if "lede" in cls or "src" in cls:
                    self.para(el, align=WD_ALIGN_PARAGRAPH.LEFT, size=8.5)
                else:
                    self.para(el)
            elif n in ("ul", "ol"):
                for li in el.find_all("li", recursive=False):
                    self.para(li, style="List Bullet" if n == "ul" else "List Number")
            elif n == "figure":
                self.figure(el, titles.get(el["id"][len("fig-"):], ""))
            elif n == "div" and "tbl" in cls:
                self.table(el)
            elif n == "div" and "eq" in cls:
                self.equation(el)
            elif n == "div" and "callout" in cls:
                self.callout(el)
            elif n in ("div", "section"):
                self.walk(el, titles, pending_headings)


# ----------------------------------------------------------------------------------------------- the document
def _toc_block(doc, title: str, instr: str, entries: list[tuple[str, str, int]], note: str | None = None):
    h = doc.add_paragraph(style="Heading 1")
    h.paragraph_format.page_break_before = True
    h.add_run(title)
    # remove from the TOC itself: use a paragraph-level style with no outline entry
    ppr = h._p.get_or_add_pPr()
    ol = OxmlElement("w:outlineLvl"); ol.set(qn("w:val"), "9"); ppr.append(ol)
    if note:
        n = doc.add_paragraph()
        r = n.add_run(note); r.italic = True; r.font.size = Pt(8)
    pars = []
    for text, pg, lvl in entries:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.25 * (lvl - 1))
        p.paragraph_format.space_after = Pt(1)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        pPr = p._p.get_or_add_pPr()
        tabs = OxmlElement("w:tabs")
        tb = OxmlElement("w:tab"); tb.set(qn("w:val"), "right"); tb.set(qn("w:leader"), "dot"); tb.set(qn("w:pos"), "9350")
        tabs.append(tb); pPr.append(tabs)
        r = p.add_run(f"{text}\t{pg}")
        r.bold = lvl == 1 and "Figure" not in instr and "Table" not in instr
        pars.append(p)
    if not pars:
        return
    first, last = pars[0], pars[-1]
    # wrap the cached entries in one TOC field: begin+instr+separate before the first entry, end after the last
    def fc(kind):
        r = OxmlElement("w:r"); f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), kind); r.append(f); return r
    it = OxmlElement("w:r"); t = OxmlElement("w:instrText"); t.set(qn("xml:space"), "preserve"); t.text = f" {instr} "; it.append(t)
    runs = [fc("begin"), it, fc("separate")]
    ppr = first._p.find(qn("w:pPr"))
    idx = list(first._p).index(ppr) + 1 if ppr is not None else 0
    for k, r in enumerate(runs):
        first._p.insert(idx + k, r)
    last._p.append(fc("end"))


def _hyperlink(paragraph, url: str, text: str, size: float = 9.4) -> None:
    """An external hyperlink (clickable in Word) showing a short label."""
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    r_id = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), r_id)
    h.set(qn("w:history"), "1")
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    col = OxmlElement("w:color"); col.set(qn("w:val"), "1F3A5F"); rpr.append(col)
    u = OxmlElement("w:u"); u.set(qn("w:val"), "single"); rpr.append(u)
    sz = OxmlElement("w:sz"); sz.set(qn("w:val"), str(int(size * 2))); rpr.append(sz)
    r.append(rpr)
    t = OxmlElement("w:t"); t.text = text; r.append(t)
    h.append(r)
    paragraph._p.append(h)


def _shade(cell, fill: str) -> None:
    tcpr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), fill)
    tcpr.append(sh)


def _cell_margins(table, left=0, right=0, top=0, bottom=0) -> None:
    tblpr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for side, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:w"), str(int(v))); e.set(qn("w:type"), "dxa")
        mar.append(e)
    tblpr.append(mar)


def _cream_background(doc) -> None:
    """Page colour for the whole document, as in the PDF."""
    bg = OxmlElement("w:background")
    bg.set(qn("w:color"), CREAM)
    doc.element.insert(0, bg)
    st = doc.settings.element
    zoom = st.find(qn("w:zoom"))
    node = OxmlElement("w:displayBackgroundShape")
    if zoom is not None:
        zoom.addnext(node)
    else:
        st.insert(0, node)


def _cover(doc, meta: dict) -> None:
    """A cover like the PDF's: navy field with the title, an amber rule, and a cream band with the contact details."""
    t = doc.add_table(rows=3, cols=1)
    t.autofit = False
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    _cell_margins(t)
    heights = [Mm(196), Mm(9), Mm(85)]
    fills = ["1F3A5F", "D99A1E", CREAM]
    for row, h, fill in zip(t.rows, heights, fills):
        row.height, row.height_rule = h, WD_ROW_HEIGHT_RULE.EXACTLY
        row.cells[0].width = Mm(210)
        _shade(row.cells[0], fill)
    c = t.rows[0].cells[0]
    first = c.paragraphs[0]
    first.paragraph_format.space_before, first.paragraph_format.left_indent, first.paragraph_format.right_indent = Mm(30), Mm(22), Mm(22)
    r = first.add_run(f"{meta['prepared_for']} · {meta['date_month_year']}".upper())
    r.bold = True; r.font.size = Pt(10); r.font.color.rgb = RGBColor(0xD9, 0x9A, 0x1E)

    def line(text, size, color, bold=False, before=0, after=0):
        p = c.add_paragraph()
        p.paragraph_format.left_indent, p.paragraph_format.right_indent = Mm(22), Mm(22)
        p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(before), Pt(after)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r_ = p.add_run(text)
        r_.bold, r_.font.size, r_.font.color.rgb = bold, Pt(size), color
        return p
    line("The Economics", 36, RGBColor(255, 255, 255), True, 28, 0)
    line("of Payment Failure", 36, RGBColor(255, 255, 255), True, 0, 10)
    rule = c.add_paragraph()
    rule.paragraph_format.left_indent, rule.paragraph_format.right_indent = Mm(22), Mm(150)
    _border(rule._p.get_or_add_pPr(), bottom=(19, "D99A1E"))
    line(meta["subtitle"], 14, RGBColor(0xDC, 0xE5, 0xEE), False, 14, 8).paragraph_format.right_indent = Mm(50)
    line(meta.get("cover_line", ""), 10.5, RGBColor(0xDC, 0xE5, 0xEE), False, 18, 0)
    line(meta["version_line"], 10.5, RGBColor(0xDC, 0xE5, 0xEE), False, 4, 0)
    # the amber strip needs a tiny paragraph so that Word does not add height
    for row in (t.rows[1],):
        pp = row.cells[0].paragraphs[0]
        pp.paragraph_format.space_after = Pt(0)
        pp.add_run("").font.size = Pt(1)
    band = t.rows[2].cells[0]
    inner = band.add_table(rows=1, cols=2)
    _cell_margins(inner, left=0, right=0, top=0, bottom=0)
    left, right = inner.rows[0].cells
    for cell, head, lines in [(left, "Contact", [meta["author_line"], f"Email  {meta['email']}", f"Telephone  {meta['telephone']}", f"ORCID  {meta['orcid']}"]),
                              (right, "Research materials and reproducibility", [("Source code  ", meta["source_code"]), ("Dashboard  ", meta["dashboard"]),
                                                                               "Data, code, figures, tables and an Excel version of the analysis are in the repository."])]:
        p0 = cell.paragraphs[0]
        p0.paragraph_format.left_indent, p0.paragraph_format.space_before = Mm(22), Mm(10)
        r0 = p0.add_run(head.upper()); r0.bold = True; r0.font.size = Pt(9.4); r0.font.color.rgb = NAVY
        for i, tx in enumerate(lines):
            p_ = cell.add_paragraph()
            p_.paragraph_format.left_indent, p_.paragraph_format.space_after = Mm(22), Pt(1)
            p_.alignment = WD_ALIGN_PARAGRAPH.LEFT
            if isinstance(tx, tuple):
                from .report import link_label
                r_ = p_.add_run(tx[0]); r_.font.size = Pt(9.4)
                if str(tx[1]).startswith("http"):
                    _hyperlink(p_, tx[1], link_label(tx[1]))
                else:
                    p_.add_run(tx[1]).font.size = Pt(9.4)
                continue
            r_ = p_.add_run(tx)
            r_.font.size = Pt(9.4)
            r_.bold = (head == "Contact" and i == 0)
    # the band's own first paragraph is empty: keep it small
    band.paragraphs[0].paragraph_format.space_after = Pt(0)
    for r_ in band.paragraphs[0].runs:
        r_.font.size = Pt(1)


def _glance_image(pdf, out: Path):
    """The one-page infographic as the PDF prints it, cropped to the text area."""
    if not pdf:
        return None
    import fitz
    from .flow import LIMIT
    d = fitz.open(pdf)
    page = next((pg for pg in d if "at a glance" in pg.get_text().lower()), None)
    if page is None:
        return None
    m = 18 * 72 / 25.4
    clip = fitz.Rect(m - 8, 40, page.rect.width - m + 8, LIMIT + 6)
    page.get_pixmap(dpi=170, clip=clip).save(str(out))
    return out


def build_docx(res: dict, root: Path, out_dir: Path, rep: dict) -> Path:
    from .pipeline import OUT, figure_file, load_figure_index
    from .report import context
    ctx = context(res)
    meta = {**rep["meta"], "cover_line": f"{ctx['failed_fees_m']} in fees on failed transactions  ·  {ctx['attempts']} payment attempts  ·  {ctx['n_markets_words']} African markets"}
    font = body_font()
    html = (out_dir / "The_Economics_of_Payment_Failure.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    idx = load_figure_index()
    titles = dict(zip(idx.slug, idx.title))
    tmp = out_dir / "_docx_tmp"
    tmp.mkdir(exist_ok=True)

    doc = Document()
    _style_fonts(doc, font)
    _cream_background(doc)
    doc.core_properties.title = meta["title"]
    doc.core_properties.author = meta["author"]
    doc.core_properties.subject = f"{meta['version_line']} · {meta['prepared_for']}"
    sec = doc.sections[0]                                  # section 1: the cover, full bleed, no footer
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Mm(0)
    sec.header_distance = sec.footer_distance = Mm(0)
    _cover(doc, meta)
    sec2 = doc.add_section(WD_SECTION.NEW_PAGE)            # section 2: the report
    sec2.page_width, sec2.page_height = Mm(210), Mm(297)
    sec2.left_margin = sec2.right_margin = Mm(22)
    sec2.top_margin, sec2.bottom_margin = Mm(22), Mm(24)
    sec2.header_distance, sec2.footer_distance = Mm(10), Mm(10)
    _footer(sec2, meta, font)
    for p_ in doc.paragraphs[-1:]:                         # the paragraph that carries the section break must not add a page
        p_.paragraph_format.space_after = Pt(0)
        p_.paragraph_format.line_spacing = Pt(1)

    xslt = _xsl()
    b = Builder(doc, font, xslt, tmp, lambda slug: figure_file(slug, ("png", "svg")))
    heads: list = []
    front = soup.find("section", class_="front")
    if front is not None:
        b.compact, b.no_break_next = True, True
        b.walk(front, titles, [])                          # page 2: the executive summary
        b.compact = False
    img = _glance_image(rep.get("pdf"), tmp / "glance.png")
    if img is not None:                                    # page 3: the one-page infographic, as the PDF prints it
        pg_ = doc.add_paragraph()
        pg_.add_run().add_break(WD_BREAK.PAGE)
        pg_.paragraph_format.space_after = Pt(0)
        pp = doc.add_paragraph()
        pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pp.paragraph_format.space_before = Pt(0)
        pp.add_run().add_picture(str(img), width=Mm(166))
    ent, pg = rep["entries"], rep["pages"] or {}
    note = "Page numbers shown are those of the PDF. Right-click the list and choose Update Field to match Word's pagination."
    _toc_block(doc, "Contents", r'TOC \o "1-2" \h \z \u', [(e["text"], pg.get(e["id"], ""), e["level"]) for e in ent["contents"]], note)
    _toc_block(doc, "List of figures", r'TOC \h \z \c "Figure"', [(e["text"], pg.get(e["id"], ""), 1) for e in ent["figures"]])
    _toc_block(doc, "List of tables", r'TOC \h \z \c "Table"', [(e["text"], pg.get(e["id"], ""), 1) for e in ent["tables"]])
    main = soup.find("main")
    b.walk(main, titles, heads)

    out = out_dir / "The_Economics_of_Payment_Failure.docx"
    doc.save(out)
    for f in tmp.glob("*"):
        f.unlink()
    tmp.rmdir()
    return out
