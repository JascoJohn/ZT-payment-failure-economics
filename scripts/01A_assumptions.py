"""01A  Loads and validates config/assumptions.yaml.

Reads:   config/assumptions.yaml
Writes:  outputs/01A_assumptions/tables/*.csv
Run:     python scripts/01A_assumptions.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from payfail.runner import main  # noqa: E402

if __name__ == "__main__":
    main("01A")
