## 0. High-level Description

This workflow implements a classic Retrieval-Augmented Generation pipeline as a strictly linear PocketFlow graph — no loops, no branches. Seven nodes execute in sequence: `ChunkDocumentsNode` splits input documents on double-newlines into a flat `@texts` list; `EmbedDocumentsNode` builds a bag-of-words TF-IDF-style vocabulary from all tokens and produces L2-normalised numpy vectors; `CreateFaissIndexNode` packages the embedding matrix and vocabulary into an index dict (pure numpy, no FAISS dependency despite the SPL CALL name); `EmbedQueryNode` projects the query into the same vocabulary space; `RetrieveDocumentNode` selects the best-matching chunk via cosine similarity (argmax over `matrix @ query_vec`); `GenerateAnswerNode` calls the LLM with the retrieved chunk as context; `WriteOutputNode` conditionally writes the answer to a file when `@output_path` contains a `.` (file-extension heuristic). The `EVALUATE @output_path WHEN contains(".")` SPL construct maps to a plain `if "." in output_path` Python guard. The workflow terminates by setting `shared["status"] = "complete"` and returning `@generated_answer`. There are no loops or EXCEPTION blocks; failures propagate as Python exceptions.

---

## 1. Purpose

Answers a query against a small local document corpus using bag-of-words cosine retrieval and a single LLM synthesis call; optionally writes the answer to a file.

---

## 2. SPL ↔ Python — PocketFlow Construct Mapping

| SPL Construct | Python — PocketFlow Equivalent | Notes |
|---|---|---|
| `WORKFLOW RAGPipeline` | `build_rag_pipeline() → Flow(start=chunk)` | Linear chain; all nodes connected with `>>` (default action) |
| `INPUT @documents LIST, @query TEXT, @output_path TEXT := ""` | `run_rag_pipeline(documents, query, output_path="")` signature | `shared` dict initialized with all three inputs |
| `OUTPUT @generated_answer TEXT` | `return shared["generated_answer"]` | Caller gets string directly; `status` remains in `shared` |
| `CALL chunk_documents(@documents) INTO @texts` | `ChunkDocumentsNode.exec()` — `re.split(r"\n\n+", ...)` per doc | Falls back to whole-doc string if no double-newline found |
| `CALL embed_documents(@texts) INTO @embeddings` | `EmbedDocumentsNode.exec()` — token-frequency vectors, L2-normalised | Returns `{"embeddings": np.array, "vocab": dict}` bundle |
| `CALL create_faiss_index(@embeddings) INTO @index` | `CreateFaissIndexNode.exec()` — no FAISS; wraps matrix+vocab as dict | Name preserved from SPL; implementation is pure numpy |
| `CALL embed_query(@query) INTO @query_embedding` | `EmbedQueryNode.exec()` — same vocabulary, L2-normalised | Uses `shared["index"]["vocab"]` for dimension consistency |
| `CALL retrieve_document(@index, @query_embedding, @texts) INTO @retrieved_document` | `RetrieveDocumentNode.exec()` — `np.argmax(matrix @ qvec)` | Returns empty string if `matrix.shape[0] == 0` |
| `GENERATE generate_answer(@query, @retrieved_document) INTO @generated_answer` | `GenerateAnswerNode.exec()` → `_claude_cli(prompt)` | Single LLM call; free-form prose answer |
| `EVALUATE @output_path WHEN contains(".") THEN CALL write_file(...)` | `WriteOutputNode.exec()` — `if "." in output_path: open(...).write(...)` | Also creates parent dirs via `os.makedirs(..., exist_ok=True)` |
| `@write_result := "skipped"` | `return "skipped"` in the else branch of `WriteOutputNode.exec()` | Stored in `shared["write_result"]` |
| `RETURN @generated_answer WITH status = "complete"` | `shared["status"] = "complete"` in `WriteOutputNode.post()` | `run_rag_pipeline()` returns `shared["generated_answer"]` string |
| `CREATE FUNCTION generate_answer(query, retrieved_document)` | Module-level `generate_answer(query, retrieved_document)` calling `_claude_cli` | Prompt template embedded as a multi-line f-string |
| Adapter: `claude_cli`, model: `sonnet` | `subprocess.run(["claude", "-p", prompt, "--model", "sonnet"])` | `_claude_cli` helper with configurable model string |

---

## 3. Logical Functions / Prompts

### `generate_answer`
- **Role:** Single synthesis call. Given the retrieved document chunk as context, produces a prose answer to the query.
- **Prompt conventions:** Instructs the model to answer solely from provided context; explicitly asks it to acknowledge when context is insufficient rather than hallucinating.
- **Output:** Free-form prose; no structured format.

### Tool calls (deterministic, no LLM)
- `chunk_documents(docs)` — splits on `\n\n+`; falls back to whole-doc. Pure Python.
- `embed_documents(texts)` — bag-of-words frequency vectors, L2-normalised. Pure numpy.
- `create_faiss_index(embeddings)` — identity passthrough wrapping matrix + vocab. Pure numpy.
- `embed_query(query, vocab)` — same tokenisation as `embed_documents`, same vocab. Pure numpy.
- `retrieve_document(index, query_vec, texts)` — cosine argmax via `matrix @ qvec`. Returns `texts[best_idx]`.
- `write_file(path, content)` — `open(path, "w").write(content)` with `os.makedirs` for nested paths.

---

## 4. Control Flow

```
INPUT @documents LIST, @query TEXT, @output_path TEXT := ""

CALL chunk_documents(@documents)      → @texts
CALL embed_documents(@texts)          → @embeddings  (numpy TF-IDF vectors)
CALL create_faiss_index(@embeddings)  → @index       (matrix + vocab dict)
CALL embed_query(@query)              → @query_embedding
CALL retrieve_document(@index, @query_embedding, @texts) → @retrieved_document

GENERATE generate_answer(@query, @retrieved_document) → @generated_answer  [LLM]

EVALUATE @output_path
  WHEN contains(".") THEN
    CALL write_file(@output_path, @generated_answer) → @write_result
  ELSE
    @write_result := "skipped"
END

RETURN @generated_answer WITH status = "complete"
```

**Observed run (2026-05-04):** Query `"What is PocketFlow?"` against 5 sample documents → `status=complete`. Answer correctly identified PocketFlow as "a minimalist 100-line LLM framework for Python" from the retrieved chunk; noted that further detail would require additional sources.

---

## 5. How to Regenerate as SPL

```bash
# Step 1 — regenerate SPL from this spec
spl3 text2spl --description "$(sed -n '/^## 0\./,/^---/p' S5-rag-claude_cli-sonnet-2-spec.md)" \
    --mode workflow --adapter claude_cli

# Step 2 — run (requires tools.py with chunk/embed/retrieve implementations)
spl3 run RAGPipeline.spl --adapter claude_cli \
    --param documents="[...]" --param query="What is PocketFlow?"

# Step 3 — recompile to any target
spl3 splc compile RAGPipeline.spl --lang python/pocketflow --llm \
    --adapter claude_cli --model sonnet
spl3 splc compile RAGPipeline.spl --lang python/langgraph
spl3 splc compile RAGPipeline.spl --lang go
```
