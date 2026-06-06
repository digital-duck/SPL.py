## 0. High-level Description

This workflow implements an iterative research agent using a WHILE-loop pattern driven by a GENERATE call to the `decide_action` function, which produces a structured YAML decision on each iteration. Three logical functions are defined: `decide_action` (a chain-of-thought reasoning prompt that evaluates accumulated context and returns either `action: search` with a `search_query` or `action: answer` with a final answer), `search_web` (a CALL side-effect that invokes DuckDuckGo and appends results to the shared `@context` variable), and `answer_question` (a GENERATE call that synthesizes accumulated research into a comprehensive final answer). The WHILE loop persists as long as `decide_action` returns `action: search`, with an EVALUATE branch directing execution to either CALL `search_web` (then loop back) or GENERATE `answer_question` (then terminate). A YAML-parsing fallback that forces block-scalar (`|`) notation on known keys and retries the parse acts as an implicit EXCEPTION handler for malformed LLM output. The workflow terminates with RETURN `@answer` WITH `status=done` after `answer_question` completes.

---

## 1. Purpose

Answers a user-supplied research question by iteratively deciding to search the web or synthesize a final answer, accumulating web search results in `@context` across multiple rounds until the agent determines it has sufficient information.

---

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW research_agent` | `create_agent_flow()` + `Flow(start=decide)` | Graph topology wired via PocketFlow `>>` edge operator |
| `CREATE FUNCTION decide_action` | `DecideAction` Node (`prep`/`exec`/`post`) | Structured YAML output; routing logic in `post()` |
| `CREATE FUNCTION search_web` | `SearchWeb` Node (`prep`/`exec`/`post`) | Pure CALL — no LLM involved |
| `CREATE FUNCTION answer_question` | `AnswerQuestion` Node (`prep`/`exec`/`post`) | Terminal GENERATE; free-form prose output |
| `GENERATE decide_action(...) INTO @decision` | `call_llm(prompt)` in `DecideAction.exec()` | Returns fenced YAML block parsed into a dict |
| `CALL search_web_duckduckgo(@search_query) INTO @results` | `search_web_duckduckgo(search_query)` in `SearchWeb.exec()` | Side-effect tool call; up to 5 DuckDuckGo results |
| `EVALUATE @decision WHEN contains('search') THEN ... ELSE ...` | `exec_res["action"] == "search"` in `DecideAction.post()` | Branches on the `action` field of parsed YAML |
| `WHILE action == "search" DO ... END` | `search - "decide" >> decide` cycle edge | PocketFlow graph cycle encodes the loop implicitly |
| `RETURN @answer WITH status="done"` | `return "done"` in `AnswerQuestion.post()` | Flow terminates; final answer stored in `shared["answer"]` |
| `EXCEPTION WHEN YAMLError THEN retry_with_block_scalars` | `parse_yaml_safely()` with key-line fixup and second `yaml.safe_load` | Forces `|` block scalars on known keys, retries once |
| `@context` | `shared["context"]` | Accumulates `SEARCH: / RESULTS:` blocks across iterations |
| `@question` | `shared["question"]` | Read-only workflow input; set before flow starts |
| `@search_query` | `shared["search_query"]` | Written by `DecideAction.post()`, consumed by `SearchWeb.prep()` |
| `@answer` | `shared["answer"]` | Final output; written by `AnswerQuestion.post()` |

---

## 3. Logical Functions / Prompts

### `decide_action`
- **Role**: The reasoning core of the agent. Given `@question` and accumulated `@context`, it decides whether to gather more information or deliver a final answer.
- **Key prompt conventions**:
  - Two-section prompt: `### CONTEXT` (question + previous research) and `### ACTION SPACE` (enumerate `search` and `answer` with parameter schemas).
  - Output is a fenced ` ```yaml ``` ` block with fields: `thinking` (block scalar `|`), `action` (`search` or `answer`), `reason` (block scalar `|`), `answer` (block scalar `|`, empty when searching), `search_query` (plain single-line string).
  - All multi-line fields explicitly require `|` block scalar to prevent embedded colons and quotes from breaking YAML parsing.
  - EXCEPTION fallback: if `yaml.safe_load` fails, lines matching known keys are rewritten to force `|` notation and parsing is retried once; if that also fails, a `ValueError` is raised.

### `answer_question`
- **Role**: Terminal synthesis prompt. Consumes `@question` and the full accumulated `@context` to produce a comprehensive prose answer.
- **Key prompt conventions**:
  - Two-section prompt: `### CONTEXT` and `## YOUR ANSWER:`.
  - No structured output format — free-form prose is expected.
  - No sentinel tokens or scoring; the raw LLM response is stored as `@answer`.

### `search_web` (tool call, not a prompt)
- **Role**: CALL side-effect. Executes a DuckDuckGo text search for `@search_query` and returns up to 5 results.
- **Key conventions**: Results are formatted as `Title: / URL: / Snippet:` blocks joined by double newlines. After execution, the result is appended to `@context` as `SEARCH: <query>\nRESULTS: <results>`, providing a running log of all searches performed.

---

## 4. Control Flow

1. **Initialization**: `@question` is populated from CLI input; `@context` defaults to `"No previous search"`. Flow starts at `decide_action`.
2. **WHILE loop entry**: `decide_action` GENERATEs a YAML decision. EVALUATE checks `@decision["action"]`:
   - **`action == "search"`** (loop continues): `@search_query` is set. CALL `search_web(@search_query) INTO @results`. `@context` is updated by appending `SEARCH: ... RESULTS: ...`. Returns `"decide"` → loops back to `decide_action`. WHILE condition remains true.
   - **`action == "answer"`** (loop exits): `@context` may be updated with an inline answer. Transitions to `answer_question`.
3. **Termination**: `answer_question` GENERATEs a final prose answer INTO `@answer`. RETURN `@answer` WITH `status=done`. Flow terminates.
4. **Exception path**: At any `decide_action` GENERATE step, if YAML parsing fails after the block-scalar fixup retry, a `ValueError` propagates — equivalent to EXCEPTION WHEN `YAMLParseError` THEN `raise`.

---

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (use Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile research_agent.spl --lang python/pocketflow
spl3 splc compile research_agent.spl --lang python/langgraph
spl3 splc compile research_agent.spl --lang go
```