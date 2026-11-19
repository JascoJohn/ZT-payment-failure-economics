"""10  Renders the report, the executive brief and the Word version.

Reads:   results of 01E and 02-08 (outputs/intermediate/), report/content/, report/assets/
Writes:  outputs/results.json, outputs/report/ (PDF, HTML, DOCX)
Run:     python scripts/10_report.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from payfail import runner  # noqa: E402

if __name__ == "__main__":
    runner.cli("10")
