## Summary

Ensemble Voting is a quality-amplification workflow that generates five independent LLM answers to a single question, scores each answer, identifies shared themes across all candidates, and then selects and polishes the best response. It exists because any single LLM call can produce a suboptimal or inconsistent answer — aggregating multiple independent generations and applying consensus logic raises reliability. Developers building question-answering systems and knowledge assistants benefit most.

---

## Detailed Specification

### 1. Purpose

Generate a high-quality, consensus-validated answer to an open-ended question by sampling multiple independent LLM responses, scoring them, and synthesizing the winner.

---

### 2. High-level Description

This WORKFLOW, named `ensemble_voting`, accepts a single TEXT input `@question` and produces a TEXT output `@final_answer`. It applies the ensemble method: five independent calls to the `answer_candidate` CREATE FUNCTION produce candidates `@candidate_1` through `@candidate_5`, each generated with no shared context so that outputs vary naturally. A second CREATE FUNCTION, `score_candidate`, is then called via GENERATE for each candidate alongside the original question, yielding numeric or structured scores (`@score_1` through `@score_5`) that reflect accuracy, completeness, and clarity. A third function, `find_consensus`, receives all five candidates and extracts common themes into `@consensus`, capturing the collective signal across the ensemble. A fourth function, `select_winner`, receives all five candidates, their scores, and the consensus summary, and returns the single best candidate as `@best_candidate`. Finally, a `polish` CREATE FUNCTION refines `@best_candidate` using the consensus insights and the original question to produce `@final_answer`, which is returned with `status = 'complete'` and `candidates = 5`. Two EXCEPTION handlers guard the workflow: `BudgetExceeded` falls back gracefully by running `select_winner` over only the first three candidates and returning with `status = 'partial'`; `HallucinationDetected` triggers a RETRY at low temperature (0.1) up to three times.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| WORKFLOW ensemble_voting | `WORKFLOW ensemble_voting` | Top-level orchestration; declares INPUT `@question` and OUTPUT `@final_answer` |
| CREATE FUNCTION answer_candidate | `CREATE FUNCTION answer_candidate(@question)` | Generates one independent candidate answer |
| CREATE FUNCTION score_candidate | `CREATE FUNCTION score_candidate(@candidate, @question)` | Scores a single candidate on accuracy, completeness, clarity |
| CREATE FUNCTION find_consensus | `CREATE FUNCTION find_consensus(@c1…@c5)` | Extracts common themes across all five candidates |
| CREATE FUNCTION select_winner | `CREATE FUNCTION select_winner(@c1,@s1…@c5,@s5,@consensus)` | Picks best candidate using scores and consensus alignment |
| CREATE FUNCTION polish | `CREATE FUNCTION polish(@best_candidate, @consensus, @question)` | Refines the winner into a clean final answer |
| GENERATE … INTO @var | `GENERATE <fn>(…) INTO @candidate_N` / `@score_N` / `@consensus` / `@best_candidate` / `@final_answer` | Each LLM call stores its result in a named variable |
| RETURN WITH status= | `RETURN @final_answer WITH status='complete', candidates=5` | Non-trivial: drives observability and the partial-fallback distinction |
| EXCEPTION WHEN BudgetExceeded | `EXCEPTION WHEN BudgetExceeded THEN … RETURN WITH status='partial'` | Graceful degradation to 3 candidates |
| EXCEPTION WHEN HallucinationDetected | `EXCEPTION WHEN HallucinationDetected THEN RETRY WITH temperature=0.1 LIMIT 3` | Automatic low-temperature retry |
| Shared state (@vars) | `@candidate_1…5`, `@score_1…5`, `@consensus`, `@best_candidate`, `@final_answer` | Variables flow across steps within the workflow scope |

---

### 4. Logical Functions / Prompts

**answer_candidate**
- Role: Independently sample one candidate answer to the question; called five times to build the ensemble pool.
- Key conventions: No cross-candidate context injected; natural temperature variation across calls produces answer diversity. Output is free-form prose.

**score_candidate**
- Role: Evaluate one candidate answer against the original question on accuracy, completeness, and clarity.
- Key conventions: Output is a structured score (numeric or labeled); must be parseable downstream by `select_winner`. Scoring criteria are explicit in the prompt to ensure comparability across all five calls.

**find_consensus**
- Role: Synthesize all five candidates into a concise summary of common themes, shared facts, and areas of agreement.
- Key conventions: Receives all five candidates in a single prompt; output (`@consensus`) is a thematic digest, not a ranked list. Serves as a cross-candidate signal rather than a preference judgment.

**select_winner**
- Role: Identify the single best candidate using both per-candidate scores and alignment with the consensus themes.
- Key conventions: Receives all five (candidate, score) pairs and `@consensus` in one prompt; output is the verbatim text of the winning candidate (or a pointer to it). Consensus alignment acts as a tiebreaker when scores are close.

**polish**
- Role: Clean and elevate the winning candidate into a publication-ready final answer.
- Key conventions: Uses `@consensus` to fill gaps or reinforce well-supported claims; the original `@question` anchors the revision to the user's intent. Output is the finalized `@final_answer`.

---

### 5. Control Flow

1. **Entry** — Log the question at INFO level.
2. **Candidate generation** — Five sequential GENERATE calls to `answer_candidate` populate `@candidate_1` through `@candidate_5`.
3. **Scoring** — Five sequential GENERATE calls to `score_candidate` populate `@score_1` through `@score_5`.
4. **Consensus extraction** — One GENERATE call to `find_consensus` over all five candidates yields `@consensus`.
5. **Winner selection** — One GENERATE call to `select_winner` with all candidates, scores, and consensus yields `@best_candidate`.
6. **Polishing** — One GENERATE call to `polish` produces `@final_answer`.
7. **Normal termination** — `RETURN @final_answer WITH status='complete', candidates=5`. The `status='complete'` token is meaningful: it is distinguished from `status='partial'` in the exception path.
8. **BudgetExceeded path** — If budget is exhausted at any point, `select_winner` is called over only the first three candidates (no polish step), and the workflow returns with `status='partial', candidates=3`.
9. **HallucinationDetected path** — Automatic RETRY at `temperature=0.1`, up to three attempts, before propagating failure.

There is no WHILE loop — the workflow is a linear pipeline with exception-driven branches, not an iterative refinement loop.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Generate a high-quality, consensus-validated answer to an \
open-ended question by sampling five independent LLM responses via answer_candidate, \
scoring each with score_candidate, extracting shared themes with find_consensus, \
selecting the best candidate with select_winner using scores and consensus alignment, \
then polishing the winner into a final answer; handle BudgetExceeded by falling back \
to three candidates with status='partial', and HallucinationDetected with a low-temperature \
retry up to three times." --mode workflow

# Step 2 — compile to any target
spl3 splc compile ensemble_voting.spl --lang python/pocketflow
spl3 splc compile ensemble_voting.spl --lang python/langgraph
spl3 splc compile ensemble_voting.spl --lang go
```