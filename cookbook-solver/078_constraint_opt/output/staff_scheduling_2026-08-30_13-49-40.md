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

**1. Total Minimum Wage Cost:** The optimal schedule results in a total minimum wage cost of $1080.00. This is calculated by summing the individual shift costs: Nurse1 Afternoon ($0), Nurse1 Morning ($200), Nurse3 Afternoon ($180), Nurse3 Night ($320) and Nurse5 Night ($320).

**2. Nurse Assignments:** Nurse1 will work the Morning shift, Nurse2 will work the Morning shift, Nurse3 will work the Afternoon shift, Nurse4 will work the Afternoon shift, and Nurse5 will work the Night shift. 

**3. Coverage Requirements:** All minimum coverage requirements are exactly met. The Morning shift has 2 nurses, the Afternoon shift has 2 nurses, and the Night shift has 1 nurse – fulfilling the set minimums. There is no overstaffing.

**4. Practical Suggestion:** To improve flexibility and reduce reliance on a single schedule, consider implementing a small standby roster of nurses who can be called upon if needed.  Exploring cross-training opportunities (e.g., basic skills in multiple roles) could also enhance resource utilization during unexpected absences or surges in patient volume.



## Solution Verification

Let’s verify the solution:

**Shift 1: Morning (2 Nurses)**
* Nurse 1 assigned: Cost = $200
* Nurse 2 assigned: Cost = $200
* Total Morning Cost: $400

**Shift 2: Afternoon (2 Nurses)**
* Nurse 3 assigned: Cost = $180
* Nurse 4 assigned: Cost = $180
* Total Afternoon Cost: $360

**Shift 3: Night (1 Nurse)**
* Nurse 5 assigned: Cost = $320
* Total Night Cost: $320

**Total Wage Cost:** $400 + $360 + $320 = $1080.00

**Nurse Assignments Check:**
* Nurse 1: Assigned to Morning (1 shift) - Valid
* Nurse 2: Assigned to Morning (1 shift) - Valid
* Nurse 3: Assigned to Afternoon (1 shift) - Valid
* Nurse 4: Assigned to Afternoon (1 shift) - Valid
* Nurse 5: Assigned to Night (1 shift) - Valid

The computed total wage cost of $1080.00 matches the solver's reported value of $1080.00, confirming the solution’s validity.

## Solver Code (LLM-generated, PuLP)

```python
```python
nurses = ["Nurse1", "Nurse2", "Nurse3", "Nurse4", "Nurse5"]
shifts = ["Morning", "Afternoon", "Night"]
wage = {"Morning": 200, "Afternoon": 180, "Night": 320}
min_coverage = {"Morning": 2, "Afternoon": 2, "Night": 1}
max_per_nurse = 1

prob = pulp.LpProblem("scheduling", pulp.LpMinimize)

# CRITICAL: x is a 2D DICT — x[nurse][shift] — NOT a single variable
# Every nurse × shift combination gets its own LpVariable
x = {n: {s: pulp.LpVariable(f"x_{n}_{s}", cat="Binary")
         for s in shifts}
     for n in nurses}

# Objective: minimize total wage cost
prob += pulp.lpSum(wage[s] * x[n][s] for n in nurses for s in shifts)

# Coverage constraints: each shift gets enough nurses
for s in shifts:
    prob += pulp.lpSum(x[n][s] for n in nurses) >= min_coverage[s]

# Workload constraints: each nurse works at most max_per_nurse shifts
for n in nurses:
    prob += pulp.lpSum(x[n][s] for s in shifts) <= max_per_nurse

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
| Stage 1 — formulation + solve (s) | 9.80 |
| Stage 2 — interpretation (s) | 11.10 |
| Total latency (s) | 21.50 |
| Input tokens | 1,246 |
| Output tokens | 942 |
| Total tokens | 2,188 |