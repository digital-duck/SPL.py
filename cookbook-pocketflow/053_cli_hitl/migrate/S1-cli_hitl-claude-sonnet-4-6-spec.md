## Summary

This workflow is an interactive command-line joke generator that asks a user for a topic, calls an LLM to produce a one-liner joke, and then requests human approval. If the user dislikes the joke, the system records it and tries again — incorporating all previously rejected jokes into the next generation prompt — until the user approves one. It is a clear, minimal demonstration of a Human-in-the-Loop (HITL) refinement loop for content generation.

---

## Detailed Specification

### 1. Purpose

Generate a topic-specific joke that satisfies the user by iterating LLM calls with accumulated negative feedback until the human explicitly approves.

---

### 2. High-level Description

The workflow opens by collecting a topic string from the user at the command line and storing it in shared state. It then enters a `GENERATE`-and-evaluate cycle: a `generate_joke` function constructs a prompt incorporating the topic and the full list of previously disliked jokes (empty on the first pass), calls the LLM to produce a one-liner, and displays the result. A subsequent human-input step asks the user to approve or reject the joke. This human gate is modelled as an `EVALUATE` branch: if the user responds `yes`, the workflow reaches a terminal `RETURN WITH status="approve"`; if the user responds `no`, the rejected joke is appended to the disliked list and control flows back to `generate_joke`, forming an explicit `WHILE`-style retry loop. The loop has no iteration cap — it runs until human approval is given. No automated LLM judge is involved; the only branching signal is direct user input. There is no exception handling in the implementation beyond basic input validation inside the feedback prompt.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW JokeGenerator` | `create_joke_flow()` + `Flow(start=get_topic_node)` | Top-level orchestration unit |
| `CREATE FUNCTION generate_joke(topic, disliked_jokes)` | `GenerateJokeNode.prep()` building the prompt string | Conditionally injects prior rejections into the prompt |
| `GENERATE generate_joke(...) INTO @current_joke` | `GenerateJokeNode.exec()` calling `call_llm(prompt)` | Single LLM call; result stored in `shared["current_joke"]` |
| `EVALUATE @feedback WHEN contains("yes") THEN ... ELSE ...` | `GetFeedbackNode.post()` branching on `exec_res in ["yes","y"]` | Drives the only real branch: approve → end, disapprove → retry |
| `WHILE user disapproves DO ... END` | `get_feedback_node - "Disapprove" >> generate_joke_node` edge | Loop back to generation on rejection; terminates on approval |
| `RETURN WITH status="approve"` | `return "Approve"` from `GetFeedbackNode.post()` | Non-default token; signals workflow termination |
| `RETURN WITH status="disapprove"` | `return "Disapprove"` from `GetFeedbackNode.post()` | Non-default token; triggers the retry loop |
| `@topic`, `@current_joke`, `@disliked_jokes`, `@user_feedback` | `shared["topic"]`, `shared["current_joke"]`, `shared["disliked_jokes"]`, `shared["user_feedback"]` | Mutable dict passed through all nodes as shared state |

---

### 4. Logical Functions / Prompts

**`get_topic` (GetTopicNode)**
- Role: Collects the user's chosen joke subject; no LLM call, pure human input.
- Conventions: Raw `input()` call; result stored verbatim in `@topic`. No prompt template.

**`generate_joke` (GenerateJokeNode.prep + exec)**
- Role: Core LLM call; produces a one-liner joke from the topic.
- Conventions:
  - First-pass prompt: `"Please generate a one-liner joke about: {topic}. Make it short and funny."`
  - Retry prompt: `"The user did not like the following jokes: [{disliked_str}]. Please generate a new, different joke about {topic}."` — all prior rejections are joined with `"; "` and injected as a negative-example list.
  - Output format: free-form single-sentence joke; no sentinel tokens or scoring.

**`get_feedback` (GetFeedbackNode)**
- Role: Human gate; collects and normalises a binary approval signal.
- Conventions: Accepts `yes/y/no/n` (case-insensitive); loops on invalid input. Maps `yes/y` → `"Approve"` action token, `no/n` → `"Disapprove"` action token and appends the rejected joke to `@disliked_jokes`.

---

### 5. Control Flow

```
START
  → get_topic          (human input → @topic)
  → generate_joke      (LLM call → @current_joke; prompt grows with each retry)
  → get_feedback       (human input → binary signal)
      EVALUATE @feedback:
          "Approve"    → RETURN WITH status="approve"  [END]
          "Disapprove" → append @current_joke to @disliked_jokes
                       → loop back to generate_joke
```

The only non-trivial control flow is the `Disapprove` edge, which forms the HITL refinement loop. The `Approve` edge is the sole termination condition. There is no maximum iteration limit.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (use Section 2 above as text2spl input)
spl3 text2spl --description "Generate a topic-specific joke that satisfies the user \
  by iterating LLM calls with accumulated negative feedback until the human explicitly \
  approves. Collect a topic from the user, then enter a WHILE loop: call a \
  generate_joke function that builds a prompt from the topic and all previously \
  disliked jokes, GENERATE the joke INTO @current_joke, display it, then ask the \
  user for approval. EVALUATE the feedback: if approved, RETURN WITH status=approve; \
  if disapproved, append @current_joke to @disliked_jokes and loop back to \
  generate_joke. No iteration cap; loop runs until human approval." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile joke_generator.spl --lang python/pocketflow
spl3 splc compile joke_generator.spl --lang python/langgraph
spl3 splc compile joke_generator.spl --lang go
```