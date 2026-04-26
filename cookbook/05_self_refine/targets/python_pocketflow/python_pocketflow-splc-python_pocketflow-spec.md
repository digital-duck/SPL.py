## 0. High-level Description

This workflow implements the **Self-Refine** pattern: an iterative draft–critique–refine loop that progressively improves a written response until it meets quality criteria or exhausts a budget. The workflow begins with a single GENERATE call using a `draft` function to produce an initial response to a user-supplied task, storing the result in `@current`. It then enters a WHILE loop driven by an iteration counter bounded by `max_iterations`: each iteration fires a GENERATE call using a `critique` function that evaluates `@current` and stores actionable feedback in `@feedback`. An EVALUATE branch inspects `@feedback` for the sentinel token `[APPROVED]`; if present, or if the iteration budget is exhausted, control transfers to a terminal RETURN step; otherwise a GENERATE call using a `refine` function rewrites `@current` using the feedback and loops back to `critique`. The workflow uses two configurable LLM models — a writer model for `draft`/`refine` and a critic model for `critique` — enabling a multi-model design where judgment and generation are separated. Each GENERATE result is persisted as a side-effect via CALL to the filesystem (draft logs, feedback logs, and a final output file). No explicit EXCEPTION handler is declared; runtime errors propagate naturally.

---

## 1. Purpose

Automatically improves a written response to a given task through iterative LLM-driven self-critique and refinement, terminating when the critic approves the output or a maximum iteration count is reached.

---

## 2. SPL ↔ Python — PocketFlow Construct Mapping

| SPL Construct | Python — PocketFlow Equivalent | Notes |
|---|---|---|
| `WORKFLOW <name>` | `build_flow() → Flow(start=draft)` | Flow wiring replaces the declarative WORKFLOW block |
| `CREATE FUNCTION <name>` | Module-level `*_PROMPT` string constants | `DRAFT_PROMPT`, `CRITIQUE_PROMPT`, `REFINE_PROMPT` — each is a `{param}`-slotted template |
| `GENERATE <fn>(...) INTO @<var>` | `Node.exec()` calling `_call_llm(model, prompt)` | Return value of `exec()` is loaded into `shared` by `post()` |
| `CALL <tool>(...) INTO @<var>` | `_write(path, content)` calls inside `post()` | Pure side-effect; no return value captured in shared |
| `WHILE <cond> DO … END` | `CritiqueNode.post()` returning `"refine"` + `RefineNode.post()` returning `"critique"` | The back-edge `refine → critique` is the loop; the condition is checked in `CritiqueNode.post()` |
| `EVALUATE @<var> WHEN contains('…') THEN … ELSE …` | `if '[APPROVED]' in exec_res` inside `CritiqueNode.post()` | Sentinel-token branch; also checks `i >= max_iterations` as a second exit condition |
| `RETURN @<var> WITH status=, iterations=` | `CommitNode.post()` writing `shared["status"]` and printing iteration count | No explicit structured return object; status written back to shared store |
| `EXCEPTION WHEN <Type> THEN …` | Not implemented | HTTP/LLM errors propagate as unhandled Python exceptions |
| Shared `@vars` | `shared` dict passed through all `prep()`/`post()` calls | `@current`, `@feedback`, `@iteration` map to `shared["current"]`, `shared["feedback"]`, `shared["iteration"]` |
| `INPUT @var` declarations | `@click.option(...)` parameters loaded into `shared` in `main()` | `task`, `max_iterations`, `writer_model`, `critic_model`, `log_dir` |

---

## 3. Logical Functions / Prompts

**`draft` (`DRAFT_PROMPT`)**
- **Role:** Produces the initial response. Called exactly once at workflow start.
- **Input slots:** `{task}` — the user-supplied task string.
- **Output:** Free-form prose; stored in `@current`.
- **Model:** `writer_model` (default: `gemma3`).
- **Conventions:** No sentinel tokens; output is consumed verbatim as the first draft.

---

**`critique` (`CRITIQUE_PROMPT`)**
- **Role:** Evaluates `@current` and either approves it or returns actionable improvement notes. Acts as the EVALUATE condition in the WHILE loop.
- **Input slots:** `{current}` — the draft under review.
- **Output:** Either the exact string `[APPROVED]` (sentinel token, terminates the loop) or a multi-sentence critique string stored in `@feedback`.
- **Model:** `critic_model` (default: `llama3.2`).
- **Conventions:** The prompt instructs the model to emit `[APPROVED]` *only* when no meaningful improvement exists, reducing false positives. The sentinel is detected with a substring check.

---

**`refine` (`REFINE_PROMPT`)**
- **Role:** Rewrites `@current` using `@feedback`, producing an improved draft. Called on every non-approved, non-exhausted iteration.
- **Input slots:** `{current}`, `{feedback}`.
- **Output:** Improved prose; overwrites `@current` in shared store.
- **Model:** `writer_model` (default: `gemma3`).
- **Conventions:** No sentinel tokens; output replaces `@current` unconditionally.

---

## 4. Control Flow

```
INPUT @task, @max_iterations, @writer_model, @critic_model, @log_dir

GENERATE draft(@task) INTO @current          ← DraftNode
CALL write("draft_0.md", @current)           ← side-effect in DraftNode.post()
SET @iteration = 0

WHILE @iteration < @max_iterations DO
    GENERATE critique(@current) INTO @feedback        ← CritiqueNode
    CALL write("feedback_{i}.md", @feedback)

    EVALUATE @feedback
        WHEN contains("[APPROVED]") THEN → commit     ← early exit
        ELSE
            IF @iteration >= @max_iterations THEN → commit  ← budget exit
            ELSE
                GENERATE refine(@current, @feedback) INTO @current  ← RefineNode
                CALL write("draft_{i}.md", @current)
                SET @iteration = @iteration + 1
                → critique                            ← loop back-edge
            END
    END
END

RETURN @current WITH status=("complete"|"max_iterations"), iterations=@iteration
CALL write("final.md", @current)             ← CommitNode side-effect
```

**Termination conditions:**
1. `[APPROVED]` sentinel detected in `@feedback` — `status = "complete"`
2. `@iteration >= max_iterations` — `status = "max_iterations"`

Both routes converge on `CommitNode`, which performs the final CALL and sets `@status`.

---

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This workflow implements the Self-Refine pattern: \
an iterative draft–critique–refine loop that progressively improves a written \
response until it meets quality criteria or exhausts a budget. The workflow \
begins with a single GENERATE call using a draft function to produce an initial \
response to a user-supplied task, storing the result in @current. It then enters \
a WHILE loop driven by an iteration counter bounded by max_iterations: each \
iteration fires a GENERATE call using a critique function that evaluates @current \
and stores actionable feedback in @feedback. An EVALUATE branch inspects @feedback \
for the sentinel token [APPROVED]; if present, or if the iteration budget is \
exhausted, control transfers to a terminal RETURN step; otherwise a GENERATE call \
using a refine function rewrites @current using the feedback and loops back to \
critique. The workflow uses two configurable LLM models — a writer model for \
draft/refine and a critic model for critique — enabling a multi-model design where \
judgment and generation are separated. Each GENERATE result is persisted as a \
side-effect via CALL to the filesystem (draft logs, feedback logs, and a final \
output file). No explicit EXCEPTION handler is declared." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile self_refine.spl --lang python/pocketflow
spl3 splc compile self_refine.spl --lang python/langgraph
spl3 splc compile self_refine.spl --lang go
```