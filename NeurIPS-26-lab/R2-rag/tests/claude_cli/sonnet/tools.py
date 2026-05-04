"""RAG tools for S3-rag-claude_cli-sonnet.spl.

Provides CALL-able implementations of the five RAG primitives:
  chunk_documents, embed_documents, create_faiss_index, embed_query, retrieve_document

Embeddings use ollama qwen3-embedding:0.6b (local, no API key needed).
Index state is serialized to a temp file so SPL can pass it as a string variable.
"""

from __future__ import annotations
import json
import tempfile
import numpy as np
import faiss
import ollama
from spl.tools import spl_tool

_EMBED_MODEL = "qwen3-embedding:0.6b"


def _get_embedding(text: str) -> list[float]:
    resp = ollama.embed(model=_EMBED_MODEL, input=text)
    return resp.embeddings[0]


@spl_tool
def chunk_documents(documents_json: str) -> str:
    """Split documents into 2000-char chunks. Input/output: JSON array of strings."""
    docs = json.loads(documents_json)
    chunks: list[str] = []
    for doc in docs:
        for i in range(0, len(doc), 2000):
            chunks.append(doc[i : i + 2000])
    return json.dumps(chunks)


@spl_tool
def embed_documents(texts_json: str) -> str:
    """Embed text chunks via ollama qwen3-embedding:0.6b. Returns JSON array of float vectors."""
    texts = json.loads(texts_json)
    embeddings = [_get_embedding(t) for t in texts]
    return json.dumps(embeddings)


@spl_tool
def create_faiss_index(embeddings_json: str) -> str:
    """Build a FAISS IndexFlatL2 from embeddings. Returns path to serialized index file."""
    embeddings = np.array(json.loads(embeddings_json), dtype=np.float32)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    tmp = tempfile.NamedTemporaryFile(suffix=".faiss", delete=False)
    faiss.write_index(index, tmp.name)
    tmp.close()
    return tmp.name


@spl_tool
def embed_query(query: str) -> str:
    """Embed a query string via ollama qwen3-embedding:0.6b. Returns JSON float array."""
    return json.dumps(_get_embedding(query))


@spl_tool
def retrieve_document(index_path: str, query_embedding_json: str, texts_json: str) -> str:
    """K=1 nearest-neighbor search. Returns the most relevant chunk as plain text."""
    index = faiss.read_index(index_path)
    q_emb = np.array(json.loads(query_embedding_json), dtype=np.float32).reshape(1, -1)
    texts = json.loads(texts_json)
    _, indices = index.search(q_emb, k=1)
    best_idx = int(indices[0][0])
    return texts[best_idx]
