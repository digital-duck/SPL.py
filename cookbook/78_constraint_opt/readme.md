# Recipe 78 — Constraint Optimization

**Category:** reasoning · **Tier:** 2 · **Requires:** `pip install pulp`

## What this demonstrates

This recipe showcases the most distinctive feature of SPL: the **deterministic-probabilistic boundary** — the ability to assign each subtask to the computation mode best suited for it, and to enforce that boundary formally with `ASSERT`.

| Stage | Mode | Tool | Why |
|-------|------|------|-----|
| Parse natural-language problem | **Probabilistic** | LLM (`formulate_lp`) | LLMs read prose; solvers don't |
| Generate PuLP code | **Probabilistic** | LLM | Code synthesis from intent |
| Run LP solver | **Deterministic** | PuLP / CBC | Solver produces proof of optimality |
| Gate on Optimal status | **Deterministic** | `ASSERT is_optimal()` | Formal boundary: execution stops here if solver fails |
| Repair failed code | **Probabilistic** | LLM (`repair_lp`) | LLM sees actual error; rewrites code |
| Interpret result | **Probabilistic** | LLM (`interpret_solution`) | Business-language explanation of verified numbers |

**Key property**: The LLM never does arithmetic. Numbers in the output come exclusively from the solver. The ASSERT gate is the formal oracle — it is structurally impossible for a non-Optimal result to reach the interpretation step.

This boundary is **inexpressible in LangChain, PDL, or AutoGen** without external orchestration scaffolding. In SPL it is four tokens: `ASSERT is_optimal(@solution)`.

## Setup

### Install PuLP

PuLP is not part of the SPL core install. Add it once to your environment:

```bash
pip install pulp        # installs PuLP + the bundled CBC solver binary
```

No additional configuration is needed. CBC (COIN-OR Branch and Cut) is bundled with the PuLP wheel and works offline.

### What is PuLP?

PuLP is a Python library for **Linear Programming (LP) and Mixed-Integer Programming (MIP)**. You describe an optimization problem in Python — decision variables, an objective function, linear constraints — and PuLP dispatches it to a solver backend (CBC by default). The solver returns not just a solution but a **proof of optimality**: a certificate that no better solution exists within the feasible region.

PuLP sits at the mature, boring end of the operations research stack:
- Open-source, BSD-licensed, actively maintained (v2.x)
- Default backend is CBC (COIN-OR), one of the best open-source MIP solvers
- Supports optional commercial backends (Gurobi, CPLEX, HiGHS) via the same API
- Widely used in supply chain, scheduling, resource allocation, logistics

### Why PuLP for this recipe?

Three reasons it is the right tool for demonstrating SPL's strengths:

**1. The solver verdict is categorical and machine-readable.**  
PuLP returns `{"status": "Optimal"}`, `{"status": "Infeasible"}`, or `{"status": "Error"}`. There is no ambiguity — unlike SQL results or LLM scoring, you cannot argue about whether the answer is correct. This makes it a clean `ASSERT` target.

**2. LP problems have known closed-form optima for verification.**  
The default bakery problem has a hand-verifiable optimum (bread=3, croissants=3, profit=$60). You can confirm the solver's answer with pencil and paper, which makes the demo self-contained and trustworthy as a tutorial.

**3. PuLP is one entry point into a wide class of deterministic solvers — the .spl workflow scales across domains by swapping the backend.**  
LLMs hallucinate LP solutions. Ask any model to maximize profit subject to three resource constraints and it will confabulate numbers that violate the constraints. A solver cannot hallucinate — it either proves global optimality or reports infeasibility. That contrast is the point of this recipe.

But PuLP is only the demo rung. The `GENERATE → CALL solver → ASSERT → WHILE repair` pattern in this workflow extends directly to other solver backends without touching the .spl logic:

| Domain | Replace `run_pulp()` with | What ASSERT checks |
|--------|--------------------------|-------------------|
| Structural engineering | FEniCS / OpenSees FEM solver | stress < yield strength, deflection < limit |
| Semiconductor process | TCAD simulator (Sentaurus, Silvaco) | threshold voltage, leakage within spec |
| Wafer metrology | on-tool measurement API | CD / overlay / film thickness within tolerance |
| Chemical process | Aspen HYSYS / DWSIM flowsheet solver | energy balance, purity ≥ target |
| Circuit design | SPICE / ngspice | gain, bandwidth, phase margin within bounds |
| Supply chain scheduling | OR-Tools CP-SAT solver | all jobs scheduled, no resource overrun |

In every case the .spl workflow is identical in structure. The LLM's job is always the same — read the natural-language specification and write the solver input. The solver's job is always the same — run the physics or mathematics and return a machine-readable verdict. `ASSERT` is always the formal boundary between them. Only the `TOOL_API` body changes, because only the solver changes. This is **DODA** (Design Once, Deploy Anywhere) applied to the deterministic layer: one workflow specification, many physical backends.

## Run

```bash
# Default problem (bakery production planning)
spl3 run cookbook/78_constraint_opt/constraint_opt.spl --llm claude_cli

# Custom problem
spl3 run cookbook/78_constraint_opt/constraint_opt.spl \
    --llm ollama:gemma3 \
    --param problem="A factory makes chairs (2h labor, 4kg wood, \$20 profit) and tables (4h labor, 3kg wood, \$30 profit). Available: 20h labor, 24kg wood. Maximize profit."

# More repair attempts (default 3)
spl3 run cookbook/78_constraint_opt/constraint_opt.spl \
    --llm claude_cli \
    --param max_tries=5
```

## Default problem

> A bakery produces artisan bread and croissants. Each loaf of bread requires 3 hours of labor and 2 kg of flour, earning $12 profit. Each batch of croissants requires 1 hour of labor and 3 kg of flour, earning $8 profit. The bakery has 12 hours of labor and 15 kg of flour available each day. Maximize daily profit.

**Known optimal** (verifiable by hand): bread = 3, croissants = 3, profit = $60.  
Labor: 3×3 + 3×1 = 12 ✓ · Flour: 3×2 + 3×3 = 15 ✓ · Both constraints binding.

## Execution flow

```
GENERATE formulate_lp(@problem)     -- LLM writes PuLP code
    │
CALL run_pulp(@lp_code)             -- CBC solver executes
    │
CALL get_status(@solution)          -- extract status string
    │
WHILE @tries < @max_tries
    ├── status = "Optimal" → exit loop
    ├── status = "init"    → first attempt (above)
    └── status = Error/Infeasible
            │
        CALL get_error()            -- get error message
        GENERATE repair_lp()        -- LLM rewrites with error
        CALL run_pulp()             -- retry
            │
ASSERT is_optimal(@solution)        -- hard gate: AssertionError if not Optimal
    │
GENERATE interpret_solution()       -- LLM explains verified result
    │
CALL format_report()                -- Markdown report
```

## Output format

```markdown
# Constraint Optimization Report

**Problem:** ...
**Solver status:** `Optimal`
**Optimal objective value:** 60

**Decision variables:**
  - Bread = 3
  - Croissants = 3

## Interpretation
The bakery should produce 3 loaves of bread and 3 batches of croissants ...

## Solver Code (LLM-generated, PuLP)
```python
...
```
```

## Exception handling

If the solver cannot reach Optimal status within `max_tries`, `ASSERT is_optimal` raises `AssertionError`, caught by `EXCEPTION WHEN AssertionError THEN`. The workflow exits with `status = "infeasible"` and a diagnostic message. This means the report variable always carries either a verified solution or an explicit failure — never a hallucinated number.

## Connection to TMLR paper

This recipe is the reference implementation for **Appendix — Domain #1: Constraint Optimization** in the SPL TMLR submission. It demonstrates that `ASSERT` is a **ground-truth oracle**, not just execution-success tracking:

- Execution success (code ran without Python exception) ≠ Optimal solution
- `ASSERT is_optimal()` distinguishes these: `{"status": "Infeasible"}` is a successful execution that returns a wrong answer
- This is the rebuttal to ZXT2's claim that ASSERT only tracks "code ran"

The same `GENERATE → SOLVE → ASSERT → WHILE` pattern replicates directly to:
- **Recipe 75** (SymPy): symbolic algebra verifier rung
- **Recipe 76** (Lean): formal proof verifier rung
- **Recipe 78** (PuLP): combinatorial optimization verifier rung
