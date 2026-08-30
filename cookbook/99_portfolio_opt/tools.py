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


def fetch_stock_data(tickers_str: str, period: str = "1y") -> str:
    """
    Fetch historical adjusted-close prices for a comma-separated list of tickers.
    Returns JSON: {"tickers": [...], "annual_returns": {...}, "cov_matrix": [[...]], "period": "..."}
    """
    try:
        import yfinance as yf
        import numpy as np

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
        min_count = int(0.8 * len(prices))
        prices = prices.loc[:, prices.count() >= min_count]
        valid_tickers = list(prices.columns)

        # Daily returns → annualise
        daily_ret = prices.pct_change().dropna()
        annual_returns = (daily_ret.mean() * 252).to_dict()
        cov_matrix = (daily_ret.cov() * 252).values.tolist()

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
                       max_weight: float = 0.40, min_weight: float = 0.0) -> str:
    """
    Run Markowitz mean-variance optimization via cvxpy.
    Minimizes portfolio variance subject to:
      - expected return >= target_return
      - sum of weights = 1  (fully invested, long only)
      - min_weight <= w_i <= max_weight  (position limits)

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

        weights_arr = w.value
        exp_ret = float(mu @ weights_arr)
        volatility = float(np.sqrt(weights_arr @ Sigma @ weights_arr))
        rf = 0.05  # risk-free rate assumption
        sharpe = (exp_ret - rf) / volatility if volatility > 0 else 0.0

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


def verify_portfolio(optimization_json: str) -> str:
    """
    Back-substitution verifier for solver=OFF path.
    Checks: weights sum ≈ 1, all weights in [0,1], return/volatility consistency.
    """
    try:
        import numpy as np

        data = json.loads(optimization_json)
        weights = data.get("weights", {})
        notes: list[str] = []
        ok = True

        if not weights:
            return json.dumps({"verdict": "UNPARSEABLE", "notes": "no weights found"})

        weight_values = list(weights.values())
        total = sum(weight_values)

        if abs(total - 1.0) > 0.02:
            notes.append(f"weights sum to {total:.4f}, expected 1.0")
            ok = False

        negative = [t for t, w in weights.items() if w < -0.01]
        if negative:
            notes.append(f"negative weights: {negative}")
            ok = False

        over_limit = [t for t, w in weights.items() if w > 0.401]
        if over_limit:
            notes.append(f"weights exceed 40% limit: {over_limit}")
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
