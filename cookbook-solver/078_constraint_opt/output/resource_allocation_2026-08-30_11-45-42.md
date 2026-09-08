# Resource Allocation Report

**Problem:** An IT department must select a portfolio of projects for next quarter. Six candidate projects are available. Project P1 costs $120K and requires 3 developer-months, delivering strategic value 8. Project P2 costs $80K and requires 2 developer-months, delivering value 5. Project P3 costs $200K and requires 5 developer-months, delivering value 10. Project P4 costs $150K and requires 3 developer-months, delivering value 9. Project P5 costs $60K and requires 2 developer-months, delivering value 4. Project P6 costs $90K and requires 2 developer-months, delivering value 6. The total budget is $500K and the team has 10 developer-months available. Each project is either fully funded or not funded - no partial investment. Select which projects to fund to maximize total strategic value.

## Solution

### Step 1: Project data

| Project | Cost ($K) | Dev-months | Value | Value/Cost | Value/Dev |
|---------|-----------|------------|-------|------------|-----------|
| P1 | 120 | 3 | 8 | 0.0667 | 2.67 |
| P2 | 80 | 2 | 5 | 0.0625 | 2.50 |
| P3 | 200 | 5 | 10 | 0.0500 | 2.00 |
| P4 | 150 | 3 | 9 | 0.0600 | 3.00 |
| P5 | 60 | 2 | 4 | 0.0667 | 2.00 |
| P6 | 90 | 2 | 6 | 0.0667 | 3.00 |

Constraints: Budget ≤ $500K, Dev-months ≤ 10.

### Step 2: Search space and strategy

2^6 = 64 subsets total. Two binding constraints (budget and dev-months) make this a two-dimensional 0/1 knapsack. Strategy: rank by value/cost ratio, greedily build a candidate, then exhaustively check all 4-project subsets (the only feasible cardinality, as shown below).

**Feasibility bounds by cardinality:**

- **5- or 6-project subsets:** The five cheapest-on-dev projects without P3 are {P1,P2,P4,P5,P6} with 3+2+3+2+2 = 12 dev-months > 10. Any 5-project set including P3 needs at least 5+9 = 14 dev-months. *All 5- and 6-project subsets are infeasible.*
- **3-project subsets:** Maximum possible value is P3+P4+P6 = 10+9+6 = 25. Cannot beat a good 4-project result.
- **4-project subsets without P3:** C(5,4) = 5 candidates (removing P3 leaves {P1,P2,P4,P5,P6}).
- **4-project subsets with P3:** P3 alone consumes 5 dev-months; the three smallest remaining projects consume 2+2+2 = 6, giving 5+6 = 11 > 10. *All 4-project sets with P3 are infeasible.*

This reduces the search to the **5 four-project subsets from {P1,P2,P4,P5,P6}**.

### Step 3: Enumerate the 5 feasible 4-project subsets

| Subset | Dev-months | Cost ($K) | Value |
|--------|------------|-----------|-------|
| {P1,P2,P4,P5} | 3+2+3+2 = 10 | 120+80+150+60 = 410 | 8+5+9+4 = **26** |
| **{P1,P2,P4,P6}** | 3+2+3+2 = 10 | 120+80+150+90 = 440 | 8+5+9+6 = **28** |
| {P1,P2,P5,P6} | 3+2+2+2 = 9 | 120+80+60+90 = 350 | 8+5+4+6 = **23** |
| {P1,P4,P5,P6} | 3+3+2+2 = 10 | 120+150+60+90 = 420 | 8+9+4+6 = **27** |
| {P2,P4,P5,P6} | 2+3+2+2 = 9 | 80+150+60+90 = 380 | 5+9+4+6 = **24** |

### Step 4: Optimal selection

**Fund P1, P2, P4, P6 — total strategic value = 28.**

---

## Verification

**Budget check:**
120 + 80 + 150 + 90 = 200 + 240 = 440K ≤ 500K ✓

**Dev-months check:**
3 + 2 + 3 + 2 = 10 ≤ 10 ✓

**Value computation:**
8 + 5 + 9 + 6 = 28 ✓

**Alternative considered — {P1, P4, P5, P6}:**
- Cost: 120 + 150 + 60 + 90 = 420K ≤ 500K ✓
- Dev: 3 + 3 + 2 + 2 = 10 ✓
- Value: 8 + 9 + 4 + 6 = **27**

This subset replaces P2 (value 5) with P5 (value 4), losing 1 unit of value for a $20K saving that cannot be redeployed (dev-months are already at the cap). It is feasible but strictly suboptimal.

**Alternative considered — {P3, P4, P6} (best 3-project set):**
- Cost: 200 + 150 + 90 = 440K ✓
- Dev: 5 + 3 + 2 = 10 ✓
- Value: 10 + 9 + 6 = **25**

P3's high absolute value (10) is offset by its large dev-month footprint (5), which prevents adding a fourth project. The optimal portfolio achieves value 28 by including four projects at the cost of dropping P3.

**Conclusion:** No feasible subset achieves value > 28. The optimal portfolio is **{P1, P2, P4, P6}** with total value **28**, total cost **$440K**, and total dev-months **10**.

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=OFF (LLM reasoning only) |
| LLM calls | 2 |
| Stage 1 — direct LLM solve (s) | 78.30 |
| Stage 2 — interpretation (s) | — |
| Total latency (s) | 84.60 |
| Input tokens | 1,683 |
| Output tokens | 917 |
| Total tokens | 2,600 |