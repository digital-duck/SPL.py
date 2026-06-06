```python
test_cases = [
    {
        "query": "What is chunking and why does chunk size matter in a RAG pipeline?",
        "documents": [
            """
            Retrieval-Augmented Generation (RAG) is a hybrid NLP architecture introduced by Lewis et al.
            (2020) that couples a dense retrieval component with a seq2seq language model. During inference
            the system first retrieves a set of relevant documents from a non-parametric external store and
            then conditions the generator on both the original input and the retrieved passages. This
            combination allows the model to access a large, updateable knowledge base without retraining,
            dramatically reducing hallucinations on knowledge-intensive tasks such as open-domain question
            answering and fact verification.
            """,
            """
            Chunking strategy is one of the most impactful hyperparameters in a RAG system. Chunk size
            controls the granularity of retrieval: smaller chunks (128-256 tokens) yield higher precision
            but may lose surrounding context; larger chunks (512-1024 tokens) preserve more context but
            reduce retrieval focus. Overlapping windows (e.g. 50-token overlap) help prevent information
            loss at chunk boundaries. Advanced strategies include sentence-aware splitting and semantic
            chunking where the document is split wherever embedding similarity drops sharply.
            """,
        ],
        "top_k": 2,
        "chunk_size": 300,
    },
    {
        "query": "How do vector databases support approximate nearest-neighbour search?",
        "documents": [
            """
            Vector databases are specialized storage engines designed to index and search high-dimensional
            embeddings at scale. Examples include Pinecone, Weaviate, Milvus, and FAISS. They support
            approximate nearest-neighbour (ANN) search algorithms such as HNSW (Hierarchical Navigable
            Small World) and IVF (Inverted File Index) that trade a small amount of recall for sub-linear
            query latency. In a RAG pipeline the vector database stores embedded document chunks; at query
            time the query embedding is compared against all stored vectors and the top-k most similar
            chunks are returned as context for the language model.
            """,
            """
            HNSW (Hierarchical Navigable Small World) is a graph-based ANN algorithm. It builds a
            multi-layer proximity graph where upper layers contain long-range shortcuts and lower layers
            contain dense local connections. Queries start at the top layer and greedily descend,
            exploiting shortcuts for fast traversal. HNSW achieves excellent recall-speed trade-offs
            and is the default algorithm in most production vector databases including Pinecone, Weaviate,
            and pgvector.
            """,
        ],
        "top_k": 3,
        "chunk_size": 400,
    },
    {
        "query": "What metrics are used to evaluate RAG system quality?",
        "documents": [
            """
            Evaluation of RAG systems typically measures two dimensions: retrieval quality
            (recall@k, MRR, NDCG) and generation quality (faithfulness, answer relevance,
            context precision). Benchmarks such as BEIR, NaturalQuestions, TriviaQA, and
            HotpotQA are widely used. Frameworks like RAGAS and TruLens provide automated
            LLM-based metrics that score whether the generated answer is grounded in the
            retrieved context (groundedness) and whether the retrieved context actually
            answers the question (context relevance).
            """,
            """
            Faithfulness is a critical RAG metric: it measures whether every claim in the
            generated answer is supported by the retrieved passages. A high-faithfulness
            score indicates the model is not hallucinating facts outside the provided context.
            Answer relevance measures how well the answer addresses the original question,
            independent of groundedness. Context precision measures the signal-to-noise ratio
            of the retrieved passages — are all retrieved chunks useful, or do some add noise?
            """,
        ],
        "top_k": 3,
        "chunk_size": 350,
    },
]

# Example usage:
# from solution import run_rag
# for tc in test_cases:
#     result = run_rag(tc["documents"], tc["query"], top_k=tc["top_k"], chunk_size=tc["chunk_size"])
#     print(result["answer"])
```