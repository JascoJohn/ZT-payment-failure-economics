"""07  Benchmark gap, scenarios, sensitivities, fee revenue remaining, break-even.

Reads:   outputs/intermediate/prepared.pkl (written by 01G)
Writes:  outputs/07_recovery/tables/*.csv and figures/ (PNG, SVG, HTML)
Run:     python scripts/07_recovery.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from payfail.runner import main  # noqa: E402

if __name__ == "__main__":
    main("07")
