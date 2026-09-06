# SPL Run: synthetic_problem_gen

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 1083 in / 2685 out
- **Latency:** 197859ms
- **Timestamp:** 2026-09-06 16:41:26

## Output

```output
=== Synthetic Problem Generator (r109) ===

Domain      : LP
n_size      : 10 decision variables per problem
Requested   : 5 variants
Generated   : 5 valid variants
Solved      : 5/5 optimally
Repair loops: 0
Saved to    : /home/papagame/projects/digital-duck/SPL.py/cookbook/109_synthetic_problems/output/lp_2026-09-06_16-44-23.json

── Test Suite ──────────────────────────────────────────────
**5/5 variants solved optimally**

| ID | Domain | Status | Optimal | Problem (excerpt) |
|---|---|---|---|---|
| v001 | lp | OPTIMAL | 2000.0 | A garment factory produces 10 clothing products: shirts (x1), trousers (x2), jac… |
| v002 | lp | OPTIMAL | 90.0 | A bakery produces 10 items, each measured in dozens: bread (x1), croissants (x2)… |
| v003 | lp | OPTIMAL | 165.0 | A chemical plant produces 10 specialty compounds (P1–P10). Profit per unit ($): … |
| v004 | lp | OPTIMAL | 535.0 | An electronics manufacturer assembles 10 product lines: wireless speakers (x1), … |
| v005 | lp | OPTIMAL | 1083.3334 | A farm allocates resources across 10 crops (each variable measured in 100-lb uni… |

── Difficulty Analysis ─────────────────────────────────────
## Benchmark Analysis: n_size=10 LP Suite

**1. Solve rate.** 5/5 optimal (100%). Zero failures — no infeasible formulations, no unbounded objectives, no solver errors. The clean sweep indicates well-posed problems with binding constraints at a tractable scale.

**2. Difficulty calibration.** n_size=10 is easy for the *solver* but not trivially easy for NL→LP decomposition: 10 variables still requires correctly mapping prose units, resource pools, and per-product coefficients. With solver=OFF, an LLM must enumerate all 10 variable bounds and constraint coefficients from natural language — error rate typically rises sharply here even though the math is simple. Expect 60–80% correctness without a solver at this scale.

**3. Best stress-test variant.** **v005** (farm, 100-lb units, optimal = 1083.3̄). The non-integer optimum signals multiple tight constraints intersecting at a fractional vertex, the scaled measurement unit requires decomposition before formulation, and crop resource allocation involves semantically ambiguous shared-resource language. It is the only variant where unit misreading directly breaks feasibility.

**4. Next step.** Scale up to **n_size=20** while also introducing one near-degenerate variant (redundant constraint or near-zero slack) at n=10. The 20-variable batch will reveal whether coefficient-mapping errors accumulate linearly or faster.
```
