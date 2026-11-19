"""01C  Loads customers; country and sector aliases; stale-date check.

Reads:   data/raw/ZT_EA_Regional_Data.xlsx (customer_details, transactions)
Writes:  outputs/01C_raw_customers/tables/*.csv
Run:     python scripts/01C_raw_customers.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from payfail.runner import main  # noqa: E402

if __name__ == "__main__":
    main("01C")
