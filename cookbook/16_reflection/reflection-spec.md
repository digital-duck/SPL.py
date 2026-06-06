## 0. High-level Description

This workflow implements a **reflection agent** pattern — a meta-cognitive loop in which the agent first produces an answer, then iteratively critiques and corrects its own reasoning until it reaches a confidence threshold or exhausts its reflection budget. Four prompt functions drive the pipeline: `solve` generates the initial answer to the problem; `reflect` performs self-assessment, identifying logical errors, gaps, or weak reasoning in that answer; `confidence_score` maps the answer and its reflection to a numeric score between 0 and 1; `extract_issues` distills the reflection into a concrete list of deficiencies; and `correct` rewrites the answer by addressing those issues. Control flow is governed by a WHILE loop bounded by `@max_reflections`, with an EVALUATE branch inside that either exits early via RETURN with `status='confident'` when the confidence score exceeds 0.85, or drives another correction cycle by incrementing `@iteration`. Every intermediate artifact — each draft answer, each reflection, and the final result — is persisted to disk via CALL `write_file`, providing a full audit trail under `@log_dir`. LOGGING statements at INFO, DEBUG, and WARN levels trace iteration progress and confidence evolution. Two EXCEPTION handlers guard the boundary conditions: `MaxIterationsReached` commits the best available answer, and `HallucinationDetected` discards the current answer and restarts from scratch with a fresh `solve` call.

## 1. Purpose

Given an open-ended problem, produce a well-reasoned written answer by having the model repeatedly critique and revise its own output until it is sufficiently confident or the reflection budget is exhausted.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@problem` | *(required)* | The question, design challenge, or explanation task to be solved |
| `@max_reflections` | `3` | Maximum number of reflect-and-correct cycles before committing best effort |
| `@log_dir` | `cookbook/16_reflection/logs-spl` | Directory path where intermediate and final answer files are written |

## 3. Process

1. Initialize `@iteration` to 0 and `@confidence` to 0; log workflow start at INFO level.
2. GENERATE `solve(@problem)` to produce the first draft answer into `@answer`; log "Initial solution ready"; CALL `write_file` to save it as `answer_0.md`.
3. Enter the WHILE loop, which continues while `@iteration < @max_reflections`.
4. GENERATE `reflect(@problem, @answer)` to produce a self-critique into `@reflection`; CALL `write_file` to save it as `reflection_{iteration}.md`.
5. GENERATE `confidence_score(@answer, @reflection)` to produce a numeric confidence value into `@confidence`; log the score at DEBUG level.
6. EVALUATE `@confidence`:
   - **WHEN > 0.85**: log confidence at INFO, CALL `write_file` to save `final.md`, and RETURN `@answer` with `status='confident'`, `confidence`, and `reflections` count — exiting the workflow.
   - **ELSE**: GENERATE `extract_issues(@reflection)` into `@issues`; GENERATE `correct(@answer, @issues, @problem)` into a revised `@answer`; increment `@iteration`; CALL `write_file` to save the new draft as `answer_{iteration}.md`. Return to step 3.
7. If the WHILE loop exhausts all reflections without reaching the confidence threshold, log a WARN, CALL `write_file` to save `final.md`, and RETURN `@answer` with `status='best_effort'`, `confidence`, and `reflections` count.

## 4. Error Handling

- **`MaxIterationsReached`** — The runtime iteration guard fires before the workflow's own WHILE bound is hit; saves the current `@answer` to `final.md` and returns it with `status='max_reflections'` and the last known `@confidence`.
- **`HallucinationDetected`** — The model's output is flagged as hallucinated; the current answer is discarded, `solve(@problem)` is called again from scratch, and the fresh answer is returned with `status='restarted'` (no confidence or reflection count metadata).

## 5. Output

Returns `@answer` (TEXT) in all paths. The RETURN metadata varies by exit path:

| Exit path | `status` | `confidence` | `reflections` |
|---|---|---|---|
| Confidence threshold met inside loop | `confident` | final score | iteration count at exit |
| Loop exhausted normally | `best_effort` | final score | `@max_reflections` |
| Runtime max-iterations exception | `max_reflections` | last score | *(not included)* |
| Hallucination exception | `restarted` | *(not included)* | *(not included)* |

Intermediate files written under `@log_dir`: `answer_0.md`, `answer_{n}.md` for each correction, `reflection_{n}.md` for each critique cycle, and `final.md` for the committed result.