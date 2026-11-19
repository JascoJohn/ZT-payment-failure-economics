"""The one figure index: outputs/figure_index.csv (written by the chapter stages) is read by the report renderer, the
dashboard and the Doc sync tool. If the file is missing (a fresh clone before the first run) the same table is built
from figures.py, so nothing breaks; stage 11 checks that the two agree."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .figures import FIG_CHAPTER, FIGURES, REPORT_ORDER, SECTION, label

INDEX = Path(__file__).resolve().parents[2] / "outputs" / "figure_index.csv"


def figure_index() -> pd.DataFrame:
    """One row per figure: label, slug, section, chapter, in_report (and title, file, dir once exported)."""
    if INDEX.exists():
        return pd.read_csv(INDEX)
    rows = [{"label": label(slug), "slug": slug, "section": SECTION[slug], "chapter": FIG_CHAPTER[slug], "in_report": slug in REPORT_ORDER}
            for _, slug, _, _ in FIGURES]
    df = pd.DataFrame(rows)
    order = {s: i for i, s in enumerate(REPORT_ORDER)}
    return df.assign(_k=df.slug.map(lambda s: order.get(s, 100 + [f[1] for f in FIGURES].index(s)))).sort_values("_k").drop(columns="_k")


def report_numbers() -> dict[str, str]:
    """slug -> printed figure number for the figures in the report ('1' ... '16')."""
    idx = figure_index()
    return {r.slug: r.label.split()[1] for r in idx[idx.in_report].itertuples()}
