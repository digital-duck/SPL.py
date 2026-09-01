# Recipe 103 — Data Quality Validator (Great Expectations style)

**The key story:** A 500-row sales dataset has 12 negative amounts (billing reversal bug) and 8 null customer_ids (data ingestion failure). LLM inspects the description → "data looks clean." The expectation engine runs 10 declarative rules against all 500 rows in <0.1s → fails 4 expectations with exact row counts.

## What it demonstrates

| Axis | solver=ON | solver=OFF |
|---|---|---|
| Engine | Declarative expectation suite (GE-style) | LLM estimates from description |
| Coverage | All 500 rows, 10 expectations | Sample-based, no row-level counts |
| Guarantee | Exact failure counts per rule | "Some rows might have issues" |
| Verification | `ASSERT all_expectations_pass` (C1) | — |
| Solver class | C1 (categorical: PASS / FAIL per expectation) | — |

## Expectation suite (SalesTransactions_v1)

| Expectation | Column | Rule |
|---|---|---|
| expect_column_to_exist | transaction_id, amount, customer_id, region | Required columns present |
| expect_column_values_to_be_unique | transaction_id | No duplicate transaction IDs |
| expect_column_values_to_not_be_null | transaction_id, customer_id, amount | No nulls in key columns |
| expect_column_values_to_be_between | amount | 0.01 ≤ amount ≤ 10,000 |
| expect_column_values_to_be_in_set | region | One of: North, South, East, West |

## Injected quality issues (demo dataset)

| Issue | Rows | Rule Violated |
|---|---|---|
| Negative amounts (-$500 to -$1) | 12 | expect_between (amount ≥ 0.01) |
| Null customer_ids | 8 | expect_not_null (customer_id) |
| Duplicate transaction_ids ("TXN99999") | 5 | expect_unique (transaction_id) |
| Invalid region ("Unknown") | 3 | expect_in_set (region) |

## Run commands

```bash
# solver=ON — expectation engine on demo dataset
spl3 run cookbook/103_data_quality/data_quality.spl \
    --adapter claude_cli --param use_solver=true

# solver=OFF — LLM inspects description
spl3 run cookbook/103_data_quality/data_quality.spl \
    --adapter ollama -m gemma3 --param use_solver=false

# Validate your own CSV file
spl3 run cookbook/103_data_quality/data_quality.spl \
    --adapter claude_cli --param use_solver=true \
    --param "data_csv=$(cat my_sales.csv)"
```

## Install

```bash
conda activate spl123
pip install pandas numpy  # already in spl123
```

No additional install required — uses a pure-Python expectation engine.
To use the actual Great Expectations library in production: `pip install great-expectations`.

## TOOL_API reference

| Function | Purpose |
|---|---|
| `get_default_suite()` | Returns SalesTransactions_v1 expectation suite JSON |
| `run_expectations(suite_json, data_csv)` | Validates a DataFrame against the suite; "demo" generates synthetic data |
| `all_expectations_pass(result_json)` | ASSERT gate: `status == "PASS"` |
| `format_quality_report(result_json)` | Markdown table of pass/fail results with row counts |

## Expectation types supported

- `expect_column_to_exist`
- `expect_column_values_to_not_be_null`
- `expect_column_values_to_be_between`
- `expect_column_values_to_be_in_set`
- `expect_column_values_to_be_unique`
- `expect_column_values_to_match_regex`

## Related recipes

- r104: pandera — schema-as-code validation (type-safe, decorator-based)
- r94: hand-rolled quality gates — the ad-hoc predecessor this recipe replaces
- r109: synthetic problem generator — can generate test CSVs for this recipe
