## Summary

This workflow implements an agent-driven Retrieval Augmented Generation (RAG) system where a large language model actively decides which documents to read before composing its final answer. Rather than blindly fetching the highest-similarity chunks, the agent iterates — inspecting document summaries, choosing one to read, accumulating context, and repeating — until it judges it has gathered enough information. Developers building question-answering systems over curated document stores benefit from more targeted, interpretable retrieval.

---

## Detailed Specification

### 1. Purpose

Answers a user question by letting an LLM agent iteratively select and read documents from a fixed store until it has sufficient context to generate an accurate, grounded response.

---

### 2. High-level Description

This workflow implements the **agentic RAG** pattern using three logical functions arranged in a decision-read loop. The workflow begins by presenting the LLM with the user's question, the list of available document names, and any context gathered so far; this is the **DecideAction** function, which emits a structured YAML response choosing either `read` (naming a specific document) or `answer`. When the decision is `read`, the **ReadDoc** function retrieves that document's full content from an in-memory store and appends it to an accumulating context variable (`@context`). Control then returns to **DecideAction**, forming a WHILE-style loop that continues until the agent emits `answer`. EVALUATE is applied to the YAML output of DecideAction to branch: a `read` decision routes back through ReadDoc, while an `answer` decision exits the loop and enters the **Answer** function, which GENERATE calls the LLM one final time with the full accumulated context to produce the response. No external side-effects (file writes, HTTP calls) occur during retrieval — all state is held in shared variables (`@question`, `@context`, `@doc_to_read`, `@answer`). There is no explicit EXCEPTION handler; document lookup falls back to a "Document not found." sentinel string returned by the store.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW agentic_rag` | `create_agentic_rag_flow()` + `Flow(start=decide)` | Top-level orchestration entry point |
| `CREATE FUNCTION decide_action` | `DecideAction.exec()` | Emits YAML with `action` and optional `doc` fields |
| `CREATE FUNCTION read_doc` | `ReadDoc.exec()` | Pure dict lookup; no LLM call |
| `CREATE FUNCTION answer` | `Answer.exec()` | Final GENERATE call with full context |
| `GENERATE decide_action(...) INTO @decision` | `call_llm(prompt)` in `DecideAction.exec()` | Output parsed from fenced YAML block |
| `GENERATE answer(...) INTO @answer` | `call_llm(...)` in `Answer.exec()` | Uses `@context` and `@question` as inputs |
| `EVALUATE @decision WHEN action='read' THEN ... ELSE ... END` | `DecideAction.post()` returning `"read"` or `"answer"` | Drives the loop vs. exit branch |
| `WHILE action != 'answer' DO ... END` | `decide - "read" >> read; read - "decide" >> decide` | Loop terminates only when LLM emits `action: answer` |
| `RETURN @answer WITH status='complete'` | `Answer.post()` writing `shared["answer"]` | Terminal node; no further routing |
| `@question`, `@context`, `@doc_to_read`, `@answer` | `shared` dict keys | Single mutable state object threaded through all nodes |

---

### 4. Logical Functions / Prompts

**decide_action**
- **Role:** The agent's reasoning core — decides whether to gather more information or answer.
- **Key conventions:** Receives `@question`, `@context` (may be empty), and `list(DOCS.keys())` as available document names. Instructs the LLM to output *only* valid YAML inside a fenced block. Two schemas: `{action: read, doc: <name>}` or `{action: answer}`. The fenced block is parsed by splitting on ` ```yaml ` / ` ``` ` and then `yaml.safe_load()`.

**read_doc**
- **Role:** Side-effect retrieval step — no LLM call; pure document store lookup.
- **Key conventions:** Takes `@doc_to_read`, fetches from `DOCS` dict, returns full text or the sentinel `"Document not found."`. Appends result to `@context` as `\n[{doc_name}]: {content}`.

**answer**
- **Role:** Final synthesis — one LLM call producing the user-facing response.
- **Key conventions:** Prompt is `"Based on this context:\n{@context}\n\nAnswer the following question concisely and accurately: {@question}"`. Result stored directly into `@answer` with no post-processing.

---

### 5. Control Flow

```
START
  │
  ▼
DecideAction  ←──────────────────────────┐
  │  GENERATE decide_action(             │
  │    @question, @context, doc_names    │
  │  ) INTO @decision                    │
  │                                      │
  │  EVALUATE @decision                  │
  │    WHEN action = 'read'  ──────► ReadDoc
  │    WHEN action = 'answer'            │  @doc_to_read ← @decision.doc
  │          │                           │  @context += doc content
  ▼          │                           │
Answer       │                           └── loop back
  GENERATE answer(@question, @context) INTO @answer
  RETURN @answer WITH status='complete'
```

The loop is open-ended: the agent iterates until it self-terminates with `action: answer`. There is no hard iteration cap in this implementation. The `"decide"` action token returned by `ReadDoc.post()` is the loop-back signal, and `"read"` / `"answer"` from `DecideAction.post()` are the branch signals — all three are non-trivial routing decisions.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "This workflow implements the agentic RAG pattern \
using three logical functions arranged in a decision-read loop. The workflow begins \
by presenting the LLM with the user's question, available document names, and any \
context gathered so far (decide_action). The LLM emits structured YAML choosing \
either read (naming a document) or answer. When read, read_doc retrieves the \
document and appends it to @context. Control returns to decide_action, forming a \
WHILE loop until answer is chosen. EVALUATE branches on the YAML output: read \
routes back through read_doc, answer exits to the answer function which GENERATEs \
the final response using full accumulated context." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile agentic_rag.spl --lang python/pocketflow
spl3 splc compile agentic_rag.spl --lang python/langgraph
spl3 splc compile agentic_rag.spl --lang go
```