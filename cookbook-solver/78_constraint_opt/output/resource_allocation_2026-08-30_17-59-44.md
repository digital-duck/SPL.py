# Resource Allocation Report

**Problem:** An IT department must select a portfolio of projects for next year. Twenty candidate projects are available. Project P1 costs $80K/2mo/value 6. Project P2 costs $120K/3mo/value 9. Project P3 costs $60K/2mo/value 5. Project P4 costs $150K/4mo/value 11. Project P5 costs $200K/5mo/value 12. Project P6 costs $90K/2mo/value 7. Project P7 costs $110K/3mo/value 8. Project P8 costs $70K/2mo/value 5. Project P9 costs $180K/4mo/value 13. Project P10 costs $100K/3mo/value 6. Project P11 costs $130K/3mo/value 10. Project P12 costs $85K/2mo/value 6. Project P13 costs $160K/4mo/value 12. Project P14 costs $75K/2mo/value 5. Project P15 costs $220K/5mo/value 14. Project P16 costs $95K/3mo/value 7. Project P17 costs $140K/4mo/value 10. Project P18 costs $65K/2mo/value 5. Project P19 costs $170K/4mo/value 12. Project P20 costs $115K/3mo/value 8. Total budget $1000K, team capacity 25 developer-months. Each project fully funded or not. Maximize total strategic value.

**Solver status:** `Optimal`
**Maximum portfolio value:** 75

**Selected projects:**
  ✓ y_P1
  ✓ y_P11
  ✓ y_P13
  ✓ y_P18
  ✓ y_P2
  ✓ y_P20
  ✓ y_P3
  ✓ y_P6
  ✓ y_P9

**Rejected projects:**
  ✗ y_P10
  ✗ y_P12
  ✗ y_P14
  ✗ y_P15
  ✗ y_P16
  ✗ y_P17
  ✗ y_P19
  ✗ y_P4
  ✗ y_P5
  ✗ y_P7
  ✗ y_P8

## Interpretation

**Selected portfolio — 9 of 20 projects, total strategic value: 75**

The optimizer selects P1, P2, P3, P6, P9, P11, P13, P18, and P20. This portfolio delivers the maximum achievable strategic value of 75 points under the given constraints.

**Resource utilization is exact:** The portfolio consumes the full $1,000K budget and all 25 developer-months. Both constraints are simultaneously binding — there is zero slack in either dimension. This is a tight, efficient fit with no wasted capacity.

**Notable exclusions:** P15 (value 14, $220K, 5mo) is the single highest-value project not selected. It was excluded because adding it would require $220K and 5 developer-months — resources already fully committed. P5 (value 12, $200K, 5mo) and P19 (value 12, $170K, 4mo) were similarly crowded out.

**Strategic observation:** Because both constraints are fully binding simultaneously, unlocking any excluded project requires growth on both dimensions — more budget alone is insufficient if headcount is also at ceiling, and vice versa. If leadership can secure an incremental ~$150K budget and 4 additional developer-months, substituting P4 (value 11) or exploring P19 (value 12) becomes feasible and should be prioritized first.

---

## Solution Verification

**Cost check — selected projects vs. $1,000K budget:**

| Project | Cost |
|---------|------|
| P1 | $80K |
| P2 | $120K |
| P3 | $60K |
| P6 | $90K |
| P9 | $180K |
| P11 | $130K |
| P13 | $160K |
| P18 | $65K |
| P20 | $115K |

80 + 120 + 60 + 90 + 180 + 130 + 160 + 65 + 115 = **$1,000K**
Result: $1,000K ≤ $1,000K ✓ (budget exactly exhausted)

---

**Headcount check — selected projects vs. 25 developer-months:**

| Project | Dev-months |
|---------|------------|
| P1 | 2 |
| P2 | 3 |
| P3 | 2 |
| P6 | 2 |
| P9 | 4 |
| P11 | 3 |
| P13 | 4 |
| P18 | 2 |
| P20 | 3 |

2 + 3 + 2 + 2 + 4 + 3 + 4 + 2 + 3 = **25 developer-months**
Result: 25 ≤ 25 ✓ (headcount exactly exhausted)

---

**Value check — selected projects:**

6 + 9 + 5 + 7 + 13 + 10 + 12 + 5 + 8 = **75**
Matches solver-reported objective of 75.0 ✓

---

**Rejected alternative — swapping P3 + P6 for P4:**

Consider dropping P3 ($60K, 2mo, value 5) and P6 ($90K, 2mo, value 7) and adding P4 ($150K, 4mo, value 11) instead.

- Cost: $1,000K − $60K − $90K + $150K = $1,000K ✓ (budget still satisfied)
- Headcount: 25 − 2 − 2 + 4 = 25 ✓ (headcount still satisfied)
- Value: 75 − 5 − 7 + 11 = **74**

This alternative is feasible but scores 74, one point below the optimal 75. The solver correctly rejects it — trading two smaller projects for one mid-value project loses net value. The original selection is confirmed optimal.

**Solver's reported value: 75.0 — verified. ✓**

## Solver Code (LLM-generated, PuLP)

```python
projects = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10", "P11", "P12", "P13", "P14", "P15", "P16", "P17", "P18", "P19", "P20"]
cost     = {"P1": 80,  "P2": 120, "P3": 60,  "P4": 150, "P5": 200, "P6": 90,  "P7": 110, "P8": 70,  "P9": 180, "P10": 100, "P11": 130, "P12": 85,  "P13": 160, "P14": 75,  "P15": 220, "P16": 95,  "P17": 140, "P18": 65,  "P19": 170, "P20": 115}
devmos   = {"P1": 2,   "P2": 3,   "P3": 2,   "P4": 4,   "P5": 5,   "P6": 2,   "P7": 3,   "P8": 2,   "P9": 4,   "P10": 3,   "P11": 3,   "P12": 2,   "P13": 4,   "P14": 2,   "P15": 5,   "P16": 3,   "P17": 4,   "P18": 2,   "P19": 4,   "P20": 3}
value    = {"P1": 6,   "P2": 9,   "P3": 5,   "P4": 11,  "P5": 12,  "P6": 7,   "P7": 8,   "P8": 5,   "P9": 13,  "P10": 6,   "P11": 10,  "P12": 6,   "P13": 12,  "P14": 5,   "P15": 14,  "P16": 7,   "P17": 10,  "P18": 5,   "P19": 12,  "P20": 8}
budget   = 1000
capacity = 25

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
| Stage 1 — formulation + solve (s) | 14.00 |
| Stage 2 — interpretation (s) | 44.20 |
| Total latency (s) | 58.90 |
| Input tokens | 1,236 |
| Output tokens | 1,031 |
| Total tokens | 2,267 |