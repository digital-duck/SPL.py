## Summary

This workflow translates a markdown document into multiple target languages in parallel, preserving all formatting, links, and code blocks. It exists to eliminate the tedious, sequential work of running separate translation requests for each language. Content creators, open-source maintainers, and documentation teams benefit by getting a full suite of localized files in a single run.

---

## Detailed Specification

### 1. Purpose

Translate a single markdown file into a configurable set of target languages concurrently, saving each result as a separate `.md` file in a specified output directory.

### 2. High-level Description

This workflow implements a **batch parallel translation** pattern using a single logical function applied fan-out style across all target languages. On startup, the workflow reads a source markdown file and a list of target languages from shared state; it then uses `CALL PARALLEL` to dispatch one LLM translation call per language simultaneously, collecting all results before writing any files. Each parallel branch invokes the same `TranslateText` prompt function with two inputs — the raw markdown content and the target language name — and instructs the model to return only the translated text with no commentary, preserving markdown structure, hyperlinks, and code fences. After all branches complete, the workflow iterates over the results and writes each translation to disk as `README_<LANGUAGE>.md` under the configured output directory. There is no iterative refinement loop and no semantic branching; execution is a straight line from fan-out to fan-in to file-write. Retry logic (`max_retries=3`) is handled at the executor level, mapping naturally to an `EXCEPTION WHEN GenerationError THEN` retry clause in SPL.

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW BatchTranslation` | `Flow(start=TranslateTextNode(...)).run(shared)` | Top-level orchestration entry point |
| `INPUT: @text, @languages, @output_dir` | `shared = {"text": ..., "languages": ..., "output_dir": ...}` | Shared state dict passed into the flow |
| `CREATE FUNCTION TranslateText` | `TranslateTextNode.exec()` prompt string | Single reusable prompt template parameterized by `{text}` and `{language}` |
| `CALL PARALLEL ... END` | `BatchNode` — `prep()` returns list; PocketFlow fans out `exec()` across all items concurrently | One branch per `(text, language)` tuple |
| `GENERATE TranslateText(...) INTO @translation` | `result = call_llm(prompt)` inside `exec()` | LLM call capturing translated text |
| `CALL write_file(...) INTO @_` | `open(fname, "w").write(...)` inside `post()` | Side-effect file write after fan-in |
| `@translations` (shared result list) | `exec_res_list` list passed to `post()` | Fan-in accumulator; SPL equivalent is a list variable |
| `EXCEPTION WHEN GenerationError THEN retry` | `max_retries=3` on `BatchNode` | Automatic retry on LLM call failure |

### 4. Logical Functions / Prompts

**`TranslateText`**

- **Role:** Core translation prompt; the only LLM-facing function in the workflow.
- **Inputs:** `{text}` (full markdown source), `{language}` (target language name, e.g. `"Japanese"`).
- **Key conventions:**
  - Instructs the model to preserve markdown format, links, and code blocks verbatim.
  - Uses a hard sentinel: `"Return the translated text only, no other comments."` — this suppresses preamble and ensures the raw output can be written directly to file without post-processing.
  - Output format is plain translated markdown; no JSON wrapper, no scoring, no structured envelope.

### 5. Control Flow

```
START
  → read source file → populate shared state (@text, @languages, @output_dir)
  → CALL PARALLEL over @languages
      for each language:
          GENERATE TranslateText(@text, language) INTO @translation
          collect {"language": ..., "translation": ...}
  → fan-in: all branches complete → exec_res_list
  → for each result: CALL write_file(output_dir, language, translation)
END
```

There is no `WHILE` loop, no `EVALUATE` branch, and no non-trivial `RETURN` status. The only non-linear construct is the `CALL PARALLEL` fan-out/fan-in. Retry on LLM failure is the sole exception path.

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Translate a single markdown file into a configurable set of target languages concurrently, saving each result as a separate .md file in a specified output directory. The workflow reads source text and a list of language names from shared state, then uses CALL PARALLEL to dispatch one GENERATE TranslateText call per language simultaneously. The TranslateText function takes the full markdown content and a target language name, instructs the model to preserve markdown formatting, links, and code blocks, and to return translated text only with no commentary. After all branches complete, the workflow writes each translation to disk as README_<LANGUAGE>.md under the output directory. Use EXCEPTION WHEN GenerationError THEN retry (max 3 attempts) on each parallel branch." --mode workflow

# Step 2 — compile to any target
spl3 splc compile batch_translation.spl --lang python/pocketflow
spl3 splc compile batch_translation.spl --lang python/langgraph
spl3 splc compile batch_translation.spl --lang go
```