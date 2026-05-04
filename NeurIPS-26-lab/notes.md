# NeurIPS-26 Lab — Issue Log

Issues found during experiments. Fixed iteratively with Claude Code CLI.

Format:
```
## [date] [recipe] [model] — short title
- symptom
- fix applied / workaround
- status: open | fixed | wontfix
```

---

## [2026-05-03] R2-rag / claude_cli / sonnet — S2 text2mmd render failure

**Symptom:** Generated `.mmd` failed to render in browser. HTML showed error container.

**Root causes (4):**
1. `\n` inside unquoted node labels (`C[foo\nbar]`) — renders as literal `\n`, not a line break
2. Unicode arrow `→` inside a label (`split texts → chunks`) — breaks Mermaid parser
3. `{{text}}` (hexagon) used for decision nodes — prompt was instructing wrong shape; `{text}` is the correct diamond/rhombus
4. `B --> OW` — edge targeting a subgraph name instead of the first node inside it; first node (`C`) was unreachable

**Fix applied to source (`spl3/cli.py`):**
- `fix_mermaid_syntax()`: added post-processing for `\n` → `<br/>` (with label quoting), Unicode `→` → `->`, removed the broken `{text}` → `{{text}}` conversion that was causing #3
- Prompt: corrected decision node to `{text}` (diamond), added explicit rules against `\n`, Unicode arrows, and subgraph-name edge targets; updated example to match

**Additional issues found on first regeneration:**
5. `-. "text" .-->` — invalid dotted-edge-with-label syntax (correct: `-.->|text|`)
6. `[("text")]` — non-standard cylindrical shape that confuses the parser (correct: `["text"]`)
7. Validator was generating false positives (split regex double-escaped, `{text}` → double-brace rule was backwards). Validator rewritten.

**Status:** fixed at source — regenerated S2 cleanly with no warnings

---

## [2026-05-03] R2-rag / claude_cli / sonnet — S3 LLM preamble before code fence

**Symptom:** `Validation: FAILED — Lexer error at 3:1: Unexpected character '\`'` — file started with "Let me check the existing SPL files..." prose then `` ```spl ``.

**Root cause:** `mmd2spl` fence-stripper checked only `lines[0]` for the opening fence. When the LLM adds preamble prose before the code block, the fence is on a later line and the check misses it, leaving the preamble + backtick in the output.

**Fix applied to source (`spl3/cli.py` `cmd_mmd2spl`):**
- Replaced `lines[0]` check with `next(i for i, l in enumerate(lines) if re.match(r"^```(spl)?\s*$", ...))` to find the opening fence anywhere in the response
- Updated prompt: added "no preamble, no markdown fences" to output instruction

**Status:** fixed at source — re-run mmd2spl for R2

---

## [2026-05-03] R2-rag / claude_cli / sonnet — S3 two WORKFLOW syntax errors

**Symptom:** `spl3 validate` reported `Parse error at 11:23: Expected DO, got SEMICOLON`.

**Root causes (2):**
1. `INPUT @question TEXT;` — semicolons after INPUT/OUTPUT declarations are invalid; correct syntax has no semicolons and all inputs comma-separated on one line
2. `DO ... END;` body wrapper inside the WORKFLOW, followed by a second `END;` — the WORKFLOW body is simply `DO ... END;` with no nesting; the extra `END;` caused a second parse error

**Root cause of both:** `_MMD2SPL_PROMPT` itself showed `INPUT @question TEXT;` with a semicolon as the example, teaching the LLM the wrong syntax.

**Fix applied to source (`spl3/cli.py` `_MMD2SPL_PROMPT`):**
- Replaced rule #1/2 with a concrete syntax block showing correct WORKFLOW structure: INPUT/OUTPUT before DO, no semicolons, single END; closes the workflow
- Added explicit IMPORTANT notes against semicolons and nested DO...END; wrappers

**Fix applied to file:** Merged INPUT lines, removed semicolons, removed extra END;

**Status:** fixed at source — validate passes

---

## [2026-05-03] R1-agent / claude_cli / claude — S3 mmd2spl truncated output

**Symptom:** `S3-agent-claude_cli-claude.spl` contained only 6 lines, ending mid-way through the first prompt template body.

**Root cause:** `mmd2spl` fence-stripping used a non-greedy regex `r"```spl\s*\n(.*?)\n```"`. When the LLM embeds an inner ` ```yaml ` code block inside a `CREATE FUNCTION` prompt template body, the `.*?` stops at that inner closing ` ``` ` rather than the outer one, discarding the rest of the SPL.

**Fix applied to source (`spl3/cli.py` `cmd_mmd2spl`):**
- Replaced regex fence-stripper with line-based stripping: check first line for `` ```spl `` / `` ``` `` opening, check last line for `` ``` `` closing, trim only those two lines. Inner fences are no longer touched.

**Status:** fixed at source — re-run S3 for R1

---

## [2026-05-03] R1-agent / claude_cli / sonnet — S2 decision node wrong shape

**Symptom:** `C{{Action == 'search'?}}` rendered as a hexagon instead of a diamond in the Mermaid diagram.

**Root cause:** `{{text}}` is Mermaid hexagon shape; `{text}` is the correct diamond/rhombus for decision nodes. The LLM used double-braces.

**Fix applied:** Replaced `{{Action == 'search'?}}` → `{Action == 'search'?}` directly in the .mmd file.

**Status:** fixed

---

## [2026-05-03] R2-rag / claude_cli / sonnet — S2 duplicate START edge

**Symptom:** `START --> A` appeared twice in the .mmd (line 2 and line 32), creating a duplicate edge in the rendered diagram.

**Root cause:** LLM emitted `START --> A` both at the top of the flowchart and again in the cross-subgraph connections section.

**Fix applied:** Removed the redundant `START --> A` from line 32 directly in the .mmd file.

**Status:** fixed

---

## [2026-05-03] R2-rag / S1 (splc describe) — "RETURN default" noise in spec

**Symptom:** S1 spec included "each step RETURNs a `"default"` action token" which propagated into S2 as double-edges labeled `RETURN default` between every node pair.

**Root cause:** `_SPLC_DESCRIBE_PROMPT` instructed the LLM to document all RETURN mappings; PocketFlow's unconditional `return "default"` (linear advance) was treated as a meaningful construct.

**Fix applied to source (`spl3/splc/cli.py`):**
- Added IMPORTANT block in prompt: suppress trivial "default" transitions; only document RETURN when status is non-trivial and drives a real branch/loop
- Updated §0, §2, §4 prompt sections to omit "default" token documentation

**Safety net (`spl3/cli.py` `fix_mermaid_syntax`):**
- Added `re.sub` to strip `|"RETURN default"|` and `|RETURN default|` edge labels from any LLM-generated Mermaid

**Status:** fixed at source

---

## [2026-05-03] R2-rag / claude_cli / sonnet — S3 write_file wrong arity

**Symptom:** `CALL write_file(@output_path, @query, @generated_answer)` — stdlib `write_file` takes `(path, content)` not 3 args; `@query` would be written as content and `@generated_answer` silently passed as mode.

**Root cause:** LLM-generated SPL passed both query and answer as separate positional args.

**Fix applied to file (`S3-rag-claude_cli-sonnet.spl`):**
- Removed `@query` arg: `CALL write_file(@output_path, @generated_answer)`

**Status:** fixed

---

## [2026-05-03] R5-research / claude_cli / sonnet — S3 write_file args reversed

**Symptom:** `CALL write_file(@report, @out)` — args in wrong order; `@report` (content) was passed as path and `@out` (path) as content.

**Root cause:** LLM-generated SPL swapped the argument order.

**Fix applied to file (`S3-research-claude_cli-sonnet.spl`):**
- Swapped to correct order: `CALL write_file(@out, @report)`

**Status:** fixed

---

## [2026-05-03] R2-rag / S3-run — RAG CALL functions missing from stdlib

**Symptom:** `spl3 run` failed because `chunk_documents`, `embed_documents`, `create_faiss_index`, `embed_query`, `retrieve_document` are not stdlib tools.

**Root cause:** These are deterministic data-transformation operations specific to the RAG recipe; correctly expressed as CALL (not GENERATE) in the SPL but have no stdlib implementation.

**Fix applied:**
- Created `tests/claude_cli/sonnet/tools.py` with all five functions using ollama `qwen3-embedding:0.6b` (local, no API key) for embeddings and FAISS for indexing/retrieval
- Created `tests/claude_cli/sonnet/test_docs.txt` with 7 diverse test documents (one per line)
- Installed `faiss-cpu` and `ollama` Python packages in `spl123` conda env

**Status:** fixed — S3-run passes

---

## [2026-05-03] R4-thinking / S3-run — CoT helper CALL functions missing from stdlib

**Symptom:** `spl3 run` failed because `format_thoughts_to_text`, `extract_last_plan`, `validate_yaml_fields`, `append_thought`, `extract_yaml_field`, `print_thought_progress` are not stdlib tools.

**Root cause:** Pure data-manipulation helpers for managing the JSON thoughts array and YAML field extraction; correctly expressed as CALL but have no stdlib implementation.

**Fix applied:**
- Created `tests/claude_cli/sonnet/tools.py` with all six functions using Python `json` and `yaml` (PyYAML)

**Status:** fixed

---

## [2026-05-03] R4-thinking / S3-run — WHILE loop never enters (LLM calls: 0)

**Symptom:** Workflow reported `LLM calls: 0`, `RETURN: 0 chars | status=complete`. Loop body never executed.

**Root cause (`spl/executor.py` `_exec_while`):** When a WHILE condition is a `Condition` node, the executor tried `float(left_val)` for numeric comparison. For string operands like `@next_thought_needed = "true"`, `float("true")` raises `ValueError` and the except block silently set `should_continue = False`. The loop never entered.

**Fix applied to source (`spl/executor.py`):**
- Added string comparison fallback after float conversion failure: `=` maps to `ls == rs`, `!=`/`<>` maps to `ls != rs`

**Status:** fixed at source

---

## [2026-05-03] R4-thinking / S3-run — AND compound WHILE condition right-hand side discarded

**Symptom:** `WHILE @yaml_valid = "false" AND @retry_count < 3 DO` — only the left side was evaluated; `@retry_count < 3` was silently dropped, allowing infinite retries.

**Root cause (`spl/parser.py` `_parse_while_condition`):** The AND/OR handler called `_parse_expression()` for right-hand sub-conditions but discarded the result, returning only the initial left-side `Condition`.

**Fix applied to source (`spl/parser.py` + `spl/ast_nodes.py`):**
- Added `CompoundCondition` dataclass (`conditions: list`, `conjunctions: list`) to `spl/ast_nodes.py`
- Rewrote AND/OR loop in `_parse_while_condition` to accumulate all arms into `CompoundCondition`
- Added `CompoundCondition` evaluation branch in `spl/executor.py` `_exec_while`

**Note:** spl3 already had its own `CompoundCondition` (binary `left/right/operator` tree) in `spl3/ast_nodes.py` with its own `_parse_while_condition` override — the spl2 path is fixed here; spl3 path fixed separately below.

**Status:** fixed at source

---

## [2026-05-03] R4-thinking / S3-run — spl3 executor string equality in WHILE condition

**Symptom:** After above fixes, R4 ran but produced only 3 LLM calls and empty `@current_thinking` at RETURN.

**Root cause (`spl3/executor.py` `_eval_while_cond`):** The spl3 executor's own WHILE condition evaluator had the same `float()` silent-False fallback bug for `Condition` nodes. Since spl3 overrides `_exec_while` and intercepts `CompoundCondition` before delegating to spl2, the spl2 fix was never reached.

**Fix applied to source (`spl3/executor.py`):**
- Same string comparison fallback added to `_eval_while_cond` for the `Condition` case

**Status:** fixed at source

---

## [2026-05-03] R4-thinking / tools.py — YAML bool coercion produces wrong-case string

**Symptom:** `extract_yaml_field(@thought_data, "next_thought_needed")` returned `"True"` / `"False"` (capital first letter). WHILE condition `@next_thought_needed = "true"` then failed string equality, causing premature loop exit.

**Root cause:** `yaml.safe_load` parses unquoted YAML `true`/`false` as Python `bool`. `str(True)` = `"True"` and `str(False)` = `"False"` — mismatched case against SPL string literals.

**Fix applied to file (`tools.py` `extract_yaml_field`):**
- Added explicit bool check: `if isinstance(value, bool): return "true" if value else "false"`

**Status:** fixed

---

## [2026-05-03] R4-thinking / tools.py — LLM wraps YAML in markdown code fences

**Symptom:** `chain_of_thought_trace.md` showed `yaml_valid=false` for every retry and empty `@current_thinking` / `@next_thought_needed` at RETURN. Claude was producing valid YAML but wrapped in ` ```yaml ... ``` ` markdown fences, causing `yaml.safe_load` to throw a parse error.

**Root cause:** Claude defaults to fenced code blocks in chat responses. `validate_yaml_fields`, `extract_yaml_field`, and `append_thought` all called `yaml.safe_load` on the raw LLM output without stripping fences first.

**Fix applied to file (`tools.py`):**
- Added `_strip_fences(text)` helper using `re.match(r'^```(?:yaml)?\s*\n?(.*?)\n?```\s*$', ...)` with `re.DOTALL`
- Applied `_strip_fences` in `validate_yaml_fields`, `extract_yaml_field`, and `append_thought` before parsing

**Fix applied to SPL (`S3-thinking-claude_cli-sonnet.spl` prompt):**
- Changed "Respond with valid YAML" → "Respond with PLAIN YAML only — do NOT wrap in code fences or markdown blocks."

**Status:** fixed
