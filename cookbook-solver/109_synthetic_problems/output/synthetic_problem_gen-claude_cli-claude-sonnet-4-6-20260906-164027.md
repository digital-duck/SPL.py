# SPL Run: synthetic_problem_gen

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 1081 in / 1986 out
- **Latency:** 359931ms
- **Timestamp:** 2026-09-06 16:40:27

## Output

```output
=== Synthetic Problem Generator (r109) ===

Domain      : LP
n_size      : 5 decision variables per problem
Requested   : 5 variants
Generated   : 5 valid variants
Solved      : 5/5 optimally
Repair loops: 0
Saved to    : /home/papagame/projects/digital-duck/SPL.py/cookbook/109_synthetic_problems/output/lp_2026-09-06_16-46-08.json

── Test Suite ──────────────────────────────────────────────
**5/5 variants solved optimally**

| ID | Domain | Status | Optimal | Problem (excerpt) |
|---|---|---|---|---|
| v001 | lp | OPTIMAL | 480.0 | A furniture workshop manufactures five products: Chairs (x1), Desks (x2), Shelve… |
| v002 | lp | OPTIMAL | 450.0 | A bakery produces five baked goods daily: Croissants (x1), Muffins (x2), Scones … |
| v003 | lp | OPTIMAL | 200.0 | A chemical plant synthesizes five compounds: Alpha (x1), Beta (x2), Gamma (x3), … |
| v004 | lp | OPTIMAL | 202.9091 | A garment factory produces five clothing items: Jackets (x1), Vests (x2), Shirts… |
| v005 | lp | OPTIMAL | 450.0 | A pharmaceutical company manufactures five drug formulations: Drug A (x1), Drug … |

── Difficulty Analysis ─────────────────────────────────────
## Benchmark Analysis: n_size=5 LP Suite

**1. Solve rate:** 5/5 (100%) optimal. Zero failures — no infeasible formulations, no unbounded objectives, no solver errors. This is a clean baseline with no diagnostic signal on failure modes.

**2. Difficulty assessment:** n_size=5 is too easy. All five are standard production-mix LPs with non-conflicting constraints and well-separated optima. This predicts solver=OFF correctness will be artificially high at this scale — LLMs can plausibly reason through 5-variable systems by inspection, masking decomposition errors that surface only under constraint pressure. The 100% rate here tells us more about problem construction than LLM capability.

**3. Best stress-test variant:** v004 (garment factory, optimal=202.9091). The fractional optimum signals a non-lattice vertex where multiple constraints bind simultaneously — the LLM must correctly map all binding constraints from NL to reproduce the exact vertex. Round optima (v002=450, v003=200, v005=450) allow lucky near-misses; v004 does not.

**4. Recommendation:** Scale up to n_size=10, then n_size=20. n=5 establishes the floor; the interesting crossover where solver=OFF errors compound likely falls between n=10 and n=20. Optionally, run a tighter-constraint n=5 variant as a control before scaling to isolate size vs. tightness effects.
```
