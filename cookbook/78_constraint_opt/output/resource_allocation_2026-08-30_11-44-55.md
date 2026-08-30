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

**Selected portfolio:** P1, P2, P4, and P6 — delivering a combined strategic value of **28 points** out of a maximum theoretically possible 42.

**Resource utilization:** The four funded projects consume **$440K of the $500K budget** (88%), leaving $60K unspent. On headcount, they consume exactly **10 of 10 developer-months** — the team is fully committed with zero capacity remaining.

**Projects left out:** P3 (value 10) and P5 (value 4) were excluded. P5 was blocked purely by headcount — no capacity remained even though $60K of budget was available. P3, despite being the single highest-value project, was excluded by a double constraint: adding it would require 5 developer-months (impossible on a full team) and $200K in additional cost, both of which are unavailable simultaneously.

**Strategic observation:** P3 deserves a second look for Q2. It is the highest-value project in the pipeline and was rejected on headcount grounds, not strategic merit. If leadership can secure one additional developer-month and $140K in incremental budget — by either swapping out P2 and converting headcount, or negotiating a budget supplement — P3 becomes fundable and would lift total portfolio value significantly.

---

## Solution Verification

**Cost check**

| Project | Cost |
|---------|------|
| P1 | $120K |
| P2 | $80K |
| P4 | $150K |
| P6 | $90K |
| **Total** | **$440K** |

$120K + $80K + $150K + $90K = **$440K ≤ $500K budget.** Constraint satisfied. $60K remains unspent.

**Headcount check**

| Project | Developer-months |
|---------|-----------------|
| P1 | 3 |
| P2 | 2 |
| P4 | 3 |
| P6 | 2 |
| **Total** | **10** |

3 + 2 + 3 + 2 = **10 ≤ 10 developer-months.** Constraint satisfied at exactly full capacity.

**Value check**

8 (P1) + 5 (P2) + 9 (P4) + 6 (P6) = **28 strategic value points.** This matches the solver's reported objective of 28.0.

**Rejected alternative — swap P2 out, swap P3 in**

A natural challenge to the optimizer: P3 scores 10 points versus P2's 5 points. Why not substitute?

- Remove P2: cost drops by $80K, headcount freed = 2 dev-months.
- Add P3: cost increases by $200K, headcount required = 5 dev-months.
- Net cost: $440K − $80K + $200K = **$560K > $500K.** Budget violated.
- Net headcount: 10 − 2 + 5 = **13 > 10.** Headcount violated.

The swap fails on both constraints simultaneously, and the portfolio value would only reach 33 if constraints were ignored — but since they cannot be, this configuration is infeasible. The optimizer's selection of 28 is confirmed as the best achievable result within the given constraints.

## Solver Code (LLM-generated, PuLP)

```python
projects = ["P1", "P2", "P3", "P4", "P5", "P6"]
cost     = {"P1": 120, "P2": 80, "P3": 200, "P4": 150, "P5": 60, "P6": 90}
devmos   = {"P1": 3,   "P2": 2,  "P3": 5,   "P4": 3,   "P5": 2,  "P6": 2}
value    = {"P1": 8,   "P2": 5,  "P3": 10,  "P4": 9,   "P5": 4,  "P6": 6}
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

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=ON  (PuLP/CBC + ASSERT gate) |
| LLM calls | 2 |
| Stage 1 — formulation + solve (s) | 8.80 |
| Stage 2 — interpretation (s) | 35.90 |
| Total latency (s) | 45.40 |
| Input tokens | 1,100 |
| Output tokens | 853 |
| Total tokens | 1,953 |