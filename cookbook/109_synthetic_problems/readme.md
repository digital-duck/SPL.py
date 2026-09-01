# Recipe 109 — Synthetic Problem Generator

**Purpose:** Turn one verified (problem, optimal) pair into a labeled test suite of N variants — expanding the benchmark space for any solver recipe without writing problems by hand.

## Why this matters

LLM problem decomposition (NL → solver formulation) is the ceiling on solver=ON correctness (findings F11, F12 from r78 ablation). To measure that ceiling systematically you need labeled (problem_text, known_optimal) pairs across a range of difficulties. Writing them by hand is slow; this recipe generates them automatically and verifies each one with the same solver.

The output — a JSON test suite with verified optima — is directly usable as:
- **Benchmark input** for solver=ON vs solver=OFF ablation sweeps across models
- **Training data** for a problem-decomposition fine-tune or router
- **Regression suite** for a given .spl script (same workflow, N problems instead of 1)

## Architecture

```
LLM generates N variants        ← structured JSON (problem_text + formal spec)
    ↓
WHILE repair loop               ← fixes malformed JSON (≤ 3 attempts)
    ↓
ASSERT has_valid_variants       ← at least 1 valid before proceeding
    ↓
batch_solve (TOOL_API)          ← routes to domain solver, returns verified optima
    ↓
format_test_suite               ← markdown table: ID / domain / status / optimal
    ↓
save_test_suite                 ← output/{domain}_{timestamp}.json
    ↓
LLM analyzes difficulty spread  ← which variant stresses decomposition most?
```

## What the LLM generates

Each variant is a structured JSON object with **both** the natural-language description and the formal solver spec in one shot:

```json
{
  "id": "v003",
  "domain": "LP",
  "problem_text": "A bakery produces muffins ($4 profit, 1 labor-hour, 2 kg flour) ...",
  "variables": [{"name": "muffins", "type": "continuous", "lb": 0}, ...],
  "objective": {"sense": "maximize", "coefficients": {"muffins": 4, ...}},
  "constraints": [{"name": "labor", "lhs": {"muffins": 1}, "op": "<=", "rhs": 40}, ...]
}
```

This means `batch_solve` can construct the PuLP model directly from the JSON — no secondary NL parsing, no extra LLM call.

## Supported domains

| Domain | Solver | Verification |
|---|---|---|
| `LP` | PuLP + CBC (continuous vars) | `status == Optimal` (C1) |
| `ILP` | PuLP + CBC (integer vars) | `status == Optimal` (C1) |
| `supply-sourcing` | PuLP + CBC (B1 pattern) | `status == Optimal` (C1) |

Additional domains (production, workforce, job-shop) can be added by extending `batch_solve` in `tools.py`.

## Run commands

```bash
# n05: small LP problems (5 products) — mirrors r78 n05 baseline
spl3 run cookbook/109_synthetic_problems/synthetic_problem_gen.spl \
    --adapter ollama -m gemma3 \
    --param domain=LP --param n_variants=5 --param n_size=5

# n10: medium scale — where gemma3 formulation starts to degrade (per r78 H2)
spl3 run cookbook/109_synthetic_problems/synthetic_problem_gen.spl \
    --adapter claude_cli \
    --param domain=LP --param n_variants=5 --param n_size=10

# n20: large scale — crossover point where solver=OFF collapses
spl3 run cookbook/109_synthetic_problems/synthetic_problem_gen.spl \
    --adapter claude_cli \
    --param domain=LP --param n_variants=5 --param n_size=20

# Supply-sourcing n10 (10 suppliers, B1 pattern)
spl3 run cookbook/109_synthetic_problems/synthetic_problem_gen.spl \
    --adapter claude_cli \
    --param domain=supply-sourcing --param n_variants=5 --param n_size=10

# Custom reference problem + ILP at n08
spl3 run cookbook/109_synthetic_problems/synthetic_problem_gen.spl \
    --adapter claude_cli \
    --param domain=ILP --param n_variants=5 --param n_size=8 \
    --param "sample_problem=A knapsack has capacity 15 kg. Items: A (value=10, weight=5), B (value=6, weight=3), C (value=12, weight=7). Maximize total value. Variables are binary (0/1). Known optimal: select A and C, value=22."
```

## Output

Results saved to `output/{domain}_{timestamp}.json`:

```json
{
  "status": "OK",
  "n_total": 5,
  "n_optimal": 4,
  "n_failed": 1,
  "results": [
    {
      "id": "v001",
      "domain": "lp",
      "problem_text": "A bakery produces muffins...",
      "solver_status": "OPTIMAL",
      "optimal": 160.0,
      "variables": {"muffins": 20.0, "cakes": 10.0}
    },
    ...
  ]
}
```

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `sample_problem` | B3 production problem | Reference problem with known optimal |
| `domain` | `LP` | `LP`, `ILP`, or `supply-sourcing` |
| `n_variants` | `5` | Number of variants to generate per batch |
| `n_size` | `5` | Decision variables per problem — mirrors r78 scale levels (n05/n10/n20) |

### `n_size` semantics by domain

| Domain | n_size means | n05 | n10 | n20 |
|---|---|---|---|---|
| LP / ILP | number of products / items | 5 products | 10 products | 20 products |
| supply-sourcing | number of suppliers | 5 suppliers | 10 suppliers | 20 suppliers |

Larger `n_size` stresses the LLM's constraint-mapping ability. Per r78 H2: gemma3 solver=ON degrades at n10/n20; solver=OFF collapses to 0/4 at n10. Use `n_size` to find the crossover point for any model.
| `scale` | `similar` | `similar` (same size) / `larger` (add variables) / `varied` (mix) |

## Related recipes

- r78: constraint optimization — the primary target for LP test suites
- r100: supply sourcing — target for supply-sourcing test suites
- r101: production sustainability — target for LP + multi-objective suites
- r68: answer-first problem generator — SymPy-domain counterpart
