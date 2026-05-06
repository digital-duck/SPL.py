## 0. High-level Description

This workflow implements a recursive map-reduce research agent using three logical functions wired into an iterative refinement loop. The `planner` function (CREATE FUNCTION) accepts a topic and optional gap-feedback and GENERATEs a YAML list of three diverse web-search queries; on the first pass it plans from the raw topic, and on subsequent passes it targets the specific gaps identified by the synthesizer. The `researcher` function is a batch variant that maps over the query list in parallel: for each query it performs a side-effect tool call (CALL search_web) to retrieve web snippets, then GENERATEs an LLM extraction of key facts, accumulating all fact-sets into a shared notes list. The `synthesizer` function receives the full topic, all accumulated notes, and the current loop count, and GENERATEs a YAML-structured response whose `action` field drives an EVALUATE branch: when `action` equals `research`, the workflow extracts a `feedback` field describing knowledge gaps, increments the loop counter, and returns the `research` sentinel to the WHILE-equivalent loop edge that routes back to the planner; when `action` equals `finalize`, it carries the completed markdown report and the workflow terminates via the `finalize` return path. A hard WHILE guard forces finalization after two research loops regardless of the synthesizer's judgment, preventing infinite iteration. The final RETURN delivers the markdown report written to a file via a CALL side-effect, with implicit metadata including loop count tracked in shared state; no explicit EXCEPTION handlers are present, though the loop-count ceiling acts as a structural safeguard.

## 1. Purpose

Automatically researches any user-supplied topic by iteratively planning web searches, extracting facts in parallel, and synthesizing a comprehensive markdown report — looping up to two times to fill identified knowledge gaps before writing the final report to disk.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW deep_research` | `create_deep_research_flow()` + `Flow(start=planner).run(shared)` | Shared state dict acts as the workflow's global scope |
| `CREATE FUNCTION planner` | `PlannerNode.exec()` | Prompt branches on whether `feedback` is empty or populated |
| `CREATE FUNCTION researcher` | `ResearcherNode.exec(query)` | BatchNode maps exec over each query independently |
| `CREATE FUNCTION synthesizer` | `SynthesizerNode.exec()` | Single LLM call returning YAML with `action` + payload field |
| `GENERATE planner(...) INTO @queries` | `call_llm(prompt)` → `yaml.safe_load(...)["queries"]` stored in `shared["current_queries"]` | YAML sentinel delimiters ` ```yaml ``` ` used for extraction |
| `CALL search_web(...) INTO @raw` | `search_web(query)` inside `ResearcherNode.exec` | Side-effect tool call; result fed immediately into next GENERATE |
| `GENERATE researcher(...) INTO @notes` | `call_llm(...)` → string stored via `shared["notes"].extend(exec_res)` | Batch results collected into accumulating list |
| `GENERATE synthesizer(...) INTO @decision` | `call_llm(prompt)` → `yaml.safe_load(...)` returning dict with `action` key | YAML sentinel ` ```yaml ``` ` used for extraction |
| `EVALUATE @decision WHEN contains('finalize')` | `if exec_res["action"] == "research": return "research"` else `return "finalize"` in `SynthesizerNode.post` | Return value is PocketFlow's action string routing the edge |
| `WHILE loop_count < 2 DO` | `if loops >= 2: return {"action": "finalize", ...}` at top of `SynthesizerNode.exec` | Guard forces exit; loop back-edge is `synthesizer - "research" >> planner` |
| `RETURN @report WITH status='complete'` | `shared["report"] = exec_res["content"]` + `Path(out).write_text(report)` | File write is the CALL side-effect; no explicit RETURN metadata beyond the report string |
| `EXCEPTION WHEN MaxIterations` | Hard `if loops >= 2` check before the EVALUATE branch | Structural guard, not a named handler |
| SPL `@var` shared variables | `shared` dict keys: `topic`, `feedback`, `current_queries`, `notes`, `loop_count`, `report` | All nodes read/write the same dict; equivalent to SPL workflow-scoped variables |

## 3. Logical Functions / Prompts

**`planner`**
- Role: Query generation — translates a research topic (or gap description) into three actionable web-search strings.
- Prompt conventions: Two modes controlled by the `feedback` parameter — cold start (`"Generate 3 diverse search queries to research: '{topic}'"`) vs. gap-fill (`"Gaps to fill: {feedback}\nGenerate 3 search queries to fill these gaps"`). Output must be strict YAML wrapped in ` ```yaml ``` ` fences with a single `queries` list key. No scoring or sentiment tokens.

**`researcher`** (batch variant)
- Role: Fact extraction — takes one search query, retrieves raw web snippets via `search_web`, then instructs the LLM to distill key facts relevant to that specific query.
- Prompt conventions: Two-part sequential call per item. First call is `search_web` (deterministic tool). Second call is `"Extract key facts relevant to this query. Be brief.\n\nQuery: {query}\nSearch result:\n{raw}"` — free-form text response, no structured output required. Result stored as `"Q: {query}\nFacts: {extracted}"` composite string.

**`synthesizer`**
- Role: Gap detection and report generation — evaluates accumulated notes for completeness and either identifies missing coverage (returning to the loop) or produces the final markdown report.
- Prompt conventions: Dual-branch YAML output using mutually exclusive schemas. Branch 1: `action: research` + `feedback: "<gap description>"`. Branch 2: `action: finalize` + `content: "<full markdown report>"`. Output wrapped in ` ```yaml ``` ` fences. When the loop counter reaches 2, the LLM is bypassed entirely and a forced-finalization prompt (`"Write a concise research report on '{topic}' using these notes"`) is called directly, returning `{"action": "finalize", "content": report}`.

## 4. Control Flow

```
START
  │
  ▼
GENERATE planner(topic, feedback="") INTO @queries          ← initial pass, no feedback
  │
  ▼
WHILE loop_count < 2 DO
  │
  ├── CALL search_web(@query) INTO @raw   ┐
  │   GENERATE researcher(@query, @raw)   │  (batched in parallel over @queries)
  │   INTO @note_set                      ┘
  │   ACCUMULATE @note_set INTO @notes
  │
  ├── GENERATE synthesizer(topic, @notes, loop_count) INTO @decision
  │
  └── EVALUATE @decision
        WHEN action == "research" THEN
          loop_count += 1
          @feedback ← @decision.feedback
          GENERATE planner(topic, @feedback) INTO @queries
          → loop back to WHILE top
        WHEN action == "finalize" THEN
          @report ← @decision.content
          → EXIT loop
END WHILE

(if loop_count >= 2 before EVALUATE: bypass LLM, force GENERATE finalization prompt)

CALL write_file(@report, path=out)
RETURN @report WITH status="complete", loop_count=loop_count
```

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile deep_research.spl --lang python/pocketflow
spl3 splc compile deep_research.spl --lang python/langgraph
spl3 splc compile deep_research.spl --lang go
```