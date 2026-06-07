# Recipe 67 — Symbolic Math Solver

**Pattern:** `CREATE TOOL_API` (deterministic SymPy) sandwiched between two `CREATE FUNCTION` (LLM) steps

## What this demonstrates

The kernel as a **deterministic, symbolic substrate**. A math question flows through
three regimes, each handled by the tool best suited for it:

```
Probabilistic (LLM)    — parse natural language → SymPy expression + operation
Deterministic (SymPy)  — compute the exact symbolic result via the kernel
Probabilistic (LLM)    — explain that exact result in plain English
```

The LLM never approximates the math — it only does the two things language models
are uniquely good at: understanding the question and explaining the answer. SymPy
computes the answer exactly, every time.

## Architecture

```
GENERATE parse_math_problem()  → probabilistic: NL → "<expression>|<operation>"
CALL solve_with_sympy()        → deterministic: exact symbolic computation (no LLM)
GENERATE explain_solution()    → probabilistic: plain-English explanation of the exact result
```

`solve_with_sympy` supports `solve` / `roots`, `diff` / `derivative`, `integrate`,
`simplify`, `expand`, and `factor` — dispatched from the operation string the LLM
extracts from the question.

## Prerequisites

```bash
pip install sympy
```

(or run with `--self-healing` and let the kernel install it on first use)

## Run

```bash
spl3 run cookbook/67_symbolic_math/symbolic_math.spl \
    --adapter ollama --model gemma3

# Custom problem
spl3 run cookbook/67_symbolic_math/symbolic_math.spl \
    --adapter ollama --model gemma3 \
    --param problem="differentiate 3x cubed plus 2x"

# With self-healing (auto-installs sympy if missing)
spl3 run cookbook/67_symbolic_math/symbolic_math.spl \
    --adapter ollama --model gemma3 --self-healing \
    --param problem="integrate sine of x"
```

## Key learning points

1. **Hallucination is structurally impossible on the computation.** The expression
   is parsed by the LLM, but the *answer* comes only from `solve_with_sympy` — exact
   symbolic algebra, not a language model's guess.

2. **`CREATE TOOL_API` imports lazily, at call time.** `solve_with_sympy` imports
   SymPy inside the function body so `--self-healing` can install it on first use
   without failing the whole workflow at parse time.

3. **The LLM is told to trust the symbolic result.** `explain_solution`'s prompt
   explicitly says "Do not re-derive the answer — trust the symbolic result above
   as exact," keeping the LLM in its lane (explanation, not computation).

4. **`EXCEPTION WHEN BudgetExceeded`** falls back to returning the raw SymPy result
   if the explanation step runs out of budget — the user still gets the exact
   answer, just without the narrative wrapper.
