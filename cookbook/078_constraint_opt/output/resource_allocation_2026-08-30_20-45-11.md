# Resource Allocation Report

**Problem:** An IT department must select a portfolio of projects for next year. Twenty candidate projects are available. Project P1 costs $80K/2mo/value 6. Project P2 costs $120K/3mo/value 9. Project P3 costs $60K/2mo/value 5. Project P4 costs $150K/4mo/value 11. Project P5 costs $200K/5mo/value 12. Project P6 costs $90K/2mo/value 7. Project P7 costs $110K/3mo/value 8. Project P8 costs $70K/2mo/value 5. Project P9 costs $180K/4mo/value 13. Project P10 costs $100K/3mo/value 6. Project P11 costs $130K/3mo/value 10. Project P12 costs $85K/2mo/value 6. Project P13 costs $160K/4mo/value 12. Project P14 costs $75K/2mo/value 5. Project P15 costs $220K/5mo/value 14. Project P16 costs $95K/3mo/value 7. Project P17 costs $140K/4mo/value 10. Project P18 costs $65K/2mo/value 5. Project P19 costs $170K/4mo/value 12. Project P20 costs $115K/3mo/value 8. Total budget $1000K, team capacity 25 developer-months. Each project fully funded or not. Maximize total strategic value.

## Solution

### Step 1 — Project Table with Ratios

| ID  | Cost ($K) | Dev-mo | Value | V/Cost   | V/DM  |
|-----|-----------|--------|-------|----------|-------|
| P1  | 80        | 2      | 6     | 0.0750   | 3.000 |
| P2  | 120       | 3      | 9     | 0.0750   | 3.000 |
| P3  | 60        | 2      | 5     | **0.0833** | 2.500 |
| P4  | 150       | 4      | 11    | 0.0733   | 2.750 |
| P5  | 200       | 5      | 12    | 0.0600   | 2.400 |
| P6  | 90        | 2      | 7     | 0.0778   | **3.500** |
| P7  | 110       | 3      | 8     | 0.0727   | 2.667 |
| P8  | 70        | 2      | 5     | 0.0714   | 2.500 |
| P9  | 180       | 4      | 13    | 0.0722   | **3.250** |
| P10 | 100       | 3      | 6     | 0.0600   | 2.000 |
| P11 | 130       | 3      | 10    | 0.0769   | **3.333** |
| P12 | 85        | 2      | 6     | 0.0706   | 3.000 |
| P13 | 160       | 4      | 12    | 0.0750   | 3.000 |
| P14 | 75        | 2      | 5     | 0.0667   | 2.500 |
| P15 | 220       | 5      | 14    | 0.0636   | 2.800 |
| P16 | 95        | 3      | 7     | 0.0737   | 2.333 |
| P17 | 140       | 4      | 10    | 0.0714   | 2.500 |
| P18 | 65        | 2      | 5     | 0.0769   | 2.500 |
| P19 | 170       | 4      | 12    | 0.0706   | 3.000 |
| P20 | 115       | 3      | 8     | 0.0696   | 2.667 |

**Total pool**: $2,415K budget, 62 dev-months across all 20 projects. We must select at most ~41% by budget and ~40% by dev-months — both constraints bite simultaneously, so a 2D analysis is required.

---

### Step 2 — Structured Enumeration Strategy

With 2²⁰ ≈ 1,048,576 subsets, exhaustive enumeration is impractical by hand. Instead:

1. **Greedy pass by V/Cost** to get a feasible baseline.
2. **Greedy pass by V/DM** to exploit the tight dev-month constraint.
3. **Structured swap testing**: for each candidate, try replacing projects to improve value without violating either constraint.

**Key observation**: The two constraints pull in different directions for some projects. P9 ranks 11th by V/Cost (0.0722) but 3rd by V/DM (3.250). A good portfolio must balance both.

---

### Step 3 — Candidate Subsets

**Candidate A — Greedy by V/Cost ratio:**

Take projects in order: P3, P6, P11, P18, P1, P2, P13, P16, P4 (stopping when adding the next project would violate a constraint).

| Running total after adding… | Cost ($K) | DM | Value |
|---|---|---|---|
| + P3  | 60   | 2  | 5  |
| + P6  | 150  | 4  | 12 |
| + P11 | 280  | 7  | 22 |
| + P18 | 345  | 9  | 27 |
| + P1  | 425  | 11 | 33 |
| + P2  | 545  | 14 | 42 |
| + P13 | 705  | 18 | 54 |
| + P16 | 800  | 21 | 61 |
| + P4  | 950  | 25 | 72 |

**Candidate A result**: Cost = $950K, DM = 25, Value = **72**. Remaining budget $50K, but DM is exhausted.

---

**Candidate B — Exploit 2-DM efficiency:**

The seven 2-DM projects (P1, P3, P6, P8, P12, P14, P18) pack the most value per dev-month consumed. Take the five highest-value ones: P1(6), P6(7), P12(6), P3(5), P18(5) = value 29, cost $380K, 10 DM. Then fill remaining 15 DM / $620K with top-ranked larger projects.

Best group for 15 DM and $620K from 3-4-DM projects:

- P9(180,4,13) + P13(160,4,12) + P11(130,3,10) + P4(150,4,11)
  - Cost: 180+160+130+150 = **$620K** ✓
  - DM: 4+4+3+4 = **15** ✓
  - Value: 13+12+10+11 = **46**

**Candidate B result**: Cost = 380+620 = **$1,000K**, DM = 10+15 = **25**, Value = 29+46 = **75**.

---

**Swap tests on Candidate B (to check for value 76):**

For any improvement, we need to drop a selected project (Pi) and add an unselected project (Pj) with cost(Pj) ≤ cost(Pi), DM(Pj) ≤ DM(Pi), and value(Pj) > value(Pi). Since both constraints are fully saturated, no slack exists.

| Drop | Freed ($K / DM) | Best unselected replacement | Gain? |
|---|---|---|---|
| P18 (65, 2dm, 5) | 65 / 2 | P8(70>65) or P14(75>65) — over budget | No |
| P3 (60, 2dm, 5)  | 60 / 2 | No unselected project costs ≤$60K | No |
| P1 (80, 2dm, 6)  | 80 / 2 | P8(val=5<6), P14(val=5<6) | No |
| P12 (85, 2dm, 6) | 85 / 2 | P8(val=5<6), P14(val=5<6) | No |
| P6 (90, 2dm, 7)  | 90 / 2 | P8(val=5<7), P14(val=5<7) | No |
| P11 (130, 3dm, 10) | 130 / 3 | P2(val=9<10), P7(val=8<10) | No |
| P4 (150, 4dm, 11) | 150 / 4 | P17(val=10<11), P19(170>150) | No |
| P13 (160, 4dm, 12) | 160 / 4 | P19(170>160), P17(val=10<12) | No |
| P9 (180, 4dm, 13) | 180 / 4 | P19(val=12<13), nothing else ≥13 | No |

**Two-for-one swap check (replace one selected with two unselected):**
The most promising case is replacing P4(150K, 4DM, val 11) with two cheaper projects totaling ≤150K, ≤4DM, value > 11. The best available pair is P8(70K,2DM,5) + P14(75K,2DM,5) = $145K, 4DM, value **10 < 11**. No valid improvement exists.

No swap improves value. **75 is optimal.**

---

### Step 4 — Optimal Selection

**Selected portfolio: {P1, P3, P4, P6, P9, P11, P12, P13, P18}**

| Project | Cost ($K) | Dev-months | Value |
|---------|-----------|------------|-------|
| P1      | 80        | 2          | 6     |
| P3      | 60        | 2          | 5     |
| P4      | 150       | 4          | 11    |
| P6      | 90        | 2          | 7     |
| P9      | 180       | 4          | 13    |
| P11     | 130       | 3          | 10    |
| P12     | 85        | 2          | 6     |
| P13     | 160       | 4          | 12    |
| P18     | 65        | 2          | 5     |
| **Total** | **1,000** | **25**   | **75** |

---

## Verification

### Budget constraint

```
80 + 60 + 150 + 90 + 180 + 130 + 85 + 160 + 65
= (80 + 60) + (150 + 90) + (180 + 130) + (85 + 160) + 65
= 140 + 240 + 310 + 245 + 65
= 380 + 310 + 245 + 65
= 690 + 310
= 1,000
```

**$1,000K ≤ $1,000K** ✓ (exactly at limit)

### Dev-month constraint

```
2 + 2 + 4 + 2 + 4 + 3 + 2 + 4 + 2
= (2 + 2 + 2 + 2 + 2) + (4 + 4 + 4) + 3
= 10 + 12 + 3
= 25
```

**25 ≤ 25** ✓ (exactly at limit)

### Total value

```
6 + 5 + 11 + 7 + 13 + 10 + 6 + 12 + 5
= (6 + 5 + 7 + 6 + 5) + (11 + 13 + 10 + 12)
= 29 + 46
= 75
```

**Total strategic value = 75** ✓

---

### Alternative considered: Candidate A (Greedy by V/Cost)

**Portfolio**: {P1, P2, P3, P4, P6, P11, P13, P16, P18}

Budget check:
```
80 + 120 + 60 + 150 + 90 + 130 + 160 + 95 + 65
= 140 + 240 + 310 + 95 + 65 = 950
$950K ≤ $1,000K ✓
```

Dev-month check:
```
2 + 3 + 2 + 4 + 2 + 3 + 4 + 3 + 2 = 25 ≤ 25 ✓
```

Value:
```
6 + 9 + 5 + 11 + 7 + 10 + 12 + 7 + 5 = 72
```

**Why it scores lower**: The greedy-by-V/Cost heuristic selects P2 (val 9, $120K, 3DM) and P16 (val 7, $95K, 3DM), consuming $215K and 6 DM for a combined value of 16. The optimal portfolio instead selects P9 (val 13, $180K, 4DM) and P12 (val 6, $85K, 2DM), spending $265K for 6 DM but delivering value 19 — a gain of 3 value for $50K more, which fits within the $50K remaining budget of Candidate A. The greedy-by-cost heuristic misses P9 because P9's V/Cost ratio (0.0722) ranks it only 11th, yet P9 is the 3rd most efficient project by V/DM (3.25) — a distinction the single-ratio greedy cannot capture.

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=OFF (LLM reasoning only) |
| LLM calls | 2 |
| Stage 1 — direct LLM solve (s) | 433.40 |
| Stage 2 — interpretation (s) | — |
| Total latency (s) | 443.60 |
| Input tokens | 2,698 |
| Output tokens | 2,071 |
| Total tokens | 4,769 |