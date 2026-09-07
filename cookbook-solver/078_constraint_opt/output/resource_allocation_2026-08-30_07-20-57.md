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

**Selected portfolio: P1, P2, P4, P6 — total strategic value of 28.**

The solver funds four projects: P1 (infrastructure/value 8), P2 (value 5), P4 (value 9), and P6 (value 6). This combination consumes **$440K of the $500K budget** (88% utilization) and **all 10 available developer-months** — the team is fully committed on headcount.

**Left out:** P3 and P5. P3 is the single highest-value project (10) but at $200K and 5 developer-months it cannot be added without violating both constraints simultaneously — budget would jump to $640K and headcount to 15. P5 (value 4) is the weakest project in the pool; even though it fits the budget, headcount is exhausted, and it would displace a higher-value project if forced in.

**Strategic observation:** P3 is the most tempting project on the table — highest absolute value, but poor resource efficiency (value 10 for 5 dev-months versus P4's value 9 for 3 dev-months). If leadership can secure **2 additional developer-months** and **~$60K in supplemental budget**, a revised portfolio including P3 in place of two lower-value projects warrants re-evaluation. Alternatively, if P3 can be scoped to 3 developer-months, it becomes competitive in the next planning cycle.

---

## Solution Verification

**Cost check:**

| Project | Cost |
|---------|------|
| P1 | $120K |
| P2 | $80K |
| P4 | $150K |
| P6 | $90K |
| **Total** | **$440K** |

$120K + $80K + $150K + $90K = **$440K ≤ $500K** ✓ ($60K budget remaining)

**Headcount check:**

| Project | Developer-months |
|---------|-----------------|
| P1 | 3 |
| P2 | 2 |
| P4 | 3 |
| P6 | 2 |
| **Total** | **10** |

3 + 2 + 3 + 2 = **10 ≤ 10** ✓ (headcount fully utilized, zero slack)

**Value check:**

8 (P1) + 5 (P2) + 9 (P4) + 6 (P6) = **28** — matches the solver's reported objective of 28.0 ✓

**Rejected alternative — swap P6 for P5:**

Remove P6 (value 6, $90K, 2 dev-months); add P5 (value 4, $60K, 2 dev-months).
- New cost: $440K − $90K + $60K = $410K ≤ $500K — budget satisfied, but...
- New value: 28 − 6 + 4 = **26 < 28** — strictly worse.

P5 is feasible but suboptimal; the solver correctly excludes it because P6 delivers 50% more value for only $30K more at identical headcount cost.

**Conclusion:** The solver's answer is correct and verified. The optimal portfolio value is **28**, achieved by P1 + P2 + P4 + P6 within all constraints.

## Solver Code (LLM-generated, PuLP)

```python
projects = {
    "P1": {"cost": 120, "devmonths": 3, "value": 8},
    "P2": {"cost": 80,  "devmonths": 2, "value": 5},
    "P3": {"cost": 200, "devmonths": 5, "value": 10},
    "P4": {"cost": 150, "devmonths": 3, "value": 9},
    "P5": {"cost": 60,  "devmonths": 2, "value": 4},
    "P6": {"cost": 90,  "devmonths": 2, "value": 6},
}

total_budget = 500
total_devmonths = 10

prob = pulp.LpProblem("project_portfolio", sense=pulp.LpMaximize)

y = {p: pulp.LpVariable(f"y_{p}", cat="Binary") for p in projects}

prob += pulp.lpSum(projects[p]["value"] * y[p] for p in projects)

prob += pulp.lpSum(projects[p]["cost"] * y[p] for p in projects) <= total_budget
prob += pulp.lpSum(projects[p]["devmonths"] * y[p] for p in projects) <= total_devmonths

prob.solve(pulp.PULP_CBC_CMD(msg=0))

_result = {
    "status": pulp.LpStatus[prob.status],
    "objective": pulp.value(prob.objective),
    "variables": {v.name: pulp.value(v) for v in prob.variables()},
}
```

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=ON  (PuLP/CBC + ASSERT gate) |
| LLM calls | 2 |
| Stage 1 — formulation + solve (s) | 8.90 |
| Stage 2 — interpretation (s) | 40.50 |
| Total latency (s) | 50.10 |
| Input tokens | 1,005 |
| Output tokens | 832 |
| Total tokens | 1,837 |