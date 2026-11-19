"""09  Builds the whole Excel workbook (sheets 00_README to 99_Checks).

Reads:   outputs/intermediate/ (prepared data, all chapter results)
Writes:  outputs/payment_failure_analysis.xlsx
Run:     python scripts/09_excel_workbook.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from payfail import runner  # noqa: E402

if __name__ == "__main__":
    runner.cli("09")
