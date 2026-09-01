"""Recipe 104 — pandera Schema Validator.

Schema-as-code: define a pandera DataFrameSchema with column types, value ranges,
and categorical checks. Validate any CSV DataFrame against the schema and return
structured results with failure details.
"""

import json
from io import StringIO


_DEFAULT_PAYROLL_SCHEMA = {
    "schema_name": "EmployeePayroll_v1",
    "columns": [
        {"name": "employee_id",  "dtype": "int64",   "nullable": False, "unique": True,  "checks": [{"type": "gt", "value": 999}]},
        {"name": "name",         "dtype": "object",  "nullable": False, "unique": False, "checks": []},
        {"name": "department",   "dtype": "object",  "nullable": False, "unique": False,
         "checks": [{"type": "isin", "value": ["Engineering", "Sales", "HR", "Finance", "Operations"]}]},
        {"name": "salary",       "dtype": "float64", "nullable": False, "unique": False,
         "checks": [{"type": "gt", "value": 0}, {"type": "lt", "value": 500000}]},
        {"name": "hire_year",    "dtype": "int64",   "nullable": False, "unique": False,
         "checks": [{"type": "ge", "value": 2000}, {"type": "le", "value": 2026}]},
    ],
}


def _make_demo_dataframe():
    """Synthetic payroll DataFrame with embedded schema violations."""
    import pandas as pd
    import numpy as np

    rng = np.random.default_rng(7)
    n   = 200

    depts = ["Engineering", "Sales", "HR", "Finance", "Operations"]
    df = pd.DataFrame({
        "employee_id": range(1000, 1000 + n),
        "name":        [f"Employee_{i}" for i in range(n)],
        "department":  rng.choice(depts, n),
        "salary":      rng.uniform(40000, 200000, n).round(2),
        "hire_year":   rng.integers(2000, 2027, n),
    })

    # Inject violations
    zero_idx = rng.choice(n, size=6, replace=False)
    df.loc[zero_idx, "salary"] = 0.0                          # salary == 0

    bad_dept_idx = rng.choice(n, size=4, replace=False)
    df.loc[bad_dept_idx, "department"] = "Temp"               # invalid department

    null_idx = rng.choice(n, size=3, replace=False)
    df.loc[null_idx, "name"] = None                           # null name

    return df


def get_default_schema() -> str:
    """Return the default payroll schema JSON."""
    return json.dumps(_DEFAULT_PAYROLL_SCHEMA)


def validate_schema(schema_json: str, data_csv: str) -> str:
    """Validate a DataFrame against a pandera schema.

    Returns:
      {"schema_name": str, "n_rows": int, "status": "PASS"|"FAIL"|"ERROR",
       "n_violations": int, "violations": [{column, check, n_failed, samples}]}
    """
    try:
        import pandas as pd
        import pandera as pa  # type: ignore[import-untyped]
    except ImportError as e:
        return json.dumps({"status": "ERROR", "error": str(e) + " — run: pip install pandera"})

    try:
        schema_def = json.loads(schema_json)
        if data_csv.strip() in ("", "demo"):
            df = _make_demo_dataframe()
        else:
            df = pd.read_csv(StringIO(data_csv))

        check_map = {
            "gt":   pa.Check.gt,
            "ge":   pa.Check.ge,
            "lt":   pa.Check.lt,
            "le":   pa.Check.le,
            "isin": pa.Check.isin,
            "ne":   pa.Check.ne,
        }

        pa_cols: dict = {}
        for col_def in schema_def["columns"]:
            checks = [check_map[c["type"]](c["value"]) for c in col_def.get("checks", [])
                      if c["type"] in check_map]
            dtype_map = {"int64": int, "float64": float, "object": str}
            dtype = dtype_map.get(col_def["dtype"], str)
            pa_cols[col_def["name"]] = pa.Column(
                dtype,
                checks=checks,
                nullable=col_def.get("nullable", True),
                unique=col_def.get("unique", False),
            )

        schema = pa.DataFrameSchema(pa_cols)

        violations = []
        try:
            schema.validate(df, lazy=True)
            return json.dumps({
                "schema_name": schema_def.get("schema_name", "unnamed"),
                "n_rows": len(df),
                "status": "PASS",
                "n_violations": 0,
                "violations": [],
            })
        except pa.errors.SchemaErrors as e:
            errors_df = e.failure_cases
            for _, grp in errors_df.groupby(["schema_context", "column"]):
                row = grp.iloc[0]
                violations.append({
                    "column":   str(row.get("column", "?")),
                    "check":    str(row.get("check", "?")),
                    "n_failed": len(grp),
                    "samples":  grp["failure_case"].head(5).tolist(),
                })
            return json.dumps({
                "schema_name": schema_def.get("schema_name", "unnamed"),
                "n_rows": len(df),
                "status": "FAIL",
                "n_violations": len(violations),
                "violations": violations,
            })

    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def schema_passes(result_json: str) -> bool:
    """ASSERT gate: schema validation passes (no violations)."""
    try:
        return json.loads(result_json).get("status") == "PASS"
    except Exception:
        return False


def format_schema_report(result_json: str) -> str:
    """Markdown report of schema validation results."""
    try:
        data       = json.loads(result_json)
        violations = data.get("violations", [])
        status_sym = "✓ PASS" if data.get("status") == "PASS" else "✗ FAIL"
        lines = [
            f"## pandera Schema Report — {data.get('schema_name', 'Schema')}",
            "",
            f"**Dataset:** {data.get('n_rows', '?')} rows  ",
            f"**Status:** {status_sym}  ",
            f"**Violations:** {data.get('n_violations', 0)} column checks failed",
            "",
        ]
        if violations:
            lines += ["| Column | Check | Failures | Sample Values |", "|---|---|---|---|"]
            for v in violations:
                samples = str(v.get("samples", [])[:3])
                lines.append(f"| {v['column']} | {v['check']} | {v['n_failed']} | {samples} |")
        else:
            lines.append("All column checks passed.")
        return "\n".join(lines)
    except Exception as e:
        return f"(format error: {e})"


def json_get_field(data_json: str, field: str) -> str:
    try:
        v = json.loads(data_json).get(field)
        return str(v) if v is not None else ""
    except Exception:
        return ""
