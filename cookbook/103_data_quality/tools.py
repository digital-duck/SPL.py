"""Recipe 103 — Data Quality Validator.

Implements a GE-style (Great Expectations) expectation suite over pandas DataFrames.
Each expectation is a declarative rule: expect_column_values_to_not_be_null,
expect_column_values_to_be_between, etc. The validator runs all expectations and
returns a structured result with pass/fail counts and failure samples.
"""

import json
from io import StringIO


# ── Expectation engine ───────────────────────────────────────────────────────

def _run_expectation(df, exp: dict) -> dict:
    """Execute a single expectation against a DataFrame. Returns result dict."""
    import pandas as pd

    col   = exp.get("column")
    etype = exp["type"]
    rows  = len(df)

    if etype == "expect_column_to_exist":
        passed = col in df.columns
        return {"type": etype, "column": col, "passed": passed,
                "n_failed": 0 if passed else rows,
                "message": "" if passed else f"Column '{col}' not found"}

    if col not in df.columns:
        return {"type": etype, "column": col, "passed": False,
                "n_failed": rows, "message": f"Column '{col}' not found"}

    series = df[col]

    if etype == "expect_column_values_to_not_be_null":
        mask    = series.isna()
        n_fail  = int(mask.sum())
        samples = series[mask].index[:5].tolist()
        return {"type": etype, "column": col, "passed": n_fail == 0,
                "n_failed": n_fail, "pct_failed": round(n_fail / rows * 100, 2),
                "sample_rows": samples}

    if etype == "expect_column_values_to_be_between":
        mn, mx = exp.get("min_value"), exp.get("max_value")
        mask   = pd.Series([False] * rows, index=df.index)
        if mn is not None:
            mask = mask | (series < mn)
        if mx is not None:
            mask = mask | (series > mx)
        n_fail = int(mask.sum())
        return {"type": etype, "column": col, "passed": n_fail == 0,
                "n_failed": n_fail, "pct_failed": round(n_fail / rows * 100, 2),
                "min_value": mn, "max_value": mx,
                "sample_values": series[mask].head(5).tolist()}

    if etype == "expect_column_values_to_be_in_set":
        allowed = set(exp.get("value_set", []))
        mask    = ~series.isin(allowed) & series.notna()
        n_fail  = int(mask.sum())
        return {"type": etype, "column": col, "passed": n_fail == 0,
                "n_failed": n_fail, "pct_failed": round(n_fail / rows * 100, 2),
                "value_set": list(allowed),
                "unexpected_values": list(series[mask].unique()[:5])}

    if etype == "expect_column_values_to_be_unique":
        dupes  = series.duplicated()
        n_fail = int(dupes.sum())
        return {"type": etype, "column": col, "passed": n_fail == 0,
                "n_failed": n_fail, "pct_failed": round(n_fail / rows * 100, 2),
                "sample_dupes": series[dupes].head(5).tolist()}

    if etype == "expect_column_values_to_match_regex":
        pattern = exp.get("regex", ".*")
        mask    = ~series.astype(str).str.match(pattern, na=False)
        n_fail  = int(mask.sum())
        return {"type": etype, "column": col, "passed": n_fail == 0,
                "n_failed": n_fail, "pct_failed": round(n_fail / rows * 100, 2),
                "regex": pattern, "sample_failures": series[mask].head(5).tolist()}

    return {"type": etype, "column": col, "passed": False,
            "n_failed": 0, "message": f"Unknown expectation type: {etype}"}


# ── Default sales dataset + expectation suite ────────────────────────────────

_DEFAULT_SUITE = {
    "suite_name": "SalesTransactions_v1",
    "expectations": [
        {"type": "expect_column_to_exist",              "column": "transaction_id"},
        {"type": "expect_column_to_exist",              "column": "amount"},
        {"type": "expect_column_to_exist",              "column": "customer_id"},
        {"type": "expect_column_to_exist",              "column": "region"},
        {"type": "expect_column_values_to_be_unique",   "column": "transaction_id"},
        {"type": "expect_column_values_to_not_be_null", "column": "transaction_id"},
        {"type": "expect_column_values_to_not_be_null", "column": "customer_id"},
        {"type": "expect_column_values_to_not_be_null", "column": "amount"},
        {"type": "expect_column_values_to_be_between",  "column": "amount",
         "min_value": 0.01, "max_value": 10000},
        {"type": "expect_column_values_to_be_in_set",   "column": "region",
         "value_set": ["North", "South", "East", "West"]},
    ],
}


def _make_demo_dataframe():
    """Create a synthetic sales dataset with embedded quality issues."""
    import pandas as pd
    import numpy as np

    rng = np.random.default_rng(42)
    n   = 500  # synthetic sample

    df = pd.DataFrame({
        "transaction_id": [f"TXN{i:05d}" for i in range(n)],
        "amount":         rng.uniform(1, 9000, n).round(2),
        "customer_id":    [f"CUST{rng.integers(1, 200):04d}" for _ in range(n)],
        "region":         rng.choice(["North", "South", "East", "West"], n),
        "date":           pd.date_range("2024-01-01", periods=n, freq="h").astype(str),
    })

    # Inject quality issues
    neg_idx   = rng.choice(n, size=12, replace=False)
    df.loc[neg_idx, "amount"] = rng.uniform(-500, -1, 12).round(2)  # negative amounts

    null_idx  = rng.choice(n, size=8, replace=False)
    df.loc[null_idx, "customer_id"] = None                          # null customer ids

    dupe_idx  = rng.choice(n, size=5, replace=False)
    df.loc[dupe_idx, "transaction_id"] = "TXN99999"                 # duplicate IDs

    region_idx = rng.choice(n, size=3, replace=False)
    df.loc[region_idx, "region"] = "Unknown"                        # invalid region

    return df


def get_default_suite() -> str:
    """Return the default expectation suite JSON."""
    return json.dumps(_DEFAULT_SUITE)


def run_expectations(suite_json: str, data_csv: str) -> str:
    """Run an expectation suite against a CSV-encoded DataFrame.

    Returns:
      {"suite_name": str, "n_rows": int, "n_expectations": int,
       "n_passed": int, "n_failed": int, "status": "PASS"|"FAIL",
       "results": [{type, column, passed, n_failed, ...}]}
    """
    try:
        import pandas as pd
    except ImportError:
        return json.dumps({"status": "ERROR", "error": "pandas not installed"})

    try:
        suite = json.loads(suite_json)
        if data_csv.strip() == "" or data_csv.strip() == "demo":
            df = _make_demo_dataframe()
        else:
            df = pd.read_csv(StringIO(data_csv))

        results  = [_run_expectation(df, exp) for exp in suite["expectations"]]
        n_passed = sum(1 for r in results if r["passed"])
        n_failed = len(results) - n_passed

        return json.dumps({
            "suite_name":    suite.get("suite_name", "unnamed"),
            "n_rows":        len(df),
            "n_expectations": len(results),
            "n_passed":      n_passed,
            "n_failed":      n_failed,
            "status":        "PASS" if n_failed == 0 else "FAIL",
            "results":       results,
        })
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def all_expectations_pass(result_json: str) -> bool:
    """ASSERT gate: all expectations pass."""
    try:
        return json.loads(result_json).get("status") == "PASS"
    except Exception:
        return False


def format_quality_report(result_json: str) -> str:
    """Markdown report of expectation validation results."""
    try:
        data    = json.loads(result_json)
        results = data.get("results", [])
        lines   = [
            f"## Data Quality Report — {data.get('suite_name', 'Suite')}",
            "",
            f"**Dataset:** {data.get('n_rows', '?')} rows  ",
            f"**Expectations:** {data.get('n_expectations', '?')} total  ",
            f"**Passed:** {data.get('n_passed', '?')}  ",
            f"**Failed:** {data.get('n_failed', '?')}  ",
            f"**Status:** {'✓ PASS' if data.get('status') == 'PASS' else '✗ FAIL'}",
            "",
            "| Expectation | Column | Status | Failures |",
            "|---|---|---|---|",
        ]
        for r in results:
            status  = "PASS" if r["passed"] else f"FAIL ({r.get('n_failed', '?')} rows, {r.get('pct_failed', '?')}%)"
            details = ""
            if not r["passed"]:
                if "unexpected_values" in r:
                    details = f" values={r['unexpected_values'][:3]}"
                elif "sample_values" in r:
                    details = f" samples={r['sample_values'][:3]}"
            lines.append(f"| {r['type']} | {r.get('column', '—')} | {status}{details} | |")
        return "\n".join(lines)
    except Exception as e:
        return f"(format error: {e})"


def json_get_field(data_json: str, field: str) -> str:
    try:
        v = json.loads(data_json).get(field)
        return str(v) if v is not None else ""
    except Exception:
        return ""
