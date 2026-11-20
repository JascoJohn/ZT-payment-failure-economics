# {{meta_title}}

**Jasco John, CPA (T)** · {{meta_prepared_for}}, {{meta_date}} · Version {{version}}

{{meta_subtitle}}.

## Start here

| | Who it is for |
| --- | --- |
| **[Full report (PDF)]({{rel_report}})** | Readers who want the whole analysis: findings, method and limitations ({{rep_pages}} pages). |
| **[Executive brief (PDF)]({{rel_brief}})** | Decision-makers: the answer and three actions in {{brief_pages}} pages. |
| **[Live dashboard]({{dashboard}})** | Anyone who wants to explore: every report figure, recomputed for the period, market, payment type and currency you choose. |
| **[Excel workbook]({{rel_xlsx}})** | Finance analysts who want to trace the numbers in formulas. About {{wb_mb}} MB: GitHub downloads it rather than previewing it. |

## The question

Where does payment failure cost ZT East Africa money, how much of it could realistically be recovered, and what should management do first? The study uses {{records}} monthly merchant records ({{attempts}} payment attempts) from Kenya, Uganda, Tanzania, Ghana and Zambia, with daily exchange rates and a customer table. It separates exceptional account behaviour from persistent failure, translates every currency with care, and values recovery against an observed benchmark.

## Key findings

1. **Fees on failed transactions total {{failed_fees_m}}, {{fee_share}} of recorded fees, and {{count_rate}} of attempts fail by count.** That headline mixes two problems with different remedies. [Report, Section 2 (p. {{pg2}})]({{rel_report}}#page={{pg2}}) · [Dashboard, 2. Scale tab]({{dashboard}})
2. **The two anomaly categories account for {{anom_m}} ({{anom_share}}).** {{an_obs_words}} extreme-volume observations, including one from account 47087, and that account's continuing escalation, carry it; this is a monitoring problem. [Report, Section 4 (p. {{pg4}})]({{rel_report}}#page={{pg4}}) · [Dashboard, 4. Diagnostics tab]({{dashboard}})
3. **Remaining exposure is {{rm_m}} ({{rm_share}}), and it is steady.** Monthly count failure stays between {{rem_range_words}}; card carries {{rm_card_share}} of remaining exposure and USD card alone {{rm_usdcard_share}}. [Report, Section 2 (p. {{pg2}})]({{rel_report}}#page={{pg2}}) · [Dashboard, 3. Concentration tab]({{dashboard}})
4. **USD card completion is the main improvement opportunity.** Excluding extreme-volume anomalies, USD card fails {{usd_card_range}} by count across the markets against {{mm_mk_range}} for mobile money; even among the {{gap_n}} customers who use both, card fails about {{gap_gs0}} percentage points more often. [Report, Section 7 (p. {{pg7}})]({{rel_report}}#page={{pg7}}) · [Dashboard, 7. Recovery tab]({{dashboard}})
5. **January 2024 was a few accounts, not a breakdown.** Extreme-volume anomalies explain {{jan_ex_share}} of the month's rise in fees on failed transactions; exchange-rate translation moved it by only {{rd_jan_fx}}. [Report, Section 5 (p. {{pg5}})]({{rel_report}}#page={{pg5}}) · [Dashboard, 5. January 2024 tab]({{dashboard}})
6. **Exchange rates distort the reported trend.** Depreciation cut local-currency fees on failed transactions by {{rd_fx_local}} ({{rd_fx_pct}}) against 2022 rates, and the Ghanaian cedi drives {{fx_ghs_share}} of that effect. [Report, Section 6 (p. {{pg6}})]({{rel_report}}#page={{pg6}}) · [Dashboard, 6. Foreign exchange tab]({{dashboard}})

## What recovery is worth

If USD card failed no more often than mobile money in each market, the platform would have earned about **{{rc_base_k0}}** more in successful-transaction fees over {{nm}} months, roughly {{rc_base_ann0}} a year. The conservative and optimistic targets give {{rc_con_k0}} and {{rc_opt_k0}}. Across benchmark and exclusion choices the base case ranges from {{rc_rng_lo}} to {{rc_rng_hi}}, and resampling customers ({{rc_ci_reps}} replicates, fixed seed) gives a {{rc_ci_level}} interval of {{rc_ci_lo}}–{{rc_ci_hi}}. Kenya, Tanzania and Uganda hold {{rc_pri_k0}} of the base case.

It is a conditional estimate, not a forecast:

- it is before processing costs: the break-even is {{rc_be}} of cost per additional successful payment;
- it assumes the gap is actually closed;
- fees on failed transactions are recorded amounts, not cash or earned revenue;
- some failures may be correct rejections: leaving out USD card customer-months with no card success gives {{rc_nr_k0}};
- the mobile money benchmark is moved by the escalation account (47087): without it the base case is {{bx_inc0}}.

[Report, Section 7 (p. {{pg7}})]({{rel_report}}#page={{pg7}})

## Recommendations

- **Contain the two anomaly categories:** two account alerts, one for sudden spikes and one for steady escalation, so that flagged accounts are throttled and reviewed in the same month.
- **Improve USD card completion in Kenya, Tanzania and Uganda,** starting with the merchant-months that had no successful card payment.
- **Report three numbers every month:** the count failure rate, the failed-fee share, and successful-transaction fees at constant 2022 exchange rates.
- **Run a 90-day pilot:** each market's target is its own best three-month USD card failure rate (Kenya {{pl_Kenya_to}} from {{pl_Kenya_from}}, Tanzania {{pl_Tanzania_to}} from {{pl_Tanzania_from}}, Uganda {{pl_Uganda_to}} from {{pl_Uganda_from}}), with {{rc_be}} per additional successful payment as the cost ceiling. [Report, Section 8 (p. {{pgPilot}})]({{rel_report}}#page={{pgPilot}})

## Key visuals

![{{vis1_title}}]({{vis1_path}})

*{{vis1_title}}. Source: ZT East Africa supplied dataset; author's calculations.*

![{{vis2_title}}]({{vis2_path}})

*{{vis2_title}}. Source: ZT East Africa supplied dataset; author's calculations.*

![{{vis3_title}}]({{vis3_path}})

*{{vis3_title}}. Source: ZT East Africa supplied dataset; author's calculations.*

![{{vis4_title}}]({{vis4_path}})

*{{vis4_title}}. Source: ZT East Africa supplied dataset; author's calculations.*

## Data and method in brief

- **Data.** The supplied ZT East Africa workbook: {{records}} monthly merchant records ({{attempts}} attempts), a customer table and daily exchange rates, January 2022 – April 2024 ([`data/raw/`](data/raw)).
- **Two populations.** Counts use every record; dollar measures use the {{records_tr}} records that have an exchange rate.
- **Translation.** The monthly average of daily rates (an IAS 21-informed approximation), month-end rates as a sensitivity, and each currency's 2022 average rate for constant currency. The Sierra Leone redenomination is corrected.
- **Exposure and recovery.** Every fee on a failed transaction falls into one of three exclusive categories: extreme-volume anomalies, the escalation account (47087) and remaining exposure. Recovery values the USD card gap to mobile money in each market; January 2024 is decomposed with LMDI-I; patterns use Laney control charts.
- **Full method:** [Report, Appendix A (p. {{pgA}})]({{rel_report}}#page={{pgA}}).

## Reproducibility

### Reproduce the analysis

Requirements: Python 3.11+ (tested on 3.14, locally and on Streamlit Cloud), plus Chrome or Edge for the static figures and the PDF.

```
git clone https://github.com/JascoJohn/ZT-payment-failure-economics.git
cd ZT-payment-failure-economics
pip install -r requirements-dev.txt
python run_pipeline.py
```

`--from <stage>`, `--only <stage>`, `--skip-excel` and `--recalc-excel` choose what runs; a full run takes about 15 minutes.

Outputs: the report, brief and Word copy are in [`outputs/report/`](outputs/report), the workbook is [`outputs/payment_failure_analysis.xlsx`](outputs/payment_failure_analysis.xlsx), tables and figures are in one folder per chapter under [`outputs/`](outputs), and the audit is [`outputs/audit_report.md`](outputs/audit_report.md).

Changing an assumption: edit [`config/assumptions.yaml`](config/assumptions.yaml) and rerun with `--from 01A`; stage 11 lists every changed value against [`baseline/`](baseline).

Dashboard: `streamlit run app/streamlit_app.py`.

Checks: {{n_checks}} automated checks, including an independent recomputation in plain pandas; `pytest -q` runs them.

| No. | Script | Report chapter | Excel sheet |
| --- | --- | --- | --- |
| 00 | `00_readme_and_environment.py` | front matter | `00_README` |
| 01A–01G | `01A_assumptions.py` … `01G_transactions.py` (01E runs after 01G) | Appendix A | `01A_…` … `01G_…` |
| 02 | `02_scale.py` | 2 Scale | `02_Scale` |
| 03 | `03_concentration.py` | 3 Where failure concentrates | `03_Concentration` |
| 04 | `04_diagnostics.py` | 4 Failure diagnostics | `04_Diagnostics`, `04_Laney` |
| 05 | `05_january.py` | 5 January 2024 investigation | `05_January` |
| 06 | `06_fx.py` | 6 Foreign exchange analysis | `06_FX` |
| 07 | `07_recovery.py` | 7 Recovery opportunity | `07_Recovery` |
| 08 | `08_recommendations.py` | 8 Management recommendations | `08_Recommendations` |
| 09 | `09_excel_workbook.py` | | |
| 10 | `10_report.py` | | |
| 11 | `11_validate.py` | Appendix B | `99_Checks` |

Details (the report token system, Word export, Excel recalculation and the baseline workflow) are in [`docs/REPRODUCING.md`](docs/REPRODUCING.md).

## Repository contents

- [`app/`](app): the Streamlit dashboard.
- [`baseline/`](baseline): the accepted results that stage 11 compares against.
- [`config/`](config): `assumptions.yaml`, every threshold and rule.
- [`data/raw/`](data/raw): the supplied dataset, unchanged.
- [`docs/`](docs): reproduction details.
- [`outputs/`](outputs): everything the pipeline writes (report, workbook, tables, figures, audit).
- [`report/`](report): the text, style and fonts of the report.
- [`scripts/`](scripts): one script per stage.
- [`src/payfail/`](src/payfail): the analysis package.
- [`tests/`](tests): a pytest wrapper around stage 11.
- [`tools/`](tools): helper scripts.

## How to cite

Jasco John ({{meta_year}}). *{{meta_title}}: {{meta_subtitle}}* (Version {{version}}). {{meta_prepared_for}} entry. {{source_code}}

## Licence

The code is released under the MIT licence ([`LICENSE`](LICENSE)). The dataset belongs to Zion Tech Hub and is included only to reproduce this entry.

## Contact

Jasco John, CPA (T) · [{{meta_email}}](mailto:{{meta_email}}) · ORCID [{{meta_orcid}}](https://orcid.org/{{meta_orcid}})
