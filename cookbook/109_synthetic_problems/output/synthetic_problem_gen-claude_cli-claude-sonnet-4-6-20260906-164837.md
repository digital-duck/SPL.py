# SPL Run: synthetic_problem_gen

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 1084 in / 3714 out
- **Latency:** 497345ms
- **Timestamp:** 2026-09-06 16:48:37

## Output

```output
=== Synthetic Problem Generator (r109) ===

Domain      : LP
n_size      : 20 decision variables per problem
Requested   : 5 variants
Generated   : 5 valid variants
Solved      : 5/5 optimally
Repair loops: 0
Saved to    : /home/papagame/projects/digital-duck/SPL.py/cookbook/109_synthetic_problems/output/lp_2026-09-06_16-56-40.json

── Test Suite ──────────────────────────────────────────────
**5/5 variants solved optimally**

| ID | Domain | Status | Optimal | Problem (excerpt) |
|---|---|---|---|---|
| v001 | lp | OPTIMAL | 13333.3336 | A software company sells 20 product lines (P1–P20). Profit per unit ($): P1=95, … |
| v002 | lp | OPTIMAL | 5000.0 | A regional farm allocates land and irrigation water across 20 crops (C1–C20). Re… |
| v003 | lp | OPTIMAL | 600.0 | A commercial print shop runs 20 job types (J1–J20) daily. Profit per batch ($): … |
| v004 | lp | OPTIMAL | 5600.0 | A furniture manufacturer produces 20 product lines (F1–F20). Profit per unit ($)… |
| v005 | lp | OPTIMAL | 4000.0 | A pharmaceutical plant manufactures 20 drug compounds (D1–D20) per production cy… |

── Difficulty Analysis ─────────────────────────────────────
## n_size=20 LP Benchmark Analysis

**1. Solve rate: 5/5 (100%) optimal.** Zero failures — no infeasible formulations, unbounded objectives, or solver errors. This clean sweep suggests the auto-generated constraint coefficients are well-conditioned at this scale, with feasible regions that are neither degenerate nor pathologically tight.

**2. Difficulty assessment: n_size=20 is too easy.** All five problems are structurally identical — bounded resource allocation with a single binding constraint class. For a competent LP solver this is trivial regardless of n. The real question is solver=OFF (pure LLM) correctness: at n=20, an LLM must track 20 variable coefficients per constraint without arithmetic drift. Expect ~60–75% accuracy from strong models; weaker models likely hallucinate shadow prices or drop variables near the end of the variable list.

**3. Hardest variant for NL→decomposition: v001 (software products).** Mixed profit magnitudes (implicit priority ordering among P1–P20) and likely multiple interacting capacity constraints make constraint-to-variable mapping ambiguous in natural language. Farm (v002) and pharma (v005) have cleaner domain semantics that LLMs pattern-match reliably.

**4. Recommendation: scale up to n_size=50, with tighter constraint tightness (RHS slack ≤ 5%).** n=20 establishes the baseline — the interesting failure cliff for LLM constraint-mapping is typically between n=30 and n=75. Tightening RHS simultaneously probes both variable-count stress and near-degenerate vertex geometry.
```
