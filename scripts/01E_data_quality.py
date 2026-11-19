"""01E  The three flags, untranslatable records, SLL evidence, spike days, legacy codes, reconciliation with the brief, headline sensitivity.

Reads:   outputs/intermediate/prepared.pkl (from 01G) and the raw workbook
Writes:  outputs/01E_data_quality/tables/*.csv
Run:     python scripts/01E_data_quality.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from payfail.runner import main  # noqa: E402

if __name__ == "__main__":
    main("01E")
