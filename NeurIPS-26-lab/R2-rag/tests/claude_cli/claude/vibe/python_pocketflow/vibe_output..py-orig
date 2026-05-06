The spec file doesn't exist yet — this is a new generation for the R2-RAG recipe. Based on the NeurIPS-26-lab structure and the `claude_cli/claude` adapter context, I'll generate the complete PocketFlow RAG implementation now.

```python
import os
import re
import logging
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import anthropic
from pocketflow import Node, Flow

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------

def call_llm(prompt: str, model: str = None) -> str:
    """Single-call LLM helper using the Anthropic Python SDK."""
    model = model or os.getenv("LLM_MODEL", "claude-opus-4-7")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY is not set")
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping fixed-size chunks, preferring sentence breaks."""
    text = text.strip()
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        segment = text[start:end]
        # Try to break at the last sentence boundary inside the window
        if end < len(text):
            last_stop = max(segment.rfind(". "), segment.rfind(".\n"))
            if last_stop > chunk_size // 2:
                segment = segment[: last_stop + 1]
                end = start + last_stop + 1
        segment = segment.strip()
        if segment:
            chunks.append(segment)
        start = end - overlap
    return chunks


# ---------------------------------------------------------------------------
# PocketFlow nodes
# ---------------------------------------------------------------------------

class DocumentIngestor(Node):
    """Chunk all input documents and store them in shared["chunks"]."""

    def prep(self, shared: dict) -> dict:
        return {
            "documents": shared.get("documents", []),
            "chunk_size": shared.get("chunk_size", 500),
            "overlap": shared.get("overlap", 80),
        }

    def exec(self, prep_res: dict) -> list[str]:
        docs = prep_res["documents"]
        chunk_size = prep_res["chunk_size"]
        overlap = prep_res["overlap"]
        all_chunks: list[str] = []
        for i, doc in enumerate(docs):
            chunks = _chunk_text(doc, chunk_size, overlap)
            logger.info("Doc %d/%d → %d chunks", i + 1, len(docs), len(chunks))
            all_chunks.extend(chunks)
        logger.info("Total chunks after ingestion: %d", len(all_chunks))
        return all_chunks

    def post(self, shared: dict, prep_res: dict, exec_res: list[str]) -> str:
        if not exec_res:
            logger.error("No chunks produced — cannot proceed")
            return "error"
        shared["chunks"] = exec_res
        return "default"


class IndexBuilder(Node):
    """Build a TF-IDF vector index over the document chunks."""

    def prep(self, shared: dict) -> list[str]:
        return shared["chunks"]

    def exec(self, chunks: list[str]) -> dict:
        logger.info("Building TF-IDF index over %d chunks …", len(chunks))
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=20_000,
            sublinear_tf=True,
            strip_accents="unicode",
        )
        matrix = vectorizer.fit_transform(chunks)
        logger.info("Index shape: %s", matrix.shape)
        return {"vectorizer": vectorizer, "matrix": matrix}

    def post(self, shared: dict, prep_res: list[str], exec_res: dict) -> str:
        shared["vectorizer"] = exec_res["vectorizer"]
        shared["tfidf_matrix"] = exec_res["matrix"]
        return "default"


class QueryRetriever(Node):
    """Retrieve the top-k most relevant chunks for the user query."""

    def prep(self, shared: dict) -> dict:
        return {
            "query": shared["query"],
            "chunks": shared["chunks"],
            "vectorizer": shared["vectorizer"],
            "tfidf_matrix": shared["tfidf_matrix"],
            "top_k": shared.get("top_k", 4),
        }

    def exec(self, prep_res: dict) -> list[str]:
        query = prep_res["query"]
        top_k = prep_res["top_k"]
        logger.info("Retrieving top-%d chunks for query: %r", top_k, query)

        q_vec = prep_res["vectorizer"].transform([query])
        scores = cosine_similarity(q_vec, prep_res["tfidf_matrix"]).flatten()
        top_indices = scores.argsort()[::-1][:top_k]

        retrieved: list[str] = []
        for rank, idx in enumerate(top_indices, 1):
            score = scores[idx]
            if score > 0.0:
                logger.info("  [%d] chunk #%d  score=%.4f", rank, idx, score)
                retrieved.append(prep_res["chunks"][idx])

        if not retrieved:
            logger.warning("No relevant chunks found — returning all chunks as fallback")
            retrieved = prep_res["chunks"][:top_k]

        return retrieved

    def post(self, shared: dict, prep_res: dict, exec_res: list[str]) -> str:
        shared["retrieved_chunks"] = exec_res
        shared["context"] = "\n\n---\n\n".join(
            f"[Passage {i+1}]\n{chunk}" for i, chunk in enumerate(exec_res)
        )
        return "default"


class AnswerSynthesizer(Node):
    """Generate a grounded answer from the retrieved context via LLM."""

    def prep(self, shared: dict) -> dict:
        return {
            "query": shared["query"],
            "context": shared["context"],
        }

    def exec(self, prep_res: dict) -> str:
        prompt = (
            "You are a precise and helpful assistant. "
            "Answer the question using ONLY the information in the passages below. "
            "If the passages do not contain enough information, say so explicitly.\n\n"
            f"{prep_res['context']}\n\n"
            f"Question: {prep_res['query']}\n\n"
            "Answer:"
        )
        logger.info("Calling LLM to synthesize final answer …")
        return call_llm(prompt)

    def post(self, shared: dict, prep_res: dict, exec_res: str) -> str:
        shared["answer"] = exec_res
        logger.info("Answer generated (%d chars)", len(exec_res))
        return "default"


# ---------------------------------------------------------------------------
# Flow factory
# ---------------------------------------------------------------------------

def build_rag_flow() -> Flow:
    ingestor = DocumentIngestor()
    indexer = IndexBuilder()
    retriever = QueryRetriever()
    synthesizer = AnswerSynthesizer()

    ingestor >> indexer >> retriever >> synthesizer

    return Flow(start=ingestor)


def run_rag(
    documents: list[str],
    query: str,
    top_k: int = 4,
    chunk_size: int = 500,
    overlap: int = 80,
) -> dict[str, Any]:
    """High-level entry point: returns the full shared state after the run."""
    shared: dict[str, Any] = {
        "documents": documents,
        "query": query,
        "top_k": top_k,
        "chunk_size": chunk_size,
        "overlap": overlap,
    }
    flow = build_rag_flow()
    flow.run(shared)
    return shared


# ---------------------------------------------------------------------------
# __main__ demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    SAMPLE_DOCS = [
        """
        Retrieval-Augmented Generation (RAG) is a hybrid NLP architecture introduced by Lewis et al.
        (2020) that couples a dense retrieval component with a seq2seq language model. During inference
        the system first retrieves a set of relevant documents from a non-parametric external store and
        then conditions the generator on both the original input and the retrieved passages. This
        combination allows the model to access a large, updateable knowledge base without retraining,
        dramatically reducing hallucinations on knowledge-intensive tasks such as open-domain question
        answering and fact verification. The retriever is typically implemented as a bi-encoder (DPR,
        Contriever, or a BM25 baseline), while the generator can be any autoregressive model such as
        BART, T5, or a GPT-family model.
        """,
        """
        Vector databases are specialized storage engines designed to index and search high-dimensional
        embeddings at scale. Examples include Pinecone, Weaviate, Milvus, and FAISS (Facebook AI
        Similarity Search). They support approximate nearest-neighbour (ANN) search algorithms such as
        HNSW (Hierarchical Navigable Small World) and IVF (Inverted File Index) that trade a small
        amount of recall for sub-linear query latency. In a RAG pipeline the vector database plays the
        role of the retriever's backing store: document chunks are embedded offline and inserted into the
        index; at query time the query embedding is compared against all stored vectors and the top-k
        most similar chunks are returned as context for the language model.
        """,
        """
        Chunking strategy is one of the most impactful hyperparameters in a RAG system. Chunk size
        controls the granularity of retrieval: smaller chunks (128–256 tokens) yield higher precision
        but may lose surrounding context; larger chunks (512–1024 tokens) preserve more context but
        reduce retrieval focus. Overlapping windows (e.g. 50-token overlap) help prevent information
        loss at chunk boundaries. Advanced strategies include sentence-aware splitting, semantic
        chunking (splitting where embedding similarity drops), and hierarchical indexing where both
        a summary and its source paragraphs are indexed independently. The right strategy depends on
        the document type, query distribution, and downstream task.
        """,
        """
        Evaluation of RAG systems typically measures two dimensions independently: retrieval quality
        (recall@k, MRR, NDCG) and generation quality (faithfulness, answer relevance, context
        precision). Benchmarks such as BEIR, NaturalQuestions, TriviaQA, and HotpotQA are widely
        used. Frameworks like RAGAS and TruLens provide automated LLM-based metrics that score
        whether the generated answer is grounded in the retrieved context (groundedness) and whether
        the retrieved context actually answers the question (context relevance). End-to-end accuracy
        on closed-book vs. open-book settings quantifies how much the retriever contributes beyond
        the model's parametric knowledge.
        """,
    ]

    QUERY = "What is chunking and why does chunk size matter in a RAG pipeline?"

    print("=" * 70)
    print(f"Query: {QUERY}")
    print("=" * 70)

    result = run_rag(SAMPLE_DOCS, QUERY, top_k=3, chunk_size=400, overlap=60)

    print("\n--- Retrieved Passages ---")
    for i, chunk in enumerate(result.get("retrieved_chunks", []), 1):
        print(f"\n[{i}] {chunk[:200]} …")

    print("\n--- Answer ---")
    print(result.get("answer", "No answer produced."))