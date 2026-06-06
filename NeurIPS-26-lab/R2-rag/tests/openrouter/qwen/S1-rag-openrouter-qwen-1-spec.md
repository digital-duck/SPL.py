## 0. High-level Description
This workflow implements a Retrieval-Augmented Generation (RAG) system by orchestrating an offline document indexing phase followed by an online query processing phase. During the offline stage, a batch processing sequence chunks raw texts, generates vector embeddings for each chunk, and constructs a searchable FAISS index, storing all intermediates in shared variables. The online phase accepts a user query, embeds it into the same vector space, performs a nearest-neighbor search against the index, and retrieves the single most relevant document. A CREATE FUNCTION named GenerateAnswer formats the query and context into a structured prompt, which is executed via GENERATE to produce the final response. The workflow relies on strict linear progression between phases to advance through the pipeline, while CALL operations handle console logging, index persistence, and optional markdown file writing. Exception handling is omitted as the pipeline assumes successful API connectivity and valid input formatting throughout execution.

## 1. Purpose
This implementation processes a document corpus into a vector-searchable index and then uses semantic retrieval paired with an LLM to answer user questions with grounded context.

## 2. SPL ↔ Python Construct Mapping
| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| WORKFLOW | `Flow` instances (`offline_flow`, `online_flow`) wrapped in `main()` | Coordinates two sequential execution phases with shared context handoff |
| CREATE FUNCTION | Prompt string in `GenerateAnswerNode.exec` | Templated prompt with `{query}` and `{context}` interpolation slots |
| GENERATE | `utils.call_llm()` and `utils.get_embedding()` | Invokes the LLM for answer generation and OpenAI-compatible vector embedding |
| CALL (tool) | `faiss.IndexFlatL2()`, `Path.write_text()`, `print()` | Side-effect operations for FAISS index construction, file output, and console logging |
| Shared State (`@var`) | `shared` dictionary passed to `Flow.run()` | Mutable pipeline memory mapping to `@texts`, `@embeddings`, `@index`, `@query`, `@query_embedding`, `@retrieved_document`, `@generated_answer` |
| WHILE / EVALUATE | Not implemented | Pipeline uses strictly linear progression; no conditional branching or iterative loops are required |
| EXCEPTION | Not implemented | Errors are unhandled at the orchestration level and propagate directly to the Python runtime |
| RETURN (non-trivial) | Not implemented | Execution advances linearly through node sequencing without status-driven branching or loop termination |

## 3. Logical Functions / Prompts
- **Name:** GenerateAnswer
- **Role:** Formats the original user question and the top-ranked retrieved document chunk into a context-aware prompt for the final LLM inference step.
- **Key prompt conventions:** Uses a plain-text template with explicit `Question:` and `Context:` labels, terminated by an `Answer:` directive to encourage concise, grounded natural language output. No JSON schemas, scoring rubrics, or sentinel termination tokens are used; raw text is expected.

## 4. Control Flow
Execution begins with the offline indexing phase, where raw documents are sequentially chunked, vectorized, and committed to a FAISS index, with all intermediate results written to shared state variables. Upon completion of the indexing sequence, control transitions to the online phase, starting with query embedding and a single nearest-neighbor search against the index to populate the `@retrieved_document` variable. The workflow then invokes the GENERATE step using the retrieved context and original query, storing the LLM's output in `@generated_answer`. Finally, the linear pipeline terminates, and the host environment optionally persists the question-answer pair to a markdown file before exiting.

## 5. How to Regenerate as SPL
```
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "<paste Section 0 here>" --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```