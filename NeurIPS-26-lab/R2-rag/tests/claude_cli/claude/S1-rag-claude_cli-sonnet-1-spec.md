## 0. High-level Description

This workflow implements a two-phase Retrieval Augmented Generation (RAG) pipeline expressed as two sequential SPL WORKFLOWs: an **offline indexing workflow** and an **online query workflow**, sharing state through a common `@shared` variable store. The offline phase contains three logical functions: `ChunkDocuments` (a batch CREATE FUNCTION that splits raw texts into fixed-size chunks), `EmbedDocuments` (a batch CREATE FUNCTION that issues CALL operations to an embedding API for each chunk and accumulates the resulting vectors), and `CreateIndex` (a CALL that builds a FAISS L2 vector index from the accumulated embeddings). The online phase contains three further logical functions: `EmbedQuery` (a CALL to the same embedding API for the user's question), `RetrieveDocument` (a CALL to the FAISS index that performs a k=1 nearest-neighbor search and returns the best-matching chunk with its distance score), and `GenerateAnswer` (a GENERATE call to an LLM whose prompt template slots in `{query}` and `{context}` from the retrieved document). Control flow is strictly linear in both workflows — no WHILE loop or EVALUATE branch is present — and each step RETURNs a `"default"` action token to advance to the next node. The final RETURN surfaces `@generated_answer` to the caller and, when an output path is supplied, issues a side-effect CALL that persists the Q/A pair to disk. No explicit EXCEPTION handlers are defined; errors propagate from the underlying API calls.

## 1. Purpose

Answers a user's natural-language question by first indexing a small document corpus into a FAISS vector store (offline), then retrieving the single most relevant chunk at query time and generating a grounded answer with an LLM (online).

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW offline_indexing` | `get_offline_flow()` → `Flow(start=chunk_docs_node)` | Linear three-node PocketFlow pipeline |
| `WORKFLOW online_query` | `get_online_flow()` → `Flow(start=embed_query_node)` | Linear three-node PocketFlow pipeline |
| `CREATE FUNCTION ChunkDocuments` | `ChunkDocumentsNode(BatchNode)` | Batch node; `exec(text)` maps `fixed_size_chunk` over each doc |
| `CREATE FUNCTION EmbedDocuments` | `EmbedDocumentsNode(BatchNode)` | Batch node; `exec(text)` calls `get_embedding` per chunk |
| `CREATE FUNCTION CreateIndex` | `CreateIndexNode(Node)` | Single node; `exec(embeddings)` runs `faiss.IndexFlatL2` + `index.add` |
| `CREATE FUNCTION EmbedQuery` | `EmbedQueryNode(Node)` | Single node; `exec(query)` calls `get_embedding` |
| `CREATE FUNCTION RetrieveDocument` | `RetrieveDocumentNode(Node)` | Single node; `exec(inputs)` calls `index.search(q_emb, k=1)` |
| `CREATE FUNCTION GenerateAnswer` | `GenerateAnswerNode(Node)` | Contains the only LLM prompt template |
| `GENERATE GenerateAnswer(...) INTO @generated_answer` | `call_llm(prompt)` inside `GenerateAnswerNode.exec` | Only true LLM generation call |
| `CALL get_embedding(...) INTO @embedding` | `get_embedding(text)` in `EmbedDocumentsNode` / `EmbedQueryNode` | Deterministic API call, not a generation |
| `CALL faiss_search(...) INTO @retrieved_document` | `index.search(query_embedding, k=1)` in `RetrieveDocumentNode` | Pure vector math side-effect |
| `CALL write_file(...)` | `Path(out).write_text(...)` in `main()` | Optional output persistence |
| `@vars` (shared state) | `shared` dict passed through `flow.run(shared)` | All inter-node data lives here |
| `RETURN @generated_answer WITH status="default"` | `return "default"` from each `post()` + final `shared["generated_answer"]` | `"default"` token routes to next node |
| `WHILE` | *(absent)* | No iterative refinement loop |
| `EVALUATE` | *(absent)* | No conditional branching |
| `EXCEPTION WHEN` | *(absent)* | Errors propagate from API calls unhandled |

## 3. Logical Functions / Prompts

**ChunkDocuments**
- Role: Preprocesses raw documents into retrieval-sized units before embedding.
- Conventions: Fixed-size chunking at 2000 characters; no overlap; returns a list of strings. Implemented as a `BatchNode` so PocketFlow maps `exec` over each document independently.

**EmbedDocuments**
- Role: Converts each text chunk into a dense float32 vector using the OpenAI `text-embedding-ada-002` model.
- Conventions: Batch node; results are stacked via `np.array(exec_res_list, dtype=np.float32)` into a 2-D matrix stored in `@embeddings`.

**CreateIndex**
- Role: Builds the offline searchable artifact — a FAISS `IndexFlatL2` — from the embedding matrix.
- Conventions: No prompt; pure deterministic CALL. Dimension inferred from `embeddings.shape[1]`. Index stored in `@index`.

**EmbedQuery**
- Role: Projects the user's query into the same vector space as the document chunks.
- Conventions: Same embedding model as `EmbedDocuments`. Output reshaped to `(1, dim)` for FAISS compatibility.

**RetrieveDocument**
- Role: Finds the single nearest chunk to the query vector.
- Conventions: `k=1` nearest-neighbor search; returns `{text, index, distance}` dict stored in `@retrieved_document`. No LLM involved.

**GenerateAnswer**
- Role: The sole GENERATE step; produces the final natural-language answer.
- Prompt template:
  ```
  Briefly answer the following question based on the context provided:
  Question: {query}
  Context: {retrieved_document.text}
  Answer:
  ```
- Conventions: Instructs brevity ("Briefly"); injects `{query}` and `{context}` slots; no sentinel tokens, no scoring rubric, no structured output format — plain text answer expected.

## 4. Control Flow

```
WORKFLOW offline_indexing
  CALL ChunkDocuments(@texts) INTO @texts          -- batch, replaces original texts with chunks
  CALL EmbedDocuments(@texts) INTO @embeddings     -- batch, one embedding per chunk
  CALL CreateIndex(@embeddings) INTO @index        -- builds FAISS L2 index
  RETURN WITH status="done"

WORKFLOW online_query
  CALL EmbedQuery(@query) INTO @query_embedding
  CALL RetrieveDocument(@query_embedding, @index, @texts) INTO @retrieved_document
  GENERATE GenerateAnswer(@query, @retrieved_document) INTO @generated_answer
  -- optional side-effect:
  CALL write_file(@out, @query, @generated_answer)
  RETURN @generated_answer WITH status="done"
```

No WHILE loop — both workflows execute their nodes exactly once in sequence. No EVALUATE branch — `RetrieveDocument` always returns one result and `GenerateAnswer` always runs. Termination is guaranteed by the finite linear chain. The `"default"` action token returned by each `post()` method is the PocketFlow equivalent of an unconditional advance to the next node.

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```

**Regeneration notes:**
- The two WORKFLOWs (`offline_indexing`, `online_query`) share `@vars`; `text2spl` should be told they run sequentially against the same shared store, not as independent pipelines.
- `EmbedDocuments` and `ChunkDocuments` must be flagged as **batch** functions so the compiler emits `BatchNode` (PocketFlow) or a `map` step (LangGraph) rather than a single-call node.
- The only `GENERATE` call is `GenerateAnswer`; the embedding and FAISS calls are `CALL` (deterministic tool calls), not LLM generations — preserve this distinction in the SPL source to avoid the compiler wrapping them in LLM retry logic.
- There is no WHILE or EVALUATE to reconstruct; if `text2spl` inserts them by default, remove them manually before compiling.