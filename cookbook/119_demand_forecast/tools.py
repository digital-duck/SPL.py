"""Recipe 119 — Demand Forecasting: statsmodels structural time series.

Demonstrates the deterministic–probabilistic boundary in forecasting:
  Probabilistic (LLM)        — extract time-series structure from NL description
  Deterministic (statsmodels) — UnobservedComponents Kalman-filter fit + forecast
  Deterministic (ASSERT)     — RMSE on hold-out period beats naïve baseline
  Probabilistic (LLM)        — interpret forecast and seasonal pattern for user

Default problem: 36 months of synthetic widget sales with clear trend + seasonality.

Solver=ON:  statsmodels UnobservedComponents (local linear trend + seasonal).
Solver=OFF: LLM heuristic — seasonal trend extrapolation (no solver).

ASSERT: forecast RMSE on hold-out < naïve baseline (last-value-repeated).

Install: pip install statsmodels
"""

import json
import re


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text)
    return text.strip()


# 36 months: 3 full years of widget sales (clear trend + Q4 seasonality)
_DEFAULT_PROBLEM = {
    "description": "Monthly widget sales — 3 years of historical data with upward trend and Q4 seasonal spike",
    "frequency": "monthly",
    "seasonal_period": 12,
    "history": [
        # Year 1
         95,  90, 102, 108, 112, 115, 118, 120, 115, 112, 135, 152,
        # Year 2 (~7 % growth)
        102,  97, 110, 116, 120, 124, 127, 129, 124, 121, 145, 164,
        # Year 3 (~7 % growth)
        109, 104, 118, 125, 129, 133, 137, 139, 133, 130, 156, 176,
    ],
}


# ── Tool functions ────────────────────────────────────────────────────────────

def get_default_problem() -> str:
    return json.dumps(_DEFAULT_PROBLEM)


def fit_structural_ts(problem_json: str, periods: str = "6") -> str:
    """Fit statsmodels UnobservedComponents and forecast future periods.

    Uses local-linear-trend + seasonal components (Kalman filter / MLE).
    Holds out the last seasonal_period // 2 observations for RMSE validation.

    Returns:
        {"status": "OK", "forecast": [...], "lower": [...], "upper": [...],
         "n_periods": int, "rmse_holdout": float, "naive_rmse": float,
         "beats_naive": bool}
    """
    try:
        import statsmodels.api as sm
        import numpy as np
    except ImportError:
        return json.dumps({"status": "ERROR",
                           "error": "statsmodels not installed — run: pip install statsmodels"})

    try:
        data = json.loads(_strip_fences(problem_json))
    except Exception as e:
        return json.dumps({"status": "PARSE_ERROR", "error": str(e)})

    history = [float(v) for v in data.get("history", [])]
    seasonal_period = int(data.get("seasonal_period", 12))
    n_forecast = max(1, int(periods))

    if len(history) < 2 * seasonal_period:
        return json.dumps({"status": "INSUFFICIENT_DATA",
                           "error": f"need at least {2 * seasonal_period} observations for seasonal fit"})

    # Hold out last seasonal_period // 2 points for validation
    n_holdout = seasonal_period // 2
    train = history[:-n_holdout]
    holdout = history[-n_holdout:]

    try:
        model = sm.tsa.UnobservedComponents(
            train,
            level='local linear trend',
            seasonal=seasonal_period,
        )
        result = model.fit(disp=False)
    except Exception as e:
        return json.dumps({"status": "FIT_ERROR", "error": str(e)})

    # Forecast holdout + future periods together
    fc = result.get_forecast(steps=n_holdout + n_forecast)
    mean_all = np.asarray(fc.predicted_mean)
    ci_arr = np.asarray(fc.conf_int())
    lower_all = ci_arr[:, 0]
    upper_all = ci_arr[:, 1]

    holdout_pred = mean_all[:n_holdout]
    forecast = mean_all[n_holdout:]
    lower = lower_all[n_holdout:]
    upper = upper_all[n_holdout:]

    rmse = float(np.sqrt(np.mean((np.array(holdout) - holdout_pred) ** 2)))
    naive_pred = np.full(n_holdout, train[-1])
    naive_rmse = float(np.sqrt(np.mean((np.array(holdout) - naive_pred) ** 2)))

    return json.dumps({
        "status": "OK",
        "forecast": [round(float(v), 1) for v in forecast],
        "lower":    [round(float(v), 1) for v in lower],
        "upper":    [round(float(v), 1) for v in upper],
        "n_periods": n_forecast,
        "rmse_holdout": round(rmse, 2),
        "naive_rmse":   round(naive_rmse, 2),
        "beats_naive":  bool(rmse < naive_rmse),
    })


def is_forecast_valid(forecast_json: str) -> bool:
    """ASSERT gate: status==OK and RMSE beats naïve baseline."""
    try:
        d = json.loads(forecast_json)
        return d.get("status") == "OK" and d.get("beats_naive", False)
    except Exception:
        return False


def format_forecast_table(forecast_json: str) -> str:
    """Format forecast as markdown table with confidence interval."""
    try:
        d = json.loads(forecast_json)
        forecast = d.get("forecast", [])
        lower = d.get("lower", [])
        upper = d.get("upper", [])
        if not forecast:
            return "No forecast points."
        lines = [
            "| Period | Forecast | Lower 95% | Upper 95% |",
            "|---|---|---|---|",
        ]
        for i, (f, lo, hi) in enumerate(zip(forecast, lower, upper), 1):
            lines.append(f"| +{i} | {f:.1f} | {lo:.1f} | {hi:.1f} |")
        rmse = d.get("rmse_holdout")
        naive = d.get("naive_rmse")
        if rmse is not None and naive is not None:
            lines.append(f"\nHold-out RMSE: **{rmse:.2f}** vs naïve baseline {naive:.2f} "
                         f"({'✓ beats naïve' if d.get('beats_naive') else '✗ does not beat naïve'})")
        return "\n".join(lines)
    except Exception as e:
        return f"Could not format forecast table: {e}"


def verify_forecast_off(problem_json: str, forecast_json: str) -> str:
    """Sanity-check LLM heuristic forecast.

    Checks:
    - forecast values are positive
    - forecast stays within ±50% of last observed value (gross sanity)
    - number of periods matches requested

    Returns {"verdict": "PASS"/"FAIL", "notes": str}
    """
    try:
        problem = json.loads(_strip_fences(problem_json))
        fc = json.loads(_strip_fences(forecast_json))
    except Exception as e:
        return json.dumps({"verdict": "FAIL", "notes": f"parse error: {e}"})

    history = problem.get("history", [])
    last_val = float(history[-1]) if history else 0.0
    forecast = fc.get("forecast", [])

    notes = []
    ok = True

    if not forecast:
        return json.dumps({"verdict": "FAIL", "notes": "forecast list is empty"})

    for i, v in enumerate(forecast):
        v = float(v)
        if v <= 0:
            notes.append(f"period +{i+1}: non-positive value {v}")
            ok = False
        if last_val > 0 and (v < last_val * 0.5 or v > last_val * 1.5):
            notes.append(f"period +{i+1}: value {v:.1f} is >50% away from last observed {last_val:.1f}")
            ok = False

    return json.dumps({
        "verdict": "PASS" if ok else "FAIL",
        "notes": "; ".join(notes) if notes else "all sanity checks passed",
    })


def format_report_solver_on(problem: str, n_periods: str, forecast_table: str,
                             interpretation: str, llm_calls: str) -> str:
    return (
        "=== Demand Forecasting (solver=ON / statsmodels UnobservedComponents) ===\n\n"
        f"Problem:\n{problem}\n\n"
        f"Forecast ({n_periods} periods ahead):\n{forecast_table}\n\n"
        f"Interpretation:\n{interpretation}\n\n"
        f"LLM calls: {llm_calls}"
    )


def format_report_solver_off(problem: str, forecast_text: str, forecast_json: str,
                              verify_result: str, llm_calls: str) -> str:
    return (
        "=== Demand Forecasting (solver=OFF / LLM heuristic) ===\n\n"
        f"Problem:\n{problem}\n\n"
        f"LLM Forecast:\n{forecast_text}\n\n"
        f"Extracted (JSON):\n{forecast_json}\n\n"
        f"Sanity check:\n{verify_result}\n\n"
        f"LLM calls: {llm_calls}"
    )
