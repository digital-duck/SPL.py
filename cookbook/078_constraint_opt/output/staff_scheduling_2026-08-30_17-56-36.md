# Staff Scheduling Report

**Problem:** A hospital clinic needs to staff one day with 4 shifts: Early Morning (5am-1pm), Day (9am-5pm), Evening (1pm-9pm), and Night (9pm-5am). Minimum nurse coverage: Early Morning needs at least 2 nurses, Day needs at least 3 nurses, Evening needs at least 3 nurses, Night needs at least 2 nurses (total minimum 10 slots). Ten nurses are available: Nurse1 through Nurse10. Each nurse can work at most 1 shift today. Wage per nurse-shift: Early Morning costs $280, Day costs $220, Evening costs $240, Night costs $350. Assign nurses to shifts to meet all minimum coverage requirements at minimum total wage cost.

**Solver status:** `Optimal`
**Minimum total wage cost:** $2640.00

**Schedule (assigned shifts):**
  - x_Nurse10_Early_Morning: assigned
  - x_Nurse1_Day: assigned
  - x_Nurse2_Night: assigned
  - x_Nurse3_Day: assigned
  - x_Nurse4_Day: assigned
  - x_Nurse5_Night: assigned
  - x_Nurse6_Early_Morning: assigned
  - x_Nurse7_Evening: assigned
  - x_Nurse8_Evening: assigned
  - x_Nurse9_Evening: assigned

## Interpretation

The optimal schedule achieves a **minimum total wage cost of $2,640** for the day.

**Assignments:**
- **Early Morning (5am–1pm):** Nurse 6, Nurse 10
- **Day (9am–5pm):** Nurse 1, Nurse 3, Nurse 4
- **Evening (1pm–9pm):** Nurse 7, Nurse 8, Nurse 9
- **Night (9pm–5am):** Nurse 2, Nurse 5

Every shift is staffed **exactly at the minimum requirement** — no shift carries extra nurses. All 10 available nurses are deployed, each working exactly one shift, leaving zero on standby.

**Practical suggestion:** Night shift costs $350/nurse — the most expensive slot. Building a small cross-trained standby pool from Day-shift nurses (lowest cost at $220) gives the manager a cheaper on-call option if a Night nurse calls out, avoiding last-minute premium agency coverage.

---

## Solution Verification

**Coverage check (minimum ≥ required):**

| Shift | Assigned Nurses | Count | Minimum | Met? |
|---|---|---|---|---|
| Early Morning | Nurse 6, Nurse 10 | 2 | 2 | Exactly met |
| Day | Nurse 1, Nurse 3, Nurse 4 | 3 | 3 | Exactly met |
| Evening | Nurse 7, Nurse 8, Nurse 9 | 3 | 3 | Exactly met |
| Night | Nurse 2, Nurse 5 | 2 | 2 | Exactly met |

All four constraints satisfied. No shift is under- or over-staffed.

**Per-nurse shift count (maximum 1 shift each):**

Each of the 10 nurses appears in exactly one assignment line. No nurse is assigned to more than one shift. Constraint satisfied for all 10 nurses.

**Wage cost computation:**

- Early Morning: 2 nurses × $280 = **$560**
- Day: 3 nurses × $220 = **$660**
- Evening: 3 nurses × $240 = **$720**
- Night: 2 nurses × $350 = **$700**

Running total: $560 + $660 = $1,220; $1,220 + $720 = $1,940; $1,940 + $700 = **$2,640**

The computed cost of **$2,640 matches the solver's reported objective exactly.** The solution is verified correct.

## Solver Code (LLM-generated, PuLP)

```python
nurses = ["Nurse1", "Nurse2", "Nurse3", "Nurse4", "Nurse5", "Nurse6", "Nurse7", "Nurse8", "Nurse9", "Nurse10"]
shifts = ["Early Morning", "Day", "Evening", "Night"]
wage         = {"Early Morning": 280, "Day": 220, "Evening": 240, "Night": 350}
min_coverage = {"Early Morning": 2, "Day": 3, "Evening": 3, "Night": 2}
max_per_nurse = 1

prob = pulp.LpProblem("scheduling", pulp.LpMinimize)

x = {n: {s: pulp.LpVariable(f"x_{n}_{s}", cat="Binary")
         for s in shifts}
     for n in nurses}

prob += pulp.lpSum(wage[s] * x[n][s] for n in nurses for s in shifts)

for s in shifts:
    prob += pulp.lpSum(x[n][s] for n in nurses) >= min_coverage[s]

for n in nurses:
    prob += pulp.lpSum(x[n][s] for s in shifts) <= max_per_nurse

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
| Stage 1 — formulation + solve (s) | 8.60 |
| Stage 2 — interpretation (s) | 20.70 |
| Total latency (s) | 30.00 |
| Input tokens | 1,259 |
| Output tokens | 688 |
| Total tokens | 1,947 |