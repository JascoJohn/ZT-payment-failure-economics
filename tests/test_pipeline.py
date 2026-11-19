"""pytest wrapper around stage 11 (src/payfail/validate.py). The checks live there, not here.

Run `python run_pipeline.py` first so that the stage outputs exist, then:  pytest -q
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from payfail.pipeline import INTER  # noqa: E402

needs_run = pytest.mark.skipif(not (INTER / "prepared.pkl").exists(), reason="run `python run_pipeline.py` first")


@needs_run
def test_integrity_baseline_and_audit_have_no_failures():
    """Integrity checks, comparison with baseline/, independent recomputation and the audit: no FAIL.
    FLAG findings are for the author to decide and do not fail the run; see outputs/audit_report.md."""
    from payfail.validate import run_validate
    out = run_validate()
    assert out["fail"] == 0


@needs_run
def test_every_stage_has_a_script():
    from payfail.pipeline import ORDER, SCRIPTS
    for code in ORDER:
        assert (ROOT / "scripts" / SCRIPTS[code]).exists(), code
