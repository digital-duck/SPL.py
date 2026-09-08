# SPL Run: data_quality

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 391 in / 368 out
- **Latency:** 14868ms
- **Timestamp:** 2026-09-06 18:43:14

## Output

```output
=== Data Quality Validator (r103) | solver=ON ===

## Data Quality Report — SalesTransactions_v1

**Dataset:** 500 rows  
**Expectations:** 10 total  
**Passed:** 6  
**Failed:** 4  
**Status:** ✗ FAIL

| Expectation | Column | Status | Failures |
|---|---|---|---|
| expect_column_to_exist | transaction_id | PASS | |
| expect_column_to_exist | amount | PASS | |
| expect_column_to_exist | customer_id | PASS | |
| expect_column_to_exist | region | PASS | |
| expect_column_values_to_be_unique | transaction_id | FAIL (4 rows, 0.8%) | |
| expect_column_values_to_not_be_null | transaction_id | PASS | |
| expect_column_values_to_not_be_null | customer_id | FAIL (8 rows, 1.6%) | |
| expect_column_values_to_not_be_null | amount | PASS | |
| expect_column_values_to_be_between | amount | FAIL (12 rows, 2.4%) samples=[-234.82, -479.91, -328.99] | |
| expect_column_values_to_be_in_set | region | FAIL (3 rows, 0.6%) values=['Unknown'] | |

── Business Explanation ────────────────────────────────────
## Data Quality Summary

**Four issues found:**

**1. Duplicate transaction IDs (4 rows, 0.8%)** — Four transactions share IDs that should be unique. Likely caused by POS system retries on failed network submissions, creating double-records for the same sale.

**2. Missing customer IDs (8 rows, 1.6%)** — Eight transactions have no customer linked. Probable cause: guest checkouts or a POS terminal that allows bypassing the customer lookup step.

**3. Negative amounts (12 rows, 2.4%)** — Samples like -$479 suggest these are refunds or chargebacks encoded as negative values rather than as a separate transaction type. May also indicate a data entry error.

**4. Unknown region (3 rows, 0.6%)** — Three rows carry `'Unknown'` instead of a valid region code, pointing to a misconfigured or new POS terminal that hasn't been assigned a region.

---

**Most urgent: duplicate transaction IDs.** A broken primary key corrupts every join, aggregate, and reconciliation downstream — revenue totals will be double-counted and audit trails will be unreliable. Fix this before any analysis runs.

**Downstream impact if uncorrected:**
- Duplicates → inflated revenue figures, broken order tracking
- Missing customer IDs → incomplete customer lifetime value and segmentation models
- Negative amounts → distorted average order value and revenue totals unless refunds are explicitly filtered
- Unknown region → regional performance reports will undercount one or more territories
```
