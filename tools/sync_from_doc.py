"""Bring the wording of a Markdown export of the Claude Doc back into report/content/, keeping every number as a {{token}}.

    python tools/sync_from_doc.py path/to/doc_export.md            # show the diff and the numbers it could not map
    python tools/sync_from_doc.py path/to/doc_export.md --apply    # write report/content/01_summary.md and 03_main_report.md

How it works
  1. The current content files are rendered with the pipeline's numbers, so each block of text has a "rendered" twin.
  2. The export's blocks (paragraphs, list items, headings, table rows) are lined up with those twins by their wording.
  3. Inside each matched block, every rendered number is turned back into its {{key}}: first the values of the tokens
     that block already used, then numbers that map to exactly one token anywhere, then numbers that were literal
     in the old text (kept as they are). Anything else is reported as "could not map" and left as typed.
  4. Structure that the Doc cannot carry (figure placeholders, table directives, formulas, source lines) is kept.

Nothing is written without --apply. Run stage 10 afterwards to rebuild the report.
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

TOKEN = re.compile(r"\{\{(\w+)\}\}")
NUM = re.compile(r"[−+\-–]?\$?\d[\d,]*(?:\.\d+)?(?:\s?(?:%|K\b|M\b|bn\b|×|pp\b))?")
STRUCT = re.compile(r"^(\[\[figure |::: table |\$\$|Source:|Note:|Flags:|\| ?-{3})")
CAPTION = re.compile(r"^(Figure|Table) (D?\d+)\.")


def blocks(text: str) -> list[dict]:
    """Paragraph-like units, in order. kind is 'text' (editable) or 'keep' (structure that is passed through)."""
    out, para = [], []

    def flush():
        if para:
            out.append({"kind": "text", "text": " ".join(x.strip() for x in para)})
            para.clear()
    in_math = False
    for ln in text.splitlines():
        s = ln.strip()
        if in_math:
            out.append({"kind": "keep", "text": ln})
            in_math = not s.endswith("$$")
            continue
        if not s:
            flush()
            out.append({"kind": "blank", "text": ""})
        elif s.startswith("$$"):
            flush()
            out.append({"kind": "keep", "text": ln})
            in_math = not (s.endswith("$$") and len(s) > 2)
        elif STRUCT.match(s):
            flush()
            out.append({"kind": "keep", "text": ln})
        elif s.startswith(("#", ">", "|")) or re.match(r"^(\d+\.|[-*]) ", s):
            flush()
            out.append({"kind": "text", "text": ln.rstrip(), "line": True})
        else:
            para.append(ln)
    flush()
    return out


def render_text(t: str, ctx: dict, figs: dict, tabs: dict) -> str:
    t = re.sub(r"\{\{fig:(\w+)\}\}", lambda m: f"Figure {figs.get(m.group(1), '?')}", t)
    t = re.sub(r"\{\{tab:(\w+)\}\}", lambda m: f"Table {tabs.get(m.group(1), '?')}", t)
    return TOKEN.sub(lambda m: ctx.get(m.group(1), m.group(0)), t)


PREFIX = re.compile(r"^\s*(?:#+\s*)?(?:(?:\d+\.)+\d*\.?\s+|Appendix [A-Z]\.\s+)?(?:[-*]\s+|\d+\.\s+)?")


def mask(t: str) -> str:
    t = re.sub(r"^#+\s*(\d+(\.\d+)*\.?\s+)?", "", t.strip())           # heading numbers are automatic
    t = re.sub(r"[*_`|]", "", t)
    return re.sub(r"\s+", " ", NUM.sub("#", t)).strip().lower()


def back_to_tokens(doc_text: str, old_template: str | None, ctx: dict, rev: dict, figs: dict, tabs: dict, unmapped: list) -> str:
    """Replace rendered numbers in the Doc's wording with {{keys}}."""
    d = doc_text
    # figure and table references
    inv_f = {v: k for k, v in figs.items()}
    inv_t = {str(v): k for k, v in tabs.items()}
    d = re.sub(r"\bFigure (\d+)\b", lambda m: "{{fig:%s}}" % inv_f[m.group(1)] if m.group(1) in inv_f else m.group(0), d)
    d = re.sub(r"\bTable (\d+)\b", lambda m: "{{tab:%s}}" % inv_t[m.group(1)] if m.group(1) in inv_t else m.group(0), d)
    used = []
    if old_template:
        keys = [k for k in TOKEN.findall(old_template) if k in ctx]
        for k in sorted(set(keys), key=lambda k: -len(ctx[k])):
            v = ctx[k]
            if not re.search(r"\d", v):
                continue
            pat = re.compile(r"(?<![\w.,$])" + re.escape(v) + r"(?![\w])")
            if pat.search(d):
                d = pat.sub("{{%s}}" % k, d, count=keys.count(k))      # as many times as the old text used this token
                used.append(k)
    literal_old = set(NUM.findall(TOKEN.sub("", old_template or "")))

    def fix(m):
        s = m.group(0)
        if s.strip() in literal_old or not re.search(r"\d", s):
            return s
        keys = rev.get(s.strip())
        if keys and len(keys) == 1:
            return "{{%s}}" % keys[0]
        unmapped.append(s.strip())
        return s
    parts = re.split(r"(\{\{[^}]+\}\})", d)
    return "".join(p if p.startswith("{{") else NUM.sub(fix, p) for p in parts)


def sync_file(path: Path, doc_blocks: list[dict], ctx: dict, figs: dict, tabs: dict, rev: dict) -> tuple[str, list]:
    old = path.read_text(encoding="utf-8")
    ob = blocks(old)
    rendered = [render_text(b["text"], ctx, figs, tabs) if b["kind"] == "text" else b["text"] for b in ob]
    otxt = [i for i, b in enumerate(ob) if b["kind"] == "text"]
    dtxt = [b for b in doc_blocks if b["kind"] == "text" and not CAPTION.match(b["text"].strip())]
    a = [mask(rendered[i]) for i in otxt]
    b = [mask(x["text"]) for x in dtxt]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    pair: dict[int, int] = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            pair.update({otxt[i1 + k]: j1 + k for k in range(i2 - i1)})
        elif tag == "replace":
            used = set()
            for i in range(i1, i2):                      # pair by similarity inside the changed stretch
                best, bj = (0.85 if rendered[otxt[i]].lstrip().startswith("#") else 0.72), None
                for j in range(j1, j2):
                    if j in used:
                        continue
                    r = difflib.SequenceMatcher(None, a[i], b[j]).ratio()
                    if r > best:
                        best, bj = r, j
                if bj is not None:
                    used.add(bj)
                    pair[otxt[i]] = bj
    unmapped, new_lines, changes = [], [], 0
    for i, blk in enumerate(ob):
        if blk["kind"] != "text" or i not in pair:
            new_lines.append((blk, None))
            continue
        d = dtxt[pair[i]]["text"].strip()
        old_prefix = PREFIX.match(blk["text"]).group(0)
        d = PREFIX.sub("", d, count=1)                                  # numbering and list markers are not numbers to map
        new = old_prefix + back_to_tokens(d, blk["text"][len(old_prefix):], ctx, rev, figs, tabs, unmapped)
        # keep the markup the Doc export may have flattened: evidence tags and the old leading marker
        if new != blk["text"] and mask(new) != mask(rendered[i]) or TOKEN.findall(new) != TOKEN.findall(blk["text"]):
            changes += 1
        new_lines.append((blk, new))
    out, buf = [], []
    for blk, new in new_lines:
        if blk["kind"] == "blank":
            out.append("")
        elif new is not None and not blk.get("line"):
            out.append(new)
        elif new is not None:
            out.append(new)
        else:
            out.append(blk["text"])
    return "\n".join(out) + ("\n" if old.endswith("\n") else ""), unmapped


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("export", type=Path, help="Markdown export of the Claude Doc")
    ap.add_argument("--apply", action="store_true", help="write the updated content files (default: show the diff only)")
    a = ap.parse_args()
    from payfail.pipeline import full_results
    from payfail.report import context, numbering
    res = full_results()
    ctx = context(res)
    content = ROOT / "report" / "content"
    files = [content / "01_summary.md", content / "03_main_report.md"]
    figs, tabs = numbering([files[1].read_text(encoding="utf-8")])
    rev: dict[str, list[str]] = {}
    for k, v in ctx.items():
        if re.search(r"\d", v):
            rev.setdefault(v.strip(), []).append(k)
    doc_blocks = blocks(a.export.read_text(encoding="utf-8"))
    total_unmapped, any_change = [], False
    for f in files:
        new, unmapped = sync_file(f, doc_blocks, ctx, figs, tabs, rev)
        old = f.read_text(encoding="utf-8")
        diff = list(difflib.unified_diff(old.splitlines(), new.splitlines(), f"a/{f.name}", f"b/{f.name}", lineterm="", n=0))
        if diff:
            any_change = True
            print("\n".join(diff))
            print(f"\nWord-level changes in {f.name}:")
            for ol, nl in zip(old.splitlines(), new.splitlines()):
                if ol != nl:
                    ow, nw = ol.split(), nl.split()
                    parts = []
                    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ow, nw, autojunk=False).get_opcodes():
                        if tag != "equal":
                            parts.append(f"[-{' '.join(ow[i1:i2])}-] {{+{' '.join(nw[j1:j2])}+}}")
                    print("  " + "  ".join(parts)[:400])
        else:
            print(f"{f.name}: no changes")
        total_unmapped += [(f.name, u) for u in unmapped]
        if a.apply and diff:
            f.write_text(new, encoding="utf-8")
            print(f"-> wrote {f}")
    print("\nNumbers that could not be mapped to a token (left as typed):")
    for name, u in total_unmapped or [("-", "none")]:
        print(f"  {name}: {u}")
    if any_change and not a.apply:
        print("\nNothing written. Re-run with --apply to update report/content/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
