## Summary

This workflow takes a text string as input and produces a dense vector embedding by calling the OpenAI Embeddings API. It is a foundational utility step — not a reasoning pipeline — useful for downstream tasks such as semantic search, clustering, or retrieval-augmented generation. Data engineers and ML practitioners benefit from having this as a reusable, composable workflow unit.

---

## Detailed Specification

### 1. Purpose

Given an arbitrary text string, produce its OpenAI embedding vector and make it available for downstream consumption.

---

### 2. High-level Description

This is a single-step, side-effect-oriented workflow with no iterative refinement and no LLM reasoning. The workflow accepts one INPUT variable `@text` and delegates immediately to a CALL targeting the OpenAI Embeddings API (`get_embedding`), storing the resulting float vector into `@embedding`. Because the operation is deterministic given a fixed model and input, there is no quality gate, no WHILE loop, and no EVALUATE branch. The OUTPUT is the raw embedding vector, which callers may persist to disk or pass to a downstream workflow. Exception handling for API failures (network errors, invalid key) is the only non-trivial control-flow concern.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW EmbedText` | `create_embedding_flow()` + `Flow(start=EmbeddingNode())` | Single-node flow; the workflow boundary is the flow object |
| `INPUT: @text` | `shared["text"]` read in `EmbeddingNode.prep()` | Populated by caller before `flow.run(shared)` |
| `CALL get_embedding(@text) INTO @embedding` | `EmbeddingNode.exec(text)` → calls `tools/embeddings.py::get_embedding()` | Pure tool call — no LLM reasoning; maps to SPL `CALL`, not `GENERATE` |
| `OUTPUT: @embedding` | `shared["embedding"] = exec_res` written in `EmbeddingNode.post()` | Stored back into shared state for the caller to read |
| `EXCEPTION WHEN APIError THEN ...` | Implicit (unhandled) — network/auth errors propagate as Python exceptions | Should be explicit in SPL for production use |

---

### 4. Logical Functions / Prompts

**`get_embedding(text)`** — `tools/embeddings.py`

- **Role:** The sole computational unit of the workflow. Wraps the OpenAI `embeddings.create` endpoint (model `text-embedding-ada-002` or equivalent).
- **Key conventions:** Input is a plain string; output is a list of floats (e.g., 1536 dimensions for `ada-002`). No prompt engineering, no temperature, no sampling — this is a deterministic API call.
- **Not a prompt template** — there is no `CREATE FUNCTION` equivalent here; the "function" is a direct API call with no parameterized prompt body.

---

### 5. Control Flow

```
START
  └─ CALL get_embedding(@text) INTO @embedding
       └─ (on success) COMMIT @embedding WITH STATUS = 'complete'
       └─ (on API failure) EXCEPTION WHEN APIError → surface to caller
END
```

Execution is strictly linear. There is no loop condition, no branching on output content, and no iterative refinement. The workflow runs exactly once per invocation.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Given an arbitrary text string, produce its OpenAI embedding vector and make it available for downstream consumption. The workflow accepts one INPUT variable @text, delegates to a CALL targeting the OpenAI Embeddings API, stores the resulting float vector into @embedding as OUTPUT, and raises an EXCEPTION on API failure. No LLM reasoning, no WHILE loop, no EVALUATE branch." --mode workflow

# Step 2 — compile to any target
spl3 splc compile embed_text.spl --lang python/pocketflow
spl3 splc compile embed_text.spl --lang python/langgraph
spl3 splc compile embed_text.spl --lang go
```