## 0. High-level Description

This workflow implements a **"pause for approval" / human-in-the-loop** pattern in which an LLM generates a first draft, execution halts deterministically to collect human feedback, and then a second LLM call conditionally refines the output based on that feedback. Two prompt functions drive the language work: `draft`, which instructs a professional tech writer persona to produce a structured 3-sentence article (opening claim → supporting example → forward-looking conclusion), and `refine`, which instructs a senior editor persona to revise that draft against reviewer feedback while preserving the original structure unless explicitly told to change it. Control flow after the human pause is expressed as an `EVALUATE` branch: when `@feedback` is non-empty the workflow issues a second `GENERATE` call (`refine`), otherwise it short-circuits with a direct assignment (`@final_article := @draft`), costing no additional LLM inference. All three substantive artifacts — the draft, the raw feedback, and the final article — are persisted to disk via `CALL write_file(...)`, and `LOGGING` statements at `INFO` and `DEBUG` levels narrate each stage of the pipeline. A single `EXCEPTION` handler catches `GenerationError` and performs a graceful degradation `RETURN`, surfacing the unrefined draft rather than failing silently.

---

## 1. Purpose

Produce a short, polished tech article on a given topic by pausing mid-workflow to incorporate a human reviewer's feedback before finalizing the output.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@topic` | `'The future of decentralized AI inference'` | The subject the article should be written about. |
| `@log_dir` | `'cookbook/41_human_steering/logs-spl'` | Directory path where intermediate and final artifacts are written. |

---

## 3. Process

1. **Log intent** — emit an `INFO` log announcing the topic about to be drafted.
2. **Generate draft** — call `GENERATE draft(@topic)` to produce a 3-sentence article stored in `@draft`.
3. **Log and persist draft** — emit an `INFO` log signalling the LLM step is complete, then `CALL write_file` to save `@draft` to `<log_dir>/draft.md`.
4. **Pause for human feedback** — `CALL wait_for_human_feedback(...)` (a deterministic, zero-LLM-cost tool) presents the draft to a human reviewer and blocks until a response is returned into `@feedback`. The raw feedback is immediately persisted to `<log_dir>/feedback.md`.
5. **Branch on feedback content** — `EVALUATE @feedback`:
   - **Non-empty string** → log `INFO` "refining draft", then `GENERATE refine(@draft, @feedback)` into `@final_article`.
   - **Empty string** → log `DEBUG` "using draft as-is", assign `@final_article := @draft` with no additional LLM call.
6. **Persist final article** — `CALL write_file` saves `@final_article` to `<log_dir>/final_article.md`.
7. **Return** — `RETURN @final_article WITH status = 'complete'`.

---

## 4. Error Handling

- **`GenerationError`** — caught if either `GENERATE` call fails; returns `@draft` (the initial draft, which may be empty or partial) with metadata `status = 'draft_only'` and `reason = 'generation_error'`, allowing the caller to recover the best available content rather than receiving an unhandled exception.

---

## 5. Output

| Field | Value / Type | Notes |
|---|---|---|
| `@final_article` | `TEXT` | The refined article (or the raw draft if no feedback was given, or the partial draft on error). |
| `status` | `'complete'` \| `'draft_only'` | `'complete'` on the happy path; `'draft_only'` when a `GenerationError` is caught. |
| `reason` | `'generation_error'` (error path only) | Present only in the exception branch to explain the degraded status. |