## 0. High-level Description

This workflow implements a **RAG-Writer pattern** — a technique where an LLM agent actively contributes structured knowledge back into the retrieval-augmented generation (RAG) vector store rather than only querying it. The single CREATE FUNCTION `synthesize` acts as a knowledge-engineering prompt, instructing the model to extract exactly three concise bullet-point insights from raw input text, deliberately excluding background knowledge in favour of novel claims, methods, or results. Execution follows a linear three-step pipeline expressed in SPL terms: a GENERATE call invokes `synthesize` and stores extracted insights in `@insights`, followed by two deterministic CALL side-effects — `write_file` persists the insights as a Markdown log artifact, and `rag_update` ingests them into the vector store alongside a source provenance string. An EVALUATE branch inspects the `@status` returned by `rag_update`, emitting an INFO log on success or a WARN log for any unexpected status, with LOGGING used at INFO and DEBUG levels throughout to trace both progress and intermediate LLM output. The workflow handles a single EXCEPTION type, `GenerationError`, which short-circuits execution and returns a structured error status if the LLM generation step fails.

## 1. Purpose

Given a raw text passage, extract three structured insights from it using an LLM and persist them into a RAG vector store so that future retrieval queries benefit from the synthesized knowledge.

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `@raw_text` | *(required)* | The raw text passage from which insights are to be extracted and synthesized. |
| `@log_dir` | `cookbook/42_knowledge_synthesis/logs-spl` | Directory path where the extracted insights Markdown file will be written. |

## 3. Process

1. **Log start** — emit an INFO-level log message indicating that insight extraction is beginning.
2. **Extract insights (LLM)** — GENERATE calls the `synthesize` prompt function with `@raw_text`, producing exactly three concise bullet-point insights stored in `@insights`.
3. **Log extracted insights** — emit a DEBUG-level log containing the full `@insights` text.
4. **Persist insights to file** — CALL `write_file` writes `@insights` to `{@log_dir}/insights.md` as a Markdown artifact; result is discarded (`INTO NONE`).
5. **Update vector store** — CALL `rag_update` ingests `@insights` into the RAG vector store with a provenance metadata string (`Source: <raw_text>`); the return value is captured in `@status`.
6. **Evaluate outcome** — EVALUATE inspects `@status`:
   - If it contains the substring `'success'`: emit an INFO log confirming the knowledge base was updated.
   - Otherwise: emit a WARN log displaying the unexpected status value.
7. **Return** — RETURN the formatted status string `'Operation: <status>'` with metadata field `status = @status`.

## 4. Error Handling

- **`GenerationError`** — if the GENERATE step (LLM call to `synthesize`) fails, the workflow immediately returns the string `'synthesis_failed'` with metadata `status = 'error'` and `reason = 'generation_error'`, skipping all subsequent steps including the file write and vector store update.

## 5. Output

| Field | Value |
|---|---|
| Return value (`@status` TEXT) | `'Operation: <status>'` — a formatted string embedding the raw status returned by `rag_update`, e.g. `'Operation: success'` |
| Metadata: `status` | The raw status string from `rag_update` (e.g. `'success'`), or `'error'` on exception |
| Metadata: `reason` | `'generation_error'` — only present when a `GenerationError` exception is caught |
| Side-effect artifact | `{@log_dir}/insights.md` — Markdown file containing the three extracted bullet-point insights |