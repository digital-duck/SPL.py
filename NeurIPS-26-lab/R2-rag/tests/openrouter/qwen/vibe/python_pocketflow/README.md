# RAG Workflow with PocketFlow Orchestration

## Overview
This implementation demonstrates a Retrieval-Augmented Generation (RAG) system using a minimalist, ETL-style orchestration framework. It splits execution into two distinct, sequential phases:
1. **Offline Indexing**: Chunks raw documents, generates vector embeddings, builds a FAISS L2 index, and persists it to disk.
2. **Online Query**: Embeds a user query, performs a single nearest-neighbor search against the FAISS index, formats a context-aware prompt, calls an LLM, and logs/persists the result.

## Requirements
```bash
pip install faiss-cpu numpy requests
```
*(Note: `faiss-cpu` is used for CPU-based vector search. Use `faiss-gpu` if CUDA is available.)*

## Setup
Export the following environment variables before running:
```bash
export OPENAI_API_KEY="your-key-here"       # or OPENROUTER_API_KEY
export LLM_MODEL="gpt-3.5-turbo"            # Optional, defaults to gpt-3.5-turbo
export EMBEDDING_MODEL="text-embedding-3-small" # Optional, defaults to text-embedding-3-small
export OPENAI_BASE_URL="https://api.openai.com/v1" # Optional, change for OpenRouter/other providers
```

## Usage
Run the script directly:
```bash
python rag_workflow.py
```

### Expected Output
```
>>> Starting Phase: Offline Indexing
  [EXEC] ChunkDocuments
    Chunked 3 texts into X chunks.
  [EXEC] EmbedDocuments
    Embedding X chunks via API...
  [EXEC] BuildIndex
  [EXEC] PersistIndex
    FAISS index saved to vector_store.idx
>>> Completed Phase: Offline Indexing

>>> Starting Phase: Online Query
  [EXEC] EmbedQuery
  [EXEC] RetrieveDocument
  [EXEC] GenerateAnswer
  [EXEC] SaveAndLog

[CONSOLE LOG] Q&A pair persisted to output_qa.md
Query: What is the primary purpose of the Faiss library?
Answer: Faiss is a library designed for efficient similarity search and clustering of dense vectors...
>>> Completed Phase: Online Query
```

## Workflow Logic Step-by-Step
1. **Initialization**: A `shared_state` dictionary is populated with `@texts` (raw corpus) and `@query` (user question).
2. **Offline Phase**:
   - `ChunkDocuments`: Splits `@texts` into fixed-size `@chunks`.
   - `EmbedDocuments`: Sends each chunk to the embedding API, storing vectors in `@embeddings`.
   - `BuildIndex`: Initializes `faiss.IndexFlatL2(d)` and adds `@embeddings`, storing it in `@index`.
   - `PersistIndex`: Writes the FAISS index to `vector_store.idx` for durability.
3. **Online Phase**:
   - `EmbedQuery`: Vectorizes `@query` into `@query_embedding`.
   - `RetrieveDocument`: Performs `k=1` L2 search on `@index`, extracting the most relevant chunk into `@retrieved_document`.
   - `GenerateAnswer`: Interpolates `@query` and `@retrieved_document` into a plain-text prompt, calls `call_llm()`, and stores output in `@generated_answer`.
   - `SaveAndLog`: Writes the Q&A pair to `output_qa.md` via `Path.write_text()` and prints to stdout via `print()`.
4. **Termination**: The pipeline completes linearly. Exception handling is intentionally omitted per spec, relying on API connectivity and valid inputs.