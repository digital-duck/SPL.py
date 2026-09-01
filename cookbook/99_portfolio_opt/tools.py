"""
Recipe 99 — Portfolio optimization via cvxpy (Markowitz mean-variance).
TOOL_APIs called from portfolio_opt.spl.
"""

import json
from datetime import datetime, timedelta


def is_optimized(optimization_json: str) -> bool:
    """Return True when cvxpy status is OPTIMAL or optimal_inaccurate."""
    import json
    try:
        data = json.loads(optimization_json)
        return data.get("status", "") in ("OPTIMAL", "optimal", "optimal_inaccurate")
    except Exception:
        return "OPTIMAL" in optimization_json or "optimal" in optimization_json


def json_get_field(data_json: str, field: str) -> str:
    """Extract a top-level field from a JSON object; return empty string on failure."""
    import json
    try:
        data = json.loads(data_json)
        return str(data.get(field, ""))
    except Exception:
        return ""


def fetch_stock_data(tickers_str: str, period: str = "1y",
                     trading_days_per_year: int = 252,
                     min_data_fraction: float = 0.8) -> str:
    """
    Fetch historical adjusted-close prices for a comma-separated list of tickers.

    Args:
        tickers_str:           Comma-separated ticker symbols (e.g. "AAPL,MSFT,GOOG").
        period:                Look-back window — "1mo","3mo","6mo","1y","2y","3y" (default "1y").
        trading_days_per_year: Used to annualize daily mean returns and covariance
                               (default 252 = NYSE/NASDAQ trading days; use 261 for a
                               broader market or 250 for a conservative estimate).
                               Must be in [200, 300].
        min_data_fraction:     Fraction of trading days a ticker must have data for to be
                               included; tickers below this threshold are dropped
                               (default 0.8 = 80%; use 1.0 to require complete data).
                               Must be in (0.0, 1.0].

    Returns JSON: {"tickers": [...], "annual_returns": {...}, "cov_matrix": [[...]], "period": "..."}
    """
    if not (200 <= trading_days_per_year <= 300):
        return json.dumps({"error": f"trading_days_per_year {trading_days_per_year} out of range [200, 300]"})
    if not (0.0 < min_data_fraction <= 1.0):
        return json.dumps({"error": f"min_data_fraction {min_data_fraction} out of range (0.0, 1.0]"})

    try:
        import yfinance as yf

        tickers = [t.strip().upper() for t in tickers_str.split(",") if t.strip()]
        if not tickers:
            return json.dumps({"error": "no tickers provided"})

        end = datetime.today()
        period_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "3y": 1095}
        days = period_map.get(period, 365)
        start = end - timedelta(days=days)

        raw = yf.download(tickers, start=start.strftime("%Y-%m-%d"),
                          end=end.strftime("%Y-%m-%d"),
                          auto_adjust=True, progress=False)
        if raw is None or raw.empty:
            return json.dumps({"error": "no price data returned"})
        prices = raw["Close"]

        # Handle single-ticker case (Series → DataFrame)
        if not hasattr(prices, "columns"):
            prices = prices.to_frame(name=tickers[0])

        # Drop tickers with insufficient data
        min_count = int(min_data_fraction * len(prices))
        prices = prices.loc[:, prices.count() >= min_count]
        valid_tickers = list(prices.columns)

        # Daily returns → annualise
        daily_ret = prices.pct_change().dropna()
        annual_returns = (daily_ret.mean() * trading_days_per_year).to_dict()
        cov_matrix = (daily_ret.cov() * trading_days_per_year).values.tolist()

        return json.dumps({
            "tickers": valid_tickers,
            "annual_returns": {k: round(v, 6) for k, v in annual_returns.items()},
            "cov_matrix": [[round(v, 8) for v in row] for row in cov_matrix],
            "period": period,
            "trading_days": len(daily_ret),
        })

    except Exception as e:
        return json.dumps({"error": str(e)})


def optimize_portfolio(market_data_json: str, target_return: float = 0.10,
                       max_weight: float = 0.25, min_weight: float = 0.0,
                       risk_free_rate: float = 0.05) -> str:
    """
    Run Markowitz mean-variance optimization via cvxpy.
    Minimizes portfolio variance subject to:
      - expected return >= target_return
      - sum of weights = 1  (fully invested, long only)
      - min_weight <= w_i <= max_weight  (position limits)

    Args:
        market_data_json: JSON output from fetch_market_data.
        target_return:    Minimum annualized portfolio return (default 0.10 = 10%).
        max_weight:       Maximum allocation per asset, 0–1 (default 0.25 = 25%).
        min_weight:       Minimum allocation per asset, 0–1 (default 0.0 = long-only).
        risk_free_rate:   Annual risk-free rate used in Sharpe ratio calculation,
                          must be in [0.0, 0.20] (default 0.05 = 5%).
                          Typical range: 0.03–0.06 for US Treasuries.

    Returns JSON: {status, weights, expected_return, annual_volatility, sharpe_ratio, solver_log}
    """
    try:
        import cvxpy as cp
        import numpy as np

        data = json.loads(market_data_json)
        if "error" in data:
            return json.dumps({"status": "DATA_ERROR", "error": data["error"]})

        tickers = data["tickers"]
        mu = np.array([data["annual_returns"][t] for t in tickers])
        Sigma = np.array(data["cov_matrix"])
        n = len(tickers)

        w = cp.Variable(n)
        port_return = mu @ w
        port_variance = cp.quad_form(w, Sigma)

        constraints = [
            cp.sum(w) == 1,
            w >= min_weight,
            w <= max_weight,
            port_return >= target_return,
        ]

        problem = cp.Problem(cp.Minimize(port_variance), constraints)
        problem.solve(solver=cp.CLARABEL, verbose=False)

        status = problem.status
        if status not in ("optimal", "optimal_inaccurate"):
            return json.dumps({
                "status": status.upper(),
                "weights": {},
                "expected_return": None,
                "annual_volatility": None,
                "sharpe_ratio": None,
                "solver_log": f"cvxpy status: {status}",
            })

        if not (0.0 <= risk_free_rate <= 0.20):
            return json.dumps({"status": "INPUT_ERROR",
                               "error": f"risk_free_rate {risk_free_rate} out of range [0.0, 0.20]"})

        weights_arr = w.value
        exp_ret = float(mu @ weights_arr)
        volatility = float(np.sqrt(weights_arr @ Sigma @ weights_arr))
        sharpe = (exp_ret - risk_free_rate) / volatility if volatility > 0 else 0.0

        weights_dict = {
            t: round(float(weights_arr[i]), 6)
            for i, t in enumerate(tickers)
            if abs(weights_arr[i]) > 1e-4
        }

        return json.dumps({
            "status": "OPTIMAL",
            "weights": weights_dict,
            "expected_return": round(exp_ret, 4),
            "annual_volatility": round(volatility, 4),
            "sharpe_ratio": round(sharpe, 4),
            "solver_log": f"cvxpy CLARABEL; obj={port_variance.value:.6f}",
        })

    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def allocate_capital(optimization_json: str, capital: float) -> str:
    """
    Convert optimal weights to dollar allocations for a given capital amount.
    Returns JSON: {tickers: [{ticker, weight_pct, dollars, shares_approx}], total}
    """
    try:
        data = json.loads(optimization_json)
        weights = data.get("weights", {})
        if not weights:
            return json.dumps({"error": "no weights in optimization result"})

        allocations = []
        for ticker, weight in sorted(weights.items(), key=lambda x: -x[1]):
            dollars = round(weight * capital, 2)
            allocations.append({
                "ticker": ticker,
                "weight_pct": round(weight * 100, 2),
                "dollars": dollars,
            })

        return json.dumps({
            "capital": capital,
            "allocations": allocations,
            "expected_annual_return": data.get("expected_return"),
            "annual_volatility": data.get("annual_volatility"),
            "sharpe_ratio": data.get("sharpe_ratio"),
        })

    except Exception as e:
        return json.dumps({"error": str(e)})


def verify_portfolio(optimization_json: str,
                     max_weight_limit: float = 0.40,
                     weight_sum_tol: float = 0.02) -> str:
    """
    Back-substitution verifier for solver=OFF path.
    Checks: weights sum ≈ 1, all weights in [0,1], return/volatility consistency.

    Args:
        optimization_json: JSON output from optimize_portfolio or an LLM-generated portfolio.
        max_weight_limit:  Per-asset weight cap for the sanity check (default 0.40 = 40%).
                           Set to match the optimizer's max_weight when running ablation sweeps.
                           Must be in (0.0, 1.0].
        weight_sum_tol:    Absolute tolerance for the weights-sum-to-1 check
                           (default 0.02; tighten to 0.001 for high-precision verification).
                           Must be in [0.0, 0.05].
    """
    if not (0.0 < max_weight_limit <= 1.0):
        return json.dumps({"verdict": "INPUT_ERROR",
                           "notes": f"max_weight_limit {max_weight_limit} out of range (0.0, 1.0]"})
    if not (0.0 <= weight_sum_tol <= 0.05):
        return json.dumps({"verdict": "INPUT_ERROR",
                           "notes": f"weight_sum_tol {weight_sum_tol} out of range [0.0, 0.05]"})

    try:
        data = json.loads(optimization_json)
        weights = data.get("weights", {})
        notes: list[str] = []
        ok = True

        if not weights:
            return json.dumps({"verdict": "UNPARSEABLE", "notes": "no weights found"})

        weight_values = list(weights.values())
        total = sum(weight_values)

        if abs(total - 1.0) > weight_sum_tol:
            notes.append(f"weights sum to {total:.4f}, expected 1.0 ± {weight_sum_tol}")
            ok = False

        negative = [t for t, w in weights.items() if w < -0.01]
        if negative:
            notes.append(f"negative weights: {negative}")
            ok = False

        over_limit = [t for t, w in weights.items() if w > max_weight_limit]
        if over_limit:
            notes.append(f"weights exceed {max_weight_limit:.0%} limit: {over_limit}")
            ok = False

        exp_ret = data.get("expected_return")
        volatility = data.get("annual_volatility")
        if exp_ret is not None and exp_ret < 0:
            notes.append(f"negative expected return: {exp_ret}")
            ok = False
        if volatility is not None and volatility < 0:
            notes.append(f"negative volatility: {volatility}")
            ok = False

        return json.dumps({
            "verdict": "PASS" if ok else "FAIL",
            "weight_sum": round(total, 4),
            "n_positions": len(weights),
            "notes": "; ".join(notes) if notes else "all checks passed",
        })

    except Exception as e:
        return json.dumps({"verdict": "UNPARSEABLE", "notes": str(e)})
