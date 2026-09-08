## 0. High-level Description

This script implements a **retrieval-augmented generation (RAG)** pattern in SPL, combining a vector-store retrieval step with an LLM generation step in a single declarative `PROMPT` block named `rag_answer`. A single `CREATE FUNCTION` called `answer` defines the prompt template: it casts the LLM into the role of a knowledgeable assistant and supplies the user's `{question}` as the sole interpolation slot, relying on the surrounding retrieval context to ground the answer. The `PROMPT rag_answer` block uses a SQL-like `SELECT` clause to compose the full LLM context: it sets the system persona via `system_role(...)`, retrieves the top three semantically relevant document chunks from the vector index via `rag.query(context.question, top_k=3)` aliased as `background`, and forwards the raw question before delegating to `GENERATE answer(question)`. The workflow contains no `WHILE` loop, no `EVALUATE` branch, no `CALL` side-effects, no `LOGGING` statements, and no `EXCEPTION` handlers, reflecting a deliberately minimal, single-shot retrieval-and-answer design. There are no explicit `INPUT` or `OUTPUT` declarations; the question reaches the prompt through `context.question`, conventionally supplied at invocation time via the `--adapter` CLI flag (here targeting an Ollama-hosted model).

---

## 1. Purpose

Answers a natural-language question by retrieving the three most relevant passages from a pre-indexed document store and generating a grounded response with an LLM.

---

## 2. Inputs

| Parameter | Default | Description |
|---|---|---|
| `question` | _(required)_ | The natural-language question to answer, passed via CLI (`question="..."`) and accessed internally as `context.question`. |
| _(adapter)_ | `ollama` | LLM backend specified at invocation with `--adapter`; not declared as a formal `INPUT` but controls model routing. |

---

## 3. Process

1. **Resolve the question** — the runtime binds the CLI argument `question=...` into `context.question`, making it available to all subsequent clauses.
2. **Set the system persona** — `system_role('You are a knowledgeable assistant. Use the provided context to answer accurately.')` is prepended to the prompt context assembled by `PROMPT rag_answer`.
3. **Retrieve relevant chunks** — `rag.query(context.question, top_k=3)` queries the pre-built FAISS vector index (populated by `spl doc-rag add`) and returns the three highest-similarity document passages, exposed as `background` in the prompt context.
4. **Assemble the prompt** — the SELECT columns (`background`, `question`) are merged with the `CREATE FUNCTION answer` template, which instructs the model to use the provided context and embeds the `{question}` slot.
5. **Generate the answer** — `GENERATE answer(question)` dispatches the composed prompt to the configured LLM (Ollama in the example) and collects the text response.
6. **Return the result** — the generated text is surfaced as the output of `PROMPT rag_answer` and returned to the caller.

---

## 4. Error Handling

_No `EXCEPTION` handlers are declared in this script._ All error conditions (model unavailability, empty retrieval results, context length overflow, etc.) propagate as unhandled runtime exceptions to the calling environment.

---

## 5. Output

The workflow returns the raw text response produced by the LLM — a natural-language answer grounded in the retrieved document chunks. There are no formal `OUTPUT` variable declarations, no `RETURN` statement with metadata fields, and no status codes; the result is the direct generation output of `PROMPT rag_answer`.