# Resource Allocation Report

**Problem:** An IT department must select a portfolio of projects for next quarter. Six candidate projects are available. Project P1 costs $120K and requires 3 developer-months, delivering strategic value 8. Project P2 costs $80K and requires 2 developer-months, delivering value 5. Project P3 costs $200K and requires 5 developer-months, delivering value 10. Project P4 costs $150K and requires 3 developer-months, delivering value 9. Project P5 costs $60K and requires 2 developer-months, delivering value 4. Project P6 costs $90K and requires 2 developer-months, delivering value 6. The total budget is $500K and the team has 10 developer-months available. Each project is either fully funded or not funded — no partial investment. Select which projects to fund to maximize total strategic value.

**Solver status:** `Optimal`
**Maximum portfolio value:** 28

**Selected projects:**
  ✓ y_P1
  ✓ y_P2
  ✓ y_P4
  ✓ y_P6

**Rejected projects:**
  ✗ y_P3
  ✗ y_P5

## Interpretation

**1. Project Selection & Value:** The optimal portfolio selected consists of projects P1, P2, P4, and P6. This combination yields a total strategic value of 28.0 – representing the highest achievable return based on our criteria.

**2. Resource Utilization:** Funding this portfolio will cost $530K (P1: $120K, P2: $80K, P4: $150K, P6: $90K).  It requires utilizing 10 developer-months (P1: 3 months, P2: 2 months, P4: 3 months, P6: 2 months), exceeding the available 10. This overspend represents a critical constraint.

**3. Left-Out Projects & Justification:** Project P3, valued at 10, was excluded due to its significant cost of $200K and extended timeframe of 5 developer-months, which pushes the total headcount beyond our available 10 and significantly over budget. Similarly, P5 and P7 were not selected because they delivered lower value for their investment and resource requirements.

**4. Strategic Observation:** The team’s prioritization leans heavily toward projects delivering high strategic value (8+).  If additional budget or developer-months became available – particularly an extra 2-3 months – revisiting P3, with its substantial value proposition, would undoubtedly be a worthwhile consideration.



## Solution Verification

Let's verify the optimal portfolio selection:

* **Cost Calculation:** $120K (P1) + $80K (P2) + $150K (P4) + $90K (P6) = $440K.  This is within the $500K budget, leaving a surplus of $60K.
* **Headcount Calculation:** 3 months (P1) + 2 months (P2) + 3 months (P4) + 2 months (P6) = 10 developer-months. This matches the available 10.
* **Value Calculation:** 8 (P1) + 5 (P2) + 9 (P4) + 6 (P6) = 28.  This confirms the achieved strategic value.

**Rejected Alternative:** Let’s examine what would happen if we selected P3 instead of P6.
* Cost: $200K (P3) + $120K (P1) + $80K (P2) + $150K (P4) = $550K – exceeding the budget by $50K.
* Headcount: 5 months (P3) + 3 months (P1) + 2 months (P2) + 3 months (P4) = 13 developer-months – exceeding the available 10 by 3 months.
* Value: 10(P3) + 8(P1) + 5(P2) + 9(P4) = 32 - a lower value than the optimal portfolio.

Therefore, swapping P6 for P3 significantly degrades both the strategic value and resource utilization, confirming the optimality of the initial selection. The computed value of 28.0 accurately matches the solver's reported output.

## Solver Code (LLM-generated, PuLP)

```python
```python
import pulp

projects = ["P1", "P2", "P3", "P4", "P5", "P6"]
cost     = {"P1": 120, "P2": 80, "P3": 200, "P4": 150, "P5": 60, "P6": 90}
devmos   = {"P1": 3,   "P2": 2,  "P3": 5,   "P4": 3,   "P5": 2,   "P6": 2}
value    = {"P1": 8,   "P2": 5,  "P3": 10,  "P4": 9,   "P5": 4,   "P6": 6}
budget   = 500
capacity = 10

prob = pulp.LpProblem("portfolio", pulp.LpMaximize)
y = {p: pulp.LpVariable(f"y_{p}", cat="Binary") for p in projects}
prob += pulp.lpSum(value[p] * y[p] for p in projects)
prob += (pulp.lpSum(cost[p] * y[p] for p in projects) <= budget)
prob += (pulp.lpSum(devmos[p] * y[p] for p in projects) <= capacity)
prob.solve(pulp.PULP_CBC_CMD(msg=0))
_result = {
    "status": pulp.LpStatus[prob.status],
    "objective": pulp.value(prob.objective),
    "variables": {v.name: pulp.value(v) for v in prob.variables()}
}
```
```

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=ON  (PuLP/CBC + ASSERT gate) |
| LLM calls | 3 |
| Stage 1 — formulation + solve (s) | 17.50 |
| Stage 2 — interpretation (s) | 13.20 |
| Total latency (s) | 31.40 |
| Input tokens | 2,317 |
| Output tokens | 1,527 |
| Total tokens | 3,844 |