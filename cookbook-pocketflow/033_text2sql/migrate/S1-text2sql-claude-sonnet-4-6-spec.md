## Summary

This workflow translates a natural language question into an executable SQLite query against a known database, then self-heals if the generated SQL fails. It first reads the live database schema, asks an LLM to produce SQL, runs it, and—if execution raises a SQLite error—loops an LLM debugger up to a configurable maximum number of attempts before surfacing a final failure. Data engineers and business analysts benefit by querying relational databases without writing SQL manually.

---

## Detailed Specification

### 1. Purpose

Convert a natural language question into a validated, executed SQLite query against a target database, automatically correcting failed queries via an LLM debug loop.

---

### 2. High-level Description

The workflow opens with a deterministic tool step (`GetSchema`) that introspects the SQLite database and extracts all table names and column definitions into a schema string stored in `@schema`. A `GenerateSQL` GENERATE step then feeds both the schema and the user's natural-language question to an LLM, instructing it to respond exclusively with a fenced YAML block containing a single `sql` key; the parsed SQL string is stored in `@generated_sql` and the debug counter is reset to zero. An `ExecuteSQL` tool step attempts to run the query; on success it writes tabular results to `@final_result` and the workflow terminates normally. On a `sqlite3.Error`, the node increments `@debug_attempts` and, if the retry budget remains, emits the non-trivial action token `"error_retry"` to enter the debug branch; once `@debug_attempts` reaches `@max_debug_attempts` (default 3), it writes `@final_error` and terminates with an error status. The `DebugSQL` GENERATE step receives the original question, schema, failed SQL, and error message, calls the LLM with the same YAML output contract, overwrites `@generated_sql` with the corrected query, and returns control to `ExecuteSQL` for another attempt—forming a WHILE-style self-healing loop.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW text_to_sql` | `create_text_to_sql_flow()` + `Flow(start=get_schema_node)` | Declares the named orchestration unit |
| `CREATE FUNCTION generate_sql_prompt` | Inline f-string in `GenerateSQL.exec()` | Parameterized by `{schema}` and `{natural_query}` |
| `CREATE FUNCTION debug_sql_prompt` | Inline f-string in `DebugSQL.exec()` | Parameterized by `{failed_sql}`, `{error_message}`, `{schema}`, `{natural_query}` |
| `GENERATE generate_sql_prompt(...) INTO @generated_sql` | `call_llm(prompt)` → YAML parse → `shared["generated_sql"]` in `GenerateSQL` | LLM call with structured YAML output |
| `GENERATE debug_sql_prompt(...) INTO @generated_sql` | `call_llm(prompt)` → YAML parse → `shared["generated_sql"]` in `DebugSQL` | Overwrites prior SQL with corrected version |
| `CALL get_schema(@db_path) INTO @schema` | `GetSchema.exec(db_path)` via `sqlite3` | Pure deterministic tool call, no LLM |
| `CALL execute_sql(@generated_sql, @db_path) INTO @result` | `ExecuteSQL.exec(prep_res)` via `sqlite3` | Tool call; returns `(success, result_or_error, columns)` |
| `WHILE @debug_attempts < @max_debug_attempts DO` | `execute_sql_node - "error_retry" >> debug_sql_node >> execute_sql_node` cycle in `flow.py` | Loop driven by non-trivial action token `"error_retry"` |
| `RETURN @result WITH status="error_retry"` | `return "error_retry"` in `ExecuteSQL.post()` | Non-trivial branch token; routes to `DebugSQL` |
| `EXCEPTION WHEN SQLiteError THEN` | `except sqlite3.Error as e` in `ExecuteSQL.exec()` | Returns `(False, str(e), [])` tuple; handled in `post()` |
| `@vars` (shared state) | `shared` dict threaded through every `prep/exec/post` | Carries `schema`, `generated_sql`, `debug_attempts`, `final_result`, `final_error` |

---

### 4. Logical Functions / Prompts

**`generate_sql_prompt`**
- **Role:** Initial SQL generation from natural language
- **Key conventions:**
  - Receives full schema block and the user's question verbatim
  - Instructs LLM to respond *only* with a fenced ` ```yaml ` block containing key `sql:`
  - Output is parsed with `yaml.safe_load`; trailing semicolons are stripped
  - Debug attempt counter is reset to 0 after this step succeeds

**`debug_sql_prompt`**
- **Role:** Self-healing SQL correction after a SQLite runtime error
- **Key conventions:**
  - Injects the failed SQL, the verbatim `sqlite3.Error` message, the original schema, and the original natural-language question
  - Same YAML output contract as `generate_sql_prompt` (`sql:` key, fenced block)
  - Output overwrites `@generated_sql`; `@execution_error` is cleared from shared state before re-execution

---

### 5. Control Flow

```
GetSchema (tool)
    → store @schema
GenerateSQL (LLM, generate_sql_prompt)
    → store @generated_sql, reset @debug_attempts = 0
ExecuteSQL (tool)
    → success  → store @final_result → terminate (workflow complete)
    → sqlite3.Error AND @debug_attempts < @max_debug_attempts
         → increment @debug_attempts
         → RETURN WITH status="error_retry"
              → DebugSQL (LLM, debug_sql_prompt)
                   → overwrite @generated_sql
                   → back to ExecuteSQL   (loop)
    → sqlite3.Error AND @debug_attempts >= @max_debug_attempts
         → store @final_error → terminate (workflow failed)
```

The WHILE-style loop has no fixed iteration construct in PocketFlow; it is expressed as a graph cycle (`ExecuteSQL -"error_retry"→ DebugSQL → ExecuteSQL`) guarded by an in-node counter check. Termination is guaranteed because `@debug_attempts` is monotonically incremented and bounded by `@max_debug_attempts`.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (paste Section 2 as text2spl input)
spl3 text2spl \
  --description "Convert a natural language question into a validated, executed SQLite query. \
First call a get_schema tool to extract the database schema. Then GENERATE SQL using \
generate_sql_prompt (schema + question → YAML block with 'sql' key). Then CALL execute_sql \
tool; on success store results and finish. On SQLite error, increment debug_attempts and, \
while debug_attempts < max_debug_attempts, GENERATE corrected SQL using debug_sql_prompt \
(failed SQL + error + schema + question → YAML 'sql' key), overwrite generated_sql, and \
retry execute_sql. If max retries reached, store final_error and terminate with failure status." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile text_to_sql.spl --lang python/pocketflow
spl3 splc compile text_to_sql.spl --lang python/langgraph
spl3 splc compile text_to_sql.spl --lang go
```