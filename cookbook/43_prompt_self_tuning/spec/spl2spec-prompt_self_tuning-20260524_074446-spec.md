## Summary

This workflow automates prompt engineering by taking a known-failing prompt and generating two improved variants, then running a mini A/B test to select the best one. It exists to remove manual trial-and-error from prompt iteration cycles. Prompt engineers, LLM application developers, and teams maintaining production prompts benefit from a repeatable, data-driven improvement loop.

---

## Detailed Specification

### 1. Purpose

Given a baseline prompt and a concrete failing input, automatically generate, evaluate, and select an improved prompt variant that handles the failure case better.

---

### 2. High-level Description

The workflow implements a **meta-prompting A/B selection pattern**: it uses the LLM itself to improve its own prompts. The WORKFLOW `prompt_self_tuning` accepts a `@baseline_prompt` and a `@failed_case` as INPUT and produces a `@winning_prompt` as OUTPUT.

Two GENERATE calls invoke `variation_prompt` — a CREATE FUNCTION that instructs a meta-prompting expert persona to produce exactly one improved prompt variant per call, each targeted at the failing case. Two further GENERATE calls invoke `test_prompt` — a CREATE FUNCTION that applies the candidate prompt to the same failing input and returns its output. A CALL to the external tool `check_quality` converts each raw LLM output into a pass/fail quality score.

Selection uses nested EVALUATE blocks: if `@score_v1` contains `'pass'`, variant 1 wins; otherwise, if `@score_v2` contains `'pass'`, variant 2 wins; otherwise the baseline is retained unchanged. The winning prompt is persisted via a CALL to `write_file`. The workflow RETURNS `@winning_prompt` with `status = 'complete'`, or falls back to the baseline with `status = 'baseline_fallback'` inside an EXCEPTION handler for `GenerationError`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW prompt_self_tuning` | `WORKFLOW` | Single named workflow; INPUT/OUTPUT declared |
| `CREATE FUNCTION variation_prompt` | `CREATE FUNCTION` | Meta-prompting template; produces one variant per call |
| `CREATE FUNCTION test_prompt` | `CREATE FUNCTION` | Applies a candidate prompt to a test input; raw LLM call |
| `GENERATE variation_prompt(...) INTO @v1 / @v2` | `GENERATE ... INTO @var` | Two independent LLM calls for variant generation |
| `GENERATE test_prompt(...) INTO @result_v1 / @result_v2` | `GENERATE ... INTO @var` | Two independent LLM calls for variant evaluation |
| `CALL check_quality(@result) INTO @score` | `CALL ... INTO @var` | External tool call; returns `'pass'` or `'fail'` string |
| `CALL write_file(...) INTO NONE` | `CALL ... INTO NONE` | Side-effect only; persists winning prompt to disk |
| `EVALUATE @score_v1 WHEN contains('pass') THEN ... ELSE ... END` | `EVALUATE` | Outer branch: selects v1 or falls through |
| `EVALUATE @score_v2 WHEN contains('pass') THEN ... ELSE ... END` | `EVALUATE` (nested) | Inner branch: selects v2 or retains baseline |
| `@winning_prompt := @v1 / @v2 / @baseline_prompt` | `@var` (shared state) | Mutable workflow variable updated by each branch |
| `RETURN @winning_prompt WITH status = 'complete'` | `RETURN ... WITH status=` | Non-trivial terminal status; signals successful selection |
| `EXCEPTION WHEN GenerationError THEN RETURN ... WITH status = 'baseline_fallback'` | `EXCEPTION WHEN` | Typed recovery; preserves usable output under failure |

---

### 4. Logical Functions / Prompts

**`variation_prompt`**
- **Role:** Meta-prompt generator — uses the LLM as a prompt engineer to produce one focused improvement of the baseline per invocation.
- **Key conventions:** Persona is "meta-prompting expert". Output must be exactly the improved prompt text — no explanation, no label, no quotes (strict output constraint). `{variant_num}` parameterizes the call so two distinct variants are generated without duplication. Called twice with `variant_num = '1'` and `'2'`.

**`test_prompt`**
- **Role:** Prompt-under-test executor — applies a candidate prompt verbatim to the failing input and returns the raw LLM response for quality scoring.
- **Key conventions:** `{prompt_text}` is injected directly as the instruction, making the function a transparent pass-through. `{test_case}` is the fixed failing input used as the evaluation harness. No output format constraint; scoring is delegated to `check_quality`.

---

### 5. Control Flow

1. **Initialization:** Log the failing case; generate `@v1` and `@v2` via two sequential GENERATE calls to `variation_prompt`.
2. **A/B evaluation:** Test `@v1` against the failing case → CALL `check_quality` → `@score_v1`. Repeat for `@v2` → `@score_v2`.
3. **Winner selection (EVALUATE):** Outer EVALUATE checks `@score_v1` for `'pass'`; if matched, `@winning_prompt := @v1`. If not, inner EVALUATE checks `@score_v2`; if matched, `@winning_prompt := @v2`. If neither passes, `@winning_prompt := @baseline_prompt` (silent fallback, logged at WARN).
4. **Persistence:** CALL `write_file` writes the winner to `winning_prompt.md`; result discarded (INTO NONE).
5. **Termination:** RETURN with `status = 'complete'`. If any GENERATE raises `GenerationError`, the EXCEPTION handler returns the original baseline with `status = 'baseline_fallback'` and `reason = 'generation_error'`, ensuring the caller always receives a usable prompt.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Given a baseline prompt and a concrete failing input, automatically generate, evaluate, and select an improved prompt variant that handles the failure case better." --mode workflow

# Step 2 — compile to any target
spl3 splc compile prompt_self_tuning.spl --lang python/pocketflow
spl3 splc compile prompt_self_tuning.spl --lang python/langgraph
spl3 splc compile prompt_self_tuning.spl --lang go
```