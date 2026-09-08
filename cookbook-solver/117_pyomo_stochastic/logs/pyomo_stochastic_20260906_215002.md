[persistence] workflow-id: bb7c9ffc-4007-405c-90f1-5b6dd2c2cda4
[persistence] backend=sqlite  workflow-id=bb7c9ffc-4007-405c-90f1-5b6dd2c2cda4
[kernel-store] db=~/.spl/workflows.db
INFO:spl.registry:Registry: loaded 3 workflow(s) from cookbook-solver/117_pyomo_stochastic/pyomo_stochastic.spl
Registry: ['pyomo_stochastic', 'solver_off_llm_sp', 'solver_on_sp']
INFO:spl.executor:HITL tools registered: wait_for_approval / send_approval
Auto-loaded 97 tool(s) from cookbook-solver/117_pyomo_stochastic/tools.py
Running workflow: pyomo_stochastic(['use_solver', 'model'])
[INFO] [r117] pyomo_stochastic start
INFO:spl.composer:CALL solver_on_sp(['problem_json']) INTO @report
INFO:spl.executor:ASSERT (kernel-store) sp_optimal('{"status": "optimal", "order_qty": 200, "expected_cost": 1360.0, "per_scenario": [{"scenario": "pessimistic", "demand": 100, "probability": 0.3, "order": 200, "shortage": 0, "excess": 100, "scenario_cost": 1200, "weighted_cost": 360.0}, {"scenario": "nominal", "demand": 200, "probability": 0.5, "order": 200, "shortage": 0, "excess": 0, "scenario_cost": 1000, "weighted_cost": 500.0}, {"scenario": "optimistic", "demand": 300, "probability": 0.2, "order": 200, "shortage": 100, "excess": 0, "scenario_cost": 2500, "weighted_cost": 500.0}], "solver": "glpk", "costs": {"order": 5, "shortage": 15, "holding": 2}}') -> True
[INFO] [r117] SP optimal: Q*=200, E[cost]=$1360.0
INFO:spl.executor:GENERATE segment 1 (explain_sp_result_prompt) -> 383 tokens, 13229ms
INFO:spl.executor:GENERATE chain done -> @explanation (1534 chars total)
INFO:spl.executor:RETURN: 3193 chars | status=complete
INFO:spl.composer:CALL solver_on_sp completed: status=complete in 14512ms (1 LLM calls)
INFO:spl.executor:RETURN: 3193 chars | status=complete, use_solver=true

Status:  complete
Output:  === Two-Stage Stochastic Programming (r117) | solver=ON ===

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
## Two-Stage Stochastic Programming: Plain-Language Explanation

**1. What it means**
You make one irreversible decision (order quantity) before uncertainty resolves, then reality hits and you pay the consequences. The solver finds the single order that minimizes expected pain across all possible futures — not just the most likely one.

**2. Why Q=200, not Q=190**
Shortages cost $15/unit; overstock costs only $2/unit — a 7.5× asymmetry. The critical ratio (83%) tells you: stock enough to cover demand in 83% of scenarios. The pessimistic scenario (100 units demand) has only 30% probability, so the solver accepts excess inventory there to avoid the brutal shortage penalty in the optimistic scenario. Ordering the average (190) is wrong precisely because averages ignore penalty asymmetry.

**3. VSS = $49**
This is the price of ignoring uncertainty. A manager who orders naively at the mean demand spends $49 more per season. Small here — but on 10,000 SKUs, that's $490,000 in preventable cost. VSS quantifies why stochastic modeling earns its complexity.

**4. The pattern appears everywhere**
- **Energy dispatch**: commit generation capacity before knowing load
- **Clinical trials**: allocate patients before knowing treatment response rates
- **Financial hedging**: buy options before knowing interest rate moves
- **Supply chain**: reserve factory capacity before knowing holiday demand

The unifying insight: when penalties are asymmetric and decisions are irreversible, optimize for the distribution — not the average.
LLM calls: 1  Latency: 15100ms
Log:     /home/papagame/.spl/logs/pyomo_stochastic-claude_cli-claude-sonnet-4-6-20260906-215126.md
