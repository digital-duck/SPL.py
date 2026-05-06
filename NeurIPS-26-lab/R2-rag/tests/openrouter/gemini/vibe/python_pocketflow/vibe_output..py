import os
import requests
import json
import numpy as np
import faiss
from typing import List, Dict, Any

# --- LLM Helper ---
def call_llm(prompt: str, model: str = None) -> str:
    """
    Helper to call the LLM using OpenRouter or similar OpenAI-compatible API.
    """
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API Key not found. Please set OPENROUTER_API_KEY or OPENAI_API_KEY.")
    
    model = model or os.getenv("LLM_MODEL", "meta-llama/llama-3-8b-instruct:free")
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content'].strip()

def get_embedding(text: str) -> List[float]:
    """
    Simulated embedding service using a simple hashing/projection for demonstration.
    In a production PocketFlow app, this would call OpenAI/HuggingFace embeddings.
    For the sake of 'executable without extra heavy deps', we use a stable projection.
    """
    # Create a deterministic pseudo-embedding of size 128
    np.random.seed(sum(ord(c) for c in text) % 1000)
    return np.random.rand(128).astype('float32').tolist()

# --- PocketFlow Node Base ---
class Node:
    def prep(self, shared: Dict[str, Any]):
        return True

    def exec(self, shared: Dict[str, Any]):
        raise NotImplementedError

    def post(self, shared: Dict[str, Any]):
        return None

# --- Offline Indexing Nodes ---

class ChunkDocumentsNode(Node):
    def exec(self, shared: Dict[str, Any]):
        raw_text = shared.get("raw_text", "")
        chunk_size = 200
        # Simple fixed-size chunking logic
        chunks = [raw_text[i:i+chunk_size] for i in range(0, len(raw_text), chunk_size)]
        shared["chunks"] = chunks
        print(f"[Offline] Created {len(chunks)} chunks.")

class EmbedDocumentsNode(Node):
    def exec(self, shared: Dict[str, Any]):
        chunks = shared.get("chunks", [])
        embeddings = [get_embedding(c) for c in chunks]
        shared["embeddings"] = np.array(embeddings).astype('float32')
        print(f"[Offline] Generated embeddings for {len(chunks)} chunks.")

class CreateIndexNode(Node):
    def exec(self, shared: Dict[str, Any]):
        embeddings = shared["embeddings"]
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        shared["index"] = index
        print(f"[Offline] FAISS index created and populated.")

# --- Online RAG Nodes ---

class EmbedQueryNode(Node):
    def exec(self, shared: Dict[str, Any]):
        query = shared.get("query", "")
        query_vec = np.array([get_embedding(query)]).astype('float32')
        shared["query_vector"] = query_vec

class RetrieveDocumentNode(Node):
    def exec(self, shared: Dict[str, Any]):
        index = shared["index"]
        query_vec = shared["query_vector"]
        chunks = shared["chunks"]
        
        # Search for top 1
        D, I = index.search(query_vec, 1)
        retrieved_idx = I[0][0]
        shared["retrieved_context"] = chunks[retrieved_idx]
        print(f"[Online] Retrieved context: {chunks[retrieved_idx][:50]}...")

class GenerateAnswerNode(Node):
    def exec(self, shared: Dict[str, Any]):
        context = shared.get("retrieved_context", "")
        question = shared.get("query", "")
        
        # CREATE FUNCTION GenerateAnswer equivalent
        prompt = f"""
        Use the following context to answer the question.
        Context: {context}
        Question: {question}
        
        Instruction: Briefly answer the question based strictly on the context provided.
        Answer:
        """
        
        response = call_llm(prompt)
        shared["final_answer"] = response

# --- Workflow Orchestrator ---

class Workflow:
    def __init__(self, nodes: List[Node]):
        self.nodes = nodes

    def run(self, shared: Dict[str, Any]):
        for node in self.nodes:
            if node.prep(shared):
                node.exec(shared)
                node.post(shared)
        return shared

def get_offline_flow():
    return Workflow([
        ChunkDocumentsNode(),
        EmbedDocumentsNode(),
        CreateIndexNode()
    ])

def get_online_flow():
    return Workflow([
        EmbedQueryNode(),
        RetrieveDocumentNode(),
        GenerateAnswerNode()
    ])

# --- Main Entry Point ---

if __name__ == "__main__":
    # Initial Shared State
    state = {
        "raw_text": (
            "PocketFlow is a minimalist ETL-style framework for LLM orchestration. "
            "It focuses on data flowing through nodes. Each node performs a specific task. "
            "FAISS is a library for efficient similarity search and clustering of dense vectors. "
            "RAG stands for Retrieval-Augmented Generation, combining search with LLMs."
        ),
        "query": "What is PocketFlow?"
    }

    print("--- Starting Offline Indexing Phase ---")
    offline_flow = get_offline_flow()
    state = offline_flow.run(state)

    print("\n--- Starting Online Query Phase ---")
    online_flow = get_online_flow()
    state = online_flow.run(state)

    print("\nFINAL RESULT:")
    print(state.get("final_answer"))