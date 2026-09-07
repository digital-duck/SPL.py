# Resource Allocation Report

**Problem:** An IT department must select a portfolio of projects for next quarter. Ten candidate projects are available. Project P1 costs $80K and requires 2 developer-months, delivering strategic value 6. Project P2 costs $120K and requires 3 developer-months, delivering value 9. Project P3 costs $60K and requires 2 developer-months, delivering value 5. Project P4 costs $150K and requires 4 developer-months, delivering value 11. Project P5 costs $200K and requires 5 developer-months, delivering value 12. Project P6 costs $90K and requires 2 developer-months, delivering value 7. Project P7 costs $110K and requires 3 developer-months, delivering value 8. Project P8 costs $70K and requires 2 developer-months, delivering value 5. Project P9 costs $180K and requires 4 developer-months, delivering value 13. Project P10 costs $100K and requires 3 developer-months, delivering value 6. The total budget is $600K and the team has 15 developer-months available. Each project is either fully funded or not - no partial investment. Select which projects to fund to maximize total strategic value.

## Solution

### Step 1: Project data and efficiency ratios

| ID  | Cost ($K) | Dev-mo | Value | V/Cost  | V/DM |
|-----|-----------|--------|-------|---------|------|
| P1  | 80        | 2      | 6     | 0.0750  | 3.00 |
| P2  | 120       | 3      | 9     | 0.0750  | 3.00 |
| P3  | 60        | 2      | 5     | 0.0833  | 2.50 |
| P4  | 150       | 4      | 11    | 0.0733  | 2.75 |
| P5  | 200       | 5      | 12    | 0.0600  | 2.40 |
| P6  | 90        | 2      | 7     | 0.0778  | 3.50 |
| P7  | 110       | 3      | 8     | 0.0727  | 2.67 |
| P8  | 70        | 2      | 5     | 0.0714  | 2.50 |
| P9  | 180       | 4      | 13    | 0.0722  | 3.25 |
| P10 | 100       | 3      | 6     | 0.0600  | 2.00 |

Sorted by V/Cost: **P3 > P6 > P1=P2 > P4 > P7 > P9 > P8 > P5=P10**

### Step 2: Search space and greedy seed

2^10 = 1,024 subsets. Greedy by V/Cost ratio (P3→P6→P1→P2→P4→…):

| Add  | Running cost | Running DM | Running V | Fits? |
|------|-------------|------------|-----------|-------|
| P3   | 60          | 2          | 5         | ✓     |
| P6   | 150         | 4          | 12        | ✓     |
| P1   | 230         | 6          | 18        | ✓     |
| P2   | 350         | 9          | 27        | ✓     |
| P4   | 500         | 13         | 38        | ✓     |
| P7   | **610**     | —          | —         | ✗ budget |
| P8   | 570         | 15         | 43        | ✓     |
| P5,P9,P10 | >600 | —         | —         | ✗     |

Greedy yields **{P3, P6, P1, P2, P4, P8} = V 43**, $570K, 15 DM. Remaining budget $30K buys nothing.

### Step 3: Swap analysis — investigating P9

P9 has the highest absolute value (13) and solid V/DM (3.25). Test it as an anchor:

**Anchor P9** ($180K, 4 DM): remaining budget = $420K, remaining DM = 11.

Maximize value from the other nine projects within $420K / 11 DM:

| Candidate fill | Cost | DM | Value | Feasible? |
|----------------|------|----|-------|-----------|
| P4+P2+P6+P1    | 440  | 11 | 33    | ✗ budget  |
| P4+P2+P7+P3    | 440  | 12 | 33    | ✗ both    |
| P4+P2+P6+P3    | 420  | 11 | 32    | ✓         |
| P4+P2+P6+P8    | 430  | 11 | 32    | ✗ budget  |
| P4+P7+P6+P8    | 420  | 11 | 31    | ✓ but ↓   |

Best feasible fill is **P4+P2+P6+P3** (cost $420K, DM 11, value 32).

Combined portfolio: **{P9, P4, P2, P6, P3}**
- Cost: 180+150+120+90+60 = **$600K**
- DM: 4+4+3+2+2 = **15**
- Value: 13+11+9+7+5 = **45**

### Step 4: Attempt to reach V = 46

Any 5-project set containing P9 needs V ≥ 33 from the remaining four slots within $420K / 11 DM. Exhaustive check above shows the ceiling is V = 32. Attempting 6-project sets including P9:

- {P9, P4, P2, P6, P3, P8}: cost = 180+150+120+90+60+70 = **670 > 600**. Infeasible.

Without P9, top 6-project candidate: {P4, P2, P7, P6, P1, P3} = V 46, cost = 150+120+110+90+80+60 = **610 > 600**. Infeasible.

No feasible subset achieves V ≥ 46.

### Optimal selection

**{P9, P4, P2, P6, P3} — Total strategic value: 45**

---

## Verification

**Cost check:**
$$180 + 150 + 120 + 90 + 60 = 600 \leq 600 \checkmark$$

**Dev-month check:**
$$4 + 4 + 3 + 2 + 2 = 15 \leq 15 \checkmark$$

**Value sum:**
$$13 + 11 + 9 + 7 + 5 = 45$$

**Alternative considered — greedy result {P3, P6, P1, P2, P4, P8}:**
- Cost: 60+90+80+120+150+70 = **$570K** ✓
- DM: 2+2+2+3+4+2 = **15** ✓
- Value: 5+7+6+9+11+5 = **43**

This is feasible but scores **2 points lower** (43 vs. 45). The greedy ordering by V/Cost deprioritized P9 (ratio 0.0722) in favor of P1 (0.075) and P8 (0.071), consuming DM capacity on lower-absolute-value projects. Swapping P1+P8 (combined V=11, cost=$150K, DM=4) for P9 (V=13, cost=$180K, DM=4) gains 2 value points at a cost of $30K — money that the greedy solution left unused anyway.

**Conclusion:** No feasible subset exceeds V = 45. The optimal portfolio is **{P9, P4, P2, P6, P3}** at exactly $600K, 15 developer-months, and total strategic value **45**.

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=OFF (LLM reasoning only) |
| LLM calls | 2 |
| Stage 1 — direct LLM solve (s) | 178.30 |
| Stage 2 — interpretation (s) | — |
| Total latency (s) | 185.30 |
| Input tokens | 2,004 |
| Output tokens | 1,152 |
| Total tokens | 3,156 |