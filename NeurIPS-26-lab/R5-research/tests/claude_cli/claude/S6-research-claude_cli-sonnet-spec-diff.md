# File Comparison Report

**Files Compared:**
- File 1: `S1-research-claude_cli-sonnet-1-spec.md` (.md)
- File 2: `S5-research-claude_cli-sonnet-2-spec.md` (.md)
- **Timestamp:** 2026-05-04 09:41:28
- **Active Modes:** llm, git-diff

---
## LLM Semantic Analysis

**Adapter:** claude_cli
**Model:** claude-opus-4-6

## Summary

Both files specify an iterative deep-research workflow that plans queries, searches the web in parallel, extracts facts, and synthesizes a report — looping until the synthesizer finalizes or a hard cap is reached. **File 2 (S5) is the stronger spec overall.** It describes a more decomposed, production-grade architecture (13 nodes, 7 named functions) with richer SPL mapping detail, explicit reachability analysis, and observed-run evidence. File 1 (S1) is cleaner and more concise but papers over implementation details that matter for faithful SPL regeneration.

---

## Content Analysis

### File 1 Strengths

- **Readability.** The monolithic Section 0 paragraph, while dense, conveys the entire workflow in one continuous narrative. A reader can grasp the full design without jumping between sections.
- **Cleaner control-flow diagram.** The Section 4 ASCII diagram is minimal and easy to follow — it reads almost like pseudocode SPL already.
- **Tighter function count.** Three logical functions (`planner`, `researcher`, `synthesizer`) map directly to the three conceptual roles. There is no extraction boilerplate to reason about.
- **Explicit batch semantics.** The `researcher` is explicitly labeled a "batch variant" with `BatchNode` semantics, making the parallelism strategy unambiguous.
- **Simpler loop guard.** `loop_count < 2` with a hard bypass before EVALUATE is easy to verify correct.

### File 2 Strengths

- **Granular function decomposition.** Seven named functions (`planner`, `extract_query`, `extract_facts`, `accumulate_notes`, `synthesizer`, `extract_report`, `extract_feedback`) plus a `write_concise_report` fallback — each maps to a distinct LLM call, making the spec-to-code correspondence 1:1.
- **Explicit parallelism mechanism.** `ThreadPoolExecutor(max_workers=3)` is named for three separate parallel stages (query extraction, search, fact extraction), not just a vague "batch" label.
- **Loop reachability analysis.** Section 4 includes a paragraph proving that the `"done"` edge is unreachable under normal flow — a formal-methods-flavored detail that builds confidence in correctness.
- **Observed run evidence.** The spec records an actual execution date (2026-05-04) and topic, grounding the spec in empirical validation rather than pure design intent.
- **Richer SPL mapping table.** 17 rows vs. 12, covering `INPUT`/`OUTPUT` declarations, `setdefault` initialization semantics, adapter/model specifics, and the `WriteConciseReportNode` forced-finalization path.
- **Adapter specificity.** Explicitly records `claude_cli` adapter with `subprocess.run(["claude", ...])` invocation and 180s timeout — critical for faithful regeneration.
- **Section separators and sub-headers.** Horizontal rules and `###` sub-headers in Section 3 improve scannability.

### Common Elements

- Both follow the same 6-section structure (§0–§5) with identical section names.
- Both model the same conceptual pipeline: plan → search → extract → accumulate → synthesize → loop-or-finalize → write file.
- Both use YAML or structured-text output from LLM calls to drive EVALUATE branching.
- Both map PocketFlow's `shared` dict to SPL `@var` workflow-scoped variables.
- Both terminate with a file-write side-effect and `RETURN @report WITH status="complete"`.
- Both include a `text2spl` regeneration command in Section 5.

---

## Detailed Comparison

### Structure & Organization

| Aspect | File 1 (S1) | File 2 (S5) |
|---|---|---|
| Section 0 length | ~220 words, single paragraph | ~250 words, single paragraph |
| Section dividers | None (bare `##` headers) | `---` horizontal rules between sections |
| Section 3 layout | 3 functions, prose paragraphs | 8 functions, `###` sub-headers with role/description |
| Section 4 diagram | ~20 lines, clean pseudocode | ~35 lines, annotated with `[LLM]`/`[LLM ×3 parallel]` tags |
| Section 5 | 3 commands, generic targets | 3 steps with concrete topic param and `--llm` flag |

File 2 is better organized for reference use. The `###` sub-headers in Section 3 and the `[LLM ×N]` annotations in Section 4 let a reader locate information without re-reading paragraphs. File 1 is more compact, which suits a quick read but hurts as a reference document.

### Logic & Completeness

**Loop semantics.** File 1 allows **2 research iterations** (`loop_count < 2`). File 2 allows **up to 3** (`loop_count < 3`), with a `max_loops` shortcut at `loop_count == 2` that forces a concise report. This means:

| | File 1 | File 2 |
|---|---|---|
| Max research passes | 2 | 2 (3rd iteration replaced by concise-report shortcut) |
| Forced finalization | Hard `if loops >= 2` before LLM call | `LoopCheckNode` routing to `WriteConciseReportNode` |
| Forced-finalization prompt | Separate finalization prompt, still through synthesizer-like path | Dedicated `write_concise_report` function with its own prompt |

File 2's three-way routing (`done` / `max_loops` / `continue`) is more complex but also more explicit about what happens at each boundary. File 1 collapses the guard into a pre-EVALUATE bypass, which is simpler but conflates two different concerns (loop ceiling vs. normal finalization).

**Parallelism granularity.** File 1 treats the entire researcher as a single `BatchNode` — one parallel stage. File 2 decomposes into three separate parallel stages (extract queries, search, extract facts), each with its own `ThreadPoolExecutor`. File 2 is more faithful to the actual Python implementation and produces a more precise SPL mapping.

**Error handling.** Neither spec defines explicit `EXCEPTION` handlers. File 1 notes the loop ceiling as a "structural safeguard." File 2 notes `RuntimeError` on non-zero CLI exit in the adapter row but doesn't map it to an SPL exception. Both are incomplete here, but File 2 at least surfaces the runtime failure mode.

**Variable initialization.** File 2 explicitly maps `@loop_count := 0; @feedback := ""; @notes := ""; @report := ""` to `InitNode.post()` with `setdefault` semantics. File 1 leaves initialization implicit. For SPL regeneration, File 2's explicitness is important — SPL requires declared variables.

### Quality & Sophistication

**Spec-to-code fidelity.** File 2 achieves near-1:1 correspondence between spec rows and Python nodes/functions. Every LLM call is named and accounted for. File 1 abstracts away intermediate extraction steps (e.g., there's no `extract_query` or `extract_report` equivalent — these are folded into the parent function descriptions). This makes File 1 cleaner to read but less faithful as a reverse-engineering artifact.

**Reachability reasoning.** File 2's loop-count reachability paragraph is a standout quality marker. It demonstrates that the spec author verified the control-flow graph's edge coverage, not just described it. File 1 has no equivalent analysis.

**Empirical grounding.** File 2 records an observed run with a specific topic and output description. This serves as a built-in acceptance test. File 1 is purely prescriptive.

**Regeneration commands.** File 2's Section 5 includes `--adapter claude_cli`, a concrete `--param topic=...`, and `--llm` flag on the compile step. File 1's commands are generic placeholders. File 2's are copy-pasteable.

### Syntax & Technical Accuracy

**SPL construct accuracy.** Both use SPL constructs correctly (`WORKFLOW`, `CREATE FUNCTION`, `GENERATE ... INTO`, `EVALUATE ... WHEN`, `WHILE ... DO`, `CALL`, `RETURN`). File 2 adds `INPUT`/`OUTPUT` declarations, which are part of the SPL spec but missing from File 1.

**YAML vs. text sentinel.** File 1 uses ` ```yaml ``` ` fenced YAML for structured output. File 2 uses `DECISION: finalize` / `QUERY_N:` text sentinels parsed by downstream LLM calls. File 2's approach is more robust in practice (LLMs more reliably produce prefixed text than valid YAML), but File 1's YAML approach is more idiomatic for SPL's structured-output conventions.

**Table formatting.** Both tables render correctly. File 2's table has more rows and wider cells, which may wrap awkwardly in narrow viewports but carries more information per row.

**Minor issues:**
- File 1, Section 2: `"Q: {query}\nFacts: {extracted}"` composite string format is described but not mapped to an SPL construct (it's an implementation detail that leaks into the spec).
- File 2, Section 2: `"2" in str(loop_count)` is a code smell (string containment check on an integer) — the spec faithfully captures this wart from the Python code, which is honest but worth flagging.

---

## Recommendations

### 1. Best Choice

**File 2 (S5)** is the better spec for any downstream use — regeneration, review, or onboarding. Its granular function decomposition, explicit variable initialization, reachability analysis, and observed-run evidence make it a more complete and trustworthy artifact. The additional complexity is justified by the additional precision.

### 2. Improvements for File 1

- **Add `INPUT`/`OUTPUT` declarations** to the mapping table — these are required for SPL regeneration.
- **Decompose the `researcher` batch node** into separate query-extraction, search, and fact-extraction stages to match the actual parallelism boundaries.
- **Add variable initialization** either as a dedicated mapping row or in the control-flow diagram preamble.
- **Include adapter/model info** in the mapping table (at minimum, which adapter and model the spec was derived from).
- **Add a reachability note** for the loop guard to confirm the exit condition is sound.
- **Make Section 5 commands concrete** with a sample topic and adapter flag.

### 3. Hybrid Approach

Take File 2's structure and content as the base, then:

1. **Adopt File 1's cleaner control-flow diagram style** — strip the `[LLM ×3 parallel]` annotations into a legend below the diagram rather than inline, reducing visual noise.
2. **Keep File 2's 7-function decomposition** but add a "Logical Grouping" column in Section 3 that maps functions back to File 1's three conceptual roles (planner, researcher, synthesizer) for quick orientation.
3. **Retain File 2's reachability analysis and observed-run note** — these are high-value additions with no readability cost.
4. **Use File 1's YAML-based structured output convention** where possible, since it aligns better with SPL's `GENERATE ... INTO` semantics for structured data.

---

## Scoring

| Dimension | File 1 (S1) | File 2 (S5) | Notes |
|---|---|---|---|
| **Structure** | 7/10 | 9/10 | F2's sub-headers, separators, and annotations improve navigability |
| **Logic** | 6/10 | 8/10 | F2's three-way loop routing, reachability proof, and explicit init are more rigorous |
| **Quality** | 6/10 | 9/10 | F2's granularity, empirical grounding, and adapter specificity set it apart |
| **Overall** | 6/10 | 9/10 | F2 is the clear winner for any use beyond casual reading |

**Bottom line:** File 1 is a reasonable first-pass spec — concise and readable. File 2 is a production-grade specification that could drive automated regeneration with high fidelity. The 3-point gap is almost entirely about completeness and precision, not correctness — File 1 isn't wrong, it's just underspecified.
---

## Mechanical Diff (Unified Style)

```diff
--- a/S1-research-claude_cli-sonnet-1-spec.md
+++ b/S5-research-claude_cli-sonnet-2-spec.md
@@ -1,86 +1,137 @@
 ## 0. High-level Description

 

-This workflow implements a recursive map-reduce research agent using three logical functions wired into an iterative refinement loop. The `planner` function (CREATE FUNCTION) accepts a topic and optional gap-feedback and GENERATEs a YAML list of three diverse web-search queries; on the first pass it plans from the raw topic, and on subsequent passes it targets the specific gaps identified by the synthesizer. The `researcher` function is a batch variant that maps over the query list in parallel: for each query it performs a side-effect tool call (CALL search_web) to retrieve web snippets, then GENERATEs an LLM extraction of key facts, accumulating all fact-sets into a shared notes list. The `synthesizer` function receives the full topic, all accumulated notes, and the current loop count, and GENERATEs a YAML-structured response whose `action` field drives an EVALUATE branch: when `action` equals `research`, the workflow extracts a `feedback` field describing knowledge gaps, increments the loop counter, and returns the `research` sentinel to the WHILE-equivalent loop edge that routes back to the planner; when `action` equals `finalize`, it carries the completed markdown report and the workflow terminates via the `finalize` return path. A hard WHILE guard forces finalization after two research loops regardless of the synthesizer's judgment, preventing infinite iteration. The final RETURN delivers the markdown report written to a file via a CALL side-effect, with implicit metadata including loop count tracked in shared state; no explicit EXCEPTION handlers are present, though the loop-count ceiling acts as a structural safeguard.

+This workflow implements a multi-iteration deep research pipeline with adaptive loop control and parallel information gathering. Seven `CREATE FUNCTION` prompts are defined: `planner` generates 3 specific search queries given the topic and prior feedback; `extract_query` extracts a single query string by position from the planner output; `extract_facts` summarises key facts from a search result; `accumulate_notes` merges existing notes with three new fact batches; `synthesizer` evaluates accumulated research and emits either `DECISION: finalize` (with a full report) or `DECISION: research` (with feedback for the next iteration); `extract_report` and `extract_feedback` extract the respective sections from the synthesizer output. The PocketFlow graph has two structural features that distinguish it from the linear recipes: (1) a `LoopCheckNode` that merges the SPL's outer WHILE condition (`@loop_count < 3`) with an inner `EVALUATE @loop_count WHEN contains("2")` shortcut, routing to `"done"` (post-loop write), `"max_loops"` (forced concise report at iteration 2), or `"continue"` (normal research path); (2) `ThreadPoolExecutor(max_workers=3)` inside `ExtractQueriesNode`, `SearchWebNode`, and `ExtractFactsNode` to implement `CALL PARALLEL`. The `ExtractFeedbackNode` also calls `planner` inline to avoid a separate node for the `GENERATE planner(...)` that follows the feedback extraction. The `search_web` tool is implemented as a live claude-CLI call instructed to search and summarise, rather than a stub. The workflow terminates by writing the report to `@out` (default `"report.txt"`) and returning `@report` with `status="complete"`.

+

+---

 

 ## 1. Purpose

 

-Automatically researches any user-supplied topic by iteratively planning web searches, extracting facts in parallel, and synthesizing a comprehensive markdown report — looping up to two times to fill identified knowledge gaps before writing the final report to disk.

+Produces a comprehensive research report on a given topic by iteratively planning queries, searching in parallel, extracting facts, accumulating notes, and asking a synthesizer LLM to finalize or continue — up to 3 iterations before forcing a concise report.

 

-## 2. SPL ↔ Python Construct Mapping

+---

 

-| SPL Construct | Python Equivalent | Notes |

+## 2. SPL ↔ Python — PocketFlow Construct Mapping

+

+| SPL Construct | Python — PocketFlow Equivalent | Notes |

 |---|---|---|

-| `WORKFLOW deep_research` | `create_deep_research_flow()` + `Flow(start=planner).run(shared)` | Shared state dict acts as the workflow's global scope |

-| `CREATE FUNCTION planner` | `PlannerNode.exec()` | Prompt branches on whether `feedback` is empty or populated |

-| `CREATE FUNCTION researcher` | `ResearcherNode.exec(query)` | BatchNode maps exec over each query independently |

-| `CREATE FUNCTION synthesizer` | `SynthesizerNode.exec()` | Single LLM call returning YAML with `action` + payload field |

-| `GENERATE planner(...) INTO @queries` | `call_llm(prompt)` → `yaml.safe_load(...)["queries"]` stored in `shared["current_queries"]` | YAML sentinel delimiters ` ```yaml ``` ` used for extraction |

-| `CALL search_web(...) INTO @raw` | `search_web(query)` inside `ResearcherNode.exec` | Side-effect tool call; result fed immediately into next GENERATE |

-| `GENERATE researcher(...) INTO @notes` | `call_llm(...)` → string stored via `shared["notes"].extend(exec_res)` | Batch results collected into accumulating list |

-| `GENERATE synthesizer(...) INTO @decision` | `call_llm(prompt)` → `yaml.safe_load(...)` returning dict with `action` key | YAML sentinel ` ```yaml ``` ` used for extraction |

-| `EVALUATE @decision WHEN contains('finalize')` | `if exec_res["action"] == "research": return "research"` else `return "finalize"` in `SynthesizerNode.post` | Return value is PocketFlow's action string routing the edge |

-| `WHILE loop_count < 2 DO` | `if loops >= 2: return {"action": "finalize", ...}` at top of `SynthesizerNode.exec` | Guard forces exit; loop back-edge is `synthesizer - "research" >> planner` |

-| `RETURN @report WITH status='complete'` | `shared["report"] = exec_res["content"]` + `Path(out).write_text(report)` | File write is the CALL side-effect; no explicit RETURN metadata beyond the report string |

-| `EXCEPTION WHEN MaxIterations` | Hard `if loops >= 2` check before the EVALUATE branch | Structural guard, not a named handler |

-| SPL `@var` shared variables | `shared` dict keys: `topic`, `feedback`, `current_queries`, `notes`, `loop_count`, `report` | All nodes read/write the same dict; equivalent to SPL workflow-scoped variables |

+| `WORKFLOW deep_research` | `build_flow() → Flow(start=init)` | 13-node graph; `LoopCheckNode` back-edge creates the WHILE loop |

+| `INPUT @topic TEXT, @out TEXT := "report.txt"` | `run_deep_research(topic, out="report.txt")` | `shared = {"topic": topic, "out": out}` |

+| `OUTPUT @report TEXT` | `return shared.get("report", "")` | Caller gets string; `status`/`write_result` remain in `shared` |

+| `@loop_count := 0; @feedback := ""; @notes := ""; @report := ""` | `InitNode.post()` calls `shared.setdefault(...)` for each variable | `setdefault` preserves any caller-supplied initial values |

+| `GENERATE planner(@topic, @feedback) INTO @queries` | `PlannerNode.exec()` → `call_llm(PLANNER_PROMPT.format(...))` | First call is pre-loop; subsequent calls are inside `ExtractFeedbackNode` |

+| `WHILE @loop_count < 3 DO` | `LoopCheckNode.post()` returning `"done"` / `"max_loops"` / `"continue"` | `"done"` edge is a safety net (unreachable in normal flow; see §4) |

+| `EVALUATE @loop_count WHEN contains("2") THEN` | `if "2" in str(loop_count): return "max_loops"` in `LoopCheckNode.post()` | Fires when `loop_count == 2`; routes to `WriteConciseReportNode` |

+| `GENERATE write_concise_report(@topic, @notes) INTO @report` | `WriteConciseReportNode.exec()` → `call_llm(WRITE_CONCISE_REPORT_PROMPT.format(...))` | Sets `shared["loop_count"] = 3`; routes directly to `WriteFileNode` |

+| `GENERATE extract_query(@queries, N) INTO @queryN` (×3) | `ExtractQueriesNode.exec()` — 3-way `ThreadPoolExecutor` over positions 1, 2, 3 | Three sequential `GENERATE` calls parallelised as concurrent LLM calls |

+| `CALL PARALLEL search_web(@queryN) INTO @resultN` (×3) | `SearchWebNode.exec()` — `ThreadPoolExecutor(max_workers=3)` mapping `search_web` | `search_web()` calls claude CLI with a "search and summarise" prompt |

+| `CALL PARALLEL extract_facts(@queryN, @resultN) INTO @noteN` (×3) | `ExtractFactsNode.exec()` — `ThreadPoolExecutor(max_workers=3)` mapping `call_llm` | Parallelises 3 independent fact-extraction LLM calls |

+| `GENERATE accumulate_notes(@notes, @note1, @note2, @note3) INTO @notes` | `AccumulateNotesNode.exec()` → `call_llm(ACCUMULATE_NOTES_PROMPT.format(...))` | Single LLM call merging previous notes + 3 new batches |

+| `GENERATE synthesizer(@topic, @notes, @loop_count) INTO @decision` | `SynthesizerNode.exec()` → `call_llm(SYNTHESIZER_PROMPT.format(...))` | Emits `DECISION: finalize` or `DECISION: research` |

+| `EVALUATE @decision WHEN contains("DECISION: finalize")` | `EvaluateDecisionNode.post()` — `"DECISION: finalize" in decision` | Routes to `"finalize"` or `"research"` action |

+| `GENERATE extract_report(@decision) INTO @report; @loop_count := 3` | `ExtractReportNode.exec()` → LLM call; `.post()` sets `loop_count=3` | Routes directly to `WriteFileNode` (bypasses `LoopCheckNode`) |

+| `GENERATE extract_feedback(@decision) INTO @feedback; @loop_count += 1; GENERATE planner(...)` | `ExtractFeedbackNode.exec()` — three sequential operations in one exec | `feedback` LLM call → increment → `planner` LLM call; result tuple pushed to `shared` in `post()` |

+| `CALL write_file(@out, @report) INTO @write_result` | `WriteFileNode.exec()` — `open(path, "w").write(content)` | Returns `"written:<path>"` string stored in `shared["write_result"]` |

+| `RETURN @report WITH status = "complete"` | `shared["status"]` set implicitly via `run_deep_research()` returning `shared["report"]` | No explicit `status` field in `WriteFileNode.post()` — caller infers success if report is non-empty |

+| Adapter: `claude_cli`, model: `sonnet` | `subprocess.run(["claude", "-p", prompt, "--model", "claude-sonnet-4-6"], timeout=180)` | `call_llm` raises `RuntimeError` on non-zero exit |

+

+---

 

 ## 3. Logical Functions / Prompts

 

-**`planner`**

-- Role: Query generation — translates a research topic (or gap description) into three actionable web-search strings.

-- Prompt conventions: Two modes controlled by the `feedback` parameter — cold start (`"Generate 3 diverse search queries to research: '{topic}'"`) vs. gap-fill (`"Gaps to fill: {feedback}\nGenerate 3 search queries to fill these gaps"`). Output must be strict YAML wrapped in ` ```yaml ``` ` fences with a single `queries` list key. No scoring or sentiment tokens.

+### `planner`

+- **Role:** Query generation. Given the topic and any prior feedback, generates exactly 3 diverse search queries in `QUERY_1: / QUERY_2: / QUERY_3:` format.

 

-**`researcher`** (batch variant)

-- Role: Fact extraction — takes one search query, retrieves raw web snippets via `search_web`, then instructs the LLM to distill key facts relevant to that specific query.

-- Prompt conventions: Two-part sequential call per item. First call is `search_web` (deterministic tool). Second call is `"Extract key facts relevant to this query. Be brief.\n\nQuery: {query}\nSearch result:\n{raw}"` — free-form text response, no structured output required. Result stored as `"Q: {query}\nFacts: {extracted}"` composite string.

+### `extract_query`

+- **Role:** Query extractor. Given the full planner output and a position number (1–3), returns just the text after `QUERY_N: `.

 

-**`synthesizer`**

-- Role: Gap detection and report generation — evaluates accumulated notes for completeness and either identifies missing coverage (returning to the loop) or produces the final markdown report.

-- Prompt conventions: Dual-branch YAML output using mutually exclusive schemas. Branch 1: `action: research` + `feedback: "<gap description>"`. Branch 2: `action: finalize` + `content: "<full markdown report>"`. Output wrapped in ` ```yaml ``` ` fences. When the loop counter reaches 2, the LLM is bypassed entirely and a forced-finalization prompt (`"Write a concise research report on '{topic}' using these notes"`) is called directly, returning `{"action": "finalize", "content": report}`.

+### `extract_facts`

+- **Role:** Fact summariser. Given a query and its search result, extracts key facts as a concise bullet-point list.

+

+### `accumulate_notes`

+- **Role:** Note merger. Combines existing notes with three new fact batches, removing duplicates and grouping related facts.

+

+### `synthesizer`

+- **Role:** Research evaluator. Reviews all accumulated notes and decides to `DECISION: finalize` (includes a full report) or `DECISION: research` (includes feedback for the next iteration).

+

+### `extract_report` / `extract_feedback`

+- **Role:** Output extractors. Parse the synthesizer's response to return only the content after `REPORT: ` or `FEEDBACK: ` respectively.

+

+### `write_concise_report`

+- **Role:** Fallback report generator. Called only when `loop_count == 2` (max-loop shortcut). Produces a concise report directly from accumulated notes without a synthesizer decision.

+

+### `search_web` (tool call)

+- **Role:** Live web search via claude CLI. Passes a "Search the web for: {query}" prompt and returns a detailed summary. **Not a stub** — makes a real LLM call.

+

+---

 

 ## 4. Control Flow

 

 ```

-START

-  │

-  ▼

-GENERATE planner(topic, feedback="") INTO @queries          ← initial pass, no feedback

-  │

-  ▼

-WHILE loop_count < 2 DO

-  │

-  ├── CALL search_web(@query) INTO @raw   ┐

-  │   GENERATE researcher(@query, @raw)   │  (batched in parallel over @queries)

-  │   INTO @note_set                      ┘

-  │   ACCUMULATE @note_set INTO @notes

-  │

-  ├── GENERATE synthesizer(topic, @notes, loop_count) INTO @decision

-  │

-  └── EVALUATE @decision

-        WHEN action == "research" THEN

-          loop_count += 1

-          @feedback ← @decision.feedback

-          GENERATE planner(topic, @feedback) INTO @queries

-          → loop back to WHILE top

-        WHEN action == "finalize" THEN

-          @report ← @decision.content

-          → EXIT loop

-END WHILE

+INPUT @topic TEXT, @out TEXT := "report.txt"

+@loop_count ← 0; @feedback ← ""; @notes ← ""; @report ← ""

 

-(if loop_count >= 2 before EVALUATE: bypass LLM, force GENERATE finalization prompt)

+GENERATE planner(@topic, "") INTO @queries                    [LLM]

 

-CALL write_file(@report, path=out)

-RETURN @report WITH status="complete", loop_count=loop_count

+── WHILE @loop_count < 3 ─────────────────────────────────────────────────

+│  LoopCheckNode checks loop_count:

+│    if >= 3      → "done"      >> WriteFileNode             (safety net)

+│    if "2" in N  → "max_loops" >> WriteConciseReportNode

+│                                      ↓ sets loop_count=3

+│                               >> WriteFileNode  ──────────────────── ~

+│    else         → "continue"

+│

+│  GENERATE extract_query(@queries, 1|2|3) INTO @q1,@q2,@q3  [LLM ×3 parallel]

+│

+│  CALL PARALLEL search_web(@q1), search_web(@q2), search_web(@q3)

+│       → @result1, @result2, @result3                        [LLM ×3 parallel]

+│

+│  CALL PARALLEL extract_facts(@q1,@r1), ..., (@q3,@r3)

+│       → @note1, @note2, @note3                             [LLM ×3 parallel]

+│

+│  GENERATE accumulate_notes(@notes, @note1, @note2, @note3)  [LLM]

+│       → @notes

+│

+│  GENERATE synthesizer(@topic, @notes, @loop_count)          [LLM]

+│       → @decision

+│

+│  EVALUATE @decision

+│    WHEN contains("DECISION: finalize") THEN

+│      GENERATE extract_report(@decision) → @report          [LLM]

+│      @loop_count := 3

+│      >> WriteFileNode  ────────────────────────────────────────────── ✓

+│    ELSE

+│      GENERATE extract_feedback(@decision) → @feedback      [LLM]

+│      @loop_count += 1

+│      GENERATE planner(@topic, @feedback) → @queries        [LLM]

+│      → LoopCheckNode (back-edge)

+│  END

+└──────────────────────────────────────────────────────────────────────────

+

+CALL write_file(@out, @report) INTO @write_result

+RETURN @report WITH status = "complete"

 ```

+

+**Loop-count reachability:** `ExtractFeedbackNode` increments `loop_count` from 0→1 or 1→2. On the pass through `LoopCheckNode` with `loop_count=2`, `"max_loops"` fires. Therefore `LoopCheckNode`'s `"done"` (≥3) edge is a safe unreachable guard — `loop_count` reaches 3 only inside `ExtractReportNode` or `WriteConciseReportNode`, which route directly to `WriteFileNode`.

+

+**Observed run (2026-05-04):** Topic `"quantum computing applications"` → comprehensive 6-section report covering hardware landscape, PQC standards, drug discovery, financial optimization, and cross-domain assessment. Report written to `report.txt`.

+

+---

 

 ## 5. How to Regenerate as SPL

 

 ```bash

-# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)

-spl3 text2spl --description "<paste Section 0 here>" --mode workflow

+# Step 1 — regenerate SPL from this spec

+spl3 text2spl --description "$(sed -n '/^## 0\./,/^---/p' S5-research-claude_cli-sonnet-2-spec.md)" \

+    --mode workflow --adapter claude_cli

 

-# Step 2 — compile to any target

-spl3 splc compile deep_research.spl --lang python/pocketflow

+# Step 2 — run

+spl3 run deep_research.spl --adapter claude_cli \

+    --param topic="quantum computing applications" \

+    --param out="report.txt"

+

+# Step 3 — recompile to any target

+spl3 splc compile deep_research.spl --lang python/pocketflow --llm \

+    --adapter claude_cli --model sonnet

 spl3 splc compile deep_research.spl --lang python/langgraph

 spl3 splc compile deep_research.spl --lang go

-```
+```

```
---

*Generated by SPL semantic comparison tool*