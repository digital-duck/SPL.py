# Staff Scheduling Report

**Problem:** A clinic needs to staff one day with 3 shifts: Morning, Afternoon, and Night. Minimum nurse coverage required: Morning needs at least 2 nurses, Afternoon needs at least 2 nurses, Night needs at least 1 nurse. Five nurses are available (Nurse1 through Nurse5). Each nurse can work at most 1 shift today. Wage per nurse-shift: Morning costs $200, Afternoon costs $180, Night costs $320. Assign nurses to shifts to meet all minimum coverage requirements at minimum total wage cost.

**Solver status:** `Optimal`
**Minimum total wage cost:** $1080.00

**Schedule (assigned shifts):**
  - x_Nurse1_Morning: assigned
  - x_Nurse2_Morning: assigned
  - x_Nurse3_Afternoon: assigned
  - x_Nurse4_Afternoon: assigned
  - x_Nurse5_Night: assigned

## Interpretation

The optimal schedule achieves a **total wage cost of $1,080** for the day.

**Assignments:**
- **Morning shift:** Nurse1 and Nurse2
- **Afternoon shift:** Nurse3 and Nurse4
- **Night shift:** Nurse5

All three shifts meet their minimums exactly — no shift carries extra staff beyond what is required. This is a lean, cost-minimized plan with no scheduling slack.

**Practical suggestion:** The Night shift is covered by a single nurse (Nurse5) with no buffer. If Nurse5 calls out, the shift falls below minimum coverage. Maintain a standby roster of one cross-trained nurse available for Night emergencies, and consider rotating Night-shift willingness across all five nurses over the pay period to avoid burnout and single-point-of-failure risk.

---

## Solution Verification

**Coverage check (minimum requirements):**

| Shift | Assigned Nurses | Count | Minimum Required | Met? |
|---|---|---|---|---|
| Morning | Nurse1, Nurse2 | 2 | 2 | Yes (exactly) |
| Afternoon | Nurse3, Nurse4 | 2 | 2 | Yes (exactly) |
| Night | Nurse5 | 1 | 1 | Yes (exactly) |

All coverage constraints satisfied.

**Per-nurse shift count (maximum 1 shift each):**

- Nurse1: Morning only → 1 shift
- Nurse2: Morning only → 1 shift
- Nurse3: Afternoon only → 1 shift
- Nurse4: Afternoon only → 1 shift
- Nurse5: Night only → 1 shift

No nurse exceeds the one-shift limit.

**Wage cost calculation:**

- Morning: 2 nurses × $200 = $400
- Afternoon: 2 nurses × $180 = $360
- Night: 1 nurse × $320 = $320
- **Total: $400 + $360 + $320 = $1,080**

The computed cost of **$1,080** matches the solver's reported objective value exactly. The solution is verified correct.

## Solver Code (LLM-generated, PuLP)

```python
```python
nurses = ["Nurse1", "Nurse2", "Nurse3", "Nurse4", "Nurse5"]
shifts = ["Morning", "Afternoon", "Night"]
wage = {"Morning": 200, "Afternoon": 180, "Night": 320}
min_nurses = {"Morning": 2, "Afternoon": 2, "Night": 1}
max_shifts_per_nurse = 1

prob = pulp.LpProblem("StaffScheduling", sense=pulp.LpMinimize)

x = {
    (n, s): pulp.LpVariable(f"x_{n}_{s}", cat="Binary")
    for n in nurses
    for s in shifts
}

prob += pulp.lpSum(wage[s] * x[(n, s)] for n in nurses for s in shifts)

for s in shifts:
    prob += pulp.lpSum(x[(n, s)] for n in nurses) >= min_nurses[s]

for n in nurses:
    prob += pulp.lpSum(x[(n, s)] for s in shifts) <= max_shifts_per_nurse

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
| LLM calls | 2 |
| Stage 1 — formulation + solve (s) | 9.10 |
| Stage 2 — interpretation (s) | 17.20 |
| Total latency (s) | 27.00 |
| Input tokens | 866 |
| Output tokens | 636 |
| Total tokens | 1,502 |