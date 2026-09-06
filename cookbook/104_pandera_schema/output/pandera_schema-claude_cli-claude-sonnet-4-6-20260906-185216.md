# SPL Run: pandera_schema

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 279 in / 1197 out
- **Latency:** 57711ms
- **Timestamp:** 2026-09-06 18:52:16

## Output

```output
=== pandera Schema Validator (r104) | solver=OFF ===

── LLM Schema Analysis ─────────────────────────────────────
## 1. Columns Most Likely to Have Quality Issues

**`department`** — highest risk. Categorical fields from HR system exports routinely carry legacy names ("IT", "Marketing"), inconsistent casing ("engineering", "SALES"), abbreviations ("Ops"), or transfer artifacts where the old department wasn't cleared before the new one was written. A five-value enum is a tight constraint that any schema drift will violate.

**`salary`** — high risk for two distinct failure modes: (a) data entry errors — an extra zero turns $85,000 into $850,000; (b) onboarding stubs — new hires sometimes land with salary = 0 before payroll is configured. Also vulnerable to CSV formatting issues (commas in numbers misparse as column delimiters).

**`hire_year`** — moderate risk. The lower bound (2000) silently excludes tenured employees hired before that year, which is plausible if the company is older than 26 years. The upper bound (2026) is the current year, so pre-entered future hires would violate it by end-of-year. NULL hire dates are common for contractors converted to FTEs with unclear start dates.

**`employee_id`** — lower frequency but high severity. Duplicates appear during org merges or when an employee has two concurrent part-time records. Legacy systems sometimes issued IDs below 1000 for contractors. Violations here are dangerous because downstream joins silently fan out.

**`name`** — lowest risk for nulls, but real encoding issues exist (accented characters, apostrophes) that can corrupt string operations without failing a "not null" check.

---

## 2. Records That PASS

| employee_id | name | department | salary | hire_year |
|---|---|---|---|---|
| 1042 | Alice Chen | Engineering | 95000.00 | 2018 |
| 2387 | Marcus Johnson | Sales | 72500.50 | 2015 |
| 1999 | Sarah O'Brien | HR | 61000.00 | 2022 |

All three satisfy: ID ≥ 1000, non-null name, valid department, 0 < salary < 500000, 2000 ≤ hire_year ≤ 2026.

---

## 3. Records That FAIL

**Fail 1 — invalid department**

| employee_id | name | department | salary | hire_year |
|---|---|---|---|---|
| 1105 | Tom Rivera | **Marketing** | 88000.00 | 2019 |

Violation: `"Marketing"` is not in `[Engineering, Sales, HR, Finance, Operations]`. Likely a renamed or legacy department that was never mapped to the canonical list.

---

**Fail 2 — salary out of range (onboarding stub)**

| employee_id | name | department | salary | hire_year |
|---|---|---|---|---|
| 1230 | Janet Wu | Finance | **0.00** | 2024 |

Violation: `salary = 0.00` fails `> 0`. Classic pattern when payroll is configured after the HR record is created.

---

**Fail 3 — two simultaneous violations: employee_id below floor and hire_year below floor**

| employee_id | name | department | salary | hire_year |
|---|---|---|---|---|
| **847** | Robert Kim | Operations | 54000.00 | **1997** |

Violations: `employee_id = 847 < 1000`; `hire_year = 1997 < 2000`. Consistent with a legacy employee migrated from an older HR system that issued IDs in the hundreds and predates the schema's intended history window.

---

## 4. Downstream Breakage by Violation Type

**Invalid department**
Any GROUP BY department aggregation (headcount per dept, average salary by dept, budget allocation) silently includes an unknown category. If downstream code maps departments to cost center codes via a lookup dictionary, unmapped values either raise a KeyError or silently produce nulls — understating departmental headcount in every report. Org-chart visualizations show a phantom node.

**Salary = 0 or salary > $500K**
- Zero salary: payroll totals and average compensation metrics are understated. Annualized cost projections (used for headcount budgeting) will be wrong for that employee's department.
- Salary > $500K (e.g., a miskeyed extra zero): skews mean salary heavily upward, distorts compensation band analysis, and may trigger false-positive outlier alerts in audit systems. If the record feeds a compensation benchmarking model, it corrupts the training distribution.

**hire_year out of range**
Tenure calculations (`current_year - hire_year`) produce negative values (future hires) or inflated values (pre-2000 hires). This breaks: seniority-based PTO accrual rules, retirement eligibility checks (vesting schedules keyed to years of service), and cohort attrition analysis where employees would be bucketed into the wrong hiring cohort or no cohort at all.

**employee_id not unique or < 1000**
Joins to other tables (performance reviews, benefits enrollment, badge access logs) produce cartesian products on duplicate IDs — one employee's salary suddenly appears twice in payroll totals. Non-unique IDs also break any upsert logic that uses `employee_id` as the merge key, causing updates intended for one record to silently overwrite another.

Note: LLM describes expected violations. Run --param use_solver=true
to validate all rows with pandera.
```
