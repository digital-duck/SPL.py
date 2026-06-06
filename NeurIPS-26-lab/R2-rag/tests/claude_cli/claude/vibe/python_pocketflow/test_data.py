test_cases = [
    {
        "documents": [
            "Python is a high-level interpreted language emphasising readability. "
            "Guido van Rossum created it and released the first version in 1991.",

            "Python's memory management is automatic. Reference counting is the primary "
            "mechanism; a cyclic garbage collector handles reference cycles.",

            "List comprehensions like [x**2 for x in range(10)] provide a concise "
            "syntax for building lists. Generator expressions are the lazy equivalent.",

            "Python decorators, applied with @, let you wrap functions to add logging, "
            "caching, or access-control behaviour without modifying the original code.",

            "NumPy, Pandas, Flask, Django, TensorFlow, and PyTorch are among the most "
            "popular third-party Python packages for scientific and web work.",
        ],
        "query": "How does Python handle memory management?",
    },
    {
        "documents": [
            "The HTTP/2 protocol multiplexes multiple requests over a single TCP connection, "
            "reducing latency compared with HTTP/1.1 which requires one connection per request.",

            "TLS 1.3 removes legacy cipher suites and cuts the handshake to one round trip, "
            "significantly speeding up secure connection establishment.",

            "DNS-over-HTTPS (DoH) encrypts DNS queries to prevent eavesdropping and "
            "tampering, improving user privacy on public networks.",

            "WebSockets provide full-duplex communication over a single TCP connection, "
            "enabling real-time features such as chat or live dashboards.",
        ],
        "query": "What are the latency benefits of HTTP/2 over HTTP/1.1?",
    },
    {
        "documents": [
            "Gradient descent updates model parameters in the direction opposite to the "
            "gradient of the loss function, iteratively minimising prediction error.",

            "Stochastic gradient descent (SGD) approximates the true gradient using a "
            "random mini-batch of training samples, trading accuracy for speed.",

            "Adam combines momentum (exponential moving average of gradients) with "
            "adaptive per-parameter learning rates derived from second-moment estimates.",

            "Learning-rate schedules such as cosine annealing or reduce-on-plateau "
            "adjust the step size during training to avoid overshooting minima.",
        ],
        "query": "How does the Adam optimiser differ from plain SGD?",
    },
]
</parameter>
</invoke>
</function_calls>

Now let me also create the README.md file in the vibe directory (matching the pattern from R1):
<function_calls>
<invoke name="Write">
<parameter name="file_path">/home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-rag/tests/claude_cli/claude/vibe/python_pocketflow/README.md</parameter>
<parameter name="content"># RAG Pipeline — PocketFlow

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
python "vibe_output..py"
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
</parameter>
</invoke>
</function_calls>

Here is the complete output as required by the mandatory output structure:

---

```python
import os
import sys
import numpy as np
from openai import OpenAI
from pocketflow import Node, Flow

LLM_MODEL   = os.environ.get("LLM_MODEL",    "anthropic/claude-3-haiku")
EMBED_MODEL = os.environ.get("EMBED_MODEL",  "openai/text-embedding-3-small")
CHUNK_SIZE  = int(os.environ.get("CHUNK_SIZE",   "500"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "50"))
TOP_K       = int(os.environ.get("TOP_K", "3"))

_client = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENROUTER_API_KEY environment variable is not set.")
        _client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    return _client


def call_llm(prompt: str, model: str = None) -> str:
    model = model or LLM_MODEL
    try:
        response = _get_client().chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"LLM call failed (model={model}): {e}") from e


def get_embedding(text: str) -> np.ndarray:
    try:
        response = _get_client().embeddings.create(model=EMBED_MODEL, input=text)
        return np.array(response.data[0].embedding, dtype=np.float32)
    except Exception as e:
        raise RuntimeError(f"Embedding call failed (model={EMBED_MODEL}): {e}") from e


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start += size - overlap
    return chunks


class IngestNode(Node):
    def prep(self, shared):
        docs = shared.get("documents", [])
        if not docs:
            raise ValueError("No documents provided. Set shared['documents'] to a non-empty list.")
        return docs

    def exec(self, docs):
        print(f"[IngestNode] Chunking {len(docs)} document(s)...")
        all_chunks = []
        for doc in docs:
            all_chunks.extend(chunk_text(doc))
        print(f"[IngestNode] Produced {len(all_chunks)} chunks. Embedding...")
        embeddings = [get_embedding(chunk) for chunk in all_chunks]
        print(f"[IngestNode] Embedded {len(embeddings)} chunks.")
        return all_chunks, embeddings

    def post(self, shared, prep_res, exec_res):
        chunks, embeddings = exec_res
        shared["chunks"] = chunks
        shared["embeddings"] = embeddings
        return "default"


class RetrieveNode(Node):
    def prep(self, shared):
        query = shared.get("query", "").strip()
        if not query:
            raise ValueError("Query is empty. Set shared['query'] to a non-empty string.")
        return query, shared["chunks"], shared["embeddings"]

    def exec(self, inputs):
        query, chunks, embeddings = inputs
        print(f"[RetrieveNode] Embedding query: '{query[:80]}'" + ("..." if len(query) > 80 else ""))
        query_emb = get_embedding(query)
        scores = [(i, cosine_similarity(query_emb, emb)) for i, emb in enumerate(embeddings)]
        scores.sort(key=lambda x: x[1], reverse=True)
        top_k = min(TOP_K, len(chunks))
        retrieved = [chunks[i] for i, _ in scores[:top_k]]
        print(f"[RetrieveNode] Retrieved top-{top_k} chunks (scores: {[round(s,4) for _,s in scores[:top_k]]}).")
        return retrieved

    def post(self, shared, prep_res, exec_res):
        shared["retrieved_chunks"] = exec_res
        return "default"


class GenerateNode(Node):
    def prep(self, shared):
        return shared["query"], shared["retrieved_chunks"]

    def exec(self, inputs):
        query, chunks = inputs
        context = "\n\n".join(f"[{i+1}] {chunk}" for i, chunk in enumerate(chunks))
        prompt = (
            "You are a helpful assistant. Answer the question using ONLY the context "
            "passages provided below. If the answer is not in the context, say so clearly.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Answer:"
        )
        print(f"[GenerateNode] Calling LLM ({LLM_MODEL})...")
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res
        return "default"


def build_rag_flow() -> Flow:
    ingest   = IngestNode()
    retrieve = RetrieveNode()
    generate = GenerateNode()
    ingest >> retrieve >> generate
    return Flow(start=ingest)


if __name__ == "__main__":
    documents = [
        (
            "Python is a high-level, interpreted programming language known for its clear syntax "
            "and readability. Created by Guido van Rossum and first released in 1991, Python "
            "emphasizes code readability and simplicity. Python supports multiple programming "
            "paradigms including procedural, object-oriented, and functional programming."
        ),
        (
            "Python's memory management is handled automatically by the runtime. It uses reference "
            "counting as the primary mechanism: each object tracks how many references point to it, "
            "and when that count drops to zero the memory is freed immediately. A supplemental cyclic "
            "garbage collector handles reference cycles that reference counting alone cannot free."
        ),
        (
            "Python's standard library is extensive and includes modules for file I/O, networking, "
            "databases, and more. Popular third-party packages include NumPy for numerical computing, "
            "Pandas for data analysis, Flask and Django for web development, and TensorFlow and "
            "PyTorch for machine learning."
        ),
        (
            "List comprehensions are a concise way to create lists in Python. For example, "
            "[x**2 for x in range(10)] produces a list of squares. Dictionary and set "
            "comprehensions work similarly. Generator expressions use parentheses and produce "
            "values lazily, making them memory-efficient for large datasets."
        ),
        (
            "Python decorators allow you to modify the behaviour of functions or classes. "
            "They are applied using the @ syntax and are commonly used for logging, "
            "authentication, caching, and measuring execution time. The functools module "
            "provides @functools.wraps to preserve wrapped function metadata."
        ),
    ]

    query = "How does Python handle memory management?"

    shared = {
        "documents": documents,
        "query":     query,
    }

    print("=" * 60)
    print("RAG Pipeline — PocketFlow demo")
    print("=" * 60)
    print(f"Query: {query}\n")

    flow = build_rag_flow()
    flow.run(shared)

    print("\n" + "=" * 60)
    print("Answer:")
    print("=" * 60)
    print(shared["answer"])
```

--- README ---

# RAG Pipeline — PocketFlow

## Overview

A Retrieval-Augmented Generation (RAG) system built with [PocketFlow](https://github.com/The-Pocket/PocketFlow). The pipeline has three stages wired in sequence:

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
| `CHUNK_OVERLAP` | no | `50` | Overlap between characters |
| `TOP_K` | no | `3` | Number of chunks to retrieve |

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

## Usage

```bash
python "vibe_output..py"
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
Python handles memory management automatically through two complementary mechanisms:
reference counting (freed immediately when count hits zero) and a cyclic garbage
collector for reference cycles that reference counting cannot handle.
```

## Workflow logic (step by step)

1. **`IngestNode.prep`** — validates `shared["documents"]` is non-empty; raises `ValueError` otherwise.
2. **`IngestNode.exec`** — splits each document into overlapping character-level chunks, then embeds each chunk via the embedding API.
3. **`IngestNode.post`** — writes `shared["chunks"]` and `shared["embeddings"]`.
4. **`RetrieveNode.prep`** — validates `shared["query"]` is non-empty; raises `ValueError` otherwise.
5. **`RetrieveNode.exec`** — embeds the query, computes cosine similarity against every stored embedding, sorts descending, returns top-k chunk texts.
6. **`RetrieveNode.post`** — writes `shared["retrieved_chunks"]`.
7. **`GenerateNode.prep`** — reads `query` and `retrieved_chunks` from shared state.
8. **`GenerateNode.exec`** — builds a numbered-context prompt (answer only from context) and calls the LLM.
9. **`GenerateNode.post`** — writes `shared["answer"]`.

--- TEST DATA ---

```python
test_cases = [
    {
        "documents": [
            "Python is a high-level interpreted language emphasising readability. "
            "Guido van Rossum created it and released the first version in 1991.",
            "Python's memory management is automatic. Reference counting is the primary "
            "mechanism; a cyclic garbage collector handles reference cycles.",
            "List comprehensions like [x**2 for x in range(10)] provide a concise "
            "syntax for building lists. Generator expressions are the lazy equivalent.",
            "Python decorators, applied with @, let you wrap functions to add logging, "
            "caching, or access-control behaviour without modifying the original code.",
            "NumPy, Pandas, Flask, Django, TensorFlow, and PyTorch are among the most "
            "popular third-party Python packages for scientific and web work.",
        ],
        "query": "How does Python handle memory management?",
    },
    {
        "documents": [
            "HTTP/2 multiplexes multiple requests over a single TCP connection, reducing "
            "latency compared with HTTP/1.1 which requires one connection per request.",
            "TLS 1.3 removes legacy cipher suites and cuts the handshake to one round trip, "
            "significantly speeding up secure connection establishment.",
            "DNS-over-HTTPS (DoH) encrypts DNS queries to prevent eavesdropping and "
            "tampering, improving user privacy on public networks.",
            "WebSockets provide full-duplex communication over a single TCP connection, "
            "enabling real-time features such as chat or live dashboards.",
        ],
        "query": "What are the latency benefits of HTTP/2 over HTTP/1.1?",
    },
    {
        "documents": [
            "Gradient descent updates model parameters opposite to the gradient of the loss, "
            "iteratively minimising prediction error.",
            "Stochastic gradient descent (SGD) approximates the true gradient using a random "
            "mini-batch of training samples, trading accuracy for speed.",
            "Adam combines momentum (exponential moving average of gradients) with adaptive "
            "per-parameter learning rates derived from second-moment estimates.",
            "Learning-rate schedules such as cosine annealing or reduce-on-plateau adjust "
            "the step size during training to avoid overshooting minima.",
        ],
        "query": "How does the Adam optimiser differ from plain SGD?",
    },
]
```

---

Files written:
- `NeurIPS-26-lab/R2-rag/tests/claude_cli/claude/S1-rag-claude_cli-claude-1-spec.md` — spec (requirement file)
- `NeurIPS-26-lab/R2-rag/tests/claude_cli/claude/vibe/python_pocketflow/vibe_output..py` — full implementation + README + TEST DATA
- `NeurIPS-26-lab/R2-rag/tests/claude_cli/claude/vibe/python_pocketflow/README.md` — standalone README

The implementation uses the exact PocketFlow `Node`/`Flow` API pattern (`prep` → `exec` → `post`, `>>` wiring) from the R1-agent reference run, adapted for a three-node RAG pipeline: `IngestNode` chunks and embeds documents, `RetrieveNode` does cosine-similarity retrieval, and `GenerateNode` constructs a grounded prompt and calls the LLM.