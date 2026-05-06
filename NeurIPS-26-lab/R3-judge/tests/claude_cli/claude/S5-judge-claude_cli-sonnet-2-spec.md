## 0. High-level Description

This workflow implements a generate-evaluate-retry quality loop using three nodes wired into a compact graph. Two `CREATE FUNCTION` prompts are defined: `generate_draft` asks the LLM to produce a high-quality description of a task, incorporating prior judge feedback when provided; `evaluate_draft` asks a judge LLM to score the draft 1–10 and emit either `VERDICT: PASS` (score ≥ 7) or `VERDICT: FAIL` (score < 7) with actionable feedback. Rather than splitting the SPL's EVALUATE and WHILE into separate PocketFlow nodes, the compiled code merges both into `CheckVerdictNode`, which inspects the `"VERDICT: PASS"` sentinel in the judgment string, updates `@attempts` and `@feedback`, and returns one of three actions: `"pass"` (early success exit), `"retry"` (loop back to `GenerateDraftNode` for refinement), or `"max_attempts"` (exhaustion exit after 3 attempts). The back-edge `check - "retry" >> generate` implements the WHILE loop. Both `"pass"` and `"max_attempts"` are terminal actions with no registered successors — PocketFlow emits a `UserWarning: Flow ends: 'pass' not found in ['retry']` on the PASS path, which is cosmetic and expected. The workflow terminates by populating `@final_description`, `@final_score`, and `@status` in `shared`.

---

## 1. Purpose

Produces a high-quality description for a given task by iterating a generate-judge loop: the LLM writes a draft, a judge scores it, and the draft is refined with feedback until it passes (score ≥ 7) or 3 attempts are exhausted.

---

## 2. SPL ↔ Python — PocketFlow Construct Mapping

| SPL Construct | Python — PocketFlow Equivalent | Notes |
|---|---|---|
| `WORKFLOW judge_workflow` | `build_flow() → Flow(start=generate)` | Three-node graph; back-edge implements the retry loop |
| `INPUT @task TEXT` | `shared["task"]` set before `Flow.run()` | Read-only throughout |
| `OUTPUT @final_description TEXT` | `shared["final_description"]` written by `CheckVerdictNode.post()` | Returned in `run_judge_workflow()` result dict |
| `@feedback := ""; @attempts := 0; ...` | `run_judge_workflow()` initialises `shared` dict | Also pre-seeds `"draft"`, `"judgment"`, `"final_score"`, `"status"` |
| `GENERATE generate_draft(@task, @feedback) INTO @draft` | `GenerateDraftNode.exec()` → `_generate_draft(task, feedback)` → `_call_llm(...)` | Re-called on every retry with updated `@feedback` |
| `GENERATE evaluate_draft(@task, @draft) INTO @judgment` | `EvaluateDraftNode.exec()` → `_evaluate_draft(task, draft)` → `_call_llm(...)` | Always called after `GenerateDraftNode` |
| `EVALUATE @judgment WHEN contains("VERDICT: PASS")` | `"VERDICT: PASS" in judgment` in `CheckVerdictNode.exec()` | String sentinel; no LLM re-evaluation needed |
| `@final_description := @draft; RETURN WITH status="pass"` | `CheckVerdictNode.post()` returns `"pass"` (terminal), sets `shared["status"]="pass"` | `"pass"` has no outgoing edge → flow ends |
| `@attempts := @attempts + 1; @feedback := @judgment` | `CheckVerdictNode.post()` updates `shared["attempts"]` and `shared["feedback"]` | Only reached on FAIL path |
| `WHILE @attempts < 3 DO ... END` | `check - "retry" >> generate` back-edge; guard `if attempts < MAX_ATTEMPTS: return "retry"` | `MAX_ATTEMPTS = 3`; loop body is the full generate→evaluate→check path |
| `RETURN @final_description WITH status="max_attempts"` | `CheckVerdictNode.post()` returns `"max_attempts"` (terminal), sets `shared["status"]="max_attempts"` | Final draft and judgment stored even on exhaustion |
| `CREATE FUNCTION generate_draft` | `_generate_draft(task, feedback)` module-level helper | Prompt template inlined as f-string |
| `CREATE FUNCTION evaluate_draft` | `_evaluate_draft(task, draft)` module-level helper | Structured sentinel output: `VERDICT: PASS/FAIL, Score: N, Feedback: ...` |
| Adapter: `claude_cli`, model: `sonnet` | `subprocess.run(["claude", "-p", prompt, "--model", MODEL, "--output-format", "text"])` | `MODEL = "claude-sonnet-4-6"` constant |

---

## 3. Logical Functions / Prompts

### `generate_draft`
- **Role:** Writer LLM. Produces a clear, detailed, well-structured description of `@task`. On retries, receives the judge's full `@feedback` as context for improvement.
- **Output:** Free-form prose; no structured format. Instructed not to repeat the task verbatim.

### `evaluate_draft`
- **Role:** Judge LLM. Scores the draft 1–10 on accuracy, clarity, completeness, and overall quality.
- **Output:** Structured sentinel line: `VERDICT: PASS, Score: N, Feedback: <comment>` (score ≥ 7) or `VERDICT: FAIL, Score: N, Feedback: <actionable suggestions>` (score < 7). The `VERDICT:` prefix is the routing token parsed by `CheckVerdictNode`.

---

## 4. Control Flow

```
INPUT @task TEXT
@feedback ← ""; @attempts ← 0

GENERATE generate_draft(@task, @feedback) INTO @draft        [LLM — writer]
GENERATE evaluate_draft(@task, @draft) INTO @judgment        [LLM — judge]

EVALUATE @judgment
  WHEN contains("VERDICT: PASS") THEN
    @final_description := @draft
    RETURN status="pass"  ──────────────────────────────────────────── ✓ (early exit)
  ELSE
    @attempts := 1; @feedback := @judgment
END

── WHILE @attempts < 3 ─────────────────────────────────────────────────
│
│  GENERATE generate_draft(@task, @feedback) INTO @draft      [LLM — writer]
│  GENERATE evaluate_draft(@task, @draft) INTO @judgment      [LLM — judge]
│
│  EVALUATE @judgment
│    WHEN contains("VERDICT: PASS") THEN
│      @final_description := @draft
│      RETURN status="pass"  ──────────────────────────────────────── ✓
│    ELSE
│      @attempts += 1; @feedback := @judgment
│      if @attempts >= 3 →  @final_description := @draft
│                            RETURN status="max_attempts"  ────────── ~
│      else → continue
│  END
│
└────────────────────────────────────────────────────────────────────────
```

**Note:** `CheckVerdictNode` collapses the SPL's separate EVALUATE and WHILE into one node, so the pre-WHILE initial attempt and the WHILE body share identical generate→evaluate→check logic — this is a compile-time factoring, not a semantic change.

**Observed run (2026-05-04):** Task `"explain quantum entanglement for a high-school student"` → `status=pass`, `Attempts=0` (first draft passed, no retries needed). Judge awarded Score: 9 with positive feedback.

*Note: `Attempts: 0` in the output reflects the counter value at pass-time — the counter is only incremented on FAIL, so a first-try pass leaves it at 0.*

---

## 5. How to Regenerate as SPL

```bash
# Step 1 — regenerate SPL from this spec
spl3 text2spl --description "$(sed -n '/^## 0\./,/^---/p' S5-judge-claude_cli-sonnet-2-spec.md)" \
    --mode workflow --adapter claude_cli

# Step 2 — run
spl3 run judge_workflow.spl --adapter claude_cli \
    --param task="explain quantum entanglement for a high-school student"

# Step 3 — recompile to any target
spl3 splc compile judge_workflow.spl --lang python/pocketflow --llm \
    --adapter claude_cli --model sonnet
spl3 splc compile judge_workflow.spl --lang python/langgraph
spl3 splc compile judge_workflow.spl --lang go
```
