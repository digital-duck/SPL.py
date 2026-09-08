# Experiment H2 — Scale Sensitivity Study

**Hypothesis:** solver=OFF (LLM direct reasoning) correctness degrades as n grows; solver=ON correctness remains flat because CBC handles any size problem in milliseconds.

**Design:** 4 recipes × 2 scales (n=10, n=20) × 2 conditions (solver=ON, solver=OFF) = 16 runs.  
**Model:** `claude-sonnet-4-6` via `claude_cli`  
**Ground truth:** solver=ON establishes the verified optimal for each problem; solver=OFF is correct iff it matches.

**What "n" means per recipe:**

| Recipe | n | Default | n=10 | n=20 |
|---|---|---|---|---|
| `constraint_opt` (LP) | decision variables (product types) | 2 products | 10 products | 20 products |
| `supply_chain` (transport LP) | warehouse×store routes | 6 routes (2×3) | 20 routes (4×5) | 40 routes (8×5) |
| `staff_scheduling` (ILP) | nurses | 5 nurses, 3 shifts | 10 nurses, 4 shifts | 20 nurses, 5 shifts |
| `resource_allocation` (Binary ILP) | projects (2^n candidate subsets) | 6 → 64 subsets | 10 → 1,024 subsets | 20 → ~1M subsets |

**Expected LLM difficulty by recipe and n:**

| | n=10 | n=20 |
|---|---|---|
| LP (corners) | Borderline — LP has structure; LLM may use ratio reasoning | Very likely fails — C(25,5)=53,130 vertices |
| Transport LP (MODI) | Hard — 20-route tableau too large to track mentally | Almost certain failure — 40-route MODI intractable by hand |
| ILP scheduling | Moderate — degenerate structure may still force a solution | Likely fails — 100 binary variables, no obvious forced assignment |
| Binary ILP (enum.) | Almost certain failure — 1,024 subsets unmanageable | Certain failure — ~1M subsets |

---

## Recipe 1: `constraint_opt.spl` — Production Planning LP

### n=10: Furniture factory, 10 products, 4 resource constraints

```bash
export PROBLEM_R1_N10="A furniture factory produces 10 product lines. Each unit requires labor (hours), lumber (kg), upholstery fabric (m²), and steel (kg), and earns a fixed profit. Product specifications per unit: Dining Chair needs 2.0h labor, 3.0kg lumber, 0.8m² fabric, 0.0kg steel, profit \$25. Dining Table needs 4.0h labor, 8.0kg lumber, 0.0m² fabric, 0.0kg steel, profit \$55. Office Desk needs 3.5h labor, 5.0kg lumber, 0.0m² fabric, 1.5kg steel, profit \$45. Bookcase needs 5.0h labor, 9.0kg lumber, 0.0m² fabric, 0.5kg steel, profit \$58. Wardrobe needs 7.0h labor, 14.0kg lumber, 0.0m² fabric, 0.5kg steel, profit \$85. Armchair needs 3.0h labor, 2.0kg lumber, 1.5m² fabric, 0.0kg steel, profit \$48. Bed Frame needs 5.0h labor, 10.0kg lumber, 0.0m² fabric, 2.0kg steel, profit \$72. Coffee Table needs 2.0h labor, 4.0kg lumber, 0.0m² fabric, 0.0kg steel, profit \$28. Storage Cabinet needs 4.0h labor, 7.0kg lumber, 0.0m² fabric, 1.0kg steel, profit \$52. Lounge Sofa needs 4.0h labor, 3.0kg lumber, 2.5m² fabric, 0.0kg steel, profit \$68. Available daily: 120 labor hours, 150 kg lumber, 15 m² upholstery fabric, 12 kg steel. Production quantities are continuous (fractional units allowed). Maximize total daily profit."

# solver=ON
spl3 run cookbook/78_constraint_opt/constraint_opt.spl \
    --llm claude_cli --param use_solver=true \
    --param problem="$PROBLEM_R1_N10"

# solver=OFF
spl3 run cookbook/78_constraint_opt/constraint_opt.spl \
    --llm claude_cli --param use_solver=false \
    --param problem="$PROBLEM_R1_N10"
```

**Why it is hard at n=10:** The feasible region is the intersection of 4 hyperplanes in 10-dimensional space. The optimal corner is not reachable by single-product ratio analysis — the binding constraints involve a mixture of products. The LLM would need to run simplex mentally across 10 variables, which is infeasible.

**LLM failure mode to watch:** Greedy by profit/labor ratio (Wardrobe: $85/7h = $12.1/h is highest) ignores lumber and fabric binding constraints. Expected error: LLM maximizes one or two high-ratio products and misses the mixed-product optimal.

---

### n=20: Furniture factory, 20 products, 5 resource constraints

```bash
export PROBLEM_R1_N20="A furniture factory produces 20 product lines. Each unit requires labor (hours), lumber (kg), upholstery fabric (m²), steel (kg), and finishing time (hours), and earns a fixed profit. Product specifications per unit — Dining Chair: 2.0h labor, 3.0kg lumber, 0.8m² fabric, 0.0kg steel, 0.5h finish, \$25 profit. Dining Table: 4.0h labor, 8.0kg lumber, 0.0m² fabric, 0.0kg steel, 1.0h finish, \$55 profit. Office Desk: 3.5h labor, 5.0kg lumber, 0.0m² fabric, 1.5kg steel, 0.8h finish, \$45 profit. Bookcase: 5.0h labor, 9.0kg lumber, 0.0m² fabric, 0.5kg steel, 1.0h finish, \$58 profit. Wardrobe: 7.0h labor, 14.0kg lumber, 0.0m² fabric, 0.5kg steel, 1.5h finish, \$85 profit. Armchair: 3.0h labor, 2.0kg lumber, 1.5m² fabric, 0.0kg steel, 0.5h finish, \$48 profit. Bed Frame: 5.0h labor, 10.0kg lumber, 0.0m² fabric, 2.0kg steel, 1.2h finish, \$72 profit. Coffee Table: 2.0h labor, 4.0kg lumber, 0.0m² fabric, 0.0kg steel, 0.4h finish, \$28 profit. Storage Cabinet: 4.0h labor, 7.0kg lumber, 0.0m² fabric, 1.0kg steel, 0.8h finish, \$52 profit. Lounge Sofa: 4.0h labor, 3.0kg lumber, 2.5m² fabric, 0.0kg steel, 0.6h finish, \$68 profit. Nightstand: 1.5h labor, 2.5kg lumber, 0.0m² fabric, 0.0kg steel, 0.3h finish, \$20 profit. Dresser: 4.5h labor, 8.0kg lumber, 0.0m² fabric, 0.5kg steel, 1.0h finish, \$62 profit. Vanity Table: 3.0h labor, 4.5kg lumber, 0.0m² fabric, 1.0kg steel, 0.7h finish, \$42 profit. Ottoman: 2.0h labor, 1.0kg lumber, 1.2m² fabric, 0.0kg steel, 0.3h finish, \$35 profit. Side Table: 1.5h labor, 2.0kg lumber, 0.0m² fabric, 0.0kg steel, 0.3h finish, \$18 profit. Media Console: 3.5h labor, 6.0kg lumber, 0.0m² fabric, 0.5kg steel, 0.7h finish, \$48 profit. Hall Tree: 3.0h labor, 5.0kg lumber, 0.0m² fabric, 1.0kg steel, 0.6h finish, \$40 profit. Shoe Rack: 2.0h labor, 3.5kg lumber, 0.0m² fabric, 0.5kg steel, 0.4h finish, \$24 profit. Bar Cart: 2.5h labor, 1.5kg lumber, 0.0m² fabric, 2.5kg steel, 0.5h finish, \$38 profit. Rocking Chair: 3.5h labor, 4.0kg lumber, 0.5m² fabric, 0.0kg steel, 0.7h finish, \$44 profit. Available daily: 200 labor hours, 250 kg lumber, 20 m² upholstery fabric, 18 kg steel, 30 finishing hours. Production quantities are continuous (fractional units allowed). Maximize total daily profit."

# solver=ON
spl3 run cookbook/78_constraint_opt/constraint_opt.spl \
    --llm claude_cli --param use_solver=true \
    --param problem="$PROBLEM_R1_N20"

# solver=OFF
spl3 run cookbook/78_constraint_opt/constraint_opt.spl \
    --llm claude_cli --param use_solver=false \
    --param problem="$PROBLEM_R1_N20"
```

**Why it is hard at n=20:** 20 continuous variables, 5 binding constraints. C(25,5) = 53,130 candidate corner points. The optimal involves a non-obvious mixture across all 5 binding constraints. Any single-ratio greedy approach misses the true optimum by a significant margin.

---

## Recipe 2: `supply_chain.spl` — Transportation LP

### n=20 routes: 4 warehouses × 5 stores

```bash
export PROBLEM_R2_N20="A regional distributor has 4 warehouses and 5 retail stores. Warehouse W1 holds 90 units, W2 holds 70 units, W3 holds 80 units, W4 holds 60 units (total supply 300). Store S1 needs 60 units, S2 needs 55 units, S3 needs 70 units, S4 needs 50 units, S5 needs 65 units (total demand 300). Shipping cost per unit: W1 to S1 \$3, W1 to S2 \$2, W1 to S3 \$5, W1 to S4 \$8, W1 to S5 \$4. W2 to S1 \$6, W2 to S2 \$4, W2 to S3 \$3, W2 to S4 \$5, W2 to S5 \$7. W3 to S1 \$4, W3 to S2 \$7, W3 to S3 \$2, W3 to S4 \$6, W3 to S5 \$3. W4 to S1 \$8, W4 to S2 \$5, W4 to S3 \$6, W4 to S4 \$2, W4 to S5 \$9. All store demand must be exactly met. Minimize total shipping cost."

# solver=ON
spl3 run cookbook/78_constraint_opt/supply_chain.spl \
    --llm claude_cli --param use_solver=true \
    --param problem="$PROBLEM_R2_N20"

# solver=OFF
spl3 run cookbook/78_constraint_opt/supply_chain.spl \
    --llm claude_cli --param use_solver=false \
    --param problem="$PROBLEM_R2_N20"
```

**Why it is hard at n=20 routes:** The MODI method (u-v potentials) requires tracking 9 basic variables in a 4×5 tableau through multiple improvement cycles. Manual application on a 20-route problem typically requires 3–5 tableau iterations, each updating all 20 cost entries. LLM working memory is insufficient for this.

**LLM failure mode to watch:** Northwest Corner Method produces an initial feasible solution but is rarely optimal. LLM may stop at NWC without iterating improvement, or lose track of dual variables during MODI.

**Known structure:** The low-cost routes are W1→S2 ($2), W3→S3 ($2), W4→S4 ($2). The optimal will route large volumes through these three routes. Solver=ON will establish the exact optimum.

---

### n=40 routes: 8 warehouses × 5 stores

```bash
export PROBLEM_R2_N40="A national distributor operates 8 warehouses and 5 regional distribution centers. Warehouse capacities: W1=100 units, W2=80 units, W3=90 units, W4=70 units, W5=60 units, W6=85 units, W7=75 units, W8=65 units (total supply 625). Distribution center requirements: D1=120 units, D2=110 units, D3=130 units, D4=140 units, D5=125 units (total demand 625). Shipping cost per unit — W1: to D1 \$4, D2 \$2, D3 \$6, D4 \$9, D5 \$5. W2: to D1 \$7, D2 \$5, D3 \$3, D4 \$6, D5 \$8. W3: to D1 \$3, D2 \$8, D3 \$2, D4 \$7, D5 \$4. W4: to D1 \$9, D2 \$4, D3 \$7, D4 \$2, D5 \$10. W5: to D1 \$5, D2 \$3, D3 \$8, D4 \$4, D5 \$6. W6: to D1 \$6, D2 \$7, D3 \$4, D4 \$5, D5 \$2. W7: to D1 \$8, D2 \$6, D3 \$5, D4 \$3, D5 \$7. W8: to D1 \$2, D2 \$9, D3 \$7, D4 \$8, D5 \$3. All distribution center demand must be exactly met. Minimize total shipping cost."

# solver=ON
spl3 run cookbook/78_constraint_opt/supply_chain.spl \
    --llm claude_cli --param use_solver=true \
    --param problem="$PROBLEM_R2_N40"

# solver=OFF
spl3 run cookbook/78_constraint_opt/supply_chain.spl \
    --llm claude_cli --param use_solver=false \
    --param problem="$PROBLEM_R2_N40"
```

**Why it is hard at n=40 routes:** 40-route tableau, up to 12 basic variables in the spanning tree. Each MODI iteration updates all 40 cost entries. Virtually impossible to complete mentally without error. Even setting up the initial NWC solution on an 8×5 matrix is error-prone.

---

## Recipe 3: `staff_scheduling.spl` — Shift Assignment ILP

### n=10 nurses, 4 shifts

```bash
export PROBLEM_R3_N10="A hospital clinic needs to staff one day with 4 shifts: Early Morning (5am–1pm), Day (9am–5pm), Evening (1pm–9pm), and Night (9pm–5am). Minimum nurse coverage: Early Morning needs at least 2 nurses, Day needs at least 3 nurses, Evening needs at least 3 nurses, Night needs at least 2 nurses (total minimum 10 slots). Ten nurses are available: Nurse1 through Nurse10. Each nurse can work at most 1 shift today. Wage per nurse-shift: Early Morning costs \$280, Day costs \$220, Evening costs \$240, Night costs \$350. Assign nurses to shifts to meet all minimum coverage requirements at minimum total wage cost."

# solver=ON
spl3 run cookbook/78_constraint_opt/staff_scheduling.spl \
    --llm claude_cli --param use_solver=true \
    --param problem="$PROBLEM_R3_N10"

# solver=OFF
spl3 run cookbook/78_constraint_opt/staff_scheduling.spl \
    --llm claude_cli --param use_solver=false \
    --param problem="$PROBLEM_R3_N10"
```

**Known optimal (hand-verifiable):** Minimum slots total 10, nurses available = 10, so all nurses must be assigned and minimum is exactly met (same degenerate structure as default problem — no slack, so LLM may still solve by inspection). 

**Cost:** 2×$280 (EM) + 3×$220 (Day) + 3×$240 (Eve) + 2×$350 (Night) = $560 + $660 + $720 + $700 = **$2,640**

**Note for study:** This n=10 problem is degenerate (capacity = demand, same as default n=5). It tests whether the LLM recognizes the forced assignment structure. The real test is n=20.

---

### n=20 nurses, 5 shifts (non-degenerate — slack exists)

```bash
export PROBLEM_R3_N20="A regional hospital needs to staff one day with 5 shifts: Night (11pm–7am), Early Morning (6am–2pm), Day (10am–6pm), Evening (2pm–10pm), and Late Night (8pm–4am). Minimum nurse coverage requirements: Night needs at least 3 nurses, Early Morning needs at least 4 nurses, Day needs at least 5 nurses, Evening needs at least 4 nurses, Late Night needs at least 3 nurses (total minimum coverage 19 slots). Twenty nurses are available: Nurse1 through Nurse20. Each nurse can work at most 1 shift today. Wage per nurse-shift: Night costs \$380, Early Morning costs \$260, Day costs \$200, Evening costs \$230, Late Night costs \$310. Assign nurses to shifts to meet all minimum coverage requirements at minimum total wage cost. Note: total nurse capacity (20) exceeds minimum demand (19), so exactly one nurse will not be assigned to any shift — the solver must choose which nurse to leave unassigned to minimize cost."

# solver=ON
spl3 run cookbook/78_constraint_opt/staff_scheduling.spl \
    --llm claude_cli --param use_solver=true \
    --param problem="$PROBLEM_R3_N20"

# solver=OFF
spl3 run cookbook/78_constraint_opt/staff_scheduling.spl \
    --llm claude_cli --param use_solver=false \
    --param problem="$PROBLEM_R3_N20"
```

**Why it is hard at n=20:** This is the first non-degenerate scheduling problem in the study — 20 nurses, 19 minimum slots, 1 nurse left unassigned. The ILP must decide both the per-shift assignment AND which nurse to leave out. The cheapest approach is to fill the cheapest shifts first (Day: $200/nurse is cheapest), then leave the unassigned slot where the marginal cost is highest. But this is non-obvious when 20 nurses must be distributed across 5 shifts.

**Hand analysis:** To minimize cost, maximize nurses in cheapest shifts: Day($200) → Evening($230) → Early Morning($260) → Late Night($310) → Night($380). Minimizing total cost means we want the "unused" slot to be the Night shift (save $380). Fill Night with 3 (minimum), use the 1 spare capacity to not assign the 20th nurse there: assign 3 Night + 4 EM + 5 Day + 4 Eve + 3 LN = 19 nurses, leave 1 nurse unassigned.

**Expected optimal cost:** 3×$380 + 4×$260 + 5×$200 + 4×$230 + 3×$310 = $1,140 + $1,040 + $1,000 + $920 + $930 = **$5,030**

**LLM failure mode:** May assign all 20 nurses (violating nothing, but not minimizing — extra nurse goes to cheapest shift, but LLM may not optimize which extra slot to eliminate).

---

## Recipe 4: `resource_allocation.spl` — Project Portfolio Binary ILP

### n=10 projects: 2^10 = 1,024 candidate subsets

```bash
export PROBLEM_R4_N10="An IT department must select a portfolio of projects for next quarter. Ten candidate projects are available. Project P1 costs \$80K and requires 2 developer-months, delivering strategic value 6. Project P2 costs \$120K and requires 3 developer-months, delivering value 9. Project P3 costs \$60K and requires 2 developer-months, delivering value 5. Project P4 costs \$150K and requires 4 developer-months, delivering value 11. Project P5 costs \$200K and requires 5 developer-months, delivering value 12. Project P6 costs \$90K and requires 2 developer-months, delivering value 7. Project P7 costs \$110K and requires 3 developer-months, delivering value 8. Project P8 costs \$70K and requires 2 developer-months, delivering value 5. Project P9 costs \$180K and requires 4 developer-months, delivering value 13. Project P10 costs \$100K and requires 3 developer-months, delivering value 6. The total budget is \$600K and the team has 15 developer-months available. Each project is either fully funded or not — no partial investment. Select which projects to fund to maximize total strategic value."

# solver=ON
spl3 run cookbook/78_constraint_opt/resource_allocation.spl \
    --llm claude_cli --param use_solver=true \
    --param problem="$PROBLEM_R4_N10"

# solver=OFF
spl3 run cookbook/78_constraint_opt/resource_allocation.spl \
    --llm claude_cli --param use_solver=false \
    --param problem="$PROBLEM_R4_N10"
```

**Known optimal: value = 45**

Verified by enumeration of high-value candidate subsets:

| Subset | Cost | Dev-mo | Value | Feasible? |
|---|---|---|---|---|
| P9+P4+P2+P6+P3 | $180+150+120+90+60=$600K | 4+4+3+2+2=15 | 13+11+9+7+5=**45** | ✅ |
| P9+P2+P6+P1+P3+P8 | $180+120+90+80+60+70=$600K | 4+3+2+2+2+2=15 | 13+9+7+6+5+5=**45** | ✅ |
| P9+P4+P2+P7 | $180+150+120+110=$560K | 4+4+3+3=14 | 13+11+9+8=41 | ✅ (worse) |
| P5+P9+P4+P3 | $200+180+150+60=$590K | 5+4+4+2=15 | 12+13+11+5=41 | ✅ (worse) |

**Why LLM fails at n=10:** With 1,024 candidate subsets, the LLM cannot enumerate exhaustively (it managed C(6,4)=15 at n=6 in the default problem). The greedy by value/dev-month ratio approach:
- P9: 13/4=3.25, P6: 7/2=3.50 (highest), P2: 9/3=3.00, P1: 6/2=3.00 — greedy sequence misses that the optimal requires combining by *both* budget and headcount simultaneously.

**Note on multiple optima:** Two different subsets achieve value=45. The solver will report one; solver=OFF may report neither, report one correctly, or report a suboptimal value like 43 or 41.

---

### n=20 projects: 2^20 ≈ 1,048,576 candidate subsets

```bash
export PROBLEM_R4_N20="An IT department must select a portfolio of projects for next year. Twenty candidate projects are available. Project P1 costs \$80K and requires 2 developer-months, delivering value 6. Project P2 costs \$120K and requires 3 developer-months, delivering value 9. Project P3 costs \$60K and requires 2 developer-months, delivering value 5. Project P4 costs \$150K and requires 4 developer-months, delivering value 11. Project P5 costs \$200K and requires 5 developer-months, delivering value 12. Project P6 costs \$90K and requires 2 developer-months, delivering value 7. Project P7 costs \$110K and requires 3 developer-months, delivering value 8. Project P8 costs \$70K and requires 2 developer-months, delivering value 5. Project P9 costs \$180K and requires 4 developer-months, delivering value 13. Project P10 costs \$100K and requires 3 developer-months, delivering value 6. Project P11 costs \$130K and requires 3 developer-months, delivering value 10. Project P12 costs \$85K and requires 2 developer-months, delivering value 6. Project P13 costs \$160K and requires 4 developer-months, delivering value 12. Project P14 costs \$75K and requires 2 developer-months, delivering value 5. Project P15 costs \$220K and requires 5 developer-months, delivering value 14. Project P16 costs \$95K and requires 3 developer-months, delivering value 7. Project P17 costs \$140K and requires 4 developer-months, delivering value 10. Project P18 costs \$65K and requires 2 developer-months, delivering value 5. Project P19 costs \$170K and requires 4 developer-months, delivering value 12. Project P20 costs \$115K and requires 3 developer-months, delivering value 8. The total budget is \$1,000K and the team has 25 developer-months available. Each project is either fully funded or not — no partial investment. Select which projects to fund to maximize total strategic value."

# solver=ON
spl3 run cookbook/78_constraint_opt/resource_allocation.spl \
    --llm claude_cli --param use_solver=true \
    --param problem="$PROBLEM_R4_N20"

# solver=OFF
spl3 run cookbook/78_constraint_opt/resource_allocation.spl \
    --llm claude_cli --param use_solver=false \
    --param problem="$PROBLEM_R4_N20"
```

**Known optimal:** Established by solver=ON run. Not computable by hand — 2^20 ≈ 1M subsets.

**Why LLM fails at n=20:** The LLM cannot enumerate, cannot run branch-and-bound mentally, and greedy heuristics by value/cost or value/dev-month ratio are provably suboptimal for 0-1 knapsack with two constraints. Expected LLM behavior: state a heuristic selection, present it as "optimal," provide no guarantee. The ASSERT gate is precisely the mechanism that would catch this.

**LLM failure mode:** High-value projects (P15 value=14, P9 value=13, P13 and P19 value=12) attract greedy selection, but P15 consumes 5 dev-months and P9+P13 together use 8 dev-months — leaving only 12 dev-months for the remaining 17 projects. The true optimal will involve a non-obvious mix that the LLM cannot derive reliably.

---

## Results Table (to fill in after running)

### H2 Results — Correctness

| Recipe | n | ON correct | OFF correct | OFF answer | True optimal |
|---|---|---|---|---|---|
| `constraint_opt` (LP) | 10 | ✅ (ASSERT) | TBD | TBD | TBD (solver establishes) |
| `constraint_opt` (LP) | 20 | ✅ (ASSERT) | TBD | TBD | TBD |
| `supply_chain` (LP) | 20 routes | ✅ (ASSERT) | TBD | TBD | TBD |
| `supply_chain` (LP) | 40 routes | ✅ (ASSERT) | TBD | TBD | TBD |
| `staff_scheduling` (ILP) | 10 nurses | ✅ (ASSERT) | TBD | TBD | $2,640 |
| `staff_scheduling` (ILP) | 20 nurses | ✅ (ASSERT) | TBD | TBD | $5,030 |
| `resource_allocation` (BILP) | 10 projects | ✅ (ASSERT) | TBD | TBD | 45 |
| `resource_allocation` (BILP) | 20 projects | ✅ (ASSERT) | TBD | TBD | TBD |

### H2 Results — Efficiency (to fill in)

| Recipe | n | ON total tok | OFF total tok | ON latency | OFF latency | OFF output tok |
|---|---|---|---|---|---|---|
| `constraint_opt` (LP) | 10 | TBD | TBD | TBD | TBD | TBD |
| `constraint_opt` (LP) | 20 | TBD | TBD | TBD | TBD | TBD |
| `supply_chain` (LP) | 20 routes | TBD | TBD | TBD | TBD | TBD |
| `supply_chain` (LP) | 40 routes | TBD | TBD | TBD | TBD | TBD |
| `staff_scheduling` (ILP) | 10 nurses | TBD | TBD | TBD | TBD | TBD |
| `staff_scheduling` (ILP) | 20 nurses | TBD | TBD | TBD | TBD | TBD |
| `resource_allocation` (BILP) | 10 projects | TBD | TBD | TBD | TBD | TBD |
| `resource_allocation` (BILP) | 20 projects | TBD | TBD | TBD | TBD | TBD |

---

## Combined Picture: Default (n_0) + H2 (n=10, n=20)

Once H2 is complete, combine with the baseline data from `readme-case-study.md` to build the full scaling table for the TMLR paper:

| Recipe | n_0 OFF correct | n=10 OFF correct | n=20 OFF correct | n_0 OFF tok | n=10 OFF tok | n=20 OFF tok |
|---|---|---|---|---|---|---|
| LP (production) | ✅ | TBD | TBD | 760 | TBD | TBD |
| LP (transport) | ✅ | TBD | TBD | 856 | TBD | TBD |
| ILP (scheduling) | ✅ | TBD | TBD | 566 | TBD | TBD |
| Binary ILP (portfolio) | ✅ | TBD | TBD | 1,158 | TBD | TBD |

**The key TMLR figure:** A 2×4 table showing correctness (✅/❌) and output tokens across (n_0, n=10, n=20) for each recipe. If the hypothesis holds:
- solver=ON: all ✅ across all n (ASSERT guarantees this)
- solver=OFF: ✅ → ❌ transition happens somewhere between n_0 and n=20 for at least the Binary ILP and transport LP

The crossover point (where solver=OFF first fails) is the quantitative claim: solver=ON correctness is n-independent; solver=OFF correctness is n-dependent and degrades predictably with problem complexity class.
