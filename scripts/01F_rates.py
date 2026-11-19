"""01F  SLL restatement, spike screen, monthly average / month-end / 2022 base rates.

Reads:   raw workbook (exchange_rates, transactions months)
Writes:  outputs/01F_rates/tables/*.csv
Run:     python scripts/01F_rates.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from payfail.runner import main  # noqa: E402

if __name__ == "__main__":
    main("01F")
