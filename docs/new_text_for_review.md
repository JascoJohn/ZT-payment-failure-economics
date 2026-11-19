# New text for review (items 19–24). Nothing below is in `report/content/` yet.

Every number is a `{{token}}`; the rendered value follows in brackets. All values are computed by the pipeline now (they are in
`outputs/results.json` and the 01E/04/07 tables). Tell me which pieces to apply, or edit them here.

---

## 19. Appendix A.5, new paragraph (after "Translation and preparation rules" bullet list) and a limitation

**What "failed" means.** The data has two statuses: failed ({{rec_failed}} records [39,570]) and successful ({{rec_success}} records [23,114]).
Declined, abandoned, pending and test attempts cannot be separated from other failures, so every attempt that is not successful counts as failed
throughout this report. Failure rates and fees on failed transactions therefore include attempts that may have been correct rejections or were never
meant to complete.

Limitations, new bullet (after "No failure codes, provider identifiers or logs"):

- **What counts as failed.** Every non-success is counted as failed ({{rec_failed}} records against {{rec_success}} successful). Declined, abandoned, pending and
  test attempts cannot be told apart, so failure rates and fees on failed transactions may include rejections that were correct.

The existing bullet "**Failure:** any status other than successful; the data has only two statuses." in A.5 stays; the new paragraph expands it.

---

## 20. Section 7.3, Table 15 gains a sixth row, and one sentence below the table

| Benchmark | Treatment | Base-case incremental fees, {{nm}} months |
| --- | --- | --- |
| USD card without zero-success customer-months | USD card customer-months with no card success are left out ({{rc_nr_share}} [33%] of USD card failed attempts, {{rc_nr_n}} [3,959] customer-months), because some may be correct rejections, including card testing. Extreme-volume anomalies are already excluded. | {{rc_nr_k}} [$158.8K] |

Sentence added to the paragraph below the table, after "The offset test lowers it, without showing that the removed failures were retries.":

> Leaving out the zero-success customer-months, on the grounds that some may be correct rejections, lowers it further, to {{rc_nr_k}}; extreme-volume anomalies are already excluded from every row.

---

## 21. Section 7.3, resampling interval (new paragraph after the paragraph below Table 15), and a limitation

> **How much does the estimate depend on which customers are in the data?** Customers were resampled with replacement within each market,
> for USD card and mobile money together, {{rc_ci_reps}} [1,000] times with a fixed seed (2026; set in `config/assumptions.yaml`), and the base case recomputed each time, fee
> per successful payment included. The {{rc_ci_level}} [90%] interval is {{rc_ci_lo}} [$140K] to {{rc_ci_hi}} [$418K] around the {{rc_base_k0}} [$254K] base case, with a median of {{rc_ci_med}} [$266K]. The
> interval is wide for two reasons the data can show: fees per successful payment are concentrated in a few customers (in Tanzania, three of 127 USD card customers earn 75%
> of successful-transaction fees, at {{rm_Tanzania_fps}} [$20.79] a payment against {{rm_Uganda_fps}} [$4.63] in Uganda), and Kenya's mobile money rate is moved by account 47087.
> The interval reflects sampling variation in customers only; it says nothing about whether mobile money's failure rate can be reached on card.

Limitations, new bullet:

- **Sampling uncertainty.** The base case is one draw of customers. Resampling customers within each market gives a {{rc_ci_level}} interval of {{rc_ci_lo}} to {{rc_ci_hi}}, wide because
  fees per successful payment and the Kenya mobile money rate depend on a few accounts.

**Two things to know before you approve this.**
1. With the fixed seed 2026 the interval is **$140K–$418K, median $266K**. Your expected "about $145K–$437K, median about $262K" is within the spread
   between seeds (seed 1 gives $146K–$439K, median $257K; seed 20260 gives $142K–$456K, median $261K), but it is not what this seed returns. I have not tuned the seed to match.
   Tell me if you want a different seed or more replicates (5,000 would settle the third digit).
2. The data support "a few customers" but not "a few high-fee Tanzanian customers" alone: holding Tanzania's customers fixed narrows the spread of the replicates by 17%, holding
   Kenya's fixed narrows it by 39%. The paragraph above says Tanzania and Kenya, with the facts that hold.

---

## 22. Section 7.3, replacement for "The estimate is robust in direction, and on the observed benchmark it is, if anything, conservative."

> The estimate is robust in direction. The base case of {{rc_base_k0}} [$254K] sits within a range of about {{rc_rng_lo}} [$159K]–{{rc_rng_hi}} [$324K] across benchmark and exclusion choices,
> with a {{rc_ci_level}} [90%] customer-resampling interval of about {{rc_ci_lo}} [$140K]–{{rc_ci_hi}} [$418K].

(The range's low end is the zero-success customer-months row, its high end the benchmark without account 47087. Same wording is proposed for the executive summary and the brief where they
say the estimate is conservative; neither says so today, so nothing changes there.)

---

## 23. Section 4.4, the lapse paragraph, rewritten; subheading and figure label renamed

Subheading: "Persistent customers, tenure and lapse" → **"Persistent customers, tenure and later inactivity"**. Figure D5 subplot title "End-period lapse rate" → **"No activity in Feb–Apr 2024"**.

Paragraph (replaces the sentences from "Failure is, however, associated with leaving." to the end):

> Failure is, however, associated with later inactivity. {{lapsed}} [4,328] of the {{active_before}} [5,451] customers active before February 2024 ({{lapse_rate}} [79%]) had no activity in February–April
> 2024. A three-month window cannot separate churn from irregular activity: {{lapse_few_pct}} [46%] of these customers were active in only one or two months over the whole period, and
> {{lapse_gap3_pct}} [33%] had earlier gaps of three months or more. Before February, these customers had failed more than the others: {{lapse_cr_l}} [59.7%] against {{lapse_cr_r}} [51.6%] by count.
> Among customers with six or more active months, {{lapse_p}} [59%] of persistent customers had no activity in February–April 2024 against {{lapse_o}} [51%] of the rest. This is consistent with
> failure contributing to attrition, but it does not prove it. *[Observed association; causation is a hypothesis]*

Limitations, new bullet:

- **Inactivity is not churn.** "No activity in February–April 2024" is measured over three months at the end of the data; it cannot separate churn from irregular activity (see Section 4.4).

---

## 24. New subsection after 8.2: "A 90-day pilot" (becomes 8.3; Monitoring triggers becomes 8.4, Conclusion 8.5)

> ### A 90-day pilot
>
> {{tab:pilot}} sets out a pilot that tests the recommendations before any market-wide spending. Costs are unknown, so the break-even of {{rc_be}} [$7.54] of cost per additional
> successful payment (Section 7.4) is used as the ceiling: stop an action whose cost per additional successful payment exceeds it. Each card target is the market's own best three-month USD card
> failure rate, which the market has already reached once. Ghana and Zambia, where no card fix is tried, and each market's own pre-pilot months are the comparisons, and the control charts (Section 4.5)
> confirm that any gain lasts. Owner names and dates are for the team to assign; the roles and timeline are suggestions.

Table (caption "90-day pilot: actions, suggested owners, targets and decision rules"):

| Action | Suggested owner role | Timeline | Target | Measure | Decision rule |
| --- | --- | --- | --- | --- | --- |
| 1. Contain extreme-volume anomalies and the escalation account (47087) | Risk / fraud operations | Alerts live by day 14; weekly review to day 90 | Every account that meets the relative or absolute alert is throttled and reviewed in the month it appears | Observations meeting either alert a month; accounts reviewed in the month | Keep the alerts if every flagged account was reviewed in its month; widen or narrow the thresholds only after reading the flagged accounts |
| 2. Kenya USD card completion | Payments operations | Days 1–14 diagnose zero-success merchant-months ({{rc_nr_n}} [3,959] customer-months across the three markets); days 15–75 fix acceptance, routing and currency set-up; days 76–90 evaluate | USD card count failure rate {{pl_Kenya_to}} [82.9%], from {{pl_Kenya_from}} [89.0%] | USD card count failure rate excluding extreme-volume anomalies, monthly, against Ghana and Zambia and the pre-pilot months; cost per additional successful payment | Extend to Ghana and Zambia if the rate reaches the target for the last month, no month sits above the control limit, and cost per additional successful payment is below {{rc_be}} [$7.54]; stop if the cost exceeds it |
| 3. Tanzania USD card completion | Payments operations | As action 2 | {{pl_Tanzania_to}} [70.5%], from {{pl_Tanzania_from}} [85.9%] | As action 2 | As action 2 |
| 4. Uganda USD card completion | Payments operations | As action 2 | {{pl_Uganda_to}} [64.9%], from {{pl_Uganda_from}} [77.6%] | As action 2 | As action 2 |
| 5. Persistent customers | Account management | Days 1–30 review the {{pers_n}} accounts with recurring elevated failure; days 31–90 follow up | Every persistent account contacted and its main failure pattern recorded | Persistent-customer fees on failed transactions ({{pers_m}} [baseline]) a month | Keep the review if persistent-customer fees fall against the comparison; otherwise reassign |
| 6. Monthly financial reporting | Finance | From month 1 | The three core measures reported monthly, with successful-transaction fees at constant currency | Count failure rate, failed-fee share, successful-transaction fees at constant currency | Continue as the standing report; add cost per additional successful payment once costs are known |

(Numbers in brackets are the rendered values; they are not part of the text. Row 5's baseline is the existing Actions table baseline. The table's owner roles are the four you named.)

---

### What applying this would change in the report

- Tables: Table 15 gets a sixth row; a new table is added (Table 21 or later, renumbering the appendix tables that follow it).
- New tokens used (all already defined in `report.context`): `rec_failed`, `rec_success`, `rc_nr_k`, `rc_nr_share`, `rc_nr_n`, `rc_ci_lo`, `rc_ci_med`, `rc_ci_hi`, `rc_ci_level`,
  `rc_ci_reps`, `rc_rng_lo`, `rc_rng_hi`, `lapse_few_pct`, `lapse_gap3_pct`, `pl_<market>_from`, `pl_<market>_to`.
- The Excel workbook gets the same sixth row in its Table 15 and the interval beside it; the Word copy and the lists of tables follow automatically.
