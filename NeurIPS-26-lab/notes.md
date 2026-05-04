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

## [2026-05-04] R5-research / openrouter / qwen3.6-plus — S3 mmd2spl undefined GENERATE functions + CONCAT

**Symptom:** Validation passed but two GENERATE calls referenced undefined functions; string concat used non-existent builtin.

**Root causes:**
1. `GENERATE plan_queries(@topic)` and `GENERATE extract_facts(@web_results)` — neither declared as `CREATE FUNCTION`; would fail at runtime with undefined function error
2. `@notes := CONCAT(@notes, @extracted_facts)` — `CONCAT` is not a stdlib SPL builtin; correct idiom is `+`
3. `RETURNS STRING` → `RETURNS TEXT` (minor)

**Fix applied to file (`S3-research-openrouter-qwen.spl`):**
1. Added `CREATE FUNCTION plan_queries(topic)` and `CREATE FUNCTION extract_facts(web_results)` with appropriate prompt bodies using `{topic}` / `{web_results}` placeholders
2. `CONCAT(@notes, @extracted_facts)` → `@notes + @extracted_facts`
3. `RETURNS STRING` → `RETURNS TEXT` throughout
4. Also simplified loop: removed dead `@synthesis_action` branch (was initialized to `"research"` and never updated, so finalize path inside loop was unreachable); final `GENERATE assess_and_report` after loop handles all cases

**Status:** fixed — `spl3 validate` passes

---

## [2026-05-04] R4-thinking / openrouter / qwen3.6-plus — S3 mmd2spl four semantic errors

**Symptom:** Validation passed but file had four runtime-breaking issues.

**Root causes:**
1. `{{state}}` / `{{plan}}` double-braces in `assemble_prompt` body — variables never substituted (same pattern as R1, R2)
2. `@iteration` used in WHILE condition `@next_thought_needed = true AND @iteration < 3` but never initialized — runtime crash
3. `@next_thought_needed := true` (boolean literal) — WHILE condition `= true` does string comparison; should be `"true"` (string)
4. `CALL print_and_save(@final_result)` — not a stdlib function

**Fix applied to file (`S3-thinking-openrouter-qwen.spl`):**
1. `{{state}}` → `{state}`, `{{plan}}` → `{plan}`; `RETURNS STRING` → `RETURNS TEXT`; `Don''t` → `Don't`
2. Added `@iteration := 0;` initialization before WHILE loop; added `@iteration := @iteration + 1;` inside loop body
3. `@next_thought_needed := true` → `@next_thought_needed := "true"`; exit sets `"false"`
4. `CALL print_and_save(...)` → `CALL write_file("chain_of_thought.md", @final_result)`

**Status:** fixed — `spl3 validate` passes

---

## [2026-05-04] R3-judge / openrouter / qwen3.6-plus — S3 mmd2spl missing placeholders + three other errors

**Symptom:** Validation passed but function bodies never injected actual values; WHILE used undefined variable; wrong type on a function return.

**Root causes:**
1. `generate_description(state, feedback)` body had no `{state}` or `{feedback}` placeholders; `evaluate_description(description)` body had no `{description}` placeholder — LLM received generic instructions with no actual input values
2. `@iteration` in WHILE condition `@attempts <= 2 AND @iteration < 3 AND @status = "retry"` never initialized — runtime crash
3. `RETURNS BOOL` on `persist_shared_state` — not a valid SPL type
4. `CALL persist_shared_state(@shared_state, @verdict)` — invokes an LLM-backed `CREATE FUNCTION` using CALL (wrong verb; CALL is for stdlib tools)

**Fix applied to file (`S3-judge-openrouter-qwen.spl`):**
1. Added `{state}`, `{feedback}`, and `{description}` placeholders to function bodies; `RETURNS STRING` → `RETURNS TEXT`
2. Removed `@iteration` from WHILE condition (guard is `@attempts <= 2 AND @status = "retry"`)
3. Removed `persist_shared_state` function and its `CALL` invocation; final state stored in `@final_result := @description`
4. `RETURN @final_result WITH status = @status` (was hardcoded `"complete"` — now reflects actual pass/retry outcome)

**Status:** fixed — `spl3 validate` passes

---

## [2026-05-04] R2-rag / openrouter / qwen3.6-plus — S3 mmd2spl three semantic errors

**Symptom:** Validation passed but file had three runtime-breaking issues.

**Root causes:**
1. `{{doc}}` / `{{query}}` double-braces in `CREATE FUNCTION FormatPrompt` body — variables never substituted at runtime (same pattern as R1-agent)
2. `@formatted_prompt := FormatPrompt(@retrieved_doc, @query)` followed by `GENERATE GenerateAnswer(@formatted_prompt) INTO @answer` — `GenerateAnswer` was never defined as a `CREATE FUNCTION`; would fail at runtime with undefined function error
3. `CALL WriteMarkdownFile(@answer)` — not a stdlib function; correct stdlib call is `write_file(path, content)`

**Fix applied to file (`S3-rag-openrouter-qwen.spl`):**
1. `{{doc}}` / `{{query}}` → `{doc}` / `{query}` (single-braces), `RETURNS STRING` → `RETURNS TEXT`
2. Dropped the intermediate `@formatted_prompt` variable; changed `GENERATE GenerateAnswer(...)` → `GENERATE FormatPrompt(@retrieved_doc, @query) INTO @result` (using the actually-defined function)
3. `CALL WriteMarkdownFile(@answer)` → `CALL write_file("output.md", @result)`

**Status:** fixed — `spl3 validate` passes

---

## [2026-05-04] R1-agent / openrouter / qwen3.6-plus — S3 mmd2spl double-brace template variables

**Symptom:** Validation passed but runtime would silently skip all variable substitution in every function prompt template. Prompts would send literal `{{query}}`, `{{context}}` etc. to the LLM instead of actual values.

**Root cause:** qwen3.6-plus used `{{param}}` (double-braces) instead of `{param}` (single-braces) in `CREATE FUNCTION` body templates. The SPL executor substitutes via `body.replace("{" + key + "}", val)` — double-braces never match so variables are never injected. Also used `RETURNS STRING` (minor: accepted by validator) and `''text''` SQL-style quote escaping inside `$$...$$` delimiters (unnecessary).

**Fix applied to file (`S3-agent-openrouter-qwen.spl`):**
- All five `CREATE FUNCTION` bodies: `{{param}}` → `{param}` (single-braces)
- `RETURNS STRING` → `RETURNS TEXT` (consistent with sonnet reference)
- `''search''` / `''answer''` etc. → `'search'` / `'answer'` (clean up double-quote escaping)

**Status:** fixed — `spl3 validate` still passes

---

## [2026-05-04] R5-research / openrouter / qwen3.6-plus — S3-run search_web returns error (ddgs not installed)

**Symptom:** Run completed `status=complete` but output was a meta-report about search tool failure rather than research on the topic. `@web_results` received an installation error string instead of search results; `extract_facts` and `assess_and_report` faithfully processed the error as content.

**Root cause:** `search_web` stdlib tool requires the `ddgs` (DuckDuckGo Search) Python package, which was not installed in the `spl123` conda env. The tool returned an error/installation prompt as a string rather than raising an exception, so the workflow ran to completion with no runtime error.

**Fix:** `pip install ddgs` in the `spl123` env, then re-run.

**Contrast with sonnet R5:** Sonnet R5 also retrieved no real web data, but via a different silent failure — `CALL PARALLEL` statements were silently skipped (`Unknown statement type: CallParallelStatement`), so `@result1/2/3` were never populated. Both models synthesized from parametric knowledge only; qwen's failure mode was at least visible in the output, sonnet's was invisible.

**Significance for scoring:** Neither qwen nor sonnet R5 actually performed live web search during S3-run. Both closure scores will reflect parametric-knowledge synthesis, not retrieval-augmented research. This should be footnoted when comparing R5 scores across models.

**Status:** workflow ran to completion; re-run pending after `pip install ddgs`

---

## [2026-05-04] R2-rag / openrouter / qwen3.6-plus — S3-run missing tools.py + texts not threaded to search

**Symptom:** `spl3 run` crashed with `FileNotFoundError: .../tests/openrouter/qwen/tools.py`.

**Root cause (1):** No `tools.py` existed in the qwen output directory. The qwen SPL uses PascalCase CALL function names (`ChunkRawTexts`, `GenerateVectorEmbeddings`, etc.) different from the sonnet `tools.py` (`chunk_documents`, `embed_documents`, etc.) — the sonnet tools.py could not be reused directly.

**Root cause (2):** The qwen SPL passes `@texts` through `ChunkRawTexts → GenerateVectorEmbeddings → ConstructFAISSIndex` but never passes them to `NearestNeighborSearch(index, query_embedding)` — only 2 args, no `@texts`. The sonnet version explicitly passes texts as a third arg to `retrieve_document`. So at search time there is no way to return the actual chunk text through SPL variable flow.

**Fix applied (`tools.py` created in `tests/openrouter/qwen/`):**
- `ChunkRawTexts(raw_text)`: takes plain string (not JSON array), stores chunks in module-level `_chunks`
- `GenerateVectorEmbeddings(texts_json)`: embeds via ollama `qwen3-embedding:0.6b`
- `ConstructFAISSIndex(embeddings_json)`: builds FAISS index, writes `.chunks.json` sidecar alongside `.faiss` file using `_chunks` module state
- `LogAndPersistIndex(index_path)`: no-op, returns status string
- `EmbedQuery(query)`: embeds via ollama
- `NearestNeighborSearch(index_path, query_embedding_json)`: reads `.chunks.json` sidecar to return actual chunk text

**Status:** tools.py created — ready to re-run

---

## [2026-05-04] ALL RECIPES / openrouter / qwen3.6-plus — README S3-run section pointed at sonnet, not qwen

**Symptom:** All five `README-qwen.md` files had S3-run commands hardcoded to the sonnet run (`export OUT=.../claude_cli/sonnet`, `--adapter claude_cli --model claude-sonnet-4-6`). Running them as written would smoke-test the sonnet SPL, not the qwen SPL.

**Root cause:** README-qwen.md was copied from README-sonnet.md without updating the S3-run section to use the `$ADAPTER` / `$MODEL_ID` / `$OUT` vars already defined in the Environment section.

**Fix applied to all five READMEs (pending):**
- Remove hardcoded `export BASE=...` and `export OUT=.../claude_cli/sonnet` lines from S3-run (vars already set in Environment)
- Change `$OUT/S3-<recipe>-claude_cli-sonnet.spl` → `$OUT/S3-$RECIPE-$ADAPTER-$MODEL.spl`
- Change `--adapter claude_cli --model claude-sonnet-4-6` → `--adapter $ADAPTER --model $MODEL_ID`

**Recipe-specific fixes (pending):**
- **R1-agent**: Remove `--claude-allowed-tools WebSearch` — openrouter adapter does not accept this flag
- **R2-rag**: Change `-p` params `documents=` / `query=` → `raw_input=` / `user_query=` to match qwen SPL `INPUT` declarations; note that `tools.py` with qwen-named CALL functions (`ChunkRawTexts`, `EmbedQuery`, etc.) must exist in `$OUT` before running
- **R3-judge**: Change `-p "task=..."` → `-p "initial_state=..."` — qwen SPL declares `INPUT @initial_state`, not `@task`
- **R4-thinking**: Remove `--tools $OUT/tools.py` — qwen SPL only uses stdlib `write_file`, no helper tools needed
- **R5-research**: Remove `-p "out=..."` — qwen SPL hardcodes `"report.txt"` output path; remove `--claude-allowed-tools WebSearch`

**New checkpoint added between S3-run and S4 in all five READMEs (pending):** Explicit qwen silent-bug checklist:
- `{param}` single-braces in all CREATE FUNCTION bodies (not `{{param}}`)
- Every GENERATE call has a matching CREATE FUNCTION declaration
- All WHILE loop variables initialized before the loop
- CALL targets are stdlib tools, not LLM-backed CREATE FUNCTIONs

**Significance for scoring:** These are all human interventions applied before S4 (splc compile). Even if qwen achieves a closure score close to sonnet, the score reflects a manually corrected SPL, not raw qwen output. The raw qwen S3 had systematic silent bugs that would have caused runtime failures or wrong behavior. This gap should be footnoted when comparing scores across models.

**Status:** documented — README edits pending

---

## [2026-05-04] R5-research / openrouter / qwen3.6-plus — S3 mmd2spl invalid LOG statement

**Symptom:** `Validation: FAILED — Parse error at 27:7: Expected statement keyword, got IDENTIFIER ('LOG')`. Generated SPL used `LOG "..."` as a statement on two lines (inside the EVALUATE THEN block and at the end of the workflow).

**Root cause:** `LOG` is not a valid SPL keyword. qwen3.6-plus invented it as a pseudo-statement to represent "write to file / console" from the `.mmd` node label `WRITE @report to File — Console Log`.

**Fix applied to file (`S3-research-openrouter-qwen.spl`):**
- Removed `LOG "..."` inside the EVALUATE THEN block (redundant — loop exits via `@loop_count := 2`)
- Replaced `LOG "..."` at workflow end with `CALL write_file("report.txt", @report)` — the correct SPL idiom for persisting output

**Status:** fixed — `spl3 validate` passes

---

## [2026-05-04] R2-rag / openrouter / qwen3.6-plus — S2 text2mmd missing sub-graphs

**Symptom:** Generated `.mmd` was a flat linear flowchart with no sub-graphs. All 13 nodes were strung together A→B→…→M with no grouping.

**Root cause:** qwen3.6-plus did not spontaneously apply sub-graph grouping the way sonnet did. The RAG recipe has a natural two-phase structure (offline indexing + online query) plus a shared variable store, all of which benefit from sub-graph separation for clarity.

**Fix applied to file (`S2-rag-openrouter-qwen.mmd` + `.md`):**
- Added `OFFLINE` sub-graph: Chunk Raw Texts → Generate Vector Embeddings → Construct FAISS Index → Log & Persist Index
- Added `SHARED` sub-graph: `@texts`, `@embeddings`, `@index`, `@query`, `@query_embedding`, `@retrieved_doc`, `@answer`
- Added `ONLINE` sub-graph: Accept User Query → Embed Query → Nearest-Neighbor Search → Retrieve Top Document → Format Prompt → Execute GENERATE LLM Call → Write Markdown File
- Added cross-subgraph edges showing shared state reads/writes (dotted `---` connections)

**Status:** fixed manually — structure now matches sonnet reference

---

## [2026-05-04] R4-thinking / openrouter / qwen3.6-plus — S2 text2mmd missing LOOP sub-graph

**Symptom:** Generated `.mmd` had the chain-of-thought loop body as a flat flowchart with no sub-graph wrapper. The iterative thinking loop (WHILE condition → assemble → generate → validate → update → repeat) was indistinguishable from linear top-level flow.

**Root cause:** qwen3.6-plus did not group the WHILE loop body into a sub-graph. The sonnet reference wraps nodes C–I in a `ChainOfThought Loop` sub-graph, making the iterative structure visually explicit.

**Fix applied to file (`S2-thinking-openrouter-qwen.mmd` + `.md`):**
- Wrapped nodes C (`WHILE: next_thought_needed?`) through I (`Update State & Stream Progress`) in a `LOOP["ChainOfThought Loop"]` sub-graph
- Exit edge `H -->|False|` goes outside the sub-graph to J (Extract Final Solution)

**Status:** fixed manually — structure now matches sonnet reference
## [2026-05-04] splc / cli.py — `_compile` NameError on `spl3 splc compile`

**Symptom:** `spl3 splc compile ... --lang python/pocketflow --llm` crashed with `NameError: name '_compile' is not defined. Did you mean: 'cmd_compile'?`

**Root cause:** `cmd_compile` called `_compile(...)` at line 400, but the actual function is named `compile_llm_code` (defined at line 656). Name was wrong — likely a late rename during development.

**Fix applied to source (`spl3/splc/cli.py` line 400):**
- Replaced `_compile(...)` → `compile_llm_code(...)`

**Status:** fixed at source

---

## [2026-05-04] splc python/pocketflow — readme wrong filename (all recipes)

**Symptom:** `readme.md` script examples in R1-agent, R2-rag, R4-thinking, R5-research all referenced the wrong filename — missing the `_python_pocketflow` suffix that splc appends to compiled output files (e.g. `S3-agent-claude_cli-claude.py` instead of `S3-agent-claude_cli-claude_python_pocketflow.py`).

**Root cause:** The LLM generating the readme dropped the `_python_pocketflow` suffix when constructing the run examples, likely using only the base SPL stem.

**Fix applied to files (readme.md in each target dir):**
- R1: `S3-agent-claude_cli-claude.py` → `S3-agent-claude_cli-claude_python_pocketflow.py`
- R2: `S3-rag-claude_cli-sonnet.py` → `S3-rag-claude_cli-sonnet_python_pocketflow.py`
- R4: `S3-thinking-claude_cli-sonnet.py` → `S3-thinking-claude_cli-sonnet_python_pocketflow.py`
- R5: `S3-research-claude_cli-sonnet.py` → `S3-research-claude_cli-sonnet_python_pocketflow.py`

**Status:** fixed

---

## [2026-05-04] splc python/pocketflow — readme programmatic import uses invalid hyphenated module name (R1, R2, R5)

**Symptom:** readme "as a module" example used `from S3-...-... import run_*`, which is a Python syntax error — hyphens are not valid in module names for standard import statements.

**Root cause:** LLM generated a `from X import Y` statement using the filename stem directly, not accounting for hyphens.

**Fix applied to files (readme.md in R1, R2, R5 target dirs):**
- Replaced `from S3-... import ...` with an `importlib.util.spec_from_file_location` pattern that works with hyphenated filenames

**Status:** fixed

---

## [2026-05-04] R5-research / splc python/pocketflow — compiled .py starts with LLM preamble and markdown fence

**Symptom:** `S3-research-claude_cli-sonnet_python_pocketflow.py` was not valid Python. Lines 1–3 contained LLM prose (`The SPL source was provided inline, so I'll compile directly from it.`) followed by an opening ` ```python ` fence, making the file unparseable.

**Root cause:** The LLM generating the PocketFlow code included its own preamble sentence and a markdown code fence before the Python source. The `compile_llm_code` function passes the raw LLM response directly to `write_text` without stripping fences.

**Fix applied to file:**
- Stripped lines 1–3 (preamble + fence) from the compiled `.py` file; confirmed `ast.parse` passes clean

**Note for source fix:** `compile_llm_code` in `spl3/splc/cli.py` should strip leading markdown fences from LLM output before writing — same issue as `mmd2spl` fixed on 2026-05-03.

**Status:** file fixed; source-level fence-stripping still open

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

---

## [2026-05-04] R1-R5 / openrouter / qwen — S4 splc compile: wrong model IDs in compiled Python

**Symptom:** All 5 compiled S4 Python files hard-coded incorrect OpenRouter model IDs instead of the benchmark model `qwen/qwen3.6-plus`:
- R1: `qwen/qwen-2.5-72b-instruct`
- R2: `qwen/qwen-turbo`
- R3: `qwen/qwen-2.5-72b-instruct`
- R4: `qwen/qwen-max`
- R5: `qwen/qwen2.5-72b-instruct`

**Root cause:** splc compiler generates a hard-coded model string from its training data rather than propagating the adapter config.

**Fix applied:** All 5 files updated to read `os.environ.get("LLM_MODEL", "qwen/qwen3.6-plus")`.

**Status:** fixed — footnote: manual intervention required for benchmarking integrity

---

## [2026-05-04] R1, R5 / openrouter / qwen — S4 splc compile: web_search is a stub

**Symptom:** R1 `web_search()` returned a fake string `f"[Search results for '{query}']"`. R5 `_search_web()` returned a hardcoded template string with no real query. Neither called any actual search API.

**Root cause:** splc compiler does not know the runtime environment — emits a placeholder rather than the real `ddgs` implementation used in the sonnet S4 reference.

**Fix applied:** Both functions replaced with the same ddgs-based implementation from the sonnet reference:
- `try: from ddgs import DDGS; except ImportError: from duckduckgo_search import DDGS`
- Extracts `search_query:` from YAML output (R1) or `QUERY:` lines (R5) before issuing search
- Returns formatted result list or error string on exception

**Status:** fixed — footnote: manual intervention; ddgs must be installed in env (`pip install ddgs`)

---

## [2026-05-04] R2 / openrouter / qwen — S4 splc compile: fake hash-based embeddings

**Symptom:** `_call_generate_vector_embeddings` and `_call_embed_query` use `hash(chunk + str(i)) % 1000` as a mock embedding — no actual vector model called. This means semantic similarity search is non-functional even though the FAISS-style cosine search logic is correct.

**Root cause:** splc compiler cannot introspect the runtime tools.py (ollama-backed) used in S3-run; emits a deterministic mock instead.

**Fix:** Not applied — the tools.py RAG pipeline is the authoritative S3 run artifact; S4 documents the logical flow. Noted as compilation quality gap.

**Status:** wontfix (S4 benchmarking note) — real embeddings are in tools.py (S3-run path)

---

## [2026-05-04] R2 / openrouter / qwen — S4 splc compile: `import requests` (non-stdlib)

**Symptom:** Compiled file imported `requests` (not stdlib); `_generate_with_openrouter` used `requests.post`.

**Fix applied:** Changed to `import urllib.request` + `json`; rewrote the HTTP call using `urllib.request.Request` / `urlopen`. Consistent with R1 / sonnet reference style.

**Status:** fixed

---

## [2026-05-04] R1-R5 / openrouter / qwen — S4 splc compile: no PocketFlow Node/Flow classes

**Symptom:** All 5 compiled files use plain Python classes or top-level functions — none import or use `pocketflow.Node` / `pocketflow.Flow`. The sonnet S4 reference uses `class DecideNode(Node)` with `prep/exec/post` methods and `build_flow()` with explicit edge wiring.

**Root cause:** splc for qwen translated SPL into flat procedural Python; the PocketFlow ETL node pattern was not applied.

**Fix:** Not applied — rewriting 5 files into PocketFlow Node/Flow structure would be a major manual rewrite beyond surgical fix scope. The procedural code is logically correct. Scoring this as a compilation quality gap vs. sonnet reference.

**Status:** wontfix (S4 benchmarking note) — counts against qwen closure score vs. sonnet

---

## [2026-05-04] R1-R5 / openrouter / qwen — S4 file rename to S4-* convention

**Action:** All 5 compiled files renamed from `S3-*_python_pocketflow.py` to `S4-*.py`:
- `S4-agent-openrouter-qwen.py`
- `S4-rag-openrouter-qwen.py`
- `S4-judge-openrouter-qwen.py`
- `S4-thinking-openrouter-qwen.py`
- `S4-research-openrouter-qwen.py`

**Status:** done
