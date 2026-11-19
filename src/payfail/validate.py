"""Stage 11: integrity checks, comparison with the baseline, independent recomputation and the audit.

Every check ends as PASS, FAIL (something is wrong; the stage exits with an error) or FLAG (a finding for the author to
decide; nothing was changed). `outputs/audit_report.md` lists all of them. tests/test_pipeline.py runs this module under pytest.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .config import ROOT, load_config
from .pipeline import OUT, SCRIPTS


@dataclass
class Check:
    section: str
    name: str
    status: str            # PASS | FAIL | FLAG
    detail: str = ""


@dataclass
class Audit:
    checks: list[Check] = field(default_factory=list)

    def add(self, section: str, name: str, ok: bool | None, detail: str = "", flag: bool = False) -> None:
        status = "FLAG" if (flag and not ok) else ("PASS" if ok else "FAIL")
        self.checks.append(Check(section, name, status, str(detail)))

    def failed(self) -> list[Check]:
        return [c for c in self.checks if c.status == "FAIL"]

    def flagged(self) -> list[Check]:
        return [c for c in self.checks if c.status == "FLAG"]


def _close(a, b, rel=1e-9, ab=1e-9) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, int) and isinstance(b, int):
            return a == b
        return math.isclose(a, b, rel_tol=rel, abs_tol=ab)
    return a == b


def _diff_json(a, b, path="", out=None):
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in a:
            if k not in b:
                out.append(f"{path}/{k}: missing")
            else:
                _diff_json(a[k], b[k], f"{path}/{k}", out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}: length {len(a)} -> {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                _diff_json(x, y, f"{path}[{i}]", out)
    elif not _close(a, b):
        out.append(f"{path}: {a} -> {b}")
    return out


# ------------------------------------------------------------------------------------------ A. integrity
def integrity(au: Audit, res: dict, prep, cfg: dict) -> None:
    S = "A. Integrity"
    h = res["headline"]
    au.add(S, "Records and attempts tie to the raw workbook", h["records"] == 62_684 and h["attempts"] == 1_645_892 and h["failed"] == 1_019_793,
           f"{h['records']:,} records, {h['attempts']:,} attempts, {h['failed']:,} failed")
    au.add(S, "Translatable + untranslatable records = all records", h["records_translatable"] + prep.stats["untranslatable_records"] == h["records"])
    au.add(S, "Fees = failed + successful", abs(h["fees"] - (h["failed_fees"] + h["succ_fees"])) < 1e-6)
    b = res["bridge"]
    au.add(S, "Exposure bridge is exclusive and exhaustive", abs(b.f_fee.sum() - h["failed_fees"]) < 1e-6 and abs(b.share.sum() - 1) < 1e-12)
    au.add(S, "Escalation account is 47087 only", prep.stats["escalation_customers"] == [47087], prep.stats["escalation_customers"])
    j = res["january"]
    comp = j["components"].set_index("component").usd
    au.add(S, "January decomposition has no residual", abs(j["residual"]) < 1e-6 and abs(comp.iloc[:-1].sum() - comp["January"]) < 1e-6, f"residual {j['residual']:.2e}")
    tx = prep.tx
    au.add(S, "Constant-currency and reported fees use the same population", bool((tx.loc[~tx.fx_ok, "fee_cc"] == 0).all() and (tx.loc[~tx.fx_ok, "fee"] == 0).all()))
    r = prep.rates_monthly
    au.add(S, "SLL redenomination applied (every month on old-leone scale)", bool(r[r.ccy == "SLL"].r_avg.max() < 0.001))
    s = res["recovery"]["scenarios"].set_index("scenario").incremental_fees
    au.add(S, "Recovery scenarios ordered conservative < base < optimistic", bool(s["Conservative"] < s["Base"] < s["Optimistic"]))
    c = res["recovery"]["contribution"]
    au.add(S, "Fee revenue remaining at 0% cost equals the base case", bool(np.isclose(c.contribution.iloc[0], s["Base"])))
    p = res["laney"]["patterns"]
    au.add(S, "Laney: 10 eligible cells, 210 tests, σz above 1 everywhere", len(p) == 10 and res["laney"]["tests"] == 210 and bool((p.sigma_z > 1).all()))
    cc = res["customer_concentration"]
    au.add(S, "Customer concentration: 5,108 ranked; top 1% is 51 customers", cc["customers"] == 5108 and cc["top1pct_n"] == 51,
           f"{cc['customers']:,} customers, top 1% = {cc['top1pct_n']} customers holding {cc['top1pct']:.1%}, top 10 {cc['top10']:.1%}")


# ------------------------------------------------------------------------------------------ B. baseline
def _approved() -> list[dict]:
    import yaml
    f = ROOT / "baseline" / "approved_changes.yaml"
    return yaml.safe_load(f.read_text(encoding="utf-8")).get("changes", []) if f.exists() else []


def _which(kind: str, name: str, groups: list[dict]) -> str | None:
    for g in groups:
        if any(re.fullmatch(p, name) for p in g.get(kind, [])):
            return g["item"]
    return None


def against_baseline(au: Audit, res: dict, ctx: dict) -> None:
    """Every difference from baseline/ must belong to a change you approved (baseline/approved_changes.yaml)."""
    S = "B. Baseline"
    base = ROOT / "baseline"
    f = base / "results_baseline.json"
    if not f.exists():
        au.add(S, "baseline/results_baseline.json exists", False, "missing")
        return
    groups = _approved()
    changes: list[str] = []
    new = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    d = _diff_json(json.loads(f.read_text(encoding="utf-8")), new)
    bad = [x for x in d if _which("json", x.split(":")[0], groups) is None]
    for x in d:
        changes.append(f"| results.json | `{x.split(':')[0]}` | {x.split(':', 1)[1].strip() if ':' in x else ''} | {_which('json', x.split(':')[0], groups) or '**NOT APPROVED**'} |")
    au.add(S, "results.json matches the baseline except approved changes (ints exact, floats to 1e-9)", not bad,
           "; ".join(bad[:5]) if bad else f"{len(d)} approved differences; every other value identical")
    tdir = base / "tables"
    mism, n, ok_changed = [], 0, []
    for bf in sorted(tdir.glob("*.csv")) if tdir.exists() else []:
        hits = list(OUT.glob(f"*/tables/{bf.name}"))
        if not hits:
            mism.append(f"{bf.name}: not produced")
            continue
        a_, b_ = pd.read_csv(bf), pd.read_csv(hits[0])
        n += 1
        diff = None
        if list(a_.columns) != list(b_.columns) or a_.shape != b_.shape:
            diff = "shape/columns differ"
        else:
            for col in a_.columns:
                if pd.api.types.is_numeric_dtype(a_[col]) and pd.api.types.is_numeric_dtype(b_[col]):
                    if not np.allclose(a_[col], b_[col], rtol=1e-9, atol=1e-9, equal_nan=True):
                        diff = f"{col} differs"
                elif not a_[col].astype(str).equals(b_[col].astype(str)):
                    diff = f"{col} differs"
        if diff:
            item = _which("tables", bf.name, groups)
            changes.append(f"| table {bf.name} | {diff} | | {item or '**NOT APPROVED**'} |")
            if item is None:
                mism.append(f"{bf.name}: {diff}")
    au.add(S, "Every baseline table (CSV) matches except approved changes", not mism, "; ".join(mism[:6]) if mism else f"{n} tables compared")
    tf = base / "report_tokens_baseline.json"
    if tf.exists():
        old = json.loads(tf.read_text(encoding="utf-8"))
        diffs = [k for k, v in old.items() if ctx.get(k) != v]
        unappr = [k for k in diffs if _which("tokens", k, groups) is None]
        for k in diffs:
            changes.append(f"| rendered value `{k}` | {old[k]} | {ctx.get(k)} | {_which('tokens', k, groups) or '**NOT APPROVED**'} |")
        au.add(S, "Every rendered report value matches the baseline except approved changes (exact text)", not unappr,
               "; ".join(f"{k}: {old[k]} -> {ctx.get(k)}" for k in unappr[:5]) if unappr else
               f"{len(old) - len(diffs)} identical, {len(diffs)} approved changes, {len(set(ctx) - set(old))} new values")
        new_keys = sorted(set(ctx) - set(old))
        for k in new_keys:
            changes.append(f"| new value `{k}` | | {ctx[k]} | {_which('tokens', k, groups) or 'new'} |")
    NL = chr(10)
    head = ("# Changes from the baseline" + NL + NL + "Every rendered value, table or results.json entry that differs from `baseline/`, and the approved item that covers it." + NL + NL
            + "| What | Baseline | Now | Approved item |" + NL + "| --- | --- | --- | --- |" + NL)
    (OUT / "changes_from_baseline.md").write_text(head + NL.join(changes) + NL, encoding="utf-8")


def run_validate() -> dict:
    from .pipeline import full_results, load_prep
    from .report import context
    cfg, prep = load_prep()
    res = full_results(prep)
    ctx = context(res)
    au = Audit()
    integrity(au, res, prep, cfg)
    against_baseline(au, res, ctx)
    try:
        from .audit import run_audit
        run_audit(au, res, prep, cfg, ctx)
    except ModuleNotFoundError as e:
        if "payfail.audit" not in str(e):
            raise
    write_report(au)
    n_fail, n_flag = len(au.failed()), len(au.flagged())
    out = {"checks": len(au.checks), "pass": sum(c.status == "PASS" for c in au.checks), "fail": n_fail, "flagged for you": n_flag,
           "report": "outputs/audit_report.md"}
    if n_fail:
        for c in au.failed():
            print(f"  FAIL  [{c.section}] {c.name}: {c.detail}")
        raise SystemExit(f"{n_fail} validation check(s) failed. See outputs/audit_report.md")
    return out


def write_report(au: Audit) -> None:
    order, secs = [], {}
    for c in au.checks:
        secs.setdefault(c.section, []).append(c)
        if c.section not in order:
            order.append(c.section)
    n = len(au.checks)
    L = ["# Audit report", "",
         f"{n} checks: **{sum(c.status == 'PASS' for c in au.checks)} pass**, **{len(au.failed())} fail**, "
         f"**{len(au.flagged())} flagged for the author**. A FLAG is a finding that needs a decision; nothing was changed because of it.", ""]
    if au.flagged():
        L += ["## Flagged for you", ""] + [f"- **[{c.section}] {c.name}.** {c.detail}" for c in au.flagged()] + [""]
    for s in order:
        L += [f"## {s}", "", "| Result | Check | Detail |", "| --- | --- | --- |"]
        for c in secs[s]:
            L.append(f"| {c.status} | {c.name} | {c.detail.replace('|', '/').replace(chr(10), ' ')[:600]} |")
        L.append("")
    (OUT / "audit_report.md").write_text("\n".join(L), encoding="utf-8")
