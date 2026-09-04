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
        n = len(tickers)
        if n < 5:
            return json.dumps({
                "status": "INFEASIBLE",
                "weights": {},
                "expected_return": None,
                "annual_volatility": None,
                "sharpe_ratio": None,
                "solver_log": f"portfolio requires at least 5 tickers; got {n}",
            })
        mu = np.array([data["annual_returns"][t] for t in tickers])
        Sigma = np.array(data["cov_matrix"])

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


def format_solver_report(tickers: str, period: str, capital: str,
                         target_return: str, max_weight: str,
                         market_data_json: str, optimization_json: str,
                         allocation_json: str, interpretation: str,
                         llm_calls: str) -> str:
    return (
        f"=== Portfolio Optimization (solver=ON / cvxpy Markowitz) ===\n\n"
        f"Tickers: {tickers}  |  Period: {period}  |  Capital: ${capital}\n"
        f"Target return: {target_return}  |  Max position: {max_weight}\n\n"
        f"Market Data:\n{market_data_json}\n\n"
        f"Optimization Result:\n{optimization_json}\n\n"
        f"Capital Allocation:\n{allocation_json}\n\n"
        f"Interpretation:\n{interpretation}\n\n"
        f"LLM calls: {llm_calls}"
    )


def format_heuristic_report(tickers: str, period: str, capital: str,
                             market_data_json: str, llm_allocation: str,
                             optimization_json: str, allocation_json: str,
                             verify_result: str, llm_calls: str) -> str:
    return (
        f"=== Portfolio Optimization (solver=OFF / LLM heuristic) ===\n\n"
        f"Tickers: {tickers}  |  Period: {period}  |  Capital: ${capital}\n\n"
        f"Market Data:\n{market_data_json}\n\n"
        f"LLM Allocation:\n{llm_allocation}\n\n"
        f"Extracted Weights (JSON):\n{optimization_json}\n\n"
        f"Capital Allocation:\n{allocation_json}\n\n"
        f"Verification:\n{verify_result}\n\n"
        f"LLM calls: {llm_calls}"
    )


def _parse_algo_results(raws: list, algo_labels: list) -> list:
    parsed = []
    for name, raw in zip(algo_labels, raws):
        try:
            d = json.loads(raw)
        except Exception:
            d = {"status": "PARSE_ERROR", "weights": {}, "expected_return": None,
                 "annual_volatility": None, "sharpe_ratio": None}
        d["_name"] = name
        parsed.append(d)
    return parsed


def comparison_to_csv(tickers: str,
                      r_markowitz: str, r_min_var: str, r_max_sharpe: str,
                      r_risk_parity: str, r_hrp: str, r_cvar: str) -> str:
    """Algorithm summary: rows=algorithms, cols=metrics + per-ticker weight."""
    import csv, io

    ticker_list = [t.strip() for t in tickers.split(",")]
    algo_labels = ["markowitz", "min_variance", "max_sharpe", "risk_parity", "hrp", "cvar"]
    parsed = _parse_algo_results(
        [r_markowitz, r_min_var, r_max_sharpe, r_risk_parity, r_hrp, r_cvar], algo_labels)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["algorithm", "status", "expected_return", "annual_volatility",
                     "sharpe_ratio"] + ticker_list)
    for d in parsed:
        weights = d.get("weights", {})
        writer.writerow([
            d["_name"],
            d.get("status", "UNKNOWN"),
            f"{d.get('expected_return') or 0:.4f}",
            f"{d.get('annual_volatility') or 0:.4f}",
            f"{d.get('sharpe_ratio') or 0:.4f}",
        ] + [f"{weights.get(t, 0.0):.4f}" for t in ticker_list])
    return buf.getvalue().strip()


def composition_to_csv(tickers: str, capital: str,
                       r_markowitz: str, r_min_var: str, r_max_sharpe: str,
                       r_risk_parity: str, r_hrp: str, r_cvar: str) -> str:
    """Portfolio composition: rows=tickers, cols=weight% and $ per algorithm."""
    import csv, io

    ticker_list = [t.strip() for t in tickers.split(",")]
    cap = float(capital)
    algo_labels = ["markowitz", "min_variance", "max_sharpe", "risk_parity", "hrp", "cvar"]
    parsed = _parse_algo_results(
        [r_markowitz, r_min_var, r_max_sharpe, r_risk_parity, r_hrp, r_cvar], algo_labels)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["ticker"]
                    + [f"{a}_wt%" for a in algo_labels]
                    + [f"{a}_$"   for a in algo_labels])
    for ticker in ticker_list:
        row = [ticker]
        row += [f"{d.get('weights', {}).get(ticker, 0.0) * 100:.2f}" for d in parsed]
        row += [f"{d.get('weights', {}).get(ticker, 0.0) * cap:.0f}" for d in parsed]
        writer.writerow(row)
    return buf.getvalue().strip()


def save_csv(csv_text: str, out_dir: str, filename: str) -> str:
    """Write csv_text to out_dir/filename, creating the directory if needed.

    Returns the absolute path of the saved file.
    """
    import os
    from pathlib import Path
    out = Path(out_dir) if os.path.isabs(out_dir) else Path(os.getcwd()) / out_dir
    out.mkdir(parents=True, exist_ok=True)
    dest = out / filename
    dest.write_text(csv_text, encoding="utf-8")
    return str(dest)


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


# ── Alternative algorithm implementations ─────────────────────

def _portfolio_result(tickers, w, mu, Sigma, algorithm,
                      risk_free_rate=0.05, status="OPTIMAL", solver_log=""):
    import numpy as np
    w = np.maximum(w, 0)
    w = w / w.sum()
    exp_ret = float(mu @ w)
    vol = float(np.sqrt(w @ Sigma @ w))
    sharpe = (exp_ret - risk_free_rate) / vol if vol > 0 else 0.0
    weights_dict = {t: round(float(w[i]), 6) for i, t in enumerate(tickers) if abs(w[i]) > 1e-4}
    return {
        "status": status,
        "algorithm": algorithm,
        "weights": weights_dict,
        "expected_return": round(exp_ret, 4),
        "annual_volatility": round(vol, 4),
        "sharpe_ratio": round(sharpe, 4),
        "solver_log": solver_log,
    }


def _opt_min_variance(tickers, mu, Sigma, max_weight, min_weight):
    """Minimize wᵀΣw with no return target — most robust to μ estimation error."""
    import cvxpy as cp
    n = len(tickers)
    w = cp.Variable(n)
    prob = cp.Problem(
        cp.Minimize(cp.quad_form(w, Sigma)),
        [cp.sum(w) == 1, w >= min_weight, w <= max_weight],
    )
    prob.solve(solver=cp.CLARABEL, verbose=False)
    if prob.status not in ("optimal", "optimal_inaccurate"):
        return None, prob.status
    return w.value, f"CLARABEL min-variance; obj={prob.value:.6f}"


def _opt_max_sharpe(tickers, mu, Sigma, max_weight, min_weight, risk_free_rate=0.05):
    """Charnes-Cooper transform: maximize (μᵀw − Rf) / √(wᵀΣw)."""
    import cvxpy as cp
    import numpy as np
    excess = mu - risk_free_rate
    if np.all(excess <= 0):
        return None, "INFEASIBLE_NO_EXCESS_RETURN"
    n = len(tickers)
    y = cp.Variable(n)   # y = w * t, t = 1/(μᵀw − Rf)
    t = cp.Variable()
    prob = cp.Problem(
        cp.Minimize(cp.quad_form(y, Sigma)),
        [excess @ y == 1, cp.sum(y) == t,
         y >= min_weight * t, y <= max_weight * t, t >= 0],
    )
    prob.solve(solver=cp.CLARABEL, verbose=False)
    if prob.status not in ("optimal", "optimal_inaccurate") or t.value is None or t.value < 1e-8:
        return None, prob.status
    w = y.value / t.value
    return w, f"CLARABEL Charnes-Cooper; obj={prob.value:.6f}"


def _opt_risk_parity(tickers, mu, Sigma, max_weight):
    """Equal Risk Contribution: each asset contributes 1/N of total portfolio risk."""
    import numpy as np
    from scipy.optimize import minimize
    n = len(tickers)

    def objective(w):
        w = np.maximum(w, 1e-10)
        port_var = w @ Sigma @ w
        marginal = Sigma @ w
        contrib = w * marginal / port_var
        target = 1.0 / n
        return float(np.sum((contrib - target) ** 2))

    result = minimize(
        objective,
        x0=np.ones(n) / n,
        method="SLSQP",
        bounds=[(0.0, max_weight)] * n,
        constraints={"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
        options={"maxiter": 2000, "ftol": 1e-12},
    )
    if not result.success:
        return None, f"scipy SLSQP: {result.message}"
    return result.x, f"scipy SLSQP risk-parity; obj={result.fun:.8f}"


def _opt_hrp(tickers, mu, Sigma, max_weight):
    """Hierarchical Risk Parity: cluster-based allocation, no matrix inversion."""
    import numpy as np
    from scipy.cluster.hierarchy import linkage
    from scipy.spatial.distance import squareform

    n = len(tickers)
    std = np.sqrt(np.diag(Sigma))
    corr = Sigma / np.outer(std, std)
    corr = np.clip(corr, -1.0, 1.0)
    np.fill_diagonal(corr, 1.0)

    dist = np.sqrt(np.clip(0.5 * (1.0 - corr), 0, None))
    np.fill_diagonal(dist, 0.0)
    link = linkage(squareform(dist), method="single")

    # Recover leaf ordering (quasi-diagonalisation)
    def _leaf_order(link, n):
        items = [[i] for i in range(n)]
        for row in link:
            i, j = int(row[0]), int(row[1])
            items.append(items[i] + items[j])
        return items[-1]

    sort_ix = _leaf_order(link, n)

    def _cluster_var(ix_list):
        cov_slice = Sigma[np.ix_(ix_list, ix_list)]
        inv_d = 1.0 / np.diag(cov_slice)
        w_ = inv_d / inv_d.sum()
        return float(w_ @ cov_slice @ w_)

    weights = {i: 1.0 for i in range(n)}
    clusters = [sort_ix]
    while clusters:
        next_lvl = []
        for c in clusters:
            if len(c) < 2:
                continue
            mid = len(c) // 2
            left, right = c[:mid], c[mid:]
            v_l, v_r = _cluster_var(left), _cluster_var(right)
            alpha = 1.0 - v_l / (v_l + v_r)
            for i in left:
                weights[i] *= alpha
            for i in right:
                weights[i] *= 1.0 - alpha
            next_lvl += [left, right]
        clusters = next_lvl

    w = np.array([weights[i] for i in range(n)])
    w = np.minimum(w, max_weight)
    w /= w.sum()
    return w, "scipy HRP single-linkage"


def _opt_cvar(tickers, mu, Sigma, max_weight, min_weight, target_return,
              alpha=0.05, n_scenarios=1000):
    """CVaR minimization: minimize expected loss in worst α% of scenarios."""
    import cvxpy as cp
    import numpy as np

    np.random.seed(42)
    n = len(tickers)
    L = np.linalg.cholesky(Sigma + 1e-8 * np.eye(n))
    scenarios = mu + (L @ np.random.randn(n, n_scenarios)).T   # (T, n)
    T = n_scenarios

    w = cp.Variable(n)
    beta = cp.Variable()
    losses = -scenarios @ w

    cvar = beta + (1.0 / (alpha * T)) * cp.sum(cp.pos(losses - beta))
    prob = cp.Problem(
        cp.Minimize(cvar),
        [cp.sum(w) == 1, w >= min_weight, w <= max_weight, mu @ w >= target_return],
    )
    prob.solve(solver=cp.CLARABEL, verbose=False)
    if prob.status not in ("optimal", "optimal_inaccurate") or w.value is None:
        return None, prob.status
    return w.value, f"CLARABEL CVaR α={alpha}; obj={prob.value:.6f}"


def optimize_by_algorithm(market_data_json: str, algorithm: str = "markowitz",
                           target_return: float = 0.10, max_weight: float = 0.25,
                           min_weight: float = 0.0, risk_free_rate: float = 0.05) -> str:
    """
    Unified dispatcher for all portfolio optimization algorithms.

    algorithm choices:
      markowitz   — Minimize variance subject to return target (default)
      min_variance— Minimize variance with no return constraint; robust to noisy μ
      max_sharpe  — Maximize Sharpe ratio via Charnes-Cooper transform
      risk_parity — Equal risk contribution from each asset (no μ needed)
      hrp         — Hierarchical Risk Parity; best for small N or short history
      cvar        — Minimize Conditional Value at Risk (tail-loss focus)
    """
    try:
        import numpy as np
        data = json.loads(market_data_json)
        if "error" in data:
            return json.dumps({"status": "DATA_ERROR", "algorithm": algorithm, "error": data["error"]})

        tickers = data["tickers"]
        n = len(tickers)
        if n < 5:
            return json.dumps({
                "status": "INFEASIBLE", "algorithm": algorithm, "weights": {},
                "expected_return": None, "annual_volatility": None, "sharpe_ratio": None,
                "solver_log": f"requires >= 5 tickers; got {n}",
            })

        mu = np.array([data["annual_returns"][t] for t in tickers])
        Sigma = np.array(data["cov_matrix"])
        alg = algorithm.lower().strip()

        valid_algorithms = ("markowitz", "min_variance", "max_sharpe", "risk_parity", "hrp", "cvar")
        if alg not in valid_algorithms:
            return json.dumps({"status": "INPUT_ERROR", "algorithm": alg,
                               "error": f"unknown algorithm '{alg}'; valid: {', '.join(valid_algorithms)}"})

        if alg == "markowitz":
            w, log = _markowitz_qp(mu, Sigma, max_weight, min_weight, target_return)
        elif alg == "min_variance":
            w, log = _opt_min_variance(tickers, mu, Sigma, max_weight, min_weight)
        elif alg == "max_sharpe":
            w, log = _opt_max_sharpe(tickers, mu, Sigma, max_weight, min_weight, risk_free_rate)
        elif alg == "risk_parity":
            w, log = _opt_risk_parity(tickers, mu, Sigma, max_weight)
        elif alg == "hrp":
            w, log = _opt_hrp(tickers, mu, Sigma, max_weight)
        else:  # cvar
            w, log = _opt_cvar(tickers, mu, Sigma, max_weight, min_weight, target_return)

        if w is None:
            return json.dumps({
                "status": str(log).upper() if log else "INFEASIBLE",
                "algorithm": alg, "weights": {}, "expected_return": None,
                "annual_volatility": None, "sharpe_ratio": None, "solver_log": str(log),
            })

        return json.dumps(_portfolio_result(tickers, w, mu, Sigma, alg,
                                            risk_free_rate=risk_free_rate,
                                            solver_log=str(log)))

    except Exception as e:
        return json.dumps({"status": "ERROR", "algorithm": algorithm, "error": str(e)})


def _markowitz_qp(mu, Sigma, max_weight, min_weight, target_return):
    """Core Markowitz QP shared by optimize_portfolio and optimize_by_algorithm."""
    import cvxpy as cp
    n = len(mu)
    w = cp.Variable(n)
    prob = cp.Problem(
        cp.Minimize(cp.quad_form(w, Sigma)),
        [cp.sum(w) == 1, w >= min_weight, w <= max_weight, mu @ w >= target_return],
    )
    prob.solve(solver=cp.CLARABEL, verbose=False)
    if prob.status not in ("optimal", "optimal_inaccurate"):
        return None, prob.status
    return w.value, f"CLARABEL Markowitz; obj={prob.value:.6f}"
