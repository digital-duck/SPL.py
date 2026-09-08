## Summary

This workflow automates prompt engineering by running a mini A/B test on an underperforming baseline prompt. Given a prompt that failed on a specific input, it generates two improved variants using a meta-prompting LLM call, tests each against the failing case, scores the outputs with a quality-check tool, and returns the best-performing prompt. Data science and ML teams benefit by reducing the manual iteration loop when a production prompt regresses on a particular class of inputs.

---

## Detailed Specification

### 1. Purpose

Automatically improve a baseline LLM prompt that failed on a known input by generating, testing, scoring, and selecting the best of two AI-generated prompt variants.

---

### 2. High-level Description

The `prompt_self_tuning` WORKFLOW implements a three-phase meta-programming pattern: variant generation, A/B evaluation, and winner selection. Two CREATE FUNCTIONs define the prompt templates used throughout: `variation_prompt` instructs an LLM to act as a meta-prompting expert and produce exactly one improved prompt variant (parameterized by `variant_num` to ensure distinct outputs), while `test_prompt` composes a given prompt with a test input to produce a candidate response. In the first phase, two independent GENERATE calls invoke `variation_prompt` to produce variants `@v1` and `@v2` in parallel logical steps. In the second phase, each variant is evaluated by a GENERATE call to `test_prompt` followed by a CALL to the `check_quality` tool, which returns a scalar `pass`/`fail` score stored in `@score_v1` and `@score_v2`. In the third phase, nested EVALUATE blocks branch on whether each score contains `'pass'`, preferring `@v1` over `@v2` over the original `@baseline_prompt` as a last resort. The winning prompt is persisted to disk via a CALL to `write_file` and returned with `status='complete'`; an EXCEPTION handler catches `GenerationError` and falls back to the original baseline with `status='baseline_fallback'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| Python class `PromptSelfTuningFlow` | `WORKFLOW prompt_self_tuning` | Declares the named multi-step orchestration |
| `variation_prompt` template class | `CREATE FUNCTION variation_prompt(baseline, failed_case, variant_num)` | Parameterized meta-prompt template with `{variant_num}` slot for distinct outputs |
| `test_prompt` template class | `CREATE FUNCTION test_prompt(prompt_text, test_case)` | Composes a candidate prompt with a test input; passes `{prompt_text}` verbatim as the LLM instruction |
| LLM call to generate variant | `GENERATE variation_prompt(...) INTO @v1` / `@v2` | Two separate calls to produce independent variants |
| LLM call to produce candidate answer | `GENERATE test_prompt(@v1, @failed_case) INTO @result_v1` | One call per variant |
| Quality scoring tool | `CALL check_quality(@result_v1) INTO @score_v1` | Side-effect tool call; returns `'pass'` or `'fail'` string |
| File persistence | `CALL write_file(..., @winning_prompt) INTO NONE` | Side-effect with no return value |
| Winner selection logic | `EVALUATE @score_v1 WHEN contains('pass') THEN ... ELSE EVALUATE @score_v2 ...` | Nested EVALUATE; drives a real three-way branch |
| Success path return | `RETURN @winning_prompt WITH status='complete'` | Non-trivial status token marking successful optimization |
| Error fallback return | `RETURN @baseline_prompt WITH status='baseline_fallback', reason='generation_error'` | Non-trivial status token in EXCEPTION handler |
| Shared mutable state | `@v1`, `@v2`, `@result_v1`, `@result_v2`, `@score_v1`, `@score_v2`, `@winning_prompt` | SPL `@vars` passed across steps |
| Error handling | `EXCEPTION WHEN GenerationError THEN ...` | Named exception handler for LLM generation failures |

---

### 4. Logical Functions / Prompts

**`variation_prompt`**
- **Role:** Meta-prompting generator. Given the baseline and a known failure, it instructs an LLM to act as a prompt engineer and produce one improved prompt variant. Called twice with `variant_num='1'` and `variant_num='2'` to elicit distinct outputs.
- **Key conventions:** Role persona ("You are a meta-prompting expert"), hard constraint on output format ("Output only the improved prompt text — no explanation, no label, no quotes"), `{variant_num}` slot ensures the two calls diverge in their search direction.

**`test_prompt`**
- **Role:** Evaluation harness. Composes any candidate prompt with a test input to produce a response that can be quality-checked. Deliberately minimal — `{prompt_text}` is injected verbatim as the system/task instruction so the variant is tested exactly as written.
- **Key conventions:** No persona, no formatting constraints; the structure `{prompt_text}\n\nInput:\n{test_case}` mirrors a clean zero-shot invocation.

---

### 5. Control Flow

1. **Variant generation:** Two sequential GENERATE calls produce `@v1` and `@v2` from `variation_prompt`.
2. **A/B testing:** For each variant, a GENERATE call runs `test_prompt` to produce a candidate answer (`@result_v1`, `@result_v2`), then a CALL to `check_quality` scores it (`@score_v1`, `@score_v2`).
3. **Winner selection (nested EVALUATE):**
   - If `@score_v1` contains `'pass'` → `@winning_prompt := @v1` (variant 1 wins).
   - Else if `@score_v2` contains `'pass'` → `@winning_prompt := @v2` (variant 2 wins).
   - Else → `@winning_prompt := @baseline_prompt` (no improvement found; baseline retained).
4. **Persistence:** CALL `write_file` saves `@winning_prompt` to `{log_dir}/winning_prompt.md`.
5. **Termination:** RETURN with `status='complete'` on the happy path; if a `GenerationError` is raised at any step, the EXCEPTION handler immediately RETURNs the original `@baseline_prompt` with `status='baseline_fallback'` and `reason='generation_error'`. There is no loop — the workflow is a single linear pass with one branching selection.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Automatically improve a baseline LLM prompt that \
  failed on a known input by generating two improved variants using a \
  meta-prompting LLM call, testing each variant against the failing case with a \
  dedicated test-prompt function, scoring each output with a check_quality tool \
  call, selecting the winner via nested EVALUATE blocks preferring variant 1 over \
  variant 2 over the original baseline, persisting the result with write_file, \
  and returning with status='complete'; catching GenerationError to fall back to \
  the baseline with status='baseline_fallback'." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile prompt_self_tuning.spl --lang python/pocketflow
spl3 splc compile prompt_self_tuning.spl --lang python/langgraph
spl3 splc compile prompt_self_tuning.spl --lang go
```