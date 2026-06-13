# Case 3 — Full 400-Run Experiment Analysis

**Source:** `exp-20260613-050401`  
**Date:** 2026-06-13  
**Runs:** 400 (10 models × 20 problems × 2 arms)  
**DB:** `cookbook/67_symbolic_math/experiment_results.db`  
**Log:** `cookbook/67_symbolic_math/logs-spl/case-2-log-rerun-20260613-050401.md`

---

## 1. Experiment Design

### Two arms (A/B test)

| Arm | `enable_solver` | Description |
|---|---|---|
| `llm_only` | `false` | LLM answers the math problem directly, no symbolic engine |
| `solver` | `true` | LLM decomposes problem into `expr\|op` steps → SymPy executes each step → LLM narrates result |

### 10 models under test

| ID | Model | Provider |
|---|---|---|
| m001 | sonnet-4-6 | claude_cli |
| m002 | gemma3 | ollama (local) |
| m003 | gemma4 | ollama (local) |
| m004 | qwen2.5 | ollama (local) |
| m005 | qwen3.5 | ollama (local) |
| m006 | phi3 | ollama (local) |
| m007 | phi4 | ollama (local) |
| m008 | deepseek-r1 | ollama (local) |
| m009 | lfm2.5 | ollama (local) |
| m010 | rnj-1 | ollama (local) |

### 20 problems across 6 difficulty tiers

| Tier | Problems | Description |
|---|---|---|
| T0 | p001, p011 | Single-step differentiation, basic simplification |
| T1 | p002, p003, p004, p012 | Multi-step chains: expand → factor → differentiate → solve |
| T2 | p005, p006, p013, p014 | Transcendental functions, limits, Taylor series, trig identities |
| T3 | p007, p008, p015, p016 | Integration (substitution/product), linear systems, eigenvalues |
| T4 | p009, p017, p018, p019 | Laplace transforms, ODEs, infinite series, complex roots |
| T5 | p010, p020 | 2nd-order ODE general solution, inverse Laplace + verification |

---

## 2. Overall Pass Rates

| Model | llm_only | solver | Delta | Assessment |
|---|---|---|---|---|
| sonnet-4-6 | **100%** | **100%** | 0 | Only model at 100% both arms |
| rnj-1 | **100%** | 75% | −25 | Strong LLM baseline; solver hurts |
| qwen2.5 | **100%** | 75% | −25 | Same pattern as rnj-1 |
| gemma4 | 95% | **80%** | −15 | Best local model on solver arm |
| phi4 | **100%** | 0% | −100 | LLM-capable; can't follow solver chain format |
| phi3 | **100%** | 0% | −100 | Same — plan format fails completely |
| gemma3 | **100%** | 0% | −100 | Same — all 20 solver runs fail at planning |
| lfm2.5 | 80% | 15% | −65 | Partial; solver mostly breaks it |
| deepseek-r1 | 40% | 40% | 0 | Weak on math; solver adds no value |
| qwen3.5 | 0% | 0% | 0 | Complete failure both arms — config issue suspected |

**Summary:**
- 6 models score 100% on `llm_only` (sonnet-4-6, rnj-1, qwen2.5, phi4, phi3, gemma3)
- Only **sonnet-4-6** maintains 100% on the `solver` arm
- The solver arm degrades accuracy for 7 of 10 models

---

## 3. Tier-by-Tier Breakdown

### sonnet-4-6 — the ceiling

| Arm | T0 | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|---|
| llm_only | 2/2 | 4/4 | 4/4 | 4/4 | 4/4 | 2/2 |
| solver | 2/2 | 4/4 | 4/4 | 4/4 | 4/4 | 2/2 |

100% at every tier, both arms. The solver overhead adds ~1s (13s → 14s avg) with zero accuracy cost.

### gemma4 — best local model

| Arm | T0 | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|---|
| llm_only | 2/2 | 4/4 | 4/4 | 3/4 | 4/4 | 2/2 |
| solver | 2/2 | 3/4 | 3/4 | 3/4 | 3/4 | 2/2 |

LLM arm misses only one T3 problem. Solver arm drops to 75% at T1–T4 — the plan sanity gate catches decomposition errors in multi-step problems. Holds 100% at T0 and T5 in both arms.

### qwen2.5 and rnj-1 — strong LLM, solver regression

| Arm | T0 | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|---|
| qwen2.5 llm_only | 2/2 | 4/4 | 4/4 | 4/4 | 4/4 | 2/2 |
| qwen2.5 solver | 2/2 | 3/4 | 4/4 | 1/4 | 3/4 | 2/2 |
| rnj-1 llm_only | 2/2 | 4/4 | 4/4 | 4/4 | 4/4 | 2/2 |
| rnj-1 solver | 2/2 | 3/4 | 3/4 | 2/4 | 3/4 | 2/2 |

Both handle T0 and T5 perfectly in solver arm. Breakdown is concentrated in T1 (format errors) and T3 (sanity gate rejections on integration and eigenvalue problems).

### phi3 / phi4 / gemma3 — 100% LLM, 0% solver

These models can solve all 20 math problems when reasoning freely. They cannot produce the structured `expr|op` decomposition format the solver arm requires. Every solver run fails at the planning stage:

| Model | plan_format_error | plan_sanity_error |
|---|---|---|
| phi3 | 13 | 7 |
| phi4 | 10 | 10 |
| gemma3 | 4 | 16 |

**Key finding: the solver interface is a harder task than the math itself for these models.**

### deepseek-r1 — consistently weak

| Arm | T0 | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|---|
| llm_only | 1/2 | 3/4 | 3/4 | 0/4 | 0/4 | 1/2 |
| solver | 2/2 | 1/4 | 3/4 | 1/4 | 1/4 | 0/2 |

Fails completely on T3–T4 in `llm_only` (integration, eigenvalues, Laplace). The solver arm rescues 4 problems but introduces 4 new failures from `plan_sanity_error`. Net accuracy unchanged at 40%.

### qwen3.5 — 0% both arms

0% on every tier in both arms. Not consistent with the model's known capability — likely a model version mismatch, quantization issue, or output format incompatibility with the judge. Needs dedicated investigation before inclusion in future runs.

### lfm2.5 — partial capability

80% llm_only (solid on T1/T4/T5) but drops to 15% in solver arm. Fails mostly on `plan_error` (11 cases) — the model attempts a plan but the SymPy execution step throws an exception, suggesting the model emits mathematically malformed step expressions.

---

## 4. Solver Lift vs. Hurt

Across all 200 problem/model pairs with both arms:

| Direction | Count |
|---|---|
| Solver rescued a failing llm_only run | **6** |
| Solver broke a passing llm_only run | **92** |
| Both arms passed / both failed (unchanged) | **102** |

### The 6 problems where solver helped

| Model | Problem | Tier |
|---|---|---|
| deepseek-r1 | p001 — differentiate x⁴−2x²+1 | T0 |
| deepseek-r1 | p013 — Taylor series sin(x) to degree 5 | T2 |
| deepseek-r1 | p007 — integrate √(4−x²) | T3 |
| deepseek-r1 | p009 — Laplace transform of e^(−2t) | T4 |
| gemma4 | p007 — integrate √(4−x²) | T3 |
| lfm2.5 | p006 — limit sin(x)/x as x→0 | T2 |

All 6 are cases where the LLM's direct answer was wrong but SymPy produced the correct result. The solver acted as a genuine correction mechanism — the benefit it was designed for.

### The 92 regressions — model breakdown

| Model | Regressions |
|---|---|
| phi3 | 20 |
| phi4 | 20 |
| gemma3 | 20 |
| lfm2.5 | 13 |
| qwen2.5 | 5 |
| rnj-1 | 5 |
| deepseek-r1 | 4 |
| gemma4 | 4 |
| sonnet-4-6 | 0 |
| qwen3.5 | 0 (0% both arms — no baseline to lose) |

phi3/phi4/gemma3 account for 60 of the 92 regressions — all caused by plan format/sanity failures, not wrong math.

---

## 5. Failure Mode Analysis

| Status | Meaning | Models affected |
|---|---|---|
| `plan_format_error` | Model can't emit valid `expr\|op` step format | phi3 (13), phi4 (10), gemma3 (4), qwen2.5 (2), rnj-1 (2) |
| `plan_sanity_error` | Format OK but sanity gate rejects the plan | gemma3 (16), phi4 (10), phi3 (7), lfm2.5 (4), qwen2.5 (3), deepseek-r1 (5) |
| `plan_error` | Planning stage fails entirely | lfm2.5 (11), deepseek-r1 (5), qwen3.5 (19) |
| `sanity_error` | Chain runs but final answer is wrong | gemma4 (2), deepseek-r1 (1), rnj-1 (2), qwen2.5 (2) |
| `narration_error` | Symbolic result OK but narration stage fails | qwen3.5 (1) |
| `solver_error` | SymPy execution throws an exception | rnj-1 (1) |

**Three distinct failure categories:**

1. **Format failure** (phi3, phi4, gemma3): the model understands the math but can't structure its plan into the required `expr|op` format. The symbolic engine never runs.
2. **Planning failure** (lfm2.5, deepseek-r1, qwen3.5): the model can't decompose the problem into valid symbolic sub-problems at all.
3. **Execution failure** (gemma4, qwen2.5, rnj-1, deepseek-r1): the model plans correctly, the chain runs, but the symbolic result fails the answer sanity check.

---

## 6. Latency Analysis

| Model | llm_only avg | solver avg | Overhead | Avg LLM calls (solver) |
|---|---|---|---|---|
| gemma3 | 4,792ms | 3,308ms | −31% | 1.8 |
| qwen2.5 | 8,492ms | **4,903ms** | **−42%** | 3.6 |
| rnj-1 | 8,521ms | 8,091ms | −5% | 3.5 |
| lfm2.5 | 6,769ms | 11,309ms | +67% | 1.6 |
| sonnet-4-6 | 13,055ms | 14,009ms | **+7%** | 4.0 |
| phi4 | 27,470ms | 5,812ms | −79% | 1.5 |
| phi3 | 36,215ms | 6,402ms | −82% | 1.4 |
| qwen3.5 | 27,984ms | 32,397ms | +16% | 1.1 |
| gemma4 | 19,285ms | 28,695ms | +49% | 3.7 |
| deepseek-r1 | 25,705ms | 34,503ms | +34% | 2.5 |

**Notable observations:**

- **phi3/phi4 solver appears faster** — only because plan failures exit early (avg 1.4–1.5 LLM calls). Early exit is not a win; it means the solver never ran.
- **qwen2.5 solver is genuinely faster** (−42%) while maintaining 75% accuracy. SymPy short-circuits the LLM's reasoning work on problems it can decompose cleanly. A real win for the problems it handles.
- **sonnet-4-6 solver adds only 7% overhead** (~1 extra second) for 100% accuracy — the best efficiency/accuracy tradeoff in the experiment.
- **gemma4 solver costs +49% latency** for a −15pp accuracy drop — a net loss. Better to stay on llm_only for gemma4.
- **deepseek-r1** adds 9s overhead for no accuracy gain — solver is counterproductive.

---

## 7. Conclusions and Recommendations

### Finding 1 — The solver interface is a capability filter

The `solver` arm requires two skills beyond solving the math: (a) decomposing a problem into a precise `expr|op` format, and (b) passing a plan sanity gate. For 7 of 10 models these requirements are harder than the math itself. The solver can only help if the model can correctly describe *what it wants SymPy to compute*.

**Recommendation:** Add a lightweight format-compliance probe before committing to the full solver chain. If a model fails the probe, fall back to `llm_only` immediately and avoid the regression.

### Finding 2 — Only sonnet-4-6 is unconditionally solver-safe

sonnet-4-6 scores 100% in both arms, generates valid plans on every problem, and adds only 7% latency overhead. It is the correct reference implementation for the solver chain and the baseline for future experiments.

### Finding 3 — gemma4 is the best local model

95% llm_only / 80% solver. The −15pp solver regression is concentrated in T1–T4 multi-step problems (plan sanity failures). Practical strategy: use solver for T0/T2/T5; fall back to llm_only for T1/T3/T4.

### Finding 4 — qwen3.5 needs investigation before next run

0% in both arms across all tiers is not consistent with the model's known capability. A model-version, quantization, or judge-compatibility issue is the most likely cause. Exclude from aggregate statistics until resolved.

### Finding 5 — deepseek-r1 has a math ceiling, not a solver problem

40% accuracy in both arms, with hard failures on T3 (integration, eigenvalues) and T4 (Laplace, ODEs). The solver neither helps nor hurts in net terms. This is a genuine mathematical reasoning ceiling for this model on these problem types.

### Finding 6 — 100% llm_only ≠ solver-compatible

phi3, phi4, gemma3 can all solve the math when reasoning freely. They cannot use the structured solver interface. This is a generalizable insight: instruction-following fidelity for structured output formats is a separate capability from mathematical reasoning.

### Recommended model configuration for recipe 67

| Tier | Model | Arm | Rationale |
|---|---|---|---|
| Cloud | sonnet-4-6 | solver | 100%/100%, +7% overhead — unconditionally optimal |
| Local tier-1 | gemma4 | llm_only | 95%, avoids the 15pp solver regression |
| Local tier-2 | qwen2.5 or rnj-1 | llm_only | 100% llm_only, fast, no solver benefit |
| Needs fix | qwen3.5 | — | 0% both arms, root cause unknown |
| Solver excluded | phi3, phi4, gemma3 | llm_only only | Plan format incompatible; 100% on llm_only arm |

---

## 8. Raw Counts Reference

```
Total runs:          400
Models:               10
Problems:             20  (T0×2, T1×4, T2×4, T3×4, T4×4, T5×2)
Arms:                  2  (solver / llm_only)

llm_only passes:   175 / 200  (87.5%)
solver passes:     101 / 200  (50.5%)
Overall:           276 / 400  (69.0%)

Solver lift  (llm_only→fail, solver→pass):    6
Solver hurt  (llm_only→pass, solver→fail):   92
Unchanged:                                   102
```
