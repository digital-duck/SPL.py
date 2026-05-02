## 0. High-level Description

This workflow implements a two-phase Retrieval-Augmented Generation (RAG) pipeline expressed as two sequential WORKFLOW blocks — an offline indexing workflow and an online query workflow — that share a common state store analogous to SPL's `@var` namespace. The offline WORKFLOW executes three logical functions in order: a `ChunkDocuments` function that splits raw texts into fixed-size segments using a utility helper, an `EmbedDocuments` function that issues a CALL to the OpenAI Embeddings API for each chunk (expressed as a BatchNode fan-out), and a `CreateIndex` function that CALL-constructs a FAISS flat-L2 vector index from the resulting embedding matrix and stores it as `@index`. The online WORKFLOW then executes three further functions: `EmbedQuery` issues a CALL to the same embedding model to convert the user's question into a vector stored as `@query_embedding`; `RetrieveDocument` performs a CALL to the FAISS index search (k=1 nearest neighbor) and stores the best-matching chunk as `@retrieved_document`; and `GenerateAnswer` issues a GENERATE call to an LLM (GPT-4o-mini via OpenAI Chat Completions, or an alternate adapter selected at runtime via the SPL shim layer) with a tightly scoped prompt that injects `@retrieved_document` and `@query` as context slots, storing the model's reply as `@generated_answer`. Neither workflow contains a WHILE loop or EVALUATE branch — both are strictly linear pipelines — and the final answer is surfaced via an implicit RETURN of `@generated_answer` with optional CALL side-effects to write the result to a file. No explicit EXCEPTION handlers are defined; error propagation relies on Python runtime exceptions bubbling out of node boundaries.

## 1. Purpose

Answers a natural-language question by semantically retrieving the most relevant passage from a local document corpus and generating a concise, grounded response via an LLM.

---

## 2. SPL ↔ Python — PocketFlow Construct Mapping

| SPL Construct | Python — PocketFlow Equivalent | Notes |
|---|---|---|
| `WORKFLOW <name>` | `Flow(start=<node>)` function (e.g. `get_offline_flow()`, `get_online_flow()`) | Two separate `Flow` objects model two named workflows sharing one `shared` dict |
| `CREATE FUNCTION <name>` | `Node` or `BatchNode` subclass with `prep` / `exec` / `post` methods | Each class is one logical function; `exec` holds the prompt or computation |
| `GENERATE <fn>(...) INTO @<var>` | `call_llm(prompt)` inside `GenerateAnswerNode.exec`; result written to `shared["generated_answer"]` in `post` | Only `GenerateAnswerNode` is a true LLM generation step |
| `CALL <tool>(...) INTO @<var>` | `get_embedding(text)` calls inside `EmbedDocumentsNode.exec` / `EmbedQueryNode.exec`; `faiss.IndexFlatL2` + `index.add()` inside `CreateIndexNode.exec`; `index.search()` inside `RetrieveDocumentNode.exec` | Side-effect tool calls (embedding API, index construction, vector search) |
| `@<var>` shared state | `shared` dict passed through all nodes (keys: `texts`, `embeddings`, `index`, `query`, `query_embedding`, `retrieved_document`, `generated_answer`) | `post()` writes; `prep()` reads — exact analogue of SPL variable scoping |
| `WHILE <cond> DO ... END` | _(not present)_ | Both flows are linear; no iterative loop is modelled |
| `EVALUATE @<var> WHEN ... THEN ... ELSE ... END` | _(not present)_ | No branching on LLM output; `post()` always returns `"default"` |
| `RETURN @<var> WITH <k>=<v>` | `shared.get("generated_answer", "No answer generated.")` in `main.py`, optionally written to file | Implicit return; metadata (query, doc count) echoed to stdout |
| `EXCEPTION WHEN <Type> THEN ...` | _(not present — relies on Python runtime exceptions)_ | No `try/except` guards inside any node |
| Fan-out / batch parallelism | `BatchNode` (`ChunkDocumentsNode`, `EmbedDocumentsNode`) — `prep` returns iterable; `exec` is called once per item | SPL has no direct BatchNode analogue; closest mapping is a WHILE loop over items or a parallel GENERATE fan-out |
| Multi-model / adapter shim | `call_llm_shim` selected by `SPL_ADAPTER` / `SPL_MODEL` env vars; `get_embedding` always uses OpenAI `text-embedding-ada-002` | Models for generation and embedding are independently configurable |

---

## 3. Logical Functions / Prompts

### `ChunkDocuments` (`ChunkDocumentsNode`)
- **Role:** Preprocessing — splits each raw document string into overlapping or fixed-size segments before embedding.
- **Key conventions:** Calls `fixed_size_chunk(text, chunk_size=2000)`; no LLM involved. Output flattens all per-document chunk lists into a single `shared["texts"]` list, overwriting the originals.

### `EmbedDocuments` (`EmbedDocumentsNode`)
- **Role:** Offline encoding — converts every text chunk into a dense vector for indexing.
- **Key conventions:** `BatchNode` fan-out; calls `get_embedding(text)` (OpenAI `text-embedding-ada-002`); assembles results as `np.float32` matrix stored in `shared["embeddings"]`.

### `CreateIndex` (`CreateIndexNode`)
- **Role:** Index construction — builds a searchable FAISS flat L2 index from the embedding matrix.
- **Key conventions:** Uses `faiss.IndexFlatL2(dimension)`; no LLM; stores index object in `shared["index"]`.

### `EmbedQuery` (`EmbedQueryNode`)
- **Role:** Online query encoding — mirrors `EmbedDocuments` for the user's question.
- **Key conventions:** Single call to `get_embedding(query)`; wraps result in a `(1, dim)` array for FAISS compatibility; stored in `shared["query_embedding"]`.

### `RetrieveDocument` (`RetrieveDocumentNode`)
- **Role:** Nearest-neighbor retrieval — finds the single most semantically similar chunk.
- **Key conventions:** `index.search(query_embedding, k=1)`; returns dict `{text, index, distance}` stored in `shared["retrieved_document"]`. Only top-1 result is used (no reranking).

### `GenerateAnswer` (`GenerateAnswerNode`)
- **Role:** Answer synthesis — the sole GENERATE step; prompts the LLM to answer the question given the retrieved passage.
- **Key conventions:** Minimal few-word prompt with two injected slots (`{query}`, `{retrieved_doc['text']}`). Instruction token is `"Briefly answer"`. No chain-of-thought, no scoring sentinel, no structured output format enforced — raw LLM text is returned and stored in `shared["generated_answer"]`.

---

## 4. Control Flow

```
[offline_flow.run(shared)]
  START → ChunkDocumentsNode
        → EmbedDocumentsNode   (BatchNode: one exec call per chunk)
        → CreateIndexNode
  END   (returns implicitly; @index, @embeddings, @texts now populated)

[online_flow.run(shared)]
  START → EmbedQueryNode
        → RetrieveDocumentNode
        → GenerateAnswerNode
  END   → RETURN @generated_answer

[optional CALL side-effect]
  IF --out provided → CALL file_write(@generated_answer) INTO <path>
```

Both flows terminate after a single pass through their linear node chain. Every `post()` returns `"default"`, so no conditional edges are ever activated. The only branching exists outside the flows: the CLI's `--input` flag selects the document corpus, and the `--out` flag triggers the file-write side-effect. In SPL terms this maps to `RETURN @generated_answer WITH status="ok", query=@query`.

---

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```

> **Tip:** When pasting Section 0 into `text2spl`, append the following hints to improve fidelity:
> - `"Use two named WORKFLOWs: OFFLINE_INDEX and ONLINE_QUERY sharing @index, @texts, @embeddings, @query_embedding, @retrieved_document, @generated_answer."`
> - `"EmbedDocuments and ChunkDocuments are BatchNode fan-outs — model as parallel CALL loops."`
> - `"GenerateAnswer is the only GENERATE step; all embedding and index operations are CALL steps."`
> - `"No WHILE or EVALUATE constructs are needed — both workflows are strictly linear."`