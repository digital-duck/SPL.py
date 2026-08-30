# Staff Scheduling Report

**Problem:** A clinic needs to staff one day with 3 shifts: Morning, Afternoon, and Night. Minimum nurse coverage required: Morning needs at least 2 nurses, Afternoon needs at least 2 nurses, Night needs at least 1 nurse. Five nurses are available (Nurse1 through Nurse5). Each nurse can work at most 1 shift today. Wage per nurse-shift: Morning costs $200, Afternoon costs $180, Night costs $320. Assign nurses to shifts to meet all minimum coverage requirements at minimum total wage cost.

## Solution

Here's a step-by-step mathematical solution to the staff scheduling problem:

**1. List of Data:**

| Nurse | Shift     | Wage ($) | Coverage Requirement |
|-------|-----------|---------|----------------------|
| Nurse1| Morning   | 200     | 2                    |
| Nurse2| Morning   | 200     | 2                    |
| Nurse3| Morning   | 200     | 2                    |
| Nurse4| Afternoon | 180     | 2                    |
| Nurse5| Afternoon | 180     | 2                    |
| Nurse1| Afternoon | 180     | 2                    |
| Nurse2| Night     | 320     | 1                    |
| Nurse3| Night     | 320     | 1                    |
| Nurse4| Night     | 320     | 1                    |

**2. Minimum Coverage and Feasibility:**

*   Minimum Morning coverage: 2 nurses
*   Minimum Afternoon coverage: 2 nurses
*   Minimum Night coverage: 1 nurse
*   Total minimum nurses needed: 2 + 2 + 1 = 5 nurses

To meet the minimum, we need to schedule at least 5 nurse-shifts.  Since there are 5 nurses available and each can work at most one shift, this is feasible. The total number of nurse-shifts possible is 5 (if all nurses worked one shift).

**3. Assignment Strategy – Greedy Approach:**

We will use a greedy approach, prioritizing the cheapest shifts first to minimize cost while meeting the minimum coverage requirements.

*   **Step 1: Morning Shifts - Minimum 2 Nurses:** We need at least 2 nurses for the morning. Assign Nurse1, Nurse2, and Nurse3 to the Morning shift.
    *   Cost of Morning Shift: (2 nurses * $200/nurse) = $400
*   **Step 2: Afternoon Shifts - Minimum 2 Nurses:** We need at least 2 nurses for the afternoon. Assign Nurse4 and Nurse5 to the Afternoon shift.
    *   Cost of Afternoon Shift: (2 nurses * $180/nurse) = $360
*   **Step 3: Night Shift - Minimum 1 Nurse:** We need at least 1 nurse for the night. Assign Nurse2 to the Night shift.
    *   Cost of Night Shift: (1 nurse * $320/nurse) = $320

Now, let’s check if all constraints are met and if we have utilized all nurses.

| Nurse | Shift     | Wage ($) | Coverage |
|-------|-----------|---------|----------|
| Nurse1| Morning   | 200     | 1        |
| Nurse2| Morning   | 200     | 1        |
| Nurse3| Morning   | 200     | 1        |
| Nurse4| Afternoon | 180     | 1        |
| Nurse5| Afternoon | 180     | 1        |
| Nurse2| Night     | 320     | 1        |

We have assigned all 5 nurses.  The coverage requirements are met: Morning has 2 nurses, Afternoon has 2 nurses and Night has 1 nurse.

Total Wage Cost = $400 + $360 + $320 = $1080

**4. Optimal Assignment & Total Minimum Wage Cost:**

*   Nurse1 - Morning
*   Nurse2 - Morning
*   Nurse3 - Morning
*   Nurse4 - Afternoon
*   Nurse5 - Afternoon
*   Nurse2 - Night

Total Minimum Wage Cost = $1080


## Verification

**Shift Coverage Check:**

*   **Morning:** Nurse1 (1) + Nurse2 (1) + Nurse3 (1) = 3 nurses.  ≥ 2 (minimum) – satisfied.
*   **Afternoon:** Nurse4 (1) + Nurse5 (1) = 2 nurses. ≥ 2 (minimum) – satisfied.
*   **Night:** Nurse2 (1) = 1 nurse. ≥ 1 (minimum) – satisfied.

**Nurse Assignment Check:**

*   Nurse1: Works 1 shift - Allowed.
*   Nurse2: Works 3 shifts - Allowed.
*   Nurse3: Works 1 shift - Allowed.
*   Nurse4: Works 1 shift - Allowed.
*   Nurse5: Works 1 shift - Allowed

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=OFF (LLM reasoning only) |
| LLM calls | 2 |
| Stage 1 — direct LLM solve (s) | 18.80 |
| Stage 2 — interpretation (s) | — |
| Total latency (s) | 24.20 |
| Input tokens | 1,640 |
| Output tokens | 1,159 |
| Total tokens | 2,799 |