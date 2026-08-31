# Staff Scheduling Report

**Problem:** A hospital clinic needs to staff one day with 4 shifts: Early Morning (5am-1pm), Day (9am-5pm), Evening (1pm-9pm), and Night (9pm-5am). Minimum nurse coverage: Early Morning needs at least 2 nurses, Day needs at least 3 nurses, Evening needs at least 3 nurses, Night needs at least 2 nurses (total minimum 10 slots). Ten nurses are available: Nurse1 through Nurse10. Each nurse can work at most 1 shift today. Wage per nurse-shift: Early Morning costs $280, Day costs $220, Evening costs $240, Night costs $350. Assign nurses to shifts to meet all minimum coverage requirements at minimum total wage cost.

## Solution

### Step 1 — Inventory

| Shift | Hours | Min nurses | Wage/nurse |
|---|---|---|---|
| Early Morning (EM) | 5 am–1 pm | 2 | $280 |
| Day (D) | 9 am–5 pm | 3 | $220 |
| Evening (EV) | 1 pm–9 pm | 3 | $240 |
| Night (N) | 9 pm–5 am | 2 | $350 |

Nurses available: Nurse1 … Nurse10 (10 total). Each works at most 1 shift.

### Step 2 — Feasibility check

Total minimum nurse-slots required: 2 + 3 + 3 + 2 = **10**
Total nurse capacity: **10**

10 ≥ 10 ✓ — feasible, but with zero slack. Every nurse must be assigned to exactly one shift, and every shift must be staffed at exactly its minimum. No extras exist anywhere.

### Step 3 — Greedy assignment by cost

Because every nurse must be used and every shift must be filled to the minimum, the only degree of freedom is *which nurse goes to which shift* — not *how many*. The counts are forced: EM=2, D=3, EV=3, N=2.

To minimize total cost we want as many nurses as possible in cheap shifts. Rank shifts:

1. Day $220 — cheapest → fill first (3 nurses)
2. Evening $240 → fill next (3 nurses)
3. Early Morning $280 → fill next (2 nurses)
4. Night $350 — most expensive → fill last with remaining nurses (2 nurses)

With exactly 10 nurses and exactly 10 required slots this ordering places no nurse in Night unless forced, and Night only gets the 2 it strictly needs. There is no alternative allocation that changes the counts (the counts are fixed), so this is the unique minimum.

### Step 4 — Optimal assignment

| Nurse | Shift | Wage |
|---|---|---|
| Nurse1 | Day | $220 |
| Nurse2 | Day | $220 |
| Nurse3 | Day | $220 |
| Nurse4 | Evening | $240 |
| Nurse5 | Evening | $240 |
| Nurse6 | Evening | $240 |
| Nurse7 | Early Morning | $280 |
| Nurse8 | Early Morning | $280 |
| Nurse9 | Night | $350 |
| Nurse10 | Night | $350 |

**Total minimum wage cost: $2,640**

---

## Verification

### Coverage check

- **Early Morning**: Nurse7, Nurse8 → 2 nurses. Required ≥ 2. 2 ≥ 2 ✓
- **Day**: Nurse1, Nurse2, Nurse3 → 3 nurses. Required ≥ 3. 3 ≥ 3 ✓
- **Evening**: Nurse4, Nurse5, Nurse6 → 3 nurses. Required ≥ 3. 3 ≥ 3 ✓
- **Night**: Nurse9, Nurse10 → 2 nurses. Required ≥ 2. 2 ≥ 2 ✓

### Shift-per-nurse check

Each of Nurse1–Nurse10 appears exactly once in the table. Maximum shifts worked by any nurse = 1. Allowed maximum = 1. ✓

### Cost computation

| Shift | Nurses assigned | Wage/nurse | Subtotal |
|---|---|---|---|
| Day | 3 | $220 | 3 × $220 = $660 |
| Evening | 3 | $240 | 3 × $240 = $720 |
| Early Morning | 2 | $280 | 2 × $280 = $560 |
| Night | 2 | $350 | 2 × $350 = $700 |

Total: $660 + $720 + $560 + $700

$660 + $720 = $1,380
$1,380 + $560 = $1,940
$1,940 + $700 = **$2,640** ✓

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=OFF (LLM reasoning only) |
| LLM calls | 2 |
| Stage 1 — direct LLM solve (s) | 25.10 |
| Stage 2 — interpretation (s) | — |
| Total latency (s) | 33.30 |
| Input tokens | 1,393 |
| Output tokens | 788 |
| Total tokens | 2,181 |