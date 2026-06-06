## 0. High-level Description

This WORKFLOW ResearchAgent implements an iterative web-research agent that loops between deciding and searching until it has gathered enough information to produce a final answer. It uses CREATE FUNCTION DecideAction as a prompt template that takes {question} and {context} slots and instructs the LLM to return a YAML-formatted decision specifying either a search_query or a draft answer along with an action field. The control flow uses a WHILE loop that continues as long as the action is "search"; inside the loop, an EVALUATE branches on the action—when it contains "search", a CALL to search_web_duckduckgo fetches web results that are appended to the accumulated context, and when it contains "answer", CREATE FUNCTION AnswerQuestion generates a comprehensive final answer from the question and the full research context. The workflow terminates via RETURN @answer WITH status="complete", iterations=<count>, and optionally performs a side-effect CALL to write the answer to a file. An EXCEPTION handler catches YAML parse errors from the DecideAction LLM output, retrying once with corrected block-scalar formatting before raising a ValueError. The design is single-model (one LLM serves both the decision and answer-generation roles) with an external tool call for DuckDuckGo web search.

## 1. Purpose

This workflow automates iterative web research on a user-supplied question by repeatedly searching for information and then synthesizing a comprehensive final answer.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW ResearchAgent` | `create_agent_flow()` returning `Flow(start=decide)` | Top-level orchestration; `main.py` is the entry point |
| `CREATE FUNCTION DecideAction` | `DecideAction.exec()` prompt string | Prompt template with `{question}` and `{context}` slots; returns parsed YAML dict |
| `CREATE FUNCTION AnswerQuestion` | `AnswerQuestion.exec()` prompt string | Prompt template with `{question}` and `{context}` slots; returns plain-text answer |
| `GENERATE DecideAction(question, context) INTO @decision` | `DecideAction.prep()` → `exec()` → `call_llm(prompt)` → YAML parse | LLM call + structured output parsing |
| `CALL search_web_duckduckgo(query) INTO @search_results` | `SearchWeb.exec()` → `search_web_duckduckgo(search_query)` | External tool (DuckDuckGo) side-effect call |
| `EVALUATE @decision.action WHEN contains('search') THEN … ELSE … END` | `DecideAction.post()` if/else on `exec_res["action"]` | Branch on LLM-decided action |
| `WHILE @action == "search" DO … END` | Graph cycle: `decide -"search">> search; search -"decide">> decide` | Implicit loop via cyclic PocketFlow edges |
| `RETURN @answer WITH status="complete"` | `AnswerQuestion.post()` stores `shared["answer"]`, returns `"done"` | Terminal node ends the flow |
| `@question, @context, @search_query, @answer` | `shared` dict keys | Shared mutable state across nodes |
| `EXCEPTION WHEN YAMLParseError THEN retry_with_fix END` | `parse_yaml_safely()` try/except with block-scalar repair | Catches `yaml.YAMLError`, retries once, then raises `ValueError` |
| `CALL write_file(out, content)` | `Path(out).write_text(...)` in `main.py` | Optional side-effect: persist answer to disk |

## 3. Logical Functions / Prompts

### DecideAction
- **Name:** `DecideAction`
- **Role:** The orchestrator prompt; examines the current question and accumulated research context, then decides whether more web searching is needed or whether sufficient information exists to answer.
- **Key prompt conventions:**
  - Output must be a YAML block inside a fenced ` ```yaml … ``` ` code block.
  - Required YAML fields: `thinking` (block scalar `|`), `action` (`search` or `answer`), `reason` (block scalar `|`), `answer` (block scalar `|`, empty if action is search), `search_query` (plain single-line string, present only if action is search).
  - Sentinel tokens: the action field acts as the routing key (`search` vs `answer`).
  - A fallback parser extracts YAML from raw text if no fenced block is found, and repairs missing block-scalar markers on retry.

### AnswerQuestion
- **Name:** `AnswerQuestion`
- **Role:** The final synthesis prompt; takes the original question and all accumulated research context and produces a comprehensive plain-text answer.
- **Key prompt conventions:**
  - Straightforward free-text output (no structured format required).
  - Instructs the LLM to base the answer on the provided research results.

## 4. Control Flow

1. **Initial step:** The workflow starts by reading `@question` from the shared state and initializing `@context` to `"No previous search"`. It then calls `GENERATE DecideAction(question, context) INTO @decision`.
2. **WHILE loop:** The implicit loop condition is `@decision.action == "search"`. As long as this holds, the workflow remains inside the loop body.
3. **Loop body — EVALUATE branch:**
   - **WHEN contains('search'):** Extract `@decision.search_query`, execute `CALL search_web_duckduckgo(search_query) INTO @search_results`, append the query and results to `@context`, then loop back to `GENERATE DecideAction(question, context) INTO @decision`.
   - **ELSE (action is 'answer'):** Save `@decision.answer` into `@context` (the draft answer becomes part of the context), then proceed to the terminal step.
4. **Terminal step:** Execute `GENERATE AnswerQuestion(question, context) INTO @answer`. Store the result in `@answer`.
5. **Termination:** `RETURN @answer WITH status="complete", iterations=<loop_count>`. Optionally, a side-effect `CALL write_file(out, f"Q: {question}\nA: {answer}\n")` persists the output if a file path was provided.

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```