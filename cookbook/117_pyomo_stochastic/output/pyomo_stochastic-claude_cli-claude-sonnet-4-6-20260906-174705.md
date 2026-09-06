# SPL Run: pyomo_stochastic

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 33 in / 0 out
- **Latency:** 16474ms
- **Timestamp:** 2026-09-06 17:47:05

## Output

```output
=== Two-Stage Stochastic Programming (r117) | solver=ON ===

## Two-Stage Stochastic Programming — Inventory Stocking

**Solver:** Pyomo + glpk  
**Status:** optimal

### Stage 1 Decision

| Method | Order Quantity | Expected Cost | vs. Optimum |
|---|---|---|---|
| **Pyomo stochastic optimum** | **200 units** | **$1,360** | — |
| EV baseline (order E[demand]) | 190 units | $1,409 | +$49 worse |

> **Value of the Stochastic Solution (VSS) = $49**
> Ordering the expected demand instead of Q* costs $49 more
> because the asymmetric penalties (shortage=$15/unit >> holding=$2/unit) push the optimal quantity above the mean.

### Per-Scenario Breakdown (Stochastic Optimum)

| Scenario | Demand | Prob | Shortage | Excess | Scenario Cost | Weighted |
|---|---|---|---|---|---|---|
| pessimistic | 100 | 0.3 | 0 | 100 | $1,200 | $360.0 |
| nominal | 200 | 0.5 | 0 | 0 | $1,000 | $500.0 |
| optimistic | 300 | 0.2 | 100 | 0 | $2,500 | $500.0 |

### Per-Scenario Breakdown (EV Baseline — order expected demand)

| Scenario | Demand | Prob | Shortage | Excess | Scenario Cost | Weighted |
|---|---|---|---|---|---|---|
| pessimistic | 100 | 0.3 | 0 | 90 | $1,130 | $339.0 |
| nominal | 200 | 0.5 | 10 | 0 | $1,100 | $550.0 |
| optimistic | 300 | 0.2 | 110 | 0 | $2,600 | $520.0 |

### Critical Ratio Insight

The optimal Q* satisfies: **P(demand ≤ Q*) = (c_shortage − c_order) / (c_shortage + c_holding)**
= (15 − 5) / (15 + 2) = **0.833**

This means: stock enough to satisfy demand in **83.3% of scenarios** — much higher than the 50th percentile, because shortages cost 7.5× more than overstock.

── Operations Research Explanation ─────────────────────────
## Two-Stage Stochastic Programming: Plain English

**1. What it means**
You make one irreversible decision *now* (order quantity), then nature reveals demand, and you pay the consequences *later* (shortage penalties or holding costs). The model optimizes that first decision by averaging across all possible futures, weighted by probability.

**2. Why Q=200, not 190**
Ordering the average demand ignores the *asymmetry* of your penalties. Running short costs $15/unit; sitting on excess costs only $2. The critical ratio formula tells you to cover demand in **83% of scenarios** — well above the 50th percentile. Demand of 200 is exactly the 80th percentile here, which is the closest feasible point to that 83% threshold. Ordering less means accepting frequent, expensive shortfalls that dwarf the savings from carrying less inventory.

**3. The VSS = $49**
It's the cost of *ignoring* uncertainty — what you pay by naively ordering the average. Small here, but in higher-stakes settings (millions of units, volatile demand) this gap widens dramatically. VSS is your business case for building a stochastic model instead of using a spreadsheet average.

**4. The pattern appears everywhere**
- **Energy dispatch**: commit power plant capacity before load is known
- **Clinical trials**: enroll patients before interim results arrive
- **Financial hedging**: buy options before volatility resolves
- **Supply chain**: place supplier contracts before retailer orders confirm

The common thread: an irreversible commitment under uncertainty, with asymmetric upside/downside — exactly where stochastic programming earns its keep.
```
