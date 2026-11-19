# Audit report

98 checks: **84 pass**, **0 fail**, **14 flagged for the author**. A FLAG is a finding that needs a decision; nothing was changed because of it.

## Flagged for you

- **[2. Every number in the text] No typed number outside the allow-list (computed numbers must be {{tokens}}).** 88 typed numbers not on the allow-list {'03_main_report.md': 76, '02_at_a_glance.html': 6, 'brief.html': 3, '01_summary.md': 2, '00_cover.html': 1}. Full list: outputs/audit_typed_numbers.csv. First: 03_main_report.md:17 Six in ten; 03_main_report.md:17 nine in ten; 03_main_report.md:34 20; 03_main_report.md:46 89%; 03_main_report.md:46 79%; 03_main_report.md:79 10; 03_main_report.md:79 1%; 03_main_report.md:79 10
- **[3. Terminology] One term for: Extreme-volume anomalies.** 56 variant uses. 03_main_report.md: 'values ( +  +  = ). The anomaly categories are prox' | 03_main_report.md: 'ies]* ### The trend once anomalies are removed  compar' | 03_main_report.md: 'the period belong to the anomaly categories. Without' | 03_main_report.md: 'n causes. It defines the anomaly categories used in'
- **[3. Terminology] One term for: The escalation account (47087).** 7 variant uses. 01_summary.md: '-months and one steadily escalating account (47087) drove most' | brief.html: 'customer-months and one escalating account carry .         The' | figures.py (titles, legends): 'flagged observations and escalation account(s) Extreme failed-atte' | figures.py (titles, legends): 'Extreme-volume anomalies Escalation account(s) Remaining exposure'
- **[3. Terminology] One term for: Remaining exposure.** 2 variant uses. 03_main_report.md: 'o about 79% in 2024. The remaining problem is chronic, but it' | README.md: 'he remaining $1.71M is a persistent card-completion problem. If USD card failur'
- **[3. Terminology] One term for: Fees on failed transactions.** 4 variant uses. 02_at_a_glance.html: '47087 account for  () of failed-transaction fees.           of Janua' | figure titles: '96% of January's rise in failed-transaction fees Figure 11. Outside' | figures.py (titles, legends): 'treme-volume anomaly All failed-transaction fees Extreme-volume anom' | figures.py (titles, legends): '0%} of January's rise in failed-transaction fees Baseline = Jul–Dec'
- **[3. Terminology] One term for: Successful-transaction fees.** 7 variant uses. 03_main_report.md: 'ot better completion. On successful fees, depreciation erase' | 03_main_report.md: 'e measures monthly, with successful fees at constant currenc' | 01_summary.md: 've earned about  more in fees on successful payments over the 28 months,' | 01_summary.md: 'he failed-fee share, and fees on successful payments at constant 2022 ex'
- **[4. Denominators] Every sentence with a percentage states or implies its population.** 87 sentences with a percentage; 19 without any population cue (list in outputs/audit_percentages.csv): It covers every channel, but card carries 82% of it ($1.40M) and USD card alone 61% ($1.04M). | USD card payments fail 78–96% of the time across the five markets, while mobile money fails 43–69% of the time in the same markets. | Bank transfer works well, failing only 5.7% of the time, but it is too small to make a difference.
- **[4. Denominators] No comparison sets two different populations without saying so.** 2 to read: Base case under alternative benchmarks Benchmark Treatment Base-case incremental fees, 28 months Base Mobile money failure rate in each market, as observed $253 | Monitoring triggers Indicator Definition Trigger Account anomaly alert, relative Failed attempts ≥ 1,000, more than 50× the 6-month median, success under 5% Sam
- **[5. Units and periods] No sentence compares an annual figure with a 28-month figure.** 1 to read: What recovery is worth If USD card failed no more often than mobile money in each market, the platform would have earned $254K more in fees on successful payments over 28
- **[6. Claims against the data] The 89% and 79% are said to be monthly averages (they are not the pooled yearly shares).** The text gives 'about 89% in 2022 to about 79% in 2024' without saying they are averages of the monthly shares. The pooled shares are 90.2% (2022) and 78.9% (2024); only the monthly averages round to 89% and 79%
- **[6. Claims against the data] Typed 'before the SLL correction' figures ($3,148,908; $2,842,692; $744,744) match the computed fix-off run.** fix-off run gives $3,148,996, $2,842,781, $744,744. The typed figures also had the rate-spike screen switched off; the difference is $89 on failed fees
- **[6. Claims against the data] Typed '$63.3K' removed by the SLL correction matches the computed difference.** computed $63,356
- **[6. Claims against the data] Customer 1039721: 'recurring UGX 500 million records ... 3,000-4,300 attempts at a consistent 3.0% fee'.** 21 recurring failed UGX mobile money records (Aug 2022 - Apr 2024): value UGX 262-520 million, attempts 2,649-4,310, fee ratio 3.00%. The fee ratio is right; '500 million' and '3,000-4,300' are looser than the data
- **[8. Hedging] No causal or overconfident wording the data cannot support.** 2 unhedged sentences to read: The: Exposure bridge – $2.78M $1.07M | 38.5% $1.71M | 61.5% Anomalous-account exposure CONTAIN Remaining failed-fee exposure IMPROVE Mutually exclusive cat | Exe: What the data shows A few accounts drive the spikes.

## A. Integrity

| Result | Check | Detail |
| --- | --- | --- |
| PASS | Records and attempts tie to the raw workbook | 62,684 records, 1,645,892 attempts, 1,019,793 failed |
| PASS | Translatable + untranslatable records = all records |  |
| PASS | Fees = failed + successful |  |
| PASS | Exposure bridge is exclusive and exhaustive |  |
| PASS | Escalation account is 47087 only | [47087] |
| PASS | January decomposition has no residual | residual 2.55e-11 |
| PASS | Constant-currency and reported fees use the same population |  |
| PASS | SLL redenomination applied (every month on old-leone scale) |  |
| PASS | Recovery scenarios ordered conservative < base < optimistic |  |
| PASS | Fee revenue remaining at 0% cost equals the base case |  |
| PASS | Laney: 10 eligible cells, 210 tests, σz above 1 everywhere |  |
| PASS | Customer concentration: 5,108 ranked; top 1% is 51 customers | 5,108 customers, top 1% = 51 customers holding 70.4%, top 10 50.4% |
| PASS | Every [[figure]] in the content resolves through outputs/figure_index.csv to an exported file | 16 distinct figures referenced; unresolved []; files missing [] |
| PASS | Report figures appear in REPORT_ORDER order, numbered 1-16 |  |
| PASS | Ten dashboard-only figures, labelled D1-D10 |  |

## B. Baseline

| Result | Check | Detail |
| --- | --- | --- |
| PASS | results.json matches the baseline (ints exact, floats to 1e-9) | 12 blocks identical |
| PASS | Every baseline table (CSV) matches | 38 tables identical |
| PASS | Every rendered report value matches the baseline (exact text) | 569 values identical; 13 new |

## 1. Independent recomputation (plain pandas from data/raw)

| Result | Check | Detail |
| --- | --- | --- |
| PASS | Headline records | independent 62,684 vs pipeline 62,684 |
| PASS | Headline attempts | independent 1,645,892 vs pipeline 1,645,892 |
| PASS | Headline failed | independent 1,019,793 vs pipeline 1,019,793 |
| PASS | Headline records_translatable | independent 62,463 vs pipeline 62,463 |
| PASS | Headline fees | independent 3,085,639.706382 vs pipeline 3,085,639.706382 |
| PASS | Headline failed_fees | independent 2,779,424.130335 vs pipeline 2,779,424.130335 |
| PASS | Headline succ_fees | independent 306,215.576048 vs pipeline 306,215.576048 |
| PASS | Headline fee_share | independent 0.900761 vs pipeline 0.900761 |
| PASS | Headline count_rate | independent 0.619599 vs pipeline 0.619599 |
| PASS | Exposure bridge: Extreme-volume anomaly | independent $825,960.17 vs pipeline $825,960.17 |
| PASS | Exposure bridge: Escalation | independent $244,996.24 vs pipeline $244,996.24 |
| PASS | Exposure bridge: Remaining | independent $1,708,467.72 vs pipeline $1,708,467.72 |
| PASS | Extreme-volume observations and escalation account | 20 observations; escalation [47087] |
| PASS | Monthly remaining-exposure failure range is 48-61% | independent 0.4845-0.6136; pipeline 0.4845-0.6136 |
| PASS | Card and mobile money failure rate by market | 10 market-channel cells compared |
| PASS | January bridge (baseline, anomalies, FX, four LMDI effects, entry/exit) | 9 components agree; independent residual 2.91e-11 |
| PASS | Base-case recovery | independent $253,694.02 vs pipeline $253,694.02 |
| PASS | Benchmark sensitivity without account 47087 ($324.1K; Kenya mobile money 56.3% vs 68.6%) | independent $324,134.13; Kenya 56.3% vs 68.6% |
| PASS | Customer concentration (5,108 with failed fees of 5,657; top 10 50.4%; top 1% = 51 customers, 70.4%) | 5,108 of 5,657; top 10 50.4%; top 1% = 51 customers, 70.4% |
| PASS | Thresholds used by the independent check equal config/assumptions.yaml |  |

## 2. Every number in the text

| Result | Check | Detail |
| --- | --- | --- |
| PASS | Allow-listed thresholds equal config/assumptions.yaml | 23 thresholds checked |
| FLAG | No typed number outside the allow-list (computed numbers must be {{tokens}}) | 88 typed numbers not on the allow-list {'03_main_report.md': 76, '02_at_a_glance.html': 6, 'brief.html': 3, '01_summary.md': 2, '00_cover.html': 1}. Full list: outputs/audit_typed_numbers.csv. First: 03_main_report.md:17 Six in ten; 03_main_report.md:17 nine in ten; 03_main_report.md:34 20; 03_main_report.md:46 89%; 03_main_report.md:46 79%; 03_main_report.md:79 10; 03_main_report.md:79 1%; 03_main_report.md:79 10 |
| PASS | Every {{token}} in the content resolves to a value |  |
| PASS | Key tokens agree with results.json (formatted independently) | 13 tokens agree |

## 3. Terminology

| Result | Check | Detail |
| --- | --- | --- |
| FLAG | One term for: Extreme-volume anomalies | 56 variant uses. 03_main_report.md: 'values ( +  +  = ). The anomaly categories are prox' / 03_main_report.md: 'ies]* ### The trend once anomalies are removed  compar' / 03_main_report.md: 'the period belong to the anomaly categories. Without' / 03_main_report.md: 'n causes. It defines the anomaly categories used in' |
| FLAG | One term for: The escalation account (47087) | 7 variant uses. 01_summary.md: '-months and one steadily escalating account (47087) drove most' / brief.html: 'customer-months and one escalating account carry .         The' / figures.py (titles, legends): 'flagged observations and escalation account(s) Extreme failed-atte' / figures.py (titles, legends): 'Extreme-volume anomalies Escalation account(s) Remaining exposure' |
| FLAG | One term for: Remaining exposure | 2 variant uses. 03_main_report.md: 'o about 79% in 2024. The remaining problem is chronic, but it' / README.md: 'he remaining $1.71M is a persistent card-completion problem. If USD card failur' |
| FLAG | One term for: Fees on failed transactions | 4 variant uses. 02_at_a_glance.html: '47087 account for  () of failed-transaction fees.           of Janua' / figure titles: '96% of January's rise in failed-transaction fees Figure 11. Outside' / figures.py (titles, legends): 'treme-volume anomaly All failed-transaction fees Extreme-volume anom' / figures.py (titles, legends): '0%} of January's rise in failed-transaction fees Baseline = Jul–Dec' |
| FLAG | One term for: Successful-transaction fees | 7 variant uses. 03_main_report.md: 'ot better completion. On successful fees, depreciation erase' / 03_main_report.md: 'e measures monthly, with successful fees at constant currenc' / 01_summary.md: 've earned about  more in fees on successful payments over the 28 months,' / 01_summary.md: 'he failed-fee share, and fees on successful payments at constant 2022 ex' |

## 4. Denominators

| Result | Check | Detail |
| --- | --- | --- |
| FLAG | Every sentence with a percentage states or implies its population | 87 sentences with a percentage; 19 without any population cue (list in outputs/audit_percentages.csv): It covers every channel, but card carries 82% of it ($1.40M) and USD card alone 61% ($1.04M). / USD card payments fail 78–96% of the time across the five markets, while mobile money fails 43–69% of the time in the same markets. / Bank transfer works well, failing only 5.7% of the time, but it is too small to make a difference. |
| FLAG | No comparison sets two different populations without saying so | 2 to read: Base case under alternative benchmarks Benchmark Treatment Base-case incremental fees, 28 months Base Mobile money failure rate in each market, as observed $253 / Monitoring triggers Indicator Definition Trigger Account anomaly alert, relative Failed attempts ≥ 1,000, more than 50× the 6-month median, success under 5% Sam |

## 5. Units and periods

| Result | Check | Detail |
| --- | --- | --- |
| FLAG | No sentence compares an annual figure with a 28-month figure | 1 to read: What recovery is worth If USD card failed no more often than mobile money in each market, the platform would have earned $254K more in fees on successful payments over 28 |
| PASS | Figure 14 reference line is the annual equivalent of successful-transaction fees (not the 28-month total) |  |
| PASS | Annual run-rate = 28-month total x 12/28 | 28 months |

## 6. Claims against the data

| Result | Check | Detail |
| --- | --- | --- |
| PASS | Account 49957 recorded no activity after January 2024 | last month Jan 2024 |
| PASS | Account 47087: 199 failed attempts in October 2023 | 199 |
| PASS | Account 47087: no more than 90 successes in any month | maximum 90 |
| PASS | Only account 47087's January 2024 observation crossed the relative rule | 1 observation(s) |
| PASS | Account 47087 is a Kenyan merchant taking GHS mobile money | country {'Kenya'}; GHS share of mobile money attempts 99% |
| PASS | Account 47087: more than 100,000 non-anomalous mobile money attempts and a few dozen USD card attempts | 106,761 mobile money attempts; 49 USD card attempts |
| PASS | Four largest extreme-volume account-months are all card, had no successes, and carry most of the anomaly exposure | 93% of 20 observations' fees |
| PASS | Extreme-volume observations in Feb and Apr 2024 and in six months between Jan 2022 and Jul 2023 | early months ['2022-01', '2022-07', '2022-08', '2023-04', '2023-05', '2023-07']; later ['2024-01', '2024-02', '2024-04'] |
| PASS | Account 51026 fell back to a handful of attempts after January | max monthly attempts after January: 15 |
| PASS | Account 49477 fell back to a handful of attempts after January | max monthly attempts after January: 1 |
| PASS | Account 49957 produced an extreme-volume observation in December 2023 |  |
| PASS | Laney signal Kenya mobilemoney 2024-04: largest customer's share about 90% | 90.3% |
| PASS | Laney signal Ghana card 2023-05: largest customer's share about 87% | 87.2% |
| PASS | Pattern flags typed in the Laney table equal the computed flags | 10 cells agree |
| PASS | Zambia card has fewer than 12 eligible months (limitations) | 9 eligible months |
| PASS | Failure is U-shaped across tenure | rates 61.6%, 53.7%, 52.8%, 62.7% |
| PASS | Failed-fee share across tenure bands is flat at 85-88% | 85.1%-87.5% |
| PASS | January: failure-rate effect is favourable (negative) and Uganda card improved | effect $-2,207 |
| PASS | January: Uganda card failure rate fell and Tanzania card fee per failed attempt rose |  |
| PASS | January: the fee-yield rise is almost all Tanzania card | Tanzania card = 120% of the fee-yield effect |
| PASS | January: the translation effect is small relative to the rise | $420 against a $664,073 rise |
| PASS | Both measures shrink by about 6% in dollar terms at constant currency | 6.1%, 5.9% |
| PASS | Failed-fee share of remaining exposure drifts from about 89% (2022) to about 79% (2024), as the average of the monthly shares in Figure 2 | monthly averages 89.2% and 78.8% |
| FLAG | The 89% and 79% are said to be monthly averages (they are not the pooled yearly shares) | The text gives 'about 89% in 2022 to about 79% in 2024' without saying they are averages of the monthly shares. The pooled shares are 90.2% (2022) and 78.9% (2024); only the monthly averages round to 89% and 79% |
| PASS | Tanzania ranks second in the base case despite fewer attempts than Uganda |  |
| PASS | Bank transfer is the one reliable channel | 5.7% |
| PASS | Card is structural: card cells' typical month fails at 84-93% | see Laney medians: Kenya 93%, Uganda 84%, Tanzania 87%, Ghana 93% |
| PASS | Card cells' median monthly failure range rounds to 84-93% | 84.4%-93.1% |
| PASS | Failed-fee share holds at 89-90% under every data and translation choice | 90.1%, 89.4%, 90.1%, 90.1% |
| PASS | Removing the anomaly categories moves the share to 85% | 86.5% and 84.8% |
| PASS | Months with a failed-fee share below 78%: two on the corrected basis, none before the correction | corrected [{'month': 'Oct 2023', 'share': 0.7788974276954704}, {'month': 'Nov 2023', 'share': 0.7759307708384584}]; before [] |
| FLAG | Typed 'before the SLL correction' figures ($3,148,908; $2,842,692; $744,744) match the computed fix-off run | fix-off run gives $3,148,996, $2,842,781, $744,744. The typed figures also had the rate-spike screen switched off; the difference is $89 on failed fees |
| FLAG | Typed '$63.3K' removed by the SLL correction matches the computed difference | computed $63,356 |
| PASS | Largest value anomaly is a failed NGN record of 2.36 trillion over 24 attempts with a fee of NGN 314 | NGN 2,356,073,196,490, 24 attempts, fee 314.3 |
| FLAG | Customer 1039721: 'recurring UGX 500 million records ... 3,000-4,300 attempts at a consistent 3.0% fee' | 21 recurring failed UGX mobile money records (Aug 2022 - Apr 2024): value UGX 262-520 million, attempts 2,649-4,310, fee ratio 3.00%. The fee ratio is right; '500 million' and '3,000-4,300' are looser than the data |

## 7. Cross-output consistency

| Result | Check | Detail |
| --- | --- | --- |
| PASS | Every value the text uses appears in the report PDF | all values found |
| PASS | Every value the text uses appears in the brief PDF | all values found |
| PASS | Report and brief draw the same rendered value for every shared token | 34 shared tokens come from one context dictionary |
| PASS | The_Economics_of_Payment_Failure.pdf: centred footer (author line, contact, ORCID) on every page except the cover | pages without it: [] |
| PASS | The_Economics_of_Payment_Failure.pdf: the page number follows the title on line 2 |  |
| PASS | Executive_Brief.pdf: centred footer (author line, contact, ORCID) on every page except the cover | pages without it: [] |
| PASS | Executive_Brief.pdf: the page number follows the title on line 2 |  |
| PASS | Dashboard at default settings: says every figure matches the report |  |
| PASS | Dashboard figure titles equal the figure index titles | 26 charts; titles missing from the dashboard: [] |

## 8. Hedging

| Result | Check | Detail |
| --- | --- | --- |
| FLAG | No causal or overconfident wording the data cannot support | 2 unhedged sentences to read: The: Exposure bridge – $2.78M $1.07M / 38.5% $1.71M / 61.5% Anomalous-account exposure CONTAIN Remaining failed-fee exposure IMPROVE Mutually exclusive cat / Exe: What the data shows A few accounts drive the spikes. |
| PASS | 'Lost revenue' appears only in the negative ('not lost revenue') | 2 uses |
