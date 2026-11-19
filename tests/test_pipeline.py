"""Integrity checks: totals tie, categories are exclusive, the decomposition has no residual,
and the report template renders the numbers the pipeline produces."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from payfail import analyse, load_config, prepare  # noqa: E402


@pytest.fixture(scope="session")
def run():
    cfg = load_config()
    prep = prepare(cfg)
    return cfg, prep, analyse(prep, cfg)


def test_headline_reconciles_to_raw_data(run):
    _, prep, res = run
    h = res["headline"]
    assert h["records"] == 62_684
    assert h["attempts"] == 1_645_892
    assert h["failed"] == 1_019_793
    assert h["records_translatable"] + prep.stats["untranslatable_records"] == h["records"]
    assert abs(h["fees"] - (h["failed_fees"] + h["succ_fees"])) < 1e-6


def test_bridge_is_exclusive_and_exhaustive(run):
    _, prep, res = run
    b = res["bridge"]
    assert abs(b.f_fee.sum() - res["headline"]["failed_fees"]) < 1e-6
    assert abs(b.share.sum() - 1) < 1e-12
    assert set(prep.tx.category.unique()) <= {"Extreme-volume anomaly", "Escalation", "Remaining"}
    assert prep.stats["escalation_customers"] == [47087]


def test_january_decomposition_has_no_residual(run):
    _, _, res = run
    j = res["january"]
    assert abs(j["residual"]) < 1e-6
    comp = j["components"].set_index("component").usd
    assert abs(comp.iloc[:-1].sum() - comp["January"]) < 1e-6


def test_fx_constant_currency_population_matches_reported(run):
    _, prep, _ = run
    tx = prep.tx
    assert (tx.loc[~tx.fx_ok, "fee_cc"] == 0).all()
    assert (tx.loc[~tx.fx_ok, "fee"] == 0).all()


def test_sll_redenomination_applied(run):
    _, prep, _ = run
    r = prep.rates_monthly
    sll = r[(r.ccy == "SLL")].r_avg
    assert sll.max() < 0.001          # every month on old-leone scale after the fix


def test_recovery_scenarios_are_ordered(run):
    _, _, res = run
    s = res["recovery"]["scenarios"].set_index("scenario").incremental_fees
    assert s["Conservative"] < s["Base"] < s["Optimistic"]
    c = res["recovery"]["contribution"]
    assert np.isclose(c.contribution.iloc[0], s["Base"])


def test_laney_sigma_and_flags(run):
    _, _, res = run
    p = res["laney"]["patterns"]
    assert len(p) == 10 and res["laney"]["tests"] == 210
    assert (p.sigma_z > 1).all()      # overdispersion: binomial limits would be too narrow


def test_report_content_renders(run):
    """Every {{number}} in the report content has a value, and key figures appear."""
    import re
    from payfail.report import context, render
    _, _, res = run
    ctx = context(res)
    content = ROOT / "report" / "content"
    for name in ["01_summary.md", "02_at_a_glance.html", "03_main_report.md", "brief.html", "00_cover.html"]:
        text = re.sub(r"\{\{(meta|fig|tab)[.:]\w+\}\}", "", (content / name).read_text(encoding="utf-8"))
        out = render(text, ctx)
        assert "{{" not in out, name
    main = render(re.sub(r"\{\{(fig|tab):\w+\}\}", "", (content / "03_main_report.md").read_text(encoding="utf-8")), ctx)
    assert "$2.78M" in main and "$1,708.5K" in main and "$253.7K" in main


def test_report_figures_exist_in_figure_list():
    import re
    from payfail.figures import REPORT_ORDER
    text = (ROOT / "report" / "content" / "03_main_report.md").read_text(encoding="utf-8")
    used = re.findall(r"\[\[figure (\w+)\]\]", text)
    assert used == REPORT_ORDER, "report figures must appear in REPORT_ORDER order"
