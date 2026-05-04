## 0. High-level Description
This workflow implements a classic Retrieval-Augmented Generation (RAG) pattern divided into two distinct WORKFLOW phases: an offline indexing phase and an online query phase. The offline phase begins by processing raw text through a `fixed_size_chunk` utility, followed by a CALL to an embedding service to transform text chunks into vectors, which are then stored in a FAISS vector index. The online phase mirrors this by using a CALL to embed a user query, followed by a retrieval step that searches the FAISS index for the most relevant document chunk. A CREATE FUNCTION named `GenerateAnswer` defines the prompt template that combines the retrieved context with the user's question. The workflow executes a GENERATE call using this function to produce the final response.

## 1. Purpose
This implementation automates a document-based question-answering system by indexing text data into a searchable vector space and using an LLM to synthesize answers from retrieved context.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
| :--- | :--- | :--- |
| **WORKFLOW** `OfflineIndexing` | `get_offline_flow()` | Orchestrates document preparation and indexing. |
| **WORKFLOW** `OnlineRAG` | `get_online_flow()` | Orchestrates query embedding, retrieval, and generation. |
| **CREATE FUNCTION** `GenerateAnswer` | `GenerateAnswerNode.exec` (prompt string) | Template for the final synthesis step. |
| **GENERATE** | `call_llm(prompt)` | LLM call within `GenerateAnswerNode`. |
| **CALL** | `get_embedding(text)`, `faiss.IndexFlatL2` | External tool calls for vectorization and indexing. |
| **@vars** | `shared` dictionary | Shared state (texts, embeddings, index, query). |

## 3. Logical Functions / Prompts

### GenerateAnswer
- **Role**: Synthesizes a concise answer by grounding the LLM in retrieved context.
- **Key Prompt Conventions**:
    - Uses a `Context:` block to provide the retrieved document chunk.
    - Uses a `Question:` block for the user's input.
    - Explicitly instructs the model to "Briefly answer" to control output length.

## 4. Control Flow
The execution follows a strictly linear orchestration across two sub-flows:
1.  **Offline Flow**: Starts with `ChunkDocumentsNode` (splitting text) → `EmbedDocumentsNode` (vectorizing) → `CreateIndexNode` (building the FAISS index).
2.  **Online Flow**: Starts with `EmbedQueryNode` (vectorizing user input) → `RetrieveDocumentNode` (performing a vector search against the index) → `GenerateAnswerNode` (invoking the LLM with the context).
3.  **Termination**: The process ends after the `GenerateAnswerNode` updates the shared state with the final string.

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This workflow implements a classic Retrieval-Augmented Generation (RAG) pattern divided into two distinct WORKFLOW phases: an offline indexing phase and an online query phase. The offline phase begins by processing raw text through a fixed_size_chunk utility, followed by a CALL to an embedding service to transform text chunks into vectors, which are then stored in a FAISS vector index. The online phase mirrors this by using a CALL to embed a user query, followed by a retrieval step that searches the FAISS index for the most relevant document chunk. A CREATE FUNCTION named GenerateAnswer defines the prompt template that combines the retrieved context with the user's question. The workflow executes a GENERATE call using this function to produce the final response." --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```