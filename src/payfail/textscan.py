"""Scan the report text for typed numbers. Used by the audit (stage 11) and for planning the move to {{tokens}}."""
from __future__ import annotations

import html
import re
from pathlib import Path

TOKEN = re.compile(r"\{\{[^}]+\}\}")
NUM = re.compile(r"(?<![\w.#/-])(?:[−+–-]?\$?\d[\d,]*(?:\.\d+)?)(?:\s?(?:%|K\b|M\b|bn\b|trillion\b|million\b|×|x\b|pp\b|th\b|st\b|nd\b|rd\b|percentage points?\b))?")
WORDS = r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty|hundred|half|third|quarter)\b"
WORDNUM = re.compile(r"\b(?:(?:one|two|three|four|five|six|seven|eight|nine|ten|twenty|thirty)(?:-\w+)? in (?:one|two|three|four|five|six|seven|eight|nine|ten)|"
                     r"(?:Twenty|Ten|Four|Three|Five|Six|Seven|Eight|Nine|Two|Eleven|Twelve|Thirty)\s+(?:\w+[- ]){0,2}(?:observations|cells|account-months|customers|accounts|conclusions|"
                     r"markets|months|currencies|problems|categories|measures|ways|measures|actions|workstreams|flags)|"
                     r"(?:two|three|four|five|six|seven|eight|nine|ten|twenty|thirty)\s+(?:\w+[- ]){0,2}(?:observations|cells|account-months|customers|accounts|markets|months|"
                     r"currencies|categories|measures|ways|actions|flags|extreme))", re.I)
SKIP_LINE = re.compile(r"^(\s*::: table|\s*\[\[figure|\s*\|\s*-{3})")


def clean_lines(path: Path) -> list[tuple[int, str]]:
    """Visible text lines of a content file: tokens, HTML tags, LaTeX formulas and attributes removed."""
    out = []
    in_math = False
    for i, ln in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        s = ln.strip()
        if in_math:
            in_math = not s.endswith("$$")
            continue
        if s.startswith("$$"):
            in_math = not (s.endswith("$$") and len(s) > 2)
            continue
        if SKIP_LINE.match(ln):
            if ln.strip().startswith("::: table"):
                s = re.sub(r"^::: table \w+ \|", "", s)        # the caption is text
            else:
                continue
        s = TOKEN.sub("", ln if not s.startswith("::: table") else s)
        s = re.sub(r"<style.*?</style>|<svg.*?</svg>", "", s, flags=re.S)
        s = re.sub(r"<[^>]+>", " ", s)
        s = re.sub(r"\\(.*?\\)", " ", s)                      # inline formulas
        s = html.unescape(s)
        s = re.sub(r"&\w+;|style=\"[^\"]*\"", " ", s)
        if s.strip():
            out.append((i, s))
    return out


def scan(path: Path) -> list[dict]:
    rows = []
    for i, s in clean_lines(path):
        t = re.sub(r"^\s*(?:#+\s*)?(?:Appendix [A-Z]\.|\d+(?:\.\d+)*\.?)\s+", " ", s)     # heading and list numbers
        t = re.sub(r"\b(?:Table|Figure|Section|Sections|Appendix)\s+[A-Z]?\d+(?:\.\d+)?\b", " ", t)
        t = re.sub(r"\b[A-Z]\.\d\b", " ", t)
        for m in NUM.finditer(t):
            lit = m.group(0).strip()
            if re.fullmatch(r"[−+–-]?\d", lit) and False:
                continue
            rows.append({"file": path.name, "line": i, "literal": lit, "context": t[max(0, m.start() - 45): m.end() + 35].strip()})
        for m in WORDNUM.finditer(t):
            rows.append({"file": path.name, "line": i, "literal": m.group(0).strip(), "context": t[max(0, m.start() - 40): m.end() + 40].strip(), "words": True})
    return rows
