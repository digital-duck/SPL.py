## Summary

This workflow implements a three-stage Chain of Thought reasoning pipeline: it first researches a topic, then analyzes the findings for trends and implications, and finally condenses the analysis into an executive brief. It exists to produce high-quality, structured prose on any topic by decomposing a single complex task into sequential, focused LLM calls. Analysts, researchers, and content teams benefit from getting a polished summary grounded in an explicit reasoning chain rather than a single unconstrained generation.

---

## Detailed Specification

### 1. Purpose

Produce a concise executive summary on any given topic by guiding an LLM through an explicit three-step reasoning chain: fact-gathering, trend analysis, and synthesis.

### 2. High-level Description

The workflow uses the Chain of Thought pattern, decomposing a complex summarization task into three sequential GENERATE steps so each LLM call receives progressively refined context. A `research` CREATE FUNCTION instructs the model to surface key facts about the input topic; its output is captured into `@research` and passed verbatim into an `analyze` CREATE FUNCTION, which prompts the model to extract trends and implications from those facts. The resulting analysis is then forwarded to a `summarize_analysis` CREATE FUNCTION that constrains the model to produce a concise executive brief. Each intermediate result is stored in a workflow variable (`@research`, `@analysis`, `@summary`) so that every downstream GENERATE call has full visibility into prior reasoning. The workflow accepts a single TEXT INPUT (`@topic`, defaulting to `'distributed AI inference'`) and emits `@summary` as its OUTPUT, concluding with `RETURN @summary WITH status = 'complete'`. There are no loops, branches, or exception handlers — the control flow is strictly linear, relying on the sequential data dependency between variables to enforce the reasoning chain.

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW chain_of_thought` | `WORKFLOW` | Named orchestration unit; accepts `INPUT:` / `OUTPUT:` declarations |
| `INPUT: @topic TEXT DEFAULT '...'` | Typed input variable | Default value makes the workflow self-contained for demo runs |
| `OUTPUT: @summary TEXT` | Typed output binding | Declares what the caller receives on `CALL chain_of_thought(...)` |
| `CREATE FUNCTION research(topic TEXT)` | `CREATE FUNCTION` | Prompt template with a `{topic}` slot; returns TEXT |
| `CREATE FUNCTION analyze(research TEXT)` | `CREATE FUNCTION` | Prompt template with a `{research}` slot; receives prior output |
| `CREATE FUNCTION summarize_analysis(analysis TEXT)` | `CREATE FUNCTION` | Prompt template with an `{analysis}` slot; produces the final brief |
| `GENERATE research(@topic) INTO @research` | `GENERATE ... INTO @var` | LLM call; result bound to `@research` |
| `GENERATE analyze(@research) INTO @analysis` | `GENERATE ... INTO @var` | LLM call; consumes `@research`, binds `@analysis` |
| `GENERATE summarize_analysis(@analysis) INTO @summary` | `GENERATE ... INTO @var` | LLM call; consumes `@analysis`, binds `@summary` |
| `@research`, `@analysis`, `@summary` | Shared workflow variables (`@var`) | Carry intermediate state between GENERATE steps |
| `RETURN @summary WITH status = 'complete'` | `RETURN ... WITH status=` | Signals clean termination to any parent `CALL` site |

### 4. Logical Functions / Prompts

**`research(topic TEXT)`**
- **Role:** Bootstraps the reasoning chain by grounding the LLM in factual material about the topic.
- **Key prompt conventions:** Open-ended retrieval directive ("Research and provide key facts about {topic}"). No sentinel tokens or scoring — the entire response is treated as raw research material for the next step.

**`analyze(research TEXT)`**
- **Role:** Elevates raw facts into structured insight by prompting the model to identify trends and implications.
- **Key prompt conventions:** The full `{research}` output is embedded inline under a labeled field (`Research: {research}`), establishing clear provenance. The directive focuses the model on interpretation rather than description.

**`summarize_analysis(analysis TEXT)`**
- **Role:** Terminal compression step; distills the analysis into a stakeholder-ready executive brief.
- **Key prompt conventions:** The full `{analysis}` output is embedded under a labeled field (`Analysis: {analysis}`). The directive explicitly constrains length and register ("concise executive brief"), shaping output style without hard token limits.

### 5. Control Flow

Execution is strictly linear with no branching or iteration. The workflow begins by invoking `research(@topic)` and binding the result to `@research`. That variable is immediately consumed by `analyze(@research)`, whose output is bound to `@analysis`. The final GENERATE call, `summarize_analysis(@analysis)`, produces `@summary`. The workflow terminates with `RETURN @summary WITH status = 'complete'`, which signals to any calling context that the output is ready and the workflow exited cleanly. The `status = 'complete'` token is meaningful at a `CALL` site — a parent workflow wrapping this one could `EVALUATE` that status — but within this workflow itself no branching occurs.

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Produce a concise executive summary on any given topic by guiding an LLM through an explicit three-step reasoning chain: fact-gathering, trend analysis, and synthesis." --mode workflow

# Step 2 — compile to any target
spl3 splc compile chain_of_thought.spl --lang python/pocketflow
spl3 splc compile chain_of_thought.spl --lang python/langgraph
spl3 splc compile chain_of_thought.spl --lang go
```