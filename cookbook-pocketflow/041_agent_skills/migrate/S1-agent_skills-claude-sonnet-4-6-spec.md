## Summary

This workflow routes an incoming text task to the most appropriate "Agent Skill" — a Markdown instruction file — and then executes that skill against the task using an LLM. It exists to make prompt engineering reusable and swappable at runtime without touching application code. Content teams, prompt engineers, and developers benefit by maintaining skills as plain files while the orchestration layer handles selection and injection.

---

## Detailed Specification

### 1. Purpose

Given a text task and a directory of Markdown skill files, select the best-fit skill via keyword matching and execute the task through an LLM using that skill's instructions as the prompt template.

---

### 2. High-level Description

The workflow implements a two-step **skill-routing pattern**: skill selection followed by skill application. On startup, a CALL to a file-loading tool reads all Markdown files from the `skills/` directory into a name→content map. Skill selection is a **deterministic EVALUATE** step — if the task contains the token `"checklist"` or `"steps"`, the `checklist_writer` skill is chosen; otherwise `executive_brief` is chosen, with a fallback to the first available skill if the preferred name is absent. The selected skill name and Markdown content are stored in SPL shared variables (`@selected_skill`, `@selected_skill_content`). A single CREATE FUNCTION defines the apply-skill prompt template, which injects the skill name, skill instructions, and user task verbatim and instructs the LLM to follow the skill exactly and return only the final result. A GENERATE call executes that prompt and stores the output in `@result`. There is no WHILE loop and no LLM-based branching — the control flow is strictly linear, and the only non-trivial logic is the keyword-based skill router in the first step. The workflow supports any LLM adapter (ollama, claude_cli, openrouter) via the SPL adapter shim, making it model-agnostic.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW agent_skills` | `create_flow()` + `Flow(start=select_skill)` | Top-level orchestration entry point |
| `CALL load_skills(...) INTO @skills` | `load_skills(shared["skills_dir"])` in `SelectSkill.prep` | File I/O side-effect; reads all `*.md` from `skills/` dir |
| `EVALUATE @task WHEN contains('checklist') OR contains('steps')` | `if "checklist" in task or "steps" in task` in `SelectSkill.exec` | Deterministic keyword router; no LLM call |
| `CREATE FUNCTION apply_skill_prompt` | f-string prompt in `ApplySkill.exec` | Injects `{skill_name}`, `{skill_content}`, `{task}` |
| `GENERATE apply_skill_prompt(...) INTO @result` | `call_llm(prompt)` in `ApplySkill.exec` | Single LLM call; adapter-agnostic via shim |
| SPL `@selected_skill` | `shared["selected_skill"]` | Name of chosen skill, passed between nodes |
| SPL `@selected_skill_content` | `shared["selected_skill_content"]` | Full Markdown text of chosen skill |
| SPL `@result` | `shared["result"]` | Final LLM output; written to file or stdout |
| `EXCEPTION WHEN ValueError` | `raise ValueError(...)` in `load_skills` | Raised when `skills/` dir contains no `.md` files |

---

### 4. Logical Functions / Prompts

**`apply_skill_prompt`**
- **Role:** The sole LLM prompt in this workflow. It wraps the selected skill's Markdown instructions around the user's task, acting as a runtime-configurable system prompt.
- **Key conventions:**
  - Skill instructions are fenced with `---` delimiters to visually separate them from the task.
  - The directive `"Follow the skill instructions exactly and return the final result only"` suppresses preamble and reasoning traces, ensuring clean output for downstream file-writing.
  - No scoring, no sentinel tokens, no structured output format — the skill Markdown itself defines the expected output shape (e.g., executive brief vs. checklist).

**`load_skills` (tool, not an LLM prompt)**
- **Role:** File-loading side-effect that hydrates the skill registry at the start of the workflow.
- **Key conventions:** Sorts by filename for deterministic ordering, which determines the fallback skill when the preferred name is absent.

---

### 5. Control Flow

```
START
  │
  ▼
CALL load_skills(@skills_dir) INTO @skills          ← file I/O, once
  │
  ▼
EVALUATE @task
  WHEN contains("checklist") OR contains("steps")
    THEN @selected_skill ← "checklist_writer"
  ELSE
    @selected_skill ← "executive_brief"
  [FALLBACK: first key in @skills if preferred absent]
  │
  ▼
GENERATE apply_skill_prompt(@task, @selected_skill, @selected_skill_content)
  INTO @result                                       ← single LLM call
  │
  ▼
COMMIT @result → stdout or file                     ← side-effect output
END
```

No loop condition. No LLM-evaluated branch. Termination is unconditional after the single GENERATE call.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Given a text task and a directory of Markdown skill files,
select the best-fit skill via keyword matching and execute the task through an LLM using
that skill's instructions as the prompt template. Use CALL to load all skills from disk,
use EVALUATE to route to checklist_writer when the task contains 'checklist' or 'steps'
and executive_brief otherwise, then use GENERATE with an apply_skill_prompt that injects
the skill name, skill Markdown instructions, and user task, instructing the LLM to return
the final result only." --mode workflow

# Step 2 — compile to any target
spl3 splc compile agent_skills.spl --lang python/pocketflow
spl3 splc compile agent_skills.spl --lang python/langgraph
spl3 splc compile agent_skills.spl --lang go
```