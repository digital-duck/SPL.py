# File Comparison Report

**Files Compared:**
- File 1: `S1-judge-claude_cli-sonnet-1-spec.md` (.md)
- File 2: `S5-judge-claude_cli-sonnet-2-spec.md` (.md)
- **Timestamp:** 2026-05-04 09:38:13
- **Active Modes:** llm, git-diff

---
## LLM Semantic Analysis

**Adapter:** claude_cli
**Model:** claude-sonnet-4-6

## Summary

Both files spec the same generate-evaluate-retry pattern compiled to PocketFlow, but they represent two different architectural generations. **File 2 (S5) is the stronger document** — it uses a cleaner three-action routing model, a more concrete implementation (specific adapter/model pinned), a real observed run, and a more complete SPL mapping. File 1 (S1) has a semantically contradictory forced-exit design and is more abstract/generic.

---

## Content Analysis

### File 1 Strengths

- **Cleaner Section 0 prose**: One dense paragraph with no fragmentation; easier to ingest as a text2spl input.
- **Detailed node-level retry annotation**: Explicitly calls out `max_retries=3, wait=10s` on each Node constructor — useful for ops/debugging.
- **Cleaner generator/judge prose in Section 3**: Both function descriptions include sentinel token conventions and YAML key contracts.
- **Simpler control flow ASCII art**: Easier to trace at a glance for a two-branch (pass/fail) mental model.

### File 2 Strengths

- **Correct three-action routing**: `"pass"` / `"retry"` / `"max_attempts"` are semantically distinct — no confusion between success-exit and exhaustion-exit.
- **Dedicated `CheckVerdictNode`**: Collapses EVALUATE + WHILE into one node, which is a faithful and defensible PocketFlow factoring with no semantic loss.
- **More complete SPL mapping (Section 2)**: Covers `INPUT`/`OUTPUT` declarations, shared-state initialization, and adapter specifics (`claude_cli`, `MODEL = "claude-sonnet-4-6"`).
- **String sentinel over YAML parsing**: `"VERDICT: PASS" in judgment` is simpler, more robust, and eliminates a class of parse failures.
- **Real observed run**: Provides ground-truth evidence of behavior (`status=pass`, `Attempts=0`, `Score: 9`).
- **More actionable regeneration section**: Multi-step bash with embedded `sed` extraction and concrete adapter flags.
- **PocketFlow UserWarning acknowledged**: Shows awareness of real runtime behavior, not just theoretical spec.

### Common Elements

- Same five-section structure (0–5: description, purpose, mapping table, control flow, regeneration)
- Same core loop: generate → evaluate → check → retry or exit
- Same termination conditions: score ≥ 7 (pass) or 3 attempts (max_attempts)
- Same shared-state model (`shared` dict as SPL variable namespace)
- Same SPL construct vocabulary (`WORKFLOW`, `CREATE FUNCTION`, `GENERATE … INTO`, `EVALUATE`, `WHILE`, `RETURN … WITH status=`)

---

## Detailed Comparison

### Structure & Organization

| Dimension | File 1 | File 2 |
|---|---|---|
| Section 0 length | Single long paragraph (tight) | Two shorter paragraphs (split by node grouping) |
| Mapping table depth | 11 rows, covers core constructs | 14 rows, adds `INPUT`, `OUTPUT`, init, adapter row |
| Control flow diagram | Clean two-branch vertical flow | Loop-unrolled diagram with inline note |
| Section 5 fidelity | Generic placeholder commands | Concrete, runnable multi-step pipeline |

File 2's mapping table is meaningfully more complete. File 1's control flow diagram is easier to read at a glance. File 2's loop-unrolled diagram is more accurate but visually busier.

### Logic & Completeness

**Critical flaw in File 1**: The max-attempts exit forces `action = "pass"` even when `status="max_attempts"`. This conflates two semantically different outcomes under one PocketFlow action string — a reader implementing from this spec would wire the "pass" edge incorrectly to handle both success and exhaustion.

```
# File 1 — ambiguous: "pass" means both quality-pass AND max-attempts
if shared["attempts"] >= 3:
    ...
    action = "pass"   ← forced exit   ← SAME action as quality pass
```

File 2 correctly defines three terminal states and uses separate action strings:

```
# File 2 — unambiguous
return "pass"          # quality success
return "retry"         # loop back
return "max_attempts"  # exhaustion
```

File 2 also documents the `@feedback := @judgment` assignment (the full judgment string as feedback, not just a `feedback:` field), which is a meaningful behavioral difference that File 1 obscures under YAML key extraction.

### Quality & Sophistication

File 1 is more theoretical — it references "OpenAI gpt-4o or Gemini gemini-2.0-flash, selected at runtime" without pinning anything. File 2 is implementation-ready: `MODEL = "claude-sonnet-4-6"`, `subprocess.run(["claude", "-p", ...])`, specific adapter.

File 2 includes an empirical validation note (observed run on 2026-05-04) that turns a spec into a verified artifact. This is the difference between documentation and verified documentation.

File 1's YAML-fenced output contract for both nodes introduces a parse-failure risk. File 2 uses YAML for the generator (simpler output) and a structured sentinel line for the judge — correctly applying structure only where routing depends on it.

### Syntax & Technical Accuracy

- **File 1**: The SPL pseudocode `RETURN @draft WITH status="max_attempts"` is correct in intent but the Python mapping entry (`action = "pass"`) directly contradicts it. This is a spec-to-implementation inconsistency.
- **File 2**: SPL pseudocode and Python mapping are consistent throughout. The `"max_attempts"` action string appears in both layers.
- **File 2** correctly notes the PocketFlow UserWarning on the PASS path as cosmetic/expected — demonstrating execution awareness.
- Both files use consistent markdown formatting, fenced code blocks, and table syntax.

---

## Recommendations

**1. Best Choice**: File 2 (S5). The three-action routing model is architecturally correct and implementable without ambiguity. The concrete adapter/model pinning and observed run make it a verified spec rather than a design document.

**2. Improvements for File 1**:
- Fix the forced-exit ambiguity: introduce a separate `"max_attempts"` action and register it as a terminal successor.
- Add `INPUT`/`OUTPUT` and initialization rows to the mapping table.
- Pin the adapter/model rather than leaving it as a runtime choice in the spec.
- Replace the YAML verdict schema with a string sentinel — or at minimum note that YAML parse failure is an unhandled exception path.
- Add an observed-run annotation once the workflow is executed.

**3. Hybrid Approach**: Take File 2 as the base and backport two elements from File 1:
- Restore the **node-level retry annotation** (`max_retries=3, wait=10s`) in Section 2 — File 2 drops this entirely.
- Adopt File 1's **clean two-branch vertical ASCII diagram** as a companion to File 2's loop-unrolled version, since the simpler diagram aids first-read comprehension.
- Merge File 1's tighter **Section 3 function descriptions** (sentinel conventions explicitly called out) into File 2's Section 3, which currently omits the YAML contract for the generator node.

---

## Scoring

| Dimension | File 1 / 10 | File 2 / 10 |
|---|---|---|
| **Structure** | 7 | 8 |
| **Logic** | 5 | 9 |
| **Quality** | 6 | 9 |
| **Overall** | **6** | **8.5** |

File 1's logic score is pulled down significantly by the `action = "pass"` forced-exit contradiction, which would produce a silent bug if implemented literally. File 2 loses half a point on structure only because its loop-unrolled control flow diagram is harder to scan than File 1's cleaner two-branch layout.
---

## Mechanical Diff (Unified Style)

```diff
--- a/S1-judge-claude_cli-sonnet-1-spec.md
+++ b/S5-judge-claude_cli-sonnet-2-spec.md
@@ -1,104 +1,106 @@
 ## 0. High-level Description

 

-This workflow implements an evaluator-optimizer loop using the LLM-as-Judge pattern to iteratively generate and refine product descriptions. A `Generator` function (CREATE FUNCTION) takes a product task and optional prior feedback as inputs, calling the LLM (GENERATE) to produce a 2–3 sentence description in YAML-fenced format; on subsequent iterations it incorporates structured feedback from the previous failed attempt. A `Judge` function (CREATE FUNCTION) receives the draft and calls the LLM (GENERATE) to rate clarity and persuasiveness on a 1–10 scale, returning a YAML-fenced object containing `score`, `reasoning`, `verdict`, and `feedback` fields. Control flow is expressed as a WHILE loop (WHILE attempts < 3 AND score < 7) with an EVALUATE branch on the verdict field: when verdict equals "PASS" or score >= 7, the loop exits and the workflow RETURNs the accepted description WITH status="pass", score, and iteration count; otherwise the Judge stores its feedback into shared state (@feedback), increments @attempts, and the loop routes back to the Generator. A hard-coded max-attempts guard of 3 forces a terminal RETURN WITH status="max_attempts" if the quality threshold is never reached, ensuring the workflow always terminates. The implementation uses a single LLM provider (OpenAI gpt-4o or Gemini gemini-2.0-flash, selected at runtime) and writes the final result to an optional file via a CALL side-effect; no explicit EXCEPTION handler is defined, relying on node-level retry logic (max_retries=3, wait=10s) for transient LLM failures.

+This workflow implements a generate-evaluate-retry quality loop using three nodes wired into a compact graph. Two `CREATE FUNCTION` prompts are defined: `generate_draft` asks the LLM to produce a high-quality description of a task, incorporating prior judge feedback when provided; `evaluate_draft` asks a judge LLM to score the draft 1–10 and emit either `VERDICT: PASS` (score ≥ 7) or `VERDICT: FAIL` (score < 7) with actionable feedback. Rather than splitting the SPL's EVALUATE and WHILE into separate PocketFlow nodes, the compiled code merges both into `CheckVerdictNode`, which inspects the `"VERDICT: PASS"` sentinel in the judgment string, updates `@attempts` and `@feedback`, and returns one of three actions: `"pass"` (early success exit), `"retry"` (loop back to `GenerateDraftNode` for refinement), or `"max_attempts"` (exhaustion exit after 3 attempts). The back-edge `check - "retry" >> generate` implements the WHILE loop. Both `"pass"` and `"max_attempts"` are terminal actions with no registered successors — PocketFlow emits a `UserWarning: Flow ends: 'pass' not found in ['retry']` on the PASS path, which is cosmetic and expected. The workflow terminates by populating `@final_description`, `@final_score`, and `@status` in `shared`.

 

 ---

 

 ## 1. Purpose

 

-Automatically produce a high-quality product description by running an LLM generator/judge loop that refines drafts based on structured feedback until a clarity-and-persuasiveness score of 7/10 or higher is achieved (or 3 attempts are exhausted).

+Produces a high-quality description for a given task by iterating a generate-judge loop: the LLM writes a draft, a judge scores it, and the draft is refined with feedback until it passes (score ≥ 7) or 3 attempts are exhausted.

 

 ---

 

-## 2. SPL ↔ Python Construct Mapping

+## 2. SPL ↔ Python — PocketFlow Construct Mapping

 

-| SPL Construct | Python Equivalent | Notes |

+| SPL Construct | Python — PocketFlow Equivalent | Notes |

 |---|---|---|

-| `WORKFLOW judge_optimizer` | `create_judge_flow()` + `Flow.run(shared)` | Entire flow object and its `run()` call constitute the workflow entry point |

-| `CREATE FUNCTION generator` | `Generator(Node)` class (`prep` + `exec` + `post`) | `prep` reads shared state; `exec` builds and calls the prompt; `post` writes back to shared |

-| `CREATE FUNCTION judge` | `Judge(Node)` class (`prep` + `exec` + `post`) | Same three-phase pattern |

-| `GENERATE generator(task, feedback) INTO @draft` | `call_llm(prompt)` inside `Generator.exec`, result written to `shared["draft"]` in `post` | YAML fencing is the structured output contract |

-| `GENERATE judge(draft) INTO @evaluation` | `call_llm(prompt)` inside `Judge.exec`, parsed dict returned | Score, verdict, and feedback fields extracted from YAML block |

-| `WHILE attempts < 3 AND score < 7 DO` | `judge - "fail" >> generator` edge + attempts counter in `Judge.post` | PocketFlow graph routing; loop termination encoded in edge action string |

-| `EVALUATE @verdict WHEN contains('PASS')` | `if verdict.upper() == "PASS" or score >= 7` in `Judge.post` | Returns `"pass"` or `"fail"` action string to drive routing |

-| `RETURN @draft WITH status="pass", score=, iterations=` | `shared["final_description"]`, `shared["final_score"]` set before returning `"pass"` | Caller reads these keys from `shared` after `flow.run()` |

-| `RETURN @draft WITH status="max_attempts"` | `if shared["attempts"] >= 3: ... return "pass"` | Forced exit with below-threshold score still uses the `"pass"` action |

-| `CALL write_file(path, content)` | `Path(out).write_text(...)` in `main.py` | Conditional side-effect; only executed when `--out` flag is provided |

-| `EXCEPTION WHEN RetryError` | `max_retries=3, wait=10` on each `Node` constructor | PocketFlow built-in retry; no explicit `EXCEPTION WHEN` block in user code |

-| Shared state (`@var`) | `shared` dict passed through every `prep`/`post` | Single mutable dict acts as the SPL variable namespace across all nodes |

+| `WORKFLOW judge_workflow` | `build_flow() → Flow(start=generate)` | Three-node graph; back-edge implements the retry loop |

+| `INPUT @task TEXT` | `shared["task"]` set before `Flow.run()` | Read-only throughout |

+| `OUTPUT @final_description TEXT` | `shared["final_description"]` written by `CheckVerdictNode.post()` | Returned in `run_judge_workflow()` result dict |

+| `@feedback := ""; @attempts := 0; ...` | `run_judge_workflow()` initialises `shared` dict | Also pre-seeds `"draft"`, `"judgment"`, `"final_score"`, `"status"` |

+| `GENERATE generate_draft(@task, @feedback) INTO @draft` | `GenerateDraftNode.exec()` → `_generate_draft(task, feedback)` → `_call_llm(...)` | Re-called on every retry with updated `@feedback` |

+| `GENERATE evaluate_draft(@task, @draft) INTO @judgment` | `EvaluateDraftNode.exec()` → `_evaluate_draft(task, draft)` → `_call_llm(...)` | Always called after `GenerateDraftNode` |

+| `EVALUATE @judgment WHEN contains("VERDICT: PASS")` | `"VERDICT: PASS" in judgment` in `CheckVerdictNode.exec()` | String sentinel; no LLM re-evaluation needed |

+| `@final_description := @draft; RETURN WITH status="pass"` | `CheckVerdictNode.post()` returns `"pass"` (terminal), sets `shared["status"]="pass"` | `"pass"` has no outgoing edge → flow ends |

+| `@attempts := @attempts + 1; @feedback := @judgment` | `CheckVerdictNode.post()` updates `shared["attempts"]` and `shared["feedback"]` | Only reached on FAIL path |

+| `WHILE @attempts < 3 DO ... END` | `check - "retry" >> generate` back-edge; guard `if attempts < MAX_ATTEMPTS: return "retry"` | `MAX_ATTEMPTS = 3`; loop body is the full generate→evaluate→check path |

+| `RETURN @final_description WITH status="max_attempts"` | `CheckVerdictNode.post()` returns `"max_attempts"` (terminal), sets `shared["status"]="max_attempts"` | Final draft and judgment stored even on exhaustion |

+| `CREATE FUNCTION generate_draft` | `_generate_draft(task, feedback)` module-level helper | Prompt template inlined as f-string |

+| `CREATE FUNCTION evaluate_draft` | `_evaluate_draft(task, draft)` module-level helper | Structured sentinel output: `VERDICT: PASS/FAIL, Score: N, Feedback: ...` |

+| Adapter: `claude_cli`, model: `sonnet` | `subprocess.run(["claude", "-p", prompt, "--model", MODEL, "--output-format", "text"])` | `MODEL = "claude-sonnet-4-6"` constant |

 

 ---

 

 ## 3. Logical Functions / Prompts

 

-### `generator`

-- **Role**: Drafts a 2–3 sentence product description for a given task; incorporates structured feedback when revising a prior rejected draft.

-- **Key prompt conventions**:

-  - Conditional feedback block appended only when `shared["feedback"]` is non-empty.

-  - Sentinel tokens: ` ```yaml ` / ` ``` ` fence wrapping a single `description:` key.

-  - Output format: YAML block parsed with `yaml.safe_load`; `.strip()` applied to the scalar value.

+### `generate_draft`

+- **Role:** Writer LLM. Produces a clear, detailed, well-structured description of `@task`. On retries, receives the judge's full `@feedback` as context for improvement.

+- **Output:** Free-form prose; no structured format. Instructed not to repeat the task verbatim.

 

-### `judge`

-- **Role**: Evaluates the current draft on a 1–10 scale for clarity and persuasiveness; produces a structured verdict with improvement feedback.

-- **Key prompt conventions**:

-  - Scoring rubric embedded in prompt: "1–10 for clarity and persuasiveness."

-  - Sentinel tokens: ` ```yaml ` / ` ``` ` fence wrapping four keys: `score` (int), `reasoning` (str), `verdict` ("PASS"/"FAIL"), `feedback` (str, populated only on FAIL).

-  - Pass threshold is defined in prose inside the prompt comment (`# Use "PASS" if score >= 7`), making it a soft contract; hard enforcement is done in `Judge.post`.

+### `evaluate_draft`

+- **Role:** Judge LLM. Scores the draft 1–10 on accuracy, clarity, completeness, and overall quality.

+- **Output:** Structured sentinel line: `VERDICT: PASS, Score: N, Feedback: <comment>` (score ≥ 7) or `VERDICT: FAIL, Score: N, Feedback: <actionable suggestions>` (score < 7). The `VERDICT:` prefix is the routing token parsed by `CheckVerdictNode`.

 

 ---

 

 ## 4. Control Flow

 

 ```

-START

-  │

-  ▼

-GENERATE generator(task, feedback="") INTO @draft          ← first iteration, no feedback

-  │

-  ▼

-GENERATE judge(@draft) INTO @evaluation

-  │

-  ▼

-EVALUATE @evaluation.verdict

-  WHEN "PASS" OR score >= 7  ──────────────────────────────► RETURN @draft

-  THEN                                                         WITH status="pass",

-       shared["final_description"] = draft                         score=@evaluation.score

-       shared["final_score"] = score

-       action = "pass"

-  │

-  ELSE (verdict == "FAIL" AND score < 7)

-       shared["attempts"] += 1

-       shared["feedback"] = evaluation.feedback

-       │

-       IF attempts >= 3  ──────────────────────────────────► RETURN @draft

-       THEN                                                    WITH status="max_attempts",

-            shared["final_description"] = draft                    score=@evaluation.score

-            shared["final_score"] = score

-            action = "pass"   ← forced exit

-       │

-       ELSE

-            action = "fail"

-            │

-            ▼

-       WHILE action == "fail" DO

-            GENERATE generator(task, @feedback) INTO @draft

-            ...loop back to EVALUATE

-       END

-  END

+INPUT @task TEXT

+@feedback ← ""; @attempts ← 0

+

+GENERATE generate_draft(@task, @feedback) INTO @draft        [LLM — writer]

+GENERATE evaluate_draft(@task, @draft) INTO @judgment        [LLM — judge]

+

+EVALUATE @judgment

+  WHEN contains("VERDICT: PASS") THEN

+    @final_description := @draft

+    RETURN status="pass"  ──────────────────────────────────────────── ✓ (early exit)

+  ELSE

+    @attempts := 1; @feedback := @judgment

+END

+

+── WHILE @attempts < 3 ─────────────────────────────────────────────────

+│

+│  GENERATE generate_draft(@task, @feedback) INTO @draft      [LLM — writer]

+│  GENERATE evaluate_draft(@task, @draft) INTO @judgment      [LLM — judge]

+│

+│  EVALUATE @judgment

+│    WHEN contains("VERDICT: PASS") THEN

+│      @final_description := @draft

+│      RETURN status="pass"  ──────────────────────────────────────── ✓

+│    ELSE

+│      @attempts += 1; @feedback := @judgment

+│      if @attempts >= 3 →  @final_description := @draft

+│                            RETURN status="max_attempts"  ────────── ~

+│      else → continue

+│  END

+│

+└────────────────────────────────────────────────────────────────────────

 ```

 

-Termination is guaranteed by the attempt counter; the WHILE resolves to either a quality-pass RETURN or a max-attempts RETURN, both with `status` metadata.

+**Note:** `CheckVerdictNode` collapses the SPL's separate EVALUATE and WHILE into one node, so the pre-WHILE initial attempt and the WHILE body share identical generate→evaluate→check logic — this is a compile-time factoring, not a semantic change.

+

+**Observed run (2026-05-04):** Task `"explain quantum entanglement for a high-school student"` → `status=pass`, `Attempts=0` (first draft passed, no retries needed). Judge awarded Score: 9 with positive feedback.

+

+*Note: `Attempts: 0` in the output reflects the counter value at pass-time — the counter is only incremented on FAIL, so a first-try pass leaves it at 0.*

 

 ---

 

 ## 5. How to Regenerate as SPL

 

 ```bash

-# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)

-spl3 text2spl --description "<paste Section 0 here>" --mode workflow

+# Step 1 — regenerate SPL from this spec

+spl3 text2spl --description "$(sed -n '/^## 0\./,/^---/p' S5-judge-claude_cli-sonnet-2-spec.md)" \

+    --mode workflow --adapter claude_cli

 

-# Step 2 — compile to any target

-spl3 splc compile <output.spl> --lang python/pocketflow

-spl3 splc compile <output.spl> --lang python/langgraph

-spl3 splc compile <output.spl> --lang go

-```
+# Step 2 — run

+spl3 run judge_workflow.spl --adapter claude_cli \

+    --param task="explain quantum entanglement for a high-school student"

+

+# Step 3 — recompile to any target

+spl3 splc compile judge_workflow.spl --lang python/pocketflow --llm \

+    --adapter claude_cli --model sonnet

+spl3 splc compile judge_workflow.spl --lang python/langgraph

+spl3 splc compile judge_workflow.spl --lang go

+```

```
---

*Generated by SPL semantic comparison tool*