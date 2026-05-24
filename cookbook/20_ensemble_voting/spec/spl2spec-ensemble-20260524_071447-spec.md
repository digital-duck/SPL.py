## Summary

Ensemble Voting is a quality-maximizing workflow that generates five independent LLM answers to a question, scores each one, finds their common ground, and selects and polishes the best candidate. It exists to reduce the variance and hallucination risk of any single LLM call by applying a judge-driven consensus mechanism. Data scientists, researchers, and product teams that need high-confidence answers to open-ended questions benefit most.

---

## Detailed Specification

### 1. Purpose

Generate a single high-quality, polished answer to an open-ended question by running a five-candidate ensemble: independently scoring each candidate, distilling a consensus, and selecting the winner before a final polish pass.

---

### 2. High-level Description

The workflow `ensemble_voting` accepts a single `@question` TEXT variable and produces a `@final_answer` TEXT. It opens by invoking the `answer_candidate` GENERATE function five times in sequence, each call storing an independent response in `@candidate_1` through `@candidate_5`; because the same prompt function is called with the same input, temperature variance within the LLM produces meaningfully diverse outputs. Each candidate is then evaluated by the `score_candidate` GENERATE function, which assesses accuracy, completeness, and clarity and stores a numeric or categorical score in `@score_1` through `@score_5`. The `find_consensus` GENERATE function receives all five candidates and extracts recurring themes and agreed-upon facts into `@consensus`. The `select_winner` GENERATE function is then called with all five (candidate, score) pairs plus the consensus, choosing the best-aligned candidate and storing it in `@best_candidate`. Finally, the `polish` GENERATE function refines that winner against the consensus and the original question, producing `@final_answer`, which is returned with `status = 'complete'` and `candidates = 5`. Two EXCEPTION handlers provide graceful degradation: a `BudgetExceeded` handler re-runs `select_winner` on only the first three candidates and returns with `status = 'partial'`, while a `HallucinationDetected` handler retries the entire workflow at `temperature = 0.1` up to three times.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW ensemble_voting` | `WORKFLOW` | Top-level named orchestration unit; accepts `INPUT: @question TEXT`, emits `OUTPUT: @final_answer TEXT` |
| `answer_candidate(...)` | `CREATE FUNCTION answer_candidate` | Prompt template producing one candidate answer; called 5× to exploit temperature diversity |
| `score_candidate(...)` | `CREATE FUNCTION score_candidate` | Prompt template that scores a single candidate on accuracy, completeness, and clarity |
| `find_consensus(...)` | `CREATE FUNCTION find_consensus` | Prompt template that distills shared themes across all five candidates |
| `select_winner(...)` | `CREATE FUNCTION select_winner` | Prompt template that picks the best (candidate, score) pair given the consensus |
| `polish(...)` | `CREATE FUNCTION polish` | Prompt template that refines the winning candidate into a final polished answer |
| `GENERATE fn(...) INTO @var` | `GENERATE` | Each LLM call; result bound to a named `@var` for downstream use |
| `@candidate_1`…`@candidate_5`, `@score_1`…`@score_5`, `@consensus`, `@best_candidate`, `@final_answer` | SPL `@vars` | Shared mutable state threaded through the pipeline |
| `RETURN @final_answer WITH status='complete', candidates=5` | `RETURN` | Non-trivial status token signals a full 5-candidate run succeeded |
| `RETURN @final_answer WITH status='partial', candidates=3` | `RETURN` | Non-trivial status token signals a degraded 3-candidate run due to budget exhaustion |
| `EXCEPTION WHEN BudgetExceeded` | `EXCEPTION WHEN BudgetExceeded` | Runs abbreviated `select_winner` on first 3 candidates; returns partial result |
| `EXCEPTION WHEN HallucinationDetected` | `EXCEPTION WHEN HallucinationDetected` | Retries the workflow at `temperature = 0.1`, up to 3 attempts |
| `LOGGING ... LEVEL INFO/DEBUG` | `LOGGING` | Observability hooks at each major pipeline stage; no effect on output |

---

### 4. Logical Functions / Prompts

**`answer_candidate(@question)`**
- **Role:** Generates one independent candidate answer to the user's question.
- **Key conventions:** Called five times with identical input; natural LLM temperature variance produces diverse outputs. No sentinel tokens required — free-form prose answer expected.

**`score_candidate(@candidate, @question)`**
- **Role:** Judges a single candidate against the original question on three axes: accuracy, completeness, and clarity.
- **Key conventions:** Should return a structured or numeric score (e.g., integer 1–10 or a JSON object) so that `select_winner` can compare candidates deterministically. Scores are stored as `@score_N` scalars.

**`find_consensus(@candidate_1, …, @candidate_5)`**
- **Role:** Reads all five candidates holistically and distills the points of agreement — recurring facts, shared conclusions, and common framings.
- **Key conventions:** Output is a prose summary of consensus themes stored in `@consensus`; it serves as both a quality signal and a grounding reference for the selection and polish steps.

**`select_winner(@candidate_N, @score_N, …, @consensus)`**
- **Role:** Picks the single best candidate by combining quantitative scores with alignment to the consensus summary.
- **Key conventions:** Receives all five (candidate, score) pairs plus `@consensus`; should output the full text of the winning candidate (not just an index) so that `polish` can operate directly on it. In the `BudgetExceeded` exception path, only the first three pairs are passed.

**`polish(@best_candidate, @consensus, @question)`**
- **Role:** Final editorial pass — tightens language, incorporates any consensus insights missing from the winner, and ensures the answer squarely addresses the original question.
- **Key conventions:** Output is the finished `@final_answer`; no scoring or branching follows this step.

---

### 5. Control Flow

The workflow is a strictly linear, five-stage pipeline with no WHILE loop and no EVALUATE branch.

1. **Candidate generation** — `answer_candidate` is called five times in sequence; results accumulate in `@candidate_1`–`@candidate_5`.
2. **Scoring** — `score_candidate` is called five times; results accumulate in `@score_1`–`@score_5`.
3. **Consensus extraction** — `find_consensus` aggregates all candidates into `@consensus`.
4. **Winner selection** — `select_winner` combines scores and consensus into `@best_candidate`.
5. **Polish** — `polish` produces `@final_answer`; the workflow returns `status = 'complete'` with `candidates = 5`.

**Exception paths (non-linear):**
- `BudgetExceeded` interrupts any step; execution jumps to an abbreviated `select_winner` over the first three candidates only, then returns `status = 'partial'` with `candidates = 3`.
- `HallucinationDetected` triggers a full retry of the workflow at `temperature = 0.1`, up to three times before propagating the exception.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Generate a single high-quality, polished answer to an \
open-ended question by running a five-candidate ensemble: independently scoring each \
candidate, distilling a consensus, and selecting the winner before a final polish pass." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile ensemble_voting.spl --lang python/pocketflow
spl3 splc compile ensemble_voting.spl --lang python/langgraph
spl3 splc compile ensemble_voting.spl --lang go
```