## Summary

This workflow implements an interactive Recipe Finder that accepts a user-supplied ingredient, fetches candidate recipes via an async HTTP call, and asks an LLM to select the best option. The user then approves or rejects the suggestion in a retry loop, ensuring the final recipe recommendation has explicit human sign-off. It demonstrates how async I/O, LLM inference, and human-in-the-loop approval can be composed into a single coherent orchestration.

---

## Detailed Specification

### 1. Purpose

Recommend a recipe for a user-supplied ingredient by combining async API retrieval, LLM selection, and interactive human approval in a retry loop.

---

### 2. High-level Description

The workflow opens by prompting the user for an ingredient via an async input call (CALL `get_user_input`), then dispatches a non-blocking API fetch (CALL `fetch_recipes`) that returns a short list of candidate recipe names stored in shared state (`@recipes`, `@ingredient`). A `suggest_recipe` function (GENERATE) sends the candidate list to the LLM with the prompt "Choose best recipe from: {recipes}" and captures the result into `@suggestion`. Control then passes to a human-approval gate (CALL `get_user_input`) that presents the suggestion and reads a y/n answer; the EVALUATE branch on that answer either commits the workflow with `RETURN @suggestion WITH status="accept"` or loops back to the suggest step with `status="retry"`. The WHILE-equivalent retry loop means the suggest → approve cycle repeats until the user explicitly accepts, with the same fetched recipe list reused across iterations. There is no explicit EXCEPTION handler in this implementation — async I/O errors would surface as uncaught exceptions.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW RecipeFinder` | `AsyncFlow(start=fetch)` in `flow.py` | Top-level orchestration unit |
| `CREATE FUNCTION suggest_recipe` | `call_llm_async(f"Choose best recipe from: {recipes}")` in `SuggestRecipe.exec_async` | Single prompt template; recipe list is the only input |
| `GENERATE suggest_recipe(@recipes) INTO @suggestion` | `suggestion = await call_llm_async(...)` | Async LLM call; result stored in `shared["suggestion"]` |
| `CALL fetch_recipes(@ingredient) INTO @recipes` | `recipes = await fetch_recipes(ingredient)` | Side-effect async HTTP/API call; result stored in `shared["recipes"]` |
| `CALL get_user_input(...) INTO @answer` | `answer = await get_user_input(prompt)` | Async blocking I/O via `loop.run_in_executor` |
| `WHILE @answer != "y" DO ... END` | `approve - "retry" >> suggest` edge in `flow.py` | Loop back to suggest step on rejection |
| `EVALUATE @answer WHEN contains("y") THEN ... ELSE ... END` | `if answer == "y": return "accept" else: return "retry"` in `GetApproval.post_async` | Branch drives loop termination vs. retry |
| `RETURN @suggestion WITH status="accept"` | `return "accept"` + print in `GetApproval.post_async` | Terminates the flow; non-trivial status token |
| Shared state `@recipes`, `@suggestion`, `@ingredient` | `shared` dict passed through all nodes | SPL `@var` bindings correspond to `shared[key]` entries |

---

### 4. Logical Functions / Prompts

**`suggest_recipe`**
- **Role:** Core LLM decision step — selects the single best recipe from a list of candidates.
- **Prompt convention:** Single instruction sentence: `"Choose best recipe from: {recipes}"` where `{recipes}` is a comma-joined string of candidate names. No sentinel tokens, scoring rubric, or structured output format; the LLM returns a plain recipe name string.

---

### 5. Control Flow

1. **Start:** `FetchRecipes` — async user input collects `@ingredient`; async API call produces `@recipes`; both stored in shared state.
2. **Suggest:** `SuggestRecipe` — GENERATE call sends `@recipes` to the LLM; result stored as `@suggestion`.
3. **Approve gate:** `GetApproval` — async user input reads y/n answer; EVALUATE branches:
   - `answer == "y"` → `RETURN WITH status="accept"` — prints recipe details and terminates.
   - `answer != "y"` → `RETURN WITH status="retry"` — loops back to step 2 (`SuggestRecipe`) using the same `@recipes` list.
4. **Termination:** Only the `"accept"` branch ends the workflow; the `"retry"` branch creates an unbounded loop until the user accepts.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Recommend a recipe for a user-supplied ingredient by
combining async API retrieval, LLM selection, and interactive human approval in a
retry loop. Prompt the user for an ingredient, fetch candidate recipes via an async
API call, use a suggest_recipe LLM function to choose the best option from the list,
then enter a WHILE loop that presents the suggestion to the user and loops back to
suggest_recipe on rejection (RETURN WITH status=retry) or terminates on acceptance
(RETURN WITH status=accept)." --mode workflow

# Step 2 — compile to any target
spl3 splc compile recipe_finder.spl --lang python/pocketflow
spl3 splc compile recipe_finder.spl --lang python/langgraph
spl3 splc compile recipe_finder.spl --lang go
```