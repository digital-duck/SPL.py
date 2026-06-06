## Summary

This workflow performs a structured, multi-pass automated code review on any submitted source file or raw code snippet. It runs four independent LLM analysis passes — security, performance, style, and bug detection — then scores the severity of each category and synthesizes findings into a single structured review with a final verdict. Engineering teams and CI pipelines benefit by getting consistent, multi-dimensional feedback without relying on a single monolithic prompt.

---

## Detailed Specification

### 1. Purpose

Automatically review submitted source code across four quality dimensions (security, performance, style, bug detection), assign severity scores, synthesize findings into a structured report, and emit a machine-readable verdict (`approve`, `request_changes`, or `block`) based on the security score.

---

### 2. High-level Description

The workflow accepts either a file path or a raw code string as input; it uses a `CALL read_file` side-effect to resolve file paths, then uses `EVALUATE` on the resulting content to determine whether `@code_to_review` should be set to the file's text or the original input. A `CREATE FUNCTION detect_lang` makes a bounded LLM call to identify the programming language from the code alone, producing a single-token reply that is trimmed and logged. Four sequential `GENERATE` calls then run `security_audit`, `performance_review`, `style_review`, and `bug_detection` against the code and detected language, with each result persisted to disk via `CALL write_file`. Three additional `GENERATE severity_score` calls assign a numeric severity (0–10) to the security, performance, and bug findings; all six intermediate results are accumulated in named `@vars` that are passed together into a final `GENERATE synthesize_review` call that produces the consolidated `@review`. The workflow closes with an `EVALUATE` on `@sec_score` that drives a three-way `RETURN` — `status='critical_issues'`/`verdict='block'` for scores above 8, `status='needs_fixes'`/`verdict='request_changes'` for scores above 5, and `status='approved'`/`verdict='approve'` otherwise. Two `EXCEPTION` handlers cover edge cases: `ContextLengthExceeded` falls back to a two-step summarize-then-quick-review path with `status='partial_large_file'`, and `BudgetExceeded` short-circuits after the security pass with `status='security_only'`.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| PocketFlow `Node` (language detect) | `CREATE FUNCTION detect_lang(code TEXT)` | Bounded single-token output; trimmed after generation |
| PocketFlow `Flow` | `WORKFLOW code_review` | Top-level orchestration unit with `INPUT:`/`OUTPUT:` |
| File resolution node | `CALL read_file(@code) INTO @file_content` | Side-effect; non-empty result triggers file path branch |
| File/raw-code branch | `EVALUATE @file_content WHEN != '' THEN ... ELSE ... END` | Sets `@code_to_review`; no loop, pure branch |
| Four analysis passes | `GENERATE security_audit / performance_review / style_review / bug_detection INTO @var` | Sequential LLM calls; each result written to disk immediately |
| Severity scoring | `GENERATE severity_score(...) INTO @sec_score / @perf_score / @bug_score` | Numeric 0–10 output per category |
| Final synthesis | `GENERATE synthesize_review(...) INTO @review` | Accepts all six intermediate `@vars` in one call |
| Verdict branch | `EVALUATE @sec_score WHEN > 8 ... WHEN > 5 ... ELSE ... END` | Drives three distinct `RETURN` outcomes |
| Non-trivial return tokens | `RETURN @review WITH status='critical_issues'/'needs_fixes'/'approved'` | Machine-readable verdict; consumed by CI caller |
| Log file persistence | `CALL write_file(f'{@log_dir}/...', @var) INTO NONE` | Side-effect; no return value needed |
| Large-file fallback | `EXCEPTION WHEN ContextLengthExceeded THEN GENERATE summarize_code → quick_review` | Two-step degraded path; `status='partial_large_file'` |
| Budget fallback | `EXCEPTION WHEN BudgetExceeded THEN RETURN @security_findings WITH status='security_only'` | Returns partial result rather than failing |
| Shared state | `@code_to_review`, `@language`, `@security_findings`, `@perf_findings`, `@style_findings`, `@bug_findings`, `@sec_score`, `@perf_score`, `@bug_score`, `@review` | All accumulated in workflow scope; passed explicitly to downstream `GENERATE` calls |

---

### 4. Logical Functions / Prompts

**`detect_lang`** (defined via `CREATE FUNCTION`)
- Role: Identifies the programming language of the submitted code with a deterministic-style, single-token response.
- Key conventions: System persona is "polyglot programmer"; output is constrained to the language name only — no prose, no explanation. Result is trimmed before use to strip whitespace.

**`security_audit`** (implied `CREATE FUNCTION`)
- Role: Scans code for security vulnerabilities (injection, unsafe calls, credential leaks, etc.) scoped to the detected language.
- Key conventions: Receives `@code_to_review` and `@language`; expected to return structured Markdown findings.

**`performance_review`** (implied `CREATE FUNCTION`)
- Role: Identifies algorithmic inefficiencies, unnecessary allocations, blocking calls, and language-specific performance anti-patterns.
- Key conventions: Same two-argument signature as `security_audit`; Markdown output written to `performance.md`.

**`style_review`** (implied `CREATE FUNCTION`)
- Role: Evaluates code style, naming conventions, idiomatic usage, and adherence to best practices for the detected language.
- Key conventions: Markdown output; no severity score is computed for style (style findings are passed raw to synthesis).

**`bug_detection`** (implied `CREATE FUNCTION`)
- Role: Finds logic errors, off-by-one issues, null dereferences, unreachable code, and other correctness defects.
- Key conventions: Markdown output; feeds both `@bug_findings` to synthesis and a severity score.

**`severity_score`** (implied `CREATE FUNCTION`)
- Role: Takes a block of findings text and returns a single numeric score from 0–10 representing the aggregate severity of the issues found.
- Key conventions: Called three times (security, performance, bugs); output is used directly in `EVALUATE` comparisons, so the prompt must constrain output to a bare integer or simple decimal.

**`synthesize_review`** (implied `CREATE FUNCTION`)
- Role: Merges all four findings blocks and their scores into a single structured review document suitable for human consumption.
- Key conventions: Accepts seven arguments (four findings, three scores); expected to produce a comprehensive Markdown report saved as `review.md`.

**`summarize_code`** (implied `CREATE FUNCTION`, exception path only)
- Role: Produces a condensed description of the code when the full source exceeds the context window.
- Key conventions: Used only in the `ContextLengthExceeded` fallback before `quick_review`.

**`quick_review`** (implied `CREATE FUNCTION`, exception path only)
- Role: Performs a lightweight review on the code summary rather than the full source, trading depth for feasibility.
- Key conventions: Accepts the summary and `@language`; result written to `review.md` with `status='partial_large_file'`.

---

### 5. Control Flow

**Entry:** The workflow resolves the input — `CALL read_file` is always attempted; `EVALUATE` on the result selects either the file content or the raw code string as `@code_to_review`.

**Linear analysis phase:** `GENERATE detect_lang` → four sequential `GENERATE` analysis passes → three `GENERATE severity_score` calls → one `GENERATE synthesize_review`. Each analysis result is persisted to disk immediately after generation. There are no loops; this phase is a straight pipeline.

**Verdict branch:** `EVALUATE @sec_score` applies two numeric thresholds in descending order. A score above 8 issues `RETURN WITH status='critical_issues', verdict='block'`; above 5 issues `RETURN WITH status='needs_fixes', verdict='request_changes'`; otherwise `RETURN WITH status='approved', verdict='approve'`. The security score is the sole gate — performance and bug scores inform the synthesized report but do not affect the verdict directly.

**Exception paths:** `ContextLengthExceeded` intercepts before or during any analysis pass and reroutes through a two-step summarize → quick-review path, terminating with `status='partial_large_file'`. `BudgetExceeded` short-circuits at whatever point funds are exhausted, writing out whatever security findings were already produced and terminating with `status='security_only'`. Both handlers ensure a `review.md` artifact is emitted even in degraded scenarios.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Automatically review submitted source code across four quality dimensions (security, performance, style, bug detection), assign severity scores, synthesize findings into a structured report, and emit a machine-readable verdict (approve, request_changes, or block) based on the security score." --mode workflow

# Step 2 — compile to any target
spl3 splc compile code_review.spl --lang python/pocketflow
spl3 splc compile code_review.spl --lang python/langgraph
spl3 splc compile code_review.spl --lang go
```