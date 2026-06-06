# File Comparison Report

**Files Compared:**
- File 1: `S1-rag-claude_cli-sonnet-1-spec.md` (.md)
- File 2: `S5-rag-claude_cli-sonnet-2-spec.md` (.md)
- **Timestamp:** 2026-05-04 09:39:25
- **Active Modes:** llm, git-diff

---
## LLM Semantic Analysis

**Adapter:** claude_cli
**Model:** claude-opus-4-6

## Summary

Both files are SPL specification documents for a RAG pipeline, but they represent **different iterations** of the same concept. **File 1 (S1)** describes an OpenAI-embedding + FAISS implementation with two separate workflows. **File 2 (S5)** describes a self-contained bag-of-words + numpy implementation with a single unified workflow. File 2 is the stronger spec overall — it is more precise, more self-contained, and includes structural elements (EVALUATE branching, observed run data) that File 1 lacks entirely. File 1, however, provides richer detail in its construct mapping and regeneration notes.

---

## Content Analysis

### File 1 Strengths

- **Exhaustive construct mapping table**: 14 rows covering every SPL construct including explicit "absent" entries for WHILE, EVALUATE, and EXCEPTION — makes the spec function as a completeness checklist.
- **Detailed regeneration notes**: Four specific bullets calling out shared-store semantics, batch-node flagging, GENERATE-vs-CALL distinction, and defensive removal of auto-inserted loops. These are actionable for someone running `text2spl`.
- **Richer logical function descriptions**: Each function gets a full "Role" + "Conventions" breakdown with concrete details (e.g., "2000-character fixed-size chunking; no overlap", "`np.array(exec_res_list, dtype=np.float32)`").
- **Prompt template shown verbatim**: The actual prompt for `GenerateAnswer` is quoted in full, letting the reader judge quality and tone without reading source code.

### File 2 Strengths

- **Single unified workflow**: Collapses the two-workflow design into one `RAGPipeline` with explicit `INPUT`/`OUTPUT` declarations — cleaner, more idiomatic SPL.
- **EVALUATE construct present**: The `EVALUATE @output_path WHEN contains(".")` block is the only conditional logic in either spec, making File 2 structurally richer and a better test of SPL's branching semantics.
- **Zero external dependencies for retrieval**: Bag-of-words TF-IDF with numpy replaces OpenAI embeddings + FAISS, making the pipeline fully runnable without API keys or native library installs.
- **Observed run data**: Section 4 includes a concrete execution result ("Query `What is PocketFlow?` against 5 sample documents → `status=complete`"), grounding the spec in an actual test.
- **Adapter-explicit mapping**: The construct table explicitly maps `claude_cli` adapter usage to the `subprocess.run(["claude", ...])` implementation — no ambiguity about which LLM backend is used.
- **Cleaner Section 0**: The high-level description names all seven nodes in execution order with one-clause summaries, reading as a self-contained abstract.

### Common Elements

- Both follow the identical 6-section structure (Sections 0–5) with the same headings.
- Both implement the same core RAG pipeline stages: chunk → embed → index → embed-query → retrieve → generate.
- Both have exactly one LLM `GENERATE` call (`GenerateAnswer` / `generate_answer`) with all other steps as deterministic `CALL` operations.
- Both use PocketFlow as the Python execution framework with `shared` dict for inter-node state.
- Both explicitly note the absence of WHILE loops and EXCEPTION handlers.
- Both provide `spl3 text2spl` and `spl3 splc compile` regeneration commands.

---

## Detailed Comparison

### Structure & Organization

| Dimension | File 1 | File 2 |
|---|---|---|
| Workflow topology | Two workflows (`offline_indexing`, `online_query`) sharing `@shared` | One workflow (`RAGPipeline`) with `INPUT`/`OUTPUT` declarations |
| Node count | 6 logical functions | 7 nodes (adds `WriteOutputNode`) |
| Section separators | None between sections | `---` horizontal rules between sections |
| Construct table completeness | 14 rows, includes absent constructs | 13 rows, more focused on what's present |
| Pseudocode in Section 4 | Present, with inline comments | Present, with type annotations and observed run |

File 1's two-workflow design is architecturally more modular (offline/online separation is a real-world pattern), but it introduces implicit coupling via the shared store. File 2's single-workflow design is simpler and more faithful to how PocketFlow actually executes the code. File 2's use of `---` separators and consistent formatting gives it a slight edge in readability.

### Logic & Completeness

**Branching logic**: File 1 has zero conditional paths — it is purely linear. File 2 includes an `EVALUATE` guard on the write step, which is a meaningful difference: it demonstrates the spec's ability to represent conditional execution.

**Input/Output declarations**: File 2 explicitly declares `INPUT @documents LIST, @query TEXT, @output_path TEXT := ""` and `OUTPUT @generated_answer TEXT` in the control flow pseudocode. File 1 leaves inputs implicit in the shared store.

**Edge case handling**: File 2 documents two edge cases — `RetrieveDocumentNode` returns empty string when the matrix has zero rows, and `WriteOutputNode` returns `"skipped"` when `output_path` lacks a file extension. File 1 documents none.

**Error handling**: Both punt — "errors propagate as Python exceptions" / "errors propagate from API calls unhandled." Neither is better here.

**Termination**: Both guarantee termination by finite linear chains. File 1 explains the `"default"` action token mechanism; File 2 assumes familiarity with PocketFlow's `>>` chaining.

### Quality & Sophistication

**Embedding approach**: File 1 uses OpenAI `text-embedding-ada-002` (production-grade, high-dimensional dense embeddings). File 2 uses hand-rolled bag-of-words TF-IDF with L2 normalization (pedagogical, zero-dependency). File 1 is more realistic for production; File 2 is more self-contained and testable.

**Retrieval approach**: File 1 uses FAISS `IndexFlatL2` with `k=1` (proper vector search library). File 2 uses `np.argmax(matrix @ qvec)` (manual cosine similarity). File 1 is more scalable; File 2 is more transparent.

**Chunking approach**: File 1 uses fixed 2000-character windows with no overlap. File 2 splits on `\n\n+` (paragraph boundaries) with whole-doc fallback. File 2's approach is semantically more meaningful; File 1's is more predictable for large documents.

**Prompt quality**: File 1 quotes the full prompt ("Briefly answer the following question based on the context provided…"). File 2 describes the prompt's behavior ("answer solely from provided context; explicitly asks it to acknowledge when context is insufficient") without quoting it. File 2's prompt is arguably more robust (hallucination guard), but File 1's transparency is more useful for a spec document.

**Batch processing**: File 1 explicitly models `ChunkDocuments` and `EmbedDocuments` as `BatchNode` subclasses, which is a meaningful PocketFlow distinction. File 2 doesn't call out batch semantics.

### Syntax & Technical Accuracy

**File 1 issues**:
- Section 4 pseudocode uses `CALL ChunkDocuments(@texts) INTO @texts` — overwriting `@texts` with its own output is confusing (the input is raw documents, the output is chunks). The variable name should change.
- `RETURN WITH status="done"` in pseudocode but `RETURN ... WITH status="default"` in the construct table — inconsistency.
- Claims `EVALUATE` is absent, but the Python code likely has the file-write conditional — this may be a spec gap rather than a code gap.

**File 2 issues**:
- Names a node `CreateFaissIndexNode` but explicitly states "no FAISS dependency" — the naming mismatch could confuse readers, though it's acknowledged in the construct table.
- The `EVALUATE @output_path WHEN contains(".")` heuristic is brittle (e.g., `"./mydir"` would match despite being a directory path). This is noted implicitly as a "file-extension heuristic" but not flagged as a limitation.
- The Section 5 `sed` command for extracting Section 0 uses `^---` as the end marker, which is fragile if the markdown evolves.

---

## Recommendations

### 1. Best Choice

**File 2 (S5)** is the better spec. It is more complete (EVALUATE construct, INPUT/OUTPUT declarations, edge cases, observed run), more self-contained (no external API dependencies), and better organized. It reads as a mature iteration that learned from File 1's gaps.

### 2. Improvements for File 1

- Add explicit `INPUT`/`OUTPUT` declarations in the Section 4 pseudocode.
- Fix the `@texts` variable overwrite — use `@chunks` for the output of `ChunkDocuments`.
- Resolve the `"done"` vs `"default"` status inconsistency.
- Add an `EVALUATE` guard for the optional file-write step (it exists in the Python code but is missing from the spec).
- Include an observed run with concrete input/output to ground the spec.

### 3. Hybrid Approach

Take File 2's structure and add:
- File 1's **verbatim prompt template** in Section 3 (transparency).
- File 1's **explicit absent-construct rows** (WHILE, EVALUATE, EXCEPTION) in the construct table (completeness checklist).
- File 1's **batch-node annotation** for chunking and embedding nodes.
- File 1's **four regeneration notes** appended to File 2's Section 5 (they're universally applicable).
- File 2's **observed run data** and **INPUT/OUTPUT declarations** (kept as-is).

---

## Scoring

| Dimension | File 1 | File 2 | Rationale |
|---|---|---|---|
| **Structure** | 7/10 | 8/10 | File 2's single-workflow + separators + INPUT/OUTPUT is cleaner; File 1's two-workflow split adds unnecessary coupling |
| **Logic** | 6/10 | 8/10 | File 2 has conditional branching, edge cases, observed run; File 1 is purely linear with a variable-name bug |
| **Quality** | 7/10 | 8/10 | File 1 has richer function docs and verbatim prompt; File 2 is more self-contained and production-tested |
| **Syntax** | 6/10 | 7/10 | Both have minor issues; File 1's status inconsistency and `@texts` overwrite are more impactful |
| **Overall** | **6.5/10** | **7.75/10** | File 2 is the clear winner; File 1's main advantage (detailed mapping table, prompt transparency) can be grafted onto File 2 |
---

## Mechanical Diff (Unified Style)

```diff
--- a/S1-rag-claude_cli-sonnet-1-spec.md
+++ b/S5-rag-claude_cli-sonnet-2-spec.md
@@ -1,100 +1,94 @@
 ## 0. High-level Description

 

-This workflow implements a two-phase Retrieval Augmented Generation (RAG) pipeline expressed as two sequential SPL WORKFLOWs: an **offline indexing workflow** and an **online query workflow**, sharing state through a common `@shared` variable store. The offline phase contains three logical functions: `ChunkDocuments` (a batch CREATE FUNCTION that splits raw texts into fixed-size chunks), `EmbedDocuments` (a batch CREATE FUNCTION that issues CALL operations to an embedding API for each chunk and accumulates the resulting vectors), and `CreateIndex` (a CALL that builds a FAISS L2 vector index from the accumulated embeddings). The online phase contains three further logical functions: `EmbedQuery` (a CALL to the same embedding API for the user's question), `RetrieveDocument` (a CALL to the FAISS index that performs a k=1 nearest-neighbor search and returns the best-matching chunk with its distance score), and `GenerateAnswer` (a GENERATE call to an LLM whose prompt template slots in `{query}` and `{context}` from the retrieved document). Control flow is strictly linear in both workflows — no WHILE loop or EVALUATE branch is present — and each step RETURNs a `"default"` action token to advance to the next node. The final RETURN surfaces `@generated_answer` to the caller and, when an output path is supplied, issues a side-effect CALL that persists the Q/A pair to disk. No explicit EXCEPTION handlers are defined; errors propagate from the underlying API calls.

+This workflow implements a classic Retrieval-Augmented Generation pipeline as a strictly linear PocketFlow graph — no loops, no branches. Seven nodes execute in sequence: `ChunkDocumentsNode` splits input documents on double-newlines into a flat `@texts` list; `EmbedDocumentsNode` builds a bag-of-words TF-IDF-style vocabulary from all tokens and produces L2-normalised numpy vectors; `CreateFaissIndexNode` packages the embedding matrix and vocabulary into an index dict (pure numpy, no FAISS dependency despite the SPL CALL name); `EmbedQueryNode` projects the query into the same vocabulary space; `RetrieveDocumentNode` selects the best-matching chunk via cosine similarity (argmax over `matrix @ query_vec`); `GenerateAnswerNode` calls the LLM with the retrieved chunk as context; `WriteOutputNode` conditionally writes the answer to a file when `@output_path` contains a `.` (file-extension heuristic). The `EVALUATE @output_path WHEN contains(".")` SPL construct maps to a plain `if "." in output_path` Python guard. The workflow terminates by setting `shared["status"] = "complete"` and returning `@generated_answer`. There are no loops or EXCEPTION blocks; failures propagate as Python exceptions.

+

+---

 

 ## 1. Purpose

 

-Answers a user's natural-language question by first indexing a small document corpus into a FAISS vector store (offline), then retrieving the single most relevant chunk at query time and generating a grounded answer with an LLM (online).

+Answers a query against a small local document corpus using bag-of-words cosine retrieval and a single LLM synthesis call; optionally writes the answer to a file.

 

-## 2. SPL ↔ Python Construct Mapping

+---

 

-| SPL Construct | Python Equivalent | Notes |

+## 2. SPL ↔ Python — PocketFlow Construct Mapping

+

+| SPL Construct | Python — PocketFlow Equivalent | Notes |

 |---|---|---|

-| `WORKFLOW offline_indexing` | `get_offline_flow()` → `Flow(start=chunk_docs_node)` | Linear three-node PocketFlow pipeline |

-| `WORKFLOW online_query` | `get_online_flow()` → `Flow(start=embed_query_node)` | Linear three-node PocketFlow pipeline |

-| `CREATE FUNCTION ChunkDocuments` | `ChunkDocumentsNode(BatchNode)` | Batch node; `exec(text)` maps `fixed_size_chunk` over each doc |

-| `CREATE FUNCTION EmbedDocuments` | `EmbedDocumentsNode(BatchNode)` | Batch node; `exec(text)` calls `get_embedding` per chunk |

-| `CREATE FUNCTION CreateIndex` | `CreateIndexNode(Node)` | Single node; `exec(embeddings)` runs `faiss.IndexFlatL2` + `index.add` |

-| `CREATE FUNCTION EmbedQuery` | `EmbedQueryNode(Node)` | Single node; `exec(query)` calls `get_embedding` |

-| `CREATE FUNCTION RetrieveDocument` | `RetrieveDocumentNode(Node)` | Single node; `exec(inputs)` calls `index.search(q_emb, k=1)` |

-| `CREATE FUNCTION GenerateAnswer` | `GenerateAnswerNode(Node)` | Contains the only LLM prompt template |

-| `GENERATE GenerateAnswer(...) INTO @generated_answer` | `call_llm(prompt)` inside `GenerateAnswerNode.exec` | Only true LLM generation call |

-| `CALL get_embedding(...) INTO @embedding` | `get_embedding(text)` in `EmbedDocumentsNode` / `EmbedQueryNode` | Deterministic API call, not a generation |

-| `CALL faiss_search(...) INTO @retrieved_document` | `index.search(query_embedding, k=1)` in `RetrieveDocumentNode` | Pure vector math side-effect |

-| `CALL write_file(...)` | `Path(out).write_text(...)` in `main()` | Optional output persistence |

-| `@vars` (shared state) | `shared` dict passed through `flow.run(shared)` | All inter-node data lives here |

-| `RETURN @generated_answer WITH status="default"` | `return "default"` from each `post()` + final `shared["generated_answer"]` | `"default"` token routes to next node |

-| `WHILE` | *(absent)* | No iterative refinement loop |

-| `EVALUATE` | *(absent)* | No conditional branching |

-| `EXCEPTION WHEN` | *(absent)* | Errors propagate from API calls unhandled |

+| `WORKFLOW RAGPipeline` | `build_rag_pipeline() → Flow(start=chunk)` | Linear chain; all nodes connected with `>>` (default action) |

+| `INPUT @documents LIST, @query TEXT, @output_path TEXT := ""` | `run_rag_pipeline(documents, query, output_path="")` signature | `shared` dict initialized with all three inputs |

+| `OUTPUT @generated_answer TEXT` | `return shared["generated_answer"]` | Caller gets string directly; `status` remains in `shared` |

+| `CALL chunk_documents(@documents) INTO @texts` | `ChunkDocumentsNode.exec()` — `re.split(r"\n\n+", ...)` per doc | Falls back to whole-doc string if no double-newline found |

+| `CALL embed_documents(@texts) INTO @embeddings` | `EmbedDocumentsNode.exec()` — token-frequency vectors, L2-normalised | Returns `{"embeddings": np.array, "vocab": dict}` bundle |

+| `CALL create_faiss_index(@embeddings) INTO @index` | `CreateFaissIndexNode.exec()` — no FAISS; wraps matrix+vocab as dict | Name preserved from SPL; implementation is pure numpy |

+| `CALL embed_query(@query) INTO @query_embedding` | `EmbedQueryNode.exec()` — same vocabulary, L2-normalised | Uses `shared["index"]["vocab"]` for dimension consistency |

+| `CALL retrieve_document(@index, @query_embedding, @texts) INTO @retrieved_document` | `RetrieveDocumentNode.exec()` — `np.argmax(matrix @ qvec)` | Returns empty string if `matrix.shape[0] == 0` |

+| `GENERATE generate_answer(@query, @retrieved_document) INTO @generated_answer` | `GenerateAnswerNode.exec()` → `_claude_cli(prompt)` | Single LLM call; free-form prose answer |

+| `EVALUATE @output_path WHEN contains(".") THEN CALL write_file(...)` | `WriteOutputNode.exec()` — `if "." in output_path: open(...).write(...)` | Also creates parent dirs via `os.makedirs(..., exist_ok=True)` |

+| `@write_result := "skipped"` | `return "skipped"` in the else branch of `WriteOutputNode.exec()` | Stored in `shared["write_result"]` |

+| `RETURN @generated_answer WITH status = "complete"` | `shared["status"] = "complete"` in `WriteOutputNode.post()` | `run_rag_pipeline()` returns `shared["generated_answer"]` string |

+| `CREATE FUNCTION generate_answer(query, retrieved_document)` | Module-level `generate_answer(query, retrieved_document)` calling `_claude_cli` | Prompt template embedded as a multi-line f-string |

+| Adapter: `claude_cli`, model: `sonnet` | `subprocess.run(["claude", "-p", prompt, "--model", "sonnet"])` | `_claude_cli` helper with configurable model string |

+

+---

 

 ## 3. Logical Functions / Prompts

 

-**ChunkDocuments**

-- Role: Preprocesses raw documents into retrieval-sized units before embedding.

-- Conventions: Fixed-size chunking at 2000 characters; no overlap; returns a list of strings. Implemented as a `BatchNode` so PocketFlow maps `exec` over each document independently.

+### `generate_answer`

+- **Role:** Single synthesis call. Given the retrieved document chunk as context, produces a prose answer to the query.

+- **Prompt conventions:** Instructs the model to answer solely from provided context; explicitly asks it to acknowledge when context is insufficient rather than hallucinating.

+- **Output:** Free-form prose; no structured format.

 

-**EmbedDocuments**

-- Role: Converts each text chunk into a dense float32 vector using the OpenAI `text-embedding-ada-002` model.

-- Conventions: Batch node; results are stacked via `np.array(exec_res_list, dtype=np.float32)` into a 2-D matrix stored in `@embeddings`.

+### Tool calls (deterministic, no LLM)

+- `chunk_documents(docs)` — splits on `\n\n+`; falls back to whole-doc. Pure Python.

+- `embed_documents(texts)` — bag-of-words frequency vectors, L2-normalised. Pure numpy.

+- `create_faiss_index(embeddings)` — identity passthrough wrapping matrix + vocab. Pure numpy.

+- `embed_query(query, vocab)` — same tokenisation as `embed_documents`, same vocab. Pure numpy.

+- `retrieve_document(index, query_vec, texts)` — cosine argmax via `matrix @ qvec`. Returns `texts[best_idx]`.

+- `write_file(path, content)` — `open(path, "w").write(content)` with `os.makedirs` for nested paths.

 

-**CreateIndex**

-- Role: Builds the offline searchable artifact — a FAISS `IndexFlatL2` — from the embedding matrix.

-- Conventions: No prompt; pure deterministic CALL. Dimension inferred from `embeddings.shape[1]`. Index stored in `@index`.

-

-**EmbedQuery**

-- Role: Projects the user's query into the same vector space as the document chunks.

-- Conventions: Same embedding model as `EmbedDocuments`. Output reshaped to `(1, dim)` for FAISS compatibility.

-

-**RetrieveDocument**

-- Role: Finds the single nearest chunk to the query vector.

-- Conventions: `k=1` nearest-neighbor search; returns `{text, index, distance}` dict stored in `@retrieved_document`. No LLM involved.

-

-**GenerateAnswer**

-- Role: The sole GENERATE step; produces the final natural-language answer.

-- Prompt template:

-  ```

-  Briefly answer the following question based on the context provided:

-  Question: {query}

-  Context: {retrieved_document.text}

-  Answer:

-  ```

-- Conventions: Instructs brevity ("Briefly"); injects `{query}` and `{context}` slots; no sentinel tokens, no scoring rubric, no structured output format — plain text answer expected.

+---

 

 ## 4. Control Flow

 

 ```

-WORKFLOW offline_indexing

-  CALL ChunkDocuments(@texts) INTO @texts          -- batch, replaces original texts with chunks

-  CALL EmbedDocuments(@texts) INTO @embeddings     -- batch, one embedding per chunk

-  CALL CreateIndex(@embeddings) INTO @index        -- builds FAISS L2 index

-  RETURN WITH status="done"

+INPUT @documents LIST, @query TEXT, @output_path TEXT := ""

 

-WORKFLOW online_query

-  CALL EmbedQuery(@query) INTO @query_embedding

-  CALL RetrieveDocument(@query_embedding, @index, @texts) INTO @retrieved_document

-  GENERATE GenerateAnswer(@query, @retrieved_document) INTO @generated_answer

-  -- optional side-effect:

-  CALL write_file(@out, @query, @generated_answer)

-  RETURN @generated_answer WITH status="done"

+CALL chunk_documents(@documents)      → @texts

+CALL embed_documents(@texts)          → @embeddings  (numpy TF-IDF vectors)

+CALL create_faiss_index(@embeddings)  → @index       (matrix + vocab dict)

+CALL embed_query(@query)              → @query_embedding

+CALL retrieve_document(@index, @query_embedding, @texts) → @retrieved_document

+

+GENERATE generate_answer(@query, @retrieved_document) → @generated_answer  [LLM]

+

+EVALUATE @output_path

+  WHEN contains(".") THEN

+    CALL write_file(@output_path, @generated_answer) → @write_result

+  ELSE

+    @write_result := "skipped"

+END

+

+RETURN @generated_answer WITH status = "complete"

 ```

 

-No WHILE loop — both workflows execute their nodes exactly once in sequence. No EVALUATE branch — `RetrieveDocument` always returns one result and `GenerateAnswer` always runs. Termination is guaranteed by the finite linear chain. The `"default"` action token returned by each `post()` method is the PocketFlow equivalent of an unconditional advance to the next node.

+**Observed run (2026-05-04):** Query `"What is PocketFlow?"` against 5 sample documents → `status=complete`. Answer correctly identified PocketFlow as "a minimalist 100-line LLM framework for Python" from the retrieved chunk; noted that further detail would require additional sources.

+

+---

 

 ## 5. How to Regenerate as SPL

 

 ```bash

-# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)

-spl3 text2spl --description "<paste Section 0 here>" --mode workflow

+# Step 1 — regenerate SPL from this spec

+spl3 text2spl --description "$(sed -n '/^## 0\./,/^---/p' S5-rag-claude_cli-sonnet-2-spec.md)" \

+    --mode workflow --adapter claude_cli

 

-# Step 2 — compile to any target

-spl3 splc compile <output.spl> --lang python/pocketflow

-spl3 splc compile <output.spl> --lang python/langgraph

-spl3 splc compile <output.spl> --lang go

+# Step 2 — run (requires tools.py with chunk/embed/retrieve implementations)

+spl3 run RAGPipeline.spl --adapter claude_cli \

+    --param documents="[...]" --param query="What is PocketFlow?"

+

+# Step 3 — recompile to any target

+spl3 splc compile RAGPipeline.spl --lang python/pocketflow --llm \

+    --adapter claude_cli --model sonnet

+spl3 splc compile RAGPipeline.spl --lang python/langgraph

+spl3 splc compile RAGPipeline.spl --lang go

 ```

-

-**Regeneration notes:**

-- The two WORKFLOWs (`offline_indexing`, `online_query`) share `@vars`; `text2spl` should be told they run sequentially against the same shared store, not as independent pipelines.

-- `EmbedDocuments` and `ChunkDocuments` must be flagged as **batch** functions so the compiler emits `BatchNode` (PocketFlow) or a `map` step (LangGraph) rather than a single-call node.

-- The only `GENERATE` call is `GenerateAnswer`; the embedding and FAISS calls are `CALL` (deterministic tool calls), not LLM generations — preserve this distinction in the SPL source to avoid the compiler wrapping them in LLM retry logic.

-- There is no WHILE or EVALUATE to reconstruct; if `text2spl` inserts them by default, remove them manually before compiling.
```
---

*Generated by SPL semantic comparison tool*