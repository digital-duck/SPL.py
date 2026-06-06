# File Comparison Report

**Files Compared:**
- File 1: `S1-rag-openrouter-gemini-1-spec.md` (.md)
- File 2: `S5-rag-openrouter-gemini-2-spec.md` (.md)
- **Timestamp:** 2026-05-04 16:33:28
- **Active Modes:** llm, git-diff

---
## LLM Semantic Analysis

**Adapter:** claude_cli
**Model:** claude-opus-4-6

## Summary

Both files describe the same RAG pipeline (chunk → embed → index → query → retrieve → generate), but File 2 (S5) is a clear revision that tightens SPL-native vocabulary, consolidates the two-workflow design into a single unified workflow, adds prompt-engineering rigor, and includes proper termination semantics. File 1 (S1) is a competent first draft that leans too heavily on Python implementation details (node class names, two separate flow functions) rather than describing the *logical* SPL specification.

**File 2 is stronger overall.** It reads like an SPL spec; File 1 reads like annotated Python documentation.

---

## Content Analysis

### File 1 Strengths

- **Explicit two-phase decomposition**: Splitting into `OfflineIndexing` and `OnlineRAG` workflows makes the architectural boundary between indexing and querying very clear. This is a legitimate design choice in SPL (two `WORKFLOW` blocks composed via `CALL`).
- **Detailed control flow section**: The three-step breakdown for each sub-flow (Offline: Chunk → Embed → Index; Online: Embed → Retrieve → Generate) is easy to follow and correctly sequenced.
- **Honest Python mapping**: The construct table directly references the actual PocketFlow class names (`ChunkDocumentsNode`, `EmbedDocumentsNode`, etc.), making it useful as a reverse-engineering artifact.

### File 2 Strengths

- **SPL-native naming**: Tool names like `ChunkRawTexts`, `GenerateVectorEmbeddings`, `ConstructFAISSIndex`, `EmbedQuery`, `NearestNeighborSearch` use verb-first imperative naming consistent with SPL `CALL` conventions, rather than leaking Python class-name patterns.
- **Explicit model specification**: Names the target model (`google/gemini-3-flash-preview` via OpenRouter) in the high-level description — critical for reproducibility and for `text2spl` to emit the correct `USING MODEL` clause.
- **Prompt engineering depth**: The `GenerateAnswer` section adds role prompting ("helpful assistant") and a groundedness constraint ("state 'I don't know'"), which are absent from File 1. These are load-bearing for RAG quality.
- **Proper termination semantics**: Includes `RETURN WITH status="complete"` and maps it to a Python equivalent. File 1 vaguely says "updates the shared state with the final string" — that's a PocketFlow implementation detail, not an SPL-level description.
- **Single unified workflow**: `RagIndexingAndQuery` as one workflow is more faithful to a single `.spl` file that uses `CALL` for tool dispatch, avoiding premature decomposition.

### Common Elements

- Both follow the identical 6-section structure (§0–§5).
- Both correctly identify the core SPL constructs: `WORKFLOW`, `CREATE FUNCTION`, `CALL`, `GENERATE`, `@var` shared state.
- Both describe a linear (non-branching, non-looping) control flow.
- Both provide the same `text2spl` → `splc` regeneration pipeline in §5.
- Both correctly identify `GenerateAnswer` as the sole logical function / prompt template.

---

## Detailed Comparison

### Structure & Organization

| Aspect | File 1 | File 2 |
|---|---|---|
| Workflow granularity | Two workflows (`OfflineIndexing` + `OnlineRAG`) | One workflow (`RagIndexingAndQuery`) |
| Section completeness | All 6 sections present | All 6 sections present |
| §0 length & density | Moderate — covers both phases but omits model and termination | Dense — covers all phases, model, and termination in one paragraph |
| §2 table rows | 6 rows | 6 rows |
| §4 detail | Numbered list with sub-steps | Narrative paragraph with convergence description |

File 1's two-workflow split is defensible but introduces a design decision (how do offline and online compose?) that the spec never resolves — it just lists them side-by-side. File 2's single workflow with sequential `CALL` steps is simpler and more directly translatable to a single `.spl` file.

File 2's §4 mentions that the query embedding and indexing paths "converge" at `NearestNeighborSearch`, which subtly implies potential parallelism. This is more sophisticated than File 1's purely sequential description, though it's slightly misleading since the index must exist before the search can run.

### Logic & Completeness

- **Termination**: File 2 explicitly models `RETURN WITH status="complete"` — a first-class SPL construct (`COMMIT @var WITH STATUS = 'complete'`). File 1 has no termination semantics at all; the workflow just... ends.
- **Error / edge cases**: Neither file addresses error handling (`EXCEPTION WHEN ... THEN`), which is a gap in both. For a RAG pipeline, handling empty retrieval results or embedding failures would be relevant.
- **Input/Output declarations**: Neither file explicitly lists `INPUT:` / `OUTPUT:` for the workflow, which SPL requires. Both should declare what goes in (raw text, user query) and what comes out (answer).
- **Prompt completeness**: File 2's groundedness constraint ("I don't know" fallback) is a real functional requirement that affects output behavior. File 1's prompt description is minimal ("Briefly answer") — functional but shallow.

### Quality & Sophistication

File 2 demonstrates deeper understanding of SPL semantics:
- Uses `@raw_input` and `@user_query` as named variables (File 1 says "shared dictionary").
- Names the model explicitly (File 1 is model-agnostic — fine for a spec, but less useful for `text2spl` regeneration).
- The §5 regeneration command in File 2 uses a concrete filename (`rag_indexing.spl`) while File 1 uses a placeholder (`<output.spl>`). Both are acceptable but File 2 is more copy-paste ready.
- File 2's construct table includes `RETURN ... WITH status=` as a distinct row — this is correct; `COMMIT/RETURN` is a real SPL construct that File 1 omits entirely.

File 1 is cleaner in §4 (numbered list vs. paragraph), making it easier to scan. File 2's narrative §4 is denser but harder to parse at a glance.

### Syntax & Technical Accuracy

- Both are well-formatted Markdown with correct table syntax.
- File 1's §5 bash block correctly escapes the `text2spl` description. File 2 also handles this correctly, including escaping the inner quotes (`status=\"complete\"`).
- File 1 references `faiss.IndexFlatL2` in the construct table — this is a Python library detail that shouldn't appear in an SPL-level spec. File 2 abstracts this behind `ConstructFAISSIndex`, which is cleaner.
- File 2's §0 references "execution metadata" in the return value, which is not explained elsewhere in the spec — a minor loose end.

---

## Recommendations

### 1. Best Choice: **File 2 (S5)**

File 2 is the stronger spec. It stays at the SPL abstraction level, includes termination semantics, provides richer prompt engineering guidance, and names the target model. It would produce a more accurate `.spl` file if fed back through `text2spl`.

### 2. Improvements to File 1

- Add `RETURN WITH status="complete"` termination semantics.
- Replace Python class names (`ChunkDocumentsNode`) with imperative verb-noun tool names (`ChunkRawTexts`).
- Remove `faiss.IndexFlatL2` from the construct table — abstract behind a named `CALL` target.
- Add model specification to §0.
- Enrich the `GenerateAnswer` prompt description with role prompting and groundedness constraints.
- Add explicit `INPUT:` / `OUTPUT:` declarations.

### 3. Hybrid Approach

Take File 2 as the base and incorporate two elements from File 1:

1. **§4 formatting**: Use File 1's numbered-list style for the control flow section instead of File 2's dense paragraph. This improves scannability:
   ```
   1. CALL ChunkRawTexts(@raw_input) INTO @chunks
   2. CALL GenerateVectorEmbeddings(@chunks) INTO @embeddings
   3. CALL ConstructFAISSIndex(@embeddings) INTO @index
   4. CALL EmbedQuery(@user_query) INTO @query_vector
   5. CALL NearestNeighborSearch(@query_vector, @index) INTO @retrieved_context
   6. GENERATE GenerateAnswer(@retrieved_context, @user_query) INTO @answer
   7. RETURN @answer WITH status="complete"
   ```

2. **Two-phase labeling**: Keep File 2's single workflow but add phase annotations (e.g., "Indexing phase: steps 1–3; Query phase: steps 4–7") to preserve File 1's clarity about the offline/online boundary.

Additionally, both files should add `INPUT:` / `OUTPUT:` declarations and at least acknowledge error handling for empty retrieval results.

---

## Scoring

| Dimension | File 1 (S1) | File 2 (S5) | Notes |
|---|---|---|---|
| **Structure** | 7/10 | 8/10 | Both well-organized; F2 better abstraction level |
| **Logic** | 6/10 | 8/10 | F2 adds termination, groundedness, model; neither has error handling |
| **Quality** | 6/10 | 8/10 | F2 is more SPL-native and prompt-aware |
| **Overall** | **6/10** | **8/10** | F2 is the clear winner; F1 is a reasonable first draft |

**Bottom line**: File 2 is the production-ready spec. File 1 served its purpose as an initial extraction but should be superseded. The main gap in File 2 is the lack of structured control flow formatting and missing `INPUT:`/`OUTPUT:` declarations — both easy fixes.
---

## Mechanical Diff (Unified Style)

```diff
--- a/S1-rag-openrouter-gemini-1-spec.md
+++ b/S5-rag-openrouter-gemini-2-spec.md
@@ -1,42 +1,38 @@
 ## 0. High-level Description

-This workflow implements a classic Retrieval-Augmented Generation (RAG) pattern divided into two distinct WORKFLOW phases: an offline indexing phase and an online query phase. The offline phase begins by processing raw text through a `fixed_size_chunk` utility, followed by a CALL to an embedding service to transform text chunks into vectors, which are then stored in a FAISS vector index. The online phase mirrors this by using a CALL to embed a user query, followed by a retrieval step that searches the FAISS index for the most relevant document chunk. A CREATE FUNCTION named `GenerateAnswer` defines the prompt template that combines the retrieved context with the user's question. The workflow executes a GENERATE call using this function to produce the final response.

+The WORKFLOW RagIndexingAndQuery implements a classic Retrieval-Augmented Generation (RAG) pattern to provide grounded answers to user queries. The process begins with a series of side-effect tool calls using CALL to prepare the knowledge base: it invokes ChunkRawTexts to segment the input data, followed by GenerateVectorEmbeddings and ConstructFAISSIndex to build a searchable vector store. To perform the retrieval, the workflow executes CALL EmbedQuery on the user's question and passes the result to CALL NearestNeighborSearch to extract relevant context from the index. This retrieved context is then passed into the logical function GenerateAnswer via a GENERATE construct, which utilizes the google/gemini-3-flash-preview model via OpenRouter to synthesize a final response. The workflow concludes by using RETURN WITH status="complete" to provide the user with the final grounded answer and execution metadata.

 

 ## 1. Purpose

-This implementation automates a document-based question-answering system by indexing text data into a searchable vector space and using an LLM to synthesize answers from retrieved context.

+This implementation automates an end-to-end RAG pipeline—from raw text indexing to vector search and LLM synthesis—to answer user questions based on specific provided documents.

 

 ## 2. SPL ↔ Python Construct Mapping

 

 | SPL Construct | Python Equivalent | Notes |

 | :--- | :--- | :--- |

-| **WORKFLOW** `OfflineIndexing` | `get_offline_flow()` | Orchestrates document preparation and indexing. |

-| **WORKFLOW** `OnlineRAG` | `get_online_flow()` | Orchestrates query embedding, retrieval, and generation. |

-| **CREATE FUNCTION** `GenerateAnswer` | `GenerateAnswerNode.exec` (prompt string) | Template for the final synthesis step. |

-| **GENERATE** | `call_llm(prompt)` | LLM call within `GenerateAnswerNode`. |

-| **CALL** | `get_embedding(text)`, `faiss.IndexFlatL2` | External tool calls for vectorization and indexing. |

-| **@vars** | `shared` dictionary | Shared state (texts, embeddings, index, query). |

+| **WORKFLOW** `RagIndexingAndQuery` | `run_rag_pipeline(raw_input, user_query)` | Orchestrates the indexing and retrieval sequence. |

+| **CREATE FUNCTION** `GenerateAnswer` | `generate_answer(context, user_query)` | Prompt template for the final synthesis step. |

+| **CALL** | Tool function calls (e.g., `ChunkRawTexts(...)`) | Used for data processing and vector database operations. |

+| **GENERATE** | `call_llm(prompt)` inside `generate_answer` | Triggers the LLM inference via the OpenRouter API. |

+| **@var** (Shared State) | Local variables (e.g., `chunked_docs`, `vector_index`) | Stores intermediate data between tool calls and LLM steps. |

+| **RETURN ... WITH status=** | `return {"final_response": ..., "status": "complete"}` | Terminates the workflow with a non-trivial "complete" status. |

 

 ## 3. Logical Functions / Prompts

-

 ### GenerateAnswer

-- **Role**: Synthesizes a concise answer by grounding the LLM in retrieved context.

-- **Key Prompt Conventions**:

-    - Uses a `Context:` block to provide the retrieved document chunk.

-    - Uses a `Question:` block for the user's input.

-    - Explicitly instructs the model to "Briefly answer" to control output length.

+- **Role**: Acts as the synthesis engine that merges retrieved context with the user's question.

+- **Key Prompt Conventions**: 

+    - **Role Prompting**: Identifies as a "helpful assistant."

+    - **Groundedness Constraint**: Explicitly instructed to state "I don't know" if the answer is missing from the context.

+    - **Context Injection**: Uses `{context}` and `{user_query}` slots for dynamic data insertion.

 

 ## 4. Control Flow

-The execution follows a strictly linear orchestration across two sub-flows:

-1.  **Offline Flow**: Starts with `ChunkDocumentsNode` (splitting text) → `EmbedDocumentsNode` (vectorizing) → `CreateIndexNode` (building the FAISS index).

-2.  **Online Flow**: Starts with `EmbedQueryNode` (vectorizing user input) → `RetrieveDocumentNode` (performing a vector search against the index) → `GenerateAnswerNode` (invoking the LLM with the context).

-3.  **Termination**: The process ends after the `GenerateAnswerNode` updates the shared state with the final string.

+The execution follows a strictly linear indexing and retrieval path. It starts by transforming `@raw_input` into a vector index through a sequence of `CALL` operations (`ChunkRawTexts` → `GenerateVectorEmbeddings` → `ConstructFAISSIndex`). Simultaneously, the `@user_query` is processed into an embedding. These paths converge at `NearestNeighborSearch` to produce `@retrieved_context`. Finally, the workflow invokes `GENERATE GenerateAnswer` and terminates by returning the result with a `status` of "complete".

 

 ## 5. How to Regenerate as SPL

 ```bash

 # Step 1 — generate SPL from this spec (Section 0 above as text2spl input)

-spl3 text2spl --description "This workflow implements a classic Retrieval-Augmented Generation (RAG) pattern divided into two distinct WORKFLOW phases: an offline indexing phase and an online query phase. The offline phase begins by processing raw text through a fixed_size_chunk utility, followed by a CALL to an embedding service to transform text chunks into vectors, which are then stored in a FAISS vector index. The online phase mirrors this by using a CALL to embed a user query, followed by a retrieval step that searches the FAISS index for the most relevant document chunk. A CREATE FUNCTION named GenerateAnswer defines the prompt template that combines the retrieved context with the user's question. The workflow executes a GENERATE call using this function to produce the final response." --mode workflow

+spl3 text2spl --description "The WORKFLOW RagIndexingAndQuery implements a classic Retrieval-Augmented Generation (RAG) pattern to provide grounded answers to user queries. The process begins with a series of side-effect tool calls using CALL to prepare the knowledge base: it invokes ChunkRawTexts to segment the input data, followed by GenerateVectorEmbeddings and ConstructFAISSIndex to build a searchable vector store. To perform the retrieval, the workflow executes CALL EmbedQuery on the user's question and passes the result to CALL NearestNeighborSearch to extract relevant context from the index. This retrieved context is then passed into the logical function GenerateAnswer via a GENERATE construct, which utilizes the google/gemini-3-flash-preview model via OpenRouter to synthesize a final response. The workflow concludes by using RETURN WITH status=\"complete\" to provide the user with the final grounded answer and execution metadata." --mode workflow

 

 # Step 2 — compile to any target

-spl3 splc compile <output.spl> --lang python/pocketflow

-spl3 splc compile <output.spl> --lang python/langgraph

-spl3 splc compile <output.spl> --lang go

+spl3 splc compile rag_indexing.spl --lang python/pocketflow

+spl3 splc compile rag_indexing.spl --lang python/langgraph

+spl3 splc compile rag_indexing.spl --lang go

 ```
```
---

*Generated by SPL semantic comparison tool*