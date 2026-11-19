"""02  Headline, exposure bridge, monthly series, three perspectives.

Reads:   outputs/intermediate/prepared.pkl (written by 01G)
Writes:  outputs/02_scale/tables/*.csv and figures/ (PNG, SVG, HTML)
Run:     python scripts/02_scale.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from payfail.runner import main  # noqa: E402

if __name__ == "__main__":
    main("02")
