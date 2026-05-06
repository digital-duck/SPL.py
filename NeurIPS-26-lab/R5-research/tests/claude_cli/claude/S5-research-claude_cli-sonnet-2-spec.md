## 0. High-level Description

This workflow implements a multi-iteration deep research pipeline with adaptive loop control and parallel information gathering. Seven `CREATE FUNCTION` prompts are defined: `planner` generates 3 specific search queries given the topic and prior feedback; `extract_query` extracts a single query string by position from the planner output; `extract_facts` summarises key facts from a search result; `accumulate_notes` merges existing notes with three new fact batches; `synthesizer` evaluates accumulated research and emits either `DECISION: finalize` (with a full report) or `DECISION: research` (with feedback for the next iteration); `extract_report` and `extract_feedback` extract the respective sections from the synthesizer output. The PocketFlow graph has two structural features that distinguish it from the linear recipes: (1) a `LoopCheckNode` that merges the SPL's outer WHILE condition (`@loop_count < 3`) with an inner `EVALUATE @loop_count WHEN contains("2")` shortcut, routing to `"done"` (post-loop write), `"max_loops"` (forced concise report at iteration 2), or `"continue"` (normal research path); (2) `ThreadPoolExecutor(max_workers=3)` inside `ExtractQueriesNode`, `SearchWebNode`, and `ExtractFactsNode` to implement `CALL PARALLEL`. The `ExtractFeedbackNode` also calls `planner` inline to avoid a separate node for the `GENERATE planner(...)` that follows the feedback extraction. The `search_web` tool is implemented as a live claude-CLI call instructed to search and summarise, rather than a stub. The workflow terminates by writing the report to `@out` (default `"report.txt"`) and returning `@report` with `status="complete"`.

---

## 1. Purpose

Produces a comprehensive research report on a given topic by iteratively planning queries, searching in parallel, extracting facts, accumulating notes, and asking a synthesizer LLM to finalize or continue — up to 3 iterations before forcing a concise report.

---

## 2. SPL ↔ Python — PocketFlow Construct Mapping

| SPL Construct | Python — PocketFlow Equivalent | Notes |
|---|---|---|
| `WORKFLOW deep_research` | `build_flow() → Flow(start=init)` | 13-node graph; `LoopCheckNode` back-edge creates the WHILE loop |
| `INPUT @topic TEXT, @out TEXT := "report.txt"` | `run_deep_research(topic, out="report.txt")` | `shared = {"topic": topic, "out": out}` |
| `OUTPUT @report TEXT` | `return shared.get("report", "")` | Caller gets string; `status`/`write_result` remain in `shared` |
| `@loop_count := 0; @feedback := ""; @notes := ""; @report := ""` | `InitNode.post()` calls `shared.setdefault(...)` for each variable | `setdefault` preserves any caller-supplied initial values |
| `GENERATE planner(@topic, @feedback) INTO @queries` | `PlannerNode.exec()` → `call_llm(PLANNER_PROMPT.format(...))` | First call is pre-loop; subsequent calls are inside `ExtractFeedbackNode` |
| `WHILE @loop_count < 3 DO` | `LoopCheckNode.post()` returning `"done"` / `"max_loops"` / `"continue"` | `"done"` edge is a safety net (unreachable in normal flow; see §4) |
| `EVALUATE @loop_count WHEN contains("2") THEN` | `if "2" in str(loop_count): return "max_loops"` in `LoopCheckNode.post()` | Fires when `loop_count == 2`; routes to `WriteConciseReportNode` |
| `GENERATE write_concise_report(@topic, @notes) INTO @report` | `WriteConciseReportNode.exec()` → `call_llm(WRITE_CONCISE_REPORT_PROMPT.format(...))` | Sets `shared["loop_count"] = 3`; routes directly to `WriteFileNode` |
| `GENERATE extract_query(@queries, N) INTO @queryN` (×3) | `ExtractQueriesNode.exec()` — 3-way `ThreadPoolExecutor` over positions 1, 2, 3 | Three sequential `GENERATE` calls parallelised as concurrent LLM calls |
| `CALL PARALLEL search_web(@queryN) INTO @resultN` (×3) | `SearchWebNode.exec()` — `ThreadPoolExecutor(max_workers=3)` mapping `search_web` | `search_web()` calls claude CLI with a "search and summarise" prompt |
| `CALL PARALLEL extract_facts(@queryN, @resultN) INTO @noteN` (×3) | `ExtractFactsNode.exec()` — `ThreadPoolExecutor(max_workers=3)` mapping `call_llm` | Parallelises 3 independent fact-extraction LLM calls |
| `GENERATE accumulate_notes(@notes, @note1, @note2, @note3) INTO @notes` | `AccumulateNotesNode.exec()` → `call_llm(ACCUMULATE_NOTES_PROMPT.format(...))` | Single LLM call merging previous notes + 3 new batches |
| `GENERATE synthesizer(@topic, @notes, @loop_count) INTO @decision` | `SynthesizerNode.exec()` → `call_llm(SYNTHESIZER_PROMPT.format(...))` | Emits `DECISION: finalize` or `DECISION: research` |
| `EVALUATE @decision WHEN contains("DECISION: finalize")` | `EvaluateDecisionNode.post()` — `"DECISION: finalize" in decision` | Routes to `"finalize"` or `"research"` action |
| `GENERATE extract_report(@decision) INTO @report; @loop_count := 3` | `ExtractReportNode.exec()` → LLM call; `.post()` sets `loop_count=3` | Routes directly to `WriteFileNode` (bypasses `LoopCheckNode`) |
| `GENERATE extract_feedback(@decision) INTO @feedback; @loop_count += 1; GENERATE planner(...)` | `ExtractFeedbackNode.exec()` — three sequential operations in one exec | `feedback` LLM call → increment → `planner` LLM call; result tuple pushed to `shared` in `post()` |
| `CALL write_file(@out, @report) INTO @write_result` | `WriteFileNode.exec()` — `open(path, "w").write(content)` | Returns `"written:<path>"` string stored in `shared["write_result"]` |
| `RETURN @report WITH status = "complete"` | `shared["status"]` set implicitly via `run_deep_research()` returning `shared["report"]` | No explicit `status` field in `WriteFileNode.post()` — caller infers success if report is non-empty |
| Adapter: `claude_cli`, model: `sonnet` | `subprocess.run(["claude", "-p", prompt, "--model", "claude-sonnet-4-6"], timeout=180)` | `call_llm` raises `RuntimeError` on non-zero exit |

---

## 3. Logical Functions / Prompts

### `planner`
- **Role:** Query generation. Given the topic and any prior feedback, generates exactly 3 diverse search queries in `QUERY_1: / QUERY_2: / QUERY_3:` format.

### `extract_query`
- **Role:** Query extractor. Given the full planner output and a position number (1–3), returns just the text after `QUERY_N: `.

### `extract_facts`
- **Role:** Fact summariser. Given a query and its search result, extracts key facts as a concise bullet-point list.

### `accumulate_notes`
- **Role:** Note merger. Combines existing notes with three new fact batches, removing duplicates and grouping related facts.

### `synthesizer`
- **Role:** Research evaluator. Reviews all accumulated notes and decides to `DECISION: finalize` (includes a full report) or `DECISION: research` (includes feedback for the next iteration).

### `extract_report` / `extract_feedback`
- **Role:** Output extractors. Parse the synthesizer's response to return only the content after `REPORT: ` or `FEEDBACK: ` respectively.

### `write_concise_report`
- **Role:** Fallback report generator. Called only when `loop_count == 2` (max-loop shortcut). Produces a concise report directly from accumulated notes without a synthesizer decision.

### `search_web` (tool call)
- **Role:** Live web search via claude CLI. Passes a "Search the web for: {query}" prompt and returns a detailed summary. **Not a stub** — makes a real LLM call.

---

## 4. Control Flow

```
INPUT @topic TEXT, @out TEXT := "report.txt"
@loop_count ← 0; @feedback ← ""; @notes ← ""; @report ← ""

GENERATE planner(@topic, "") INTO @queries                    [LLM]

── WHILE @loop_count < 3 ─────────────────────────────────────────────────
│  LoopCheckNode checks loop_count:
│    if >= 3      → "done"      >> WriteFileNode             (safety net)
│    if "2" in N  → "max_loops" >> WriteConciseReportNode
│                                      ↓ sets loop_count=3
│                               >> WriteFileNode  ──────────────────── ~
│    else         → "continue"
│
│  GENERATE extract_query(@queries, 1|2|3) INTO @q1,@q2,@q3  [LLM ×3 parallel]
│
│  CALL PARALLEL search_web(@q1), search_web(@q2), search_web(@q3)
│       → @result1, @result2, @result3                        [LLM ×3 parallel]
│
│  CALL PARALLEL extract_facts(@q1,@r1), ..., (@q3,@r3)
│       → @note1, @note2, @note3                             [LLM ×3 parallel]
│
│  GENERATE accumulate_notes(@notes, @note1, @note2, @note3)  [LLM]
│       → @notes
│
│  GENERATE synthesizer(@topic, @notes, @loop_count)          [LLM]
│       → @decision
│
│  EVALUATE @decision
│    WHEN contains("DECISION: finalize") THEN
│      GENERATE extract_report(@decision) → @report          [LLM]
│      @loop_count := 3
│      >> WriteFileNode  ────────────────────────────────────────────── ✓
│    ELSE
│      GENERATE extract_feedback(@decision) → @feedback      [LLM]
│      @loop_count += 1
│      GENERATE planner(@topic, @feedback) → @queries        [LLM]
│      → LoopCheckNode (back-edge)
│  END
└──────────────────────────────────────────────────────────────────────────

CALL write_file(@out, @report) INTO @write_result
RETURN @report WITH status = "complete"
```

**Loop-count reachability:** `ExtractFeedbackNode` increments `loop_count` from 0→1 or 1→2. On the pass through `LoopCheckNode` with `loop_count=2`, `"max_loops"` fires. Therefore `LoopCheckNode`'s `"done"` (≥3) edge is a safe unreachable guard — `loop_count` reaches 3 only inside `ExtractReportNode` or `WriteConciseReportNode`, which route directly to `WriteFileNode`.

**Observed run (2026-05-04):** Topic `"quantum computing applications"` → comprehensive 6-section report covering hardware landscape, PQC standards, drug discovery, financial optimization, and cross-domain assessment. Report written to `report.txt`.

---

## 5. How to Regenerate as SPL

```bash
# Step 1 — regenerate SPL from this spec
spl3 text2spl --description "$(sed -n '/^## 0\./,/^---/p' S5-research-claude_cli-sonnet-2-spec.md)" \
    --mode workflow --adapter claude_cli

# Step 2 — run
spl3 run deep_research.spl --adapter claude_cli \
    --param topic="quantum computing applications" \
    --param out="report.txt"

# Step 3 — recompile to any target
spl3 splc compile deep_research.spl --lang python/pocketflow --llm \
    --adapter claude_cli --model sonnet
spl3 splc compile deep_research.spl --lang python/langgraph
spl3 splc compile deep_research.spl --lang go
```
