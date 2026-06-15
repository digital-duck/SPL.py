## Summary

This workflow implements a minimal task management system backed by a local SQLite database. It initializes the database schema, inserts a single user-provided task, and retrieves all stored tasks — producing a structured list as its final output. It exists to demonstrate clean separation between database tooling and workflow orchestration, and serves as a reference pattern for developers integrating persistent storage into PocketFlow pipelines.

---

## Detailed Specification

### 1. Purpose

Execute a three-step database pipeline — initialize schema, insert a task, list all tasks — accepting title and description as inputs and returning the full task roster as output.

---

### 2. High-level Description

This is a linear three-step tool-orchestration workflow with no LLM calls and no branching. It follows the CALL pattern exclusively: each step invokes a database tool function rather than a language model. The workflow begins by calling `init_db` to create the `tasks` table if it does not already exist, recording a status message in shared state. It then calls `execute_sql` with a parameterized `INSERT` statement to write the user-supplied title and description, again storing a confirmation string. Finally it calls `execute_sql` with a `SELECT *` query to retrieve all rows from the tasks table and stores the result set in shared state. The CLI entry point accepts `--title` and `--description` options, pre-populates shared state before the flow runs, and prints the results after the flow completes. There is no WHILE loop, no EVALUATE branch, and no EXCEPTION handler in this implementation — control flow is strictly sequential.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW database_pipeline` | `create_database_flow()` + `Flow(start=init_db)` | Top-level orchestration unit |
| `INPUT: task_title, task_description` | `shared = {"task_title": ..., "task_description": ...}` set in `main.py` | Flow receives inputs via shared store before `.run()` |
| `CALL init_db() INTO @db_status` | `InitDatabaseNode.exec` calling `init_db()` | Pure side-effect tool call; no LLM involved |
| `CALL execute_sql(insert_query, params) INTO @task_status` | `CreateTaskNode.exec` calling `execute_sql(query, (title, description))` | Parameterized insert; SQL injection safe |
| `CALL execute_sql(select_query) INTO @tasks` | `ListTasksNode.exec` calling `execute_sql("SELECT * FROM tasks")` | Returns list of row tuples |
| `OUTPUT: @db_status, @task_status, @tasks` | `shared.get("db_status")`, `shared.get("task_status")`, `shared.get("tasks")` printed in `main.py` | Shared store acts as SPL output bindings |
| `@var` (shared state variables) | `shared` dict threaded through all nodes | Central data carrier across steps |

---

### 4. Logical Functions / Prompts

There are no LLM prompt functions in this workflow. All logical functions are deterministic database tool calls:

**`init_db`**
- Role: Schema bootstrapper — creates the `tasks` table (`id`, `title`, `description`, `status`, `created_at`) if it does not exist.
- Conventions: No parameters; idempotent; returns no value (side-effect only).

**`execute_sql` (INSERT variant)**
- Role: Task writer — inserts a new row with user-supplied title and description; `status` defaults to `pending`.
- Conventions: Uses `?` positional parameter binding to prevent SQL injection; parameters passed as a tuple.

**`execute_sql` (SELECT variant)**
- Role: Task reader — fetches all rows from the tasks table and returns them as a list of tuples in column order `(id, title, description, status, created_at)`.
- Conventions: No parameters; returns raw row data for the caller to format.

---

### 5. Control Flow

```
[START]
  ↓
InitDatabaseNode   — calls init_db(); writes "Database initialized" → @db_status
  ↓
CreateTaskNode     — reads @task_title, @task_description from shared;
                     calls execute_sql(INSERT); writes "Task created successfully" → @task_status
  ↓
ListTasksNode      — calls execute_sql(SELECT *); writes row list → @tasks
  ↓
[END]              — caller reads @db_status, @task_status, @tasks from shared store
```

Linear, no branching, no loops, no conditional termination.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Execute a three-step database pipeline: initialize \
  schema via init_db tool, insert a task via execute_sql with parameterized INSERT, \
  list all tasks via execute_sql with SELECT *. Accept task_title and task_description \
  as inputs. No LLM calls. No branching. Store db_status, task_status, and tasks list \
  in shared state as outputs." --mode workflow

# Step 2 — compile to any target
spl3 splc compile database_pipeline.spl --lang python/pocketflow
spl3 splc compile database_pipeline.spl --lang python/langgraph
spl3 splc compile database_pipeline.spl --lang go
```

**Note:** Because this workflow contains no LLM calls, `text2spl` will produce a workflow composed entirely of `CALL` statements with no `GENERATE` steps. Ensure your `tools/database.py` functions are registered as `@spl_tool` decorated callables so the SPL executor can resolve them at runtime.