# Staff Scheduling Report

**Problem:** A clinic needs to staff one day with 3 shifts: Morning, Afternoon, and Night. Minimum nurse coverage required: Morning needs at least 2 nurses, Afternoon needs at least 2 nurses, Night needs at least 1 nurse. Five nurses are available (Nurse1 through Nurse5). Each nurse can work at most 1 shift today. Wage per nurse-shift: Morning costs $200, Afternoon costs $180, Night costs $320. Assign nurses to shifts to meet all minimum coverage requirements at minimum total wage cost.

## Solution

**Step 1 — Inputs**

| Shift | Min nurses | Wage per nurse |
|-------|-----------|----------------|
| Morning | 2 | $200 |
| Afternoon | 2 | $180 |
| Night | 1 | $320 |

Available nurses: Nurse1, Nurse2, Nurse3, Nurse4, Nurse5 (5 total, each works at most 1 shift).

**Step 2 — Feasibility check**

Minimum nurse-shifts required: 2 + 2 + 1 = **5**
Total nurse capacity: **5**
5 ≥ 5 → feasible, but with zero slack. Every nurse must be assigned to exactly one shift; no nurse can be left idle and no shift can receive more than its minimum.

This means the headcount per shift is fully determined: Morning gets exactly 2, Afternoon gets exactly 2, Night gets exactly 1. There is no room to trade nurses across shifts.

**Step 3 — Minimize cost (greedy by wage, cheapest first)**

Since the counts are fixed, minimizing cost means confirming the only feasible allocation is also the cheapest. Apply greedy to verify:

1. Afternoon ($180, cheapest) — assign 2 nurses → cost contribution: 2 × $180 = $360
2. Morning ($200, next cheapest) — assign 2 nurses → cost contribution: 2 × $200 = $400
3. Night ($320, most expensive) — assign 1 nurse → cost contribution: 1 × $320 = $320

No alternatives exist: the counts 2/2/1 are the only feasible partition of 5 nurses given the minimums sum exactly to 5.

**Step 4 — Optimal assignment**

| Nurse | Shift | Wage |
|-------|-------|------|
| Nurse1 | Afternoon | $180 |
| Nurse2 | Afternoon | $180 |
| Nurse3 | Morning | $200 |
| Nurse4 | Morning | $200 |
| Nurse5 | Night | $320 |

**Total minimum wage cost: $1,080**

---

## Verification

**Coverage check:**

- Morning: Nurse3, Nurse4 → 2 nurses assigned; 2 ≥ 2 ✓
- Afternoon: Nurse1, Nurse2 → 2 nurses assigned; 2 ≥ 2 ✓
- Night: Nurse5 → 1 nurse assigned; 1 ≥ 1 ✓

**Shift-per-nurse check:**

- Nurse1: 1 shift (Afternoon) ≤ 1 ✓
- Nurse2: 1 shift (Afternoon) ≤ 1 ✓
- Nurse3: 1 shift (Morning) ≤ 1 ✓
- Nurse4: 1 shift (Morning) ≤ 1 ✓
- Nurse5: 1 shift (Night) ≤ 1 ✓

**Total wage cost:**

- Afternoon: 2 nurses × $180 = $360
- Morning: 2 nurses × $200 = $400
- Night: 1 nurse × $320 = $320
- Sum: $360 + $400 + $320 = **$1,080** ✓

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=OFF (LLM reasoning only) |
| LLM calls | 2 |
| Stage 1 — direct LLM solve (s) | 28.90 |
| Stage 2 — interpretation (s) | — |
| Total latency (s) | 34.00 |
| Input tokens | 1,199 |
| Output tokens | 599 |
| Total tokens | 1,798 |