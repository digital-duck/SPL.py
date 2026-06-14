## Summary

This workflow converts a plain-language diagram description into valid Mermaid syntax and automatically repairs compilation errors by feeding them back to the LLM. It targets developers and technical writers who want LLM-assisted diagramming without manually debugging Mermaid syntax. The self-healing loop means the user gets a compilable diagram even when the first generation attempt is incorrect.

---

## Detailed Specification

### 1. Purpose

Generate syntactically valid Mermaid diagram code from a natural-language description, using an iterative LLM repair loop backed by the official Mermaid CLI compiler for validation.

---

### 2. High-level Description

This workflow implements a **generate-validate-repair** pattern using two logical functions: `WriteChart` and `CompileChart`. The WORKFLOW accepts a single `task` string (a plain-language diagram description) and maintains a shared list of failed attempts throughout its lifetime.

`WriteChart` constructs a prompt that includes the original task and, on subsequent iterations, the full history of previously failed Mermaid code blocks along with their compiler error messages. It issues a GENERATE call to the LLM, instructing it to emit only a fenced ` ```mermaid ``` ` block. The output is extracted from the fence and stored in the shared `@chart` variable.

`CompileChart` performs a CALL to a side-effect tool: it writes `@chart` to a temporary file and invokes `npx mmdc` (mermaid-cli) via subprocess. If compilation succeeds, the workflow terminates with RETURN status `"done"`. If it fails and fewer than three attempts have been recorded, the error is appended to the `@attempts` log and the workflow REPLAYs from `WriteChart` with RETURN status `"fix"`. After three consecutive failures, the workflow exits with RETURN status `"done"` carrying the failure state, preventing infinite loops.

Exception handling covers a subprocess timeout (60 seconds), which is treated as a non-retryable failure and returned immediately as an error result. No external storage or multi-model design is employed; the same LLM handles all generation and repair calls.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW MermaidGenerator` | `create_mermaid_flow()` + `Flow(start=write_chart)` | Top-level orchestration unit |
| `CREATE FUNCTION write_chart_prompt` | `WriteChart.exec()` prompt string | Embeds `{task}` and `{history}` slots |
| `GENERATE write_chart_prompt(...) INTO @chart` | `call_llm(prompt)` → `shared["chart"]` | LLM call; extracts fenced mermaid block |
| `CALL compile_mermaid(@chart) INTO @result` | `CompileChart.exec()` subprocess call | Side-effect: writes temp file, runs `npx mmdc` |
| `WHILE attempts < 3 AND NOT success DO ... END` | `CompileChart.post()` checking `len(shared["attempts"]) >= 3` | Drives the fix→write→compile loop |
| `EVALUATE @result WHEN success THEN ... ELSE ... END` | `if exec_res["success"]: return "done" ... return "fix"` | Real branch: `"done"` vs `"fix"` action tokens |
| `RETURN @chart WITH status="done"` | `return "done"` in `CompileChart.post()` | Terminates the flow (success or max-retries) |
| `RETURN WITH status="fix"` | `return "fix"` in `CompileChart.post()` | Loops back to `WriteChart` with error context |
| `@attempts` shared variable | `shared["attempts"]` (list of `{code, error}` dicts) | Accumulates failure history passed to next LLM call |
| `@chart` shared variable | `shared["chart"]` (string) | Current Mermaid code under validation |
| `EXCEPTION WHEN TimeoutError THEN ...` | `except subprocess.TimeoutExpired` | Returns non-retryable failure immediately |

---

### 4. Logical Functions / Prompts

**`write_chart_prompt`**
- **Role**: Primary generation function; produces a complete Mermaid diagram from the task description on the first pass, or repairs a broken diagram on subsequent passes.
- **Key prompt conventions**:
  - Sentinel instruction: `Output ONLY the mermaid code in a \`\`\`mermaid\`\`\` block. Do not include any other text.`
  - On retry: injects numbered history blocks (`Attempt N: <code> / Error: <stderr>`) and adds an explicit repair directive: `Fix the syntax errors from the previous attempts.`
  - Extraction: splits on ` ```mermaid ` and ` ``` ` delimiters — the LLM must respect the fence exactly.

**`compile_mermaid` (tool, not LLM)**
- **Role**: Ground-truth validator using `npx mmdc`; replaces any LLM-based self-scoring with an objective compiler signal.
- **Key conventions**:
  - Filters stderr to lines containing `Parse error`, `Expecting`, or `Error` for cleaner feedback (max 3 lines) before injecting into the next prompt.
  - Treats both non-zero exit code and missing output SVG as failure conditions.
  - Hard timeout of 60 seconds treated as a distinct error case.

---

### 5. Control Flow

```
INPUT: task (string)
  │
  ▼
WriteChart — GENERATE write_chart_prompt(task, attempts=[]) INTO @chart
  │
  ▼
CompileChart — CALL compile_mermaid(@chart) INTO @result
  │
  EVALUATE @result:
    ├── success=true  ──────────────────────────────► RETURN @chart WITH status="done"  [SUCCESS]
    │
    ├── success=false AND len(attempts) < 3 ──► append {code, error} to @attempts
    │                                           RETURN WITH status="fix"
    │                                           └──► WriteChart (loop)
    │
    └── success=false AND len(attempts) >= 3 ──► RETURN @chart WITH status="done"  [MAX RETRIES]
```

Termination is guaranteed: the `WHILE` condition (`attempts < 3`) ensures the loop exits after at most 3 LLM calls. The `"done"` token is non-trivial because it is emitted under two distinct semantic conditions (success and exhaustion) and the caller distinguishes them by inspecting `@attempts` length.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Generate syntactically valid Mermaid diagram code from a \
  natural-language task description. Use a WHILE loop (max 3 iterations) that calls \
  WriteChart (GENERATE: prompt includes task + history of prior failed code+errors) then \
  CompileChart (CALL: runs npx mmdc on a temp file). EVALUATE the compiler result: on \
  success RETURN with status='done'; on failure append the error to @attempts and loop \
  back; after 3 failures RETURN with status='done' and failure state. \
  EXCEPTION WHEN TimeoutError THEN return failure immediately." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile mermaid_generator.spl --lang python/pocketflow
spl3 splc compile mermaid_generator.spl --lang python/langgraph
spl3 splc compile mermaid_generator.spl --lang go
```