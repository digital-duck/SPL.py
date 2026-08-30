# Resource Allocation Report

**Problem:** An IT department must select a portfolio of projects for next quarter. Six candidate projects are available. Project P1 costs $120K and requires 3 developer-months, delivering strategic value 8. Project P2 costs $80K and requires 2 developer-months, delivering value 5. Project P3 costs $200K and requires 5 developer-months, delivering value 10. Project P4 costs $150K and requires 3 developer-months, delivering value 9. Project P5 costs $60K and requires 2 developer-months, delivering value 4. Project P6 costs $90K and requires 2 developer-months, delivering value 6. The total budget is $500K and the team has 10 developer-months available. Each project is either fully funded or not funded - no partial investment. Select which projects to fund to maximize total strategic value.

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

**1. Project Selection & Value:** The optimal portfolio selected projects P1, P2, P4, and P6. This delivers a total strategic value of 28.0 – representing the highest possible outcome given the constraints.

**2. Resource Utilization:**  The selected projects require a combined cost of $440K ($120K + $80K + $150K + $90K) and utilize 10 developer-months (3 + 2 + 3 + 2). This exceeds the available budget of $500K and fully utilizes the 10 developer-month capacity.

**3. Key Decisions & Justification:** Project P3, with a value of 10, was left out due to its high cost ($200K) and significant headcount requirement (5 developer-months).  This represents a substantial investment that pushes the portfolio beyond the budget limit. Similarly, while P5 and P6 offer valuable contributions at $60K and $90K respectively, their lower value scores didn’t justify the resource commitment in this scenario.

**4. Strategic Observation:** The selection prioritizes projects with high value-to-cost ratios. If the IT department were to increase its budget by approximately $60K (or acquire an additional developer-month), it could potentially include Project P3, significantly boosting the overall portfolio value to 28.  Exploring combinations leveraging higher-value projects at a slightly increased investment would be prudent.



## Solution Verification

Let’s verify this optimal solution:

* **Cost Calculation:** $120K (P1) + $80K (P2) + $150K (P4) + $90K (P6) = $440K ≤ $500K (Budget). This is correct.
* **Headcount Calculation:** 3 months (P1) + 2 months (P2) + 3 months (P4) + 2 months (P6) = 10 months ≤ 10 months (Available).  This is also correct.
* **Value Calculation:** 8 (P1) + 5 (P2) + 9 (P4) + 6 (P6) = 28.0. This confirms the optimal value.

**Rejected Alternative & Verification:** Let's consider swapping P3 for P5:

* Cost: $200K (P3) + $60K (P5) = $260K
* Headcount: 5 months (P3) + 2 months (P5) = 7 months
* Value: 10 (P3) + 4 (P5) = 14

This alternative produces a lower total value of 14 and utilizes 7 developer-months, exceeding the available capacity. Therefore, P3 was correctly excluded from the optimal portfolio.

* **Computed Value Confirmation:** The final calculated strategic value is indeed 28.0 - matching the JSON output.

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

print(_result)
```
```

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=ON  (PuLP/CBC + ASSERT gate) |
| LLM calls | 4 |
| Stage 1 — formulation + solve (s) | 26.50 |
| Stage 2 — interpretation (s) | 12.10 |
| Total latency (s) | 39.60 |
| Input tokens | 3,397 |
| Output tokens | 1,881 |
| Total tokens | 5,278 |