## Summary

This workflow accelerates code quality assurance by running three independent reviews — style, security, and test generation — simultaneously against a single code snippet, then consolidating the results into one prioritised action plan. Instead of waiting for each check to finish before starting the next, all three run in parallel, cutting total review time to roughly the duration of the slowest individual check. Engineering teams and CI pipelines benefit by getting richer, faster feedback without manual coordination.

---

## Detailed Specification

### 1. Purpose

Produce a consolidated, prioritised code-review report by running style, security, and test-generation checks concurrently on a code snippet and merging their outputs into a single senior-engineer-level action plan.

---

### 2. High-level Description

The `parallel_code_review` WORKFLOW accepts a code snippet, a target language, a model identifier, and a log directory as inputs. It fans out immediately to three imported sub-WORKFLOWs — `style_review`, `security_audit`, and `test_generator` — via a single CALL PARALLEL block, which executes all three concurrently; each sub-workflow reads the shared `@code` input and writes exclusively to its own output variable (`@style_fb`, `@sec_fb`, `@test_fb`), so there is no shared-state interference. Once all three branches complete, the results are passed to a GENERATE call backed by the `merge_reviews` CREATE FUNCTION, which instructs the model (via a senior-engineering-lead persona prompt) to produce a three-section report: a CRITICAL-first numbered action-item list capped at 150 words, verbatim generated test cases in a code block, and a one-paragraph production-readiness summary. The GENERATE call applies an explicit output token budget of 1 024 tokens using the caller-supplied model. Throughout execution, structured LOGGING statements at INFO and ERROR/WARN levels record progress milestones and result sizes. Two EXCEPTION handlers guard the merge phase: WHEN ModelUnavailable returns a hard error string with `status='failed'`, and WHEN BudgetExceeded returns whatever partial report was produced with `status='truncated'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW parallel_code_review` | `WORKFLOW <name>` | Top-level orchestrator; declares typed `INPUT`/`OUTPUT` with defaults |
| `IMPORT '00_style_review'` etc. | `IMPORT '<module>'` | Loads three sub-workflow definitions from separate files; makes their names callable |
| `CALL PARALLEL … END` | `CALL PARALLEL` | Fan-out: dispatches three sub-WORKFLOWs concurrently with named-argument dispatch; each result captured in its own `INTO @var` |
| `CREATE FUNCTION merge_reviews(…)` | `CREATE FUNCTION <name>` | Reusable prompt template with `{style}`, `{sec_audit}`, `{tests}` parameter slots |
| `GENERATE merge_reviews(…) INTO @report` | `GENERATE <fn>(…) INTO @<var>` | LLM call that renders the function template; result stored in `@report` |
| `WITH OUTPUT BUDGET 1024 TOKENS` | output budget clause on `GENERATE` | Hard cap on model response length |
| `USING MODEL @review_model` | model selection clause on `GENERATE` | Runtime model selection via input variable |
| `@code`, `@style_fb`, `@sec_fb`, `@test_fb`, `@report` | SPL `@<var>` shared state | Typed workflow variables; parallel branches write only to their own vars |
| `LOGGING … LEVEL INFO/ERROR/WARN` | `LOGGING` | Structured log emission at named severity levels; supports f-string interpolation |
| `EXCEPTION WHEN ModelUnavailable THEN … RETURN … WITH status='failed'` | `EXCEPTION WHEN <Type> THEN … RETURN … WITH <k>=<v>` | Hard-error path; non-trivial status token `'failed'` signals caller |
| `EXCEPTION WHEN BudgetExceeded THEN … RETURN @report WITH status='truncated'` | `EXCEPTION WHEN <Type> THEN … RETURN @<var> WITH <k>=<v>` | Graceful-degradation path; non-trivial status token `'truncated'` signals partial output |

---

### 4. Logical Functions / Prompts

**`merge_reviews`**

- **Role:** Final synthesis step. Consolidates the three independently produced review artifacts into one coherent, prioritised engineering brief.
- **Key prompt conventions:**
  - Persona: "senior engineering lead" — establishes authoritative, actionable voice.
  - Three labelled input blocks injected via `{style}`, `{sec_audit}`, `{tests}` slots, matching the three parallel outputs.
  - Mandates exactly three output sections with bold Markdown headers: **Action Items**, **Test Coverage**, **Summary**.
  - Explicit constraint: Action Items section must stay under 150 words.
  - Test cases must appear verbatim inside a fenced code block — preserves formatting for downstream tooling.
  - Closes with a binary-leaning qualitative signal ("is this code production-ready?") in the Summary paragraph.

*(The three sub-workflow prompt templates — `style_review`, `security_audit`, `test_generator` — are defined in their respective imported modules and are not inlined here.)*

---

### 5. Control Flow

1. **Initialisation** — WORKFLOW starts, logs entry with `lang` and `review_model` values at INFO level.
2. **Fan-out (CALL PARALLEL)** — `style_review`, `security_audit`, and `test_generator` are dispatched concurrently. All three receive `@code`, `@lang`, `@review_model`, and `@log_dir` as named arguments. Execution blocks here until all three branches resolve.
3. **Merge (GENERATE)** — `merge_reviews` is called with the three feedback variables; the LLM produces `@report` within the 1 024-token budget.
4. **Termination** — Final INFO log records report length; `@report` is returned to the caller (implicit success path, no status token needed).
5. **Exception paths** (non-trivial RETURN):
   - `ModelUnavailable` → returns a static error string with `status='failed'`; caller must treat the output as unusable.
   - `BudgetExceeded` → returns `@report` (potentially partial) with `status='truncated'`; caller can still use the output but should flag incompleteness.

There is no WHILE loop; the workflow is a single-pass fan-out/merge with no iteration.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Produce a consolidated, prioritised code-review report \
  by running style, security, and test-generation checks concurrently on a code snippet \
  and merging their outputs into a single senior-engineer-level action plan." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile parallel_code_review.spl --lang python/pocketflow
spl3 splc compile parallel_code_review.spl --lang python/langgraph
spl3 splc compile parallel_code_review.spl --lang go
```