# Staff Scheduling Report

**Problem:** A regional hospital needs to staff one day with 5 shifts: Night (11pm-7am), Early Morning (6am-2pm), Day (10am-6pm), Evening (2pm-10pm), and Late Night (8pm-4am). Minimum nurse coverage: Night needs at least 3 nurses, Early Morning needs at least 4 nurses, Day needs at least 5 nurses, Evening needs at least 4 nurses, Late Night needs at least 3 nurses (total minimum 19 slots). Twenty nurses are available: Nurse1 through Nurse20. Each nurse can work at most 1 shift today. Wage per nurse-shift: Night costs $380, Early Morning costs $260, Day costs $200, Evening costs $230, Late Night costs $310. Assign nurses to shifts to meet all minimum coverage requirements at minimum total wage cost. Note: total nurse capacity (20) exceeds minimum demand (19), so exactly one nurse will not be assigned to any shift.

## Solution

### Step 1 — Inventory

**Nurses:** Nurse1 through Nurse20 (20 total; each works at most 1 shift)

| Shift | Hours | Wage/Nurse | Min Nurses |
|---|---|---|---|
| Night | 11pm–7am | $380 | 3 |
| Early Morning | 6am–2pm | $260 | 4 |
| Day | 10am–6pm | $200 | 5 |
| Evening | 2pm–10pm | $230 | 4 |
| Late Night | 8pm–4am | $310 | 3 |

### Step 2 — Feasibility check

Minimum nurse-shifts required: 3 + 4 + 5 + 4 + 3 = **19**
Nurses available: **20**
Slack: 20 − 19 = **1** (exactly one nurse will be unassigned)

Because capacity equals demand + 1, we must assign exactly 19 nurses. Any assignment of a 20th nurse adds cost without satisfying a new requirement, so the optimum staffs every shift at exactly its minimum.

### Step 3 — Greedy fill (cheapest shifts first)

Rank shifts by wage, ascending:

| Rank | Shift | Wage | Min |
|---|---|---|---|
| 1 | Day | $200 | 5 |
| 2 | Evening | $230 | 4 |
| 3 | Early Morning | $260 | 4 |
| 4 | Late Night | $310 | 3 |
| 5 | Night | $380 | 3 |

Fill each shift to its minimum and stop — adding any extra nurse to any shift increases cost. There is no ambiguity: every shift has a unique wage, and the only choice is which numbered nurses go where (nurses are wage-equivalent within a shift). Assign in ascending nurse order for clarity.

### Step 4 — Optimal assignment

| Shift | Wage | Assigned Nurses | Count |
|---|---|---|---|
| Day | $200 | Nurse1, Nurse2, Nurse3, Nurse4, Nurse5 | 5 |
| Evening | $230 | Nurse6, Nurse7, Nurse8, Nurse9 | 4 |
| Early Morning | $260 | Nurse10, Nurse11, Nurse12, Nurse13 | 4 |
| Late Night | $310 | Nurse14, Nurse15, Nurse16 | 3 |
| Night | $380 | Nurse17, Nurse18, Nurse19 | 3 |
| **Unassigned** | — | Nurse20 | — |

**Total minimum wage cost: $5,030**

---

## Verification

### Coverage check (count ≥ minimum for each shift)

- **Day:** Nurse1–5 → count = 5 ≥ 5 ✓
- **Evening:** Nurse6–9 → count = 4 ≥ 4 ✓
- **Early Morning:** Nurse10–13 → count = 4 ≥ 4 ✓
- **Late Night:** Nurse14–16 → count = 3 ≥ 3 ✓
- **Night:** Nurse17–19 → count = 3 ≥ 3 ✓

### Per-nurse shift count (≤ 1 each)

Nurse1–19 each appear in exactly one shift. Nurse20 appears in zero shifts. No nurse exceeds the 1-shift limit. ✓

### Total wage computation

| Shift | Nurses | Wage | Subtotal |
|---|---|---|---|
| Day | 5 | × $200 | $1,000 |
| Evening | 4 | × $230 | $920 |
| Early Morning | 4 | × $260 | $1,040 |
| Late Night | 3 | × $310 | $930 |
| Night | 3 | × $380 | $1,140 |

Running sum:
- $1,000 + $920 = $1,920
- $1,920 + $1,040 = $2,960
- $2,960 + $930 = $3,890
- $3,890 + $1,140 = **$5,030**

All constraints satisfied. The minimum total wage cost is **$5,030**.

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=OFF (LLM reasoning only) |
| LLM calls | 2 |
| Stage 1 — direct LLM solve (s) | 33.80 |
| Stage 2 — interpretation (s) | — |
| Total latency (s) | 43.60 |
| Input tokens | 1,492 |
| Output tokens | 856 |
| Total tokens | 2,348 |