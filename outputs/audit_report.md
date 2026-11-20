# Audit report

116 checks: **114 pass**, **0 fail**, **2 flagged for the author**. A FLAG is a finding that needs a decision; nothing was changed because of it.

## Flagged for you

- **[4. Denominators] Every sentence with a percentage states or implies its population.** 66 sentences with a percentage; 8 without any population cue (list in outputs/audit_percentages.csv): Remaining exposure: $1.71M (61.5%) Improve This is everything left once the two anomaly categories are set aside. | It covers every channel, but card carries 82% of remaining exposure ($1.40M) and USD card alone 61% of remaining exposure ($1.04M). | The high-value gap survives every exclusion: 75% against 42% even with all three applied.
- **[7. Cross-output consistency] Layout: no chapter-end page under 25% full.** pages 10 (22%), 35 (20%)

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
| PASS | figure_index.csv (read by the report, dashboard and Doc sync) agrees with figures.label() |  |
| PASS | Ten dashboard-only figures, labelled D1-D10 |  |

## B. Baseline

| Result | Check | Detail |
| --- | --- | --- |
| PASS | results.json matches the baseline except approved changes (ints exact, floats to 1e-9) | 0 approved differences; every other value identical |
| PASS | Every baseline table (CSV) matches except approved changes | 38 tables compared |
| PASS | Every rendered report value matches the baseline except approved changes (exact text) | 566 identical, 3 approved changes, 93 new values |

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
| PASS | Allow-listed thresholds equal config/assumptions.yaml | 24 thresholds checked |
| PASS | No typed number outside the allow-list (computed numbers must be {{tokens}}) | 0 typed numbers not on the allow-list {}. Full list: outputs/audit_typed_numbers.csv. First:  |
| PASS | Every {{token}} in the content resolves to a value |  |
| PASS | Key tokens agree with results.json (formatted independently) | 13 tokens agree |

## 3. Terminology

| Result | Check | Detail |
| --- | --- | --- |
| PASS | One term for: Extreme-volume anomalies | 0 variant uses.  |
| PASS | One term for: The escalation account (47087) | 0 variant uses.  |
| PASS | One term for: Remaining exposure | 0 variant uses.  |
| PASS | One term for: Fees on failed transactions | 0 variant uses.  |
| PASS | One term for: Successful-transaction fees | 0 variant uses.  |

## 4. Denominators

| Result | Check | Detail |
| --- | --- | --- |
| PASS | Fee per failed attempt (Table 3): fees and failed attempts both from records with an exchange rate | recomputed from the prepared records and compared with the six printed cells; all six agree |
| PASS | Sector table covers all fees on failed transactions (with an 'Unlabelled sector' row) | sector rows sum to $2,779,424; headline $2,779,424; unlabelled $71,766 |
| FLAG | Every sentence with a percentage states or implies its population | 66 sentences with a percentage; 8 without any population cue (list in outputs/audit_percentages.csv): Remaining exposure: $1.71M (61.5%) Improve This is everything left once the two anomaly categories are set aside. / It covers every channel, but card carries 82% of remaining exposure ($1.40M) and USD card alone 61% of remaining exposure ($1.04M). / The high-value gap survives every exclusion: 75% against 42% even with all three applied. |
| PASS | No comparison sets two different populations without saying so | 0 to read:  |

## 5. Units and periods

| Result | Check | Detail |
| --- | --- | --- |
| PASS | No sentence compares an annual figure with a 28-month figure | 0 to read:  |
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
| PASS | The 89% and 79% are described as averages of the monthly shares (the pooled yearly shares are different) | pooled yearly shares are 90.2% (2022) and 78.9% (2024); the text gives the monthly averages 89.2% and 78.8% |
| PASS | Tanzania ranks second in the base case despite fewer attempts than Uganda |  |
| PASS | Bank transfer is the one reliable channel | 5.7% |
| PASS | Card is structural: card cells' typical month fails at 84-93% | see Laney medians: Kenya 93%, Uganda 84%, Tanzania 87%, Ghana 93% |
| PASS | Card cells' median monthly failure range rounds to 84-93% | 84.4%-93.1% |
| PASS | Failed-fee share holds at 89-90% under every data and translation choice | 90.1%, 89.4%, 90.1%, 90.1% |
| PASS | Removing the anomaly categories moves the share to 85% | 86.5% and 84.8% |
| PASS | Months with a failed-fee share below 78%: two on the corrected basis, none before the correction | corrected [{'month': 'Oct 2023', 'share': 0.7788974276954704}, {'month': 'Nov 2023', 'share': 0.7759307708384584}]; before [] |
| PASS | The 'before the SLL correction' figures are computed by a run with only the redenomination fix switched off | fees $3,148,996; fees on failed transactions $2,842,781; January $744,744; removed by the correction $63,356 |
| PASS | Largest value anomaly is a failed NGN record of 2.36 trillion over 24 attempts with a fee of NGN 314 | NGN 2,356,073,196,490, 24 attempts, fee 314.3 |
| PASS | Customer 1039721: 21 recurring failed UGX records, UGX 262-520 million, 2,649-4,310 attempts, 3.0% fee (exact values in the text) | 21 records; UGX 262-520 million; attempts 2,649-4,310; fee ratio 3.00% |
| PASS | 'Six in ten' and 'nine in ten' equal the count failure rate and failed-fee share rounded to tenths | count failure rate 62.0%; failed-fee share 90.1% |
| PASS | Recovery: zero-success USD card customer-months are a third of USD card failed attempts, and the base case leaves them out at about $158.8K | 33.3% of failed attempts in 3,959 customer-months; $158,819 |
| PASS | Recovery: the resampling interval contains the base case; 5,000 replicates with a fixed seed | 90% interval $142,444-$430,626, median $262,338, seed 2026 |
| PASS | Lapse: 4,328 customers had no activity in Feb-Apr 2024; 46% were active in only one or two months and 33% had an earlier gap of three months or more | 4,328 customers; 46.2% in one or two months; 32.8% with a gap of three months or more |
| PASS | Records by status: 39,570 failed and 23,114 successful | 39,570 failed; 23,114 successful |
| PASS | The executive summary: the $324K sentence is followed by the zero-success and interval sentence, with the figures of Section 7 | zero-success $159K; 90% interval $142K–$431K; benchmark without account 47087 $324K |
| PASS | The brief: the $324K sentence is followed by the zero-success and interval sentence, with the figures of Section 7 | zero-success $159K; 90% interval $142K–$431K; benchmark without account 47087 $324K |
| PASS | Executive summary is 400-500 words | 493 words |
| PASS | Brief is 5 pages | 5 pages |
| PASS | Brief and summary open the anomaly bullet with 'Twenty extreme-volume observations' (the number in words) |  |
| PASS | No content uses the ambiguous {{customers}} token (customers with failed fees: customers_failed; who transacted: customers_transacting) |  |

## 7. Cross-output consistency

| Result | Check | Detail |
| --- | --- | --- |
| PASS | Every value the text uses appears in the report PDF | all values found |
| PASS | Every value the text uses appears in the brief PDF | all values found |
| PASS | Report and brief draw the same rendered value for every shared token | 42 shared tokens come from one context dictionary |
| PASS | The_Economics_of_Payment_Failure.pdf: centred footer (author line, contact, ORCID) on every page except the cover | pages without it: [] |
| PASS | The_Economics_of_Payment_Failure.pdf: the page number follows the title on line 2 |  |
| PASS | Executive_Brief.pdf: centred footer (author line, contact, ORCID) on every page except the cover | pages without it: [] |
| PASS | Executive_Brief.pdf: the page number follows the title on line 2 |  |
| PASS | Excel 99_Checks: every row reads OK (recalculated copy) | 93 of 93 OK |
| PASS | Layout: no paragraph, list item or table splits across pages (tables over 12 rows may continue) | 35 pages;  |
| PASS | Layout: all ten chapters and appendices start a page | pages [7, 8, 11, 15, 19, 21, 23, 27, 31, 34] |
| PASS | Layout: no main-report page under 60% full unless it ends a chapter | every body page is at least 60% full |
| FLAG | Layout: no chapter-end page under 25% full | pages 10 (22%), 35 (20%) |
| PASS | Dashboard at default settings: says every figure matches the report |  |
| PASS | Dashboard figure titles equal the figure index titles | 26 charts; titles missing from the dashboard: [] |

## 8. Hedging

| Result | Check | Detail |
| --- | --- | --- |
| PASS | No causal or overconfident wording the data cannot support | 0 unhedged sentences to read:  |
| PASS | 'Lost revenue' appears only in the negative ('not lost revenue') | 2 uses |
