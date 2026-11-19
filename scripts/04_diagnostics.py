"""04  Anomaly tables and sensitivity, escalation, hard/mixed, persistence, tenure, lapse, Laney.

Reads:   outputs/intermediate/prepared.pkl (written by 01G)
Writes:  outputs/04_diagnostics/tables/*.csv and figures/ (PNG, SVG, HTML)
Run:     python scripts/04_diagnostics.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from payfail.runner import main  # noqa: E402

if __name__ == "__main__":
    main("04")
