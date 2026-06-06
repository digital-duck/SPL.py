import os
import json
import numpy as np
import requests
import faiss
from pathlib import Path

# --- Configuration & Environment ---
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY", "")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

if not API_KEY:
    raise EnvironmentError("Missing API key. Set OPENAI_API_KEY or OPENROUTER_API_KEY.")

# --- LLM & Embedding Helpers ---
def call_llm(prompt: str, model: str = None) -> str:
    """Invokes the LLM for answer generation."""
    model = model or LLM_MODEL
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    res = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload)
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"].strip()

def get_embedding(text: str) -> list:
    """Generates a vector embedding for a given text."""
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": EMBEDDING_MODEL, "input": text}
    res = requests.post(f"{BASE_URL}/embeddings", headers=headers, json=payload)
    res.raise_for_status()
    return res.json()["data"][0]["embedding"]

# --- PocketFlow Minimalist Orchestration Core ---
class Node:
    """Atomic ETL/LLM operation that reads/writes shared state."""
    def __init__(self, name, action):
        self.name = name
        self.action = action
    def __call__(self, state):
        return self.action(state)

class Flow:
    """Sequential workflow orchestrator passing shared state between nodes."""
    def __init__(self, name, nodes):
        self.name = name
        self.nodes = nodes
    def run(self, state):
        print(f"\n>>> Starting Phase: {self.name}")
        for node in self.nodes:
            print(f"  [EXEC] {node.name}")
            state = node(state)
        print(f">>> Completed Phase: {self.name}\n")
        return state

# --- Workflow Nodes (Offline Phase) ---
def chunk_documents(state):
    """Splits raw @texts into smaller @chunks for indexing."""
    raw_texts = state.get("@texts", [])
    chunks = []
    chunk_size = 150
    for text in raw_texts:
        words = text.split()
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i + chunk_size]))
    state["@chunks"] = chunks
    state["@chunk_count"] = len(chunks)
    return state

def embed_documents(state):
    """Generates @embeddings for each @chunk."""
    chunks = state["@chunks"]
    print(f"    Embedding {len(chunks)} chunks via API...")
    state["@embeddings"] = np.array([get_embedding(c) for c in chunks], dtype=np.float32)
    return state

def build_faiss_index(state):
    """Constructs a FAISS @index from @embeddings."""
    embeddings = state["@embeddings"]
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    state["@index"] = index
    return state

def persist_index(state):
    """Persists the @index to disk for future reuse."""
    faiss.write_index(state["@index"], "vector_store.idx")
    print("    FAISS index saved to vector_store.idx")
    return state

# --- Workflow Nodes (Online Phase) ---
def embed_query(state):
    """Embeds the @query into @query_embedding."""
    query = state["@query"]
    state["@query_embedding"] = np.array([get_embedding(query)], dtype=np.float32)
    return state

def retrieve_document(state):
    """Performs nearest-neighbor search to populate @retrieved_document."""
    index = state["@index"]
    query_emb = state["@query_embedding"]
    chunks = state["@chunks"]
    # k=1: retrieve single most relevant document
    _, indices = index.search(query_emb, 1)
    best_idx = indices[0][0]
    state["@retrieved_document"] = chunks[best_idx]
    return state

def generate_answer(state):
    """Formats prompt and calls LLM to produce @generated_answer."""
    query = state["@query"]
    context = state["@retrieved_document"]
    prompt = f"Question: {query}\n\nContext: {context}\n\nAnswer:"
    state["@generated_answer"] = call_llm(prompt)
    return state

def save_and_log(state):
    """Persists Q&A to markdown and logs to console."""
    query = state["@query"]
    answer = state["@generated_answer"]
    md_content = f"# Q&A Result\n\n**Question:** {query}\n\n**Answer:**\n{answer}\n"
    Path("output_qa.md").write_text(md_content)
    print("\n[CONSOLE LOG] Q&A pair persisted to output_qa.md")
    print(f"Query: {query}")
    print(f"Answer: {answer}")
    return state

# --- Main Entry Point ---
def main():
    # Initialize shared pipeline memory
    shared_state = {
        "@texts": [
            "Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation.",
            "Faiss is a library for efficient similarity search and clustering of dense vectors. It contains algorithms that search in sets of vectors of any size, even those that do not fit in RAM.",
            "PocketFlow provides a minimalist, ETL-style orchestration pattern for LLM workflows. It relies on explicit node wiring and shared state dictionaries to manage data flow between offline indexing and online query phases."
        ],
        "@query": "What is the primary purpose of the Faiss library?"
    }

    # Offline Indexing Phase
    offline_flow = Flow("Offline Indexing", [
        Node("ChunkDocuments", chunk_documents),
        Node("EmbedDocuments", embed_documents),
        Node("BuildIndex", build_faiss_index),
        Node("PersistIndex", persist_index)
    ])

    # Online Query Phase
    online_flow = Flow("Online Query", [
        Node("EmbedQuery", embed_query),
        Node("RetrieveDocument", retrieve_document),
        Node("GenerateAnswer", generate_answer),
        Node("SaveAndLog", save_and_log)
    ])

    # Execute linear pipeline with shared state handoff
    shared_state = offline_flow.run(shared_state)
    shared_state = online_flow.run(shared_state)

    return shared_state

if __name__ == "__main__":
    main()