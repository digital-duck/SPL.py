## Summary

`safe_generation` is a single-turn LLM workflow that generates a response to any text prompt and then immediately judges its own output for quality before deciding whether to return it as-is, refine it, or accept it as a best-effort result. It wraps the entire process in a typed exception handler that covers four LLM-specific failure modes — hallucination, context overflow, refusal, and budget exhaustion — each producing a distinct status code so callers can handle failures gracefully. Teams building production-grade LLM features benefit by getting a predictable, labeled result even when the model misbehaves.

---

## Detailed Specification

### 1. Purpose

Generate a high-quality LLM response to a user prompt, self-assess that response, optionally refine it once, and return a labeled result — while gracefully handling four categories of LLM-specific runtime failure.

---

### 2. High-level Description

The `safe_generation` WORKFLOW accepts a single text prompt and produces a text result tagged with a quality status string. It uses three CREATE FUNCTIONs: `response` generates the initial answer, `quality_assess` acts as an LLM-as-judge scoring the answer against a three-value scale (`high_quality`, `acceptable`, `low_quality`), and `improved` rewrites the answer when the judge deems it merely acceptable. After the initial GENERATE call into `@result`, a second GENERATE call populates `@quality`, which feeds an EVALUATE block that branches on the judge's verdict: a `high_quality` verdict returns immediately with `status='high_quality'`, an `acceptable` verdict triggers one additional GENERATE into `@result` using `improved` before returning with `status='refined'`, and any other verdict returns the original result with `status='best_effort'`. Outside the main path, an EXCEPTION block handles four typed LLM failures: `HallucinationDetected` re-runs `response` and returns with `status='conservative'`; `ContextLengthExceeded` retries the generation up to three times at low temperature; `RefusalToAnswer` short-circuits and returns the original prompt with `status='refused'`; `BudgetExceeded` returns whatever partial result exists with `status='truncated'`. The workflow carries a `SECURITY: CLASSIFICATION: internal` declaration, indicating it is not intended for public-facing exposure without additional hardening.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW safe_generation` | `WORKFLOW` | Top-level orchestration unit; declares `INPUT:` / `OUTPUT:` / `SECURITY:` |
| `CREATE FUNCTION response` | `CREATE FUNCTION` | Prompt template; `{prompt}` slot injected at call time |
| `CREATE FUNCTION quality_assess` | `CREATE FUNCTION` | LLM-as-judge template; returns a sentinel token from a fixed vocabulary |
| `CREATE FUNCTION improved` | `CREATE FUNCTION` | Rewrite template; takes both `{result}` and `{prompt}` slots |
| `GENERATE response(@prompt) INTO @result` | `GENERATE … INTO @var` | First LLM call; binds initial answer to shared state variable |
| `GENERATE quality_assess(@result) INTO @quality` | `GENERATE … INTO @var` | Second LLM call; judge verdict bound to `@quality` |
| `GENERATE improved(@result, @prompt) INTO @result` | `GENERATE … INTO @var` | Conditional third LLM call; overwrites `@result` in place |
| `EVALUATE @quality WHEN … END` | `EVALUATE` | Semantic branch on judge output; not string equality — LLM resolves match |
| `RETURN @result WITH status = 'high_quality'` | `RETURN … WITH status=` | Non-trivial: status drives caller-side handling logic |
| `RETURN @result WITH status = 'refined'` | `RETURN … WITH status=` | Non-trivial: signals one refinement pass was applied |
| `RETURN @result WITH status = 'best_effort'` | `RETURN … WITH status=` | Non-trivial: signals quality gate was not met |
| `EXCEPTION WHEN HallucinationDetected THEN …` | `EXCEPTION WHEN <Type>` | Typed handler; re-runs generation conservatively |
| `EXCEPTION WHEN ContextLengthExceeded THEN RETRY …` | `EXCEPTION WHEN <Type>` | Built-in RETRY directive with `temperature` and `LIMIT` overrides |
| `EXCEPTION WHEN RefusalToAnswer THEN …` | `EXCEPTION WHEN <Type>` | Returns prompt unchanged with `status='refused'` |
| `EXCEPTION WHEN BudgetExceeded THEN …` | `EXCEPTION WHEN <Type>` | Graceful truncation; returns partial `@result` |
| `@prompt`, `@result`, `@quality` | SPL `@var` shared state | All mutable within the workflow frame; `@result` is overwritten on refinement |

---

### 4. Logical Functions / Prompts

**`response(prompt TEXT)`**
- **Role:** Primary generation — produces the first-pass answer the rest of the workflow evaluates and potentially refines.
- **Prompt conventions:** Minimal system framing ("helpful assistant"); single `{prompt}` slot. No sentinel tokens or structured output required — free-form prose expected.

**`quality_assess(result TEXT)`**
- **Role:** LLM-as-judge — scores the current `@result` so the EVALUATE branch can make a routing decision.
- **Prompt conventions:** Strict three-value vocabulary enforced by the prompt: `high_quality`, `acceptable`, `low_quality`. The EVALUATE block matches against these tokens. The LLM must reply with exactly one of these values; the prompt does not instruct wrapping or JSON.

**`improved(result TEXT, prompt TEXT)`**
- **Role:** Single-pass refinement — rewrites `@result` when the judge returns `acceptable`, using the original `@prompt` as grounding context to avoid semantic drift.
- **Prompt conventions:** Two slots: `{result}` (current output) and `{prompt}` (original intent). No output format constraint — free-form improved prose expected. Only invoked once; there is no refinement loop.

---

### 5. Control Flow

1. **Initial generation:** `GENERATE response(@prompt) INTO @result` — single LLM call, unconditional.
2. **Quality judgment:** `GENERATE quality_assess(@result) INTO @quality` — LLM-as-judge scores the result.
3. **Branch via EVALUATE:**
   - `high_quality` → terminate immediately, `status='high_quality'` (zero extra LLM calls).
   - `acceptable` → one refinement pass via `GENERATE improved(…)`, then terminate with `status='refined'`.
   - anything else (`low_quality` or unexpected) → terminate without refinement, `status='best_effort'`.
4. **Exception paths (parallel to steps 1–3, not sequential):**
   - `HallucinationDetected` → re-runs `response(@prompt)` once, returns `status='conservative'`.
   - `ContextLengthExceeded` → RETRY the failing call up to 3 times at `temperature=0.1`.
   - `RefusalToAnswer` → short-circuits, returns `@prompt` verbatim with `status='refused'`.
   - `BudgetExceeded` → returns whatever is in `@result` at time of exception, `status='truncated'`.

There is no WHILE loop; the maximum number of LLM calls on the happy path is three (generate → judge → refine). The four status tokens (`high_quality`, `refined`, `best_effort`, `conservative`, `refused`, `truncated`) are all non-trivial and meaningful to any downstream EVALUATE or CALL that invokes this workflow.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 2 above as text2spl input)
spl3 text2spl --description "Generate a high-quality LLM response to a user prompt, \
self-assess that response using an LLM-as-judge scoring it as high_quality, acceptable, \
or low_quality, optionally refine it once if acceptable, and return a labeled result with \
a status tag. Handle four typed LLM exceptions: HallucinationDetected, \
ContextLengthExceeded, RefusalToAnswer, and BudgetExceeded." \
--mode workflow --adapter ollama -m gemma3

# Step 2 — compile to any target
spl3 splc compile safe_generation.spl --lang python/pocketflow
spl3 splc compile safe_generation.spl --lang python/langgraph
spl3 splc compile safe_generation.spl --lang go
```