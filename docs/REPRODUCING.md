# Reproducing the analysis

Details behind the short "Reproduce the analysis" section of the [README](../README.md).

## Requirements

- Python 3.11 or later (tested on 3.14 locally and Streamlit Cloud [version shown in the app settings]).
- `pip install -r requirements-dev.txt` (`requirements.txt` is the runtime set used by the dashboard).
- Chrome or Microsoft Edge: Kaleido uses it for the static figures, and stage 10 prints the PDFs through it.
- Optional: Microsoft Excel (Windows) or LibreOffice to recalculate the workbook. Source Sans 3 is bundled in `report/assets/fonts/`; install it to get exactly the report font in the figures, otherwise they fall back to Segoe UI or Arial.

## Run

```
python run_pipeline.py                  # stages 00 to 11, one progress line each, a summary at the end
python run_pipeline.py --from 05        # restart from a stage (uses what earlier stages saved)
python run_pipeline.py --only 03        # one stage
python run_pipeline.py --skip-excel     # skip stage 09 (the workbook)
python run_pipeline.py --recalc-excel   # also recalculate the workbook and read back 99_Checks
python scripts/05_january.py            # one stage on its own: writes outputs/05_january/
```

A full run takes about 15 minutes, most of it the figures and the workbook. Stage 01G saves `outputs/intermediate/prepared.pkl`, which stages 01E and 02–08 read; after changing the raw data or the assumptions, run `--from 01A`. Stage 01E reports on what 01F and 01G produce, so it runs after them.

## Numbering

One scheme runs through the scripts, the Excel sheets, the output folders and the report chapters.

| No. | Script (`scripts/`) | Excel sheet | Report | Writes (`outputs/`) |
| --- | --- | --- | --- | --- |
| 00 | `00_readme_and_environment.py` | `00_README` | front matter | console |
| 01A | `01A_assumptions.py` | `01A_Assumptions` | 1, Appendix A | `01A_assumptions/` |
| 01B | `01B_raw_transactions.py` | `01B_Raw_Transactions` | Appendix A | `01B_raw_transactions/` |
| 01C | `01C_raw_customers.py` | `01C_Raw_Customers` | Appendix A | `01C_raw_customers/` |
| 01D | `01D_raw_rates.py` | `01D_Raw_Rates` | Appendix A | `01D_raw_rates/` |
| 01E | `01E_data_quality.py` | `01E_Data_Quality` | Appendix A.3–A.5, B | `01E_data_quality/` |
| 01F | `01F_rates.py` | `01F_Rates` | Appendix A.4–A.5, 6 | `01F_rates/` |
| 01G | `01G_transactions.py` | `01G_Transactions`, `01G_Anomaly_Rules` | Appendix A.1 | `01G_transactions/`; saves `intermediate/prepared.pkl` |
| 02 | `02_scale.py` | `02_Scale` | 2 | `02_scale/` |
| 03 | `03_concentration.py` | `03_Concentration` | 3 | `03_concentration/` |
| 04 | `04_diagnostics.py` | `04_Diagnostics`, `04_Laney` | 4 | `04_diagnostics/` |
| 05 | `05_january.py` | `05_January` | 5 | `05_january/` |
| 06 | `06_fx.py` | `06_FX` | 6 | `06_fx/` |
| 07 | `07_recovery.py` | `07_Recovery` | 7 | `07_recovery/` |
| 08 | `08_recommendations.py` | `08_Recommendations` | 8 | `08_recommendations/` |
| 09 | `09_excel_workbook.py` | all sheets | | `payment_failure_analysis.xlsx` |
| 10 | `10_report.py` | | | `results.json`, `report/`, `README.md` |
| 11 | `11_validate.py` | `99_Checks` | Appendix B | `audit_report.md`, `changes_from_baseline.md` |

Each chapter folder holds `tables/` (CSV) and, for chapters with figures, `figures/` (PNG, SVG, interactive HTML). `outputs/figure_index.csv` is the one list of figures (number, title, file) that the report, the dashboard, the Excel charts and the checks read.

## Assumptions

Every threshold, alias and rule is in `config/assumptions.yaml` (for example `anomalies.relative.min_failed`, `recovery.bootstrap`). Edit it and run `python run_pipeline.py --from 01A`: every table, figure, the report, the workbook and the audit update.

## Audit

`outputs/audit_report.md` lists every check as PASS, FAIL or FLAG. FAIL stops the run; FLAG is a finding for the author to decide and changes nothing.

- Integrity: totals tie, categories are exclusive, the January decomposition has no residual, every `[[figure]]` resolves through `figure_index.csv`.
- Independent recomputation from `data/raw` in plain pandas (`src/payfail/independent.py`, which imports nothing from the package): headline, exposure bridge, failure by market, January decomposition, recovery with and without account 47087, customer concentration.
- Report text: every number is a `{{token}}` or on `report/content/number_allowlist.yaml`; one term per concept; denominators; units and periods; claims against the data; hedging.
- Outputs: PDFs, brief, workbook (`99_Checks`), dashboard at its default settings, page fill, links, README figures and links.

`pytest -q` runs stage 11 as a test. Run the pipeline first.

## Baseline

`baseline/` holds the accepted results (`results_baseline.json`, tables, report tokens). Stage 11 compares every run against it and fails on any difference that is not listed in `baseline/approved_changes.yaml`; every difference, approved or not, is written to `outputs/changes_from_baseline.md`. After you accept new results, copy the new `outputs/results.json`, tables and tokens into `baseline/` and clear the approved list.

## Report tokens

The text in `report/content/` (`01_summary.md`, `03_main_report.md`, `brief.html`, `00_cover.html`, `02_at_a_glance.html`, `readme.md`, `meta.yaml`) carries numbers as `{{key}}`, so they come from the pipeline. `{{fig:slug}}` and `{{tab:slug}}` give a figure or table number, `[[figure slug]]` places a figure, and subheadings are numbered automatically. A number typed in the text must be on `number_allowlist.yaml`, or stage 11 flags it. Author, contact, links and version are in `meta.yaml`.

To bring edits made in a shared document back, export it as Markdown and run `python tools/sync_from_doc.py export.md`. It shows a diff of `report/content/`, maps rendered numbers back to tokens and lists any it could not map; add `--apply` to write the changes.

## Layout and Word export

Stage 10 prints the report twice or more through Chrome: the first pass reads each heading's page from the PDF so that the contents and the lists of figures and tables carry page numbers; later passes apply the page flow rules in `src/payfail/flow.py` (figures follow the paragraph that first refers to them; a figure that leaves a page under 70% full is scaled down, then the paragraphs after it move up). Every chapter starts a page and no paragraph splits across pages. Stage 11 reports how full each page is in `outputs/report/page_fill.md`.

The Word copy (`outputs/report/The_Economics_of_Payment_Failure.docx`) is built from the same content in the same order, with a cover, the infographic and cream pages. Edits made in Word do not flow back into the pipeline. Update the contents field in Word after editing.

## Excel recalculation

The workbook is built with live formulas (about 2.5 million) and `99_Checks` compares every key figure with the Python results. `--recalc-excel` recalculates it with LibreOffice if `soffice` is installed, otherwise with Microsoft Excel through `tools/recalc_excel.ps1`, and reads back `99_Checks`. Set Formulas > Calculation Options > Manual while editing the file, then press F9.
