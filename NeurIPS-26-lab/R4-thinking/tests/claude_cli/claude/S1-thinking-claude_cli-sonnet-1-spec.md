## 0. High-level Description

This workflow implements an externally-orchestrated Chain-of-Thought (CoT) reasoning loop using a single self-referential WORKFLOW named `ChainOfThought`. A single CREATE FUNCTION called `ChainOfThoughtStep` builds a structured prompt from the accumulated reasoning history (`@thoughts`), the current plan state (`@last_plan`), and the original `@problem`, instructing the LLM to evaluate the previous thought, execute the next pending plan step, update the plan structure (a list of status-tagged dictionaries with optional `sub_steps`), and emit a `next_thought_needed` sentinel field. Each invocation issues a GENERATE call that stores a YAML-encoded thought object into `@thought_data`, whose `current_thinking`, `planning`, and `next_thought_needed` fields are extracted and appended to `@thoughts`. A WHILE loop drives re-entry of the node via the `"continue"` action as long as `next_thought_needed` is `true`; an EVALUATE on that sentinel field then either returns `"continue"` (keeping the loop alive) or `"end"` (setting `@solution` and issuing a RETURN WITH `status=complete`, `iterations=thought_number`). EXCEPTION handling is implicit via PocketFlow's `max_retries=3` / `wait=10` retry policy, which triggers on YAML parse failures or missing required keys caught by `assert` guards in the exec phase. There are no multi-model or side-effect CALL steps beyond an optional file-write of the final solution.

---

## 1. Purpose

Solves complex multi-step reasoning problems (e.g., probability puzzles) by orchestrating an LLM through a structured, self-evaluating Chain-of-Thought loop that maintains and refines a hierarchical plan until the LLM signals completion.

---

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW ChainOfThought` | `create_chain_of_thought_flow()` + `Flow(start=cot_node).run(shared)` | PocketFlow `Flow` is the workflow container |
| `CREATE FUNCTION ChainOfThoughtStep` | `ChainOfThoughtNode.exec()` prompt construction block | Builds prompt from `@problem`, `@thoughts_text`, `@last_plan_text`, `@current_thought_number` |
| `GENERATE ChainOfThoughtStep(...) INTO @thought_data` | `response = call_llm(prompt)` → `thought_data = yaml.safe_load(...)` | LLM call + YAML extraction; result stored in `exec_res` |
| `WHILE next_thought_needed DO … END` | `cot_node - "continue" >> cot_node` self-loop + `post()` returning `"continue"` | PocketFlow action routing implements the loop |
| `EVALUATE @thought_data WHEN contains('next_thought_needed: false') THEN … ELSE …` | `if not exec_res.get("next_thought_needed", True)` in `post()` | Branches on sentinel field in parsed YAML |
| `RETURN @solution WITH status=complete, iterations=N` | `shared["solution"] = ...; return "end"` | `shared` dict persists solution; thought_number acts as iteration counter |
| `EXCEPTION WHEN YAMLError THEN retry` | `assert` statements + `max_retries=3, wait=10` in `ChainOfThoughtNode(...)` | PocketFlow retries the full `exec()` on assertion failure |
| `@problem`, `@thoughts`, `@solution` (shared vars) | `shared` dict keys: `"problem"`, `"thoughts"`, `"solution"` | Mutable dict passed through all node lifecycle phases |
| `@current_thought_number` | `shared["current_thought_number"]` incremented in `prep()` | Tracks loop iteration count |

---

## 3. Logical Functions / Prompts

### `ChainOfThoughtStep`

- **Role**: The sole prompt template driving all reasoning. Called once per loop iteration. It instructs the LLM to (1) evaluate the prior thought, (2) execute the first `Pending` plan step, (3) emit an updated hierarchical plan as a YAML list of dicts, and (4) set the `next_thought_needed` termination sentinel.
- **Key prompt conventions**:
  - **Sentinel token**: `next_thought_needed: false` — the loop termination signal embedded in YAML output.
  - **Output format**: Strict YAML fenced block (` ```yaml ... ``` `), with keys `current_thinking` (pipe-literal string), `planning` (list of dicts), `next_thought_needed` (bool).
  - **Plan dict schema**: `{description, status, result?, mark?, sub_steps?}` where `status` ∈ `{Pending, Done, Verification Needed}`.
  - **Evaluation prefix convention**: `current_thinking` must begin with `"Evaluation of Thought N: [Correct/Minor Issues/Major Error …]"` for all non-first thoughts.
  - **Termination rule**: `next_thought_needed` set to `false` only when executing the step with `description: "Conclusion"`.
  - **First-thought variant**: When `is_first_thought=true`, the prompt omits evaluation instructions and requests initial plan creation.

---

## 4. Control Flow

```
START
  │
  ▼
Initialize shared state:
  @problem ← CLI input
  @thoughts ← []
  @current_thought_number ← 0
  @solution ← None
  │
  ▼
┌─────────────────────────────────────────────────┐
│  WHILE (implicit — loop via "continue" action)  │
│                                                 │
│  prep():                                        │
│    Format @thoughts → @thoughts_text            │
│    Extract last plan → @last_plan_text          │
│    Increment @current_thought_number            │
│                                                 │
│  exec():                                        │
│    GENERATE ChainOfThoughtStep(                 │
│      @problem, @thoughts_text,                  │
│      @last_plan_text,                           │
│      @current_thought_number                    │
│    ) INTO @thought_data                         │
│    [EXCEPTION: assert fields present → retry]   │
│                                                 │
│  post():                                        │
│    Append @thought_data to @thoughts            │
│    EVALUATE @thought_data.next_thought_needed:  │
│      WHEN false THEN                            │
│        @solution ← @thought_data.current_think │
│        RETURN WITH status=complete,             │
│                    iterations=thought_number    │
│        → "end"                                  │
│      ELSE                                       │
│        Print thought + plan                     │
│        → "continue"  (re-enter loop)            │
└─────────────────────────────────────────────────┘
```

The loop has no hard iteration cap in the SPL sense; termination is purely LLM-driven via the `next_thought_needed` sentinel. The `total_thoughts_estimate` in shared state is informational only.

---

## 5. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile chain_of_thought.spl --lang python/pocketflow
spl3 splc compile chain_of_thought.spl --lang python/langgraph
spl3 splc compile chain_of_thought.spl --lang go
```