## Summary

RAG Query is a single-step retrieval-augmented generation workflow that answers user questions by first fetching the most relevant passages from a locally indexed document store, then feeding those passages to an LLM for a grounded response. It exists to prevent hallucination by anchoring the model's answer in real retrieved content rather than parametric memory. Any team that needs accurate, document-backed Q&A over a private knowledge base benefits immediately.

---

## Detailed Specification

### 1. Purpose

Given a free-text question, retrieve the top-3 most relevant document chunks from a local vector index and generate a factually grounded answer using an LLM.

### 2. High-level Description

This workflow implements the classic Retrieval-Augmented Generation (RAG) pattern using two cooperating SPL constructs. A single `CREATE FUNCTION` named `answer` defines the prompt template that instructs the LLM to use provided context when answering a question. The main `PROMPT` block, `rag_answer`, assembles the full prompt at inference time by invoking `rag.query` as a side-effect CALL that returns the top-3 document chunks for the incoming `context.question`, binds them into a `background` variable, and pipes both the retrieved context and the original question into the `answer` function via a GENERATE call. Control flow is entirely linear — there is no iterative refinement (no WHILE), no semantic branching (no EVALUATE), and no error recovery path (no EXCEPTION), because a single retrieval-and-generation cycle is sufficient for this use case. The adapter and model are resolved at runtime via `--adapter` and `-m` flags, keeping the `.spl` source provider-agnostic in accordance with the DODA design principle.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `PROMPT rag_answer` | `WORKFLOW rag_answer` | Top-level named orchestration unit |
| `CREATE FUNCTION answer(question TEXT)` | `CREATE FUNCTION answer(...)` | Reusable prompt template with `{question}` slot |
| `rag.query(context.question, top_k=3)` | `CALL rag.query(...) INTO @background` | Side-effect retrieval call; returns top-3 chunks |
| `GENERATE answer(question)` | `GENERATE answer(question) INTO @result` | Single LLM call binding retrieved context + question |
| `context.question` | `@question` (workflow INPUT variable) | Caller-supplied question bound as shared state |
| `system_role(...)` | System prompt passed to adapter | Sets LLM persona for the generation step |

### 4. Logical Functions / Prompts

**`answer(question TEXT)`**
- **Role:** The sole prompt template; instructs the LLM to act as a knowledgeable assistant and ground its response in the provided context.
- **Key conventions:**
  - System role reinforces accuracy over creativity: *"Use the provided context to answer accurately."*
  - The `{question}` slot is filled at GENERATE time from the caller's input.
  - Retrieved document chunks (`background`) are injected into the prompt context by the `rag.query` call upstream — they flow into the generation implicitly through the PROMPT block's SELECT projection.
  - No sentinel tokens, scoring rubrics, or structured output format — plain-text natural language answer expected.

### 5. Control Flow

```
Input: context.question (user's free-text question)
  │
  ▼
CALL rag.query(context.question, top_k=3)  →  @background (top-3 doc chunks)
  │
  ▼
GENERATE answer(question)  →  @result  (LLM answer grounded in @background)
  │
  ▼
Return @result to caller
```

No branching, no looping, no exception handlers. The workflow is a straight retrieval → generation pipeline and terminates after the single GENERATE call.

### 6. How to Regenerate as SPL

```bash
# Step 1 — index your documents first
spl doc-rag add path/to/your-docs/

# Step 2 — generate SPL from this spec (paste Section 1 as text2spl input)
spl3 text2spl --description \
  "Given a free-text question, retrieve the top-3 most relevant document chunks \
   from a local vector index and generate a factually grounded answer using an LLM." \
  --mode workflow

# Step 3 — compile to any target
spl3 splc compile rag_query.spl --lang python/pocketflow
spl3 splc compile rag_query.spl --lang python/langgraph
spl3 splc compile rag_query.spl --lang go

# Step 4 — run directly
spl3 run rag_query.spl --adapter ollama -m gemma3 question="Where did Wen grow up?"
```