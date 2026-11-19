"""00  Checks the Python version, packages, Chrome/Edge, the Source Sans 3 font and the raw workbook; prints what each script does.

Reads:   the environment and data/raw/ZT_EA_Regional_Data.xlsx
Writes:  the console
Run:     python scripts/00_readme_and_environment.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from payfail import runner  # noqa: E402

if __name__ == "__main__":
    runner.cli("00")
