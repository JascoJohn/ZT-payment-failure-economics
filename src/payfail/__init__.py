"""payfail: the economics of payment failure, ZT East Africa, Jan 2022 - Apr 2024.

One pipeline feeds the report, the dashboard, the Excel workbook and the tests:

    from payfail import load_config, prepare, analyse
    cfg = load_config()
    prep = prepare(cfg)
    res = analyse(prep, cfg)
"""
from .config import load_config
from .data import prepare
from .analysis import analyse

__all__ = ["load_config", "prepare", "analyse"]
