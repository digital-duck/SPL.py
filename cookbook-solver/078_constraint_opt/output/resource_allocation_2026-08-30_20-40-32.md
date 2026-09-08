# Resource Allocation Report

**Problem:** An IT department must select a portfolio of projects for next quarter. Six candidate projects are available. Project P1 costs $120K and requires 3 developer-months, delivering strategic value 8. Project P2 costs $80K and requires 2 developer-months, delivering value 5. Project P3 costs $200K and requires 5 developer-months, delivering value 10. Project P4 costs $150K and requires 3 developer-months, delivering value 9. Project P5 costs $60K and requires 2 developer-months, delivering value 4. Project P6 costs $90K and requires 2 developer-months, delivering value 6. The total budget is $500K and the team has 10 developer-months available. Each project is either fully funded or not funded - no partial investment. Select which projects to fund to maximize total strategic value.

## Solution

### Step 1: Project Data

| Project | Cost ($K) | Dev-Months | Value | Value/Cost | Value/DM |
|---------|-----------|------------|-------|------------|----------|
| P1 | 120 | 3 | 8 | 0.0667 | 2.67 |
| P2 | 80 | 2 | 5 | 0.0625 | 2.50 |
| P3 | 200 | 5 | 10 | 0.0500 | 2.00 |
| P4 | 150 | 3 | 9 | 0.0600 | 3.00 |
| P5 | 60 | 2 | 4 | 0.0667 | 2.00 |
| P6 | 90 | 2 | 6 | 0.0667 | 3.00 |

Constraints: Budget ≤ $500K, Dev-months ≤ 10.

### Step 2: Bound the Search Space

With n=6 projects there are 2^6 = 64 subsets. Total cost of all six: 120+80+200+150+60+90 = **700K**; total dev-months: 3+2+5+3+2+2 = **17**. We must discard enough projects to shed ≥200K and ≥7 dev-months simultaneously.

**5-project subsets (drop 1):** The cheapest single project is P5 ($60K), the most expensive is P3 ($200K). Even dropping P3 leaves cost = 500K (just fits) but dev-months = 17−5 = 12 > 10. Every other drop leaves cost > 500K as well. *All 5-project subsets are infeasible.*

Therefore the optimum lies among **4-project subsets** (drop exactly 2) or smaller. A 3-project subset has maximum possible value of 10+9+8 = 27, so if any 4-project subset reaches ≥ 28 it is optimal.

### Step 3: Enumerate All 15 Four-Project Subsets (C(6,2) = 15 drops)

| Dropped | Kept | Cost ($K) | DM | Value | Feasible? |
|---------|------|-----------|----|-------|-----------|
| P1, P2 | P3,P4,P5,P6 | 200+150+60+90 = 500 | 5+3+2+2 = 12 | 29 | ✗ DM |
| P1, P3 | P2,P4,P5,P6 | 80+150+60+90 = 380 | 2+3+2+2 = 9 | 24 | ✓ |
| P1, P4 | P2,P3,P5,P6 | 80+200+60+90 = 430 | 2+5+2+2 = 11 | 25 | ✗ DM |
| P1, P5 | P2,P3,P4,P6 | 80+200+150+90 = 520 | — | — | ✗ Budget |
| P1, P6 | P2,P3,P4,P5 | 80+200+150+60 = 490 | 2+5+3+2 = 12 | 28 | ✗ DM |
| P2, P3 | P1,P4,P5,P6 | 120+150+60+90 = 420 | 3+3+2+2 = 10 | **27** | ✓ |
| P2, P4 | P1,P3,P5,P6 | 120+200+60+90 = 470 | 3+5+2+2 = 12 | 27 | ✗ DM |
| P2, P5 | P1,P3,P4,P6 | 120+200+150+90 = 560 | — | — | ✗ Budget |
| P2, P6 | P1,P3,P4,P5 | 120+200+150+60 = 530 | — | — | ✗ Budget |
| **P3, P5** | **P1,P2,P4,P6** | **120+80+150+90 = 440** | **3+2+3+2 = 10** | **28** | **✓** |
| P3, P6 | P1,P2,P4,P5 | 120+80+150+60 = 410 | 3+2+3+2 = 10 | 26 | ✓ |
| P4, P5 | P1,P2,P3,P6 | 120+80+200+90 = 490 | 3+2+5+2 = 12 | 29 | ✗ DM |
| P4, P6 | P1,P2,P3,P5 | 120+80+200+60 = 460 | 3+2+5+2 = 12 | 27 | ✗ DM |
| P5, P6 | P1,P2,P3,P4 | 120+80+200+150 = 550 | — | — | ✗ Budget |
| P3, P4 | P1,P2,P5,P6 | 120+80+60+90 = 350 | 3+2+2+2 = 9 | 23 | ✓ |

Feasible subsets and their values: {P2,P4,P5,P6}=24, {P1,P4,P5,P6}=27, **{P1,P2,P4,P6}=28**, {P1,P2,P4,P5}=26, {P1,P2,P5,P6}=23.

### Step 4: Optimal Selection

**Fund P1, P2, P4, P6** — total strategic value = **28**.

No 3-project subset can exceed 10+9+8 = 27, so no smaller portfolio beats this. No 5-project subset is feasible (shown above). The optimum is confirmed.

---

## Verification

**Cost check:**
```
P1:  $120K
P2:   $80K
P4:  $150K
P6:   $90K
     ------
     $440K  ≤  $500K  ✓
```

**Dev-month check:**
```
P1:  3 DM
P2:  2 DM
P4:  3 DM
P6:  2 DM
     ----
     10 DM  ≤  10 DM  ✓  (exactly at limit)
```

**Value computation:**
```
P1:  8
P2:  5
P4:  9
P6:  6
     --
     28
```

**Alternative considered — {P1, P4, P5, P6}, value = 27:**

```
Cost:  120+150+60+90 = 420K  ≤ 500K  ✓
DM:    3+3+2+2       = 10    ≤ 10    ✓
Value: 8+9+4+6       = 27
```

This portfolio is feasible but scores **27 vs. 28**. The difference: swapping P5 (value 4, $60K, 2 DM) for P2 (value 5, $80K, 2 DM) costs $20K more but uses the same dev-months and gains 1 unit of value. Since $20K of budget remains available ($500K − $420K = $80K remaining vs. $80K − $60K = $20K delta), the swap is affordable and strictly improves the objective.

**Conclusion:** The optimal portfolio is **{P1, P2, P4, P6}** at $440K, 10 developer-months, and total strategic value **28**.

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=OFF (LLM reasoning only) |
| LLM calls | 2 |
| Stage 1 — direct LLM solve (s) | 84.70 |
| Stage 2 — interpretation (s) | — |
| Total latency (s) | 90.40 |
| Input tokens | 1,838 |
| Output tokens | 1,071 |
| Total tokens | 2,909 |