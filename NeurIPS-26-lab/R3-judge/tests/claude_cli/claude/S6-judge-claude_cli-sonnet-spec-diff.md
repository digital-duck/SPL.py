# File Comparison Report

**Files Compared:**
- File 1: `S1-judge-claude_cli-sonnet-1-spec.md` (.md)
- File 2: `S5-judge-claude_cli-sonnet-2-spec.md` (.md)
- **Timestamp:** 2026-05-04 09:40:08
- **Active Modes:** llm, git-diff

---
## LLM Semantic Analysis

**Adapter:** claude_cli
**Model:** claude-opus-4-6

## Summary

Both files specify the same **generate→judge→retry** evaluator-optimizer pattern compiled to PocketFlow, but they represent different maturity levels. **File 1 (S1)** is a first-pass spec with a two-node architecture and YAML-fenced output contracts. **File 2 (S5)** is a refined second-pass spec with a three-node architecture, cleaner action semantics, and empirical validation data. File 2 is the stronger spec overall — it is more precise, more self-consistent, and better separates concerns — though File 1 has a few structural qualities worth preserving.

---

## Content Analysis

### File 1 Strengths

- **Structured output contracts**: Both generator and judge use YAML-fenced output (`yaml.safe_load`), giving a formal parsing contract rather than string-sentinel matching. This is more robust against prompt drift.
- **Explicit retry/exception mapping**: Maps PocketFlow's `max_retries=3, wait=10` to `EXCEPTION WHEN RetryError`, making transient failure handling visible in the spec. File 2 omits this entirely.
- **CALL side-effect mapping**: Documents the optional file-write (`--out` flag → `Path(out).write_text(...)`) as a `CALL write_file(path, content)` construct, capturing an I/O side-effect that File 2 ignores.
- **Dual-model mention**: Acknowledges runtime model selection (gpt-4o / gemini-2.0-flash), consistent with the DODA principle of provider-agnostic specs.

### File 2 Strengths

- **Three-node decomposition**: Factoring verdict logic into a dedicated `CheckVerdictNode` separates evaluation from routing, making the architecture cleaner and easier to reason about.
- **Three distinct actions**: `"pass"`, `"retry"`, `"max_attempts"` each carry clear semantic intent. File 1's reuse of `"pass"` for both success and exhaustion exit is confusing and semantically lossy.
- **Empirical validation**: Includes an observed run result (task, score, status, attempt count) with a clarifying note on counter semantics — this grounds the spec in reality.
- **More complete mapping table**: Includes adapter/model row (`subprocess.run(["claude", ...])`) and shared-state initialization row, giving a fuller picture of the compiled artifact.
- **Compile-time factoring note**: Explicitly explains that `CheckVerdictNode` collapses the SPL's EVALUATE + WHILE into one node as a compilation optimization, not a semantic change — important for round-trip fidelity.
- **Better Section 5**: Includes an actual run command with `--param`, references the spec file by name in the `sed` command, and shows a three-step workflow (generate → run → recompile).

### Common Elements

- Same five-section structure (§0–§5): High-level Description → Purpose → Construct Mapping → Control Flow → Regeneration
- Same core pattern: generate draft → judge draft → branch on verdict → retry or exit
- Same termination guarantee: `MAX_ATTEMPTS = 3` hard cap
- Same pass threshold: score ≥ 7
- Same output variables: `@final_description`, `@final_score`, `@status`
- Both use PocketFlow's `shared` dict as the SPL variable namespace
- Both document the `WHILE` loop as a graph back-edge

---

## Detailed Comparison

### Structure & Organization

Both files follow an identical five-section skeleton, which makes comparison straightforward. The sections serve the same purposes and appear in the same order.

**File 1** keeps §0 as a single dense paragraph. It packs every detail (YAML fencing, retry config, model names, file-write side-effect) into one block. This is comprehensive but hard to scan.

**File 2** also uses a single paragraph for §0 but is more focused: it describes the three-node topology, the three actions, the cosmetic warning, and the shared-state contract. It defers implementation details (model constant, subprocess call) to the mapping table where they belong.

**File 2's §4** is more readable — it uses a pseudo-SPL notation with clear WHILE block indentation and annotated exit arrows (`✓`, `~`). File 1's ASCII flowchart mixes Python implementation details (`shared["final_description"] = draft`) into what should be a logical flow diagram, blurring the abstraction level.

### Logic & Completeness

**Verdict routing** is the sharpest logical difference. File 1 reuses `"pass"` as the action for both quality-pass and max-attempts exit:

```
# File 1's confusing reuse
if shared["attempts"] >= 3: ... return "pass"   ← forced exit, not a quality pass
```

This creates ambiguity — the caller cannot distinguish success from exhaustion by action alone and must inspect `shared["status"]`. File 2 uses `"max_attempts"` as a distinct terminal action, making the graph self-documenting.

**Error handling**: File 1 maps `max_retries=3, wait=10` to an SPL `EXCEPTION WHEN RetryError` construct. File 2 says nothing about transient failure recovery. This is a completeness gap in File 2 — a production spec should document retry behavior.

**Side-effects**: File 1 documents the optional file-write as a `CALL`. File 2 omits it. If the compiled code includes this path, File 2 is incomplete.

**State initialization**: File 2 explicitly maps the shared-dict initialization (`@feedback := ""; @attempts := 0; ...`) to a mapping table row. File 1 leaves initialization implicit.

### Quality & Sophistication

**File 2** is more sophisticated in several ways:

1. **Architectural clarity**: Three nodes with single responsibilities vs. two nodes where Judge handles both evaluation and routing.
2. **Self-awareness**: Acknowledges the cosmetic `UserWarning` and explains why it's expected — this saves future maintainers from chasing a false alarm.
3. **Empirical grounding**: The observed-run note in §4 provides a concrete trace that validates the spec against actual behavior.
4. **Counter semantics note**: Explaining that `Attempts: 0` on a first-try pass reflects increment-on-FAIL-only logic prevents a common misreading.

**File 1** shows more sophistication in its output format design: YAML-fenced structured output with `yaml.safe_load` parsing is more robust than File 2's string-sentinel approach (`"VERDICT: PASS" in judgment`). Sentinel-based parsing is fragile if the LLM includes "VERDICT: PASS" in its reasoning text before the actual verdict line.

### Syntax & Technical Accuracy

**File 1**:
- Mapping table is accurate and well-formatted.
- Control flow diagram uses valid ASCII-art but leaks Python-level details (`shared["final_description"]`).
- §5 regeneration commands are generic and don't reference the spec file itself.
- Minor issue: says "Gemini gemini-2.0-flash" (redundant brand prefix).

**File 2**:
- Mapping table is more thorough, includes the `subprocess.run` adapter call.
- Control flow uses a cleaner pseudo-SPL notation.
- §5 uses `sed -n` to extract §0 from the spec file itself — a self-referential pattern that's elegant but fragile (depends on exact heading format).
- Minor issue: the pre-WHILE first attempt and the WHILE body are shown separately in §4, which is slightly redundant — but the closing note explains this is intentional (mirrors the compiled code's structure).

---

## Recommendations

### 1. Best Choice: **File 2 (S5)**

File 2 is the better spec. Its three-node architecture is a cleaner decomposition, its three-action routing is unambiguous, its mapping table is more complete, and its empirical validation adds confidence. The observed-run data and counter-semantics note demonstrate a level of verification absent from File 1.

### 2. Improvements to File 2

| Gap | Fix |
|---|---|
| No retry/exception handling documented | Add a mapping row: `EXCEPTION WHEN RetryError` → `max_retries=N, wait=Ns` on Node constructors (or document if the compiled code omits retries) |
| No file-write side-effect | If the compiled code has an `--out` path, add a `CALL write_file` mapping row; if removed, state explicitly that file output is not part of this version |
| String-sentinel parsing fragility | Consider noting in §3 that the `VERDICT:` prefix must appear as the **first** token on its line, or add a regex guard, to prevent false matches in reasoning text |
| §5 `sed -n` fragility | Add a fallback note: "or paste §0 directly as the `--description` argument" |

### 3. Hybrid Approach

Take File 2 as the base and back-port these from File 1:

- **YAML-fenced output** for the judge function (or at minimum, document the sentinel fragility and mitigation).
- **Retry/exception mapping row** in §2.
- **CALL side-effect row** if the file-write path exists in the compiled code.
- **Provider-agnostic language** in §0 (mention model selection at runtime rather than hardcoding `claude-sonnet-4-6`), consistent with DODA.

---

## Scoring

| Dimension | File 1 (S1) | File 2 (S5) | Notes |
|---|---|---|---|
| **Structure** | 7/10 | 8/10 | Both follow the same skeleton; File 2's §4 is cleaner, §0 is better scoped |
| **Logic** | 6/10 | 8/10 | File 1's `"pass"` reuse for exhaustion is a semantic flaw; File 2's three-action model is correct. File 1 gets credit for retry handling |
| **Quality** | 6/10 | 9/10 | File 2's three-node decomposition, empirical validation, and cosmetic-warning note show a higher level of engineering maturity |
| **Overall** | **6/10** | **8/10** | File 2 is the stronger spec; back-porting retry docs and structured output would bring it to 9+ |
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