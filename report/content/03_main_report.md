## 1. Introduction

This report measures what payment failure costs ZT East Africa, where that cost comes from, how much of it could realistically be recovered, and what management should do first. It uses the supplied dataset: {{records}} monthly records of {{attempts}} payment attempts by merchants in Kenya, Uganda, Tanzania, Ghana and Zambia, from January 2022 to April 2024, with daily exchange rates and a customer table.

The challenge brief asks for the issues to be highlighted. This report goes further in three ways. It separates exceptional account behaviour from the persistent problem, so that a few accounts do not set the agenda. It translates every currency carefully and shows how much of the trend is exchange rates rather than performance. And it values a realistic recovery against an observed benchmark rather than treating every failed fee as lost money.

Three measures recur throughout. They answer different questions, so all three are reported:

$$ \text{Count failure rate} = \frac{\text{failed attempts}}{\text{all attempts}}, \qquad \text{Failed-fee share} = \frac{\text{fees on failed transactions}}{\text{all recorded fees}}, \qquad \text{Failed-value share} = \frac{\text{value of failed attempts}}{\text{value of all attempts}} $$

Count measures use every record. Dollar measures use the {{records_tr}} records that have an exchange rate (Appendix A). Each finding carries a label showing how firmly the data supports it: *[Observed]* for figures read directly from the data, *[Calculated]* for results of a stated formula, *[Proxy]* for classifications standing in for something the data cannot show, and *[Hypothesis]* for possible explanations.

## 2. Scale: separating exceptional from persistent exposure

Fees recorded on failed transactions total {{failed_fees_m}}, {{fee_share}} of all recorded fees. That headline mixes two very different things, and this section separates them before anything else is analysed.

Six in ten attempts fail by count ({{count_rate}}), and nine in ten fee dollars sit on failed transactions. The gap between the two rates is itself a finding, explained at the end of this section.

### The exposure bridge

The headline is split into three mutually exclusive categories. Every failed fee falls into exactly one:

$$ F_{\text{total}} = F_{\text{extreme-volume anomalies}} + F_{\text{escalation}} + F_{\text{remaining}} $$

Extreme-volume anomalies are sudden account-level bursts, defined in Section 4. Escalation is the other activity of one account whose failures grew steadily rather than suddenly. Remaining exposure is everything else.

[[figure bridge]]

{{fig:bridge}} shows that {{anom_share}} of the exposure, {{anom_m}}, sits in exceptional account behaviour. {{tab:bridge}} gives the detail behind the bars.

::: table bridge | Exposure bridge: fees on failed transactions by category
| Category | Definition | Failed attempts | Fees on failed transactions | Share |
| --- | --- | --- | --- | --- |
| Extreme-volume anomalies | 20 customer-month-channel observations meeting the relative rule (Section 4), including account 47087's January 2024 mobile money observation ({{an4_ff}}) | {{ex_fatt}} | {{ex_k}} | {{ex_share}} |
| Escalation | Account 47087's other observations | {{es_fatt}} | {{es_k}} | {{es_share}} |
| Remaining exposure | All other observations | {{rm_fatt}} | {{rm_k}} | {{rm_share}} |
| **Total** |  | **{{failed}}** | **{{failed_fees_k}}** | **100%** |
Source: ZT East Africa supplied dataset; author's calculations.

The categories reconcile exactly on unrounded values ({{ex_d}} + {{es_d}} + {{rm_d}} = {{failed_fees_d}}). The anomaly categories are proxies: they identify unusual behaviour, not its cause. Remaining exposure is not a single channel or customer group: card carries {{rm_card_share}} of it ({{rm_card_m}}), USD card alone {{rm_usdcard_share}}, and mobile money {{rm_mm_share}}. *[Observed; categories are proxies]*

### The trend once anomalies are removed

[[figure trend]]

{{fig:trend}} compares all records with the remaining exposure, which excludes both the extreme-volume anomalies and the escalation account's other observations. The spikes at the end of the period belong to the anomaly categories. Without them, the count failure rate stays between {{rem_range_words}} in every month, and the failed-fee share drifts down from about 89% in 2022 to about 79% in 2024. The remaining problem is chronic, but it is not getting worse. *[Observed]*

### Three ways to measure the same failures

The three measures in Section 1 give different answers, as {{tab:perspectives}} shows.

::: table perspectives | Three exposure perspectives, whole period
| Perspective | Measure | Whole period | Population |
| --- | --- | --- | --- |
| Operational | Count failure rate | {{count_rate}} | All records |
| Financial | Failed-fee share | {{fee_share}} | Translatable records |
| Commercial | Failed-value share | {{failed_value_share}} | Translatable records, excluding value anomalies |

The dollar measures sit well above the count measure because failures skew to larger payments. The average failed attempt carried {{avg_failed_value}} of value against {{avg_success_value}} for a successful one, {{value_ratio}} as much. Fees are charged at a similar rate on both: {{failed_intensity}} of value on failed attempts and {{success_intensity}} on successful ones. Failed fees are high because failed payments are large, not because failures are priced differently. *[Observed]*

## 3. Where failure concentrates

This section asks where the remaining exposure sits: by payment type, market, customer, cell and payment size. The answer is consistent at every level. One channel holds most of the exposure, and it fails in every market.

### By payment type and market

[[figure channels]]

{{fig:channels}} shows that card holds {{card_share}} of fees on failed transactions and mobile money {{mm_share}}. Bank transfer is the one reliable channel, failing {{bank_rate}} of the time. It carries only {{bank_att_share}} of attempts at {{bank_fpf}} per failed attempt, however, so moving volume towards it is not a meaningful lever. *[Observed]*

[[figure heatmap]]

{{fig:heatmap}} crosses market with payment type. Card failure is high in every market ({{card_range}}), while mobile money ranges from {{mm_min}} in Uganda to {{mm_max}} in Kenya, where account 47087 inflates the rate. Kenya card carries {{kenya_card_all}} across all records, of which {{kenya_card_extreme}} is extreme-volume anomalies. Among currencies, USD records fail {{usd_rate}} of the time and hold {{usd_share}} of failed fees ({{usd_ff}}); GHS ({{ghs_ff}}) and UGX ({{ugx_ff}}) follow. The problem is a channel problem that shows up everywhere, not a market problem. *[Observed]*

### By customer

[[figure pareto]]

Exposure is also concentrated by customer. Of the {{customers_transacting}} customers who transacted, {{customers_failed}} recorded fees on failed transactions, and {{fig:pareto}} ranks these {{customers_failed}}. The top 10 hold {{top10}} of failed fees, and the top 1% ({{top1pct_n}} customers) hold {{top1pct}}. Excluding extreme-volume anomalies, the top 10 still hold {{top10_ex}}. Account-level review is therefore an efficient first step: a small list of merchants covers most of the money. *[Observed]*

### What drives each cell: volume, failure rate or fee yield

A cell's failed fees can be written as the product of three drivers, so the same exposure can arise for different reasons:

$$ F_i = A_i \times f_i \times y_i $$

Here \( A_i \) is the cell's attempts, \( f_i \) its failure rate and \( y_i \) the fee per failed attempt. {{tab:drivers}} applies this to the six largest cells, excluding extreme-volume anomalies.

::: table drivers | Drivers of failed fees by cell, excluding extreme-volume anomalies
| Cell | Share of attempts | Failure rate | Fee per failed attempt | Fees on failed transactions | Dominant driver |
| --- | --- | --- | --- | --- | --- |
| Kenya card | {{dr_kc_sa}} | {{dr_kc_fr}} | {{dr_kc_fpf}} | {{dr_kc_ff}} | Reliability, at scale |
| Kenya mobile money | {{dr_km_sa}} | {{dr_km_fr}} | {{dr_km_fpf}} | {{dr_km_ff}} | One account (47087) |
| Uganda card | {{dr_uc_sa}} | {{dr_uc_fr}} | {{dr_uc_fpf}} | {{dr_uc_ff}} | Reliability |
| Tanzania card | {{dr_tc_sa}} | {{dr_tc_fr}} | {{dr_tc_fpf}} | {{dr_tc_ff}} | Yield: 8× the average |
| Ghana card | {{dr_gc_sa}} | {{dr_gc_fr}} | {{dr_gc_fpf}} | {{dr_gc_ff}} | Reliability |
| Uganda mobile money | {{dr_um_sa}} | {{dr_um_fr}} | {{dr_um_fpf}} | {{dr_um_ff}} | Scale: low failure, most attempts |
| **All cells** | 100% | {{dr_all_fr}} | {{dr_all_fpf}} | {{dr_all_ff}} | — |

[[figure drivers]]

{{fig:drivers}} places each cell by its share of attempts and its failure rate. The card cells sit high: they need a reliability fix. Uganda mobile money sits low and far to the right. It fails less often than average and its exposure comes from volume, so it does not need the same fix. Tanzania card is a yield story: each failure carries about three and a half times the fee of a Kenyan card failure. *[Calculated]*

### By payment size

[[figure quintiles]]

{{fig:quintiles}} splits attempts into five size bands (quintiles of the average value per aggregated record). Card fails at {{q_card_range}} in every band. Mobile money fails {{q_mm_range}} below the top band and {{q_mm_5}} within it. Because a single account can drive a band, the result was rerun under four exclusions in {{tab:quintiles}}.

::: table quintiles | Top-quintile failure under alternative exclusions
| Version | Mobile money Q5 failure | Mobile money Q1–Q4 failure | Mobile money Q5 failed fees | Largest customer's share of Q5 failed fees | Card Q5 / Q1–Q4 failure |
| --- | --- | --- | --- | --- | --- |
| All translatable records | {{qa_m5}} | {{qa_m14}} | {{qa_mf}} | 57% | {{qa_c}} |
| Excluding extreme-volume anomalies | {{qe_m5}} | {{qe_m14}} | {{qe_mf}} | 54% | {{qe_c}} |
| Excluding account 47087 | {{qs_m5}} | {{qs_m14}} | {{qs_mf}} | 40% | {{qs_c}} |
| Excluding value anomalies | {{qv_m5}} | {{qv_m14}} | {{qv_mf}} | 58% | {{qv_c}} |
| All three exclusions | {{q3_m5}} | {{q3_m14}} | {{q3_mf}} | 41% | {{q3_c}} |

The high-value gap survives every exclusion: {{q3_m5_0}} against {{q3_m14_0}} even with all three applied. More than half of the fee exposure behind it, however, is account 47087. High-value mobile money failure is a genuine pattern worth investigating, not yet a case for changing payment limits. *[Observed pattern; cause is a hypothesis]*

## 4. Failure diagnostics

The data has no failure codes, so this section classifies patterns rather than causes. It defines the anomaly categories used in Section 2, splits failures into "hard" and "mixed", and identifies which customers and cells fail persistently. *[Proxy throughout]*

### Extreme-volume anomalies

A customer-month-payment type is flagged as an extreme-volume anomaly when all three conditions hold:

$$ F_{c,m} \ge 1{,}000, \qquad A_{c,m} > 50 \times \max\left(\operatorname{median}(A_{c,m-6},\ldots,A_{c,m-1}),\ 1\right), \qquad \frac{S_{c,m}}{A_{c,m}} < 5\% $$

Here \( F \), \( A \) and \( S \) are failed, total and successful attempts for customer \( c \) in month \( m \). Twenty observations from {{an_cust}} customers qualify. {{tab:anomalies}} lists the largest.

::: table anomalies | Largest extreme-volume anomaly observations
| Account | Market | Channel | Month | Failed attempts | Successes | Prior six-month median | Fees on failed transactions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 49957 | Kenya | Card | Jan 2024 | {{an0_f}} | 0 | 1 | {{an0_ff}} |
| 51026 | Uganda | Card | Jan 2024 | {{an1_f}} | 0 | {{an1_m}} | {{an1_ff}} |
| 49477 | Uganda | Card | Jan 2024 | {{an2_f}} | 0 | 0 | {{an2_ff}} |
| 49957 | Kenya | Card | Dec 2023 | {{an3_f}} | 0 | 1 | {{an3_ff}} |
| 47087 | Kenya | Mobile money | Jan 2024 | {{an4_f}} | 28 | 103 | {{an4_ff}} |
| Other 15 observations | — | — | 2022–2024 | {{an_rest_f}} | — | — | {{an_rest_ff}} |

Four account-months, all card, carry most of the anomaly exposure, and none of them recorded a single success. The pattern is consistent with automated retries or card testing, but the data cannot confirm automation. The result is not sensitive to the thresholds: the anomalies' share of failed fees is {{an_strict}} under strict rules (2,000 attempts, 100×, under 2% success), {{an_agreed}} under the agreed ones and {{an_loose}} under loose ones (500, 25×, under 10%). *[Proxy]*

### Sustained escalation

The relative rule has a blind spot: an account whose failures grow steadily raises its own baseline and is never flagged.

[[figure escalation]]

{{fig:escalation}} shows exactly this. Account 47087, a Kenyan merchant taking GHS mobile money, rose from 199 failed attempts in October 2023 to {{esc_jan}} in January 2024 and {{esc_apr}} in April, with no more than 90 successes in any month. Only its January observation crossed the relative rule. Its other activity forms the escalation category in Section 2 ({{es_k}}), and the monitoring framework in Section 8 adds an absolute trigger to catch this pattern. *[Observed]*

### Hard and mixed failures

A customer-month-channel with failures but no successes is a "hard" failure; one with both is "mixed". Hard failures may be consistent with configuration or acceptance problems, while mixed failures may reflect retries, entry errors or other intermittent issues; the data cannot distinguish these explanations. {{tab:hardmixed}} gives the split.

::: table hardmixed | Hard and mixed failures
| Classification | Customer-month-channels | Failed attempts | Share | Fees on failed transactions | Share |
| --- | --- | --- | --- | --- | --- |
| Extreme-volume anomaly | 20 | {{hx_f}} | {{hx_fs}} | {{hx_ff}} | {{hx_ffs}} |
| Hard: no successes that month | {{hh_o}} | {{hh_f}} | {{hh_fs}} | {{hh_ff}} | {{hh_ffs}} |
| Mixed: successes and failures | {{hm_o}} | {{hm_f}} | {{hm_fs}} | {{hm_ff}} | {{hm_ffs}} |

[[figure hard_mixed]]

{{fig:hard_mixed}} shows the split by channel. Hard failures make up {{hard_card}} of card's non-anomalous failed fees, against {{hard_mm}} for mobile money. Customer-months with repeated failures and no successes warrant checking acceptance, configuration and currency routing, although the data cannot rule out customer-side causes. *[Proxy; causes are hypotheses]*

### Persistent customers, tenure and lapse

Of {{pers_elig}} customers with at least six active months, {{pers_n}} ({{pers_pct}}) are persistent: their monthly failure rate is 75% or higher in at least half of their active months. They hold {{pers_fatt}} of failed attempts but **{{pers_ffee}} of failed fees** outside the anomalies, so they matter financially, not only in number. A further {{one_off}} customers had an elevated month without it recurring. *[Observed]*

{{tab:tenure}} asks whether new customers fail more.

::: table tenure | Failure by customer tenure at the month of attempt
| Tenure | Count failure rate | Failed-fee share | Share of failed fees |
| --- | --- | --- | --- |
| 0–3 months | {{ten0_cr}} | {{ten0_fs}} | {{ten0_sh}} |
| 4–12 months | {{ten1_cr}} | {{ten1_fs}} | {{ten1_sh}} |
| 13–24 months | {{ten2_cr}} | {{ten2_fs}} | {{ten2_sh}} |
| 25+ months | {{ten3_cr}} | {{ten3_fs}} | {{ten3_sh}} |

Failure is U-shaped across tenure, but the failed-fee share is flat at 85–88%, so onboarding is not the main source of exposure. Failure is, however, associated with leaving. {{lapsed}} of the {{active_before}} customers active before February 2024 ({{lapse_rate}}) made no attempts in February–April 2024. Before February, these lapsed customers had failed more than retained ones: {{lapse_cr_l}} against {{lapse_cr_r}} by count. Among customers with six or more active months, {{lapse_p}} of persistent customers lapsed against {{lapse_o}} of the rest. This is consistent with failure driving attrition, but it does not prove it. *[Observed association; causation is a hypothesis]*

### Structural or episodic: control charts by cell

To tell a structural problem from a temporary spike, each market × payment type cell was tracked on a Laney p′ control chart. This is a standard chart adjusted for the extra month-to-month variation that large samples show. For month \( i \) with \( n_i \) attempts:

$$ \bar p = \frac{\sum_i F_i}{\sum_i n_i}, \qquad \sigma_{p,i} = \sqrt{\frac{\bar p(1-\bar p)}{n_i}}, \qquad z_i = \frac{p_i - \bar p}{\sigma_{p,i}}, \qquad \sigma_z = \frac{\overline{|z_i - z_{i-1}|}}{1.128}, \qquad \text{UCL}_i = \bar p + 3\,\sigma_{p,i}\,\sigma_z $$

Ten cells have at least 12 months with 500 or more attempts; the excluded cells hold {{lp_exc_share}} of failed fees. {{tab:laney}} gives each cell's flags, which are not mutually exclusive.

::: table laney | Pattern flags by cell
| Cell | Eligible months | Median monthly failure | First 6 → last 6 months | Flags | Months above the control limit (largest customer's share) |
| --- | --- | --- | --- | --- | --- |
| Kenya card | 28 | {{lp_Kenya_card_med}} | {{lp_Kenya_card_f6}} → {{lp_Kenya_card_l6}} | Structural, episodic | Dec 2023 (70%), Jan 2024 (58%) |
| Uganda card | 28 | {{lp_Uganda_card_med}} | {{lp_Uganda_card_f6}} → {{lp_Uganda_card_l6}} | Structural, episodic | Jan 2024 (50%) |
| Kenya mobile money | 28 | {{lp_Kenya_mobilemoney_med}} | {{lp_Kenya_mobilemoney_f6}} → {{lp_Kenya_mobilemoney_l6}} | Deteriorating, episodic | Apr 2024 (90%) |
| Tanzania card | 12 | {{lp_Tanzania_card_med}} | {{lp_Tanzania_card_f6}} → {{lp_Tanzania_card_l6}} | Structural | — |
| Ghana card | 20 | {{lp_Ghana_card_med}} | {{lp_Ghana_card_f6}} → {{lp_Ghana_card_l6}} | Structural, deteriorating, episodic | May 2023 (87%) |
| Uganda mobile money | 28 | {{lp_Uganda_mobilemoney_med}} | {{lp_Uganda_mobilemoney_f6}} → {{lp_Uganda_mobilemoney_l6}} | Episodic | Oct 2022, Aug and Sep 2023 (35–41%) |
| Kenya alternative channels | 22 | {{lp_Kenya_alternative_channels_med}} | {{lp_Kenya_alternative_channels_f6}} → {{lp_Kenya_alternative_channels_l6}} | Structural | — |
| Tanzania mobile money | 14 | {{lp_Tanzania_mobilemoney_med}} | {{lp_Tanzania_mobilemoney_f6}} → {{lp_Tanzania_mobilemoney_l6}} | Stable | — |
| Zambia mobile money | 15 | {{lp_Zambia_mobilemoney_med}} | {{lp_Zambia_mobilemoney_f6}} → {{lp_Zambia_mobilemoney_l6}} | Stable | — |
| Ghana mobile money | 15 | {{lp_Ghana_mobilemoney_med}} | {{lp_Ghana_mobilemoney_f6}} → {{lp_Ghana_mobilemoney_l6}} | Unstable | — |
Flags: structural = median failure of 70% or more; deteriorating = last six months at least 10 points above the first six; episodic = a month above the control limit; unstable = standard deviation of 15 points or more.

The adjustment matters: \( \sigma_z \) ranges from {{lp_sz_min}} to {{lp_sz_max}}, so ordinary limits would be several times too narrow. The largest-customer share decides how each signal should be read. Kenya mobile money's April "deterioration" is 90% one account (47087), and Ghana card's May 2023 signal is 87% one account. Uganda mobile money's signals are weak and should be treated as monitoring prompts rather than evidence of a material deterioration. All these readings are limited by the short series of 28 monthly points, which allows no test of seasonality or of independence between months, and by the concentration of some months in single customers. The structural problems are the card cells, which fail at 84–93% in a typical month, spikes or not. *[Calculated]*

## 5. January 2024 investigation

January 2024 is the month the brief singles out. Fees on failed transactions rose from a {{jan_base_k}} monthly average in July–December 2023 to {{jan_k}}. This section explains the jump in full, in a fixed order: anomalies first, then exchange rates, then the underlying drivers.

[[figure january]]

{{fig:january}} shows that extreme-volume anomalies account for {{jan_ex_k}} ({{jan_ex_share}}) of the increase. January's anomaly fees were {{jan_ex_jan_k}}, of which {{jan_top3}} sat in three card accounts, against a {{jan_ex_base_k}} baseline average. The remaining non-anomalous change was decomposed with the additive LMDI-I method:

$$ \Delta F = \sum_i L\left(F_i^1, F_i^0\right)\left[\ln\frac{N^1}{N^0} + \ln\frac{s_i^1}{s_i^0} + \ln\frac{f_i^1}{f_i^0} + \ln\frac{y_i^1}{y_i^0}\right], \qquad L(a,b) = \frac{a-b}{\ln a - \ln b} $$

The four terms are the volume, mix, failure-rate and fee-yield effects. \( N \) is total attempts, \( s_i \) the cell's share of attempts, \( f_i \) its failure rate and \( y_i \) its fee per failed attempt, at constant 2022 exchange rates. The method leaves no residual. {{tab:january}} gives the complete bridge.

::: table january | January 2024 bridge against the July–December 2023 monthly average
| Component | Amount | Evidence |
| --- | --- | --- |
| Baseline: Jul–Dec 2023 monthly average | {{jan_base_d}} | Observed |
| Extreme-volume anomalies (January {{jan_ex_jan_d}} less the {{jan_ex_base_d}} baseline) | {{jan_ex_d}} | Proxy |
| FX translation effect | {{jan_fx}} | Calculated |
| Volume effect | {{jan_vol}} | Calculated (LMDI) |
| Mix effect | {{jan_mix}} | Calculated (LMDI) |
| Failure-rate effect | {{jan_fr}} | Calculated (LMDI) |
| Fee-yield effect | {{jan_fy}} | Calculated (LMDI) |
| Entry/exit cells ({{jan_cells_out_n}} of {{jan_cells}} cells) | {{jan_ee}} | Calculated |
| **January 2024** | **{{jan_d}}** | Observed |

[[figure lmdi]]

{{fig:lmdi}} isolates the non-anomalous change of {{jan_nb_chg}}. Three conclusions follow.

- **Reliability did not worsen.** The failure-rate effect is slightly favourable, led by Uganda card, which improved from {{jan_ug_r0}} to {{jan_ug_r1}} failing. Outside the extreme-volume anomalies, January's failed-fee share was {{jan_fs1}} against an {{jan_fs0}} baseline.
- **Volume and yield explain the rest.** More attempts added {{jan_vol_k}}. A higher fee per failed attempt added {{jan_fy_k}}, almost all from Tanzania card, where it rose from {{jan_tz_y0}} to {{jan_tz_y1}}: a few large-ticket failures.
- **Exchange rates hardly matter here.** The translation effect is only {{jan_fx}}, because the gap between reported and 2022-rate fees was almost the same in the baseline months and in January.

January was an exceptional account-concentration event, not a broad deterioration. The three January card accounts did not repeat the burst: account 49957 recorded no activity after January, and the other two fell back to a handful of attempts. Account 47087 followed a different path, escalating through April 2024 (Section 4.2). Smaller extreme-volume observations also occur in February and April 2024, and in six months between January 2022 and July 2023. Account 49957 had already produced {{an3_ff}} in December, so a December alert would have caught it. The response January calls for is detection and containment, not a structural fix. *[Calculated]*

## 6. Foreign exchange analysis

{{fx_local_share}} of recorded fees are in local currencies, and several of them fell sharply against the US dollar during the period. This section measures how much of the reported trend is exchange rates rather than performance. Every local-currency fee is restated at its currency's 2022 average rate, record by record:

$$ F^{\text{cc}} = \sum_r L_r \times \bar e_{c(r),\,2022}, \qquad \text{Translation effect} = F^{\text{reported}} - F^{\text{cc}} $$

Here \( L_r \) is a record's fee in local currency and \( \bar e \) the currency's 2022 average rate in US dollars per unit.

[[figure fx_currency]]

{{fig:fx_currency}} shows that depreciation cut reported local-currency fees by {{fx_local_eff}} ({{fx_local_pct}}) against 2022 rates, and that the Ghanaian cedi accounts for {{fx_ghs_share}} of the effect. The effect grows with the cedi's slide: {{fx_y2022}} in 2022, {{fx_y2023}} in 2023 and {{fx_y2024}} in January–April 2024. {{tab:fxmeasures}} shows where it lands.

::: table fxmeasures | Reported fees against 2022 constant currency
| Measure | Reported | At 2022 constant currency | Difference |
| --- | --- | --- | --- |
| Fees on failed transactions | {{failed_fees_k}} | {{fx_ff_c}} | {{fx_ff_d}} ({{fx_ff_p}}) |
| Successful-transaction fees | {{succ_fees_k}} | {{fx_sf_c}} | {{fx_sf_d}} ({{fx_sf_p}}) |

Both measures shrink by about 6% in dollar terms. The two effects mean different things, though. On failed fees, depreciation flatters the trend: part of the apparent fall is exchange rates, not better completion. On successful fees, depreciation erased {{fx_sf_abs}} that was actually earned. Reporting only in US dollars would hide both. *[Calculated]*

### Is a monthly average rate appropriate?

Fees are translated at the monthly average of daily rates. This is an approximation informed by IAS 21, which allows an average rate when rates do not fluctuate significantly. To test that condition, currency-months whose daily high–low range exceeds 10% of the average were flagged; the 10% threshold is an analytical choice, not an IAS 21 rule. {{tab:ias}} gives the result.

::: table ias | Rate-volatility screen for the six main currencies
| Currency | Months above the 10% screen (of 28) | Average monthly range | Widest month |
| --- | --- | --- | --- |
| NGN | {{ias_NGN_n}} | {{ias_NGN_avg}} | {{ias_NGN_max}} |
| GHS | {{ias_GHS_n}} | {{ias_GHS_avg}} | {{ias_GHS_max}} |
| ZMW | {{ias_ZMW_n}} | {{ias_ZMW_avg}} | {{ias_ZMW_max}} |
| KES | {{ias_KES_n}} | {{ias_KES_avg}} | {{ias_KES_max}} |
| TZS | {{ias_TZS_n}} | {{ias_TZS_avg}} | {{ias_TZS_max}} |
| UGX | {{ias_UGX_n}} | {{ias_UGX_avg}} | {{ias_UGX_max}} |

As a sensitivity only, the flagged months were also translated at month-end rates. Fees in those months move from {{fx_flag_avg}} to {{fx_flag_end}} ({{fx_flag_pct}}), and all fees on failed transactions from {{failed_fees_k}} to {{fx_me_ff}} ({{fx_me_pct}}). The translation basis is not material to the totals. The volatile naira and cedi months should still be disclosed, and performance reported at constant currency alongside reported US dollars. *[Calculated]*

## 7. Recovery opportunity

Not every failed fee could be recovered, so this section values a realistic target rather than the whole {{failed_fees_m}}. It asks what USD card would earn if it failed no more often than mobile money does in the same market.

### Why USD card, and why the mobile money benchmark

Outside the extreme-volume anomalies, USD card holds {{rc_addr}} of fees on failed transactions, {{rc_addr_share}} of the total, and it has a natural benchmark: mobile money in the same market. A benchmark is only useful if the comparison is fair. Different customers might simply use different channels, so {{tab:gap}} compares the two channels across all activity and then among the same customers.

::: table gap | USD card against mobile money failure, all activity and the same customers
| Market | USD card, all | Mobile money, all | Gap (pp) | USD card, same customers | Mobile money, same customers | Gap (pp) | Customers using both |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Kenya | {{rm_Kenya_r}} | {{gap_Kenya_ma}} | {{rm_Kenya_pp}} | {{gap_Kenya_cs}} | {{gap_Kenya_ms}} | {{gap_Kenya_gs}} | {{gap_Kenya_n}} |
| Uganda | {{rm_Uganda_r}} | {{gap_Uganda_ma}} | {{rm_Uganda_pp}} | {{gap_Uganda_cs}} | {{gap_Uganda_ms}} | {{gap_Uganda_gs}} | {{gap_Uganda_n}} |
| Tanzania | {{rm_Tanzania_r}} | {{rm_Tanzania_t}} | {{rm_Tanzania_pp}} | {{gap_Tanzania_cs}} | {{gap_Tanzania_ms}} | {{gap_Tanzania_gs}} | {{gap_Tanzania_n}} |
| Ghana | {{rm_Ghana_r}} | {{rm_Ghana_t}} | {{rm_Ghana_pp}} | {{gap_Ghana_cs}} | {{gap_Ghana_ms}} | {{gap_Ghana_gs}} | {{gap_Ghana_n}} |
| Zambia | {{gap_Zambia_ca}} | {{rm_Zambia_t}} | {{rm_Zambia_pp}} | {{gap_Zambia_cs}} | {{gap_Zambia_ms}} | {{gap_Zambia_gs}} | {{gap_Zambia_n}} |
| **All five** | **{{gap_ca}}** | **{{gap_ma}}** | **{{gap_ga}}** | **{{gap_cs}}** | **{{gap_ms}}** | **{{gap_gs}}** | **{{gap_n}}** |

Among the {{gap_n}} customers who use both channels, the gap is {{gap_gs}} points, against {{gap_ga}} across all activity. Account 47087 distorts both comparisons. It is a Kenyan merchant with more than 100,000 non-anomalous mobile money attempts and a few dozen USD card attempts, so it sits inside Kenya's mobile money benchmark and among the customers using both channels. Without it, Kenya's mobile money failure rate falls from {{rm_Kenya_t}} to {{bx_kenya_mm}}, and the five-market gap is {{bx_gap_all}} points across all activity and {{bx_gap_same}} points among the {{bx_same_n}} customers using both. Kenya's narrow same-customer gap ({{gap_Kenya_gs}} points) is therefore mostly this one account; without it, the gap is {{bx_kenya_gap_same}} points. This comparison is descriptive: it does not separate channel effects from customer choice, nor show that mobile money's performance can be achieved on card. *[Observed]*

### The calculation

For each market \( c \):

$$ \Delta S_c = A_c \times \max\left(f_c - f_c^{*},\ 0\right), \qquad \Delta R_c = \Delta S_c \times \bar y^{\,s}_c, \qquad \text{Annual run-rate} = \sum_c \Delta R_c \times \frac{12}{28} $$

Here \( A_c \) is all non-anomalous USD card attempts (not only failed ones, since a lower failure rate applies to every attempt), \( f_c \) the current failure rate, \( f_c^{*} \) the target and \( \bar y^{\,s}_c \) the observed fee per successful USD card payment. Valuing additional successes at that observed average assumes the historical average fee applies to the extra payments as well. The assumption matters most in Tanzania, where the average is {{rm_Tanzania_fps}}, against {{rm_Uganda_fps}} in Uganda. {{tab:recovery}} applies the base case, which sets the target at mobile money's rate.

::: table recovery | Base-case recovery by market
| Market | Attempts (A) | Failed attempts | Current failure | Target (mobile money) | Reduction (pp) | Additional successes | Fee per success | Incremental fees |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Kenya | {{rm_Kenya_a}} | {{rm_Kenya_f}} | {{rm_Kenya_r}} | {{rm_Kenya_t}} | {{rm_Kenya_pp}} | {{rm_Kenya_add}} | {{rm_Kenya_fps}} | {{rm_Kenya_inc}} |
| Tanzania | {{rm_Tanzania_a}} | {{rm_Tanzania_f}} | {{rm_Tanzania_r}} | {{rm_Tanzania_t}} | {{rm_Tanzania_pp}} | {{rm_Tanzania_add}} | {{rm_Tanzania_fps}} | {{rm_Tanzania_inc}} |
| Uganda | {{rm_Uganda_a}} | {{rm_Uganda_f}} | {{rm_Uganda_r}} | {{rm_Uganda_t}} | {{rm_Uganda_pp}} | {{rm_Uganda_add}} | {{rm_Uganda_fps}} | {{rm_Uganda_inc}} |
| Ghana | {{rm_Ghana_a}} | {{rm_Ghana_f}} | {{rm_Ghana_r}} | {{rm_Ghana_t}} | {{rm_Ghana_pp}} | {{rm_Ghana_add}} | {{rm_Ghana_fps}} | {{rm_Ghana_inc}} |
| Zambia | {{rm_Zambia_a}} | {{rm_Zambia_f}} | {{rm_Zambia_r}} | {{rm_Zambia_t}} | {{rm_Zambia_pp}} | {{rm_Zambia_add}} | {{rm_Zambia_fps}} | {{rm_Zambia_inc}} |
| **Total** | **{{rc_tot_att}}** | **{{rc_tot_fatt}}** | **{{rc_tot_rate}}** |  |  | **{{rc_base_add}}** | **{{rc_be}}** | **{{rc_base_k}}** |

[[figure recovery_market]]

{{fig:recovery_market}} shows where the base case sits: Kenya, Tanzania and Uganda hold {{rc_pri_k0}} of it. Tanzania ranks second despite having fewer attempts than Uganda, because each successful Tanzanian card payment earns {{rm_Tanzania_fps}} in fees.

### Scenarios and sensitivities

The target is a judgement, so {{tab:scenarios}} brackets it with a conservative case (each market's own best three-month card rate) and an optimistic case (ten points below mobile money).

::: table scenarios | Recovery scenarios
| Scenario | Target failure rate | Additional successes | Incremental fees, 28 months | Annual run-rate | Share of recorded fees | Share of addressable failed fees |
| --- | --- | --- | --- | --- | --- | --- |
| Conservative | Card's own best 3-month rate | {{rc_con_add}} | {{rc_con_k}} | {{rc_con_ann}} | {{rc_con_sr}} | {{rc_con_sa}} |
| Base | Mobile money's rate, same market | {{rc_base_add}} | {{rc_base_k}} | {{rc_base_ann}} | {{rc_base_sr}} | {{rc_base_sa}} |
| Optimistic | 10 points below mobile money | {{rc_opt_add}} | {{rc_opt_k}} | {{rc_opt_ann}} | {{rc_opt_sr}} | {{rc_opt_sa}} |

[[figure scenarios]]

{{fig:scenarios}} sets the annual run-rates against the annual equivalent of fees actually earned on successful payments: {{succ_annual}} a year, from {{succ_fees_k0}} over 28 months. The base case would add {{rc_base_vs_succ_ann}} to that figure. {{tab:recsens}} tests the base case against other benchmark definitions.

::: table recsens | Base case under alternative benchmarks
| Benchmark | Treatment | Base-case incremental fees, 28 months |
| --- | --- | --- |
| Base | Mobile money failure rate in each market, as observed | {{rc_base_k}} |
| Mobile money without account 47087 | Escalation account removed from the benchmark (Kenya {{rm_Kenya_t}} → {{bx_kenya_mm}}) | {{bx_inc}} |
| Same customers | Mobile money failure among the {{gap_n}} customers using both channels | {{rc_same}} |
| Same customers without account 47087 | As above, {{bx_same_n}} customers | {{bx_same_inc}} |
| Same-month failure offset | Failed attempts reduced by successes in the same customer-month-channel: {{rc_off_n}} attempts ({{rc_off_share}}) removed | {{rc_off}} |

The base case is kept as the central estimate, but the benchmark matters: leaving account 47087 out of it raises the estimate by {{bx_uplift}}, almost all in Kenya ({{bx_kenya_inc}} against {{rm_Kenya_inc}}). The offset test lowers it, without showing that the removed failures were retries. The estimate is robust in direction, and on the observed benchmark it is, if anything, conservative. *[Calculated]*

### Fee revenue is not profit

The dataset has no cost information, so every figure above is fee revenue before processing costs. Break-even is reached when the cost of each additional successful payment equals its fee: {{rc_be}} on average, from {{rc_fps_min}} in Ghana to {{rc_fps_max}} in Tanzania. {{tab:costs}} shows how much base-case fee revenue would remain at illustrative processing-cost ratios, which are scenarios, not observed costs.

::: table costs | Illustrative fee revenue remaining after assumed processing costs
| Processing cost as a share of incremental fees | 0% | 20% | 40% | 60% | 100% |
| --- | --- | --- | --- | --- | --- |
| Base-case fee revenue remaining, 28 months | {{contrib_0}} | {{contrib_20}} | {{contrib_40}} | {{contrib_60}} | {{contrib_100}} |

Even at an assumed 60% processing cost, {{contrib_60}} of base-case fee revenue would remain over the period. Other incremental operating costs are not included. The opportunity is worth pursuing, provided each market's improvement is costed before spending.

## 8. Management recommendations

The two problems need different responses. The account-level anomalies are a monitoring problem: contain them. Card completion in Kenya, Tanzania and Uganda is the improvement opportunity. Ranking cells by failure rate alone would point to the wrong places. Uganda alternative channels, for example, fails {{mx_ua_fr}} of the time but holds only {{mx_ua_ff}}.

### Failure-to-Revenue Prioritisation Matrix

The matrix sets transparent criteria side by side rather than combining them into a weighted score, because no weighting could be justified from the data. It shows two improvement potentials:

- **Internal potential:** what a cell would recover by reaching its own best three-month failure rate. This is improvement the cell has already achieved once.
- **Cross-channel potential:** for card cells, what the cell would recover at mobile money's rate in the same market, in every currency. This is why Kenya's figure ({{mx_kc_cp}}) exceeds the USD-only {{rm_Kenya_inc}} in Section 7.

It also separates **data confidence**, which reflects how complete the cell's data is, from **diagnostic confidence**, which reflects how strongly the pattern supports the explanation. Diagnostic confidence is low when one customer holds most of a cell's failed fees.

[[figure matrix]]

{{fig:matrix}} plots each cell by exposure and failure rate, with bubble size showing internal potential. The three card cells in the upper right are the priorities. {{tab:matrix}} gives the full criteria for the cells that matter.

::: table matrix | Failure-to-Revenue Prioritisation Matrix
| Cell | Failure rate | Fees on failed transactions | Failed value | Internal potential | Cross-channel potential | Persistence | Data confidence | Diagnostic confidence | Action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Kenya card | {{dr_kc_fr}} | {{dr_kc_ff}} | {{mx_kc_fv}} | {{mx_kc_ip}} | {{mx_kc_cp}} | Structural, episodic | High | High | Prioritise |
| Uganda card | {{dr_uc_fr}} | {{dr_uc_ff}} | {{mx_uc_fv}} | {{mx_uc_ip}} | {{mx_uc_cp}} | Structural, episodic | High | High | Prioritise |
| Tanzania card | {{dr_tc_fr}} | {{dr_tc_ff}} | {{mx_tc_fv}} | {{mx_tc_ip}} | {{mx_tc_cp}} | Structural | Medium | Medium | Prioritise |
| Kenya mobile money | {{dr_km_fr}} | {{dr_km_ff}} | {{mx_km_fv}} | {{mx_km_ip}} | — | Deteriorating, episodic | High | Low: {{mx_km_top}} one account | Contain account 47087 |
| Ghana card | {{dr_gc_fr}} | {{dr_gc_ff}} | {{mx_gc_fv}} | {{mx_gc_ip}} | {{mx_gc_cp}} | Structural, deteriorating | High | High | Investigate root cause |
| Uganda mobile money | {{dr_um_fr}} | {{dr_um_ff}} | {{mx_um_fv}} | {{mx_um_ip}} | — | Episodic (weak signals) | High | Low: {{mx_um_top}} one customer | Monitor |
| Zambia card | {{mx_zc_fr}} | {{mx_zc_ff}} | {{mx_zc_fv}} | {{mx_zc_ip}} | {{mx_zc_cp}} | Too little data | Low | Medium | Monitor |

Ghana card shows why both potentials matter. It has never had a good quarter, so its internal potential is small ({{mx_gc_ip}}), yet its gap to mobile money is large ({{mx_gc_cp}}). That combination calls for diagnosing acceptance or routing before committing spend.

### Actions, owners and measures

{{tab:actions}} turns the matrix into five actions, each with a measure and a baseline to track it against. Owners are to be assigned by the team.

::: table actions | Actions, measures and baselines
| Priority | Intervention | Measure | Baseline |
| --- | --- | --- | --- |
| 1. Anomaly containment | Account alerts on sudden spikes and sustained escalation; throttle and review | Extreme failed-attempt observations a month | 20 observations and {{anom_m}} over 28 months |
| 2. USD card completion | Investigate merchant-months with zero card successes, then routing, acceptance and currency set-up in Kenya, Tanzania and Uganda | USD card count failure rate by market | Kenya {{rm_Kenya_r}}, Tanzania {{rm_Tanzania_r}}, Uganda {{rm_Uganda_r}} |
| 3. Persistent customers | Review the {{pers_n}} accounts with recurring elevated failure | Persistent-customer failed fees | {{pers_m}} ({{pers_ffee}} of non-anomalous failed fees) |
| 4. High-value mobile money | Investigate the top-quintile result; do not change limits yet | Top-quintile mobile money failure rate | {{qa_m5}} ({{q3_m5}} after exclusions) |
| 5. Financial monitoring | Report the three core measures monthly, with successful fees at constant currency | Monthly financial performance | {{se_cr}} count failure, {{rm_fs}} failed-fee share (excluding anomalies) |

Each intervention should be measured against its own baseline. For Kenya card, for example: track the current failure rate against {{rm_Kenya_r}}, convert the improvement into additional successful payments (attempts × the fall in the failure rate), value them at {{rm_Kenya_fps}} each, and check on the cell's control chart that the gain persists.

### Monitoring triggers

{{tab:triggers}} sets out the triggers that would turn this analysis into a standing monitoring framework.

::: table triggers | Monitoring triggers
| Indicator | Definition | Trigger |
| --- | --- | --- |
| Account anomaly alert, relative | Failed attempts ≥ 1,000, more than 50× the 6-month median, success under 5% | Same month: throttle, then review |
| Account anomaly alert, absolute | Failed attempts ≥ 5,000 in a month with success under 5%, or failed attempts doubling 3 months running | Same month; would have caught account 47087 in January 2024 |
| Card cell control chart | Laney p′ chart for each market's card cell | A month above the limit, unless one customer holds more than half of it |
| Core failure measures | Count failure rate, failed-fee share, successful-transaction fees | Monthly, side by side |
| Constant-currency revenue | Successful-transaction fees at 2022 rates | Monthly, alongside reported US dollars |
| Rate-data checks | Daily high–low range above 10%; any day more than 5× the monthly median; any scale break | Disclose; investigate breaks such as the SLL redenomination |

### Conclusion

The {{failed_fees_m}} headline overstates the structural problem and understates how concentrated the risk is. About {{anom_share}} of it comes from {{an_accounts}} accounts that need detecting and containing. The remaining {{rm_m}} is steady and spans every channel; card carries {{rm_card_share}} of it, and USD card completion is the clearest improvement opportunity. Closing part of the gap to mobile money in Kenya, Tanzania and Uganda is the clearest route to more earned revenue. Reporting at constant currency would show whether that revenue is really growing.

## Appendix A. Data and methodology

This appendix documents how the data was prepared. The brief's figures reproduce exactly from the data as supplied. One error in the supplied exchange rates is corrected, and every other apparent discrepancy is a difference of measure, not an error.

### Two analytical populations

[[figure flow]]

{{fig:flow}} shows how the records flow into the two populations used throughout, and {{tab:populations}} gives the counts.

::: table populations | Analytical populations
| Population | Records | Attempts | Used for |
| --- | --- | --- | --- |
| All records | {{records}} | {{attempts}} | Every count measure: failure rates, attempts, persistence, control charts |
| Translatable records | {{records_tr}} | {{attempts_tr}} | Every dollar measure: fees, values, yields, recovery |

The {{untr_records}} records outside the second population are in 30 currencies with no exchange rate in the supplied data, and hold {{untr_att}} attempts.

### Reconciliation with the challenge brief

{{tab:brief}} sets the brief's figures beside the recalculated ones.

::: table brief | Reconciliation with the challenge brief
| Measure | Brief | Recalculated | Population | Status |
| --- | --- | --- | --- | --- |
| Transaction attempts | 1.65M | {{attempts}} | All records | Reconciles |
| Failed attempts | 1.02M (62%) | {{failed}} ({{count_rate}}) | All records | Reconciles |
| Recorded fee revenue | $3.15M | {{fees_d}} ($3,148,908 before the SLL correction) | Translatable | Brief includes the SLL error |
| Fees on failed transactions | $2.85M (90%) | {{failed_fees_d}} ({{fee_share}}); $2,842,692 before the correction | Translatable | Brief includes the SLL error |
| January 2024 "failure rate" | 97% | 79.8% by count; 97.3% failed-fee share | Both | Brief reports the failed-fee share |
| Months below 78% | None | Failed-fee share: 2 (Oct 2023 77.9%, Nov 2023 77.6%); none before the correction | Translatable | Holds only before the correction |
| January 2024 failed fees | Over $745K | {{jan_d}} ($744,744 before the correction) | Translatable | Overstated |
| Card / mobile money / bank transfer failed-fee share | 94% / 77% / 3% | {{card_fs}} / {{mm_fs}} / {{bank_fs}} | Translatable | Reconciles |
| Bank transfer share of volume | 2% | {{bank_att_share}} of attempts; 1.6% of records | All records | Brief counts records |
| Kenya failed-fee share | 93% | {{kenya_fs}} | Translatable | Reconciles |

Most differences come from the SLL correction or from the brief using a different measure. Fees on failed transactions are not treated as earned revenue anywhere in this report, because their recognition and collection cannot be established from the data.

### Data-quality flags

Data problems were flagged independently, so that one kind of problem never excludes data affected by another. {{tab:flags}} lists the three flags.

::: table flags | Independent data-quality flags
| Flag | Rule | Records | Treatment |
| --- | --- | --- | --- |
| Fee-ratio anomaly | Fee below 0.5% or above 20% of transaction value | {{flag_fee_ratio}}, including {{fee_exceeds_value}} where the fee exceeds the value | Kept in fee measures; reviewed |
| Missing fee | No fee recorded | 39 | Zero in fee sums; kept in counts |
| Transaction-value anomaly | Value above $10,000 per attempt (about the 99.9th percentile), or zero or negative | 64, holding {{flag_value_bn}} of {{value_total_bn}} reported value | Excluded from value measures only |

The largest value anomaly is a failed NGN record of 2.36 trillion across 24 attempts with a fee of NGN 314: the fee is plausible, the value is not. By contrast, the recurring UGX 500 million records of customer 1039721 are valid monthly aggregates of 3,000–4,300 attempts at a consistent 3.0% fee, and are kept.

### Exchange-rate corrections

- **Sierra Leone redenomination.** On 1 July 2022 Sierra Leone moved to the new leone at 1 SLE = 1,000 SLL. The supplied SLL rate series switches to the new scale from that date, while the transactions stay at old-leone amounts. Translating them at the new rate overstates their fees 1,000-fold. Post-switch SLL rates are divided by 1,000, which removes $63.3K from fees on failed transactions.
- **Rate spikes.** {{spike_days}} single-day rates more than five times away from their monthly median (MOP, MXN, THB, VEF), and two zero-rate TZS days, were dropped before averaging.
- **Legacy codes.** GHC and ZMK amounts were checked against GHS and ZMW medians and are at new-unit scale, so they are mapped to GHS and ZMW. XAF/CFA and CFA are mapped to XAF.

### Translation and preparation rules

- **Rate convention:** US dollars per unit of currency, so a dollar amount is the local amount multiplied by the rate.
- **Reported basis:** the monthly average of daily rates (Section 6). Month-end rates are a sensitivity only, because closing rates relate mainly to monetary balances at reporting dates.
- **Constant currency:** each currency's 2022 average rate, applied record by record, so that a shift in currency mix is not mistaken for a rate effect.
- **Failure:** any status other than successful; the data has only two statuses.
- **Country:** taken from the merchant's customer record, not from the currency.
- **Customer table:** for {{stale}} of {{customers}} transacting customers ({{stale_share}}), the table's last transaction date precedes their last observed transaction, so lapse is measured from the transactions.
- **Unit of analysis:** customer × month × payment type. The data cannot show transaction sequence or time of month.

## Appendix B. Sensitivity, validation and limitations

This appendix tests whether the headline depends on the choices made in Appendix A, and states what the data cannot show.

### Headline sensitivity

{{tab:sensitivity}} recomputes the three headline measures under each alternative treatment. The report basis keeps the 64 value-anomaly records in every fee measure and excludes them only from value measures; the third row shows the alternative of excluding them, and untranslatable records, from fees as well.

::: table sensitivity | Headline measures under alternative treatments
| Treatment | Fees on failed transactions | Failed-fee share | Count failure rate |
| --- | --- | --- | --- |
| Report basis (SLL corrected, monthly-average rates) | {{failed_fees_k}} | {{fee_share}} | {{count_rate}} |
| Before the SLL correction (as in the brief) | $2,842.7K | 90.3% | {{count_rate}} |
| Alternative: value-anomaly and untranslatable records also excluded from fees | {{sv_ff}} | {{sv_fs}} | {{sv_cr}} |
| Month-end rates in volatile months | {{sm_ff}} | {{sm_fs}} | {{sm_cr}} |
| 2022 constant currency | {{sc_ff}} | {{sc_fs}} | {{sc_cr}} |
| Excluding extreme-volume anomalies | {{sx_ff}} | {{sx_fs}} | {{sx_cr}} |
| Also excluding account 47087 | {{se_ff}} | {{se_fs}} | {{se_cr}} |

The failed-fee share holds at 89–90% under every data and translation choice. Only removing the anomaly categories moves it, and then to 85%. The headline is robust; what changes the story is separating the anomalies, which is why the report is built around that split.

### Limitations

- **No failure codes, provider identifiers or logs.** "Extreme-volume anomaly", "escalation", "hard" and "mixed" are proxies; causes are hypotheses.
- **Monthly aggregation.** There is no transaction sequence, time of month or individual ticket size. Size quintiles describe aggregated records.
- **No settlement, collection or cost data.** Cash collected, realised exchange differences and contribution cannot be measured. Recovery is fee revenue before costs.
- **Benchmark transferability.** The same-customer comparison is descriptive; it does not show that mobile money's performance can be achieved on card.
- **Short series.** The control charts rest on 28 monthly points, with no test of seasonality or of independence between months. Tanzania card has only 12 eligible months and Zambia card {{lp_exc_top_n}}, below the 12 needed, so Zambia card is not pattern-classified; the excluded cells hold {{lp_exc_share}} of failed fees.
- **Rate data.** Other undetected rate errors would move dollar measures, though not count measures.

### Reproducibility

Every number, table and figure in this report comes from one pipeline run over the supplied workbook. The rules sit in a single assumptions file. The dashboard draws the same figures from the same code and recomputes them for any selection, and an Excel workbook rebuilds the main calculations in live formulas. The source code, data and outputs are listed on the cover.
