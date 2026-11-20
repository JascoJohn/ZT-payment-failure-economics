# The Economics of Payment Failure

Financial exposure, foreign-currency translation and realistic recovery in ZT East Africa payment data, January 2022 – April 2024.
Entry to the Zion Tech Hub Finance Data Challenge (November 2026) by **Jasco John, CPA (T), MBA (Finance)**.

**Headline.** Fees on failed transactions total $2.78M (90.1% of recorded fees). $1.07M (38.5%) comes from exceptional account behaviour:
extreme-volume anomalies and one escalation account (47087). The remaining $1.71M is *remaining exposure*, spread across every channel: card
carries 82% of it, USD card alone 61%, mobile money 14%. If USD card failure fell to mobile money's rate in each market, incremental
successful-transaction fees would be about $254K over 28 months. That is a conditional estimate before processing costs, not a forecast.

| | |
| --- | --- |
| Source code | https://github.com/JascoJohn/ZT-payment-failure-economics |
| Live dashboard | *Streamlit link to be added once deployed (see "Deploy the dashboard")* |

---

## If you do not code

Pick whichever of these suits you. None needs Python.

1. **Excel.** Open `outputs/payment_failure_analysis.xlsx` and start at the `00_README` sheet. It rebuilds the study in formulas, one sheet per
   report chapter, with native charts and a `99_Checks` sheet that compares every key figure with the Python results. Blue cells are inputs: change one and the
   workbook recalculates. The file is large (about 2.5 million formulas), so set *Formulas > Calculation Options > Manual*, edit, then press F9.
2. **Read the report.** `outputs/report/The_Economics_of_Payment_Failure.pdf` is the full report. `outputs/report/Executive_Brief.pdf` is the 5-page brief.
   A Word copy for editing is `outputs/report/The_Economics_of_Payment_Failure.docx` (edits made in Word do not flow back into the pipeline; the PDF is the master).
3. **Use the live dashboard** (link above once deployed). Every figure in the report is there, interactive, and recomputes for a period, market, payment type or
   currency you choose. At its default settings every figure matches the report.

---

## If you code

### Setup

Python 3.11 or later. Chrome or Microsoft Edge is needed for static figures and the PDF.

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python scripts\00_readme_and_environment.py     # checks the machine and lists what each script does
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/00_readme_and_environment.py
```

For figures that use exactly the report font, install `report/assets/fonts/SourceSans3[wght].ttf` (and the italic file) on the machine that runs the pipeline;
otherwise they fall back to Segoe UI or Arial. On Windows: right-click the file, choose *Install for me*.

### Run everything

```powershell
python run_pipeline.py                  # stages 00 -> 11, one progress line each, a summary at the end
python run_pipeline.py --from 05        # restart from a stage (uses what earlier stages saved)
python run_pipeline.py --only 03        # one stage
python run_pipeline.py --skip-excel     # skip stage 09 (the workbook)
python run_pipeline.py --recalc-excel   # also recalculate the workbook and read back 99_Checks
```

A full run takes about 15 minutes without `--recalc-excel`, most of it the figures and the workbook.
Stage 01E (data quality) reports on what 01F and 01G produce, so it runs after them; its number does not change.

### One numbering scheme for scripts, Excel sheets, output folders and report chapters

| No. | Script (`scripts/`) | Excel sheet | Report | Reads | Writes (`outputs/`) |
| --- | --- | --- | --- | --- | --- |
| 00 | `00_readme_and_environment.py` | `00_README` | Front matter | the machine, the raw workbook | console |
| 01A | `01A_assumptions.py` | `01A_Assumptions` | 1 / Appendix A | `config/assumptions.yaml` | `01A_assumptions/` (validation, flattened assumptions) |
| 01B | `01B_raw_transactions.py` | `01B_Raw_Transactions` | Appendix A | raw workbook | `01B_raw_transactions/`; caches the sheets in `intermediate/` |
| 01C | `01C_raw_customers.py` | `01C_Raw_Customers` | Appendix A | raw workbook | `01C_raw_customers/` (aliases, stale dates) |
| 01D | `01D_raw_rates.py` | `01D_Raw_Rates` | Appendix A | raw workbook | `01D_raw_rates/` |
| 01E | `01E_data_quality.py` | `01E_Data_Quality` | Appendix A.3–A.4, B | `intermediate/prepared.pkl`, raw workbook | `01E_data_quality/` (flags, SLL evidence, spike days, legacy codes, reconciliation, sensitivity) |
| 01F | `01F_rates.py` | `01F_Rates` | Appendix A.4–A.5, 6 | raw workbook | `01F_rates/` (monthly, month-end and 2022 base rates) |
| 01G | `01G_transactions.py` | `01G_Transactions` | Appendix A.1 | raw workbook, assumptions | `01G_transactions/`; **saves `intermediate/prepared.pkl`**, which stages 01E and 02–08 read |
| 02 | `02_scale.py` | `02_Scale` | 2 | `prepared.pkl` | `02_scale/` tables and figures |
| 03 | `03_concentration.py` | `03_Concentration` | 3 | `prepared.pkl` | `03_concentration/` |
| 04 | `04_diagnostics.py` | `04_Diagnostics`, `04_Laney` | 4 | `prepared.pkl` | `04_diagnostics/` |
| 05 | `05_january.py` | `05_January` | 5 | `prepared.pkl` | `05_january/` |
| 06 | `06_fx.py` | `06_FX` | 6 | `prepared.pkl` | `06_fx/` |
| 07 | `07_recovery.py` | `07_Recovery` | 7 | `prepared.pkl` | `07_recovery/` |
| 08 | `08_recommendations.py` | `08_Recommendations` | 8 | `prepared.pkl` | `08_recommendations/` |
| 09 | `09_excel_workbook.py` | – | – | `intermediate/` | `payment_failure_analysis.xlsx` |
| 10 | `10_report.py` | – | – | `intermediate/`, `report/content/` | `results.json`, `report/` (PDF, HTML, DOCX) |
| 11 | `11_validate.py` | `99_Checks` | Appendix B | everything above, `baseline/` | `audit_report.md` |

Each chapter folder holds `tables/` (CSV) and, for chapters with figures, `figures/` (PNG, SVG for the report, interactive HTML). `outputs/figure_index.csv` is the
one list of figures (number, title, file) that the report, the Excel charts and the checks read.

### Rerun one chapter

```powershell
python scripts\05_january.py        # reproduces exactly what Chapter 5 shows: outputs\05_january\
```

Chapter scripts read the prepared data saved by 01G, so after a change to the raw data or to `config/assumptions.yaml` run `python scripts\01G_transactions.py` first.
`python run_pipeline.py --from 01G` does both.

### Change an assumption

Edit `config/assumptions.yaml` (for example `anomalies.relative.min_failed`), then `python run_pipeline.py --from 01A`. Every table, figure, the report, the workbook and
the audit update. Stage 11 will then report differences from `baseline/` as failures unless they are listed in `baseline/approved_changes.yaml`: that is the point of the baseline. Every difference, approved or not, is listed in `outputs/changes_from_baseline.md`. Refresh it deliberately by copying the new
`outputs/results.json` to `baseline/results_baseline.json` (and the tables and tokens beside it) once you accept the new results.

### The report

`report/content/` holds the text; `report/assets/report.css` holds the style; stage 10 prints both to PDF through Chrome or Edge.

- **Editing wording:** change the files in `report/content/` (`01_summary.md`, `03_main_report.md`, `brief.html`, `00_cover.html`, `02_at_a_glance.html`, `meta.yaml`).
  A number written `{{key}}` comes from the pipeline; `{{fig:slug}}` and `{{tab:slug}}` give the figure or table number; `[[figure slug]]` places a figure.
  Subheadings are numbered automatically (2.1, 2.2 …, A.1 …). Every other typed number must be on `report/content/number_allowlist.yaml`, or stage 11 flags it.
- **Author, contact, footer, links:** `report/content/meta.yaml` (`author`, `credentials`, `email`, `telephone`, `orcid`, `source_code`, `dashboard`).
  The centred two-line footer on every page except the cover is built from it.
- **Layout:** each chapter and appendix starts a page; paragraphs, list items, tables, formula boxes and figures are never split; a table stays with the sentence that
  introduces it and a figure with the sentence that discusses it. The contents, list of figures and list of tables are filled by printing twice: the first pass reads each
  heading's page from the PDF (PyMuPDF), the second prints the numbers, and stage 10 stops if any entry moves between passes.
- **Claude Doc sync:** export the Doc as Markdown, then `python tools/sync_from_doc.py export.md` shows a diff of `report/content/` and lists any number it could not map to a
  token; add `--apply` to write it. Rerun stage 10 afterwards.
- **Word copy:** stage 10 also writes `outputs/report/The_Economics_of_Payment_Failure.docx` from the same content (same headings, a contents field, plain tables,
  equations as Word equations when Office's converter is present and as images otherwise). **Edits made in Word do not flow back into the pipeline.** Right-click the
  contents and choose *Update Field* after you edit.

### The Excel workbook

Built by stage 09 from the raw rows in live formulas, following the report: `01B`–`01D` hold the supplied data unchanged, `01E`–`01G` the data preparation, `02`–`08` one sheet per
chapter with the report's table numbers and captions and native charts (same figure numbers, titles and colours as `figures.py`; where Excel has no equivalent form, such as a
waterfall, a heat map or a bubble chart, the closest form is used and a note sits beside it), and `99_Checks` compares every key figure with Python.
Rebuilt in formulas: the customer Pareto, the exposure bridge, the drivers, the escalation series, the January decomposition and the recovery scenarios. Supplied as values from Python,
each labelled with its script and a check row: size quintiles, sensitivity thresholds, hard/mixed split, persistence, tenure and lapse, the same-customer benchmark and the failure offset,
and the prioritisation matrix.

Recalculating (`--recalc-excel`): with LibreOffice if `soffice` is installed (verified in another environment, 63 of 63 checks; **not tested on this machine**), otherwise with
Microsoft Excel through PowerShell on Windows (`tools/recalc_excel.ps1`), which is what was used here. Either way the result is zero formula errors and every check row OK, or the
stage says what is wrong.

### What `11_validate.py` checks

Every check ends PASS, FAIL or FLAG and is listed in `outputs/audit_report.md`. FAIL stops the run. FLAG is a finding for you to decide; nothing is changed automatically.

- **Integrity:** totals tie, categories are exclusive, no January residual, every `[[figure]]` resolves through `figure_index.csv`.
- **Baseline:** `results.json`, every table and every rendered report value against `baseline/`.
- **Independent recomputation** from `data/raw` in plain pandas, without importing `payfail`: headline, exposure bridge, monthly range, failure by market, January bridge, recovery
  with and without account 47087, customer concentration.
- **Every number in the text** is a `{{token}}` or on the allow-list; **terminology** variants; **denominators**; **units and periods**; **claims against the data**
  (each factual statement about an account, month or market); **cross-output consistency** (PDF, brief, Excel checks, dashboard at default settings, figure titles, footers); **hedging**.

`pytest -q` runs stage 11 as a test (run the pipeline first).

### Put it on GitHub

```powershell
git remote add origin https://github.com/<your-username>/payment-failure-economics.git
git push -u origin main                 # after merging the working branch
```

Create the empty repository on GitHub first (no README, so the first push is clean). The largest file is the Excel workbook, under GitHub's 100 MB limit. Do not push until
you have checked the report and the workbook.

### Deploy the dashboard on Streamlit Community Cloud

1. Sign in at share.streamlit.io with your GitHub account.
2. **Create app**, then **Deploy a public app from GitHub**.
3. Repository, branch `main`, main file path `app/streamlit_app.py`. Streamlit installs `requirements.txt`.
4. The first load takes about 20 seconds while the data is prepared; after that selections are cached.

**Then put the two URLs into `report/content/meta.yaml`** (`source_code` and `dashboard`) and into the table at the top of this file, and rerun stage 10 so the cover and the Word
copy show them.

### What is here

| Path | What it is |
| --- | --- |
| `data/raw/ZT_EA_Regional_Data.xlsx` | The supplied dataset, unchanged |
| `config/assumptions.yaml` | Every threshold and rule |
| `src/payfail/` | The analysis package: `data.py` (prepare), `analysis.py` (every analytical block and its chapter), `figures.py` (every figure), `pipeline.py` and `stages.py` (the stages), `report.py`, `docx_export.py`, `excel*.py`, `validate.py`, `audit.py`, `independent.py` |
| `scripts/` | One thin script per stage |
| `run_pipeline.py` | Runs the stages in order |
| `app/streamlit_app.py` | The dashboard: sixteen report figures and ten dashboard-only ones (D1–D10) |
| `report/` | Content, style and the bundled Source Sans 3 font (SIL Open Font Licence) |
| `baseline/` | The accepted results that stage 11 compares against |
| `tools/` | `sync_from_doc.py`, `recalc_excel.py`, `recalc_excel.ps1` |
| `docs/` | Working notes |
| `tests/` | A thin pytest wrapper around stage 11 |

## Method in brief

The full method is in Appendix A of the report.

- **Two populations.** Count measures use all 62,684 records. USD measures use the 62,463 records with an exchange rate.
- **Translation.** Monthly average of daily rates, an IAS 21-informed approximation; month-end rates only as a sensitivity; constant currency uses each currency's 2022 average rate.
- **Exposure bridge.** Extreme-volume anomalies (at least 1,000 failed attempts, more than 50× the prior 6-month median, under 5% success), then the escalation account
  (absolute trigger: at least 5,000 failed attempts, under 5% success). Remaining exposure is everything else.
- **January 2024.** Extreme-volume anomalies are removed, FX is isolated at constant currency, then LMDI-I splits the rest into volume, mix, failure-rate and fee-yield effects, with no residual.
- **Patterns.** Laney p′ charts with σz = mean moving range / 1.128.
- **Recovery.** Additional successes = attempts × max(failure rate − target, 0), valued at the observed fee per successful payment.

Fees on failed transactions are recorded amounts, not earned revenue: their recognition and collection cannot be established from the data.
