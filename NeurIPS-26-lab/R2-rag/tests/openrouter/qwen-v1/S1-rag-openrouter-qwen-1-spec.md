## 0. High-level Description
This workflow defines a two-phase Retrieval-Augmented Generation (RAG) pipeline orchestrated as a single named WORKFLOW that transitions from offline document indexing to online query resolution. It leverages CREATE FUNCTION to define a reusable prompt template for answer synthesis, relying on sequential CALL operations to handle text chunking, vector embedding via a dedicated embedding model, and FAISS index construction. The online stage embeds the user query via another CALL, retrieves the most semantically relevant context through a vector similarity search, and invokes GENERATE using the prompt function to produce a context-grounded response. Execution proceeds linearly but incorporates an EVALUATE block to verify the retrieval distance against a confidence threshold before proceeding, concluding with a RETURN statement that packages the final answer alongside retrieval metadata. Side-effects such as optional file persistence and console logging are managed via dedicated tool calls, while a global EXCEPTION handler intercepts API timeouts, rate limits, or empty context payloads to ensure graceful degradation and workflow continuity.

## 1. Purpose
This implementation provides end users with an automated RAG system that indexes a document corpus and answers natural language questions by retrieving relevant context and synthesizing concise LLM-generated responses.

## 2. SPL ↔ Python Construct Mapping
| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW` | `pocketflow.Flow` (`get_offline_flow`, `get_online_flow`) | Defines the end-to-end orchestration boundaries and shared state lifecycle |
| `CREATE FUNCTION` | Prompt string in `GenerateAnswerNode.exec()` | Reusable template with `{query}` and `{context}` interpolation slots |
| `GENERATE` | `call_llm()` inside `GenerateAnswerNode` | Triggers the generative LLM and stores the completion in `@generated_answer` |
| `CALL` | `get_embedding()`, `fixed_size_chunk()`, FAISS `index.add/search` | External tool invocations for chunking, vectorization, and vector DB operations |
| `WHILE` | `BatchNode` iteration over `shared["texts"]` | Implicitly loops over documents; SPL uses explicit `WHILE` for chunking/embedding batches |
| `EVALUATE @<var> WHEN contains(...) THEN ...` | Distance threshold check in `RetrieveDocumentNode` | Branches on retrieval confidence; routes to fallback if similarity is below threshold |
| `RETURN @<var> WITH ...` | Final `shared` dict extraction in `main.py` | Outputs the answer payload with `status=`, `iterations=`, and `retrieval_score=` |
| `EXCEPTION WHEN <Type> THEN ...` | Implicit `try/except` around `OpenAI` client calls | Handles `APIError`, `ConnectionError`, or empty retrieval payloads |
| Shared State (`@<var>`) | `shared` dictionary (`texts`, `embeddings`, `index`, etc.) | Memory-passed variables bridging offline and online phases |

## 3. Logical Functions / Prompts
### AnswerSynthesis
- **Role in the workflow:** Generates a concise, factually grounded response to the user's natural language query using only the top-retrieved document chunk as context.
- **Key prompt conventions:** 
  - Uses explicit structural delimiters: `Question:`, `Context:`, `Answer:`
  - Enforces brevity with the instruction `Briefly answer the following question...`
  - Expects plain-text output without markdown formatting or conversational filler
  - Relies on exact string interpolation for `{query}` and `{retrieved_context}` slots
  - No few-shot examples or chain-of-thought directives; single-turn completion expected

## 4. Control Flow
The workflow initializes by populating `@texts` with raw input documents. It enters the offline indexing phase, where a `WHILE` loop iterates over each document, applying chunking and embedding `CALL` operations until `@texts` is fully vectorized, then invokes a `CALL` to construct a FAISS `@index`. The workflow transitions to the online query phase, embedding the input query via another `CALL` and executing a nearest-neighbor search. An `EVALUATE` block inspects the returned similarity distance; if the distance exceeds a predefined threshold (indicating low confidence), it branches to a safe fallback, otherwise it proceeds to `GENERATE` using the `AnswerSynthesis` function with the retrieved text. Finally, a `RETURN @generated_answer WITH status="success", score=<distance>, doc_index=<idx>` terminates execution, while any `APIError` or `ValueError` triggers the `EXCEPTION` handler to log the fault and return a degraded response.

## 5. How to Regenerate as SPL
```
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```