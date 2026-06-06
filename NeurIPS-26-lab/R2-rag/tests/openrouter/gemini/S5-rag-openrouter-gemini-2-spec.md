## 0. High-level Description
The WORKFLOW RagIndexingAndQuery implements a classic Retrieval-Augmented Generation (RAG) pattern to provide grounded answers to user queries. The process begins with a series of side-effect tool calls using CALL to prepare the knowledge base: it invokes ChunkRawTexts to segment the input data, followed by GenerateVectorEmbeddings and ConstructFAISSIndex to build a searchable vector store. To perform the retrieval, the workflow executes CALL EmbedQuery on the user's question and passes the result to CALL NearestNeighborSearch to extract relevant context from the index. This retrieved context is then passed into the logical function GenerateAnswer via a GENERATE construct, which utilizes the google/gemini-3-flash-preview model via OpenRouter to synthesize a final response. The workflow concludes by using RETURN WITH status="complete" to provide the user with the final grounded answer and execution metadata.

## 1. Purpose
This implementation automates an end-to-end RAG pipeline—from raw text indexing to vector search and LLM synthesis—to answer user questions based on specific provided documents.

## 2. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
| :--- | :--- | :--- |
| **WORKFLOW** `RagIndexingAndQuery` | `run_rag_pipeline(raw_input, user_query)` | Orchestrates the indexing and retrieval sequence. |
| **CREATE FUNCTION** `GenerateAnswer` | `generate_answer(context, user_query)` | Prompt template for the final synthesis step. |
| **CALL** | Tool function calls (e.g., `ChunkRawTexts(...)`) | Used for data processing and vector database operations. |
| **GENERATE** | `call_llm(prompt)` inside `generate_answer` | Triggers the LLM inference via the OpenRouter API. |
| **@var** (Shared State) | Local variables (e.g., `chunked_docs`, `vector_index`) | Stores intermediate data between tool calls and LLM steps. |
| **RETURN ... WITH status=** | `return {"final_response": ..., "status": "complete"}` | Terminates the workflow with a non-trivial "complete" status. |

## 3. Logical Functions / Prompts
### GenerateAnswer
- **Role**: Acts as the synthesis engine that merges retrieved context with the user's question.
- **Key Prompt Conventions**: 
    - **Role Prompting**: Identifies as a "helpful assistant."
    - **Groundedness Constraint**: Explicitly instructed to state "I don't know" if the answer is missing from the context.
    - **Context Injection**: Uses `{context}` and `{user_query}` slots for dynamic data insertion.

## 4. Control Flow
The execution follows a strictly linear indexing and retrieval path. It starts by transforming `@raw_input` into a vector index through a sequence of `CALL` operations (`ChunkRawTexts` → `GenerateVectorEmbeddings` → `ConstructFAISSIndex`). Simultaneously, the `@user_query` is processed into an embedding. These paths converge at `NearestNeighborSearch` to produce `@retrieved_context`. Finally, the workflow invokes `GENERATE GenerateAnswer` and terminates by returning the result with a `status` of "complete".

## 5. How to Regenerate as SPL
```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "The WORKFLOW RagIndexingAndQuery implements a classic Retrieval-Augmented Generation (RAG) pattern to provide grounded answers to user queries. The process begins with a series of side-effect tool calls using CALL to prepare the knowledge base: it invokes ChunkRawTexts to segment the input data, followed by GenerateVectorEmbeddings and ConstructFAISSIndex to build a searchable vector store. To perform the retrieval, the workflow executes CALL EmbedQuery on the user's question and passes the result to CALL NearestNeighborSearch to extract relevant context from the index. This retrieved context is then passed into the logical function GenerateAnswer via a GENERATE construct, which utilizes the google/gemini-3-flash-preview model via OpenRouter to synthesize a final response. The workflow concludes by using RETURN WITH status=\"complete\" to provide the user with the final grounded answer and execution metadata." --mode workflow

# Step 2 — compile to any target
spl3 splc compile rag_indexing.spl --lang python/pocketflow
spl3 splc compile rag_indexing.spl --lang python/langgraph
spl3 splc compile rag_indexing.spl --lang go
```