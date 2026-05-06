I need to implement a RAG (Retrieval-Augmented Generation) system using PocketFlow with OpenRouter/Claude. Let me create a complete implementation.

```python
#!/usr/bin/env python3
"""
RAG Pipeline using PocketFlow + OpenRouter/Claude
Retrieval-Augmented Generation with document ingestion, chunking, embedding, and Q&A
"""

import os
import re
import json
import math
import hashlib
import logging
from typing import Any, Optional
from openai import OpenAI

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── LLM Configuration ─────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENAI_API_KEY     = os.environ.get("OPENAI_API_KEY", "")
LLM_MODEL          = os.environ.get("LLM_MODEL", "anthropic/claude-3.5-sonnet")
EMBED_MODEL        = os.environ.get("EMBED_MODEL", "text-embedding-3-small")

# ── OpenRouter client for chat/LLM ────────────────────────────────────────────
def _get_llm_client() -> OpenAI:
    if OPENROUTER_API_KEY:
        return OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )
    if OPENAI_API_KEY:
        return OpenAI(api_key=OPENAI_API_KEY)
    raise EnvironmentError("Set OPENROUTER_API_KEY or OPENAI_API_KEY.")


def call_llm(prompt: str, model: str = None, system: str = None) -> str:
    """Call LLM via OpenRouter (or OpenAI fallback) and return text."""
    model = model or LLM_MODEL
    client = _get_llm_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    logger.debug("call_llm model=%s prompt_len=%d", model, len(prompt))
    resp = client.chat.completions.create(model=model, messages=messages, temperature=0.2)
    return resp.choices[0].message.content.strip()


def call_embedding(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using OpenAI embedding API."""
    if not OPENAI_API_KEY:
        raise EnvironmentError("OPENAI_API_KEY is required for embeddings.")
    client = OpenAI(api_key=OPENAI_API_KEY)
    logger.debug("call_embedding texts=%d model=%s", len(texts), EMBED_MODEL)
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [item.embedding for item in resp.data]


# ── Cosine similarity ─────────────────────────────────────────────────────────
def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot   = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ── PocketFlow minimal base ───────────────────────────────────────────────────
class Node:
    """Base PocketFlow node."""
    def __init__(self, max_retries: int = 1):
        self.max_retries = max_retries
        self._successors: dict[str, "Node"] = {}

    def add_successor(self, node: "Node", action: str = "default") -> "Node":
        self._successors[action] = node
        return node

    def prep(self, shared: dict) -> Any:
        return None

    def exec(self, prep_result: Any) -> Any:
        return None

    def post(self, shared: dict, prep_result: Any, exec_result: Any) -> str:
        return "default"

    def run(self, shared: dict) -> str:
        prep_result = self.prep(shared)
        last_exc = None
        for attempt in range(self.max_retries):
            try:
                exec_result = self.exec(prep_result)
                break
            except Exception as exc:
                last_exc = exc
                logger.warning("Node %s attempt %d failed: %s", self.__class__.__name__, attempt + 1, exc)
        else:
            raise RuntimeError(f"Node {self.__class__.__name__} failed after {self.max_retries} retries") from last_exc
        return self.post(shared, prep_result, exec_result)


class Flow:
    """PocketFlow orchestrator."""
    def __init__(self, start: Node):
        self.start = start

    def run(self, shared: dict) -> dict:
        node = self.start
        while node is not None:
            action = node.run(shared)
            node = node._successors.get(action) or node._successors.get("default")
        return shared


class BatchNode(Node):
    """Node that processes a list of items."""
    def exec(self, prep_result: Any) -> Any:
        return [self.exec_item(item) for item in (prep_result or [])]

    def exec_item(self, item: Any) -> Any:
        raise NotImplementedError


# ── Shared state keys ─────────────────────────────────────────────────────────
# shared["documents"]   -> list of raw document strings
# shared["chunks"]      -> list of {"id", "text", "doc_idx", "chunk_idx"}
# shared["embeddings"]  -> list of float vectors (parallel to chunks)
# shared["query"]       -> str
# shared["query_embedding"] -> list[float]
# shared["retrieved"]   -> list of {"chunk", "score"}
# shared["answer"]      -> str
# shared["history"]     -> list of {"question", "answer"}


# ── Node 1 : Ingest Documents ─────────────────────────────────────────────────
class IngestDocumentsNode(Node):
    """Load raw documents into shared state."""

    def prep(self, shared: dict) -> list[str]:
        docs = shared.get("documents", [])
        logger.info("IngestDocuments: %d document(s) received.", len(docs))
        return docs

    def exec(self, prep_result: list[str]) -> list[str]:
        # Basic validation / cleaning
        cleaned = []
        for doc in prep_result:
            doc = doc.strip()
            if doc:
                cleaned.append(doc)
        return cleaned

    def post(self, shared: dict, prep_result, exec_result: list[str]) -> str:
        shared["documents"] = exec_result
        if not exec_result:
            logger.warning("No documents to process.")
            return "no_docs"
        return "default"


# ── Node 2 : Chunk Documents ──────────────────────────────────────────────────
class ChunkDocumentsNode(BatchNode):
    """Split documents into overlapping chunks."""

    CHUNK_SIZE    = int(os.environ.get("CHUNK_SIZE",    "500"))   # chars
    CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "100"))   # chars

    def prep(self, shared: dict) -> list[dict]:
        return [{"doc_idx": i, "text": doc}
                for i, doc in enumerate(shared["documents"])]

    def exec_item(self, item: dict) -> list[dict]:
        text      = item["text"]
        doc_idx   = item["doc_idx"]
        size      = self.CHUNK_SIZE
        overlap   = self.CHUNK_OVERLAP
        chunks    = []
        start     = 0
        chunk_idx = 0
        while start < len(text):
            end   = min(start + size, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                uid = hashlib.md5(f"{doc_idx}-{chunk_idx}-{chunk_text[:50]}".encode()).hexdigest()[:8]
                chunks.append({
                    "id":        uid,
                    "text":      chunk_text,
                    "doc_idx":   doc_idx,
                    "chunk_idx": chunk_idx,
                })
                chunk_idx += 1
            start += size - overlap
        return chunks

    def exec(self, prep_result: list[dict]) -> list[dict]:
        all_chunks = []
        for item in prep_result:
            all_chunks.extend(self.exec_item(item))
        return all_chunks

    def post(self, shared: dict, prep_result, exec_result: list[dict]) -> str:
        shared["chunks"] = exec_result
        logger.info("ChunkDocuments: %d chunk(s) created.", len(exec_result))
        return "default"


# ── Node 3 : Embed Chunks ─────────────────────────────────────────────────────
class EmbedChunksNode(Node):
    """Embed all chunks in batches."""

    BATCH_SIZE = int(os.environ.get("EMBED_BATCH_SIZE", "100"))

    def prep(self, shared: dict) -> list[str]:
        return [c["text"] for c in shared["chunks"]]

    def exec(self, prep_result: list[str]) -> list[list[float]]:
        texts  = prep_result
        size   = self.BATCH_SIZE
        embeds = []
        for i in range(0, len(texts), size):
            batch = texts[i:i + size]
            logger.info("EmbedChunks: embedding batch %d/%d …",
                        i // size + 1, math.ceil(len(texts) / size))
            embeds.extend(call_embedding(batch))
        return embeds

    def post(self, shared: dict, prep_result, exec_result: list[list[float]]) -> str:
        shared["embeddings"] = exec_result
        logger.info("EmbedChunks: %d embedding(s) stored.", len(exec_result))
        return "default"


# ── Node 4 : Embed Query ──────────────────────────────────────────────────────
class EmbedQueryNode(Node):
    """Embed the user query."""

    def prep(self, shared: dict) -> str:
        return shared["query"]

    def exec(self, prep_result: str) -> list[float]:
        logger.info("EmbedQuery: embedding query …")
        return call_embedding([prep_result])[0]

    def post(self, shared: dict, prep_result, exec_result: list[float]) -> str:
        shared["query_embedding"] = exec_result
        return "default"


# ── Node 5 : Retrieve Chunks ──────────────────────────────────────────────────
class RetrieveChunksNode(Node):
    """Cosine-similarity retrieval over embedded chunks."""

    TOP_K = int(os.environ.get("RETRIEVE_TOP_K", "5"))

    def prep(self, shared: dict) -> dict:
        return {
            "query_embedding": shared["query_embedding"],
            "chunks":          shared["chunks"],
            "embeddings":      shared["embeddings"],
        }

    def exec(self, prep_result: dict) -> list[dict]:
        q_emb   = prep_result["query_embedding"]
        chunks  = prep_result["chunks"]
        embeds  = prep_result["embeddings"]
        scored  = []
        for chunk, emb in zip(chunks, embeds):
            score = cosine_similarity(q_emb, emb)
            scored.append({"chunk": chunk, "score": score})
        scored.sort(key=lambda x: x["score"], reverse=True)
        top = scored[:self.TOP_K]
        logger.info("RetrieveChunks: top-%d scores: %s",
                    self.TOP_K, [round(r["score"], 4) for r in top])
        return top

    def post(self, shared: dict, prep_result, exec_result: list[dict]) -> str:
        shared["retrieved"] = exec_result
        return "default"


# ── Node 6 : Generate Answer ──────────────────────────────────────────────────
class GenerateAnswerNode(Node):
    """Generate answer from retrieved context using LLM."""

    def prep(self, shared: dict) -> dict:
        context_parts = []
        for i, r in enumerate(shared["retrieved"], 1):
            context_parts.append(f"[{i}] {r['chunk']['text']}")
        context = "\n\n".join(context_parts)

        history = shared.get("history", [])
        history_text = ""
        if history:
            lines = []
            for turn in history[-4:]:   # last 4 turns
                lines.append(f"Q: {turn['question']}\nA: {turn['answer']}")
            history_text = "\n\n".join(lines)

        return {
            "query":        shared["query"],
            "context":      context,
            "history_text": history_text,
        }

    def exec(self, prep_result: dict) -> str:
        query        = prep_result["query"]
        context      = prep_result["context"]
        history_text = prep_result["history_text"]

        history_section = ""
        if history_text:
            history_section = f"\n\nConversation history:\n{history_text}\n"

        system = (
            "You are a knowledgeable assistant that answers questions based strictly "
            "on the provided context. If the context does not contain enough information "
            "to answer the question, say so clearly. Be concise and accurate."
        )
        prompt = (
            f"Context:\n{context}"
            f"{history_section}\n\n"
            f"Question: {query}\n\n"
            "Answer based on the context above:"
        )
        logger.info("GenerateAnswer: calling LLM …")
        return call_llm(prompt, system=system)

    def post(self, shared: dict, prep_result, exec_result: str) -> str:
        shared["answer"] = exec_result
        # Update conversation history
        history = shared.setdefault("history", [])
        history.append({"question": shared["query"], "answer": exec_result})
        logger.info("GenerateAnswer: answer produced (%d chars).", len(exec_result))
        return "default"


# ── Node 7 : Output / Display ─────────────────────────────────────────────────
class OutputNode(Node):
    """Print the final answer and retrieved sources."""

    def prep(self, shared: dict) -> dict:
        return {
            "query":     shared["query"],
            "answer":    shared["answer"],
            "retrieved": shared["retrieved"],
        }

    def exec(self, prep_result: dict) -> None:
        print("\n" + "═" * 70)
        print(f"❓ Question : {prep_result['query']}")
        print("─" * 70)
        print(f"💡 Answer   :\n{prep_result['answer']}")
        print("─" * 70)
        print("📚 Sources  :")
        for i, r in enumerate(prep_result["retrieved"], 1):
            c = r["chunk"]
            snippet = c["text"][:120].replace("\n", " ")
            print(f"  [{i}] score={r['score']:.4f} doc={c['doc_idx']} "
                  f"chunk={c['chunk_