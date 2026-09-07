# SPL Run: hard_milp_scip

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 429 in / 415 out
- **Latency:** 17579ms
- **Timestamp:** 2026-09-07 12:50:53

## Output

```output
=== Hard MILP Unit Commitment (r123) | solver=ON ===

## Unit Commitment Report — SCIP

**Total operating cost:** $150,550  
**Optimality gap:** 0.0%  
**Solve time:** 1.2s  
**Status:** optimal  

### Generator Schedule (hours committed / 24)

| Generator | Hours ON | Min MW | Max MW | Var Cost $/MWh |
|---|---|---|---|---|
| G1_coal | 24 | 50 | 200 | 28.0 |
| G2_gas_cc | 12 | 30 | 150 | 45.0 |
| G3_gas_ct | 0 | 10 | 80 | 72.0 |
| G4_nuclear | 24 | 80 | 120 | 12.0 |
| G5_peaker | 0 | 5 | 50 | 95.0 |

### Peak Hour Snapshot (hour 18 — evening peak, 360 MW demand)

| Generator | Output (MW) |
|---|---|
| G1_coal | 200.0 |
| G2_gas_cc | 50.0 |
| G3_gas_ct | 0.0 |
| G4_nuclear | 120.0 |
| G5_peaker | 0.0 |

── Analyst Explanation ─────────────────────────────────────
## Unit Commitment: SCIP Deep Dive

**1. Cutting Planes**
A cutting plane is a linear inequality added to the LP relaxation that eliminates fractional solutions without removing any integer-feasible points. SCIP detects that the LP relaxes `on[g,t] ∈ {0,1}` to `[0,1]`, producing physically impossible fractional commitment states (e.g., G4_nuclear "40% on"). Gomory cuts and knapsack covers tighten the feasible region so the LP bound rises closer to the true integer optimum — reducing the branch-and-bound tree SCIP must explore.

**2. Why HiGHS Gaps Linger**
Unit commitment has three compounding hardness sources: *temporal coupling* (min up/down constraints link 24 periods into one tight block), *startup cost discontinuities* (fixed charges create non-convex jumps), and *symmetry* (multiple generators with similar costs produce many equivalent but non-obvious integer solutions). HiGHS's MIP engine applies fewer cutting-plane families, so its LP bound stays looser — the branch tree is larger and it hits time limits with gap remaining.

**3. Economic Cost of a 5% Gap**
On a $2B annual fuel bill, 5% = **$100M/year in preventable fuel spend** — enough to finance 2–3 peaker plants. Real ISOs run UC every 15 minutes; a persistent gap compounds across 35,000+ dispatches annually.

**4. ISO-Scale Limits**
1000 generators × 8760 hours = ~8.7M binaries. SCIP handles this via decomposition (Lagrangian relaxation by generator, Benders by time block) and parallel branch-and-bound. In practice, ISOs use rolling 24-hour windows with warm-starts from the prior solution — SCIP typically closes to <1% gap in under 60 seconds per window on modern hardware.
```
