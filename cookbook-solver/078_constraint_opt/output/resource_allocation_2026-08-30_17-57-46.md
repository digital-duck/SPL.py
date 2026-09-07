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

**Selected portfolio:** P1, P2, P4, and P6 are funded, delivering a combined strategic value of **28 points** — the maximum achievable under the given constraints.

**Resource utilization:** The portfolio costs **$440K against a $500K budget** (88% utilized, $60K unspent) and consumes exactly **10 of 10 developer-months** — the team is fully staffed to capacity.

**What was left out and why:** P3 (value 10, $200K, 5 dev-months) is the highest-value excluded project, but it is headcount-constrained, not budget-constrained. Even with $60K in budget headroom, there is no developer capacity left. P5 (value 4) was a straightforward exclusion — low value relative to cost and an inefficient use of scarce developer-months.

**Strategic observation:** The binding constraint is headcount, not budget. The $60K unspent budget is essentially stranded. If leadership can source even two additional developer-months — via contractors, temporary staff, or re-prioritization from BAU — P3 becomes worth revisiting in combination with dropping either P2 or P6 to free both budget and capacity. However, that swap would reduce total value (P3 alone scores 10; P2+P6 together score 11), so the business case for P3 would need to rest on non-quantified factors such as strategic fit or technical foundation for future quarters.

---

## Solution Verification

**Step 1 — Cost constraint**

Selected projects: P1 ($120K), P2 ($80K), P4 ($150K), P6 ($90K)

$$120 + 80 + 150 + 90 = 440$$

$440K ≤ $500K budget. **Constraint satisfied.**

**Step 2 — Headcount constraint**

Developer-months: P1 (3), P2 (2), P4 (3), P6 (2)

$$3 + 2 + 3 + 2 = 10$$

10 ≤ 10 developer-months available. **Constraint satisfied (exactly at limit).**

**Step 3 — Portfolio value**

Strategic value: P1 (8), P2 (5), P4 (9), P6 (6)

$$8 + 5 + 9 + 6 = 28$$

**Total value: 28 points.**

**Step 4 — Rejected alternative: swap P4 for P3**

Suppose the team considered replacing P4 (value 9) with P3 (value 10), reasoning that P3 scores one point higher:

Resulting portfolio: P1, P2, P3, P6

- Cost: $120K + $80K + $200K + $90K = **$490K ≤ $500K** ✓ (budget holds)
- Dev-months: 3 + 2 + 5 + 2 = **12 > 10** ✗ (headcount violated by 2 months)

This portfolio is **infeasible**. P3's 5 dev-months cannot be accommodated alongside P1, P2, and P6 within the 10-month cap. The solver correctly rejected it.

**Step 5 — Confirm solver output**

The solver reports `"objective": 28.0`. Our manual arithmetic yields the same figure: 8 + 5 + 9 + 6 = **28**. The reported optimum is **confirmed correct.**

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
| Stage 1 — formulation + solve (s) | 8.70 |
| Stage 2 — interpretation (s) | 47.10 |
| Total latency (s) | 56.50 |
| Input tokens | 1,100 |
| Output tokens | 846 |
| Total tokens | 1,946 |