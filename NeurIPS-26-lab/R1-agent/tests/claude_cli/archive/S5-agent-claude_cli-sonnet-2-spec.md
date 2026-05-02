## 0. High-level Description

This workflow implements a ReAct (Reasoning + Acting) research agent that iteratively gathers web evidence before synthesizing a final answer. The WORKFLOW begins with a `DecideAction` CREATE FUNCTION that prompts an LLM to reason step-by-step about whether it has sufficient context to answer a question, outputting a structured YAML decision containing either `action: search` with a `search_query` or `action: answer`; this decision is stored in a shared `@decision` variable via GENERATE. A WHILE loop governs the research cycle: when the LLM signals `action: search`, a CALL to the `web_search` tool retrieves DuckDuckGo results and appends them to the `@context` accumulator, then control returns to DECIDE — this continues until the LLM judges itself ready or the `max_iterations` guard fires. When the exit condition is met, EVALUATE routes control to the `AnswerQuestion` CREATE FUNCTION, which performs a final GENERATE synthesizing all accumulated `@context` into a comprehensive answer stored in `@answer`. The RETURN is emitted with `status=complete` on a natural exit or `status=max_iterations` when the iteration cap is hit; no explicit EXCEPTION block is defined, though the `_call_llm` helper surfaces network failures as Python exceptions that would map to a `NetworkError` handler in SPL.

## 1. Purpose

Answers a user's research question by autonomously searching the web in a reasoning loop — stopping only when the LLM decides it has enough evidence or the iteration cap is reached — and returning a fully synthesized, citation-aware response.

## 2. SPL ↔ Python — PocketFlow Construct Mapping

| SPL Construct | Python — PocketFlow Equivalent | Notes |
|---|---|---|
| `WORKFLOW react_research` | `build_flow() → Flow(start=decide)` | Flow wiring replaces the declarative WORKFLOW header |
| `INPUT @question, @max_iterations` | `shared = {"question": ..., "max_iterations": ...}` passed to `Flow.run()` | `shared` dict is the ETL staging area / variable store |
| `CREATE FUNCTION DecideAction` | `DECIDEACTION_PROMPT` string constant | Prompt template with `{question}` and `{context}` slots |
| `CREATE FUNCTION AnswerQuestion` | `ANSWERQUESTION_PROMPT` string constant | Prompt template with `{question}` and `{context}` slots |
| `GENERATE DecideAction(...) INTO @decision` | `DecideNode.exec()` → `shared["decision"]` (via `post()`) | One-shot LLM call; result stored in shared state |
| `GENERATE AnswerQuestion(...) INTO @answer` | `AnswerNode.exec()` → `shared["answer"]` (via `post()`) | Final synthesis call |
| `CALL web_search(@decision) INTO @search_results` | `SearchNode.exec()` calling `_web_search(decision)` | Side-effect tool; result appended to `@context` |
| `EVALUATE @decision WHEN contains('action: answer')` | `DecideNode.post()` string-matching `exec_res` for `'action: answer'` | Also matches `'action: "answer"'` for YAML quoting variants |
| `WHILE sufficient_context = false DO ... END` | `search.post() → "decide"` back-edge in the Flow graph | Loop terminates via EVALUATE exit or iteration guard |
| Max-iterations guard | `if i >= shared.get("max_iterations", 3): return "answer"` in `DecideNode.post()` | Equivalent to a WHILE loop ceiling with forced EVALUATE exit |
| `RETURN @answer WITH status='complete'` | `shared["status"] = "complete"` + `AnswerNode.post() → None` | `None` return signals flow termination |
| `RETURN @answer WITH status='max_iterations'` | `shared["status"] = "max_iterations"` | Non-`complete` status mirrors `WorkflowCompositionError` signal |
| `@context` accumulator | `shared["context"]` string, appended in `SearchNode.post()` | Grows with each `--- Search Results ---` block |
| `@iteration` counter | `shared["iteration"]` integer, incremented in `SearchNode.post()` | Drives the max-iterations guard |
| `EXCEPTION WHEN NetworkError` | Unhandled — `_call_llm` raises raw `urllib` exceptions | Not implemented; would need explicit SPL handler |
| Adapter / model selection | `_call_llm("llama3.2", ...)` hardcoded to Ollama `localhost:11434` | SPL externalizes this via `--adapter ollama -m llama3.2` |
| `spl3 run ... --param question="..."` | `@click.command()` with `--question` / `--max-iterations` options | CLI entry point mirrors SPL's built-in parameter injection |

## 3. Logical Functions / Prompts

### `DecideAction`
- **Role:** The reasoning core of the ReAct loop. Called at the start of every iteration to judge whether accumulated context is sufficient for a final answer or whether more search is needed.
- **Key prompt conventions:**
  - Explicit chain-of-thought scaffold: four numbered reasoning steps force the model to inventory what it knows and identify gaps before committing to an action.
  - **Output sentinel:** structured YAML block with mandatory keys `reasoning`, `action`, and `search_query`. The `action` key is the routing sentinel — only `"search"` or `"answer"` are valid values.
  - YAML repair instruction included inline: `"If syntax errors occur, immediately provide a corrected version"` — a self-healing prompt pattern.
  - `search_query` is extracted by `_web_search` via regex (`search_query:\s*(.+)`), so it only needs to appear anywhere in the YAML value.

### `AnswerQuestion`
- **Role:** Terminal synthesis step. Consumes the full accumulated `@context` to produce the final user-facing response. Called exactly once, after the EVALUATE exit condition is met.
- **Key prompt conventions:**
  - No structured output format — free-form prose is expected.
  - Explicit instruction to reference "key findings and sources from your research" encourages grounded, citation-like answers.
  - Receives the complete `@context` string, which includes every `--- Search Results ---` block appended during the loop, giving the model full research provenance.

## 4. Control Flow

```
INPUT @question, @max_iterations
@context ← "Initial question: " + @question
@iteration ← 0

── WHILE loop ───────────────────────────────────────────────────────────────
│
│  GENERATE DecideAction(question=@question, context=@context) INTO @decision
│
│  EVALUATE @decision
│    WHEN contains('action: answer') OR @iteration >= @max_iterations THEN
│      EXIT loop → AnswerNode
│    ELSE  (action: search)
│      CALL web_search(search_query extracted from @decision) INTO @search_results
│      @context ← @context + "\n\n--- Search Results ---\n" + @search_results
│      @iteration ← @iteration + 1
│      CONTINUE loop (back-edge → DecideNode)
│  END
│
└─────────────────────────────────────────────────────────────────────────────

GENERATE AnswerQuestion(question=@question, context=@context) INTO @answer

EVALUATE @iteration
  WHEN @iteration < @max_iterations THEN
    RETURN @answer WITH status='complete', iterations=@iteration
  ELSE
    RETURN @answer WITH status='max_iterations', iterations=@iteration
END
```

**Termination guarantees:** The max-iterations guard fires inside `DecideNode.post()` before calling the LLM — so the final iteration still consumes one `DecideAction` call but is forced to route to `AnswerNode` regardless of the LLM's preference. This means at most `max_iterations` search calls and `max_iterations + 1` decide calls occur.

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 0 as the description)
spl3 text2spl --description "This workflow implements a ReAct (Reasoning + Acting) research agent that iteratively gathers web evidence before synthesizing a final answer. The WORKFLOW begins with a DecideAction CREATE FUNCTION that prompts an LLM to reason step-by-step about whether it has sufficient context to answer a question, outputting a structured YAML decision containing either action: search with a search_query or action: answer; this decision is stored in a shared @decision variable via GENERATE. A WHILE loop governs the research cycle: when the LLM signals action: search, a CALL to the web_search tool retrieves DuckDuckGo results and appends them to the @context accumulator, then control returns to DECIDE — this continues until the LLM judges itself ready or the max_iterations guard fires. When the exit condition is met, EVALUATE routes control to the AnswerQuestion CREATE FUNCTION, which performs a final GENERATE synthesizing all accumulated @context into a comprehensive answer stored in @answer. The RETURN is emitted with status=complete on a natural exit or status=max_iterations when the iteration cap is hit; no explicit EXCEPTION block is defined, though network failures from the LLM adapter would map to a NetworkError handler in SPL." --mode workflow

# Step 2 — run the generated workflow
spl3 run react_research.spl --adapter ollama -m llama3.2 \
    --param question="What are the latest advances in fusion energy?" \
    --param max_iterations=5

# Step 3 — compile to any target runtime
spl3 splc compile react_research.spl --lang python/pocketflow   # back to PocketFlow
spl3 splc compile react_research.spl --lang python/langgraph    # LangGraph equivalent
spl3 splc compile react_research.spl --lang go                  # Go runtime
```