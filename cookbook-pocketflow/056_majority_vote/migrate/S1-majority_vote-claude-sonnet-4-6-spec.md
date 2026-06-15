## Summary

This workflow solves hard reasoning problems by running the same question through an LLM multiple times in parallel and returning whichever answer appears most often. It exists because any single LLM attempt may make an arithmetic or logical slip, and aggregating independent attempts via consensus dramatically raises accuracy. Data scientists, researchers, and engineers who need reliable numerical answers from probabilistic models benefit most.

---

## Detailed Specification

### 1. Purpose

Run a user-supplied reasoning question through N independent LLM attempts in parallel, then return the most frequently occurring answer as the consensus solution.

---

### 2. High-level Description

This workflow implements a **majority-vote ensemble** pattern over a single LLM using SPL's `CALL PARALLEL` (batch) construct. A single logical function — the `solve_reasoning` prompt template — is instantiated `num_tries` times with identical input, each invocation instructing the model to reason step-by-step and emit a structured YAML block containing a `thinking` field and a scalar `answer` field. The parallel calls are independent: no shared context, no iteration between them. After all N results are collected, a post-processing step aggregates the answers using a frequency counter and selects the plurality winner, storing it in the shared state variable `@majority_answer`. Any individual attempt that fails to produce a well-formed YAML response is caught by an `EXCEPTION WHEN ParseError` handler that silently drops the attempt, ensuring partial failures do not abort the ensemble. There is no WHILE loop and no EVALUATE branch — control flow is a single fan-out/fan-in: parallel generation → aggregate → terminate.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW MajorityVoteReasoning` | `Flow(start=MajorityVoteNode()).run(shared)` | Entire execution graph |
| `CREATE FUNCTION solve_reasoning` | inline prompt string in `exec()` | Parameterised by `{question}` |
| `CALL PARALLEL ... END` (`num_tries` branches) | `BatchNode` — `prep()` returns a list; `exec()` runs once per item | PocketFlow runs each `exec()` call independently |
| `GENERATE solve_reasoning(@question) INTO @attempt` | `call_llm(prompt)` → raw text per attempt | One GENERATE per branch |
| `EXCEPTION WHEN ParseError THEN RETURN NULL` | `exec_fallback(prep_res, exc) → None` | Drops malformed YAML silently |
| `@majority_answer` (shared state variable) | `shared["majority_answer"]` | Written in `post()`, read by caller |
| `@num_tries` (input parameter) | `shared["num_tries"]` / `--tries` CLI flag | Controls fan-out width |
| `@question` (input parameter) | `shared["question"]` / `--question` CLI flag | Broadcast to all parallel branches |

> **Note:** `post()` returning `"end"` is a terminal sentinel, not a branching decision — it is not modelled as `RETURN WITH status=` in SPL.

---

### 4. Logical Functions / Prompts

**`solve_reasoning`**

- **Role:** The sole generation step. Called N times in parallel with the same question text; each call is fully independent.
- **Prompt conventions:**
  - System role set inline: `"You are a helpful assistant."`
  - Output format enforced with a YAML fence sentinel:
    ````
    ```yaml
    thinking: |
        (chain-of-thought reasoning)
    answer: 0.123
    ```
    ````
  - The `thinking` field is required but discarded after parsing — it exists solely to elicit chain-of-thought before committing to `answer`.
  - `answer` must be a scalar (numeric string). The caller casts it to `str` for stable Counter comparison.
  - Parsing failure raises `RuntimeError`, caught by `exec_fallback`.

---

### 5. Control Flow

```
INPUT: @question, @num_tries
  │
  ▼
CALL PARALLEL (num_tries × solve_reasoning(@question))
  │  ← each branch: GENERATE → parse YAML → extract answer string
  │  ← EXCEPTION WHEN ParseError → drop attempt (return None)
  ▼
Aggregate: filter nulls → Counter.most_common(1) → @majority_answer
  │
  ▼
OUTPUT: @majority_answer
```

There is no WHILE loop. There is no EVALUATE branch. The fan-out width is fixed at `num_tries` before execution begins. Termination is unconditional after the single batch completes.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from the spec (paste Section 2 as the description)
spl3 text2spl --description "Run a user-supplied reasoning question through N independent LLM \
attempts in parallel, each instructed to emit a YAML block with a thinking field and a scalar \
answer field. Aggregate results with a frequency counter and return the plurality answer as \
majority_answer. Drop any attempt that fails to parse. No loop, no branching." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile majority_vote.spl --lang python/pocketflow
spl3 splc compile majority_vote.spl --lang python/langgraph
spl3 splc compile majority_vote.spl --lang go
```