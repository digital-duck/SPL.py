# File Comparison Report

**Files Compared:**
- File 1: `pocketflow-agent-claude_cli-claude-sonnet-4-6-spec.md` (.md)
- File 2: `pocketflow-agent-openrouter-gemini-31-pro-spec.md` (.md)
- **Adapter:** claude_cli
- **Model:** default
- **Focus:** all
- **Generated:** 2026-05-01 13:03:55


---

## Summary

Both files document the same ReAct research agent compiled to PocketFlow, but File 1 (claude-sonnet-4-6) is substantially stronger — it reads as a primary specification, while File 2 (gemini-3.1-pro) reads as a condensed summary. File 1 is more precise in its termination semantics, more complete in its construct mapping, and more actionable in its regeneration instructions.

---

## Content Analysis

### File 1 Strengths

- **Termination semantics are exact.** The note in Section 4 — "at most `max_iterations` search calls and `max_iterations + 1` decide calls" — is a non-obvious invariant that directly matters when reasoning about cost and correctness. File 2 omits this entirely.
- **Negative space coverage.** The `EXCEPTION WHEN NetworkError` row in the mapping table explicitly records what is *not* implemented, which is critical for anyone trying to harden the agent or port it to SPL. File 2 silently omits this.
- **YAML robustness detail.** Section 3 documents the self-healing prompt pattern (`"If syntax errors occur, immediately provide a corrected version"`) and the regex extraction path for `search_query`. These are operational details that affect real-world reliability and are absent in File 2.
- **Adapter externalization contrast.** The mapping row explicitly flags that `_call_llm("llama3.2", ...)` is hardcoded to Ollama localhost, contrasting it with SPL's `--adapter` flag. This is architecturally important given the DODA principle in this codebase.
- **Section 5 is immediately runnable.** The `spl3 run` command includes concrete `--param` values and a `--target` example, making it copy-pasteable.
- **ASCII control-flow diagram.** The visual in Section 4 captures the back-edge loop topology in a way that prose alone cannot — it also correctly shows that `EVALUATE` is a separate step from `WHILE`.

### File 2 Strengths

- **Crisper Section 0.** The high-level description is more linear and easier to scan on first read. It avoids the parenthetical density of File 1's opening paragraph.
- **ETL framing in the mapping table.** File 2 consistently uses the "ETL node pattern" vocabulary (`prep()` / `exec()` / `post()`), which is the canonical PocketFlow mental model. File 1 uses this vocabulary inconsistently.
- **Section 4 uses numbered steps.** The prose walkthrough in ordered list form is easier to follow sequentially than File 1's hybrid ASCII-diagram approach for readers unfamiliar with SPL syntax.
- **Table column alignment.** File 2 uses `:---` left-alignment markers in the markdown table, which renders more consistently across viewers.

### Common Elements

- Sections 0–5 structure is identical.
- Both cover the same six SPL constructs: `WORKFLOW`, `CREATE FUNCTION`, `GENERATE`, `CALL`, `EVALUATE`, `WHILE`/`RETURN`.
- Both correctly identify `DecideNode.post()` as the routing locus and `shared` dict as the variable store analog.
- Both document the `action: search` / `action: answer` sentinel pattern.
- Both cover the two prompt functions (`DecideAction`, `AnswerQuestion`) with role + key conventions.
- Both reference `spl3 text2spl`, `spl3 splc compile`, and the three target runtimes.

---

## Detailed Comparison

### Structure & Organization

File 1 has six fully fleshed sections with consistent depth. File 2 has the same six sections but Section 5 is a stub — the `--description` argument is left as `"<paste Section 0 here>"` rather than providing the actual text, and the `spl3 run` step is omitted entirely. This makes File 2's Section 5 non-actionable without File 1 as a reference.

File 1's mapping table has 16 rows; File 2's has 8. File 2 collapses `GENERATE` and `CALL` into single rows that cover both use cases, losing the instance-level traceability. File 1 maps each SPL statement to its specific Python expression, which is more useful for a port or audit.

### Logic & Completeness

The most significant logical gap in File 2 is in the termination description. File 2 says the WHILE loop is "governed by `@iteration < @max_iterations`" but this is only half-correct — the guard fires in `DecideNode.post()` *before* the LLM is queried on that iteration, not after. File 1 explicitly documents this off-by-one distinction. Getting this wrong leads to incorrect cost estimates and mismatched SPL reconstruction.

File 2 also omits:
- The `@context` initialization string (`"Initial question: " + @question`)
- The dual-status RETURN path (`status='complete'` vs `status='max_iterations'`)
- The `'action: "answer"'` YAML quoting variant in the routing condition

File 1 covers all three.

### Quality & Sophistication

File 1 is a primary specification; File 2 is a summary. The prompt engineering notes in File 1 Section 3 (chain-of-thought scaffold, YAML repair instruction, regex extraction) reflect production-level awareness of LLM failure modes. File 2's Section 3 is accurate but surface-level — it describes *what* the prompts do but not *how* they guard against failure.

The ASCII diagram in File 1 Section 4 correctly captures the graph topology as a loop with an explicit back-edge label, which is the PocketFlow-idiomatic way to think about it. File 2's numbered list is cleaner to read but loses the topology signal.

### Syntax & Technical Accuracy

Both files are syntactically correct markdown. File 1's inline code spans are more consistent — every SPL keyword and variable name is backtick-wrapped. File 2 is less consistent (e.g., `@var` in the table header row is plain text, not code-formatted).

File 2 has one technical inaccuracy: in the mapping table, `RETURN` is mapped to `AnswerNode.post() returning None`, with the note "Final variables are flushed to the console/state." The `shared` dict is not "flushed" — it persists in memory and is read by the caller. This is a minor but misleading description.

File 1's Section 5 uses `spl3 splc compile react_research.spl --lang python/pocketflow`, which aligns with the `spl3 splc` command documented in `CLAUDE.md`. File 2 uses `spl3 splc compile <output.spl>` with a placeholder, which is less useful.

---

## Recommendations

**1. Best Choice:** File 1. It is the authoritative specification. Any consumer trying to reconstruct the SPL source, audit the agent's behavior, or port it to another runtime should use File 1. File 2 is useful only as a quick orientation.

**2. Improvements for File 2:**
- Fill in Section 5 with the concrete `spl3 run` command and actual `--description` text.
- Add the missing mapping rows: `@context` accumulator, `@iteration` counter, max-iterations guard, `EXCEPTION WHEN NetworkError`, and the adapter/model row.
- Correct the termination description: the max-iterations guard fires *before* querying the LLM on the capped iteration, not after.
- Add the termination count invariant ("at most N search calls, N+1 decide calls") to Section 4.
- Document the YAML quoting variant (`'action: "answer"'`) in Section 3 or the mapping table.

**3. Hybrid Approach:** Use File 1 as the base and adopt two things from File 2: (a) rewrite Section 0 with File 2's cleaner linear prose, then append File 1's detail as a second paragraph; (b) add File 2's `prep()` / `exec()` / `post()` ETL framing as a "Notes" column supplement in the mapping table, since it's the idiomatic PocketFlow vocabulary that a reader coming from PocketFlow docs will expect.

---

## Scoring

| Dimension | File 1 (claude-sonnet-4-6) | File 2 (gemini-3.1-pro) |
|---|---|---|
| **Structure** | 9/10 | 7/10 |
| **Logic** | 9/10 | 6/10 |
| **Quality** | 9/10 | 6/10 |
| **Overall** | **9/10** | **6/10** |

The 3-point gap on Logic reflects the missing termination invariant and the off-by-one ambiguity in File 2 — for a specification document, those are load-bearing omissions. The Structure gap is driven entirely by File 2's incomplete Section 5 and the collapsed mapping table.



---

*Generated by SPL semantic comparison tool*
