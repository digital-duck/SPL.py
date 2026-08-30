# Recipe 99 — Portfolio Optimization (cvxpy / Markowitz)

Given a capital amount and a pool of stock candidates, find the minimum-risk allocation  
that achieves a target annual return — using the classic Markowitz mean-variance model.

**Personal use**: run it monthly with fresh data to get rebalancing signals.  
**DODA**: same `.spl` spec runs on any adapter (ollama for exploration, claude_cli for production).

## What it demonstrates

| Axis | solver=ON | solver=OFF |
|---|---|---|
| Engine | cvxpy (CLARABEL interior-point QP) | LLM heuristic allocation |
| Guarantee | Globally optimal convex solution | Plausible weights, may violate constraints |
| Verification | `ASSERT` on cvxpy status | `verify_portfolio` back-substitution |
| Solver class | C3 (Convex optimization) | — |

## Default problem

```
Tickers: AAPL, MSFT, GOOGL, AMZN, NVDA
Capital: $10,000
Period: 1y (trailing 1-year history)
Target return: 12% annual
Max single position: 40%
```

## Run commands

```bash
# solver=ON, claude_cli — fetch live data + optimize
spl3 run cookbook/99_portfolio_opt/portfolio_opt.spl \
  --adapter claude_cli \
  --param use_solver=ON \
  --param tickers="AAPL,MSFT,GOOGL,AMZN,NVDA" \
  --param capital=10000 \
  --param period=1y \
  --param target_return=0.12 \
  --param max_weight=0.40

# solver=OFF, ollama/gemma3 — LLM heuristic (no market data fetch needed but still runs)
spl3 run cookbook/99_portfolio_opt/portfolio_opt.spl \
  --adapter ollama -m gemma3 \
  --param use_solver=OFF \
  --param tickers="AAPL,MSFT,GOOGL,AMZN,NVDA" \
  --param capital=10000 \
  --param period=1y \
  --param target_return=0.12 \
  --param max_weight=0.40
```

## Adaptive use

Run monthly (or after major market moves) to get fresh rebalancing signals:

```bash
# Swap tickers or capital as needed — the spec never changes
spl3 run cookbook/99_portfolio_opt/portfolio_opt.spl \
  --adapter claude_cli \
  --param use_solver=ON \
  --param tickers="AAPL,MSFT,NVDA,TSLA,META,BRK-B" \
  --param capital=25000 \
  --param period=6mo \
  --param target_return=0.15 \
  --param max_weight=0.35
```

## TOOL_API reference

| Function | Purpose |
|---|---|
| `fetch_stock_data(tickers, period)` | yfinance → annual returns + covariance matrix |
| `optimize_portfolio(data, target_return, max_weight, min_weight)` | cvxpy Markowitz QP |
| `allocate_capital(optimization_json, capital)` | Weights → dollar amounts |
| `verify_portfolio(optimization_json)` | Checks sum=1, bounds, non-negative return |

## Optimization formulation

```
Minimize    w' Σ w                (portfolio variance)
Subject to  μ' w ≥ target_return  (return constraint)
            1' w = 1              (fully invested)
            0 ≤ w_i ≤ max_weight  (long only, position limit)
```

where `μ` = vector of historical annual returns, `Σ` = historical annual covariance matrix.

## Verification (solver=OFF)

`verify_portfolio` checks:
1. **Budget**: sum of weights ≈ 1.0 (within 2%)
2. **Long-only**: no negative weights
3. **Position limit**: no weight exceeds `max_weight`
4. **Sanity**: expected return and volatility are non-negative

## Output metadata

The `RETURN` statement surfaces:
- `objective = @sharpe_str` — Sharpe ratio of the optimal portfolio
- `verify = @verify_status` — PASS / FAIL / N/A

## Disclaimer

Past performance does not guarantee future results. This recipe is for educational  
and personal exploration purposes only — not financial advice.

## Related recipes

- Recipe 78: LP / MILP via PuLP (linear & integer programs)
- Recipe 98: Job-shop scheduling via OR-Tools CP-SAT (constraint programming)
