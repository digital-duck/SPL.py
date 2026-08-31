# Recipe 107 — Workforce 3-Objective Scheduling (cost, quality, risk)

**First 3D Pareto surface benchmark in the suite.** Optimizes shift staffing
across three competing objectives simultaneously using pymoo NSGA-II.

---

## What it demonstrates

| Mode | Solver | What happens |
|------|--------|--------------|
| `use_solver=true` | NSGA-II (pymoo) | LLM extracts structure → NSGA-II produces 3D Pareto front → LLM interprets tradeoffs |
| `use_solver=false` | LLM only | LLM proposes (xD, xE, xN) integers → back-substitution verifier checks arithmetic |

Unlike single-objective recipes (r78), this recipe returns a **surface** of non-dominated
solutions rather than one optimal point. The ASSERT gate ensures at least 3 Pareto points
before interpretation proceeds.

---

## Problem (Benchmark B4)

3 shift types, minimum 10 staff per shift, cap 20, total >= 30:

| Shift | Cost/employee | Quality | Fatigue risk | Range |
|-------|---------------|---------|--------------|-------|
| Day (D)     | $100 | 0.90 | 0.10 | [10, 20] |
| Evening (E) | $130 | 1.00 | 0.25 | [10, 20] |
| Night (N)   | $160 | 0.70 | 0.40 | [10, 20] |

**Three objectives (all simultaneously):**

1. Minimize total cost: `100·xD + 130·xE + 160·xN`
2. Maximize blended quality: `(0.90·xD + 1.00·xE + 0.70·xN) / (xD+xE+xN)`
3. Minimize blended risk: `(0.10·xD + 0.25·xE + 0.40·xN) / (xD+xE+xN)`

---

## Utopia anchors (per-objective best)

| Anchor | xD | xE | xN | Cost ($) | Quality | Risk |
|--------|----|----|-----|----------|---------|------|
| Min-cost   | 20 | 10 | 10 | 5,000 | 0.900 | 0.150 |
| Max-quality| 10 | 20 | 10 | 5,100 | 0.953 | 0.195 |
| Min-risk   | 20 | 10 | 10 | 5,000 | 0.900 | 0.150 |

Note: cost and risk are aligned (both prefer Day shifts); quality pulls toward Evening.
The tradeoff is between the Day-dominated front and Evening-heavy schedules.

---

## Run commands

```bash
# solver=ON — NSGA-II produces 3D Pareto surface
spl3 run cookbook/107_workforce_3obj/workforce_3obj.spl \
    --adapter claude_cli --param use_solver=true

# solver=OFF — LLM proposes a single schedule, verifier checks it
spl3 run cookbook/107_workforce_3obj/workforce_3obj.spl \
    --adapter claude_cli --param use_solver=false

# Custom NSGA-II settings
spl3 run cookbook/107_workforce_3obj/workforce_3obj.spl \
    --adapter ollama -m gemma3 \
    --param use_solver=true --param n_gen=100 --param pop_size=200

# Custom problem
spl3 run cookbook/107_workforce_3obj/workforce_3obj.spl \
    --adapter momagrid --param use_solver=true \
    --param "problem=A hospital runs Day ($120/nurse, quality 0.95, risk 0.08, min 15 max 25), Evening ($150, quality 1.00, risk 0.20, min 10 max 20), Night ($180, quality 0.75, risk 0.45, min 10 max 20). Total minimum: 40 nurses."
```

---

## Install

```bash
pip install pymoo pulp
```

---

## Optimization formulation

**Variables:** xD, xE, xN ∈ ℤ

**Objectives:**
- f1 = 100·xD + 130·xE + 160·xN  (minimize)
- f2 = -(0.90·xD + 1.00·xE + 0.70·xN) / (xD+xE+xN)  (minimize negated quality)
- f3 = (0.10·xD + 0.25·xE + 0.40·xN) / (xD+xE+xN)  (minimize)

**Constraints:** xD+xE+xN >= 30, xD ∈ [10,20], xE ∈ [10,20], xN ∈ [10,20]

**Solver:** NSGA-II with IntegerRandomSampling, SBX crossover, PM mutation, 50 generations, population 100.

---

## TOOL_API reference

| Function | Description |
|----------|-------------|
| `solve_workforce_pareto(problem_json, n_gen, pop_size)` | Run NSGA-II; returns Pareto front JSON |
| `is_pareto_feasible(front_json)` | ASSERT gate: status==OK and n_points >= 3 |
| `format_pareto_surface(front_json)` | Markdown table sorted by cost; min/max footer |
| `compute_utopia_anchors(problem_json)` | Per-objective PuLP anchors for reference |
| `verify_workforce_off(problem_json, solution_json)` | Back-substitution check for solver=OFF |
| `json_get_field(data_json, field)` | Extract field from JSON as string |

---

## Related recipes

- **r78** — constraint optimization (single-objective, PuLP), solver=ON/OFF ablation
- **r99** — portfolio optimization (Markowitz, cvxpy)
- **r100** — supply sourcing (2-objective Pareto, cost vs. fill rate)
- **r101** — production sustainability (multi-objective)
