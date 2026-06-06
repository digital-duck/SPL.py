## 0. High-level Description

This workflow implements a **fan-out / merge** (parallel map-reduce) pattern to produce a morning news digest from three independent topic streams. The orchestrator workflow `parallel_news_digest` accepts three topic strings and a shared model name via INPUT parameters, then uses `CALL PARALLEL` to dispatch three concurrent invocations of the sub-workflow `summarise_single` — one per topic — each receiving a snapshot of the parent scope with no shared mutable state between branches, writing results back only through `INTO @var`. The sub-workflow `summarise_single` wraps a single `GENERATE` call using the `summarise_topic` CREATE FUNCTION, which instructs the model to produce a neutral, 3-sentence analysis ending with a near-term outlook sentence, capped at 256 output tokens via an `OUTPUT BUDGET` constraint. Once all three parallel branches complete, the orchestrator calls `GENERATE` a second time using the `morning_briefing` CREATE FUNCTION, which combines the three summaries into a structured 200-word executive digest with bold topic headers and a closing "watch today" callout. The `@digest_model` INPUT parameter uniformly drives every LLM call across both the parallel sub-workflows and the final merge step, making it trivial to swap models (e.g. `gemma3`) at the command line. LOGGING statements at INFO level bracket the major pipeline phases (start, parallel-complete, done with digest length), while DEBUG-level logging inside the sub-workflow traces each individual topic dispatch; EXCEPTION handlers cover `ModelUnavailable` (hard failure, returns an error sentinel with `status='failed'`) and `BudgetExceeded` (soft truncation, returns whatever was generated with `status='truncated'`).

---

## 1. Purpose

Concurrently summarise three user-specified news topics using parallel LLM calls, then synthesise the results into a single cohesive morning briefing digest ready for an executive reader.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@topic_tech` | `'AI and large language models'` | Subject line for the technology news summary |
| `@topic_science` | `'space exploration and astronomy'` | Subject line for the science news summary |
| `@topic_business` | `'global markets and energy transition'` | Subject line for the business news summary |
| `@digest_model` | `'gemma3'` | LLM model identifier used for every GENERATE call |
| `@output_budget` | `512` | Maximum token budget for the final merged digest |
| `@log_dir` | `'cookbook/64_parallel_news_digest/logs-spl'` | Directory path passed to sub-workflows for log output |

---

## 3. Process

1. **Initialise** — The main workflow `parallel_news_digest` logs the chosen model and all three topic strings at INFO level.

2. **Fan-out (parallel summarisation)** — `CALL PARALLEL` dispatches three concurrent invocations of the sub-workflow `summarise_single`, one for each topic (`@topic_tech`, `@topic_science`, `@topic_business`). Each branch receives its own scope snapshot along with `@digest_model` and `@log_dir`. No mutable state is shared between branches.

3. **Per-branch summarisation** — Inside each `summarise_single` invocation:
   - A DEBUG log records which topic is being processed.
   - `GENERATE summarise_topic(@topic, @context)` calls the LLM using the `summarise_topic` prompt function, capped at **256 output tokens**.
   - The result is stored in the branch-local `@summary` and returned to the parent scope via `INTO` (`@tech_summary`, `@sci_summary`, `@biz_summary` respectively).

4. **Fan-in checkpoint** — Once all three parallel branches complete, the orchestrator logs a merge-start message at INFO level.

5. **Synthesis** — `GENERATE morning_briefing(@tech_summary, @sci_summary, @biz_summary)` calls the LLM using the `morning_briefing` prompt function, capped at `@output_budget` tokens (default 512). The prompt instructs the model to open with an orienting sentence, present each topic under a bold header, and close with a single "watch today" callout. The result is stored in `@digest`.

6. **Completion log** — The orchestrator logs a done message including the character length of `@digest` at INFO level.

7. **Return** — `@digest` is returned to the caller.

---

## 4. Error Handling

- **`ModelUnavailable`** — Logs the unavailable model name at ERROR level, then immediately returns the literal string `'[ERROR] Model unavailable.'` with metadata `status = 'failed'`. No partial output is preserved.
- **`BudgetExceeded`** — Logs a token-budget warning at WARN level, then returns whatever was generated in `@digest` (potentially truncated) with metadata `status = 'truncated'`. The workflow does not abort; partial content is surfaced to the caller.

---

## 5. Output

The workflow RETURNs `@digest` (type TEXT), a synthesised 200-word morning briefing covering all three topics.

| Scenario | Returned value | `status` metadata |
|---|---|---|
| Success | Full digest text | *(not set — defaults to success)* |
| Token budget exceeded | Truncated digest text | `'truncated'` |
| Model unavailable | `'[ERROR] Model unavailable.'` | `'failed'` |