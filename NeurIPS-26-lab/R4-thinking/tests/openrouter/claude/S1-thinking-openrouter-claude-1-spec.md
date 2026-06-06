## 0. High-level Description

This workflow implements a **Chain-of-Thought (CoT) reasoning engine** that solves complex analytical problems — such as probability puzzles — through iterative, self-correcting structured thinking. A single reusable logical function, `ChainOfThoughtNode`, acts as both the prompt template (CREATE FUNCTION) and the LLM call site (GENERATE), producing a YAML-structured response containing three fields: `current_thinking` (the reasoning narrative), `planning` (a hierarchical list of step-dictionaries with `description`, `status`, optional `result`, `mark`, and `sub_steps` keys), and `next_thought_needed` (a boolean termination sentinel). The workflow enters a WHILE loop — implemented as a self-referential node edge on the `"continue"` action token — that re-invokes the same node repeatedly, each iteration appending a new thought to the shared `thoughts` list, incrementing `current_thought_number`, and feeding all prior thoughts back into the next prompt as accumulated context. An EVALUATE-equivalent branch fires inside `post()`: when `next_thought_needed` resolves to `false`, the node writes the final `current_thinking` to `shared["solution"]`, optionally persists it to disk via a CALL-equivalent file-write side-effect, and returns the `"end"` action to terminate the loop; otherwise it returns `"continue"` to re-enter the loop. The model used is Claude 3.7 Sonnet (Anthropic), with a 6 000-token output budget, and the workflow tolerates transient LLM failures through PocketFlow's built-in `max_retries=3, wait=10` retry policy on the node. Validation of the YAML payload is enforced via assertion guards that raise immediately if required keys are absent or malformed, functioning as inline EXCEPTION handlers.

---

## 1. Purpose

Automatically solve complex multi-step reasoning problems (e.g., probability puzzles) by having an LLM iteratively generate, evaluate, and self-correct a structured plan until it reaches a verified conclusion, then optionally save the final solution to a file.

---

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW chain_of_thought` | `create_chain_of_thought_flow()` in `flow.py` + `Flow(start=cot_node)` | The `Flow` object is the named workflow container |
| `CREATE FUNCTION ChainOfThought(...)` | `ChainOfThoughtNode` class with `prep()` / `exec()` / `post()` | `prep` assembles prompt params; `exec` renders and calls the LLM; `post` processes the result |
| `GENERATE ChainOfThought(...) INTO @thought` | `call_llm(prompt)` inside `exec()` + `yaml.safe_load(...)` | LLM call via Anthropic Claude 3.7 Sonnet; result parsed from fenced YAML block into `thought_data` dict |
| `WHILE next_thought_needed DO ... END` | `cot_node - "continue" >> cot_node` self-loop + `return "continue"` in `post()` | Loop continues as long as `exec_res["next_thought_needed"]` is truthy |
| `EVALUATE @thought WHEN contains('next_thought_needed: false') THEN ... ELSE ... END` | `if not exec_res.get("next_thought_needed", True):` in `post()` | Branch: `"end"` action exits loop and stores solution; `"continue"` re-enters loop |
| `RETURN @solution WITH status="end"` | `shared["solution"] = dedented_thinking; return "end"` | Non-trivial termination token `"end"` drives loop exit; no further nodes follow |
| `CALL file_write(...) INTO @_` | `Path(out).write_text(...)` in `main.py` after flow completes | Side-effect: writes `Q: ...\n\n<solution>` to caller-specified path; only fires if `--out` provided |
| `EXCEPTION WHEN ValidationError THEN ...` | `assert` statements in `exec()` (checked keys: `current_thinking`, `planning`, `next_thought_needed`) | Assertion failures propagate as Python `AssertionError`; PocketFlow retry policy (`max_retries=3, wait=10`) catches transient LLM/network errors |
| Shared state (`@problem`, `@thoughts`, `@solution`, etc.) | `shared` dict passed through all node lifecycle methods | Keys: `problem`, `thoughts` (list), `current_thought_number`, `total_thoughts_estimate`, `solution` |
| Retry policy | `ChainOfThoughtNode(max_retries=3, wait=10)` | PocketFlow built-in; retries `exec()` up to 3 times with 10 s delay on exception |

---

## 3. Logical Functions / Prompts

### 3.1 `ChainOfThoughtNode` — Iterative Reasoning Prompt

- **Name:** `ChainOfThoughtNode` (serves as the sole CREATE FUNCTION in this workflow)
- **Role:** On every iteration, constructs a full-context prompt that includes the original problem, all prior thoughts (formatted with plan status trees), and detailed instructions for the current reasoning step; sends it to the LLM; parses and validates the structured YAML response.

**Key prompt conventions:**

| Convention | Detail |
|---|---|
| **Output sentinel** | `next_thought_needed: true/false` — boolean field in YAML; `false` signals the Conclusion step and terminates the loop |
| **Output format** | Response must be wrapped in a fenced ` ```yaml ... ``` ` block; extracted via `split("```yaml")[1].split("```")[0]` |
| **Plan schema** | `planning` is a list of dicts with mandatory keys `description` (str) and `status` (`"Pending"` / `"Done"` / `"Verification Needed"`); optional keys `result` (str), `mark` (str), `sub_steps` (recursive list of same schema) |
| **Evaluation instruction** | From thought 2 onward, `current_thinking` must open with `"Evaluation of Thought N: [Correct/Minor Issues/Major Error — explain]"` before proceeding to the next pending step |
| **Termination instruction** | `next_thought_needed` must be set to `false` **only** when the step with `description: "Conclusion"` is being executed |
| **First-thought bootstrap** | When `is_first_thought=True`, the prompt instructs the model to create an initial plan from scratch and immediately execute step 1, marking it `Done` with a `result` |
| **Context accumulation** | All prior thoughts are serialised as numbered blocks (`Thought N: / Thinking: / Plan Status After Thought N:`) separated by `--------------------` dividers and injected verbatim into each subsequent prompt |
| **Model & limits** | Claude 3.7 Sonnet (`claude-3-7-sonnet-20250219`), `max_tokens=6000` |

---

## 4. Control Flow

```
START
  │
  ▼
[ChainOfThoughtNode — Thought 1]
  prep()  → reads shared["problem"], initialises empty thoughts list,
             builds bootstrap plan [{Understand, Pending}, {High-level plan, Pending}, {Conclusion, Pending}],
             increments current_thought_number to 1
  exec()  → renders prompt (first-thought variant), calls LLM, parses YAML,
             validates required keys via assertions, attaches thought_number=1
  post()  → appends thought to shared["thoughts"]
            EVALUATE next_thought_needed:
              ├─ false → write shared["solution"], print conclusion, RETURN "end"  ← loop exits
              └─ true  → print intermediate thought/plan, RETURN "continue"
                           │
                           ▼  (self-loop on "continue")
              ┌────────────────────────────────────────────┐
              │  [ChainOfThoughtNode — Thought N]           │
              │  prep()  → serialises all prior thoughts,   │
              │             extracts last plan structure,    │
              │             increments thought counter       │
              │  exec()  → renders full-context prompt,     │
              │             calls LLM, parses & validates   │
              │  post()  → appends thought                  │
              │            EVALUATE next_thought_needed:    │
              │              ├─ false → RETURN "end" ───────┼──► EXIT LOOP
              │              └─ true  → RETURN "continue" ──┘
              └────────────────────────────────────────────┘

After flow.run(shared) returns:
  EVALUATE shared["solution"] AND --out flag:
    ├─ both present → CALL file_write(path, content)   ← side-effect
    └─ otherwise    → no file output
END
```

**Termination condition:** The WHILE loop terminates when the LLM sets `next_thought_needed: false` in its YAML response, which the prompt instructs it to do exclusively when executing the `"Conclusion"` step. There is no hard iteration cap enforced in code (the `total_thoughts_estimate: 10` field in shared state is advisory only and not checked by any guard).

**Exception path:** Any `AssertionError` from the validation block, or any `YAMLError` / network error from `call_llm`, triggers PocketFlow's retry mechanism (up to 3 attempts, 10 s apart). If all retries are exhausted, PocketFlow raises and the workflow aborts with an unhandled exception.

---

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This workflow implements a Chain-of-Thought (CoT) \
reasoning engine that solves complex analytical problems through iterative, \
self-correcting structured thinking. A single reusable logical function, \
ChainOfThoughtNode, acts as both the prompt template (CREATE FUNCTION) and the \
LLM call site (GENERATE), producing a YAML-structured response containing three \
fields: current_thinking (the reasoning narrative), planning (a hierarchical list \
of step-dictionaries with description, status, optional result, mark, and sub_steps \
keys), and next_thought_needed (a boolean termination sentinel). The workflow enters \
a WHILE loop that re-invokes the same node repeatedly, each iteration appending a \
new thought to the shared thoughts list, incrementing current_thought_number, and \
feeding all prior thoughts back into the next prompt as accumulated context. An \
EVALUATE branch fires after each LLM call: when next_thought_needed resolves to \
false, the node writes the final current_thinking to the solution variable, \
optionally persists it to disk via a CALL file-write side-effect, and issues \
RETURN WITH status=end to terminate the loop; otherwise it issues RETURN WITH \
status=continue to re-enter the loop. The model is Claude 3.7 Sonnet with a 6000 \
token output budget, and the workflow applies a max_retries=3 wait=10 retry policy \
on the node, with inline EXCEPTION handling via assertion guards that validate \
required YAML keys before the result is accepted." \
--mode workflow

# Step 2 — compile to any target runtime
spl3 splc compile chain_of_thought.spl --lang python/pocketflow
spl3 splc compile chain_of_thought.spl --lang python/langgraph
spl3 splc compile chain_of_thought.spl --lang go
```