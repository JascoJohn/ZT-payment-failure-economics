"""03  Payment type, market, currency, sector, Pareto, drivers, quintiles.

Reads:   outputs/intermediate/prepared.pkl (written by 01G)
Writes:  outputs/03_concentration/tables/*.csv and figures/ (PNG, SVG, HTML)
Run:     python scripts/03_concentration.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from payfail.runner import main  # noqa: E402

if __name__ == "__main__":
    main("03")
