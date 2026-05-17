## Summary

This workflow implements Retrieval-Augmented Generation (RAG): given a natural-language question, it fetches the most relevant passages from a pre-indexed document store and feeds them as context to an LLM to produce a grounded answer. It exists to prevent hallucination by anchoring the model's response to real source material. Developers and knowledge-base maintainers use it to build accurate Q&A systems over their own documents.

---

## Detailed Specification

### 1. Purpose

Answers a free-text question accurately by retrieving the top-3 most relevant document passages from a vector index and using them as grounding context for an LLM response.

---

### 2. High-level Description

This implementation follows the standard RAG pattern using two SPL constructs: a `CREATE FUNCTION` that defines the answer prompt template, and a `PROMPT` block that assembles the full context and triggers the LLM call via `GENERATE`. The `CREATE FUNCTION answer` establishes the instruction persona ("knowledgeable assistant") and accepts `question` as its sole parameter, producing a TEXT response. The `PROMPT rag_answer` block acts as the pipeline's single execution unit: it calls `rag.query(context.question, top_k=3)` to retrieve the three most semantically similar document chunks from the pre-built FAISS vector index, binds them as `background`, and passes the original question through as `question`. The assembled context and question are then fed into `GENERATE answer(question)`, which dispatches the LLM call (via the configured adapter, e.g. Ollama) and stores the result. There is no iterative loop or branching — the workflow is a single-pass, linear retrieval-then-generation pipeline. No side-effect tool calls, exception handlers, or multi-model routing are used; correctness relies entirely on the quality of the vector index and the retrieved passages.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `CREATE FUNCTION answer(question TEXT)` | `CREATE FUNCTION` | Defines the reusable LLM prompt template with `{question}` slot |
| `PROMPT rag_answer ... SELECT ...` | `WORKFLOW` (single-step) | Declares the named execution unit; `SELECT` assembles the input context |
| `rag.query(context.question, top_k=3)` | `CALL <tool>(...) INTO @<var>` | Side-effect retrieval call; fetches top-3 chunks from vector store into `background` |
| `GENERATE answer(question)` | `GENERATE <fn>(...) INTO @<var>` | Dispatches the LLM call using the assembled prompt template |
| `context.question` | SPL `@var` (input binding) | Runtime-bound input variable carrying the user's question |
| `background` (alias) | SPL `@var` (intermediate) | Holds the retrieved document passages injected as RAG context |
| `system_role(...)` | Prompt system header convention | Sets the LLM system persona within the PROMPT block |

---

### 4. Logical Functions / Prompts

**`answer`**
- **Role:** The sole generation prompt template. It instructs the LLM to act as a knowledgeable assistant and answer using the provided context.
- **Key conventions:**
  - Accepts `{question}` as its only slot parameter.
  - No sentinel tokens, scoring rubrics, or structured output format are specified — response is free-form TEXT.
  - The system persona is reinforced both in the `CREATE FUNCTION` body and redundantly via `system_role(...)` in the `PROMPT` block's `SELECT`.

---

### 5. Control Flow

Execution is fully linear and single-pass:

1. **Input binding** — `context.question` is populated from the `--question` CLI argument (or caller-supplied binding).
2. **Retrieval** — `rag.query(context.question, top_k=3)` queries the FAISS vector index, returning the three most relevant document passages as `background`.
3. **Generation** — `GENERATE answer(question)` invokes the LLM with the assembled prompt (system role + background passages + question) and produces the final answer.
4. **Termination** — The result is returned to the caller. There is no `WHILE` loop, no `EVALUATE` branch, and no non-trivial `RETURN` status — the workflow terminates after a single retrieval-generation cycle.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Answers a free-text question accurately by retrieving the top-3 most relevant document passages from a vector index and using them as grounding context for an LLM response." --mode workflow

# Step 2 — compile to any target
spl3 splc compile rag_query.spl --lang python/pocketflow
spl3 splc compile rag_query.spl --lang python/langgraph
spl3 splc compile rag_query.spl --lang go
```