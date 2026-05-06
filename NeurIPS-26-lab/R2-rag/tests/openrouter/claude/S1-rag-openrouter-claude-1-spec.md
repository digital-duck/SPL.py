## 0. High-level Description

This workflow implements a two-phase Retrieval-Augmented Generation (RAG) system using two named SPL WORKFLOWs: an **offline indexing workflow** and an **online query-answering workflow**, both sharing a common state store (SPL `@vars`). The offline WORKFLOW applies three sequential functions — `ChunkDocuments`, `EmbedDocuments`, and `CreateIndex` — which respectively split raw text documents into fixed-size chunks using a utility function, embed each chunk in batch via the OpenAI `text-embedding-ada-002` model, and build a FAISS flat-L2 vector index over the resulting embeddings, storing all intermediate artifacts (`@chunks`, `@embeddings`, `@index`) in shared state. The online WORKFLOW then applies three further sequential functions — `EmbedQuery`, `RetrieveDocument`, and `GenerateAnswer` — which embed the user's natural-language query using the same embedding model, perform a nearest-neighbour search (k=1) against the FAISS index to retrieve the single most relevant chunk (stored as `@retrieved_document`), and finally GENERATE a grounded answer by calling an LLM (`gpt-4o-mini` or a configurable adapter) with a prompt that injects the query and the retrieved context, storing the result in `@generated_answer`. Both batch embedding steps (documents and query) are modelled as GENERATE calls over iterables, while the FAISS index construction and vector search are CALL side-effect tool operations; there are no WHILE loops or EVALUATE branches because the control flow is strictly linear within each WORKFLOW. The final answer is returned from the online WORKFLOW along with optional CALL side-effects to write the result to a file on disk.

---

## 1. Purpose

This implementation gives end users a lightweight, fully local-or-cloud RAG pipeline that indexes an arbitrary text corpus once (offline), then answers natural-language questions against it in real time (online) by retrieving the most semantically relevant chunk and generating a grounded, concise answer.

---

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW offline_indexing` | `get_offline_flow()` → `Flow(start=chunk_docs_node)` | Encapsulates the three-node document ingestion pipeline |
| `WORKFLOW online_querying` | `get_online_flow()` → `Flow(start=embed_query_node)` | Encapsulates the three-node retrieval-and-generation pipeline |
| `CREATE FUNCTION ChunkDocuments` | `ChunkDocumentsNode` (`BatchNode`) with `fixed_size_chunk()` utility | Splits each document into 2 000-character fixed-size chunks |
| `CREATE FUNCTION EmbedDocuments` | `EmbedDocumentsNode` (`BatchNode`) calling `get_embedding()` per chunk | Batch embedding via OpenAI `text-embedding-ada-002` |
| `CREATE FUNCTION CreateIndex` | `CreateIndexNode` (`Node`) using `faiss.IndexFlatL2` | Pure tool operation; no LLM call |
| `CREATE FUNCTION EmbedQuery` | `EmbedQueryNode` (`Node`) calling `get_embedding()` | Single-vector embedding of the user query |
| `CREATE FUNCTION RetrieveDocument` | `RetrieveDocumentNode` (`Node`) calling `index.search(k=1)` | FAISS nearest-neighbour lookup; pure tool operation |
| `CREATE FUNCTION GenerateAnswer` | `GenerateAnswerNode` (`Node`) calling `call_llm(prompt)` | Only node that invokes the generative LLM |
| `GENERATE GenerateAnswer(...) INTO @generated_answer` | `call_llm(prompt)` inside `GenerateAnswerNode.exec()` | Prompt injects `{query}` and `{retrieved_document.text}` |
| `CALL CreateIndex(...) INTO @index` | `faiss.IndexFlatL2` + `index.add(embeddings)` in `CreateIndexNode.exec()` | Side-effect tool call; mutates the FAISS index object |
| `CALL RetrieveDocument(...) INTO @retrieved_document` | `index.search(query_embedding, k=1)` in `RetrieveDocumentNode.exec()` | Side-effect tool call; reads FAISS index |
| `CALL write_file(@generated_answer)` | `Path(out).write_text(...)` in `main.py` | Optional file-write side-effect after online flow completes |
| Shared `@vars` (`@chunks`, `@embeddings`, `@index`, `@query_embedding`, `@retrieved_document`, `@generated_answer`) | `shared` dict passed to every node's `prep` / `post` | Single mutable store threaded through both workflows |
| `EXCEPTION WHEN EmbeddingError` | Not explicitly coded; implicit OpenAI SDK exceptions propagate | No named handler present; would be added in SPL for robustness |

---

## 3. Logical Functions / Prompts

### 3.1 `ChunkDocuments`
- **Role:** Pre-processing entry point of the offline WORKFLOW. Transforms the raw list of document strings into a flat list of fixed-size text chunks ready for embedding.
- **Key conventions:** Uses a pure utility function `fixed_size_chunk(text, chunk_size=2000)` with a sliding window of 2 000 characters and no overlap. No LLM call. Output replaces `shared["texts"]` in-place so downstream nodes see only chunks.

### 3.2 `EmbedDocuments`
- **Role:** Batch embedding step in the offline WORKFLOW. Converts every chunk into a dense float32 vector.
- **Key conventions:** Runs as a `BatchNode` — each chunk is embedded independently via `get_embedding(text)` which calls the OpenAI `text-embedding-ada-002` endpoint. Results are stacked into a `numpy` array of shape `(N, D)` and stored as `shared["embeddings"]`. No prompt template; this is a deterministic embedding call, not a generative LLM call.

### 3.3 `CreateIndex`
- **Role:** Finalises the offline WORKFLOW by building a searchable vector index from the embeddings.
- **Key conventions:** Uses FAISS `IndexFlatL2` (exact L2 nearest-neighbour, no quantisation). Dimension is inferred from `embeddings.shape[1]`. The resulting index object is stored as `shared["index"]`. Pure CALL side-effect; no LLM or embedding call.

### 3.4 `EmbedQuery`
- **Role:** Entry point of the online WORKFLOW. Converts the user's natural-language query string into a single query embedding vector.
- **Key conventions:** Calls the same `get_embedding()` utility as `EmbedDocuments`, ensuring the query and document embeddings live in the same vector space. Output is wrapped in a `(1, D)` numpy array for FAISS compatibility and stored as `shared["query_embedding"]`.

### 3.5 `RetrieveDocument`
- **Role:** Nearest-neighbour retrieval step in the online WORKFLOW. Finds the single most semantically similar chunk to the query.
- **Key conventions:** Calls `index.search(query_embedding, k=1)` returning the best index position and L2 distance. Returns a structured dict `{text, index, distance}` stored as `shared["retrieved_document"]`. No LLM call; this is a deterministic CALL side-effect.

### 3.6 `GenerateAnswer`
- **Role:** The sole generative LLM step; the terminal node of the online WORKFLOW.
- **Key conventions:** Constructs a concise instruction prompt with two injected slots:
  ```
  Briefly answer the following question based on the context provided:
  Question: {query}
  Context: {retrieved_document.text}
  Answer:
  ```
  The word "Briefly" acts as a soft length sentinel. Output is free-form natural-language text; no structured format, scoring, or sentinel tokens are required. Result stored as `shared["generated_answer"]` and echoed to stdout.

---

## 4. Control Flow

**Offline WORKFLOW (linear, no branches or loops):**

1. `ChunkDocuments` reads `shared["texts"]`, chunks every document, and writes the flat chunk list back to `shared["texts"]`.
2. `EmbedDocuments` reads the chunk list, embeds each chunk in batch, and writes `shared["embeddings"]`.
3. `CreateIndex` reads `shared["embeddings"]`, builds and populates a FAISS index, and writes `shared["index"]`. The offline WORKFLOW then terminates.

**Online WORKFLOW (linear, no branches or loops):**

1. `EmbedQuery` reads `shared["query"]`, embeds it, and writes `shared["query_embedding"]`.
2. `RetrieveDocument` reads `shared["query_embedding"]`, `shared["index"]`, and `shared["texts"]`; executes a k=1 FAISS search; and writes `shared["retrieved_document"]`.
3. `GenerateAnswer` reads `shared["query"]` and `shared["retrieved_document"]`, constructs the prompt, calls the LLM, and writes `shared["generated_answer"]`. The online WORKFLOW then terminates.

**Top-level orchestration (`main.py`):**
The offline WORKFLOW runs first to completion, then the online WORKFLOW runs. After both complete, the answer is read from `shared["generated_answer"]` and optionally written to a file via a CALL side-effect. There are no WHILE loops, EVALUATE branches, or retry logic anywhere in the current implementation.

---

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This workflow implements a two-phase Retrieval-Augmented Generation (RAG) system using two named SPL WORKFLOWs: an offline indexing workflow and an online query-answering workflow, both sharing a common state store (SPL @vars). The offline WORKFLOW applies three sequential functions — ChunkDocuments, EmbedDocuments, and CreateIndex — which respectively split raw text documents into fixed-size chunks using a utility function, embed each chunk in batch via the OpenAI text-embedding-ada-002 model, and build a FAISS flat-L2 vector index over the resulting embeddings, storing all intermediate artifacts (@chunks, @embeddings, @index) in shared state. The online WORKFLOW then applies three further sequential functions — EmbedQuery, RetrieveDocument, and GenerateAnswer — which embed the user's natural-language query using the same embedding model, perform a nearest-neighbour search (k=1) against the FAISS index to retrieve the single most relevant chunk (stored as @retrieved_document), and finally GENERATE a grounded answer by calling an LLM (gpt-4o-mini or a configurable adapter) with a prompt that injects the query and the retrieved context, storing the result in @generated_answer. Both batch embedding steps (documents and query) are modelled as GENERATE calls over iterables, while the FAISS index construction and vector search are CALL side-effect tool operations; there are no WHILE loops or EVALUATE branches because the control flow is strictly linear within each WORKFLOW. The final answer is returned from the online WORKFLOW along with optional CALL side-effects to write the result to a file on disk." --mode workflow

# Step 2 — compile to any target runtime
spl3 splc compile rag_pipeline.spl --lang python/pocketflow
spl3 splc compile rag_pipeline.spl --lang python/langgraph
spl3 splc compile rag_pipeline.spl --lang go
```