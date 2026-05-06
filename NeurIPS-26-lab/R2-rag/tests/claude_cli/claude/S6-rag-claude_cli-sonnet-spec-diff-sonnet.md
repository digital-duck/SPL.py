# File Comparison Report

**Files Compared:**
- File 1: `S1-rag-claude_cli-sonnet-1-spec.md` (.md)
- File 2: `S5-rag-claude_cli-sonnet-2-spec.md` (.md)
- **Timestamp:** 2026-05-04 09:36:11
- **Active Modes:** llm, git-diff

---
## LLM Semantic Analysis

**Adapter:** claude_cli
**Model:** claude-sonnet-4-6

## Summary

Both specs document a RAG pipeline as SPL workflows compiled to PocketFlow, but they represent fundamentally different design philosophies. **File 2 is the stronger spec overall** — it is more honest about its implementation, covers more SPL constructs (including `EVALUATE` and `INPUT`/`OUTPUT` declarations), and includes empirical run evidence. File 1 is architecturally richer (two-workflow separation, real neural embeddings) but describes a more expensive dependency stack and omits several SPL features that File 2 captures.

---

## Content Analysis

### File 1 Strengths

- **Two-workflow architecture** (`offline_indexing` + `online_query`) is semantically correct RAG design — separating indexing from serving is production-relevant and maps cleanly to real deployment patterns.
- **Real embedding quality**: Uses OpenAI `text-embedding-ada-002` + FAISS `IndexFlatL2`, so retrieval accuracy is genuinely semantic, not lexical.
- **BatchNode pattern** is explicitly described for both `ChunkDocuments` and `EmbedDocuments`, and the spec explains *why* (PocketFlow maps `exec` over each document independently) — this is pedagogically valuable.
- **Prompt template** is fully quoted with slot labels (`{query}`, `{context}`), making it directly reproducible.
- **Construct mapping table** is the most complete: covers `WHILE`, `EVALUATE`, and `EXCEPTION WHEN` as absent-but-noted rows, which is good negative documentation.

### File 2 Strengths

- **EVALUATE construct** is present and mapped to a Python `if` guard — File 2 covers a SPL branch that File 1 entirely omits.
- **INPUT/OUTPUT declarations** are explicitly documented in the mapping table, capturing the full SPL workflow signature.
- **Intellectual honesty**: The spec explicitly flags the mismatch between the SPL CALL name (`create_faiss_index`) and the pure-numpy implementation — "pure numpy, no FAISS dependency despite the SPL CALL name." This prevents downstream confusion.
- **Observed run evidence** (2026-05-04, `"What is PocketFlow?"` → `status=complete`) grounds the spec in empirical reality, not just design intent.
- **WriteOutputNode as a first-class node** rather than a side-effect `CALL` in `main()` — better models the SPL construct it represents.
- **Regeneration command** in Section 5 uses a live `sed` pipeline to extract the description, making it directly executable.
- **`generate_answer` prompt convention** explicitly requires the model to acknowledge insufficient context rather than hallucinate — a meaningful quality improvement over File 1's "Briefly answer" instruction.

### Common Elements

- Both describe a 6-step RAG pipeline: chunk → embed docs → build index → embed query → retrieve → generate
- Both map SPL constructs to PocketFlow nodes with `"default"` action routing
- Both document `@vars` / `shared` dict as the inter-node state mechanism
- Both note absence of `WHILE` and `EXCEPTION WHEN`
- Both use `GENERATE` for exactly one LLM call (`GenerateAnswer` / `generate_answer`)
- Both document deterministic tool calls (`CALL`) vs. generative calls (`GENERATE`) as a meaningful distinction

---

## Detailed Comparison

### Structure & Organization

| Dimension | File 1 | File 2 |
|---|---|---|
| Workflow count | 2 (`offline_indexing`, `online_query`) | 1 (`RAGPipeline`) |
| Section separators | None between sections | `---` horizontal rules give visual breathing room |
| Node count | 6 across 2 workflows | 7 in a single workflow (adds `WriteOutputNode`) |
| Subsection headers | Flat list under Section 3 | `###` headers per function + "Tool calls" grouping |

File 1's two-workflow split is architecturally motivated — offline indexing genuinely belongs in a separate execution phase. However, for a spec document, File 2's single-workflow view is easier to read linearly. File 2 also uses horizontal rules that make section boundaries unambiguous; File 1 relies only on `##` headings.

### Logic & Completeness

File 1's control flow pseudocode in Section 4 is accurate but minimal — it shows the two workflows in isolation without showing how they compose (who calls `offline_indexing` before `online_query`?). The shared `@shared` state is mentioned in the table but never shown in the pseudocode.

File 2's Section 4 pseudocode is self-contained: it shows the full `INPUT` declaration, every `CALL`/`GENERATE`/`EVALUATE` step, the `ELSE` branch, and the `RETURN`. This is unambiguously complete.

**EVALUATE coverage is a significant gap in File 1.** The `write_file` side-effect is shown as a bare `CALL` in the pseudocode, with no conditional guard — but the actual code has a condition (`if output_path`). File 2 correctly models this as `EVALUATE @output_path WHEN contains(".")`.

**Error handling**: Both specs note the absence of `EXCEPTION WHEN`. File 1 mentions it as an absent row in the table. File 2 says "failures propagate as Python exceptions" — cleaner phrasing for the same fact.

### Quality & Sophistication

File 1 is architecturally more sophisticated:
- Two-workflow separation reflects production RAG design (index once, query many times)
- Real neural embeddings (ada-002) give genuine semantic retrieval
- `BatchNode` pattern is correctly identified and explained

File 2 is implementation-quality more sophisticated for its scope:
- TF-IDF bag-of-words is a deliberate simplification to eliminate external API dependencies — valid for a self-contained demo
- The `generate_answer` prompt is strictly better: it instructs the model to acknowledge context gaps rather than fabricate, which is a meaningful safety property
- The observed run data makes File 2 a *validated* spec rather than a design document

File 1's embedding approach (OpenAI API + FAISS) introduces two non-trivial external dependencies and costs. File 2's pure-numpy approach works offline and is reproducible by anyone with `claude` CLI — a deliberate tradeoff that the spec acknowledges honestly.

### Syntax & Technical Accuracy

**File 1 issues:**
- Section 4 pseudocode uses `RETURN WITH status="done"` for both workflows, but Section 2 uses `status="default"` for node transitions — conflates workflow-exit status with PocketFlow action tokens.
- `CALL write_file(...)` appears in Section 4 pseudocode without a conditional, but the prose in Section 3 says "when an output path is supplied" — inconsistency.
- `CREATE FUNCTION` is used in both the description and mapping table, but it is not a standard SPL construct — likely should be `PROCEDURE` or just described as a node definition.

**File 2 issues:**
- The `EVALUATE @output_path WHEN contains(".")` heuristic (file-extension detection) is fragile — a bare filename like `output` would be skipped, a path like `/dev/null` would be written. The spec acknowledges "file-extension heuristic" but does not flag this as a limitation.
- The regeneration command in Section 5 uses `sed -n '/^## 0\./,/^---/p'` which would capture only through the first `---` separator — this may not extract all of Section 0 if the section itself contains `---`.

**File 2's mapping table is more complete**: it documents `INPUT`/`OUTPUT` declarations, `@write_result := "skipped"`, and the adapter/model row (`claude_cli` → `subprocess.run(["claude", ...])`), none of which appear in File 1.

---

## Recommendations

**1. Best Choice: File 2**

File 2 is the better spec for its stated purpose. It covers more SPL constructs faithfully, is empirically validated, is self-contained (no OpenAI key or FAISS install required), and is more honest about its implementation choices. For a NeurIPS lab demo or teaching context, these properties dominate.

**2. Improvements for File 1:**

- Add an `EVALUATE` row to the mapping table (even if the condition is `output_path != ""`), and show the conditional guard in the Section 4 pseudocode.
- Add `INPUT:`/`OUTPUT:` declarations to both workflows in the pseudocode so the workflow signatures are explicit.
- Show how `offline_indexing` and `online_query` compose — a "caller pseudocode" snippet showing `CALL offline_indexing(...); CALL online_query(...)` in sequence.
- Replace `CREATE FUNCTION` with canonical SPL terminology (`PROCEDURE` or node description).
- Fix the `status="done"` vs `status="default"` inconsistency.

**3. Hybrid Approach:**

Take File 2's spec structure and SPL construct coverage, then graft in File 1's two-workflow architecture and BatchNode documentation:

- Split the single `RAGPipeline` workflow into `IndexCorpus` (offline) and `QueryCorpus` (online), with explicit composition shown in a caller snippet.
- Keep File 2's `EVALUATE` for output handling, `INPUT`/`OUTPUT` declarations, and adapter/model row in the mapping table.
- Keep File 2's `generate_answer` prompt (acknowledge gaps rather than hallucinate).
- Document `ChunkDocumentsNode` and `EmbedDocumentsNode` as `BatchNode` subclasses (from File 1), since the batch distinction matters for PocketFlow compilation.
- Keep File 2's observed run evidence as a validation anchor.

---

## Scoring

| Dimension | File 1 | File 2 |
|---|---|---|
| **Structure** | 7/10 | 8/10 |
| **Logic** | 6/10 | 9/10 |
| **Quality** | 8/10 | 8/10 |
| **Overall** | 7/10 | 8.5/10 |

File 1 loses points on Logic primarily for the missing `EVALUATE` coverage, the unresolved composition story between its two workflows, and the status-token inconsistency. File 2 loses a half-point on Structure for the fragile file-extension heuristic and the `sed` command edge case. Both are professional-quality documents — File 2 simply covers more ground with fewer gaps.
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