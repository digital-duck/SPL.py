# File Comparison Report

**Files Compared:**
- File 1: `S1-research-openrouter-qwen-1-spec.md` (.md)
- File 2: `S5-research-openrouter-qwen-2-spec.md` (.md)
- **Timestamp:** 2026-05-04 11:08:09
- **Active Modes:** llm, git-diff

---
## LLM Semantic Analysis

**Adapter:** claude_cli
**Model:** claude-opus-4-6

## Summary

Both files spec the same conceptual task — an iterative web-research pipeline that plans queries, searches, extracts facts, and synthesizes a report. The core difference is **architectural paradigm**: File 1 describes a **graph-based, LLM-routed orchestration** (PocketFlow nodes with dynamic routing), while File 2 describes a **procedural, fixed-iteration pipeline** (monolithic class with a bounded `while` loop). File 1 is the stronger spec overall: it captures more behavioral nuance, has richer prompt-engineering detail, and models genuinely adaptive control flow. File 2 is cleaner to read but sacrifices precision and flexibility.

---

## Content Analysis

### File 1 Strengths
- **Dynamic control flow**: The `EVALUATE @synthesis_action` routing pattern lets the LLM decide whether to loop or finalize, making the workflow adaptive rather than mechanically fixed. This is a qualitatively different (and harder to spec) design.
- **Precise prompt conventions**: Specifies exact YAML keys (`action: research|finalize`, `feedback:`, `content:`), output delimiters (`\n---\n`), and expected cardinality ("exactly three diverse query strings"). A developer could implement from this spec without guessing formats.
- **Accurate RETURN semantics**: Correctly identifies `return "research"` / `return "finalize"` as non-trivial routing tokens that override linear progression — this is the key PocketFlow concept and File 1 nails it.
- **Richer Section 0**: Packs more architectural information into the high-level description (YAML parsing, side-effect inventory, exception delegation strategy), making it viable as a standalone `text2spl` input.

### File 2 Strengths
- **Readability**: Every section is shorter and easier to parse on first read. The control flow description is straightforward and unambiguous.
- **Explicit exception mapping**: Includes `EXCEPTION → try...except` as a first-class row in the construct table with a clear fallback strategy (deterministic mock outputs), whereas File 1 hand-waves this into a prose sentence.
- **Dual-counter safeguard**: The `@loop_count < 2 AND @iteration < 3` compound condition is a concrete defensive-programming detail that File 1 doesn't surface.
- **Cleaner Section 3 formatting**: Uses bold headers with dash-separated fields consistently, making prompt roles scannable.

### Common Elements
- Identical 6-section template (0–5) with the same regeneration instructions in Section 5.
- Same three logical functions: `plan_queries`, `extract_facts`, `assess_and_report`.
- Same shared-state variables: `@topic`, `@notes`, `@report`, `@loop_count`/`@iteration_count`, `@feedback`.
- Same external side effects: DuckDuckGo web search + filesystem write.
- Same LLM provider context (OpenRouter / Qwen model).
- Both cap the loop at 2 research iterations.

---

## Detailed Comparison

### Structure & Organization

| Aspect | File 1 | File 2 |
|---|---|---|
| Section 0 density | High — one long, information-rich paragraph | Moderate — slightly shorter, clearer sentence boundaries |
| Section 2 table | 7 rows, includes non-trivial `RETURN` semantics | 8 rows, adds `EXCEPTION` and `RETURN` as separate entries |
| Section 3 format | Markdown list with `- **Name**:` / `- **Role**:` / `- **Key prompt conventions**:` | Bold headers with `- **Role:**` / `- **Key prompt conventions:**` — slightly more scannable |
| Section 4 length | ~6 sentences, covers dynamic routing | ~5 sentences, covers linear loop |

File 1's structure carries more information per section but requires more careful reading. File 2 is leaner but omits details a downstream compiler or developer would need.

### Logic & Completeness

**Control flow fidelity**: File 1 models a **feedback loop with LLM-driven exit** — the synthesizer evaluates research completeness and can either route back to the planner (with gap feedback) or finalize. File 2 models a **fixed-count loop with post-loop synthesis** — there is no mid-loop decision; it always runs exactly 2 iterations then synthesizes. This is a fundamental behavioral difference. If the target code has adaptive routing, File 1 is accurate and File 2 is lossy.

**Error handling**: File 2 is more complete here. It specifies the fallback strategy (mock outputs) and maps `EXCEPTION` explicitly. File 1 only mentions that exceptions "surface as immediate workflow halts," which is less precise and less useful for regeneration.

**Prompt output parsing**: File 1 specifies YAML output with exact keys. File 2 specifies `QUERY:` prefix regex and bullet-point format. Both are valid but describe different implementations — File 1's YAML convention is more robust for structured extraction.

**Gap analysis**: File 1 explicitly describes `assess_and_report` as switching between gap-analysis and final-document generation modes. File 2 describes it only as a final synthesis step, missing the dual-mode behavior.

### Quality & Sophistication

File 1 operates at a higher level of abstraction fidelity. It captures:
- The graph topology (node chain + routing edges)
- The distinction between implicit linear progression and explicit routing overrides
- The conditional prompt injection (`feedback` string only injected when gaps exist)
- The forced-finalize escape hatch (`@loop_count >= 2` bypasses LLM evaluation)

File 2 is competent but flatter — it describes a sequential pipeline without the adaptive intelligence that distinguishes a research agent from a batch script.

### Syntax & Technical Accuracy

Both files are syntactically clean with no formatting errors. Specific technical notes:

- **File 1**: The construct mapping correctly identifies `prep`/`post` as the PocketFlow execution model. The `RETURN @report WITH status=complete, iterations=@loop_count` syntax accurately models keyword-argument-style metadata on the return value.
- **File 2**: The `S3ResearchOpenrouterQwenFlow` class name is more specific (includes the model/adapter context). The `temperature 0.7` callout is a useful implementation detail absent from File 1. However, "guaranteeing exactly two research passes" is an overstatement if the `@iteration < 3` guard can trigger independently.

---

## Recommendations

### 1. Best Choice: **File 1**

File 1 is the better spec for regeneration, code review, or onboarding purposes. Its adaptive control flow, precise prompt conventions, and accurate mapping of PocketFlow semantics make it a higher-fidelity representation of a non-trivial workflow. The added density is justified — a spec that loses behavioral nuance for readability fails its primary purpose.

### 2. Improvements to File 2

- **Add dynamic routing**: If the target code actually has LLM-driven loop exit (not just a counter), this must be reflected. Replace the fixed-loop description with an `EVALUATE` step that can route back or finalize.
- **Enrich prompt conventions**: Specify exact output formats (YAML keys, delimiters, expected field names). "Concise bullet-point list" is too vague for reliable regeneration.
- **Document the dual-mode synthesizer**: `assess_and_report` should describe both gap-analysis mode and final-report mode, not just the latter.
- **Clarify the dual-counter semantics**: Explain why both `loop_count` and `iteration` exist and when they diverge.

### 3. Hybrid Approach

Take File 1 as the base and incorporate from File 2:
- The explicit `EXCEPTION` row in the construct table with the mock-fallback strategy.
- The `temperature 0.7` and model-specific details as implementation notes.
- The slightly cleaner Section 3 formatting (bold headers without nested lists).
- The dual-counter safeguard as an additional defensive detail in Section 4.

---

## Scoring

| Dimension | File 1 | File 2 |
|---|---|---|
| **Structure** | 8/10 | 7/10 |
| **Logic** | 9/10 | 6/10 |
| **Quality** | 9/10 | 7/10 |
| **Overall** | **9/10** | **7/10** |

The 2-point gap on Logic is the critical differentiator: File 1 captures adaptive LLM-driven routing while File 2 reduces it to a fixed loop, which is a material loss of behavioral information. File 2's advantages (readability, explicit exception handling) are real but incremental — they're easy to graft onto File 1's stronger foundation.
---

## Mechanical Diff (Unified Style)

```diff
--- a/S1-research-openrouter-qwen-1-spec.md
+++ b/S5-research-openrouter-qwen-2-spec.md
@@ -1,36 +1,39 @@
 ## 0. High-level Description

-This `WORKFLOW` implements a recursive map-reduce research orchestration that iteratively plans web searches, gathers factual snippets in parallel, and synthesizes a comprehensive markdown report. It begins by invoking `GENERATE plan_queries` to produce a structured list of search objectives, then executes `CALL search_web` for each query followed by `GENERATE extract_facts` to distill raw results into a shared `@notes` buffer. Control flow is governed by a `WHILE @iteration_count < 2` refinement loop, where `EVALUATE @synthesis_action` routes execution back to the planner on `"research"` or terminates with `RETURN @report WITH status=complete` when `"finalize"` is triggered. The `CREATE FUNCTION assess_and_report` dynamically switches between gap-analysis and final-document generation based on accumulated context, while strict YAML parsing ensures reliable LLM-to-code transitions across multiple inference providers. Side effects include persistent file I/O for the final deliverable and console progress logging, and `EXCEPTION` handling is delegated to the underlying HTTP client and LLM shim, surfacing network or quota failures as immediate workflow halts.

+This workflow implements an iterative research-and-synthesis pipeline orchestrated via a structured `WHILE` loop that executes exactly two research cycles. It begins by invoking a `CREATE FUNCTION` for query planning to generate targeted search prompts, followed by a `GENERATE` call to an OpenRouter-hosted Qwen model. The system then performs a side-effect `CALL` to a web search tool, feeding the raw results into a second `GENERATE` function that extracts and consolidates factual notes into shared memory. After the loop condition evaluates to false, a final `GENERATE` step synthesizes the aggregated findings into a comprehensive deliverable using a dedicated assessment prompt, which is immediately persisted to disk via a second side-effect `CALL`. The pipeline incorporates robust exception handling for network or API failures by gracefully falling back to deterministic mock outputs, and concludes by `RETURN`ing the finalized report with an explicit completion status. Multi-step state accumulation occurs within a shared variable context, ensuring that research findings compound across iterations before final synthesis.

 

 ## 1. Purpose

-This implementation autonomously researches a user-specified topic by iteratively generating targeted web queries, extracting concise factual summaries, and refining the scope until a comprehensive markdown report is synthesized and saved.

+This implementation automates a multi-iteration web research and fact-extraction pipeline to generate, consolidate, and persist a structured final report on a user-specified topic.

 

 ## 2. SPL ↔ Python Construct Mapping

 | SPL Construct | Python Equivalent | Notes |

 |---|---|---|

-| `WORKFLOW` | `create_deep_research_flow()` + `Flow(start=planner)` | Defines the node chain, shared context, and routing edges |

-| `CREATE FUNCTION` | Prompt strings inside `PlannerNode.exec`, `ResearcherNode.exec`, `SynthesizerNode.exec` | Reusable templates with `{topic}`, `{feedback}`, `{notes}` interpolation slots |

-| `GENERATE` | `call_llm(prompt)` inside each node | LLM inference call; results parsed from YAML blocks into `@queries`, `@notes`, `@report` |

-| `CALL` (tool) | `search_web(query)`, `Path(out).write_text(...)` | External side-effects: DuckDuckGo HTTP search and markdown file persistence |

-| `WHILE` / `EVALUATE` | `SynthesizerNode.post` returning `"research"` vs `"finalize"`, `shared["loop_count"] < 2` | Branches back to planner on gap feedback or exits when sufficient data/max iterations reached |

-| `RETURN` (non-trivial) | `return "research"` / `return "finalize"` in `post()` | Explicit status tokens that override implicit linear progression and drive loop termination or routing |

-| Shared State (`@var`) | `shared` dictionary passed through `prep`/`post` | Mutable context carrying `@topic`, `@current_queries`, `@notes`, `@loop_count`, `@feedback`, `@report` |

+| `WORKFLOW` | `S3ResearchOpenrouterQwenFlow` class + `run()` method | Encapsulates orchestration lifecycle and mutable `self.state` |

+| `CREATE FUNCTION` | `_plan_queries_prompt`, `_extract_facts_prompt`, `_assess_and_report_prompt` | Pure template builders that inject `{param}` slots into fixed system prompts |

+| `GENERATE` | `_llm_generate(prompt)` | Wraps OpenRouter HTTP POST (Qwen model) with temperature `0.7` |

+| `CALL` (tool) | `_search_web()`, `_write_file()` | External I/O operations for DuckDuckGo scraping and filesystem persistence |

+| `WHILE` | `while self.state["loop_count"] < 2 and self.state["iteration"] < 3:` | Drives the bounded research loop with dual counter safeguards |

+| Shared State (`@var`) | `self.state` dict | Acts as workflow memory (`@topic`, `@notes`, `@report`, etc.) across steps |

+| `EXCEPTION` | `try...except` in `_llm_generate()` | Catches API/network errors and safely routes to deterministic mock fallbacks |

+| `RETURN` | `return self.state["report"]` | Terminates the workflow and delivers the synthesized artifact with a logged `status = "complete"` |

 

 ## 3. Logical Functions / Prompts

-- **Name**: `plan_queries`

-  - **Role in workflow**: Generates the initial or gap-filling search strategy to guide information gathering.

-  - **Key prompt conventions**: Enforces strict YAML output with `queries:` list; conditionally injects `feedback` string from previous synthesis when gaps are detected; expects exactly three diverse query strings.

-- **Name**: `extract_facts`

-  - **Role in workflow**: Maps raw web search snippets into concise, query-relevant insights for downstream aggregation.

-  - **Key prompt conventions**: Input formatted as `Query: ... \n Search result: ...`; instructs extreme brevity; outputs plain text prefixed with `Q: ... Facts: ...` for clean list extension.

-- **Name**: `assess_and_report`

-  - **Role in workflow**: Evaluates research completeness, identifying knowledge gaps or triggering final document generation.

-  - **Key prompt conventions**: Forces YAML with `action: research|finalize` and corresponding `feedback:` or `content:` keys; uses `\n---\n` as delimiter when injecting `@notes` context; bypasses LLM evaluation and forces `action: finalize` if `@loop_count >= 2`.

+**`plan_queries`**

+- **Role:** Initiates the research phase by generating targeted, high-yield search strings for a given topic.

+- **Key prompt conventions:** Instructs the LLM to act as a research planner, mandates exactly 3 queries, and enforces a strict line-by-line `QUERY: ` prefix for reliable downstream regex extraction.

+

+**`extract_facts`**

+- **Role:** Distills raw, unstructured web search snippets into structured, high-signal knowledge.

+- **Key prompt conventions:** Directs the LLM to filter noise, output only the most critical findings, and format them as a concise bullet-point list for clean state accumulation.

+

+**`assess_and_report`**

+- **Role:** Synthesizes all accumulated iteration notes into a polished, actionable final deliverable.

+- **Key prompt conventions:** Commands the LLM to organize aggregated data logically, eliminate redundancy, ensure clarity, and emphasize actionable takeaways without requiring additional formatting constraints.

 

 ## 4. Control Flow

-The workflow initializes shared context with `@topic` and immediately executes `GENERATE plan_queries` to populate `@current_queries`. These queries undergo parallel processing: each triggers `CALL search_web` followed by `GENERATE extract_facts`, with outputs aggregated into the `@notes` list. The orchestrator then evaluates the synthesis result; if `EVALUATE @synthesis_action` yields `"research"` and `@loop_count < 2`, the loop increments, stores the gap description in `@feedback`, and routes execution back to the planning step. When `EVALUATE` returns `"finalize"` (either by LLM judgment or forced by the iteration limit), the workflow halts the `WHILE` loop, `RETURN`s the generated markdown in `@report WITH status=complete, iterations=@loop_count`, and triggers the final file-write side effect before terminating.

+The workflow initializes by binding the user-provided `@topic` to shared state and zeroing iteration counters. It immediately enters a `WHILE` loop governed by the compound condition `@loop_count < 2 AND @iteration < 3`, guaranteeing exactly two research passes. During each iteration, the system chains a `plan_queries` generation, a web search `CALL`, and an `extract_facts` generation, appending the distilled findings to the `@notes` accumulator. Once the loop condition evaluates to false, execution exits the iterative phase and triggers a single terminal `GENERATE` call using `assess_and_report`. The resulting `@report` is routed to a `CALL` for disk persistence (`"report.txt"`), after which the workflow terminates by `RETURN`ing the complete string payload to the host process with `status="complete"`.

 

 ## 5. How to Regenerate as SPL

-```

+```bash

 # Step 1 — generate SPL from this spec (Section 0 above as text2spl input)

 spl3 text2spl --description "<paste Section 0 here>" --mode workflow

 

```
---

*Generated by SPL semantic comparison tool*