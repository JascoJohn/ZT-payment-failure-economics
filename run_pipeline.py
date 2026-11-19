"""Run the whole analysis, stage by stage: 00 -> 01A..01G -> 02..08 -> 09 (Excel) -> 10 (report) -> 11 (validate).

    python run_pipeline.py                  # everything
    python run_pipeline.py --from 05        # restart from stage 05 (uses what earlier stages saved)
    python run_pipeline.py --only 03        # one stage
    python run_pipeline.py --skip-excel     # leave out stage 09
    python run_pipeline.py --recalc-excel   # recalculate the workbook after building it (LibreOffice, or Excel on Windows)

Stage 01E (data quality) reports on what 01F and 01G produce, so it runs after them; its number does not change.
Each stage is also a script in scripts/ that you can run on its own.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from payfail.pipeline import CHAPTERS, ORDER, OUT, SCRIPTS  # noqa: E402

TITLES = {"00": "Environment check", "09": "Excel workbook", "10": "Report, brief and Word copy", "11": "Validation and audit"}
TITLES.update({k: v[2] for k, v in CHAPTERS.items()})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="start", metavar="STAGE", help="first stage to run, e.g. 05 or 01E")
    ap.add_argument("--only", metavar="STAGE", help="run a single stage")
    ap.add_argument("--skip-excel", action="store_true", help="skip stage 09")
    ap.add_argument("--recalc-excel", action="store_true", help="recalculate the workbook after stage 09")
    a = ap.parse_args()
    stages = list(ORDER)
    for name, v in [("--from", a.start), ("--only", a.only)]:
        if v and v.upper() not in stages:
            ap.error(f"{name}: unknown stage '{v}'. Stages: {', '.join(stages)}")
    if a.only:
        stages = [a.only.upper()]
    elif a.start:
        stages = stages[stages.index(a.start.upper()):]
    if a.skip_excel and "09" in stages:
        stages.remove("09")
    results, t0 = [], time.time()
    for n, code in enumerate(stages, start=1):
        t = time.time()
        cmd = [sys.executable, "-W", "ignore", str(ROOT / "scripts" / SCRIPTS[code])]
        if code == "09" and a.recalc_excel:
            cmd.append("--recalc")
        print(f"\n[{n}/{len(stages)}] {code}  {TITLES[code][:90]}", flush=True)
        p = subprocess.run(cmd, cwd=ROOT)
        ok = p.returncode == 0
        results.append((code, "ok" if ok else f"FAILED ({p.returncode})", time.time() - t))
        if not ok:
            print(f"      stage {code} failed; stopping. Fix it, then: python run_pipeline.py --from {code}")
            break
    print("\n" + "=" * 62 + "\nSummary")
    for code, status, sec in results:
        print(f"  {code:<4}{status:<14}{sec:>6.0f}s   {TITLES[code][:60]}")
    print(f"  total {time.time() - t0:.0f}s")
    if all(s == "ok" for _, s, _ in results):
        try:
            import json
            h = json.loads((OUT / "results.json").read_text())["headline"]
            print(f"\nFees on failed transactions ${h['failed_fees']:,.0f} ({h['fee_share']:.1%} of recorded fees); "
                  f"count failure rate {h['count_rate']:.1%}.")
        except Exception:
            pass
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
