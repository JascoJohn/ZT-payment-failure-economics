"""11  Integrity checks, independent recomputation, audit, and comparison with baseline/results_baseline.json.

Reads:   raw workbook, outputs/, report/content/, baseline/
Writes:  outputs/audit_report.md; exit code 1 if a check fails
Run:     python scripts/11_validate.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from payfail import runner  # noqa: E402

if __name__ == "__main__":
    runner.cli("11")
