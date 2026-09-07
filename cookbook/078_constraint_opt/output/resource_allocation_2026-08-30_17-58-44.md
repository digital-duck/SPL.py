# Resource Allocation Report

**Problem:** An IT department must select a portfolio of projects for next quarter. Ten candidate projects are available. Project P1 costs $80K and requires 2 developer-months, delivering strategic value 6. Project P2 costs $120K and requires 3 developer-months, delivering value 9. Project P3 costs $60K and requires 2 developer-months, delivering value 5. Project P4 costs $150K and requires 4 developer-months, delivering value 11. Project P5 costs $200K and requires 5 developer-months, delivering value 12. Project P6 costs $90K and requires 2 developer-months, delivering value 7. Project P7 costs $110K and requires 3 developer-months, delivering value 8. Project P8 costs $70K and requires 2 developer-months, delivering value 5. Project P9 costs $180K and requires 4 developer-months, delivering value 13. Project P10 costs $100K and requires 3 developer-months, delivering value 6. The total budget is $600K and the team has 15 developer-months available. Each project is either fully funded or not - no partial investment. Select which projects to fund to maximize total strategic value.

**Solver status:** `Optimal`
**Maximum portfolio value:** 45

**Selected projects:**
  ✓ y_P2
  ✓ y_P3
  ✓ y_P4
  ✓ y_P6
  ✓ y_P9

**Rejected projects:**
  ✗ y_P1
  ✗ y_P10
  ✗ y_P5
  ✗ y_P7
  ✗ y_P8

## Interpretation

**Selected portfolio:** P2, P3, P4, P6, and P9 — delivering a combined strategic value of **45 points**, the maximum achievable under the given constraints.

**Resource utilization:**
- Budget consumed: **$600K of $600K** (100% utilized)
- Developer-months consumed: **15 of 15** (100% utilized)

Both constraints are fully saturated, leaving zero slack for mid-quarter additions.

**What was excluded and why:**
- **P5** ($200K, 5 dev-months, value 12) — too costly and headcount-intensive relative to its value; its inclusion would require removing more value than it contributes.
- **P7** ($110K, 3 dev-months, value 8) — any swap to include P7 in place of a lower-value project pushes the budget over $600K.
- **P1, P8, P10** — individually modest value; no combination fits within the remaining slack once the core five are selected.

**Strategic observation:** This portfolio sits exactly on both constraint boundaries — a brittle position. If leadership can authorize even a **$20K budget increase**, swapping P3 (value 5, $60K) for P1 (value 6, $80K) yields one additional value point at the same headcount. A $110K increase unlocks the P3→P7 swap for three additional points, though that also requires one extra developer-month.

---

## Solution Verification

**Step 1 — Cost check (Budget ≤ $600K)**

| Project | Cost |
|---------|------|
| P2 | $120K |
| P3 | $60K |
| P4 | $150K |
| P6 | $90K |
| P9 | $180K |

$120K + $60K + $150K + $90K + $180K = **$600K** ✓ (exactly at limit, does not exceed $600K)

**Step 2 — Headcount check (Developer-months ≤ 15)**

| Project | Dev-months |
|---------|-----------|
| P2 | 3 |
| P3 | 2 |
| P4 | 4 |
| P6 | 2 |
| P9 | 4 |

3 + 2 + 4 + 2 + 4 = **15 dev-months** ✓ (exactly at limit, does not exceed 15)

**Step 3 — Value sum**

| Project | Value |
|---------|-------|
| P2 | 9 |
| P3 | 5 |
| P4 | 11 |
| P6 | 7 |
| P9 | 13 |

9 + 5 + 11 + 7 + 13 = **45** ✓ Matches the solver's reported objective of 45.0.

**Step 4 — Rejected alternative: swap P3 → P7**

P7 offers higher value (8 vs. 5) and the same developer-months (3 vs. 2, actually one more), so it appears attractive. Test:

- Remove P3: budget freed = $60K, dev-months freed = 2
- Add P7: budget required = $110K, dev-months required = 3
- New total cost: $600K − $60K + $110K = **$620K > $600K** ✗ Budget violated.

The swap fails on cost alone, confirming P3 cannot be displaced by P7 without additional funding. The solver's exclusion of P7 is correct.

**Conclusion:** The solver's solution is verified. Total value = **45**, within budget ($600K = $600K), within headcount (15 = 15), and no alternative swap improves the score without violating a constraint.

## Solver Code (LLM-generated, PuLP)

```python
projects = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"]
cost     = {"P1": 80, "P2": 120, "P3": 60, "P4": 150, "P5": 200, "P6": 90, "P7": 110, "P8": 70, "P9": 180, "P10": 100}
devmos   = {"P1": 2,  "P2": 3,   "P3": 2,  "P4": 4,   "P5": 5,   "P6": 2,  "P7": 3,   "P8": 2,  "P9": 4,   "P10": 3}
value    = {"P1": 6,  "P2": 9,   "P3": 5,  "P4": 11,  "P5": 12,  "P6": 7,  "P7": 8,   "P8": 5,  "P9": 13,  "P10": 6}
budget   = 600
capacity = 15

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
| Stage 1 — formulation + solve (s) | 10.70 |
| Stage 2 — interpretation (s) | 46.70 |
| Total latency (s) | 57.90 |
| Input tokens | 1,263 |
| Output tokens | 914 |
| Total tokens | 2,177 |