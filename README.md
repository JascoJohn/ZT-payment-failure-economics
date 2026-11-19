# The Economics of Payment Failure

Financial exposure, foreign-currency translation and realistic recovery in ZT East Africa payment data, January 2022 – April 2024.
Entry to the Zion Tech Hub Finance Data Challenge (November 2026) by Jasco Francis John, CPA(T).

**Headline.** Fees on failed transactions total $2.78M (90.1% of recorded fees). $1.07M (38.5%) comes from exceptional account behaviour, either extreme-volume anomalies or one escalating account. The remaining $1.71M is a persistent card-completion problem. If USD card failure fell to mobile money's rate in each market, incremental successful-transaction fees would be about $254K over 28 months. That is a conditional estimate before processing costs, not a forecast.

Everything in this repository is generated from the raw workbook by code. Anyone can rerun it, change an assumption and see what moves.

## What is here

| Path | What it is |
| --- | --- |
| `data/raw/ZT_EA_Regional_Data.xlsx` | The supplied dataset, unchanged: transactions, customer details, daily exchange rates |
| `config/assumptions.yaml` | Every threshold and rule: FX corrections, data flags, anomaly rules, pattern flags, January window, recovery scenarios |
| `src/payfail/` | The analysis package: `data.py` (load, translate, flag, classify), `analysis.py` (every analytical block), `figures.py` (all figures), `report.py` (renders the report and brief), `excel.py` (the Excel workbook) |
| `run_all.py` | Rebuilds every output from the raw data |
| `app/streamlit_app.py` | Interactive dashboard: the report figures plus ten dashboard-only ones, recomputed for any selection |
| `report/content/` | Report text you can edit: cover details (`meta.yaml`), written summary, one-page infographic, main report, executive brief |
| `report/assets/` | Report stylesheet and the bundled Source Sans 3 font (SIL Open Font Licence) |
| `outputs/report/` | The full report and the 5-page executive brief, as PDF and HTML |
| `outputs/figures/` | Every figure as PNG and interactive HTML, plus SVG for the report; `index.csv` lists them |
| `outputs/tables/` | Every result table as CSV |
| `outputs/results.json` | Every headline number |
| `outputs/payment_failure_analysis.xlsx` | Excel version of the analysis in live formulas, with a Checks sheet against Python |
| `tests/` | Integrity tests: totals tie, categories exclusive, no decomposition residual, template renders |

## Rerun it

Python 3.11 or later.

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python run_all.py                    # about a minute plus the Excel build
pytest -q
streamlit run app/streamlit_app.py
```

To test a different assumption, edit `config/assumptions.yaml` (for example `anomalies.relative.min_failed`) and run `python run_all.py` again. The report, figures, tables and workbook all update.

Static figure export (`kaleido`) needs Chrome or Chromium on the machine. The PDF report and the optional `--recalc-excel` step need LibreOffice. Without them, everything else still runs.

## One set of figures, two views

`src/payfail/figures.py` builds every figure once. Sixteen appear in the report, numbered 1–16 in reading order (`REPORT_ORDER`); ten more appear only in the dashboard, numbered D1–D10, because the report gives those numbers in a table. `run_all.py` saves them as static images for the report; the dashboard draws the same figures interactively from the same functions. In the dashboard you can filter by period, market, payment type and currency, exclude anomalies, and change the anomaly thresholds and the optimistic recovery margin. With the default selection, every dashboard figure matches the report.

## The report

The report (cover, written executive summary, one-page infographic, main report, appendices) and a 5-page executive brief are rendered from `report/content/` with `report/assets/report.css`, then printed to PDF with Chrome or Microsoft Edge.

- **Editing text** means editing the files in `report/content/`. Numbers written as `{{key}}` come from the pipeline; everything else is plain text. Changing words, order or emphasis never affects the analysis.
- **Editing the look** (colours, fonts, spacing) means editing `report/assets/report.css`; the figure colours are set to match in `figures.py`.
- **Formulas** are written in LaTeX between `$$ … $$` and rendered as real mathematics.
- Rerunning the report stage overwrites `outputs/report/`. Keep any hand-edited PDF elsewhere.
- For figures to use exactly the report font, install `report/assets/fonts/SourceSans3[wght].ttf` on the machine that runs the pipeline; otherwise they fall back to Segoe UI or Arial.

## The Excel workbook

`outputs/payment_failure_analysis.xlsx` rebuilds the analysis from the raw rows in formulas (about 2.2 million). It covers:

- **Rates:** the SLL redenomination fix, the 5× spike screen and duplicate-day weighting. From those it builds the monthly average, month-end and 2022 constant-currency rates.
- **Transactions:** USD translation of all 62,684 records and the three data flags.
- **Anomaly rules:** prior 6-month medians, the extreme-volume rule and the escalation trigger.
- **Summaries:** the exposure bridge, monthly series, payment types and markets.
- **January:** the full LMDI-I decomposition.
- **Laney:** p′ charts and pattern flags for the 10 eligible cells.
- **Recovery:** scenarios with editable targets and cost ratios.
- **FX:** the FX tables and the 10% screen.

The `Checks` sheet compares about 60 figures with the Python results; all read OK.

Blue cells on `Assumptions` are inputs. Excel recalculates on opening. The workbook is large, so set calculation to manual while editing, then press F9. One input is supplied as values rather than formulas, for speed: the customer × payment type × month attempt grid, which is a pivot of `Transactions`. Each of its rows reconciles back to `Transactions`. The Pareto curve, quintiles, persistence, hard/mixed split, same-customer benchmark and prioritisation matrix are Python-only; their tables are in `outputs/tables/`.

## Put it on GitHub

```bash
cd payment-failure-economics
git init
git add .
git commit -m "Payment failure economics: data, code, report, dashboard, Excel"
git branch -M main
git remote add origin https://github.com/<your-username>/payment-failure-economics.git
git push -u origin main
```

Create the empty repository on GitHub first (no README, so the first push is clean). The largest file is the Excel workbook at about 30 MB, under GitHub's 100 MB limit.

## Deploy the dashboard on Streamlit Community Cloud

1. Sign in at share.streamlit.io with your GitHub account.
2. Click **Create app**, then **Deploy a public app from GitHub**.
3. Choose the repository, branch `main`, main file path `app/streamlit_app.py`.
4. Deploy. Streamlit installs `requirements.txt`. The first load takes about 20 seconds while the data is prepared; after that, selections are cached.

Then add the app's URL to the top of this README and to the report.

## Method in brief

The full method is in Appendix A of the report. In brief:

- **Two populations.** Count measures use all 62,684 records. USD measures use the 62,463 records with an exchange rate.
- **Translation.** Monthly average of daily rates, an IAS 21-informed approximation. Month-end rates are used only as a sensitivity. Constant currency uses each currency's 2022 average rate.
- **Exposure bridge.** Relative extreme-volume rule (at least 1,000 failed attempts, more than 50× the prior 6-month median, under 5% success). Then an absolute escalation trigger (at least 5,000 failed attempts, under 5% success). Remaining exposure is everything else.
- **January 2024.** Anomalies are removed, FX is isolated at constant currency, then LMDI-I splits the rest into volume, mix, failure-rate and fee-yield effects with no residual.
- **Patterns.** Laney p′ charts with σz = mean moving range / 1.128.
- **Recovery.** Additional successes = attempts × max(failure rate − target, 0), valued at fee per successful payment.

Fees on failed transactions are not treated as earned revenue: their recognition and collection cannot be established from the data.
