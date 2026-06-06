# File Comparison Report

**Files Compared:**
- File 1: `S1-agent-openrouter-qwen-1-spec.md` (.md)
- File 2: `S5-agent-openrouter-qwen-2-spec.md` (.md)
- **Timestamp:** 2026-05-04 07:53:25
- **Active Modes:** llm, git-diff

---
## LLM Semantic Analysis

**Adapter:** claude_cli
**Model:** claude-opus-4-6

## Summary

Both files specify a ReAct-style research agent that loops between web search and answer synthesis. **File 2 is the stronger spec** — it introduces explicit loop bounds, a multi-stage YAML validation/repair pipeline, deterministic fallback handling, and a post-loop safety guard, all of which File 1 either omits or handles loosely. File 1 is more concise and reads well as a high-level design document, but it leaves several robustness concerns implicit. File 2 closes those gaps at the cost of some added verbosity.

---

## Content Analysis

### File 1 Strengths
- **Conciseness and clarity.** The description reads as a single coherent narrative without burying the reader in implementation details. The PocketFlow-native framing (`Flow(start=decide)`, node `post()` routing) is idiomatic and easy to map to code.
- **Clean construct mapping.** The SPL↔Python table is tight — each row has a clear 1:1 correspondence. The `WHILE` entry cleverly maps the implicit edge loop to a string-based routing convention, which is faithful to how PocketFlow actually works.
- **Prompt minimalism.** Only two prompts are declared (decide + answer), which is the minimum viable set for a ReAct loop. This reduces LLM call count and keeps the token budget small.

### File 2 Strengths
- **Explicit loop bounding.** Both the outer research loop (`iteration < 3`) and the inner repair loop (`parse_iter < 3`) have hard ceilings, preventing runaway execution — a critical production concern File 1 ignores.
- **Multi-stage validation pipeline.** Five distinct prompt functions (`decide_action`, `validate_yaml`, `repair_output`, `extract_action`, `generate_final`) decompose the problem into single-responsibility stages. This makes each LLM call more predictable and individually testable.
- **Deterministic error recovery.** Network timeouts and API failures are caught with fallback strings (`[MOCK_LLM_RESPONSE]`), keeping the loop alive. File 1's YAML repair is a single heuristic; File 2 uses a dedicated repair prompt plus a binary validator.
- **Post-loop safety guard.** If iteration limits exhaust without an answer, File 2 ensures `@final_response` is populated — File 1 has no equivalent, meaning an unlucky run could terminate with no output.
- **Temperature control noted.** The spec explicitly calls out `temperature=0.1` for deterministic routing, a detail that matters for reproducibility.

### Common Elements
- Both follow the same 6-section structure (Sections 0–5).
- Both use a `WORKFLOW` → `EVALUATE` → `CALL`/`GENERATE` → `RETURN` skeleton.
- Both use DuckDuckGo as the search tool and a shared mutable dictionary for state.
- Both include YAML-based structured output from the decision prompt.
- Both end with identical `spl3` regeneration instructions.
- Both map `EXCEPTION` to some form of YAML repair or error fallback.

---

## Detailed Comparison

### Structure & Organization

| Aspect | File 1 | File 2 |
|---|---|---|
| Section layout | Identical 0–5 structure | Identical 0–5 structure |
| Section 0 length | ~8 sentences, single paragraph | ~8 sentences, single paragraph — slightly denser |
| Construct table rows | 9 rows | 9 rows |
| Prompt inventory | 2 prompts | 5 prompts |
| Section 4 narrative | Linear, single-pass description | Two-level (outer + inner loop) with explicit exit conditions |

File 2's structure mirrors File 1 but adds depth at every section. The inner validation loop is the major structural addition — it introduces a second axis of iteration that File 1 folds into a single `parse_yaml_safely()` utility.

### Logic & Completeness

**Loop termination.** File 1's loop terminates only when the LLM emits `answer`. If the model keeps selecting `search` (a known failure mode with weaker models), the workflow runs indefinitely. File 2 caps this at 3 iterations.

**YAML validation.** File 1 applies a heuristic block-scalar repair and retries parsing — a single synchronous fallback. File 2 separates validation (`validate_yaml`), repair (`repair_output`), and extraction (`extract_action`) into three LLM calls with a bounded retry loop. This is more expensive but far more robust to diverse failure modes.

**Error handling scope.** File 1 handles only YAML parse failures. File 2 additionally handles network timeouts and API errors with deterministic fallback strings, keeping the control flow linear even under infrastructure failures.

**Graceful degradation.** File 2's post-loop guard ensures output is always populated. File 1 assumes the happy path — if the synthesis node never fires, the workflow silently produces nothing.

**Action extraction.** File 1 relies on direct YAML field access after parsing. File 2 uses a dedicated `extract_action` prompt that outputs a single lowercase keyword, adding a normalization layer that reduces sensitivity to formatting variations.

### Quality & Sophistication

File 1 is a **design-level spec** — clean, readable, and sufficient for an experienced developer to implement. It trusts the reader to infer robustness requirements.

File 2 is a **implementation-level spec** — it specifies retry budgets, temperature settings, fallback strings, and validation stages. It's the kind of document you hand to a code generator or a junior developer and expect correct output.

The trade-off: File 2's five-prompt pipeline means 3–5× more LLM calls per iteration than File 1's two-prompt design. For a Qwen model on OpenRouter (where latency and cost matter), this is non-trivial. File 1's minimalism is a legitimate design choice, not just an omission.

### Syntax & Technical Accuracy

**File 1:**
- SPL construct names are consistent (`WORKFLOW`, `CREATE FUNCTION`, `GENERATE`, `CALL`, `EVALUATE`, `WHILE`, `EXCEPTION`, `RETURN`).
- The `WHILE` mapping to PocketFlow's edge-based routing is technically accurate and well-annotated.
- Section 5 code block uses proper `bash` fencing.

**File 2:**
- SPL construct names match File 1's vocabulary plus add `WHEN contains(...)` syntax in `EVALUATE`.
- Python equivalents are more concrete (actual variable names like `ctx["@done"]`, `ctx["@iteration"]`).
- The `WHILE` mapping is more explicit, showing both outer and inner loop conditions.
- Section 5 code block is missing the `bash` language tag on the fence — minor formatting gap.
- One conceptual concern: using an LLM call (`validate_yaml`) just to check YAML syntax is unusual when a deterministic parser (e.g., `yaml.safe_load`) would suffice. The spec doesn't justify this choice.

---

## Recommendations

### 1. Best Choice
**File 2** is the better spec for production use and for driving automated code generation. Its explicit bounds, multi-stage validation, and graceful degradation address real failure modes that arise when running weaker/cheaper models like Qwen through OpenRouter.

Choose File 1 only if you want a minimal reference design or are targeting a high-capability model (e.g., Sonnet) where YAML compliance is near-guaranteed and iteration count is naturally low.

### 2. Improvements to File 1
- **Add iteration cap.** A single sentence in Section 0 and one row in Section 2 (`WHILE` with counter) would close the runaway-loop risk.
- **Add post-loop fallback.** Specify what happens if the loop exhausts without reaching the answer branch.
- **Add network error handling.** The `EXCEPTION` row currently covers only YAML; extend to cover `CALL` failures.
- **Specify temperature.** Note the routing prompt's temperature to ensure deterministic action selection.

### 3. Hybrid Approach
Take File 2's control flow and error handling model, but:
- **Collapse `validate_yaml` + `repair_output` + `extract_action` into a single deterministic parse-and-repair utility** (as File 1 does with `parse_yaml_safely`), reserving the LLM repair prompt only as a last-resort fallback. This cuts 2 LLM calls per iteration.
- **Keep File 2's outer loop bound and post-loop guard.**
- **Adopt File 1's prose style** — File 2's Section 0 is slightly over-specified for a high-level description; compress it.
- **Use File 1's PocketFlow-native framing** in the construct table where the target is PocketFlow, since `Flow(start=decide)` and node `post()` routing are more idiomatic than a flat `run()` method.

---

## Scoring

| Dimension | File 1 | File 2 |
|---|---|---|
| **Structure** | 7/10 | 8/10 |
| **Logic** | 6/10 | 9/10 |
| **Quality** | 7/10 | 8/10 |
| **Overall** | 6.5/10 | 8.5/10 |

File 1 loses points primarily on logic (no loop bound, no post-loop guard, narrow error handling). File 2 loses a point on quality for the questionable LLM-as-YAML-validator design and the additional latency cost of five prompt functions. Both are well-structured and syntactically sound.
---

## Mechanical Diff (Unified Style)

```diff
--- a/S1-agent-openrouter-qwen-1-spec.md
+++ b/S5-agent-openrouter-qwen-2-spec.md
@@ -1,36 +1,44 @@
 ## 0. High-level Description

-This workflow implements a ReAct-style research agent orchestration that iteratively decides between querying external knowledge and synthesizing a final response. It declares a WORKFLOW that delegates all reasoning and synthesis to a unified LLM backend via a configurable adapter shim, ensuring consistent prompt routing regardless of the underlying provider. The orchestration begins by invoking a CREATE FUNCTION decision prompt, which instructs the model to output a structured YAML response selecting either a search or answer action. The workflow uses EVALUATE to branch on the parsed action token: if search, a CALL executes a web search tool and appends results to the shared context before looping back to the decision phase; if answer, a second prompt generates the final text. Shared state variables persist across iterations via a centralized dictionary, while an EXCEPTION handler automatically repairs malformed YAML outputs and retries parsing before halting execution. The graph terminates cleanly when the synthesis node issues a RETURN with status done, materializing the final answer for CLI output and optional file persistence.

+This workflow implements a structured, self-correcting decision agent that iteratively gathers external information before synthesizing a final answer. It begins with `CREATE FUNCTION` templates that prompt the language model to output a YAML routing structure containing an explicit action token. Execution enters a bounded outer `WHILE` loop that tracks step count and a completion flag, ensuring strict iteration limits. Within each cycle, an inner validation `WHILE` loop paired with `EVALUATE` branches checks for YAML syntax; if malformed, it automatically triggers a repair prompt, increments a retry counter, and loops until valid or until the retry ceiling is reached. After validation, a second `EVALUATE` branch inspects the extracted action token: a `search` directive executes a `CALL` side-effect to query DuckDuckGo and appends results to shared memory, while an `answer` directive invokes a synthesis prompt and sets the termination flag. Network timeouts or API errors are intercepted by `EXCEPTION` handlers that inject deterministic fallback strings, preserving linear execution flow without crashing. The workflow concludes with a post-loop safety guard and a `RETURN` statement that delivers the compiled response with a `complete` status.

 

 ## 1. Purpose

-This implementation enables users to ask open-ended research questions and automatically retrieves, evaluates, and synthesizes web search results into a comprehensive final answer through an autonomous LLM agent.

+This implementation provides an autonomous, self-validating research agent that dynamically decides when to query external search engines and when to synthesize accumulated context into a final answer.

 

 ## 2. SPL ↔ Python Construct Mapping

 | SPL Construct | Python Equivalent | Notes |

 |---|---|---|

-| `WORKFLOW` | `pocketflow.Flow(start=decide)` | Defines the directed graph topology and initializes execution at the decision node |

-| `CREATE FUNCTION` | Inline prompt strings in `DecideAction.exec` & `AnswerQuestion.exec` | Parameterized with `{question}` and `{context}` slots for dynamic injection |

-| `GENERATE` | `call_llm(prompt)` | Invokes the LLM API and captures raw text output into a variable |

-| `CALL` | `search_web_duckduckgo(query)` | Side-effect tool execution that fetches external data over HTTP |

-| `EVALUATE` | Conditional routing logic in `DecideAction.post()` | Branches execution path based on the parsed `action` field (`search` vs `answer`) |

-| `WHILE` | `"decide"` edge routing from `SearchWeb` back to `DecideAction` | Implicit loop that repeats the research cycle until the LLM selects the answer action |

-| `EXCEPTION` | `parse_yaml_safely()` fallback in `nodes.py` | Catches YAML parsing failures, applies heuristic block-scalar repairs, and retries |

-| Shared state (`@var`) | `shared` dictionary passed through node lifecycle | Stores `@question`, `@context`, `@search_query`, and `@answer` across steps |

-| `RETURN WITH status=` | `post()` methods returning `"done"`, `"search"`, or `"answer"` | Drives non-trivial routing and explicit workflow termination |

+| `WORKFLOW <name>` | `class S3AgentOpenRouterQwen` + `run()` method | Defines the orchestration container with typed inputs/outputs and manages a shared context dictionary. |

+| `CREATE FUNCTION <name>` | `prompt_decide_action()`, `prompt_validate_yaml()`, `prompt_repair_output()`, `prompt_extract_action()`, `prompt_generate_final()` | Python f-string functions returning prompt templates with `{param}` interpolation slots. |

+| `GENERATE <fn>(...) INTO @<var>` | `generate(prompt_function(...))` | Wraps the OpenRouter API call with system prompts and temperature control, assigning the raw string to `ctx["..."]`. |

+| `CALL <tool>(...) INTO @<var>` | `web_search()` | Executes a DuckDuckGo API call, formats snippets, and returns the structured text to shared state. |

+| `WHILE <cond> DO ... END` | `while not ctx["@done"] and ctx["@iteration"] < 3:` (outer) and `while not ctx["@parse_valid"] and ctx["@parse_iter"] < 3:` (inner) | Iterative loops bounded by boolean flags and integer counters to prevent runaway execution. |

+| `EVALUATE @<var> WHEN contains(...) THEN ... ELSE ... END` | `if "keyword" in ctx["..."].lower():` | Case-insensitive substring matching that routes execution based on LLM-generated validation or routing tokens. |

+| Shared State (`@vars`) | `ctx = {"@user_query": ..., "@shared_state": "", ...}` | A single mutable Python dictionary acting as workflow memory, updated in-place across steps. |

+| `EXCEPTION WHEN <Type> THEN ...` | `try/except` blocks inside `generate()` and `web_search()` | Catches network timeouts/import errors and returns safe fallback strings (`[MOCK_LLM_RESPONSE]`, etc.) so the loop continues. |

+| `RETURN @<var> WITH status="complete"` | `return {"status": "complete", "final_response": ctx["@final_response"]}` | Terminates the workflow and packages the output with a non-trivial status token for downstream consumers. |

 

 ## 3. Logical Functions / Prompts

-**decide_action_prompt**

-- **Role:** Orchestrator/Planner that evaluates the current research gap and selects the next operational mode.

-- **Key prompt conventions:** Enforces strict YAML output with an explicit action space (`search` vs `answer`). Requires `|` block scalars for `thinking`, `reason`, and `answer` fields to prevent syntax breaks from colons or quotes. Includes a parsing retry heuristic for malformed outputs.

-

-**answer_question_prompt**

-- **Role:** Synthesizer/Writer that compiles accumulated research findings into a cohesive, comprehensive response.

-- **Key prompt conventions:** Direct instruction format that explicitly references the original `Question:` and aggregated `Research:` context blocks. Expects unstructured prose output without wrapper tags.

+- **`decide_action`**

+  - **Role:** Routing/Orchestration prompt that determines whether the agent should fetch new data or compile existing context.

+  - **Key Conventions:** Requires YAML output containing an explicit `action` token and an optional `query` field. Low temperature (0.1) enforces deterministic formatting.

+- **`validate_yaml`**

+  - **Role:** Syntax validator for the routing LLM's output.

+  - **Key Conventions:** Strict binary output convention: must return exactly `valid` or `malformed` to drive the inner repair loop.

+- **`repair_output`**

+  - **Role:** Self-correction prompt that fixes broken YAML structures.

+  - **Key Conventions:** Forces strict YAML compliance; expects clean, parseable output on retry without conversational filler.

+- **`extract_action`**

+  - **Role:** Parser/token isolator that pulls the routing directive from validated YAML.

+  - **Key Conventions:** Outputs a single lowercase keyword (`search` or `answer`) for deterministic `EVALUATE` branching.

+- **`generate_final`**

+  - **Role:** Synthesizer that compiles accumulated search results into a coherent, user-facing response.

+  - **Key Conventions:** Consumes full `@shared_state` and original `@user_query`; expects comprehensive prose without YAML artifacts or tool-call syntax.

 

 ## 4. Control Flow

-Execution initializes by populating shared state with the user query and entering the decision phase. The workflow triggers an EVALUATE on the LLM's parsed output: if the action matches `search`, the query variable is updated, a CALL executes the web scraper, and the retrieved snippets are concatenated into the context before routing back to the decision prompt. This forms a WHILE loop that repeats the search-accumulate cycle until the evaluator matches `answer`. At that point, the accumulated context is cached, the synthesis prompt is invoked, and the resulting text is stored in the answer variable. The synthesis node then issues a RETURN with status `done`, which halts the graph and propagates the final payload to the CLI layer for display and optional filesystem persistence.

+Execution initializes the shared context with the user query, empty state, and zeroed iteration/termination counters. The workflow enters a bounded outer `WHILE` loop that persists until `@done` is true or `@iteration` reaches three. Inside, it invokes `GENERATE decide_action` to produce routing YAML, which is immediately validated by an inner `WHILE` loop. This inner loop uses `EVALUATE` to check for a `malformed` token; if detected, it triggers `GENERATE repair_output`, increments the parse counter, and repeats until valid YAML is confirmed or the retry limit is hit. Once validated, `GENERATE extract_action` isolates the routing directive, followed by a second `EVALUATE` branch. If the directive contains `search`, the workflow executes `CALL web_search`, appends the results to `@shared_state`, and increments the outer iteration counter before looping back. If the directive contains `answer`, it invokes `GENERATE generate_final` to produce the output, sets `@done` to true, and exits the loop. A post-loop guard ensures `@final_response` is populated even if iteration limits are reached, finally executing `RETURN @final_response WITH status="complete"` to deliver the result.

 

 ## 5. How to Regenerate as SPL

-```bash

+```

 # Step 1 — generate SPL from this spec (Section 0 above as text2spl input)

 spl3 text2spl --description "<paste Section 0 here>" --mode workflow

 

```
---

*Generated by SPL semantic comparison tool*