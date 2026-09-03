# Markowitz Portfolio Optimization — Deep Dive

How the math works, how cvxpy implements it, and what alternatives exist.

---

## 1 — The Markowitz Framework

### Core Idea

Harry Markowitz (1952) showed that portfolio construction is a two-dimensional problem: **expected return** and **risk (variance)**. You don't just pick the highest-return stocks — you pick the combination of stocks that minimizes variance for a given return target. The mathematical insight is that correlations between assets matter as much as individual returns.

### Step 1 — Measure the Ingredients

From historical daily prices, `fetch_stock_data` computes two quantities for each stock universe:

**Expected annual return vector μ:**
```
μᵢ = mean(daily_returnsᵢ) × 252
```
252 = NYSE trading days per year. This is the annualized mean return for stock i.

**Annual covariance matrix Σ:**
```
Σᵢⱼ = cov(daily_returnsᵢ, daily_returnsⱼ) × 252
```
Σ is an N×N matrix. The diagonal Σᵢᵢ is the variance of stock i. Off-diagonal Σᵢⱼ captures how stocks i and j move together:
- Σᵢⱼ > 0 → move in the same direction → less diversification
- Σᵢⱼ < 0 → move in opposite directions → strong diversification benefit
- Σᵢⱼ ≈ 0 → uncorrelated → moderate diversification benefit

### Step 2 — The Optimization Problem

Given weight vector **w** (fraction of capital in each stock), the portfolio metrics are:

```
Portfolio return    = μᵀ w          (weighted average of stock returns)
Portfolio variance  = wᵀ Σ w        (quadratic form — the risk)
Portfolio std dev   = √(wᵀ Σ w)     (volatility, annualized)
```

Markowitz formulates this as a **Quadratic Program (QP)**:

```
Minimize    wᵀ Σ w                     ← minimize risk

Subject to  μᵀ w ≥ target_return       ← hit the return target
            Σ wᵢ = 1                   ← fully invested (100%)
            wᵢ ≥ 0                     ← long only, no short selling
            wᵢ ≤ max_weight            ← position limit (e.g. 40%)
```

This is a **convex** optimization problem — the objective `wᵀ Σ w` is a convex quadratic (Σ is positive semi-definite), and all constraints are linear. Convexity guarantees a unique global optimum.

### Step 3 — Output Metrics

From the solved weights w*:

| Metric | Formula | Meaning |
|---|---|---|
| Expected return | `μᵀ w*` | Annualized portfolio return |
| Volatility | `√(w*ᵀ Σ w*)` | Annualized standard deviation |
| Sharpe ratio | `(return − Rf) / volatility` | Return per unit of risk; Rf = risk-free rate (e.g. 5%) |

**Sharpe ratio** is the key quality metric. A Sharpe > 1.0 is considered good; > 2.0 is excellent.

### The Efficient Frontier

If you solve the QP across a sweep of target returns from min to max, you trace the **efficient frontier** — the set of portfolios that maximize return for each level of risk. Every point above this frontier is unachievable; every point below it is suboptimal (same risk, less return).

```
Return ▲
       │              * Efficient Frontier
       │           ***
       │        ***
       │     ***
       │   **
       │  *
       └──────────────────► Risk (volatility)
```

---

## 2 — cvxpy Tutorial

[cvxpy](https://www.cvxpy.org) is a Python DSL for convex optimization. You express the problem symbolically; cvxpy handles the solver interface.

### Installation

```bash
pip install cvxpy yfinance numpy
```

### Minimal Markowitz Example

```python
import cvxpy as cp
import numpy as np

# Inputs (annualized)
mu    = np.array([0.12, 0.18, 0.09, 0.22])   # expected returns for 4 stocks
Sigma = np.array([                             # covariance matrix
    [0.04, 0.01, 0.005, 0.02],
    [0.01, 0.09, 0.003, 0.03],
    [0.005, 0.003, 0.025, 0.01],
    [0.02, 0.03, 0.01, 0.16],
])

n = len(mu)
target_return = 0.12
max_weight    = 0.40

# Decision variable: portfolio weights
w = cp.Variable(n)

# Objective: minimize portfolio variance
portfolio_variance = cp.quad_form(w, Sigma)

# Constraints
constraints = [
    cp.sum(w) == 1,          # fully invested
    w >= 0,                  # long only
    w <= max_weight,         # position limit
    mu @ w >= target_return, # return target
]

# Solve
problem = cp.Problem(cp.Minimize(portfolio_variance), constraints)
problem.solve(solver=cp.CLARABEL)

print("Status:   ", problem.status)
print("Weights:  ", w.value.round(4))
print("Return:   ", float(mu @ w.value))
print("Volatility:", float(np.sqrt(w.value @ Sigma @ w.value)))
```

### Key cvxpy Concepts

| Concept | What it does |
|---|---|
| `cp.Variable(n)` | Creates n decision variables (the weights) |
| `cp.quad_form(w, Sigma)` | Computes wᵀΣw — requires Σ to be PSD |
| `cp.Problem(objective, constraints)` | Assembles the problem |
| `problem.solve(solver=cp.CLARABEL)` | CLARABEL is a modern interior-point solver; also try `cp.SCS`, `cp.OSQP` |
| `problem.status` | "optimal", "infeasible", "unbounded" |
| `w.value` | Optimal weights as numpy array (available after solve) |

### Common Extensions

```python
# Maximize Sharpe ratio (non-convex — use a trick: fix return=1, minimize risk)
# Standard approach: parametric sweep over target_return values

# Add a minimum position size (e.g. at least 5% if holding)
# This requires a binary variable → Mixed-Integer QP
z = cp.Variable(n, boolean=True)
constraints += [w >= 0.05 * z, w <= max_weight * z]

# L2 regularization to penalize concentrated positions
lam = 0.1
objective = cp.Minimize(portfolio_variance + lam * cp.sum_squares(w))

# Turnover constraint (limit rebalancing cost)
w_prev = np.array([0.25, 0.25, 0.25, 0.25])
max_turnover = 0.20
constraints += [cp.norm(w - w_prev, 1) <= max_turnover]
```

### Solver Choice

| Solver | Best for | Notes |
|---|---|---|
| `CLARABEL` | QP (default choice) | Modern, robust, open-source |
| `OSQP` | Large sparse QP | Fast, good for rebalancing |
| `SCS` | Large-scale, warm-starting | Less accurate but scalable |
| `MOSEK` | Production-grade, all cones | Commercial, free academic license |
| `GUROBI` | MIQP (binary variables) | Commercial, fast |

---

## 3 — Alternative Portfolio Optimization Algorithms

### 3.1 Minimum Variance Portfolio

A special case of Markowitz — drop the return constraint entirely and just minimize variance. Tends to produce very concentrated portfolios but is robust to return estimation error (since μ estimates are noisy).

```python
# No return constraint
problem = cp.Problem(cp.Minimize(cp.quad_form(w, Sigma)), [cp.sum(w)==1, w>=0, w<=max_weight])
```

**Use when:** you trust Σ but distrust μ estimates; good for defensive, low-volatility portfolios.

### 3.2 Maximum Sharpe Ratio

Maximize `(μᵀw − Rf) / √(wᵀΣw)`. This is non-convex as written, but can be converted to a convex QP via the Dinkelbach / Charnes-Cooper change of variables:

```
Let y = w / (μᵀw − Rf)
Minimize  yᵀ Σ y
Subject to  μᵀ y − Rf · 1ᵀ y = 1
            y ≥ 0
Then recover w = y / sum(y)
```

**Use when:** you want the single best risk-adjusted portfolio on the efficient frontier (the "tangency portfolio").

### 3.3 Black-Litterman

A Bayesian extension of Markowitz. Instead of using raw historical μ, it blends:
- **Prior**: return implied by market-cap weights (CAPM equilibrium)
- **Views**: investor's explicit beliefs, e.g. "I think MOS will outperform by 5%"

The posterior μ_BL is fed into the standard Markowitz QP. Key advantage: avoids the "garbage in, garbage out" problem where noisy historical returns dominate the solution.

```python
# Pseudo-code
tau = 0.05                           # uncertainty scaling
Pi = risk_aversion * Sigma @ w_mkt  # implied equilibrium returns
P = view_pick_matrix                 # which assets your views cover
Q = view_returns                     # your expected outperformance
Omega = tau * P @ Sigma @ P.T        # view uncertainty
mu_bl = np.linalg.inv(np.linalg.inv(tau * Sigma) + P.T @ np.linalg.inv(Omega) @ P) \
        @ (np.linalg.inv(tau * Sigma) @ Pi + P.T @ np.linalg.inv(Omega) @ Q)
# Then run standard Markowitz QP with mu_bl instead of raw mu
```

**Use when:** you have strong conviction views on specific stocks (like MOS/EWZ); this is the institutional standard.

### 3.4 Risk Parity

Each stock contributes **equally** to total portfolio risk. Instead of equal weights (naïve 1/N), it weights inversely proportional to volatility — low-volatility assets get larger allocations.

```python
# Risk contribution of asset i = wᵢ × (Σw)ᵢ / (wᵀΣw)
# Goal: make all risk contributions equal → wᵢ(Σw)ᵢ = constant for all i
# This is a non-linear system; solve iteratively or via cvxpy with log-barrier
```

**Use when:** you want diversification by risk budget, not by capital — common in multi-asset portfolios (stocks + bonds + commodities).

### 3.5 Hierarchical Risk Parity (HRP)

Developed by Marcos Lopez de Prado (2016). Uses **hierarchical clustering** on the correlation matrix instead of inverting Σ. Avoids the numerical instability of matrix inversion with small N or short history.

```python
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform

corr = daily_ret.corr()
dist = np.sqrt(0.5 * (1 - corr))       # correlation → distance
link = linkage(squareform(dist), 'single')
# Recursively bisect clusters, allocate inverse-variance within each leaf
```

**Use when:** fewer than ~20 stocks or short history (< 2 years) where Σ inversion is unstable; also more robust out-of-sample than Markowitz.

### 3.6 CVaR Optimization (Tail Risk)

Instead of minimizing variance, minimize **Conditional Value at Risk** — the expected loss in the worst α% of scenarios. More robust to fat-tailed return distributions (which stocks exhibit in practice).

```python
import cvxpy as cp
import numpy as np

alpha = 0.05   # 5% worst cases
T = len(returns_matrix)
z = cp.Variable(T)           # auxiliary loss variables
beta = cp.Variable()         # VaR threshold

# CVaR = VaR + (1/αT) Σ max(loss - VaR, 0)
cvar = beta + (1/(alpha * T)) * cp.sum(cp.pos(z))
constraints_cvar = [z >= -returns_matrix @ w - beta, z >= 0,
                    cp.sum(w) == 1, w >= 0, mu @ w >= target_return]
problem = cp.Problem(cp.Minimize(cvar), constraints_cvar)
```

**Use when:** downside risk matters more than symmetric variance — relevant for concentrated positions or during high-volatility regimes.

### Summary Comparison

| Algorithm | Input needed | Convex? | Robust to estimation error | Best for |
|---|---|---|---|---|
| Markowitz min-variance | μ, Σ | Yes (QP) | Medium | Classic baseline |
| Max Sharpe | μ, Σ, Rf | Convertible | Low (μ-sensitive) | Single optimal portfolio |
| Black-Litterman | μ, Σ, views | Yes (QP on μ_BL) | High | When you have stock views |
| Risk Parity | Σ only | Non-linear | High (no μ needed) | Multi-asset, defensive |
| HRP | Correlations only | N/A (clustering) | Very high | Small N, short history |
| CVaR | Return scenarios | Yes (LP/QP) | High | Tail-risk focus |

---

## Connection to MOS + EWZ

Running `optimize_portfolio` with `tickers="MOS,EWZ,..."` would:
1. Fetch μ and Σ for each stock historically
2. Discover whether MOS and EWZ have **low correlation** with typical tech stocks (AAPL, MSFT) — which they likely do, being commodity-driven
3. Assign them **larger weights** than their individual return would justify, purely because they reduce overall portfolio variance through diversification
4. This is precisely the mathematical expression of your intuition: "two different commodity plays that hedge each other and the broader market"

**Black-Litterman** would be especially appropriate here: you have explicit views ("MOS to $40", "EWZ to $50"), which can be encoded as Q (expected outperformance) and P (view matrix), blended with the market prior to produce a more stable μ_BL.
