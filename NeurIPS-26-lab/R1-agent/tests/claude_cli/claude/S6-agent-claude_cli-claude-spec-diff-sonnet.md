# File Comparison Report

**Files Compared:**
- File 1: `S1-agent-claude_cli-claude-1-spec.md` (.md)
- File 2: `S5-agent-claude_cli-claude-2-spec.md` (.md)
- **Timestamp:** 2026-05-04 09:35:47
- **Active Modes:** llm, git-diff

---
## LLM Semantic Analysis

**Adapter:** claude_cli
**Model:** claude-sonnet-4-6

## Summary

Both specs describe the same conceptual ReAct-style iterative research agent compiled to PocketFlow Python, but they represent **different generations of the same design**. File 1 is a cleaner, more concise first-pass spec with a real search backend. File 2 is a more mature, production-aware spec with explicit loop guards, multi-state termination, formal tool decomposition, and observed run evidence. **File 2 is the stronger document overall**, though File 1 has advantages in prose clarity and using a live search implementation.

---

## Content Analysis

### File 1 Strengths
- **Real search backend**: Uses live DuckDuckGo via `search_web_duckduckgo()` — not a stub. The spec is immediately runnable end-to-end.
- **Concise prose**: Section 0 is denser and more readable as a single-paragraph summary. Better for quick onboarding.
- **YAML exception handling described narratively**: The block-scalar fixup logic is explained inline in Section 3, making the intent clear without requiring a separate node.
- **Simpler mental model**: Fewer moving parts — 3 logical functions, one clear loop, one exit path. Easier to reason about.

### File 2 Strengths
- **Explicit loop guard**: `@iteration < 10` with `LoopCheckNode` prevents infinite loops — a critical production safeguard absent from File 1.
- **Multi-state termination**: Three distinct exit states (`status="complete"`, `status="error"`, `status="max_iterations_reached"`) versus File 1's single `status=done`. Enables proper error handling by callers.
- **Formal tool decomposition**: `parse_yaml_tool`, `force_block_scalars_tool`, `extract_field_tool`, `search_web_tool` are named, discrete, testable units. File 1 treats these as inline logic.
- **ASCII control-flow diagram**: Section 4's box-drawing diagram makes the branching structure immediately scannable — a significant documentation upgrade.
- **Observed run evidence**: "Who invented telephone → 2 iterations, status=complete" grounds the spec in empirical reality, not just design intent.
- **More complete SPL ↔ Python table**: Covers `@iteration`, `@done`, `LoopCheckNode`, `InitNode`, retry/error paths — 22 rows vs File 1's 13 rows.
- **Stub is honest**: Flagging `search_web_tool` as a stub with `# Replace with SerpAPI / Tavily / DuckDuckGo` is more production-honest than hiding implementation debt.

### Common Elements
| Element | Both Files |
|---|---|
| Core pattern | ReAct WHILE-loop: decide → search → loop, or decide → answer → exit |
| `decide_action` function | Fenced YAML block with `action: search\|answer` |
| `answer_question` function | Free-form prose synthesis terminal node |
| YAML error recovery | Force block-scalar fixup + retry-once pattern |
| `@context` accumulation | `SEARCH: / RESULTS:` blocks appended each iteration |
| PocketFlow encoding | Loop via action-string routing (`"decide"`, `"search"`, `"done"`) |
| SPL ↔ Python mapping table | Section 2 in both |
| Regeneration commands | `spl3 text2spl` + `spl3 splc` in Section 5 |

---

## Detailed Comparison

### Structure & Organization

**File 1** follows a clean 5-section layout where each section stands alone. Section 4 (Control Flow) is prose-only, which is readable but loses precision at branch junctions.

**File 2** uses the same 5-section skeleton but upgrades Section 4 to an ASCII flow diagram with explicit branch labels (`──✗`, `──✓`) and a parenthetical max-iterations exit. The SPL ↔ Python table is also structurally superior — it includes all lifecycle state variables (`@iteration`, `@done`, `@raw_response`, `@parse_result`, `@fixed_response`, `@retry_result`) whereas File 1 covers only the "happy path" variables.

**Winner: File 2** — the diagram alone justifies the preference.

---

### Logic & Completeness

**File 1's critical gap**: No iteration cap. The WHILE loop continues as long as `decide_action` returns `action: search`. A misbehaving or stuck LLM could loop indefinitely. This is a production defect, not a design choice.

**File 2 closes this gap** with `@iteration < 10` guarded by `LoopCheckNode`, and defines `status="max_iterations_reached"` as a distinct exit, enabling callers to distinguish "answered" from "gave up."

**File 2's gap**: The `search_web_tool` is a stub. As written, the agent never retrieves real information — it generates an answer over fabricated context. This makes the spec runnable but not useful without modification.

**File 1's gap**: YAML error recovery (the block-scalar fixup) is described narratively in Section 3 but does not appear in the Section 2 mapping table or Section 4 control flow. A reader implementing from spec could miss this path.

**File 2 addresses this**: `ForceBlockScalarsNode` and `RetryParseNode` appear in both the mapping table and the flow diagram with explicit routing (`"parse_error"` → fixup → retry → `"error"` terminal).

**Winner: File 2** on logical completeness; File 1 on real-world utility (live search).

---

### Quality & Sophistication

| Dimension | File 1 | File 2 |
|---|---|---|
| Loop safety | No cap — infinite loop risk | Explicit 10-iteration guard |
| Exit states | 1 (`done`) | 3 (`complete`, `error`, `max_iterations_reached`) |
| Tool granularity | Mixed (tools described but not decomposed) | 4 named, testable tool functions |
| Search backend | Live DuckDuckGo | Stub (honest but non-functional) |
| Error path visibility | Implicit / narrative | Explicit nodes in graph and diagram |
| Empirical grounding | None | Observed run with question, iteration count, result |
| Prompt detail | High (block-scalar requirements, two-section layout) | Moderate (less prompt-engineering specificity) |

File 1 is stronger on **prompt engineering specificity** — it explicitly documents why block scalars (`|`) are required (embedded colons and quotes break YAML parsing) and what the two-section prompt structure looks like. File 2 omits this detail.

**Winner: File 2** on engineering rigor; File 1 on prompt design documentation.

---

### Syntax & Technical Accuracy

Both files use syntactically valid Markdown with consistent table formatting and properly fenced code blocks.

**File 1 inaccuracy**: The Section 2 table maps `WHILE action == "search" DO` to a PocketFlow cycle edge — this is architecturally correct but elides the `LoopCheckNode` abstraction layer, which could mislead an implementer.

**File 2 accuracy issues**:
- `LoopCheckNode.post()` returning `"exit"` with "no successor → flow terminates" is correct PocketFlow behavior, but this should be noted explicitly in the table (it is, in the Notes column — good).
- The `@iteration += 1` placement (after LLM call in `DecideActionNode.post()`) means the loop check reads the *post-increment* value — this is correct behavior but subtle, and File 2 calls it out explicitly ("Incremented after LLM call; LoopCheckNode reads updated value next pass"), which is exemplary annotation.

**File 1 bash command accuracy**: The `spl3 text2spl --description "<paste Section 0 here>"` instruction in Section 5 is informal and non-reproducible. File 2's Section 5 uses `$(sed -n '/^## 0\./,/^---/p' S5-...)` — a reproducible shell one-liner that self-references the file.

**Winner: File 2** on technical precision and reproducibility.

---

## Recommendations

### 1. Best Choice
**File 2 is the better production spec.** It is safer (loop cap), more complete (multi-state exits), more testable (decomposed tools), better documented (flow diagram), and empirically grounded (observed run). Use it as the canonical reference.

### 2. Improvements for File 1
- **Add iteration cap**: Add `AND @iteration < 10` to the WHILE condition and define `status="max_iterations_reached"` as an exit state.
- **Surface the YAML error path in the mapping table**: Add `ForceBlockScalarsNode` / `RetryParseNode` rows so the recovery path isn't buried in Section 3 prose.
- **Add a flow diagram**: Adopt File 2's ASCII box-drawing diagram in Section 4 — it pays for itself immediately in reviewer comprehension.
- **Add observed run evidence**: A single concrete example ("Question X → N iterations → status=complete") transforms a design document into a validated spec.

### 3. Hybrid Approach to Combine Both
A merged spec would take:
- **From File 2**: Loop guard (`@iteration < 10`), multi-state exits, formal tool decomposition, ASCII flow diagram, observed run block, reproducible `sed`-based regeneration command.
- **From File 1**: Live DuckDuckGo backend (replace the stub), richer prompt engineering documentation (two-section prompt layout, block-scalar requirement rationale), and the cleaner single-paragraph Section 0.

The merged Section 3 would document both the *why* of block-scalar requirements (File 1's strength) and the formal tool signatures (File 2's strength). The merged Section 5 would use File 2's reproducible `sed` command pointing at the merged file.

---

## Scoring

| Dimension | File 1 | File 2 |
|---|---|---|
| **Structure** | 7/10 | 9/10 |
| **Logic** | 6/10 | 8/10 |
| **Quality** | 7/10 | 8/10 |
| **Overall** | 6.5/10 | 8.5/10 |

File 1 loses 1.5 points on Structure for the missing flow diagram and incomplete mapping table; loses 2 points on Logic for the absent iteration cap; the live DuckDuckGo backend keeps its Quality score competitive. File 2 loses 1 point on Logic for the stub search tool and slightly less prompt-engineering specificity in Section 3.
---

## Mechanical Diff (Unified Style)

```diff
--- a/S1-agent-claude_cli-claude-1-spec.md
+++ b/S5-agent-claude_cli-claude-2-spec.md
@@ -1,78 +1,118 @@
 ## 0. High-level Description

 

-This workflow implements an iterative research agent using a WHILE-loop pattern driven by a GENERATE call to the `decide_action` function, which produces a structured YAML decision on each iteration. Three logical functions are defined: `decide_action` (a chain-of-thought reasoning prompt that evaluates accumulated context and returns either `action: search` with a `search_query` or `action: answer` with a final answer), `search_web` (a CALL side-effect that invokes DuckDuckGo and appends results to the shared `@context` variable), and `answer_question` (a GENERATE call that synthesizes accumulated research into a comprehensive final answer). The WHILE loop persists as long as `decide_action` returns `action: search`, with an EVALUATE branch directing execution to either CALL `search_web` (then loop back) or GENERATE `answer_question` (then terminate). A YAML-parsing fallback that forces block-scalar (`|`) notation on known keys and retries the parse acts as an implicit EXCEPTION handler for malformed LLM output. The workflow terminates with RETURN `@answer` WITH `status=done` after `answer_question` completes.

+This workflow implements a ReAct-style web search agent that iteratively decides whether to search or answer using a structured YAML decision loop. Two `CREATE FUNCTION` prompts are defined: `decide_action` prompts the LLM to reason about the accumulated context and return a fenced YAML block containing `action: search` (with `search_query`) or `action: answer`; `answer_question` synthesizes all accumulated context into a final prose answer. Execution begins with `InitNode` which seeds `@context`, `@iteration`, `@done`, and `@decision`. A `LoopCheckNode` guards the WHILE condition (`@done != "true" AND @iteration < 10`) by returning `"continue"` or `"exit"`. On each iteration `DecideActionNode` calls the LLM, then `ParseYamlNode` attempts `yaml.safe_load` on the fenced YAML response; a YAML parse failure routes to `ForceBlockScalarsNode` (which strips inline quotes) and `RetryParseNode` — if the retry also fails the flow terminates with `status="error"`. On clean parse, `EvaluateDecisionNode` inspects `decision["action"]` and routes to either `SearchWebNode` (stub tool, appends to `@context`, loops back) or `AnswerQuestionNode` (final LLM synthesis, sets `@done="true"`, terminates with `status="complete"`). The `search_web_tool` is a stub intended to be replaced with a live search API. There is no explicit EXCEPTION block; unhandled `subprocess.CalledProcessError` would propagate from `call_llm`.

 

 ---

 

 ## 1. Purpose

 

-Answers a user-supplied research question by iteratively deciding to search the web or synthesize a final answer, accumulating web search results in `@context` across multiple rounds until the agent determines it has sufficient information.

+Answers a user research question by autonomously looping through web-search and reasoning steps — up to 10 iterations — until the LLM decides it has sufficient context to deliver a final synthesized answer.

 

 ---

 

-## 2. SPL ↔ Python Construct Mapping

+## 2. SPL ↔ Python — PocketFlow Construct Mapping

 

-| SPL Construct | Python Equivalent | Notes |

+| SPL Construct | Python — PocketFlow Equivalent | Notes |

 |---|---|---|

-| `WORKFLOW research_agent` | `create_agent_flow()` + `Flow(start=decide)` | Graph topology wired via PocketFlow `>>` edge operator |

-| `CREATE FUNCTION decide_action` | `DecideAction` Node (`prep`/`exec`/`post`) | Structured YAML output; routing logic in `post()` |

-| `CREATE FUNCTION search_web` | `SearchWeb` Node (`prep`/`exec`/`post`) | Pure CALL — no LLM involved |

-| `CREATE FUNCTION answer_question` | `AnswerQuestion` Node (`prep`/`exec`/`post`) | Terminal GENERATE; free-form prose output |

-| `GENERATE decide_action(...) INTO @decision` | `call_llm(prompt)` in `DecideAction.exec()` | Returns fenced YAML block parsed into a dict |

-| `CALL search_web_duckduckgo(@search_query) INTO @results` | `search_web_duckduckgo(search_query)` in `SearchWeb.exec()` | Side-effect tool call; up to 5 DuckDuckGo results |

-| `EVALUATE @decision WHEN contains('search') THEN ... ELSE ...` | `exec_res["action"] == "search"` in `DecideAction.post()` | Branches on the `action` field of parsed YAML |

-| `WHILE action == "search" DO ... END` | `search - "decide" >> decide` cycle edge | PocketFlow graph cycle encodes the loop implicitly |

-| `RETURN @answer WITH status="done"` | `return "done"` in `AnswerQuestion.post()` | Flow terminates; final answer stored in `shared["answer"]` |

-| `EXCEPTION WHEN YAMLError THEN retry_with_block_scalars` | `parse_yaml_safely()` with key-line fixup and second `yaml.safe_load` | Forces `|` block scalars on known keys, retries once |

-| `@context` | `shared["context"]` | Accumulates `SEARCH: / RESULTS:` blocks across iterations |

-| `@question` | `shared["question"]` | Read-only workflow input; set before flow starts |

-| `@search_query` | `shared["search_query"]` | Written by `DecideAction.post()`, consumed by `SearchWeb.prep()` |

-| `@answer` | `shared["answer"]` | Final output; written by `AnswerQuestion.post()` |

+| `WORKFLOW web_search_agent` | `build_flow() → Flow(start=init)` | Node graph replaces declarative WORKFLOW header |

+| `INPUT @question TEXT` | `shared["question"]` set before `Flow.run()` | Read-only throughout; passed into every prompt |

+| `OUTPUT @answer TEXT` | `shared["answer"]` written by `AnswerQuestionNode.post()` | Returned in result dict by `run_web_search_agent()` |

+| `@context := 'No previous search'` | `InitNode.post()` sets `shared["context"]` | Accumulates `SEARCH: / RESULTS:` blocks each iteration |

+| `@iteration := 0`, `@done := 'false'` | `InitNode.post()` seeds `shared["iteration"]`, `shared["done"]` | String `"true"/"false"` mirror SPL string convention |

+| `WHILE @done != 'true' AND @iteration < 10 DO` | `LoopCheckNode.prep/exec/post` returning `"continue"` or `"exit"` | `"exit"` has no successor → flow terminates (max iterations) |

+| `@iteration := @iteration + 1` | `shared["iteration"] += 1` in `DecideActionNode.post()` | Incremented after LLM call; LoopCheckNode reads updated value next pass |

+| `GENERATE decide_action(@question, @context) INTO @raw_response` | `DecideActionNode.exec()` → `call_llm(prompt)` | Expects fenced ` ```yaml ``` ` block in response |

+| `CALL parse_yaml(@raw_response) INTO @parse_result` | `ParseYamlNode.exec()` → `parse_yaml_tool(raw)` | Extracts YAML from code fence; returns `{"parse_error": ...}` on failure |

+| `EVALUATE @parse_result WHEN contains('parse_error')` | `ParseYamlNode.post()` returning `"parse_error"` or `"evaluate"` | Drives YAML error-recovery path |

+| `CALL force_block_scalars(@raw_response) INTO @fixed_response` | `ForceBlockScalarsNode.exec()` → `force_block_scalars_tool(raw)` | Strips inline quotes from YAML values |

+| `CALL parse_yaml(@fixed_response) INTO @retry_result` | `RetryParseNode.exec()` → `parse_yaml_tool(fixed)` | Second parse attempt after fixup |

+| `RETURN @retry_result WITH status='error'` | `RetryParseNode.post()` sets `shared["status"]="error"`, returns `"error"` (terminal) | Unrecoverable YAML failure path |

+| `EVALUATE @decision WHEN contains('action: search')` | `EvaluateDecisionNode.post()` checks `decision.get("action") == "search"` | Non-search action falls through to answer path |

+| `CALL extract_field(@decision, 'search_query') INTO @search_query` | `SearchWebNode.exec()` calls `extract_field_tool(decision, "search_query")` | Inline within `SearchWebNode`; not a separate node |

+| `CALL search_web(@search_query) INTO @search_results` | `search_web_tool(query)` → stub returning placeholder string | Replace with SerpAPI / Tavily / DuckDuckGo for production |

+| `@context := @context + '\nSEARCH: ...'` | `SearchWebNode.post()` appends to `context` from `prep_res` | Uses value captured at `prep()` time (consistent within iteration) |

+| `GENERATE answer_question(@question, @context) INTO @answer` | `AnswerQuestionNode.exec()` → `call_llm(ANSWER_QUESTION_PROMPT.format(...))` | Free-form prose synthesis |

+| `@done := 'true'` | `AnswerQuestionNode.post()` sets `shared["done"] = "true"` | Signals loop exit, though flow terminates via `"done"` action (no successor) |

+| `RETURN @answer WITH status='complete'` | `shared["status"] = "complete"` + `"done"` terminal action | `"done"` has no successor registered → flow ends |

+| Adapter: `claude_cli` | `subprocess.run(["claude", "-p", prompt])` | No `--model` flag; defaults to Claude's own default |

 

 ---

 

 ## 3. Logical Functions / Prompts

 

 ### `decide_action`

-- **Role**: The reasoning core of the agent. Given `@question` and accumulated `@context`, it decides whether to gather more information or deliver a final answer.

-- **Key prompt conventions**:

-  - Two-section prompt: `### CONTEXT` (question + previous research) and `### ACTION SPACE` (enumerate `search` and `answer` with parameter schemas).

-  - Output is a fenced ` ```yaml ``` ` block with fields: `thinking` (block scalar `|`), `action` (`search` or `answer`), `reason` (block scalar `|`), `answer` (block scalar `|`, empty when searching), `search_query` (plain single-line string).

-  - All multi-line fields explicitly require `|` block scalar to prevent embedded colons and quotes from breaking YAML parsing.

-  - EXCEPTION fallback: if `yaml.safe_load` fails, lines matching known keys are rewritten to force `|` notation and parsing is retried once; if that also fails, a `ValueError` is raised.

+- **Role:** Reasoning core of the ReAct loop. Given the accumulated `@context`, decides whether to search further or answer.

+- **Output:** Fenced ` ```yaml ``` ` block with keys `action` (`search` or `answer`) and `search_query` (only when `action: search`).

+- **Error recovery:** If the raw LLM response fails YAML parse, `force_block_scalars_tool` strips inline quotes and the parse is retried once. A second failure terminates the flow with `status="error"`.

 

 ### `answer_question`

-- **Role**: Terminal synthesis prompt. Consumes `@question` and the full accumulated `@context` to produce a comprehensive prose answer.

-- **Key prompt conventions**:

-  - Two-section prompt: `### CONTEXT` and `## YOUR ANSWER:`.

-  - No structured output format — free-form prose is expected.

-  - No sentinel tokens or scoring; the raw LLM response is stored as `@answer`.

+- **Role:** Terminal synthesis step. Consumes `@question` and the full accumulated `@context` to produce the final user-facing answer.

+- **Output:** Free-form prose; no structured format required.

 

-### `search_web` (tool call, not a prompt)

-- **Role**: CALL side-effect. Executes a DuckDuckGo text search for `@search_query` and returns up to 5 results.

-- **Key conventions**: Results are formatted as `Title: / URL: / Snippet:` blocks joined by double newlines. After execution, the result is appended to `@context` as `SEARCH: <query>\nRESULTS: <results>`, providing a running log of all searches performed.

+### Tool calls (not prompts)

+- `parse_yaml_tool(raw)` — extracts content from ` ```yaml ``` ` fence and calls `yaml.safe_load`; returns `{"parse_error": ...}` on failure.

+- `force_block_scalars_tool(raw)` — strips `"..."` and `'...'` inline quoting from YAML values to coerce block-scalar compatibility.

+- `extract_field_tool(decision, field)` — `dict.get(field, "")` with `str()` cast.

+- `search_web_tool(query)` — stub; returns `"[stub: search results for '...']"`.

 

 ---

 

 ## 4. Control Flow

 

-1. **Initialization**: `@question` is populated from CLI input; `@context` defaults to `"No previous search"`. Flow starts at `decide_action`.

-2. **WHILE loop entry**: `decide_action` GENERATEs a YAML decision. EVALUATE checks `@decision["action"]`:

-   - **`action == "search"`** (loop continues): `@search_query` is set. CALL `search_web(@search_query) INTO @results`. `@context` is updated by appending `SEARCH: ... RESULTS: ...`. Returns `"decide"` → loops back to `decide_action`. WHILE condition remains true.

-   - **`action == "answer"`** (loop exits): `@context` may be updated with an inline answer. Transitions to `answer_question`.

-3. **Termination**: `answer_question` GENERATEs a final prose answer INTO `@answer`. RETURN `@answer` WITH `status=done`. Flow terminates.

-4. **Exception path**: At any `decide_action` GENERATE step, if YAML parsing fails after the block-scalar fixup retry, a `ValueError` propagates — equivalent to EXCEPTION WHEN `YAMLParseError` THEN `raise`.

+```

+INPUT @question

+@context ← "No previous search"; @iteration ← 0; @done ← "false"

+

+── WHILE @done != "true" AND @iteration < 10 ───────────────────────────

+│

+│  GENERATE decide_action(@question, @context) INTO @raw_response

+│  @iteration += 1

+│

+│  CALL parse_yaml(@raw_response) INTO @parse_result

+│  EVALUATE @parse_result

+│    WHEN contains("parse_error") THEN

+│      CALL force_block_scalars(@raw_response) INTO @fixed_response

+│      CALL parse_yaml(@fixed_response) INTO @retry_result

+│      EVALUATE @retry_result

+│        WHEN contains("parse_error") THEN RETURN status="error"  ──────── ✗

+│        ELSE @decision := @retry_result

+│      END

+│    ELSE @decision := @parse_result

+│  END

+│

+│  EVALUATE @decision

+│    WHEN action == "search" THEN

+│      CALL search_web(@decision["search_query"]) INTO @search_results

+│      @context += "\nSEARCH: ... RESULTS: ..."

+│      → loop back

+│    ELSE (action == "answer")

+│      GENERATE answer_question(@question, @context) INTO @answer

+│      @done ← "true"

+│      RETURN @answer WITH status="complete"  ───────────────────────── ✓

+│  END

+│

+└────────────────────────────────────────────────────────────────────────

+(loop exits via @iteration >= 10 → RETURN status="max_iterations_reached", answer="")

+```

+

+**Observed run (2026-05-04):** Question `"Who invented telephone"` → 2 iterations, `status=complete`. The agent performed one search then synthesized a multi-perspective answer covering Bell, Gray, Meucci, and Reis.

 

 ---

 

 ## 5. How to Regenerate as SPL

 

 ```bash

-# Step 1 — generate SPL from this spec (use Section 0 above as text2spl input)

-spl3 text2spl --description "<paste Section 0 here>" --mode workflow

+# Step 1 — regenerate SPL from this spec

+spl3 text2spl --description "$(sed -n '/^## 0\./,/^---/p' S5-agent-claude_cli-claude-2-spec.md)" \

+    --mode workflow --adapter claude_cli

 

-# Step 2 — compile to any target

-spl3 splc compile research_agent.spl --lang python/pocketflow

-spl3 splc compile research_agent.spl --lang python/langgraph

-spl3 splc compile research_agent.spl --lang go

-```
+# Step 2 — run

+spl3 run web_search_agent.spl --adapter claude_cli \

+    --param question="Who invented the telephone?"

+

+# Step 3 — recompile to any target

+spl3 splc compile web_search_agent.spl --lang python/pocketflow --llm \

+    --adapter claude_cli --model claude

+spl3 splc compile web_search_agent.spl --lang python/langgraph

+spl3 splc compile web_search_agent.spl --lang go

+```

```
---

*Generated by SPL semantic comparison tool*