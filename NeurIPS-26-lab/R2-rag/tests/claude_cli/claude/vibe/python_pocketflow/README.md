## RAG Pipeline — PocketFlow Implementation

A four-node Retrieval-Augmented Generation (RAG) pipeline built with PocketFlow.  
The pipeline ingests a corpus of plain-text documents, builds a TF-IDF vector index,
retrieves the most relevant passages for a user query, and generates a grounded answer
via the Anthropic Claude API.

```
DocumentIngestor → IndexBuilder → QueryRetriever → AnswerSynthesizer
```

### Requirements

```bash
pip install pocketflow anthropic scikit-learn numpy
```

### Setup — environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | — | Your Anthropic API key |
| `LLM_MODEL` | No | `claude-opus-4-7` | Claude model to use for synthesis |

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export LLM_MODEL="claude-opus-4-7"   # optional
```

### Usage

**Run the built-in demo:**

```bash
python solution.py
```

**Expected output (abbreviated):**

```
2026-05-06 12:00:00 INFO Doc 1/4 → 3 chunks
...
2026-05-06 12:00:00 INFO Total chunks after ingestion: 11
2026-05-06 12:00:00 INFO Building TF-IDF index over 11 chunks …
2026-05-06 12:00:00 INFO Index shape: (11, 312)
2026-05-06 12:00:00 INFO Retrieving top-3 chunks for query: 'What is chunking …'
  [1] chunk #7  score=0.6142
  [2] chunk #8  score=0.4381
  [3] chunk #3  score=0.2017
2026-05-06 12:00:00 INFO Calling LLM to synthesize final answer …

--- Answer ---
Chunking is the process of splitting documents into fixed-size or semantically
coherent segments before indexing …
```

**Programmatic usage:**

```python
from solution import run_rag

docs = ["Your document text here …", "Second document …"]
result = run_rag(docs, query="What does document 1 say?", top_k=3)
print(result["answer"])
```

### Workflow logic — step by step

1. **DocumentIngestor** — iterates over the `documents` list, splits each one into
   overlapping text windows (`chunk_size` chars, `overlap` chars of overlap, sentence-
   boundary-aware), and stores the flat list in `shared["chunks"]`.

2. **IndexBuilder** — fits a `TfidfVectorizer` (unigrams + bigrams, sublinear TF,
   up to 20 k features) over all chunks and stores the fitted vectorizer and the sparse
   TF-IDF matrix in `shared`.

3. **QueryRetriever** — transforms the query with the same vectorizer, computes cosine
   similarity against every chunk, and writes the top-k passages (by score) into
   `shared["retrieved_chunks"]` and a formatted `shared["context"]` string.

4. **AnswerSynthesizer** — constructs a grounded-answer prompt from the retrieved
   context and the query, calls Claude via `call_llm()`, and stores the result in
   `shared["answer"]`.

The `shared` dict is the single mutable state object that flows through all nodes,
following PocketFlow's ETL pattern (prep → exec → post per node).

---