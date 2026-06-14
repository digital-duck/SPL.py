## Summary

This workflow reads a directory of candidate resume files, evaluates each one in parallel using an LLM judge, and aggregates the results into a qualification summary. It exists to replace slow sequential screening with a scalable batch pipeline that applies consistent, criteria-driven scoring across any number of resumes. Hiring teams and talent-ops pipelines are the primary beneficiaries.

---

## Detailed Specification

### 1. Purpose

Automatically screen a batch of resume files against defined qualification criteria and produce a ranked summary of which candidates qualify for an advanced technical role.

---

### 2. High-level Description

This workflow implements a classic Map-Reduce pattern across three sequential phases. In the **map phase**, the workflow reads every `.txt` file from a local `data/` directory and stores the raw text of each resume in shared state (`@resumes`). In the **batch phase** — expressed in SPL as `CALL PARALLEL` — every resume is dispatched concurrently to a single `evaluate_resume` function that GENERATEs an LLM response; the LLM returns structured YAML containing `candidate_name`, a boolean `qualifies` field, and a `reasons` list. The batch phase collects all individual results into `@evaluations`. In the **reduce phase**, the workflow aggregates `@evaluations` by counting how many candidates have `qualifies: true`, collecting their names, and computing a percentage, storing the final dictionary as `@summary`. There is no iterative refinement (WHILE) or semantic branching (EVALUATE) — control flow is strictly linear, driven by the map → batch → reduce dependency chain. The only LLM call is the per-resume evaluation prompt, which uses a YAML sentinel (`\`\`\`yaml … \`\`\``) to delimit structured output for deterministic parsing.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW resume_qualification` | `create_resume_processing_flow()` + `Flow(start=...)` | Top-level orchestration unit |
| `CALL read_resumes() INTO @resumes` | `ReadResumesNode.exec()` → `shared["resumes"]` | Side-effect file I/O; no LLM call |
| `CREATE FUNCTION evaluate_resume` | Inline prompt string in `EvaluateResumesNode.exec()` | Single prompt template with `{content}` slot |
| `CALL PARALLEL evaluate_resume(...)` | `BatchNode` — PocketFlow runs each item from `prep()` through `exec()` concurrently | Core parallelism; maps one function over a list |
| `GENERATE evaluate_resume(...) INTO @result` | `call_llm(prompt)` → `yaml.safe_load(...)` | LLM call + YAML parse per resume |
| Shared `@evaluations` | `shared["evaluations"]` dict | Intermediate accumulator between batch and reduce phases |
| Shared `@summary` | `shared["summary"]` dict | Final output written by reduce node |
| `CALL aggregate_results() INTO @summary` | `ReduceResultsNode.exec(evaluations)` | Pure computation, no LLM |
| `EXCEPTION WHEN ParseError` | Implicit — `yaml.safe_load` raises on malformed output | Not explicitly handled; should be added |

*(No `RETURN WITH status=` mapping needed — all transitions are linear implicit flow.)*

---

### 4. Logical Functions / Prompts

#### `evaluate_resume`

- **Role**: The sole LLM call in the pipeline; acts as a binary qualification judge for a single candidate.
- **Input**: Raw resume text injected verbatim into the prompt body.
- **Qualification criteria baked into prompt**:
  - At least a bachelor's degree in a relevant field
  - At least 3 years of relevant work experience
  - Strong technical skills relevant to the position
- **Output format**: Structured YAML block fenced with ` ```yaml … ``` ` sentinel tokens.
  ```yaml
  candidate_name: <string>
  qualifies: <true|false>
  reasons:
    - <string>
    - <string>
  ```
- **Parsing convention**: The response is split on `` ```yaml `` and `` ``` `` to extract the YAML block before calling `yaml.safe_load`. If no fence is present, the entire response is passed to the parser (graceful fallback).

---

### 5. Control Flow

```
START
  │
  ▼
read_resumes          — file I/O, no LLM; populates @resumes (dict: filename → text)
  │
  ▼
CALL PARALLEL         — for each (filename, text) in @resumes:
  evaluate_resume()       GENERATE evaluate_resume(text) INTO @result
                          parse YAML → {candidate_name, qualifies, reasons}
  │  (all branches complete before continuing)
  ▼
aggregate_results     — pure Python reduce over @evaluations;
                        computes total, qualified_count, percentage, qualified_names
                        writes @summary; prints formatted report to stdout
  │
  ▼
END
```

There is no loop condition and no semantic branch — the pipeline terminates unconditionally after the reduce node writes `@summary`.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Read all resume .txt files from a data directory into @resumes. \
  For each resume, CALL PARALLEL evaluate_resume(text) INTO @result using GENERATE with a structured \
  YAML prompt that checks for a bachelor's degree, 3+ years experience, and strong technical skills; \
  the LLM returns candidate_name, a boolean qualifies, and reasons. Collect all results into @evaluations. \
  Then aggregate @evaluations: count qualified candidates, compute percentage, collect qualified_names \
  into @summary." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile resume_qualification.spl --lang python/pocketflow
spl3 splc compile resume_qualification.spl --lang python/langgraph
spl3 splc compile resume_qualification.spl --lang go
```