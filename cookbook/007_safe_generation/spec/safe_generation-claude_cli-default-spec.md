## Summary

This workflow generates a response to a user-supplied prompt and immediately evaluates its quality using an LLM-as-judge pattern. If the output is merely acceptable, it triggers a self-refinement pass to improve it before returning. Developers building production LLM pipelines benefit from the built-in quality gate and exception handling for common LLM failure modes.

---

## Detailed Specification

### 1. Purpose

Generate a high-quality LLM response to an arbitrary text prompt, automatically assessing and refining the output, while gracefully handling LLM-specific runtime failures.

---

### 2. High-level Description

This WORKFLOW named `safe_generation` implements a single-pass generate-evaluate-refine pattern for robust LLM response production. It defines three CREATE FUNCTIONs: `response`, which instructs the LLM to answer the input prompt; `quality_assess`, which acts as an LLM-as-judge and returns one of three categorical quality tokens (`high_quality`, `acceptable`, `low_quality`); and `improved`, which rewrites the current result given the original prompt. Execution begins with a GENERATE call to `response` that stores the initial answer in `@result`, followed immediately by a GENERATE call to `quality_assess` that stores a quality verdict in `@quality`. An EVALUATE block branches on `@quality`: a `high_quality` verdict terminates with `RETURN @result WITH status='high_quality'`; an `acceptable` verdict triggers one GENERATE call to `improved` that overwrites `@result` and then returns with `status='refined'`; any other verdict returns the best available output with `status='best_effort'`. Four EXCEPTION handlers guard against LLM-specific failures: `HallucinationDetected` re-generates from scratch and returns with `status='conservative'`; `ContextLengthExceeded` retries up to three times at low temperature; `RefusalToAnswer` returns the original prompt with `status='refused'`; and `BudgetExceeded` returns whatever partial result exists with `status='truncated'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW safe_generation` | `WORKFLOW <name>` | Top-level orchestration unit with declared INPUT/OUTPUT and SECURITY classification |
| `CREATE FUNCTION response(...)` | `CREATE FUNCTION <name>` | Prompt template for initial response generation |
| `CREATE FUNCTION quality_assess(...)` | `CREATE FUNCTION <name>` | LLM-as-judge template; output is a categorical quality token |
| `CREATE FUNCTION improved(...)` | `CREATE FUNCTION <name>` | Self-refinement template; takes both original prompt and current result |
| `GENERATE response(@prompt) INTO @result` | `GENERATE <fn>(...) INTO @<var>` | LLM call; result stored in shared workflow variable |
| `GENERATE quality_assess(@result) INTO @quality` | `GENERATE <fn>(...) INTO @<var>` | LLM-as-judge call; verdict stored for EVALUATE |
| `EVALUATE @quality WHEN ... THEN ... ELSE ... END` | `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | Branches on quality token; drives non-trivial status returns |
| `RETURN @result WITH status='high_quality'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status token signals quality tier to caller |
| `RETURN @result WITH status='refined'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status signals a refinement pass occurred |
| `RETURN @result WITH status='best_effort'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial status signals quality was insufficient |
| `EXCEPTION WHEN HallucinationDetected THEN` | `EXCEPTION WHEN <Type> THEN` | Named LLM-specific exception handler; re-generates conservatively |
| `EXCEPTION WHEN ContextLengthExceeded THEN` | `EXCEPTION WHEN <Type> THEN` | Retries with reduced temperature up to 3 times |
| `EXCEPTION WHEN RefusalToAnswer THEN` | `EXCEPTION WHEN <Type> THEN` | Returns prompt itself with `status='refused'` |
| `EXCEPTION WHEN BudgetExceeded THEN` | `EXCEPTION WHEN <Type> THEN` | Returns partial result with `status='truncated'` |
| `@prompt`, `@result`, `@quality` | Shared state (`@<var>`) | Workflow-scoped variables passed between GENERATE and EVALUATE steps |

---

### 4. Logical Functions / Prompts

**`response(prompt TEXT)`**
- Role: Initial generation; the primary LLM call that produces a candidate answer.
- Conventions: Generic assistant persona; no sentinel tokens; output is free-form text stored in `@result`.

**`quality_assess(result TEXT)`**
- Role: LLM-as-judge; evaluates the candidate answer and emits a categorical verdict.
- Key conventions: Output is constrained to exactly one of three sentinel tokens — `high_quality`, `acceptable`, or `low_quality` — which the EVALUATE block matches directly. Sentinel tokens must appear verbatim for branching to work correctly.

**`improved(result TEXT, prompt TEXT)`**
- Role: Self-refinement; rewrites the current result with awareness of the original prompt.
- Conventions: Takes two parameters (current output and original intent); output overwrites `@result` in-place. Only invoked on the `acceptable` branch, so it runs at most once per workflow execution.

---

### 5. Control Flow

1. **Initial generation** — GENERATE `response(@prompt)` produces `@result`.
2. **Quality assessment** — GENERATE `quality_assess(@result)` produces `@quality`.
3. **EVALUATE branch** —
   - `high_quality` → RETURN immediately with `status='high_quality'` (best path).
   - `acceptable` → GENERATE `improved(@result, @prompt)` overwrites `@result`, then RETURN with `status='refined'`.
   - anything else → RETURN `@result` as-is with `status='best_effort'` (no further improvement attempted).
4. **Exception paths** — Any EXCEPTION interrupts normal flow:
   - `HallucinationDetected`: re-runs GENERATE `response(@prompt)`, returns with `status='conservative'`.
   - `ContextLengthExceeded`: RETRY up to 3 times at `temperature=0.1`.
   - `RefusalToAnswer`: returns the input `@prompt` unchanged with `status='refused'`.
   - `BudgetExceeded`: returns whatever is in `@result` with `status='truncated'`.

There is no WHILE loop; execution is linear with a single conditional branch and bounded exception retries.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Generate a high-quality LLM response to an arbitrary text prompt, automatically assessing and refining the output, while gracefully handling LLM-specific runtime failures." --mode workflow

# Step 2 — compile to any target
spl3 splc compile safe_generation.spl --lang python/pocketflow
spl3 splc compile safe_generation.spl --lang python/langgraph
spl3 splc compile safe_generation.spl --lang go
```