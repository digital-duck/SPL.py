## Summary

Model Showdown sends the same user-supplied prompt to two different local LLMs simultaneously, then passes both responses to a neutral evaluator model that reproduces and scores them side by side. It exists to make multi-model comparison reproducible and scriptable — no shell loops, no manual copy-paste. Product teams, researchers, and prompt engineers benefit by seeing objective, logged comparisons in a single run.

---

## Detailed Specification

### 1. Purpose

Execute the same prompt against two user-specified LLMs in parallel, then produce a structured side-by-side evaluation that identifies which model gave the more helpful answer.

---

### 2. High-level Description

The `model_showdown` WORKFLOW accepts a prompt string and two model identifiers as INPUT, with a log directory for persisting results. It dispatches the prompt to both models concurrently using parallel CTEs (`WITH … SELECT … INTO`) — a `CALL PARALLEL` idiom — so neither model waits on the other. Each branch applies the `answer` CREATE FUNCTION, which is a minimal pass-through template that forwards the raw prompt text to the model with a standard helpful-assistant system role. Once both responses are captured into `@answer_1` and `@answer_2`, the workflow executes a single GENERATE step using the `compare_responses` CREATE FUNCTION: this acts as an LLM judge that reproduces both responses verbatim in a structured block and then scores each on quality, strengths, and weaknesses before naming a winner. Three CALL side-effects write the individual model responses and the final comparison to Markdown files under `@log_dir`. The workflow terminates with RETURN carrying `status = 'complete'` and the two model names as metadata; a top-level EXCEPTION handler for `GenerationError` short-circuits to `status = 'error'` if either parallel branch or the judge step fails.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW model_showdown` | `WORKFLOW` | Named workflow with typed INPUT/OUTPUT declarations |
| `CREATE FUNCTION answer(...)` | `CREATE FUNCTION` | Minimal pass-through prompt template; single `{prompt}` slot |
| `CREATE FUNCTION compare_responses(...)` | `CREATE FUNCTION` | LLM-judge template; six `{param}` slots including both model names and answers |
| `WITH … response_1 AS (…), response_2 AS (…) SELECT … INTO @answer_1, @answer_2` | `CALL PARALLEL … END` | Parallel CTE dispatch; both branches execute concurrently via `asyncio.gather` |
| `GENERATE compare_responses(…) INTO @comparison` | `GENERATE … INTO @var` | Sequential LLM call after parallel branches complete |
| `CALL write_file(…) INTO NONE` | `CALL … INTO @var` | Side-effect tool calls; result discarded (`INTO NONE`) |
| `@prompt`, `@model_1`, `@model_2`, `@answer_1`, `@answer_2`, `@comparison` | SPL `@vars` | Shared mutable state passed between steps |
| `RETURN @comparison WITH status = 'complete'` | `RETURN … WITH status=` | Non-trivial terminal status; pairs with `'error'` path |
| `RETURN … WITH status = 'error'` | `RETURN … WITH status=` | Short-circuit exit driven by EXCEPTION handler |
| `EXCEPTION WHEN GenerationError THEN …` | `EXCEPTION WHEN … THEN … END` | Typed recovery for any failed LLM generation in either branch or judge |

---

### 4. Logical Functions / Prompts

**`answer`**
- **Role:** Forwards the raw user prompt to whichever model is assigned to that parallel branch. Acts as a transparent relay — no framing, no instructions beyond the system role set inline.
- **Key conventions:** Single `{prompt}` slot. System role (`You are a helpful, knowledgeable assistant.`) is injected via `system_role(...)` at the call site, not inside the template body. Output is free-form prose from the target model.

**`compare_responses`**
- **Role:** LLM judge. Receives the original prompt plus both model names and their raw responses, then produces a structured evaluation.
- **Key conventions:** Reproduces each response verbatim inside a named sentinel block (`=== {model_1} ===` / `=== {model_2} ===`) before scoring. Scoring criteria: response quality, key strengths, key weaknesses. Concludes with an explicit winner statement and rationale. No numeric scores — qualitative prose only. Note: the template body references "three AI models" in its preamble, a leftover artifact; the actual workflow passes exactly two models.

---

### 5. Control Flow

1. **Parallel dispatch** — `WITH` CTE launches `ask_model_1` and `ask_model_2` concurrently; both branches apply the `answer` template against their respective models. Results bind to `@answer_1` and `@answer_2` upon completion of both branches.
2. **Judge step** — A single sequential GENERATE feeds all four values (`@prompt`, `@model_1`, `@answer_1`, `@model_2`, `@answer_2`) to `compare_responses`, storing the evaluation in `@comparison`.
3. **Side effects** — Three sequential CALL steps write `resp_<model_1>.md`, `resp_<model_2>.md`, and `comparison.md` to `@log_dir`.
4. **Termination** — RETURN `@comparison` with `status = 'complete'`, `model_1`, and `model_2` as metadata.
5. **Error path** — If any GENERATE in steps 1–2 raises `GenerationError`, the EXCEPTION handler fires and returns a fixed error string with `status = 'error'`, bypassing the file writes.

There is no WHILE loop and no EVALUATE branch in this workflow; control flow is a single parallel fan-out followed by a linear sequence to termination.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (paste Section 2 as text2spl input)
spl3 text2spl --description "Execute the same prompt against two user-specified LLMs \
in parallel using CALL PARALLEL, capture both responses, then run a single GENERATE \
judge step using a compare_responses CREATE FUNCTION that reproduces both responses \
verbatim in sentinel blocks and scores quality, strengths, and weaknesses before naming \
a winner. Write each raw response and the final comparison to Markdown files via CALL \
write_file side-effects. Handle GenerationError with an EXCEPTION block that returns \
status = 'error'." --mode workflow

# Step 2 — compile to any target
spl3 splc compile model_showdown.spl --lang python/pocketflow
spl3 splc compile model_showdown.spl --lang python/langgraph
spl3 splc compile model_showdown.spl --lang go
```