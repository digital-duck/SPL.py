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

The optimal schedule costs **$1,080 total** — the minimum possible wage for meeting all coverage requirements.

**Assignments:**
- **Morning:** Nurse 1, Nurse 2
- **Afternoon:** Nurse 3, Nurse 4
- **Night:** Nurse 5

All three shifts are staffed at exactly their minimum thresholds — no shift has surplus coverage. Nurses 1 through 5 each work exactly one shift; no one is double-booked.

**Practical suggestion:** Night shift carries the highest per-nurse cost ($320) and the thinnest coverage (one nurse). Consider maintaining a short standby list of nurses willing to cover Night on short notice, since a single callout would immediately breach minimum coverage with no buffer.

---

## Solution Verification

**Coverage check by shift:**

| Shift | Assigned Nurses | Count | Minimum | Satisfied? |
|---|---|---|---|---|
| Morning | Nurse 1, Nurse 2 | 2 | 2 | Yes (2 ≥ 2) |
| Afternoon | Nurse 3, Nurse 4 | 2 | 2 | Yes (2 ≥ 2) |
| Night | Nurse 5 | 1 | 1 | Yes (1 ≥ 1) |

**Nurse shift-count check:**

Each nurse appears in exactly one assignment variable set to 1.0. No nurse is assigned to more than one shift. All five nurses are assigned; constraint "at most 1 shift" holds for every nurse.

**Wage cost computation:**

- Morning: 2 nurses × $200/nurse = $400
- Afternoon: 2 nurses × $180/nurse = $360
- Night: 1 nurse × $320/nurse = $320
- **Total: $400 + $360 + $320 = $1,080**

This matches the solver's reported objective value of $1,080.00 exactly. The solution is confirmed correct.

## Solver Code (LLM-generated, PuLP)

```python
nurses = ["Nurse1", "Nurse2", "Nurse3", "Nurse4", "Nurse5"]
shifts = ["Morning", "Afternoon", "Night"]
wage         = {"Morning": 200, "Afternoon": 180, "Night": 320}
min_coverage = {"Morning": 2, "Afternoon": 2, "Night": 1}
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
| Stage 1 — formulation + solve (s) | 6.00 |
| Stage 2 — interpretation (s) | 14.80 |
| Total latency (s) | 21.50 |
| Input tokens | 1,038 |
| Output tokens | 589 |
| Total tokens | 1,627 |