## 0. High-level Description
This workflow implements a Retrieval-Augmented Generation (RAG) pipeline that ingests raw document text and a user query, processes them through a deterministic ETL sequence, and produces a grounded response using a configurable OpenRouter-hosted Qwen model. It begins by declaring a named `WORKFLOW` that initializes shared state variables and accepts string inputs. The pipeline executes a linear chain of `CALL` operations to semantically chunk the text, generate vector embeddings, construct an in-memory FAISS-style index, and persist it with console logging. After embedding the user query and performing a nearest-neighbor search, it invokes `GENERATE` using a `CREATE FUNCTION` prompt template to produce a concise answer. A final side-effect `CALL` writes the output to a markdown file before the workflow terminates via `RETURN @result WITH status="complete"`. Exception handling and model routing are delegated to the underlying runtime environment, with no `WHILE` loops or `EVALUATE` branches required for this strictly sequential execution path.

## 1. Purpose
This implementation provides a fully automated, file-backed RAG pipeline that indexes raw text, retrieves contextually relevant chunks for a given query, and generates a concise, model-grounded answer using OpenRouter.

## 2. SPL ↔ Python Construct Mapping
| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW` | `class S3RagOpenrouterQwenPipeline` | Encapsulates workflow state, input parameters, and the `run()` execution entry point |
| `INPUT` / `OUTPUT` | `__init__(raw_input, user_query)` & `self.result` | Initializes `@raw_input`, `@user_query`, and allocates the final `@result` slot |
| `CREATE FUNCTION` | `def FormatPrompt(doc, query)` | Defines a reusable prompt template with `{doc}` and `{query}` interpolation slots |
| `CALL` (ETL/Tools) | `_call_chunk_raw_texts`, `_call_generate_vector_embeddings`, `_call_construct_faiss_index`, `_call_log_and_persist_index`, `_call_embed_query`, `_call_nearest_neighbor_search`, `_call_write_file` | Executes deterministic data transformations, vector math, and I/O side-effects, sequentially mutating `@vars` |
| `GENERATE` | `_generate_with_openrouter(prompt)` | Performs HTTP POST to OpenRouter, handles JSON payload/response, and stores LLM text in `@result` |
| Shared `@vars` | Local variables in `run()` (`texts`, `embeddings`, `index`, `query_embedding`, `retrieved_doc`, etc.) | Mirrors SPL variable scoping; each step assigns its output to the next step's input |
| `RETURN WITH` | `return self.result, {"status": "complete"}` | Terminates execution and emits a non-default status token to signal successful completion |
| `EXCEPTION` | Not explicitly defined | Runtime errors (e.g., missing API key, network timeout) propagate as standard Python exceptions; no named handler is wired into the workflow graph |

## 3. Logical Functions / Prompts
- **FormatPrompt**
  - **Role:** Constructs the final generation prompt by injecting the retrieved document context and the original user query into a single instruction.
  - **Key prompt conventions:** Uses explicit `Context: {doc}. Question: {query}.` framing to ground the LLM in the retrieved passage. Directs the model to output a "concise and accurate answer." Does not enforce JSON schema or sentinel tokens; expects free-form natural language text.

## 4. Control Flow
The workflow begins by assigning the raw input and query to scoped variables. It then advances through six sequential `CALL` operations: text chunking, embedding generation, index construction, index persistence/logging, query embedding, and cosine similarity-based nearest-neighbor search. Once the top-matching chunk is retrieved, a `GENERATE` step invokes the OpenRouter Qwen model with the formatted prompt. The resulting text is immediately passed to a `CALL` operation that writes it to `output.md`. The pipeline halts execution with a `RETURN @result WITH status="complete"`. Control flow is entirely linear; there are no `WHILE` iterations or `EVALUATE` conditional branches.

## 5. How to Regenerate as SPL
```
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```