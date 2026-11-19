"""01G  USD translation of every record, flags, anomaly rules, exposure category.

Reads:   raw workbook (cached by 01B) and config/assumptions.yaml
Writes:  outputs/01G_transactions/tables/*.csv and figures/ (PNG, SVG, HTML)
Run:     python scripts/01G_transactions.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from payfail.runner import main  # noqa: E402

if __name__ == "__main__":
    main("01G")
