# SPL Run: resource_allocation

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 471 in / 1158 out
- **Latency:** 77453ms
- **Timestamp:** 2026-08-30 07:21:57

## Output

```output
# Resource Allocation Report

**Problem:** An IT department must select a portfolio of projects for next quarter. Six candidate projects are available. Project P1 costs $120K and requires 3 developer-months, delivering strategic value 8. Project P2 costs $80K and requires 2 developer-months, delivering value 5. Project P3 costs $200K and requires 5 developer-months, delivering value 10. Project P4 costs $150K and requires 3 developer-months, delivering value 9. Project P5 costs $60K and requires 2 developer-months, delivering value 4. Project P6 costs $90K and requires 2 developer-months, delivering value 6. The total budget is $500K and the team has 10 developer-months available. Each project is either fully funded or not funded — no partial investment. Select which projects to fund to maximize total strategic value.

## Solution

### Step 1 — Project Data

| Project | Cost ($K) | Dev-months | Value |
|---------|-----------|------------|-------|
| P1 | 120 | 3 | 8 |
| P2 | 80 | 2 | 5 |
| P3 | 200 | 5 | 10 |
| P4 | 150 | 3 | 9 |
| P5 | 60 | 2 | 4 |
| P6 | 90 | 2 | 6 |

**Constraints:** Total cost ≤ $500K, total dev-months ≤ 10.

---

### Step 2 — Search Space and Prioritisation

With n = 6 projects the full search space is 2⁶ = 64 subsets. Rather than enumerate all 64, compute two efficiency ratios to guide structured search.

**Value / Cost (per $K):**

- P1: 8 ÷ 120 = 0.0667
- P2: 5 ÷ 80  = 0.0625
- P3: 10 ÷ 200 = 0.0500
- P4: 9 ÷ 150 = 0.0600
- P5: 4 ÷ 60  = 0.0667
- P6: 6 ÷ 90  = 0.0667

**Value / Dev-month:**

- P1: 8 ÷ 3 = 2.67
- P2: 5 ÷ 2 = 2.50
- P3: 10 ÷ 5 = 2.00
- P4: 9 ÷ 3 = 3.00  ← highest
- P5: 4 ÷ 2 = 2.00
- P6: 6 ÷ 2 = 3.00  ← highest

P4 and P6 are the most efficient users of the binding constraint (dev-months). P1, P5, P6 share the best cost efficiency. P3 is weak on both; it consumes 5 of 10 dev-months for only 10 value.

**Observation:** A 5-project or 6-project portfolio is almost certainly infeasible. The five cheapest projects (P2+P5+P6+P1+P4) cost exactly $500K but require 2+2+2+3+3 = 12 dev-months — already over the headcount limit. So the optimum must be 3 or 4 projects.

---

### Step 3 — Enumerate Candidate Subsets

**C(6,4) = 15 four-project subsets.** Feasibility requires cost ≤ 500 and dev ≤ 10 simultaneously.

| Subset | Cost ($K) | Dev-months | Value | Feasible? |
|--------|-----------|------------|-------|-----------|
| P1+P2+P3+P4 | 120+80+200+150 = 550 | 13 | 27 | No — cost AND dev |
| P1+P2+P3+P5 | 120+80+200+60 = 460 | 12 | 27 | No — dev |
| P1+P2+P3+P6 | 120+80+200+90 = 490 | 12 | 29 | No — dev |
| **P1+P2+P4+P5** | 120+80+150+60 = **410** | 3+2+3+2 = **10** | 8+5+9+4 = **26** | **Yes** |
| **P1+P2+P4+P6** | 120+80+150+90 = **440** | 3+2+3+2 = **10** | 8+5+9+6 = **28** | **Yes** |
| **P1+P2+P5+P6** | 120+80+60+90 = **350** | 3+2+2+2 = **9** | 8+5+4+6 = **23** | **Yes** |
| P1+P3+P4+P5 | 120+200+150+60 = 530 | 13 | 31 | No — cost AND dev |
| P1+P3+P4+P6 | 120+200+150+90 = 560 | 13 | 33 | No — cost AND dev |
| P1+P3+P5+P6 | 120+200+60+90 = 470 | 12 | 28 | No — dev |
| **P1+P4+P5+P6** | 120+150+60+90 = **420** | 3+3+2+2 = **10** | 8+9+4+6 = **27** | **Yes** |
| P2+P3+P4+P5 | 80+200+150+60 = 490 | 12 | 28 | No — dev |
| P2+P3+P4+P6 | 80+200+150+90 = 520 | 12 | 30 | No — cost AND dev |
| P2+P3+P5+P6 | 80+200+60+90 = 430 | 11 | 25 | No — dev |
| **P2+P4+P5+P6** | 80+150+60+90 = **380** | 2+3+2+2 = **9** | 5+9+4+6 = **24** | **Yes** |
| P3+P4+P5+P6 | 200+150+60+90 = 500 | 12 | 29 | No — dev |

**Feasible four-project subsets and their values:**

| Subset | Value |
|--------|-------|
| P1+P2+P4+P6 | **28** ← best |
| P1+P4+P5+P6 | 27 |
| P1+P2+P4+P5 | 26 |
| P2+P4+P5+P6 | 24 |
| P1+P2+P5+P6 | 23 |

**Best three-project subsets** (verified for completeness):
The highest-value feasible three-project combos include P3+P4+P6 (cost=440, dev=10, value=25) and P3+P4+P2 (cost=430, dev=10, value=24) — both under 28.

**Optimal selection: P1 + P2 + P4 + P6, total value = 28.**

---

### Step 4 — Optimal Selection

Fund **P1, P2, P4, P6**. Do not fund P3 or P5.

---

## Verification

### Feasibility check

**Budget:**
```
P1: $120K
P2:  $80K
P4: $150K
P6:  $90K
─────────
     $440K  ≤  $500K  ✓
```

**Dev-months:**
```
P1: 3
P2: 2
P4: 3
P6: 2
────
  10  ≤  10  ✓
```

**Total strategic value:**
```
P1:  8
P2:  5
P4:  9
P6:  6
────
  28
```

---

### Alternative considered — P1+P4+P5+P6 (value 27)

This is the next-best feasible subset. It swaps P2 ($80K, 2 dev-months, value 5) for P5 ($60K, 2 dev-months, value 4), saving $20K but losing 1 unit of value.

```
Cost: 120+150+60+90 = 420 ≤ 500  ✓
Dev:    3+ 3+ 2+ 2  = 10 ≤ 10   ✓
Value:  8+ 9+ 4+ 6  = 27  <  28  ✗ (suboptimal)
```

The freed $20K cannot fund any additional project (cheapest remaining is P3 at $200K or P2 at $80K, but dev-months are exhausted at 10). So adding P2 instead of P5 strictly improves value by 1 with no constraint violation.

---

### Why other high-value subsets fail

**P1+P2+P3+P6** would deliver value 8+5+10+6 = 29 but requires 3+2+5+2 = **12 dev-months** — two over the limit. No swap can rescue it without dropping P3, which eliminates the value advantage.

**P3+P4+P5+P6** achieves value 29 with cost exactly $500K but uses 5+3+2+2 = **12 dev-months** — also infeasible.

---

**Conclusion:** The optimal portfolio is **{P1, P2, P4, P6}** with total strategic value = **28**, total cost = **$440K**, and total dev-months = **10**. No feasible selection achieves a higher value.

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=OFF (LLM reasoning only) |
| LLM calls | 1 |
| Stage 1 — direct LLM solve (s) | 76.50 |
| Stage 2 — interpretation (s) | — |
| Total latency (s) | 76.90 |
| Input tokens | 471 |
| Output tokens | 1,158 |
| Total tokens | 1,629 |
```
