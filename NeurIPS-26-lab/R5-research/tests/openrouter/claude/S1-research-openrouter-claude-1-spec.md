## 0. High-level Description

This workflow implements a recursive map-reduce deep research pipeline with iterative refinement, orchestrated across three logical functions: a Planner, a Researcher, and a Synthesizer. The Planner function uses a structured YAML-output prompt to generate exactly three diverse search queries for a given topic, incorporating gap-filling feedback from prior iterations when available. The Researcher function operates as a batch processor — executing one web search and one LLM fact-extraction call per query in parallel — accumulating notes into shared state across all iterations. The Synthesizer function then evaluates the accumulated notes using an EVALUATE-style branch: if the LLM judges the information insufficient and the iteration count is below two, it emits a `"research"` action token that drives a WHILE-like loop back to the Planner with targeted feedback; once sufficient or after two loops, it emits a `"finalize"` action token and generates the complete markdown report inline. The workflow uses a single LLM backend (auto-detected between GPT-4o and Gemini 2.0 Flash based on available API keys) for all generation steps, and a DuckDuckGo search tool call for web retrieval. Upon finalization, a CALL-equivalent side-effect writes the report to a user-specified output file path, and the workflow RETURNS with the completed report stored in shared state.

---

## 1. Purpose

This workflow enables end users to automatically produce a comprehensive, iteratively refined research report on any topic by orchestrating multi-round web search, fact extraction, and gap-aware synthesis through a loop-controlled LLM pipeline.

---

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW deep_research` | `create_deep_research_flow()` + `Flow(start=planner)` in `flow.py` | Declares the named multi-step orchestration pipeline |
| `CREATE FUNCTION planner_prompt` | `PlannerNode.exec()` prompt string with `{topic}` and `{feedback}` slots | Branches on whether `feedback` is empty to alter the instruction prefix |
| `CREATE FUNCTION researcher_prompt` | `ResearcherNode.exec()` fact-extraction prompt with `{query}` and `{raw}` slots | Called once per query inside the batch; always brief-extraction role |
| `CREATE FUNCTION synthesizer_prompt` | `SynthesizerNode.exec()` sufficiency-check prompt with `{topic}` and `{notes_text}` slots | Omitted when `loops >= 2`; replaced by a direct finalization prompt |
| `GENERATE planner_prompt(...) INTO @current_queries` | `call_llm(prompt)` → `yaml.safe_load(...)["queries"]` → `shared["current_queries"]` | YAML sentinel parsing extracts the list |
| `GENERATE researcher_prompt(...) INTO @notes` | `call_llm(...)` → `shared["notes"].extend(exec_res)` | BatchNode maps across `@current_queries`; results accumulated |
| `GENERATE synthesizer_prompt(...) INTO @synthesis` | `call_llm(prompt)` → `yaml.safe_load(...)` → `exec_res` dict | Returns `action` + `feedback` or `action` + `content` |
| `CALL search_web(...) INTO @raw_results` | `search_web(query)` via `DDGS().text(...)` | Side-effect tool call; not an LLM generation |
| `CALL write_file(...) INTO @_` | `Path(out).write_text(report)` in `main.py` | Side-effect file write after workflow completes |
| `WHILE loop_count < 2 AND action == "research"` | `synthesizer - "research" >> planner` edge + `loops >= 2` guard in `SynthesizerNode.exec()` | Loop back to Planner only when gaps found and under iteration cap |
| `EVALUATE @synthesis WHEN contains("research") THEN ... ELSE ...` | `if exec_res["action"] == "research": return "research"` else `return "finalize"` in `SynthesizerNode.post()` | Drives the real branch: loop vs. termination |
| `RETURN @report WITH status="finalize"` | `shared["report"] = exec_res["content"]`; `return "finalize"` | Non-trivial action token that terminates the loop and signals completion |
| `RETURN WITH status="research"` | `return "research"` in `SynthesizerNode.post()` | Non-trivial action token that re-enters the Planner with updated feedback |
| Shared state (`@vars`) | `shared` dict passed through all nodes | Holds `topic`, `feedback`, `current_queries`, `notes`, `loop_count`, `report` |
| `EXCEPTION WHEN ValueError` | `raise ValueError("Set OPENAI_API_KEY or GEMINI_API_KEY")` in `call_llm` | Raised when neither API key is present; no explicit handler in flow nodes |

---

## 3. Logical Functions / Prompts

### 3.1 `planner_prompt` — PlannerNode

- **Role:** Generates three diverse search queries to drive the next research round. On the first iteration it receives only the topic; on subsequent iterations it also receives the synthesizer's gap-filling feedback, allowing targeted query refinement.
- **Key prompt conventions:**
  - Conditional instruction prefix: plain query generation vs. gap-filling mode selected in Python before the prompt is assembled.
  - Output format enforced by the sentinel `Output ONLY yaml:` followed by a fenced YAML block.
  - Parsed via `resp.split("```yaml")[1].split("```")[0].strip()` → `yaml.safe_load(...)["queries"]`.
  - Always produces exactly three string queries.

### 3.2 `researcher_fact_extraction_prompt` — ResearcherNode (batch)

- **Role:** For each query, distills raw DuckDuckGo search results into concise, relevant facts. Operates as a map step over `@current_queries`.
- **Key prompt conventions:**
  - Instruction: `"Extract key facts relevant to this query. Be brief."` — brevity constraint keeps notes compact for downstream synthesis.
  - Inputs are `{query}` and `{raw}` (the raw search snippet text).
  - Output is free-form prose; no YAML sentinel required.
  - Each result is stored as `"Q: {query}\nFacts: {extracted}"` and appended to `shared["notes"]`.

### 3.3 `synthesizer_sufficiency_prompt` — SynthesizerNode (conditional path)

- **Role:** Acts as the EVALUATE gate — determines whether accumulated notes are sufficient for a comprehensive report or whether another research loop is needed.
- **Key prompt conventions:**
  - Skipped entirely when `loop_count >= 2`; a direct finalization prompt is used instead (see 3.4).
  - Dual-branch YAML output with sentinel `Output ONLY yaml:`.
  - Branch A (insufficient): `action: research` + `feedback: "<what's missing>"` — feedback string is stored in `shared["feedback"]` and forwarded to the next Planner call.
  - Branch B (sufficient): `action: finalize` + `content: "<full markdown report>"` — report written directly into the YAML response.
  - Parsed identically to the Planner: split on fenced YAML block → `yaml.safe_load(...)`.

### 3.4 `synthesizer_finalization_prompt` — SynthesizerNode (forced path)

- **Role:** Unconditionally generates the final report when the loop cap (`loops >= 2`) is reached, bypassing the sufficiency evaluation entirely.
- **Key prompt conventions:**
  - Instruction: `"Write a concise research report on '{topic}' using these notes:"` — no YAML output format; expects plain markdown prose.
  - Notes are joined with `"\n---\n"` as a section separator.
  - Returns `{"action": "finalize", "content": report}` constructed in Python (not parsed from LLM YAML).

---

## 4. Control Flow

**Initialization:** The workflow starts at `PlannerNode` with `shared = {"topic": <user_input>}`. No feedback or notes exist yet.

**Round structure (WHILE loop_count < 2 AND gaps_remain):**

1. **PlannerNode** reads `topic` and optional `feedback` from shared state, calls the LLM to produce three queries, and writes them to `shared["current_queries"]`.

2. **ResearcherNode (batch)** iterates over `shared["current_queries"]`, calling `search_web` (CALL) and then the LLM fact-extraction function (GENERATE) for each query. All results are appended to `shared["notes"]`.

3. **SynthesizerNode** reads `topic`, `notes`, and `loop_count`. It branches:
   - If `loop_count >= 2`: skips the EVALUATE prompt entirely, calls the finalization LLM directly, sets `shared["report"]`, and RETURNS WITH `status="finalize"` — terminating the loop.
   - Otherwise: runs the sufficiency EVALUATE prompt. If the LLM returns `action: research`, increments `loop_count`, stores `feedback`, and RETURNS WITH `status="research"` — routing back to PlannerNode for another round.
   - If the LLM returns `action: finalize`, stores the report in `shared["report"]` and RETURNS WITH `status="finalize"` — terminating early.

**Termination:** On `status="finalize"`, no outgoing edge is followed. Control returns to `main.py`, which reads `shared["report"]`, prints it, and writes it to the output file via a CALL side-effect.

**Maximum iterations:** Hard-capped at 2 full Planner→Researcher→Synthesizer rounds (enforced by the `loops >= 2` guard), plus one possible early exit if the Synthesizer judges notes sufficient after round 1.

---

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This workflow implements a recursive map-reduce deep \
research pipeline with iterative refinement, orchestrated across three logical \
functions: a Planner, a Researcher, and a Synthesizer. The Planner function uses a \
structured YAML-output prompt to generate exactly three diverse search queries for a \
given topic, incorporating gap-filling feedback from prior iterations when available. \
The Researcher function operates as a batch processor — executing one web search and \
one LLM fact-extraction call per query in parallel — accumulating notes into shared \
state across all iterations. The Synthesizer function then evaluates the accumulated \
notes using an EVALUATE-style branch: if the LLM judges the information insufficient \
and the iteration count is below two, it emits a 'research' action token that drives \
a WHILE-like loop back to the Planner with targeted feedback; once sufficient or after \
two loops, it emits a 'finalize' action token and generates the complete markdown \
report inline. The workflow uses a single LLM backend (auto-detected between GPT-4o \
and Gemini 2.0 Flash based on available API keys) for all generation steps, and a \
DuckDuckGo search tool call for web retrieval. Upon finalization, a CALL-equivalent \
side-effect writes the report to a user-specified output file path, and the workflow \
RETURNS with the completed report stored in shared state." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile deep_research.spl --lang python/pocketflow
spl3 splc compile deep_research.spl --lang python/langgraph
spl3 splc compile deep_research.spl --lang go
```