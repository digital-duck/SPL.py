"""RAG tools for S3-rag-openrouter-qwen.spl.

Provides CALL-able implementations matching the qwen-generated SPL function names:
  ChunkRawTexts, GenerateVectorEmbeddings, ConstructFAISSIndex,
  LogAndPersistIndex, EmbedQuery, NearestNeighborSearch

Key differences from sonnet tools.py:
- ChunkRawTexts takes a plain string (not JSON array)
- NearestNeighborSearch only receives (index_path, query_embedding) — texts are not
  passed through the SPL pipeline, so they are preserved in module-level state and
  written as a .chunks.json sidecar alongside the .faiss file at index creation time.
- Embeddings: ollama qwen3-embedding:0.6b (local, no API key needed)
"""

from __future__ import annotations
import json
import time
import tempfile
import numpy as np
import faiss
import ollama
from spl.tools import spl_tool

_EMBED_MODEL = "qwen3-embedding:0.6b"

# Module-level state: chunks are stored here by ChunkRawTexts so that
# ConstructFAISSIndex can write them to a sidecar and NearestNeighborSearch
# can look them up without receiving @texts as an argument.
_chunks: list[str] = []


def _get_embedding(text: str) -> list[float]:
    """Embed text with retry to handle ollama cold-start (model runner EOF on first load)."""
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            resp = ollama.embed(model=_EMBED_MODEL, input=text)
            return resp.embeddings[0]
        except Exception as e:
            last_err = e
            time.sleep(2)
    raise RuntimeError(f"ollama embed failed after 3 attempts: {last_err}") from last_err


@spl_tool
def ChunkRawTexts(raw_text: str) -> str:
    """Split a plain text string into 2000-char chunks. Returns JSON array of strings."""
    global _chunks
    _chunks = []
    for i in range(0, len(raw_text), 2000):
        _chunks.append(raw_text[i : i + 2000])
    return json.dumps(_chunks)


@spl_tool
def GenerateVectorEmbeddings(texts_json: str) -> str:
    """Embed text chunks via ollama qwen3-embedding:0.6b. Returns JSON array of float vectors."""
    texts = json.loads(texts_json)
    embeddings = [_get_embedding(t) for t in texts]
    return json.dumps(embeddings)


@spl_tool
def ConstructFAISSIndex(embeddings_json: str) -> str:
    """Build a FAISS IndexFlatL2. Writes .faiss file and .chunks.json sidecar. Returns index path."""
    embeddings = np.array(json.loads(embeddings_json), dtype=np.float32)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    tmp = tempfile.NamedTemporaryFile(suffix=".faiss", delete=False)
    faiss.write_index(index, tmp.name)
    tmp.close()
    # write chunks sidecar so NearestNeighborSearch can retrieve actual text
    with open(tmp.name + ".chunks.json", "w") as f:
        json.dump(_chunks, f)
    return tmp.name


@spl_tool
def LogAndPersistIndex(index_path: str) -> str:
    """Log index persistence (index already written to disk by ConstructFAISSIndex)."""
    return f"index persisted at {index_path}"


@spl_tool
def EmbedQuery(query: str) -> str:
    """Embed a query string via ollama qwen3-embedding:0.6b. Returns JSON float array."""
    return json.dumps(_get_embedding(query))


@spl_tool
def NearestNeighborSearch(index_path: str, query_embedding_json: str) -> str:
    """K=1 nearest-neighbor search. Reads chunks from {index_path}.chunks.json sidecar.
    Returns the most relevant chunk as plain text."""
    index = faiss.read_index(index_path)
    q_emb = np.array(json.loads(query_embedding_json), dtype=np.float32).reshape(1, -1)
    _, indices = index.search(q_emb, k=1)
    best_idx = int(indices[0][0])
    with open(index_path + ".chunks.json") as f:
        chunks = json.load(f)
    return chunks[best_idx]
