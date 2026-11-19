# Audit report

15 checks: **15 pass**, **0 fail**, **0 flagged for the author**. A FLAG is a finding that needs a decision; nothing was changed because of it.

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

## B. Baseline

| Result | Check | Detail |
| --- | --- | --- |
| PASS | results.json matches the baseline (ints exact, floats to 1e-9) | 12 blocks identical |
| PASS | Every baseline table (CSV) matches | 38 tables identical |
| PASS | Every rendered report value matches the baseline (exact text) | 569 values identical; 13 new |
