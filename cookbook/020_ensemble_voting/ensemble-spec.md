## 0. High-level Description

This workflow implements an **ensemble voting** pattern: rather than relying on a single LLM call, it generates five independent candidate answers via repeated `GENERATE answer_candidate(...)` calls, then applies a multi-stage comparative scoring pipeline before committing to a final answer. Each candidate is scored independently through `GENERATE score_candidate(...)`, which evaluates accuracy, completeness, and clarity and stores a numeric score into a dedicated OUTPUT variable. A `GENERATE find_consensus(...)` call then synthesizes common themes across all five candidates, and `GENERATE select_winner(...)` combines both the per-candidate scores and the consensus signal to elect the best response. The winning candidate is refined by `GENERATE polish(...)`, which integrates consensus insights before the result is returned. LOGGING statements at INFO and DEBUG levels bracket every major phase — generation, scoring, consensus, selection, and polish — providing a structured audit trail. On `BudgetExceeded`, the workflow gracefully degrades by running `select_winner` over only the first three candidates and returning with `status = 'partial'`; on `HallucinationDetected`, it retries with a reduced temperature of 0.1 up to three times.

## 1. Purpose

Given a free-text question, produce a high-quality answer by generating five independent LLM responses, scoring them, identifying consensus themes, and selecting and polishing the best candidate.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@question` | *(required)* | The user's question to be answered by the ensemble |

## 3. Process

1. Log the incoming question at INFO level.
2. Call `GENERATE answer_candidate(@question)` five times in sequence, storing results in `@candidate_1` through `@candidate_5`.
3. Log that five candidates are ready, then score each one: call `GENERATE score_candidate(@candidate_N, @question)` for N = 1–5, storing numeric scores in `@score_1` through `@score_5`.
4. Log all five scores at DEBUG level.
5. Call `GENERATE find_consensus(...)` with all five candidates to extract shared themes and dominant claims into `@consensus`.
6. Call `GENERATE select_winner(...)` with all five candidate/score pairs plus `@consensus` to elect the single best candidate into `@best_candidate`.
7. Call `GENERATE polish(@best_candidate, @consensus, @question)` to refine the winning answer and store it as `@final_answer`.
8. Log "Final answer ready" at INFO level and `RETURN @final_answer`.

## 4. Error Handling

- **`BudgetExceeded`** — Skips scoring candidates 4 and 5; calls `select_winner` over only the first three candidates and their scores (no consensus argument), stores the result as `@final_answer`, and returns with `status = 'partial'` and `candidates = 3`.
- **`HallucinationDetected`** — Retries the triggering generation step with `temperature = 0.1`, up to a maximum of 3 attempts, to reduce model hallucination through lower sampling randomness.

## 5. Output

| Field | Value / Type | Notes |
|---|---|---|
| `@final_answer` | `TEXT` | The polished, consensus-informed winning answer |
| `status` | `'complete'` \| `'partial'` | `'partial'` when budget was exceeded and only 3 candidates were used |
| `candidates` | `5` \| `3` | Number of candidates that participated in the final selection |