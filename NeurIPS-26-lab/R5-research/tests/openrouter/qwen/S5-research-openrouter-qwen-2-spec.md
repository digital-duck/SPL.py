## 0. High-level Description
This workflow implements an iterative research-and-synthesis pipeline orchestrated via a structured `WHILE` loop that executes exactly two research cycles. It begins by invoking a `CREATE FUNCTION` for query planning to generate targeted search prompts, followed by a `GENERATE` call to an OpenRouter-hosted Qwen model. The system then performs a side-effect `CALL` to a web search tool, feeding the raw results into a second `GENERATE` function that extracts and consolidates factual notes into shared memory. After the loop condition evaluates to false, a final `GENERATE` step synthesizes the aggregated findings into a comprehensive deliverable using a dedicated assessment prompt, which is immediately persisted to disk via a second side-effect `CALL`. The pipeline incorporates robust exception handling for network or API failures by gracefully falling back to deterministic mock outputs, and concludes by `RETURN`ing the finalized report with an explicit completion status. Multi-step state accumulation occurs within a shared variable context, ensuring that research findings compound across iterations before final synthesis.

## 1. Purpose
This implementation automates a multi-iteration web research and fact-extraction pipeline to generate, consolidate, and persist a structured final report on a user-specified topic.

## 2. SPL ↔ Python Construct Mapping
| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW` | `S3ResearchOpenrouterQwenFlow` class + `run()` method | Encapsulates orchestration lifecycle and mutable `self.state` |
| `CREATE FUNCTION` | `_plan_queries_prompt`, `_extract_facts_prompt`, `_assess_and_report_prompt` | Pure template builders that inject `{param}` slots into fixed system prompts |
| `GENERATE` | `_llm_generate(prompt)` | Wraps OpenRouter HTTP POST (Qwen model) with temperature `0.7` |
| `CALL` (tool) | `_search_web()`, `_write_file()` | External I/O operations for DuckDuckGo scraping and filesystem persistence |
| `WHILE` | `while self.state["loop_count"] < 2 and self.state["iteration"] < 3:` | Drives the bounded research loop with dual counter safeguards |
| Shared State (`@var`) | `self.state` dict | Acts as workflow memory (`@topic`, `@notes`, `@report`, etc.) across steps |
| `EXCEPTION` | `try...except` in `_llm_generate()` | Catches API/network errors and safely routes to deterministic mock fallbacks |
| `RETURN` | `return self.state["report"]` | Terminates the workflow and delivers the synthesized artifact with a logged `status = "complete"` |

## 3. Logical Functions / Prompts
**`plan_queries`**
- **Role:** Initiates the research phase by generating targeted, high-yield search strings for a given topic.
- **Key prompt conventions:** Instructs the LLM to act as a research planner, mandates exactly 3 queries, and enforces a strict line-by-line `QUERY: ` prefix for reliable downstream regex extraction.

**`extract_facts`**
- **Role:** Distills raw, unstructured web search snippets into structured, high-signal knowledge.
- **Key prompt conventions:** Directs the LLM to filter noise, output only the most critical findings, and format them as a concise bullet-point list for clean state accumulation.

**`assess_and_report`**
- **Role:** Synthesizes all accumulated iteration notes into a polished, actionable final deliverable.
- **Key prompt conventions:** Commands the LLM to organize aggregated data logically, eliminate redundancy, ensure clarity, and emphasize actionable takeaways without requiring additional formatting constraints.

## 4. Control Flow
The workflow initializes by binding the user-provided `@topic` to shared state and zeroing iteration counters. It immediately enters a `WHILE` loop governed by the compound condition `@loop_count < 2 AND @iteration < 3`, guaranteeing exactly two research passes. During each iteration, the system chains a `plan_queries` generation, a web search `CALL`, and an `extract_facts` generation, appending the distilled findings to the `@notes` accumulator. Once the loop condition evaluates to false, execution exits the iterative phase and triggers a single terminal `GENERATE` call using `assess_and_report`. The resulting `@report` is routed to a `CALL` for disk persistence (`"report.txt"`), after which the workflow terminates by `RETURN`ing the complete string payload to the host process with `status="complete"`.

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```