# SPL Run: pandera_schema

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 232 in / 216 out
- **Latency:** 12886ms
- **Timestamp:** 2026-09-06 19:02:01

## Output

```output
=== pandera Schema Validator (r104) | solver=ON ===

## pandera Schema Report — EmployeePayroll_v1

**Dataset:** 200 rows  
**Status:** ✗ FAIL  
**Violations:** 3 column checks failed

| Column | Check | Failures | Sample Values |
|---|---|---|---|
| department | isin(['Engineering', 'Sales', 'HR', 'Finance', 'Operations']) | 4 | ['Temp', 'Temp', 'Temp'] |
| name | not_nullable | 3 | ['(null)', '(null)', '(null)'] |
| salary | greater_than(0) | 6 | [0.0, 0.0, 0.0] |

── Business Explanation ────────────────────────────────────
**Violations found:**

1. **Department (4 rows):** Values "Temp" aren't in the approved department list — likely contractors or temporary workers loaded without proper department mapping.
2. **Name (3 rows):** Null employee names — probable upstream ETL failure where source records had missing fields that weren't caught before ingestion.
3. **Salary (6 rows):** Zero-dollar salaries — likely placeholder rows for new hires not yet processed through payroll, or a default-fill bug replacing NULLs with 0.

**Highest priority:** Salary zeros. Zero pay means employees may go unpaid — direct financial and legal exposure.

**Pipeline fix:** Add a pre-ingestion validation gate (pandera or Great Expectations) that rejects or quarantines records failing these checks before they reach the payroll table, enforcing referential integrity at load time rather than after.
```
