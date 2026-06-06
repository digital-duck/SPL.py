## 0. High-level Description

This workflow implements an **adversarial multi-turn debate** pattern in which two LLM personas argue opposing sides of a motion before a neutral judge renders a verdict. Three CREATE FUNCTIONs drive the pattern: `pro_argument` and `con_argument` each receive the motion and the opponent's most recent accumulated history as `{previous}`, instructing the model to argue exclusively for one side (no balanced views) in 3–5 paragraphs; `judge_debate` receives the full accumulated histories for both sides and scores them on argument strength, rebuttal quality, and persuasiveness, ending with an explicit `PRO` or `CON` declaration. The control flow opens with unconditional GENERATE calls for both sides' opening statements, then enters a WHILE loop bounded by `@round < @max_rounds` in which Pro rebuts Con's latest history and Con rebuts Pro's updated history, mirroring a live cross-examination structure. Every generated artifact — opening statements, per-round rebuttals, and the final verdict — is persisted via CALL `write_file` side-effects into a configurable `@log_dir`, and LOGGING statements at INFO and DEBUG levels bracket each phase (start, per-round progress, judge deliberation, verdict ready). Two EXCEPTION handlers provide graceful degradation: `MaxIterationsReached` still invokes `judge_debate` on whatever history was accumulated and RETURNs with `status = 'partial'`, while `BudgetExceeded` aborts immediately and RETURNs the partial pro history with `status = 'budget_limit'`; the happy path RETURNs `@verdict` with `status = 'complete'` and the actual round count as metadata.

---

## 1. Purpose

Simulate a structured debate between two LLM personas arguing for and against a user-supplied motion, then produce a judge's verdict declaring a winner with reasoning.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@topic` | `'AI should be open-sourced'` | The debate motion both sides argue about |
| `@max_rounds` | `3` | Number of rebuttal rounds after opening statements |
| `@log_dir` | `'cookbook/11_debate_arena/logs-spl'` | Directory path where all generated artifacts are written |

---

## 3. Process

1. Initialize `@round` to `0`, `@pro_history` and `@con_history` to empty strings.
2. Log debate start (topic, round count) at INFO level.
3. GENERATE a Pro opening statement via `pro_argument(@topic, 'opening statement')` → `@pro`.
4. GENERATE a Con opening statement via `con_argument(@topic, 'opening statement')` → `@con`.
5. Set `@pro_history := @pro` and `@con_history := @con`.
6. Log "Opening statements complete" at INFO; CALL `write_file` to persist both opening statements to `opening_pro.md` and `opening_con.md`.
7. Enter WHILE loop while `@round < @max_rounds`:
   - Log "Round N | pro rebuttal …" at DEBUG.
   - GENERATE `pro_argument(@topic, @con_history)` → `@pro_rebuttal`; append to `@pro_history` with a `---` separator; CALL `write_file` → `round_N_pro.md`.
   - Log "Round N | con rebuttal …" at DEBUG.
   - GENERATE `con_argument(@topic, @pro_history)` → `@con_rebuttal`; append to `@con_history` with a `---` separator; CALL `write_file` → `round_N_con.md`.
   - Increment `@round`; log "Round N complete" at INFO.
8. Log "All rounds done — judge deliberating …" at INFO.
9. GENERATE `judge_debate(@topic, @pro_history, @con_history)` → `@verdict`.
10. Log "Verdict ready | rounds=N" at INFO; CALL `write_file` → `verdict.md`.
11. RETURN `@verdict` with metadata `status = 'complete'`, `rounds = @round`.

---

## 4. Error Handling

- **`MaxIterationsReached`** — the loop was forcibly stopped before `@max_rounds` completed; the workflow still calls `judge_debate` on the accumulated histories and RETURNs the verdict with `status = 'partial'` (no round count metadata).
- **`BudgetExceeded`** — token or cost budget was exhausted mid-run; the workflow skips judging entirely and RETURNs whatever partial pro history exists with `status = 'budget_limit'`.

---

## 5. Output

| Field | Value |
|---|---|
| Return variable | `@verdict` — the judge's full deliberation text naming PRO or CON as winner with 2–3 paragraphs of reasoning |
| `status` | `'complete'` (all rounds finished) · `'partial'` (max iterations hit, judged anyway) · `'budget_limit'` (aborted, no judgment) |
| `rounds` | Integer count of rebuttal rounds actually completed (only present on `'complete'` path) |

Artifact files written to `@log_dir`: `opening_pro.md`, `opening_con.md`, `round_0_pro.md` … `round_N_con.md`, `verdict.md`.