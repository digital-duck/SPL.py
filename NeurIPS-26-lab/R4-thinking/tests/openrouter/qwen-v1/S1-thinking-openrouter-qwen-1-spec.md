## 0. High-level Description
This workflow orchestrates an externalized Chain-of-Thought reasoning process by iteratively guiding an LLM through structured, step-by-step problem solving within a self-looping WHILE construct, supporting adapter-routed multi-model execution via a unified call interface. A CREATE FUNCTION named GenerateReasoningStep defines a dynamic prompt template that directs the model to evaluate prior thinking, execute the next pending plan item, update a hierarchical YAML planning structure, and emit a boolean termination flag. Each iteration invokes GENERATE to produce the structured response, followed by an EVALUATE block that parses the YAML, validates the schema, updates the shared thought history, and adjusts execution flow based on plan status markers. The loop persists WHILE the termination flag remains true, allowing the system to decompose complex tasks into sub-steps, correct errors through verification cycles, and converge on a final conclusion. Upon completion, a CALL side-effect optionally persists the verified answer to disk, an EXCEPTION handler intercepts malformed outputs or parsing failures for graceful recovery, and the workflow concludes via RETURN yielding the final solution alongside iteration counts and execution metadata.

## 1. Purpose
This implementation enables users to solve complex reasoning problems by externally orchestrating a structured, iterative Chain-of-Thought process that dynamically maintains and updates a step-by-step execution plan until a verified conclusion is reached.

## 2. SPL ↔ Python Construct Mapping
| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW <name>` | `create_chain_of_thought_flow()` + `main()` | Initializes the PocketFlow graph, configures shared state, and drives the execution lifecycle. |
| `CREATE FUNCTION <name>` | Prompt assembly in `ChainOfThoughtNode.exec()` | Constructs the instruction template using `textwrap.dedent` with dynamic `{problem}`, `{thoughts_text}`, and `{last_plan_text}` interpolation slots. |
| `GENERATE <fn>(...) INTO @<var>` | `response = call_llm(prompt)` | Routes context to the underlying model (Anthropic/shim), captures raw string output into a local variable. |
| `EVALUATE @<var> WHEN contains('...') THEN ...` | YAML parsing & `post()` state inspection | Splits ````yaml` blocks, asserts required keys, inspects `next_thought_needed` and plan dict statuses to route control flow. |
| `WHILE <cond> DO ... END` | `cot_node - "continue" >> cot_node` | PocketFlow self-loop; repeats `prep`/`exec`/`post` cycles as long as `post()` returns `"continue"`. |
| `CALL <tool>(...) INTO @<var>` | `Path(out).write_text(...)` in `main.py` | Optional file I/O side-effect executed only when `--out` is provided and a valid solution exists. |
| `EXCEPTION WHEN <Type> THEN ...` | `assert` statements & `yaml.YAMLError` handling | Catches missing keys, malformed YAML, or non-dict planning structures to prevent silent workflow failures. |
| Shared State (`@<var>`) | `shared` dictionary | Persists `problem`, `thoughts` (list), `current_thought_number`, and `solution` across loop iterations. |
| `RETURN @<var> WITH <k>=<v>` | `return "end"` + `shared["solution"] = ...` | Exits the loop, stores the final answer in shared state, and implicitly yields execution metadata. |

## 3. Logical Functions / Prompts
- **Name:** `GenerateReasoningStep`
- **Role in the workflow:** Drives the core iterative reasoning cycle by instructing the LLM to evaluate previous thinking, execute the next pending plan item, dynamically update a hierarchical task list, and decide whether additional reasoning steps are required.
- **Key prompt conventions:** 
  - **Sentinel tokens:** Strict ````yaml` ... ```` delimiters for reliable extraction.
  - **Output format:** Enforces a YAML dictionary containing `current_thinking` (multiline string), `planning` (list of nested dictionaries with mandatory `description` and `status` keys, plus optional `result`, `mark`, and `sub_steps`), and `next_thought_needed` (boolean).
  - **Scoring/Logic:** Replaces numeric confidence scoring with explicit state flags (`Pending`, `Done`, `Verification Needed`) and hierarchical breakdowns to guide external control flow.

## 4. Control Flow
The execution begins by initializing shared context with the target problem, empty thought history, thought counter, and a baseline plan structure. It enters a `WHILE next_thought_needed IS true DO` loop that repeatedly invokes `GENERATE GenerateReasoningStep` with accumulated context and formatted plan state. The raw LLM output is parsed and validated, triggering an `EXCEPTION` handler if the YAML is malformed or schema constraints are violated. An `EVALUATE` block inspects the `next_thought_needed` boolean and scans the `planning` list for a completed `Conclusion` entry. If the flag evaluates to `true`, the workflow appends the new thought to the shared state, prints progress, and returns `continue` to the loop head. When the flag evaluates to `false`, the `EVALUATE` block extracts the final reasoning trace, stores it in `@solution`, triggers a `CALL` side-effect to optionally write the result to a specified file path, and terminates the workflow via `RETURN @solution WITH status="completed", iterations=@current_thought_number`.

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```