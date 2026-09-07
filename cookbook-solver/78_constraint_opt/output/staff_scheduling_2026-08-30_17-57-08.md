# Staff Scheduling Report

**Problem:** A regional hospital needs to staff one day with 5 shifts: Night (11pm-7am), Early Morning (6am-2pm), Day (10am-6pm), Evening (2pm-10pm), and Late Night (8pm-4am). Minimum nurse coverage: Night needs at least 3 nurses, Early Morning needs at least 4 nurses, Day needs at least 5 nurses, Evening needs at least 4 nurses, Late Night needs at least 3 nurses (total minimum 19 slots). Twenty nurses are available: Nurse1 through Nurse20. Each nurse can work at most 1 shift today. Wage per nurse-shift: Night costs $380, Early Morning costs $260, Day costs $200, Evening costs $230, Late Night costs $310. Assign nurses to shifts to meet all minimum coverage requirements at minimum total wage cost. Note: total nurse capacity (20) exceeds minimum demand (19), so exactly one nurse will not be assigned to any shift.

**Solver status:** `Optimal`
**Minimum total wage cost:** $5030.00

**Schedule (assigned shifts):**
  - x_Nurse10_EarlyMorning: assigned
  - x_Nurse11_EarlyMorning: assigned
  - x_Nurse12_Evening: assigned
  - x_Nurse13_EarlyMorning: assigned
  - x_Nurse14_LateNight: assigned
  - x_Nurse15_Day: assigned
  - x_Nurse16_LateNight: assigned
  - x_Nurse17_LateNight: assigned
  - x_Nurse18_Evening: assigned
  - x_Nurse19_EarlyMorning: assigned
  - x_Nurse1_Night: assigned
  - x_Nurse20_Day: assigned
  - x_Nurse3_Day: assigned
  - x_Nurse4_Day: assigned
  - x_Nurse5_Day: assigned
  - x_Nurse6_Night: assigned
  - x_Nurse7_Evening: assigned
  - x_Nurse8_Night: assigned
  - x_Nurse9_Evening: assigned

## Interpretation

**Total minimum wage cost: $5,030.**

Assignments by shift:
- **Night (11pm–7am):** Nurses 1, 6, 8
- **Early Morning (6am–2pm):** Nurses 10, 11, 13, 19
- **Day (10am–6pm):** Nurses 3, 4, 5, 15, 20
- **Evening (2pm–10pm):** Nurses 7, 9, 12, 18
- **Late Night (8pm–4am):** Nurses 14, 16, 17
- **Unassigned:** Nurse 2

Every shift is staffed at exactly its minimum — no shift carries surplus headcount. The optimizer fills the cheapest shifts first (Day at $200, then Evening at $230) to keep costs down, parking the one idle nurse in the pool rather than adding an extra body to any paid slot.

**Practical suggestion:** Designate Nurse 2 as today's float/standby. Confirm their availability by 6am so they can cover any last-minute call-out without triggering overtime on an already-assigned nurse.

---

## Solution Verification

**Step 1 — Coverage check (minimum ≥ requirement)**

| Shift | Assigned nurses | Count | Minimum | Met? |
|---|---|---|---|---|
| Night | 1, 6, 8 | 3 | 3 | ✓ (exactly) |
| Early Morning | 10, 11, 13, 19 | 4 | 4 | ✓ (exactly) |
| Day | 3, 4, 5, 15, 20 | 5 | 5 | ✓ (exactly) |
| Evening | 7, 9, 12, 18 | 4 | 4 | ✓ (exactly) |
| Late Night | 14, 16, 17 | 3 | 3 | ✓ (exactly) |

Total slots filled: 3 + 4 + 5 + 4 + 3 = **19**. Remaining: 20 − 19 = **1** (Nurse 2, unassigned). ✓

**Step 2 — Per-nurse shift count (max 1 allowed)**

Every nurse has exactly one variable set to 1.0, except Nurse 2 who has all zeros. No nurse appears in more than one shift. Maximum shifts per nurse = 1. ✓

**Step 3 — Wage cost computation**

| Shift | Nurses | Rate | Subtotal |
|---|---|---|---|
| Night | 3 | $380 | 3 × 380 = **$1,140** |
| Early Morning | 4 | $260 | 4 × 260 = **$1,040** |
| Day | 5 | $200 | 5 × 200 = **$1,000** |
| Evening | 4 | $230 | 4 × 230 = **$920** |
| Late Night | 3 | $310 | 3 × 310 = **$930** |

Grand total: 1,140 + 1,040 + 1,000 + 920 + 930 = **$5,030**

This matches the solver's reported objective value of **$5,030.00** exactly. The solution is verified correct.

## Solver Code (LLM-generated, PuLP)

```python
nurses = ["Nurse1", "Nurse2", "Nurse3", "Nurse4", "Nurse5", "Nurse6", "Nurse7", "Nurse8", "Nurse9", "Nurse10", "Nurse11", "Nurse12", "Nurse13", "Nurse14", "Nurse15", "Nurse16", "Nurse17", "Nurse18", "Nurse19", "Nurse20"]
shifts = ["Night", "EarlyMorning", "Day", "Evening", "LateNight"]
wage         = {"Night": 380, "EarlyMorning": 260, "Day": 200, "Evening": 230, "LateNight": 310}
min_coverage = {"Night": 3, "EarlyMorning": 4, "Day": 5, "Evening": 4, "LateNight": 3}
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
| Stage 1 — formulation + solve (s) | 9.10 |
| Stage 2 — interpretation (s) | 26.60 |
| Total latency (s) | 36.40 |
| Input tokens | 1,755 |
| Output tokens | 779 |
| Total tokens | 2,534 |