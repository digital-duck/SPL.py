# RAG Pipeline — PocketFlow

## Overview

A Retrieval-Augmented Generation (RAG) system built with [PocketFlow](https://github.com/The-Pocket/PocketFlow).
The pipeline has three stages wired in sequence:

```
IngestNode → RetrieveNode → GenerateNode
```

| Stage | What it does |
|---|---|
| **IngestNode** | Chunks input documents and embeds each chunk |
| **RetrieveNode** | Embeds the query, ranks chunks by cosine similarity, returns top-k |
| **GenerateNode** | Builds a grounded prompt and calls the LLM for the final answer |

All state lives in a single `shared` dict — no persistent storage.

## Requirements

```bash
pip install openai numpy pocketflow
```

Python 3.10+ recommended.

## Setup

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OPENROUTER_API_KEY` | **yes** | — | API key for OpenRouter |
| `LLM_MODEL` | no | `anthropic/claude-3-haiku` | Chat model |
| `EMBED_MODEL` | no | `openai/text-embedding-3-small` | Embedding model |
| `CHUNK_SIZE` | no | `500` | Chunk size in characters |
| `CHUNK_OVERLAP` | no | `50` | Overlap between chunks in characters |
| `TOP_K` | no | `3` | Number of chunks to retrieve |

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

## Usage

```bash
python vibe_output..py
```

### Expected output (abbreviated)

```
============================================================
RAG Pipeline — PocketFlow demo
============================================================
Query: How does Python handle memory management?

[IngestNode] Chunking 5 document(s)...
[IngestNode] Produced 5 chunks. Embedding...
[IngestNode] Embedded 5 chunks.
[RetrieveNode] Embedding query: 'How does Python handle memory management?'
[RetrieveNode] Retrieved top-3 chunks (scores: [0.8821, 0.7134, 0.6208]).
[GenerateNode] Calling LLM (anthropic/claude-3-haiku)...

============================================================
Answer:
============================================================
Python handles memory management automatically through two complementary mechanisms.
The primary mechanism is reference counting: every object maintains a count of how many
references point to it, and when that count reaches zero the memory is freed immediately.
For cases where reference counting falls short—specifically reference cycles—Python
includes a supplemental cyclic garbage collector that detects and frees cyclic structures.
```

## Workflow logic (step by step)

1. **`IngestNode.prep`** — validates that `shared["documents"]` is non-empty; raises `ValueError` otherwise.
2. **`IngestNode.exec`** — splits each document into overlapping character-level chunks, then calls the embedding API for each chunk sequentially.
3. **`IngestNode.post`** — writes `shared["chunks"]` and `shared["embeddings"]`.
4. **`RetrieveNode.prep`** — validates that `shared["query"]` is non-empty; raises `ValueError` otherwise.
5. **`RetrieveNode.exec`** — embeds the query, computes cosine similarity against every stored chunk embedding, sorts descending, returns the top-k chunk texts.
6. **`RetrieveNode.post`** — writes `shared["retrieved_chunks"]`.
7. **`GenerateNode.prep`** — reads `query` and `retrieved_chunks` from shared state.
8. **`GenerateNode.exec`** — builds a numbered-context prompt instructing the model to answer only from context, then calls the LLM.
9. **`GenerateNode.post`** — writes `shared["answer"]`.