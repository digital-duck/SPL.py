## Summary

Knowledge Synthesis is a RAG-Writer workflow that turns raw text into structured, reusable knowledge. An LLM distills the text into exactly three bullet-point insights, which are then persisted to both a log file and a vector store so every future query benefits from the new material. It is most useful to teams building self-improving retrieval systems where agents are expected to contribute back to the shared knowledge base, not just consume it.

---

## Detailed Specification

### 1. Purpose

Ingest raw text, extract three concise LLM-synthesized insights, and persist them to a vector store so the knowledge base grows automatically as new information arrives.

---

### 2. High-level Description

The workflow implements the **RAG-Writer pattern**: a single LLM call extracts knowledge, and deterministic side-effect CALLs persist it — no LLM tokens are spent on storage. The `synthesize` FUNCTION is a tightly-constrained prompt template that instructs a knowledge-engineer persona to produce exactly three one-sentence bullet points covering novel claims, methods, or results from the supplied text. After the GENERATE step captures insights into `@insights`, two CALLs handle persistence: `write_file` logs the markdown to disk (result discarded via `INTO NONE`), and `rag_update` stores the insights alongside their source provenance, returning an `@status` token. An EVALUATE on `@status` branches logging to INFO on success or WARN otherwise — both paths then converge to a RETURN that surfaces the status as the workflow OUTPUT. A `GenerationError` EXCEPTION handler short-circuits the entire pipeline and returns `status='error'` with a `reason` field so callers can distinguish synthesis failures from storage failures.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW knowledge_synthesis` | `WORKFLOW <name>` | Declares the named orchestration unit with `INPUT:`/`OUTPUT:` declarations |
| `CREATE FUNCTION synthesize(raw_text)` | `CREATE FUNCTION <name>` | Reusable prompt template; `{raw_text}` is the single interpolation slot |
| `GENERATE synthesize(@raw_text) INTO @insights` | `GENERATE fn(...) INTO @var` | Single LLM call; result bound to `@insights` |
| `CALL write_file(...) INTO NONE` | `CALL tool(...) INTO NONE` | Side-effect only; return value explicitly discarded |
| `CALL rag_update(...) INTO @status` | `CALL tool(...) INTO @var` | Deterministic vector-store write; return value (`@status`) drives downstream branch |
| `EVALUATE @status WHEN contains('success') THEN ... ELSE ... END` | `EVALUATE @var WHEN contains('...') THEN ... ELSE ... END` | Branches logging severity; both paths converge immediately after |
| `RETURN f'Operation: ...' WITH status = @status` | `RETURN @var WITH k=v, ...` | Non-trivial: propagates the storage-layer status token as workflow OUTPUT |
| `EXCEPTION WHEN GenerationError THEN ...` | `EXCEPTION WHEN <Type> THEN ...` | Typed handler; returns `status='error', reason='generation_error'` to caller |
| `@raw_text`, `@insights`, `@status`, `@log_dir` | SPL `@vars` | Shared mutable state passed between steps within the workflow frame |

---

### 4. Logical Functions / Prompts

#### `synthesize`

- **Role:** The sole LLM call in the workflow; transforms free-form text into a structured insight list.
- **Persona:** "knowledge engineer" — instructs the model to act as a curator, not a summarizer.
- **Output format:** Exactly three bullet points, one sentence each, no sub-bullets. Strict count constraint prevents verbose or sparse outputs that would degrade RAG retrieval quality.
- **Scope constraint:** Only novel claims, methods, or results — explicitly excludes background knowledge to keep the vector store signal-dense.
- **No sentinel tokens or scoring:** This is an extraction prompt, not a judge or evaluator. The downstream `CALL rag_update` determines success, not the LLM output itself.

---

### 5. Control Flow

```
INPUT @raw_text
    │
    ▼
GENERATE synthesize(@raw_text) → @insights          [single LLM call]
    │
    ▼
CALL write_file(insights.md)    → discarded          [disk side-effect]
    │
    ▼
CALL rag_update(@insights, src) → @status            [vector store write]
    │
    ▼
EVALUATE @status
    ├─ contains('success') → LOG INFO
    └─ else               → LOG WARN
    │  (both paths converge)
    ▼
RETURN WITH status=@status                           [surface to caller]

EXCEPTION GenerationError → RETURN status='error', reason='generation_error'
```

There is no WHILE loop — the workflow is a single-pass extraction and store. The EVALUATE drives only logging verbosity; the RETURN always fires regardless of branch. The only hard fork is the EXCEPTION handler, which exits early without reaching the RETURN.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Ingest raw text, extract three concise LLM-synthesized insights using a knowledge-engineer prompt, persist them to a log file via a file-write CALL, and store them in a vector store via a rag_update CALL that returns a status token. EVALUATE the status for logging, RETURN it as workflow output, and handle GenerationError with a typed EXCEPTION." --mode workflow

# Step 2 — compile to any target
spl3 splc compile knowledge_synthesis.spl --lang python/pocketflow
spl3 splc compile knowledge_synthesis.spl --lang python/langgraph
spl3 splc compile knowledge_synthesis.spl --lang go
```