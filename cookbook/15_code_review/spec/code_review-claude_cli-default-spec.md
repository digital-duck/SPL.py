## Summary

This workflow performs a multi-pass automated code review by running four independent LLM analysis passes (security, performance, style, and bug detection), scoring each for severity, then synthesizing all findings into a single structured review document. It accepts either a file path or raw code text as input and writes per-pass findings and a final report to disk. Development teams and CI pipelines benefit by getting a consistent, machine-generated code review gate before human review.

---

## Detailed Specification

### 1. Purpose

Automatically review submitted code across four quality dimensions — security, performance, style, and bug detection — and produce a severity-gated verdict that signals whether the code should be approved, revised, or blocked.

---

### 2. High-level Description

The WORKFLOW `code_review` accepts either a raw code string or a file path and an optional log directory. It begins with a CALL to `read_file` and an EVALUATE branch: if the file read returns content, it uses that; otherwise it falls back to the raw input string. A bounded GENERATE call to `detect_lang` identifies the programming language from the code, trimming whitespace from the result to ensure a clean value.

Four sequential GENERATE passes then execute against the normalized code: `security_audit`, `performance_review`, `style_review`, and `bug_detection`, each writing its findings to a dedicated Markdown file via CALL to `write_file`. Three additional GENERATE calls to `severity_score` quantify the security, performance, and bug findings as numeric scores stored in @vars. A final GENERATE call to `synthesize_review` combines all findings and scores into a unified review document, also written to disk.

The workflow concludes with an EVALUATE on the security score: a score above 8 triggers RETURN with `status='critical_issues'` and `verdict='block'`; above 5 yields `status='needs_fixes'` and `verdict='request_changes'`; otherwise `status='approved'` and `verdict='approve'`. Two EXCEPTION handlers cover edge cases: `ContextLengthExceeded` falls back to a summarize-then-quick-review path, and `BudgetExceeded` exits early after flushing whatever security findings were produced.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| WORKFLOW `code_review` | `WORKFLOW code_review` | Declares the top-level orchestration entry point |
| CREATE FUNCTION `detect_lang` | `CREATE FUNCTION detect_lang(code TEXT)` | Reusable prompt template; bounded one-word output |
| CALL `read_file` | `CALL read_file(@code) INTO @file_content` | Side-effect tool; reads file from disk |
| CALL `write_file` | `CALL write_file(...) INTO NONE` | Side-effect tool; persists findings to Markdown files |
| GENERATE (analysis passes) | `GENERATE security_audit(...) INTO @security_findings` | LLM call; repeated for perf, style, bug, score, synthesize |
| GENERATE (scoring) | `GENERATE severity_score(@findings) INTO @score` | LLM call returning a numeric score for gating |
| EVALUATE (file vs raw) | `EVALUATE @file_content WHEN != '' THEN ... ELSE ... END` | Branch to resolve input type |
| EVALUATE (verdict gate) | `EVALUATE @sec_score WHEN > 8 THEN ... WHEN > 5 THEN ... ELSE ... END` | Three-way branch on security severity |
| RETURN WITH status= | `RETURN @review WITH status='critical_issues', verdict='block'` | Non-trivial: drives three distinct downstream outcomes |
| EXCEPTION `ContextLengthExceeded` | `EXCEPTION WHEN ContextLengthExceeded THEN ...` | Fallback: summarize then quick-review for oversized code |
| EXCEPTION `BudgetExceeded` | `EXCEPTION WHEN BudgetExceeded THEN ...` | Partial exit: returns only security findings completed so far |
| Shared state (@vars) | `@code_to_review`, `@language`, `@*_findings`, `@*_score`, `@review` | Passed between all GENERATE and CALL steps |

---

### 4. Logical Functions / Prompts

**`detect_lang`**
- Role: Identifies the programming language of the submitted code before any analysis begins.
- Key conventions: Strict output constraint ("reply with only the language name — nothing else"); result is trimmed before use to prevent downstream prompt contamination.

**`security_audit`**
- Role: Pass 1 — scans code for security vulnerabilities (e.g., injection, unsafe eval, exposed secrets).
- Key conventions: Receives both code and detected language; output is free-form Markdown findings.

**`performance_review`**
- Role: Pass 2 — identifies performance bottlenecks, inefficient algorithms, or resource waste.
- Key conventions: Same input signature as `security_audit`; output is Markdown.

**`style_review`**
- Role: Pass 3 — evaluates code style, naming conventions, and language-specific best practices.
- Key conventions: Same input signature; findings written to `style.md`.

**`bug_detection`**
- Role: Pass 4 — detects logic errors, off-by-one mistakes, null dereferences, and similar defects.
- Key conventions: Same input signature; findings written to `bugs.md`.

**`severity_score`**
- Role: Converts free-form findings text into a numeric severity score used for the verdict gate.
- Key conventions: Called independently for security, performance, and bug findings; numeric output is used directly in EVALUATE comparisons (> 8, > 5).

**`synthesize_review`**
- Role: Merges all four findings sets and their scores into a single structured review document.
- Key conventions: Receives all findings plus three severity scores; output written to `review.md` and returned as the workflow's primary OUTPUT.

**`summarize_code`** *(exception path only)*
- Role: Produces a condensed code summary when the original exceeds the context window.
- Key conventions: Used only under `ContextLengthExceeded`; output feeds `quick_review`.

**`quick_review`**
- Role: Performs a lightweight holistic review on the summarized code when a full pass is impossible.
- Key conventions: Accepts summary and language; returns a partial review with `status='partial_large_file'`.

---

### 5. Control Flow

**Input resolution:** The workflow begins with CALL `read_file`; EVALUATE branches on whether a non-empty file was loaded, setting `@code_to_review` accordingly.

**Language detection:** A single GENERATE to `detect_lang` produces a trimmed language label stored in `@language`. No looping; this is a one-shot deterministic call.

**Four analysis passes (linear):** `security_audit` → `performance_review` → `style_review` → `bug_detection` execute sequentially, each followed by CALL `write_file`. No branching between passes.

**Scoring:** Three parallel-intent GENERATE calls to `severity_score` produce `@sec_score`, `@perf_score`, and `@bug_score`.

**Synthesis:** GENERATE `synthesize_review` combines everything; result written to `review.md`.

**Verdict gate:** EVALUATE on `@sec_score` produces one of three RETURN paths:
- `@sec_score > 8` → RETURN WITH `status='critical_issues'`, `verdict='block'`
- `@sec_score > 5` → RETURN WITH `status='needs_fixes'`, `verdict='request_changes'`
- else → RETURN WITH `status='approved'`, `verdict='approve'`

**Exception paths:**
- `ContextLengthExceeded`: summarize → quick review → write → RETURN WITH `status='partial_large_file'`
- `BudgetExceeded`: flush partial security findings → RETURN WITH `status='security_only'`

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (use Section 2, High-level Description as text2spl input)
spl3 text2spl --description "The WORKFLOW code_review accepts either a raw code string or a file path and an optional log directory. It begins with a CALL to read_file and an EVALUATE branch: if the file read returns content, it uses that; otherwise it falls back to the raw input string. A bounded GENERATE call to detect_lang identifies the programming language from the code, trimming whitespace from the result to ensure a clean value. Four sequential GENERATE passes then execute against the normalized code: security_audit, performance_review, style_review, and bug_detection, each writing its findings to a dedicated Markdown file via CALL to write_file. Three additional GENERATE calls to severity_score quantify the security, performance, and bug findings as numeric scores stored in @vars. A final GENERATE call to synthesize_review combines all findings and scores into a unified review document, also written to disk. The workflow concludes with an EVALUATE on the security score: a score above 8 triggers RETURN with status='critical_issues' and verdict='block'; above 5 yields status='needs_fixes' and verdict='request_changes'; otherwise status='approved' and verdict='approve'. Two EXCEPTION handlers cover edge cases: ContextLengthExceeded falls back to a summarize-then-quick-review path, and BudgetExceeded exits early after flushing whatever security findings were produced." --mode workflow

# Step 2 — compile to any target
spl3 splc compile code_review.spl --lang python/pocketflow
spl3 splc compile code_review.spl --lang python/langgraph
spl3 splc compile code_review.spl --lang go
```