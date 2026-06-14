## Summary

This workflow implements an interactive chat assistant that maintains both a short-term sliding window of recent exchanges and a long-term vector memory of archived conversations. When the user asks something, the system retrieves the single most semantically relevant past exchange from the archive and injects it into the LLM context alongside the three most recent pairs. Non-technical stakeholders can think of it as a personal assistant that never forgets what you've told it, even across hundreds of exchanges.

---

## Detailed Specification

### 1. Purpose

Provide a persistent, context-aware conversational agent that combines a fixed-size recent-message window with embedding-based retrieval of archived conversations so the LLM always has the most relevant history regardless of session length.

---

### 2. High-level Description

The workflow is an infinite interactive loop built on four logical functions: `get_user_question`, `retrieve_relevant`, `generate_answer`, and `embed_and_archive`. On each turn, `get_user_question` reads a line from stdin and appends it to the shared `@messages` list; if the user types "exit" the workflow terminates immediately. `retrieve_relevant` then embeds the latest user message using an embedding model and performs a nearest-neighbor search (k=1) over a persistent `@vector_index` of archived conversation pairs, storing the best match in `@retrieved_conversation`; if the archive is empty it skips retrieval silently. `generate_answer` assembles a prompt context that injects the retrieved pair as a framing system message followed by the last three live conversation pairs (six messages), calls the LLM via GENERATE, and appends the response to `@messages`. After answering, the workflow EVALUATE`s message count: WHEN `len(@messages) > 6` THEN it RETURN`s with status="embed", routing to `embed_and_archive`; otherwise it loops directly back to `get_user_question`. `embed_and_archive` pops the oldest user-assistant pair from `@messages`, embeds the combined text, stores the vector in `@vector_index`, and saves the raw conversation in `@vector_items`, then loops back. The entire cycle repeats via WHILE the user has not typed "exit", maintaining a bounded active window while growing an unbounded searchable archive.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW chat_with_memory` | `create_chat_flow()` + `Flow(start=question_node)` | Top-level orchestration; shared dict is the SPL store |
| `CREATE FUNCTION get_user_question` | `GetUserQuestionNode.exec()` — `input("\nYou: ")` | Reads stdin; returns `None` on "exit" to terminate |
| `CREATE FUNCTION retrieve_relevant` | `RetrieveNode.exec()` — `get_embedding()` + `search_vectors()` | Tool calls, not LLM generation; k=1 neighbor search |
| `CREATE FUNCTION generate_answer` | `AnswerNode.exec()` — `call_llm(messages)` | The only true `GENERATE` call; constructs full context before calling |
| `CREATE FUNCTION embed_and_archive` | `EmbedNode.exec()` — `get_embedding()` + `add_vector()` | Side-effect tool calls; no LLM text generation |
| `GENERATE generate_answer(...) INTO @response` | `call_llm(context)` in `AnswerNode.exec()` | Context = system framing + retrieved pair + last 6 messages |
| `CALL get_embedding(...) INTO @vec` | `get_embedding(text)` in `RetrieveNode` and `EmbedNode` | External embedding API call |
| `CALL search_vectors(...) INTO @match` | `search_vectors(index, query_vec, k=1)` in `RetrieveNode` | Returns indices + distances |
| `CALL add_vector(...) INTO @pos` | `add_vector(index, embedding)` in `EmbedNode` | Mutates `@vector_index` in shared state |
| `@messages` | `shared["messages"]` | Mutable list; bounded to last 6 entries after archiving |
| `@vector_index` | `shared["vector_index"]` | FAISS (or similar) index; grows unboundedly |
| `@retrieved_conversation` | `shared["retrieved_conversation"]` | Nullable; set each turn, read by `generate_answer` |
| `@vector_items` | `shared["vector_items"]` | Parallel list of raw conversation pairs indexed alongside vectors |
| `WHILE user_has_not_exited DO ... END` | Cyclic PocketFlow edges looping back to `GetUserQuestionNode` | Loop terminates when `GetUserQuestionNode.post()` returns `None` |
| `EVALUATE @messages WHEN len > 6 THEN ... END` | `AnswerNode.post()` branching on `len(shared["messages"]) > 6` | Drives "embed" vs "question" routing — non-trivial branch |
| `RETURN @response WITH status="embed"` | `AnswerNode.post()` returning `"embed"` | Routes to archive node; non-default, load-bearing status |
| `EXCEPTION WHEN TerminationSignal THEN END` | `GetUserQuestionNode.post()` returning `None` on "exit" input | Halts the PocketFlow execution loop |

---

### 4. Logical Functions / Prompts

**`get_user_question`**
- Role: Session gate — collects the turn's input and initializes shared state on first run.
- Conventions: No LLM call. Emits `None` as a sentinel to signal loop termination. Appends `{"role": "user", "content": ...}` to `@messages`.

**`retrieve_relevant`**
- Role: Memory lookup — converts the current query to a dense vector and finds the nearest archived exchange.
- Conventions: No LLM call; pure vector math. Skips gracefully when `@vector_index` is empty. Stores a single `{"conversation": [...], "distance": float}` result in `@retrieved_conversation`. Prints a truncated preview and cosine distance for observability.

**`generate_answer`**
- Role: Core LLM generation step — the only node that calls the chat completion API.
- Key prompt conventions:
  - Context order: (optional) system framing header → retrieved pair → system framing footer → last 6 live messages.
  - System message sentinels: `"The following is a relevant past conversation..."` and `"Now continue the current conversation:"` bracket the injected archive excerpt to prevent the model from confusing past and present.
  - Output format: raw assistant prose; no structured tokens or scoring.

**`embed_and_archive`**
- Role: Memory writer — evicts the oldest conversation pair from the live window and stores it in the vector archive.
- Conventions: No LLM call. Concatenates `"User: {u} Assistant: {a}"` into a single string before embedding. Maintains `@vector_items` as a parallel list so retrieved indices map directly to raw conversation pairs. Prints position and total count for observability.

---

### 5. Control Flow

```
[start]
  └─► get_user_question
        │ (user types text)
        ▼
      retrieve_relevant          ← skips if archive empty
        │
        ▼
      generate_answer
        │
        EVALUATE len(@messages) > 6
        ├─ YES ─► embed_and_archive ─► get_user_question  (loop)
        └─ NO  ──────────────────────► get_user_question  (loop)

  EXCEPTION: get_user_question receives "exit"
        └─► RETURN WITH status=None  →  [terminate]
```

The live window is always trimmed to ≤ 6 messages (3 pairs) before the next turn begins. The archive grows monotonically; retrieval cost is O(log n) with a FAISS index.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (paste Section 2 "High-level Description" as input)
spl3 text2spl --description "The workflow is an infinite interactive loop built on four logical functions: get_user_question, retrieve_relevant, generate_answer, and embed_and_archive. On each turn, get_user_question reads a line from stdin and appends it to the shared @messages list; if the user types 'exit' the workflow terminates immediately. retrieve_relevant embeds the latest user message using an embedding model and performs a nearest-neighbor search (k=1) over a persistent @vector_index of archived conversation pairs, storing the best match in @retrieved_conversation; if the archive is empty it skips retrieval silently. generate_answer assembles a prompt context that injects the retrieved pair as a framing system message followed by the last three live conversation pairs (six messages), calls the LLM via GENERATE, and appends the response to @messages. After answering, the workflow evaluates message count: WHEN len(@messages) > 6 THEN it returns with status='embed', routing to embed_and_archive; otherwise it loops directly back to get_user_question. embed_and_archive pops the oldest user-assistant pair from @messages, embeds the combined text, stores the vector in @vector_index, and saves the raw conversation in @vector_items, then loops back. The entire cycle repeats via WHILE the user has not typed 'exit', maintaining a bounded active window while growing an unbounded searchable archive." --mode workflow

# Step 2 — compile to any target
spl3 splc compile chat_with_memory.spl --lang python/pocketflow
spl3 splc compile chat_with_memory.spl --lang python/langgraph
spl3 splc compile chat_with_memory.spl --lang go
```