# PocketFlow RAG Implementation

This project implements a minimalist Retrieval-Augmented Generation (RAG) workflow using a PocketFlow-style ETL orchestration. It separates the logic into an **Offline Indexing Phase** (preparing data) and an **Online Query Phase** (answering questions).

## Requirements
- Python 3.8+
- `requests` (for LLM API calls)
- `numpy` (for vector math)
- `faiss-cpu` (for vector similarity search)

```bash
pip install requests numpy faiss-cpu
```

## Setup
Set your API key as an environment variable:
```bash
export OPENROUTER_API_KEY='your_key_here'
# Optional: export LLM_MODEL='your_preferred_model'
```

## Usage
Run the script directly:
```bash
python your_file_name.py
```

## Workflow Logic
1.  **Offline Phase**:
    - `ChunkDocumentsNode`: Splits the input `raw_text` into manageable strings.
    - `EmbedDocumentsNode`: Converts text chunks into vector embeddings.
    - `CreateIndexNode`: Initializes a FAISS index and stores the vectors for fast retrieval.
2.  **Online Phase**:
    - `EmbedQueryNode`: Converts the user's `query` into the same vector space.
    - `RetrieveDocumentNode`: Finds the most relevant chunk in the FAISS index.
    - `GenerateAnswerNode`: Constructs a prompt using the context and query, then calls the LLM to generate a grounded response.