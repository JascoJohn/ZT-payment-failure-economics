# Fee per failed attempt: before and after (item 5)

**Before:** fees on failed transactions (translatable records) ÷ failed attempts of *all* records, so attempts of the 221 records without an exchange rate sat in the denominator with no fee.
**After:** fees ÷ failed attempts, both on translatable records only. Drivers table (Table 3), non-anomalous records.

| Cell | Failed attempts, all records | Failed attempts, translatable | Before | After | Change | Printed before → after |
| --- | --- | --- | --- | --- | --- | --- |
| Kenya card | 122,580 | 122,164 | $5.4207 | $5.4391 | +0.34% | $5.42 → $5.44 |
| Kenya mobilemoney | 259,186 | 259,186 | $1.1172 | $1.1172 | +0.00% | $1.12 → $1.12 (unchanged) |
| Uganda card | 45,572 | 45,533 | $6.2624 | $6.2677 | +0.09% | $6.26 → $6.27 |
| Tanzania card | 12,416 | 12,412 | $18.8609 | $18.8670 | +0.03% | $18.86 → $18.87 |
| Ghana card | 22,920 | 22,908 | $8.0565 | $8.0607 | +0.05% | $8.06 → $8.06 (unchanged) |
| Uganda mobilemoney | 247,049 | 247,049 | $0.5743 | $0.5743 | +0.00% | $0.57 → $0.57 (unchanged) |
| All cells | 867,132 | 866,595 | $2.2528 | $2.2542 | +0.06% | $2.25 → $2.25 |
| Bank transfer (Section 3.1) | 694 | – | $0.2631 | $0.2631 | +0.00% | $0.26 → $0.26 |

## Derived statements

- Tanzania card yield against the all-cells average: before 8.37× → after 8.37× (printed "8×" both ways).
- Tanzania card fee per failed attempt against Kenya card: before 3.479 → after 3.469 (printed "three and a half times" both ways).

## Rendered values that change (baseline → now)

| Token | Baseline | Now |
| --- | --- | --- |
| `dr_kc_fpf` (Table 3, Kenya card) | $5.42 | $5.44 |
| `dr_uc_fpf` (Table 3, Uganda card) | $6.26 | $6.27 |
| `dr_tc_fpf` (Table 3, Tanzania card) | $18.86 | $18.87 |

Every other rendered value, including `dr_km_fpf`, `dr_gc_fpf`, `dr_um_fpf`, `dr_all_fpf` and `bank_fpf`, is unchanged at two decimals.

The Excel workbook's driver table uses the same definition (both numerator and denominator on records with an exchange rate) and ties to the Python values on `99_Checks`.
