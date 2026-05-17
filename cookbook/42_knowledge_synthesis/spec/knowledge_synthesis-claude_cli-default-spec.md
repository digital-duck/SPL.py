## Summary

This workflow automates knowledge extraction and ingestion by combining an LLM-powered synthesis step with deterministic persistence to a vector store. Given a raw text document, it extracts three concise insights and stores them so that future retrieval-augmented generation (RAG) queries benefit from the newly indexed knowledge. It is designed for knowledge engineers and AI platform teams who need agents to contribute structured information back to a shared knowledge base.

---

## Detailed Specification

### 1. Purpose

Extract structured insights from raw text using an LLM and persist them to a vector store, enriching the knowledge base for future RAG-based queries.

### 2. High-level Description

The WORKFLOW `knowledge_synthesis` implements a RAG-writer pattern in which an LLM structures unstructured text and a deterministic side-effect persists the result. It begins by invoking a single GENERATE call using the `synthesize` function, which prompts the model to act as a knowledge engineer and produce exactly three bullet-point insights focused on novel claims, methods, or results. The extracted insights are written to a local log file via a CALL to `write_file`, incurring no additional LLM cost. A second CALL to `rag_update` persists the insights to the vector store, pairing them with the original source text as metadata. An EVALUATE block then inspects the update status: if it contains the token "success", an INFO log is emitted; otherwise a WARN log records the unexpected status. The workflow concludes with RETURN WITH status carrying the raw `@status` value, so callers can branch on success or failure. A named EXCEPTION handler catches `GenerationError` from the synthesis step and returns a structured error payload with `status='error'` and `reason='generation_error'`.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW knowledge_synthesis` | `WORKFLOW` | Top-level orchestration unit with typed INPUT/OUTPUT declarations |
| `CREATE FUNCTION synthesize(...)` | `CREATE FUNCTION` | Reusable prompt template with `{raw_text}` slot; returns TEXT |
| `GENERATE synthesize(@raw_text) INTO @insights` | `GENERATE` | Single LLM call; result bound to `@insights` |
| `CALL write_file(...) INTO NONE` | `CALL` | Deterministic side-effect; return value discarded |
| `CALL rag_update(...) INTO @status` | `CALL` | Deterministic side-effect; return value captured for downstream branching |
| `EVALUATE @status WHEN contains('success') THEN ... ELSE ... END` | `EVALUATE` | Branches on LLM/tool output using a substring sentinel token |
| `RETURN ... WITH status = @status` | `RETURN WITH` | Non-trivial: status value drives caller-side branching |
| `EXCEPTION WHEN GenerationError THEN` | `EXCEPTION` | Named handler for LLM generation failures |
| `@raw_text`, `@insights`, `@status`, `@log_dir` | `@vars` (shared state) | Workflow-scoped variables passed across steps |

### 4. Logical Functions / Prompts

**`synthesize`**
- **Role:** The sole LLM prompt in the workflow; transforms unstructured raw text into structured knowledge.
- **Key prompt conventions:**
  - System persona: "You are a knowledge engineer."
  - Hard cardinality constraint: "Extract exactly 3 core insights."
  - Output format: concise bullet points, one sentence each, no sub-bullets.
  - Scope filter: novel claims, methods, or results only — explicitly excludes background knowledge.
  - Input slot: `{raw_text}` is the only parameterized slot.

### 5. Control Flow

1. **Entry:** Log an INFO message, then GENERATE `synthesize(@raw_text)` → `@insights`.
2. **Side-effects:** CALL `write_file` to persist insights to `{log_dir}/insights.md`; CALL `rag_update` to index insights in the vector store, capturing the result in `@status`.
3. **Branch:** EVALUATE `@status` — if it `contains('success')`, log INFO; otherwise log WARN. No loop; this is a single-pass check.
4. **Termination:** RETURN the formatted status string WITH `status = @status`, allowing callers to inspect the outcome.
5. **Exception path:** If GENERATE raises `GenerationError`, execution jumps to the EXCEPTION handler, which returns `'synthesis_failed'` WITH `status='error'`, `reason='generation_error'` — bypassing all subsequent steps.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Extract structured insights from raw text using an LLM and persist them to a vector store, enriching the knowledge base for future RAG-based queries." --mode workflow

# Step 2 — compile to any target
spl3 splc compile knowledge_synthesis.spl --lang python/pocketflow
spl3 splc compile knowledge_synthesis.spl --lang python/langgraph
spl3 splc compile knowledge_synthesis.spl --lang go
```