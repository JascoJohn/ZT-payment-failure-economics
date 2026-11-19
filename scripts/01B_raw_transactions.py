"""01B  Loads the transactions sheet unchanged; record and attempt counts.

Reads:   data/raw/ZT_EA_Regional_Data.xlsx (transactions)
Writes:  outputs/01B_raw_transactions/tables/*.csv
Run:     python scripts/01B_raw_transactions.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from payfail.runner import main  # noqa: E402

if __name__ == "__main__":
    main("01B")
