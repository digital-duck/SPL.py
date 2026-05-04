#!/usr/bin/env python3
"""
S3-rag-openrouter-gemini — compiled from S3-rag-openrouter-gemini.spl
Target: Python — PocketFlow (minimalist ETL-style LLM orchestration)
Adapter: openrouter / google/gemini-3-flash-preview
"""
import os
import sys
import requests

# Real tool implementations from tools.py (ChunkRawTexts, GenerateVectorEmbeddings,
# ConstructFAISSIndex, EmbedQuery, NearestNeighborSearch — ollama + FAISS)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from tools import (
    ChunkRawTexts,
    GenerateVectorEmbeddings,
    ConstructFAISSIndex,
    EmbedQuery,
    NearestNeighborSearch,
)

_MODEL = "google/gemini-3-flash-preview"


# ---------------------------------------------------------------------------
# LLM helper — adapter: openrouter
# ---------------------------------------------------------------------------

def call_llm(prompt: str) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": _MODEL, "messages": [{"role": "user", "content": prompt}]},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


# ---------------------------------------------------------------------------
# SPL: CREATE FUNCTION GenerateAnswer(context TEXT, user_query TEXT)
# ---------------------------------------------------------------------------

def generate_answer(context: str, user_query: str) -> str:
    prompt = (
        "You are a helpful assistant. Based on the provided context:\n"
        f"{context}\n\n"
        f"Please answer the following question:\n{user_query}\n\n"
        "If the answer isn't in the context, say you don't know."
    )
    return call_llm(prompt)


# ---------------------------------------------------------------------------
# SPL: WORKFLOW RagIndexingAndQuery
# ---------------------------------------------------------------------------

def run_rag_pipeline(raw_input: str, user_query: str) -> dict:
    """
    SPL: WORKFLOW RagIndexingAndQuery
           INPUT  @raw_input TEXT, @user_query TEXT
           OUTPUT @final_response TEXT
    """
    # SPL: CALL ChunkRawTexts(@raw_input) INTO @chunked_docs
    chunked_docs = ChunkRawTexts(raw_input)

    # SPL: CALL GenerateVectorEmbeddings(@chunked_docs) INTO @doc_embeddings
    doc_embeddings = GenerateVectorEmbeddings(chunked_docs)

    # SPL: CALL ConstructFAISSIndex(@doc_embeddings) INTO @vector_index
    vector_index = ConstructFAISSIndex(doc_embeddings)

    # SPL: CALL EmbedQuery(@user_query) INTO @query_embedding
    query_embedding = EmbedQuery(user_query)

    # SPL: CALL NearestNeighborSearch(@vector_index, @query_embedding) INTO @retrieved_context
    retrieved_context = NearestNeighborSearch(vector_index, query_embedding)

    # SPL: GENERATE GenerateAnswer(@retrieved_context, @user_query) INTO @final_response
    final_response = generate_answer(retrieved_context, user_query)

    # SPL: RETURN @final_response WITH status = "complete"
    return {"final_response": final_response, "status": "complete"}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _raw  = sys.argv[1] if len(sys.argv) > 1 else "PocketFlow is a minimalist LLM framework for building agentic pipelines."
    _query = sys.argv[2] if len(sys.argv) > 2 else "What is PocketFlow and how do I install it?"
    result = run_rag_pipeline(_raw, _query)
    print(f"\nStatus : {result['status']}")
    print(f"\nAnswer:\n{result['final_response']}")
