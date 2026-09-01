# Recipe 104 — pandera Schema Validator

**The key story:** A 200-row employee payroll CSV has 6 rows with `salary=0` (data entry error) and 4 rows with `department="Temp"` (non-standard value). pandera validates all 200 rows against a typed schema in <0.1s and returns exact violation counts. LLM inspects a sample and misses both issues.

## What it demonstrates

| Axis | solver=ON | solver=OFF |
|---|---|---|
| Engine | pandera DataFrameSchema | LLM schema reasoning from description |
| Coverage | All 200 rows, all columns | Sample-based, no row-level counts |
| Contract | Typed columns, range checks, categoricals, uniqueness | "Should be positive salary, standard departments" |
| Verification | `ASSERT schema_passes` (C1) | — |
| Solver class | C1 (categorical: PASS / FAIL per column check) | — |

## Default schema (EmployeePayroll_v1)

| Column | Type | Checks |
|---|---|---|
| employee_id | int64 | unique, not null, > 999 |
| name | object | not null |
| department | object | isin [Engineering, Sales, HR, Finance, Operations] |
| salary | float64 | not null, > 0, < 500,000 |
| hire_year | int64 | not null, 2000 ≤ x ≤ 2026 |

## Injected violations (demo dataset)

| Violation | Rows | Check Failed |
|---|---|---|
| `salary = 0.0` | 6 | `salary > 0` |
| `department = "Temp"` | 4 | `isin [Engineering, Sales, HR, Finance, Operations]` |
| `name = None` | 3 | `name not null` |

## Run commands

```bash
# solver=ON — pandera validates all 200 rows
spl3 run cookbook/104_pandera_schema/pandera_schema.spl \
    --adapter claude_cli --param use_solver=true

# solver=OFF — LLM reasons from schema description
spl3 run cookbook/104_pandera_schema/pandera_schema.spl \
    --adapter ollama -m gemma3 --param use_solver=false

# Validate your own CSV
spl3 run cookbook/104_pandera_schema/pandera_schema.spl \
    --adapter claude_cli --param use_solver=true \
    --param "data_csv=$(cat employees.csv)"
```

## Install

```bash
conda activate spl123
pip install pandera
```

## TOOL_API reference

| Function | Purpose |
|---|---|
| `get_default_schema()` | Returns EmployeePayroll_v1 schema JSON |
| `validate_schema(schema_json, data_csv)` | pandera validation; "demo" generates synthetic data |
| `schema_passes(result_json)` | ASSERT gate: `status == "PASS"` |
| `format_schema_report(result_json)` | Markdown table of violations with sample values |

## pandera vs Great Expectations (r103)

| | r103 (GE-style) | r104 (pandera) |
|---|---|---|
| API style | Rule suite JSON → validator | Schema class → `schema.validate(df)` |
| Integration | Standalone quality gate | Decorator on functions (`@pa.check_input`) |
| Best for | Production pipelines, CI checks | Library code, API input validation |
| Scale | Configurable (GE has data docs) | Lightweight, zero config |

## Related recipes

- r103: GE-style data quality validator (expectation suites)
- r78: constraint optimization — pandera can validate solver inputs
- r109: synthetic problem generator — generates test datasets for schema testing
