import os
import json
import math
import urllib.request
from typing import Any, Dict, List, Tuple

# =============================================================================
# SPL to Python — PocketFlow Translation
# Recipe: S3-rag-openrouter-qwen
# =============================================================================

# SPL: CREATE FUNCTION FormatPrompt(doc, query)
# SPL: RETURNS TEXT AS $$ 
# SPL: Context: {doc}. Question: {query}. Provide a concise and accurate answer. 
# SPL: $$;
def FormatPrompt(doc: str, query: str) -> str:
    """Constructs the RAG prompt template."""
    return f"Context: {doc}. Question: {query}. Provide a concise and accurate answer. "


class S3RagOpenrouterQwenPipeline:
    # SPL: WORKFLOW RAGPipeline
    # SPL:   INPUT @raw_input STRING, @user_query STRING := "default query"
    # SPL:   OUTPUT @result STRING
    def __init__(self, raw_input: str, user_query: str = "default query"):
        self.raw_input: str = raw_input
        self.user_query: str = user_query
        self.result: str = ""

    # SPL: DO
    def run(self) -> Tuple[str, Dict[str, str]]:
        # SPL: @texts := @raw_input;
        texts = self.raw_input

        # SPL: CALL ChunkRawTexts(@texts) INTO @texts;
        texts = self._call_chunk_raw_texts(texts)

        # SPL: CALL GenerateVectorEmbeddings(@texts) INTO @embeddings;
        embeddings = self._call_generate_vector_embeddings(texts)

        # SPL: CALL ConstructFAISSIndex(@embeddings) INTO @index;
        index = self._call_construct_faiss_index(embeddings, texts)

        # SPL: CALL LogAndPersistIndex(@index) INTO @persist_status;
        persist_status = self._call_log_and_persist_index(index)

        # SPL: @query := @user_query;
        query = self.user_query

        # SPL: CALL EmbedQuery(@query) INTO @query_embedding;
        query_embedding = self._call_embed_query(query)

        # SPL: CALL NearestNeighborSearch(@index, @query_embedding) INTO @retrieved_doc;
        retrieved_doc = self._call_nearest_neighbor_search(index, query_embedding)

        # SPL: GENERATE FormatPrompt(@retrieved_doc, @query) INTO @result;
        prompt = FormatPrompt(retrieved_doc, query)
        self.result = self._generate_with_openrouter(prompt)

        # SPL: CALL write_file("output.md", @result);
        self._call_write_file("output.md", self.result)

        # SPL: RETURN @result WITH status = "complete";
        return self.result, {"status": "complete"}

    # -------------------------------------------------------------------------
    # ETL Node Implementations (PocketFlow-style pure functions)
    # -------------------------------------------------------------------------

    # SPL: CALL ChunkRawTexts(@texts) INTO @texts;
    def _call_chunk_raw_texts(self, texts: str) -> List[str]:
        """Splits raw text into semantic chunks."""
        return [chunk.strip() for chunk in texts.replace('\n', '. ').split('. ') if chunk.strip()]

    # SPL: CALL GenerateVectorEmbeddings(@texts) INTO @embeddings;
    def _call_generate_vector_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """Generates mock embeddings. Replace with actual embedding API in prod."""
        dim = 64
        return [[float(hash(chunk + str(i)) % 1000) / 1000.0 for i in range(dim)] for chunk in chunks]

    # SPL: CALL ConstructFAISSIndex(@embeddings) INTO @index;
    def _call_construct_faiss_index(self, embeddings: List[List[float]], chunks: List[str]) -> Dict[str, Any]:
        """Constructs a lightweight vector index with chunk mapping."""
        return {"vectors": embeddings, "chunks": chunks, "size": len(embeddings)}

    # SPL: CALL LogAndPersistIndex(@index) INTO @persist_status;
    def _call_log_and_persist_index(self, index: Dict[str, Any]) -> str:
        """Logs index stats and simulates persistence."""
        print(f"[LOG] Index constructed: {index['size']} vectors. Persisting to disk...")
        return "persisted"

    # SPL: CALL EmbedQuery(@query) INTO @query_embedding;
    def _call_embed_query(self, query: str) -> List[float]:
        """Embeds user query. Matches dimensionality of doc embeddings."""
        dim = 64
        return [float(hash(query + str(i)) % 1000) / 1000.0 for i in range(dim)]

    # SPL: CALL NearestNeighborSearch(@index, @query_embedding) INTO @retrieved_doc;
    def _call_nearest_neighbor_search(self, index: Dict[str, Any], query_emb: List[float]) -> str:
        """Finds the top-1 nearest chunk via cosine similarity."""
        if not index["vectors"]:
            return "No context available."
        
        best_idx = 0
        best_sim = -1.0
        
        for i, vec in enumerate(index["vectors"]):
            dot = sum(a * b for a, b in zip(vec, query_emb))
            mag_q = math.sqrt(sum(a**2 for a in query_emb)) or 1.0
            mag_v = math.sqrt(sum(a**2 for a in vec)) or 1.0
            sim = dot / (mag_q * mag_v)
            if sim > best_sim:
                best_sim = sim
                best_idx = i
                
        return index["chunks"][best_idx]

    # SPL: GENERATE FormatPrompt(@retrieved_doc, @query) INTO @result;
    def _generate_with_openrouter(self, prompt: str) -> str:
        """Calls OpenRouter Qwen model for generation."""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print("[WARN] OPENROUTER_API_KEY not set. Returning mock response.")
            return f"[Mock Response] Based on: {prompt}"

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/splc-compiler",
            "X-Title": "S3-RAG-OpenRouter-Qwen"
        }
        model = os.environ.get("LLM_MODEL", "qwen/qwen3.6-plus")
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())["choices"][0]["message"]["content"]

    # SPL: CALL write_file("output.md", @result);
    def _call_write_file(self, filename: str, content: str) -> None:
        """Writes the final output to a markdown file."""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[LOG] Output written to {filename}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-input", required=True, help="Raw document text to index")
    parser.add_argument("--query", required=True, help="User query")
    args = parser.parse_args()

    pipeline = S3RagOpenrouterQwenPipeline(
        raw_input=args.raw_input,
        user_query=args.query,
    )
    result, status = pipeline.run()
    print(result)