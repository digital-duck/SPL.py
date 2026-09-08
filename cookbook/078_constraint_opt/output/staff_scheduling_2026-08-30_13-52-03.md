# Staff Scheduling Report

**Problem:** A regional hospital needs to staff one day with 5 shifts: Night (11pm-7am), Early Morning (6am-2pm), Day (10am-6pm), Evening (2pm-10pm), and Late Night (8pm-4am). Minimum nurse coverage: Night needs at least 3 nurses, Early Morning needs at least 4 nurses, Day needs at least 5 nurses, Evening needs at least 4 nurses, Late Night needs at least 3 nurses (total minimum 19 slots). Twenty nurses are available: Nurse1 through Nurse20. Each nurse can work at most 1 shift today. Wage per nurse-shift: Night costs $380, Early Morning costs $260, Day costs $200, Evening costs $230, Late Night costs $310. Assign nurses to shifts to meet all minimum coverage requirements at minimum total wage cost. Note: total nurse capacity (20) exceeds minimum demand (19), so exactly one nurse will not be assigned to any shift.

## Solution

Here's a step-by-step solution to this nurse scheduling problem:

**1. List All Data:**

| Nurse | Shift          | Wage ($) | Coverage Min |
|-------|-----------------|----------|---------------|
| 1     | Night           | 380      | 3             |
| 1     | Early Morning   | 260      | 4             |
| 1     | Day             | 200      | 5             |
| 1     | Evening         | 230      | 4             |
| 1     | Late Night      | 310      | 3             |
| 2     | Night           | 380      | 3             |
| ...   | ...             | ...      | ...           |
| 20    | Late Night      | 310      | 3             |

* **Shifts:** Night (11pm-7am), Early Morning (6am-2pm), Day (10am-6pm), Evening (2pm-10pm), Late Night (8pm-4am)
* **Nurses:** Nurse 1 through Nurse 20
* **Wage per nurse-shift:** Night: $380, Early Morning: $260, Day: $200, Evening: $230, Late Night: $310
* **Minimum Coverage Requirements:** Night (3 nurses), Early Morning (4 nurses), Day (5 nurses), Evening (4 nurses), Late Night (3 nurses)

**2. Calculate Minimum Number of Nurse-Shifts Needed & Feasibility:**

Total minimum coverage = 3 + 4 + 5 + 4 + 3 = 19
Total nurse capacity = 20

Since the total nurse capacity (20) exceeds the minimum required (19), we can certainly meet all coverage requirements.  This means one nurse will not be assigned to any shift.

**3. Assign Nurses to Shifts - Greedy Approach:**

We'll prioritize assigning nurses to shifts with the highest wage, while ensuring minimum coverage is met for each shift.

* **Night (11pm-7am):** Needs 3 nurses.  Assign Nurse 1, Nurse 2, Nurse 3. (Wage: 3 * $380 = $1140)
* **Early Morning (6am-2pm):** Needs 4 nurses. Assign Nurse 4, Nurse 5, Nurse 6, Nurse 7.  (Wage: 4 * $260 = $1040)
* **Day (10am-6pm):** Needs 5 nurses. Assign Nurse 8, Nurse 9, Nurse 10, Nurse 11, Nurse 12. (Wage: 5 * $200 = $1000)
* **Evening (2pm-10pm):** Needs 4 nurses. Assign Nurse 13, Nurse 14, Nurse 15, Nurse 16. (Wage: 4 * $230 = $920)
* **Late Night (8pm-4am):** Needs 3 nurses. Assign Nurse 17, Nurse 18, Nurse 19. (Wage: 3 * $310 = $930)

Now let's check if the minimum coverage is met for each shift:
* Night: 3 nurses
* Early Morning: 4 nurses
* Day: 5 nurses
* Evening: 4 nurses
* Late Night: 3 nurses
Total nurses assigned: 3+4+5+4+3 = 19.

Since we have 20 available nurses and only 19 are needed, one nurse (Nurse 20) is not assigned a shift.

**4. Optimal Assignment & Total Minimum Wage Cost:**

* Nurse 1 - Night
* Nurse 2 - Night
* Nurse 3 - Night
* Nurse 4 - Early Morning
* Nurse 5 - Early Morning
* Nurse 6 - Early Morning
* Nurse 7 - Early Morning
* Nurse 8 - Day
* Nurse 9 - Day
* Nurse 10 - Day
* Nurse 11 - Day
* Nurse 12 - Day
* Nurse 13 - Evening
* Nurse 14 - Evening
* Nurse 15 - Evening
* Nurse 16 - Evening
* Nurse 17 - Late Night
* Nurse 18 - Late Night
* Nurse 19 - Late

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=OFF (LLM reasoning only) |
| LLM calls | 2 |
| Stage 1 — direct LLM solve (s) | 20.00 |
| Stage 2 — interpretation (s) | — |
| Total latency (s) | 29.00 |
| Input tokens | 1,858 |
| Output tokens | 1,337 |
| Total tokens | 3,195 |