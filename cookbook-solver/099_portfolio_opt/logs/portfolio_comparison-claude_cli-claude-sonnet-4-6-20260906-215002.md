# SPL Run: portfolio_comparison

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 720 in / 797 out
- **Latency:** 33742ms
- **Timestamp:** 2026-09-06 21:50:02

## Output

```output
=== Cross-Algorithm Portfolio Comparison ===

Tickers: AAPL,MSFT,GOOGL,AMZN,NVDA  |  Period: 1y  |  Capital: $10000
Target return: 0.12  |  Max position: 0.20

Algorithm Summary (CSV):
algorithm,status,expected_return,annual_volatility,sharpe_ratio,AAPL,MSFT,GOOGL,AMZN,NVDA
markowitz,OPTIMAL,0.2724,0.2022,1.0998,0.2000,0.2000,0.2000,0.2000,0.2000
min_variance,OPTIMAL,0.2724,0.2022,1.0998,0.2000,0.2000,0.2000,0.2000,0.2000
max_sharpe,OPTIMAL,0.2724,0.2022,1.0998,0.2000,0.2000,0.2000,0.2000,0.2000
risk_parity,OPTIMAL,0.2724,0.2022,1.0998,0.2000,0.2000,0.2000,0.2000,0.2000
hrp,OPTIMAL,0.2706,0.1961,1.1245,0.2472,0.2387,0.1656,0.1390,0.2095
cvar,OPTIMAL,0.2724,0.2022,1.0998,0.2000,0.2000,0.2000,0.2000,0.2000

Portfolio Composition (CSV):
ticker,markowitz_wt%,min_variance_wt%,max_sharpe_wt%,risk_parity_wt%,hrp_wt%,cvar_wt%,markowitz_$,min_variance_$,max_sharpe_$,risk_parity_$,hrp_$,cvar_$
AAPL,20.00,20.00,20.00,20.00,24.72,20.00,2000,2000,2000,2000,2472,2000
MSFT,20.00,20.00,20.00,20.00,23.87,20.00,2000,2000,2000,2000,2387,2000
GOOGL,20.00,20.00,20.00,20.00,16.56,20.00,2000,2000,2000,2000,1656,2000
AMZN,20.00,20.00,20.00,20.00,13.90,20.00,2000,2000,2000,2000,1390,2000
NVDA,20.00,20.00,20.00,20.00,20.95,20.00,2000,2000,2000,2000,2095,2000

LLM Synthesis & Recommendation:
## Portfolio Optimization Comparison

### 1. Results Table

| Algorithm    | Ann. Return | Ann. Volatility | Sharpe Ratio | # Positions |
|-------------|-------------|-----------------|--------------|-------------|
| Markowitz   | 27.24%      | 20.22%          | 1.0998       | 5           |
| Min Variance| 27.24%      | 20.22%          | 1.0998       | 5           |
| Max Sharpe  | 27.24%      | 20.22%          | 1.0998       | 5           |
| Risk Parity | 27.24%      | 20.22%          | 1.0998       | 5           |
| **HRP**     | **27.06%**  | **19.61%**      | **1.1245**   | **5**       |
| CVaR        | 27.24%      | 20.22%          | 1.0998       | 5           |

### 2. Best Risk-Adjusted Return

**HRP** wins with Sharpe **1.1245** — 2.2% better than the five tied algorithms. It also delivers the lowest volatility at 19.61%, giving up only 18 bps of return.

### 3. Most Diversified Allocation

**HRP** is the only algorithm that produced non-trivial, risk-aware weights:

| Ticker | HRP Weight | Equal Weight |
|--------|-----------|--------------|
| AAPL   | 24.72%    | 20.00%       |
| MSFT   | 23.87%    | 20.00%       |
| NVDA   | 20.95%    | 20.00%       |
| GOOGL  | 16.56%    | 20.00%       |
| AMZN   | 13.90%    | 20.00%       |

This is economically sensible: AAPL has the lowest variance (σ²=0.063) in the covariance matrix, so HRP correctly tilts toward it. AMZN carries the highest variance (σ²=0.119) and high cross-correlations, so it gets underweighted.

### 4. Recommendation: **HRP**

HRP is the best choice for a personal investor. It is the only algorithm that actually leveraged the covariance structure of the data — all other solvers converged to the degenerate equal-weight solution (see §5). HRP improves both Sharpe and volatility simultaneously, and its hierarchical clustering approach is robust to estimation error in expected returns, which is notoriously unreliable over short windows. For a buy-and-hold personal investor who cannot continuously rebalance, robustness to parameter noise matters more than theoretical optimality.

### 5. Degenerate Results — Five Algorithms Failed

**Markowitz, Min Variance, Max Sharpe, Risk Parity, and CVaR all returned identical 20%/20%/20%/20%/20% weights.** This is a strong signal of a solver or constraint configuration problem — most likely the per-asset bounds were inadvertently set to `[0.20, 0.20]` (min = max = 0.20), forcing equal weight regardless of the objective. As a sanity check:

- **Min Variance** should underweight NVDA (σ²=0.146) and AMZN (σ²=0.119) in favor of AAPL (σ²=0.063).
- **Max Sharpe** should concentrate in GOOGL (42.4% return) and AAPL (33.4% return).
- **Risk Parity** should equalize risk contributions, which almost certainly does not equal capital-weight here.

These five results should be treated as **invalid** until the constraint configuration is audited.

---

> **Disclaimer:** Past performance does not guarantee future results. Expected returns, volatility, and Sharpe ratios are estimated from 1 year of historical data and are subject to significant estimation error. This analysis is for educational purposes and does not constitute investment advice.
```
