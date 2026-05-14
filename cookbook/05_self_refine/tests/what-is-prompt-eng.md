(spl123) gong2@gong2:~/projects/digital-duck/SPL.py/cookbook/05_self_refine/tests (intent-eng)$ spl3 run self_refine.spl \
    --adapter claude_cli \
    --param draft_topic="what is prompt engineering" \
    --param max_iterations=3
INFO:spl.registry:Registry: loaded 1 workflow(s) from self_refine.spl
Registry: ['draft_critique_loop']
Running workflow: draft_critique_loop(['draft_topic', 'max_iterations'])
INFO:spl.executor:GENERATE segment 1 (draft) -> 1369 tokens, 34265ms
INFO:spl.executor:GENERATE chain done -> @draft (5479 chars total)
INFO:spl.executor:GENERATE segment 1 (critique) -> 2 tokens, 5897ms
INFO:spl.executor:GENERATE chain done -> @feedback (10 chars total)
INFO:spl.executor:RETURN: 5479 chars | status=approved, iterations=0

Status:  complete
Output:  # Prompt Engineering

Prompt engineering is the practice of designing and refining inputs to language models to reliably elicit desired outputs. It is part craft, part empirical science — you iterate on prompts the way a programmer iterates on code.

---

## Why It Matters

LLMs are sensitive to how instructions are phrased. The same underlying task can yield wildly different results depending on word choice, structure, context, and framing. Prompt engineering is the discipline that tames this sensitivity.

---

## Core Techniques

### 1. Zero-Shot Prompting
Ask the model to perform a task with no examples.

```
Classify the sentiment of this review as positive, negative, or neutral:
"The battery died after two hours."
```

Works well for simple, well-defined tasks. Fails when the task requires implicit knowledge about format or edge cases.

---

### 2. Few-Shot Prompting
Provide examples (shots) before the actual task. The model pattern-matches from them.

```
Review: "Loved it!" → Sentiment: Positive
Review: "Waste of money." → Sentiment: Negative
Review: "It arrived on time." → Sentiment: Neutral

Review: "Couldn't stop reading it." → Sentiment:
```

More reliable than zero-shot. Example quality matters — bad examples mislead the model.

---

### 3. Chain-of-Thought (CoT)
Instruct or demonstrate step-by-step reasoning before the final answer. Dramatically improves performance on multi-step problems.

```
Q: A store has 48 apples. They sell 15, then buy 30 more. How many remain?
A: Start with 48. Subtract 15: 48 - 15 = 33. Add 30: 33 + 30 = 63. Answer: 63.

Q: A bakery has 24 loaves. They sell 9, then bake 18 more. How many remain?
A:
```

The phrase **"think step by step"** is a zero-shot CoT trigger that often works without examples.

---

### 4. Role / Persona Prompting
Assign the model a role to bias its tone, style, and knowledge emphasis.

```
You are a senior security engineer reviewing code for vulnerabilities. 
Your job is to be skeptical and thorough, not reassuring.
```

---

### 5. Instruction Decomposition
Break complex tasks into explicit sub-steps in the prompt itself.

```
Do the following in order:
1. Summarize the passage in one sentence.
2. Identify the main claim.
3. List two potential counterarguments.
```

---

### 6. Output Format Specification
Constrain the output structure to reduce parsing burden and increase consistency.

```
Respond only with a JSON object matching this schema:
{"intent": string, "confidence": float, "entities": [string]}
```

---

### 7. Self-Refine / Critique-and-Revise
Ask the model to evaluate its own output and improve it. Used in agentic pipelines.

```
Draft an answer. Then critique it for accuracy and completeness. 
Then write a revised final answer incorporating your critique.
```

---

### 8. System Prompt vs. User Prompt
In chat-based APIs, system prompts set persistent context and persona. User prompts are the per-turn instructions. Keeping them separate is itself a form of prompt engineering — put constraints and persona in the system prompt, task specifics in the user turn.

---

## Advanced Concepts

### Prompt Sensitivity and Robustness
Small changes (punctuation, synonym substitution, instruction order) can shift outputs significantly. Robust prompts are tested across paraphrases and edge-case inputs.

### Token Budget Awareness
Every token in context is a cost and an attention resource. Verbose prompts can dilute focus on critical instructions. Concise, high-signal prompts often outperform long ones.

### Prompt Injection
When user-controlled input is inserted into a prompt, malicious content can hijack instructions. A key security concern in agentic systems — mitigated by clear delimiters, input sanitization, and privilege separation.

### Retrieval-Augmented Prompting (RAG)
Rather than fitting all knowledge in the prompt, retrieve relevant documents at runtime and inject them as context. The prompt engineering challenge shifts to: how to format retrieved chunks, how to instruct the model to use (or distrust) them.

### Structured Prompting Frameworks
- **ReAct**: Interleave reasoning (`Thought:`) with action calls (`Action:`) and observations (`Observation:`).
- **COSTAR**: Context, Objective, Style, Tone, Audience, Response — a template for comprehensive prompts.
- **SPL (your project)**: A declarative pipeline language that compiles to structured prompts — prompt engineering at the language level.

---

## What Makes a Good Prompt

| Property | Description |
|---|---|
| **Clear intent** | One unambiguous task per instruction |
| **Sufficient context** | Background the model cannot infer |
| **Constrained output** | Format, length, and structure specified |
| **Examples** | When format or nuance is hard to describe |
| **Escape hatches** | What to do when the task is ambiguous or impossible |

---

## The Engineering in Prompt Engineering

It's called *engineering* because it requires:
- **Iteration**: prompts are tested, measured, and revised
- **Evaluation**: results are compared against ground truth or rubrics
- **Version control**: prompts are artifacts that change over time
- **Decomposition**: complex behaviors are split into composable sub-prompts
- **Failure analysis**: edge cases reveal where prompts are underspecified

The output of good prompt engineering is not just a prompt — it's a **prompt system**: instructions, examples, retrieval logic, output schemas, and fallback behaviors working together.
LLM calls: 2  Latency: 40164ms
Log:     /home/gong2/.spl/logs/self_refine-claude_cli-20260514-001608.md
