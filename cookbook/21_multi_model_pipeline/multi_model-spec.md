## 0. High-level Description

This workflow implements a **multi-model pipeline** pattern — a sequential, staged orchestration where each processing step can target a different LLM via `GENERATE ... USING MODEL`. Four prompt functions are defined: `research`, which instructs a research-specialist persona to retrieve facts and statistics about a topic; `analyze`, which instructs a data-analyst persona to extract the three most significant insights with significance ratings (1–10) from the research output; `write_summary`, which instructs a professional-writer persona to produce a structured two-paragraph summary (findings then implications); and `quality_check`, which instructs a reviewer persona to score the summary on clarity, accuracy, and completeness, returning **only** a single float in [0.0, 1.0]. Control flow after the three linear generation steps enters a `WHILE @iteration < @max_iterations` loop that drives a self-refine pattern: on each iteration, `GENERATE quality_check` evaluates the draft, and an `EVALUATE @quality` branch either exits early via `RETURN ... WITH status='high_quality'` when the score exceeds 0.7, or regenerates the summary and increments the counter. All intermediate and final artifacts are persisted via `CALL write_file(...)` into a configurable log directory, and `LOGGING` statements at INFO, DEBUG, and WARN levels trace pipeline milestones. Two `EXCEPTION` handlers cover `MaxIterationsReached` (returns a partial result) and `ModelOverloaded` (returns a degraded-service result).

## 1. Purpose

Produce a high-quality, reviewed written summary of any topic by chaining research, analysis, and writing stages across targeted LLM models, with iterative self-refinement until a quality threshold is met or a maximum iteration budget is exhausted.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@topic` | *(required)* | The subject to research, analyze, and summarize |
| `@max_iterations` | `3` | Maximum number of quality-check / rewrite cycles before fallback |
| `@log_dir` | `cookbook/21_multi_model_pipeline/logs-spl` | Directory path where intermediate and final markdown files are written |

## 3. Process

1. Log pipeline start at INFO level, including the topic.
2. **Research** — `GENERATE research(@topic) USING MODEL 'gemma3'` to retrieve facts and statistics into `@facts`; log completion at DEBUG; write `research.md` to disk.
3. **Analysis** — `GENERATE analyze(@facts) USING MODEL 'gemma3'` to identify three insights with significance ratings into `@analysis`; log completion at DEBUG; write `analysis.md` to disk.
4. **Initial draft** — `GENERATE write_summary(@analysis) USING MODEL 'gemma3'` to produce a two-paragraph summary into `@draft`; log at INFO; write `draft_0.md` to disk.
5. Initialize `@iteration := 0` and `@quality := 0`.
6. Enter `WHILE @iteration < @max_iterations` loop:
   - Log current iteration at DEBUG.
   - `GENERATE quality_check(@draft)` (no model pin — uses default) to score the draft into `@quality`; log score at DEBUG.
   - `EVALUATE @quality`:
     - **When `> 0.7`**: log threshold met at INFO, write `final.md`, and `RETURN @draft WITH status='high_quality', score=@quality` (early exit).
     - **Else**: `GENERATE write_summary(@analysis)` to regenerate `@draft`, increment `@iteration`, write `draft_{@iteration}.md` to disk.
7. If the loop exhausts all iterations without meeting the threshold, log a WARN with the final score, write `final.md`, and `RETURN @draft WITH status='max_iterations', score=@quality`.

## 4. Error Handling

- **`MaxIterationsReached`** — catches the SPL runtime's built-in iteration-limit signal; returns whatever draft exists with `status='partial'` and no score metadata.
- **`ModelOverloaded`** — catches a backend capacity failure on any `GENERATE` call; returns the last available draft with `status='model_overloaded'`.

## 5. Output

The workflow returns `@final` — the last generated draft text — accompanied by metadata fields on every exit path:

| Exit path | `status` | `score` |
|---|---|---|
| Quality threshold met (score > 0.7) | `'high_quality'` | float score |
| Loop exhausted without threshold | `'max_iterations'` | float score |
| `MaxIterationsReached` exception | `'partial'` | *(absent)* |
| `ModelOverloaded` exception | `'model_overloaded'` | *(absent)* |

In all cases, the last successfully generated draft is also persisted to `{@log_dir}/final.md` on the two normal exit paths (the exception handlers do not guarantee a file write).