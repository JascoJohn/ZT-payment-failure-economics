# Typed numbers: proposal to convert to `{{tokens}}` (nothing converted yet)

Stage 11 found **88 typed numbers** in `report/content/` that are not on the allow-list
(`outputs/audit_typed_numbers.csv` lists each with its line). This page groups them, says which pipeline value each
would come from, and shows where the computed value differs from what is typed. Reply with approval, or strike lines.

## A. Convert to a token that already exists (same value, no change to the printed text)

| Where | Typed | Token | Rendered |
| --- | --- | --- | --- |
| Table 4, column "Largest customer's share of Q5 failed fees" | 57%, 54%, 40%, 58%, 41% | `qa_ml`, `qe_ml`, `qs_ml`, `qv_ml`, `q3_ml` | 57%, 54%, 40%, 58%, 41% |
| Table 5 rows (successes, prior six-month median) | 0, 1, 28, 103 | `an0_s`, `an0_m` … `an4_s`, `an4_m` | same |
| Table 5 "Other 15 observations" | 15 | `an_rest_n` | 15 |
| Table 6, Table 18, Section 4 text | 20 | `an_obs` / `hx_o` | 20 |
| Section 4.2 | 199 failed attempts in October 2023 | `esc_oct` | 199 |
| Table 8 "Eligible months" | 28, 12, 20, 22, 14, 15 … | `lp_<market>_<channel>_n` | same |
| Appendix A flags and text | 39; 64; 30 currencies | `flag_missing`; `flag_value`; `untr_ccy` | 39; 64; 30 |
| "28 months", "of 28" (about 25 places) | 28 | `nm` | 28 |

## B. New tokens for numbers that are results (same value unless marked)

| Where | Typed | New token and definition | Computed |
| --- | --- | --- | --- |
| Chapter 2 opening | "Six in ten", "nine in ten" | `count_rate_tenths`, `fee_share_tenths`: the rate rounded to tenths, in words | Six in ten (62.0%); nine in ten (90.1%) |
| 2.2 trend, glance page | "about 89% in 2022 to about 79% in 2024" | `fs_rem_2022`, `fs_rem_2024`: **average of the monthly failed-fee shares** of remaining exposure | 89%, 79% |
| 3.3 Table 3 | "Yield: 8× the average" | `tc_yield_x`: Tanzania card fee per failed attempt ÷ all-cells average | 8× (8.4) |
| 3.3 text | "three and a half times the fee of a Kenyan card failure" | `tc_vs_kc_words`: ratio rounded to the nearest half, in words | three and a half (3.48) |
| 4.1, 4.2 | "Twenty observations", "Twenty extreme customer-months" (summary, glance, brief) | `an_obs_words` | Twenty |
| 4.2 | "no more than 90 successes in any month" | `esc_smax`: largest monthly successes of the escalation account | 90 |
| 4.4 | "flat at 85–88%" | `ten_fs_range`: range of the four tenure bands' failed-fee share | 85–88% |
| 4.5 | "Ten cells have at least 12 months …" | `lp_cells_words` | Ten |
| 4.5 Table 8 "Flags" column | typed flags per cell | `lp_<cell>_flags` | identical to typed (checked) |
| 4.5 Table 8 last column | "Dec 2023 (70%), Jan 2024 (58%)", "Oct 2022, Aug and Sep 2023 (35–41%)" … | `lp_<cell>_sig`, **generated** as "month (share), …" | **wording changes** for Uganda mobile money: "Oct 2022 (36%), Aug 2023 (35%), Sep 2023 (41%)" |
| 4.5 text | "90% one account", "87% one account" | `lp_km_last_share`, `lp_gc_share` | 90%, 87% |
| 4.5 text | "84–93% in a typical month" | `lp_card_med_range`: range of the four card cells' median monthly failure | 84–93% |
| 5 text | "three card accounts", "three January card accounts" | `jan_card_n_words`: January card accounts among the largest extreme-volume observations | three |
| 5 text (your wording) | "in six months between January 2022 and July 2023" | `an_early_n_words`: months in that window with an extreme-volume observation (the dates stay typed) | six |
| 6 | "about 6%" | `fx_mean_pct`: mean of the two measures' difference ÷ constant | 6% |
| 7.1 | "more than 100,000 non-anomalous mobile money attempts and a few dozen USD card attempts" | `esc_mm_att`, `esc_card_att` | **wording changes** to "106,761 … and 49" |
| Brief | "Two in five failed-fee dollars" | `anom_in_n_words` | Two in five (38.5%) |
| Cover, summary, glance, brief | "five African markets", "five markets" | `n_markets_words` | five |
| Appendix A.3 | "2.36 trillion across 24 attempts with a fee of NGN 314", "UGX 500 million … 3,000–4,300 attempts … 3.0%" | `va_*`: the largest value anomaly and customer 1039721's recurring records, read from the data | 2.36 trillion, 24, NGN 314 ✓; **500 million → "262–520 million" and 3,000–4,300 → "2,649–4,310"** (the typed ranges are looser than the data) |
| Appendix B | "89–90%", "then to 85%" | `sens_fs_range`, `sens_fs_anom` | 89–90%, 85% |

## C. Brief reconciliation and the SLL figures (computed by switching the fix off in stage 01E)

The typed "before the SLL correction" figures reproduce **only** when the rate-spike screen is also switched off. With only
the SLL fix off (what you asked for), the computed figures differ slightly:

| Item | Typed | Computed (fix off) | Difference |
| --- | --- | --- | --- |
| Recorded fees before correction | $3,148,908 | $3,148,996 | +$88 |
| Fees on failed transactions before correction | $2,842,692 (also $2,842.7K) | $2,842,781 ($2,842.8K) | +$89 |
| Failed-fee share before correction | 90.3% | 90.3% | none |
| January 2024 failed fees before correction | $744,744 | $744,744 | none |
| Removed by the SLL correction (Appendix A.5, glance page) | $63.3K | $63.4K ($63,356) | +$0.1K |
| January count rate / failed-fee share | 79.8% / 97.3% | 79.8% / 97.3% | none |
| Months below 78% | 2 (Oct 2023 77.9%, Nov 2023 77.6%); none before | same | none |
| Bank transfer share of records | 1.6% | 1.6% | none |

Tokens: `pre_fees_d`, `pre_ff_d`, `pre_ff_k`, `pre_fs`, `pre_jan_d`, `sll_effect_k`, `jan_cr`, `jan_fs_all`, `lo78_n`, `lo78_list`,
`lo78_n_pre`, `bank_rec_share` (already defined in `report.context`).

## D. Stay typed (allow-list, `report/content/number_allowlist.yaml`)

Years; account numbers (47087, 49957, 51026, 49477, 1039721, checked against the data by stage 11); thresholds that are
in `config/assumptions.yaml` (stage 11 checks each equals the config value): 1,000 / 50× / 5% / 5,000, the strict and
loose sensitivity thresholds, 75%, 500, 12, 70%, 10 points, 15 points, 10% screen, 5×, 0.5% / 20%, $10,000, cost ratios,
best 3-month window, tenure band labels; the Laney constant 1.128; IAS 21; the 1 July 2022 redenomination and 1 SLE = 1,000 SLL;
figures quoted from the challenge brief (1.65M, 1.02M, 62%, $3.15M, $2.85M, 90%, 97%, 78%, $745K, 94% / 77% / 3%, 2%, 93%);
document structure words (three actions, three measures, six largest cells, five actions …).

## Also flagged, no change made

- **89% and 79%**: they only hold as averages of the *monthly* shares (89.2%, 78.8%). The pooled yearly shares are 90.2% (2022)
  and 78.9% (2024). The text does not say "average of the monthly shares".
