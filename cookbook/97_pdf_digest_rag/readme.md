# Recipe 97: PDF Digest via RAG (planned)

Given any PDF document (not just arXiv papers), answer a fixed set of digest
questions by retrieving the most relevant chunks per question rather than
summarizing every section in sequence. This makes the digest quality independent
of how many chunks the PDF produces and eliminates the WHILE-loop iteration cap
that recipe 89 hit on appendix-heavy papers.

## Motivation

Recipe 89 (`89_arxiv_digest_eaai27`) uses a MAP-REDUCE pattern: summarize every
section independently (map), then reduce into one digest. This breaks down when:

- A PDF has more sections than the SPL runtime's WHILE loop cap (observed:
  71 sections on a paper with a large cookbook appendix — see
  `89_arxiv_digest_eaai27/readme.md` "Fixed issues", 2026-08-20).
- Many chunks are irrelevant to the digest (appendix examples, table rows,
  boilerplate) and waste LLM calls.
- The PDF is not an academic paper — it may have no "Conclusion" section or a
  completely different structure.

The RAG approach fixes all three: it retrieves only the K chunks most relevant
to each digest question, so the number of LLM calls equals the number of digest
questions (typically 5–8), not the number of chunks (which can be hundreds).

## Proposed pattern

```
download_or_load_pdf(path_or_url) → pdf_path
semantic_chunk_plan(pdf_path, max_chars) → chunks[]     # same tool as recipe 89
embed_chunks(chunks[]) → embeddings[]                   # NEW: one Ollama embed call per chunk
                                                        #   model: nomic-embed-text (already
                                                        #   installed) or any embed model
FOR each question in digest_schema:
    retrieve_top_k(embeddings[], question, k) → context_chunks[]   # cosine similarity
    GENERATE digest_section_writer(question, context_chunks) INTO @answer
assemble_digest(answers[]) → one JSON object
```

## Digest schema (the fixed questions)

Unlike recipe 89 (which mirrors the paper's own section structure), this recipe
answers a fixed schema regardless of how the PDF is organized:

| Field | Question posed to the retriever + LLM |
|---|---|
| `problem` | What problem or need does this document address? |
| `approach` | What method, design, or solution does it propose? |
| `evidence` | What results, data, or arguments support the claims? |
| `limitations` | What are the stated limitations, caveats, or open questions? |
| `contributions` | What are the 3 most important takeaways? (bullet form) |

The schema is defined as a JSON array of `{field, question}` objects, passed
as a workflow parameter so callers can substitute domain-specific schemas
(e.g. a legal-document schema, a medical-paper schema) without touching the
`.spl` file.

## New tools needed (to add to tools.spl)

### `embed_chunks(chunks_json, model)`
Calls `POST /api/embeddings` (Ollama) or equivalent for each chunk's text,
returns a JSON array of `{title, text, embedding: float[]}` objects.
In-process numpy cosine similarity is sufficient at this scale (no vector DB
needed for single-document digests).

### `retrieve_top_k(embeddings_json, query, k, model)`
Embeds `query` the same way as chunks, computes cosine similarity against all
chunk embeddings, returns the top-K chunks as a JSON array (same shape as
`semantic_chunk_plan` output, so `get_chunk_field` works unchanged).

### `assemble_digest(answers_json, metadata_json)`
Packages the per-question answers plus document metadata into the final JSON
card. Shape is compatible with recipe 89's `assemble_paper_digest` so the same
frontend `ResultsPanel.vue` can render both.

## Key differences from recipe 89

| | Recipe 89 (MAP-REDUCE) | Recipe 97 (RAG) |
|---|---|---|
| LLM calls per doc | N sections (can be 70+) | fixed (= # digest questions, ~5-8) |
| Input | arXiv URL | any PDF path or URL |
| Structure assumed | academic paper sections | none — schema-driven |
| Abstract | verbatim from arXiv API | extracted from top-K retrieval |
| Iteration limit risk | yes (WHILE loop over N) | no (no WHILE loop) |
| Embedding model needed | no | yes (`nomic-embed-text` or similar) |
| Retrieval quality | N/A | depends on embedding model + K |

## Embedding models available (Ollama, this machine, 2026-08-20)

- `nomic-embed-text` (137M, F16, 768-dim, context 2048) — already installed
- `paraphrase-multilingual` (277M, F16, 768-dim, context 512) — already installed
- `qwen3-embedding:0.6b` (596M, Q8, 1024-dim, context 32768) — already installed

`nomic-embed-text` is the natural first choice (lightweight, well-tested for
RAG). `qwen3-embedding` has a larger context window (32K) which matters if
chunks are long.

## Relationship to recipe 89

Recipe 89 remains the EAAI-27 workshop capstone (it demonstrates MAP-REDUCE
explicitly for pedagogical reasons). Recipe 97 is a standalone general-purpose
PDF digest tool. The two share `semantic_chunk_plan`, `download_arxiv_pdf`
(optionally), and the frontend card shape — recipe 97 should import from a
shared `tools` library rather than copy-paste.
