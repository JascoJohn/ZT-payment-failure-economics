"""01D  Loads daily exchange rates unchanged.

Reads:   data/raw/ZT_EA_Regional_Data.xlsx (exchange_rates)
Writes:  outputs/01D_raw_rates/tables/*.csv
Run:     python scripts/01D_raw_rates.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from payfail.runner import main  # noqa: E402

if __name__ == "__main__":
    main("01D")
