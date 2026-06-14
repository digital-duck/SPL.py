## Summary

This workflow implements an adversarial debate pattern where two LLM advocates argue opposing sides of a user-supplied claim, and a third impartial LLM judge scores both arguments and declares a winner. It exists to improve decision-making quality by forcing structured consideration of multiple perspectives before reaching a conclusion. Non-technical stakeholders—analysts, researchers, policy teams—benefit from a transparent, evidence-grounded evaluation of any contestable proposition.

---

## Detailed Specification

### 1. Purpose

Given a natural-language claim, orchestrate two LLM advocates and one LLM judge to produce a scored, reasoned verdict on which side of the debate is stronger.

---

### 2. High-level Description

This workflow implements a three-stage adversarial debate using a linear WORKFLOW with three CREATE FUNCTIONs. The first function, `advocate_for`, receives the bare claim as input and GENERATE s the strongest evidence-based case in favor, returning a structured YAML block containing a prose argument and three bullet-point key points. The second function, `advocate_against`, receives both the original claim and the full FOR argument, then GENERATEs a point-by-point rebuttal plus independent counterarguments in the same YAML format. The third function, `judge_debate`, receives the claim and both completed arguments, then GENERATEs a structured verdict that names the winner (FOR or AGAINST), assigns integer scores out of 10 to each side, and provides a one-sentence verdict and a brief comparative analysis. All intermediate results—case for, case against, scores, winner, verdict, reasoning—are stored as workflow-scoped `@vars` and passed forward through the pipeline. The flow is strictly linear with no loops or branches; control passes unconditionally from advocate-for → advocate-against → judge.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW debate` | `create_debate_flow()` + `Flow(start=...)` | Top-level named orchestration unit |
| `INPUT: @claim` | `shared = {"claim": claim}` passed to `flow.run()` | Workflow entry parameter |
| `CREATE FUNCTION advocate_for` | `AdvocateFor.exec()` with inline prompt string | Prompt template with `{claim}` slot |
| `CREATE FUNCTION advocate_against` | `AdvocateAgainst.exec()` with inline prompt string | Prompt template with `{claim}` and `{opposing}` slots |
| `CREATE FUNCTION judge_debate` | `JudgeDebate.exec()` with inline prompt string | Prompt template with `{claim}`, `{case_for}`, `{case_against}` slots |
| `GENERATE advocate_for(@claim) INTO @case_for` | `call_llm(prompt)` → YAML parse → `shared["case_for"]` | LLM call + YAML extraction in `exec`; binding in `post` |
| `GENERATE advocate_against(@claim, @case_for) INTO @case_against` | `call_llm(prompt)` → YAML parse → `shared["case_against"]` | Same pattern; reads `@case_for` from shared state |
| `GENERATE judge_debate(@claim, @case_for, @case_against) INTO @verdict` | `call_llm(prompt)` → YAML parse → multiple `shared[...]` writes | Writes `@winner`, `@score_for`, `@score_against`, `@verdict`, `@reasoning` |
| `@var` (shared workflow state) | `shared` dict passed by reference through all nodes | PocketFlow's shared store maps 1-to-1 to SPL scoped variables |
| `EXCEPTION WHEN LLMError THEN ...` | `max_retries=3, wait=10` on each Node constructor | PocketFlow's built-in retry is the implicit exception handler |

---

### 4. Logical Functions / Prompts

**`advocate_for`**
- **Role:** Opens the debate by constructing the affirmative case with no knowledge of any counterargument.
- **Prompt conventions:** System persona is "expert advocate arguing FOR." Output must be a fenced YAML block with keys `argument` (prose, 3–4 sentences) and `key_points` (list of 3 strings). The fence sentinel ` ```yaml ` / ` ``` ` is parsed by splitting on those tokens.

**`advocate_against`**
- **Role:** Reads the full FOR argument before generating its response, enabling direct rebuttal rather than generic opposition.
- **Prompt conventions:** System persona is "expert advocate arguing AGAINST." Receives both `claim` and the literal `opposing` argument text. Same YAML schema as `advocate_for`. Prompt explicitly instructs the model to rebut specific points, not just argue from scratch.

**`judge_debate`**
- **Role:** Impartial evaluator that produces a final scored verdict.
- **Prompt conventions:** System persona is "impartial judge." Output YAML has five keys: `winner` ("FOR" or "AGAINST"), `score_for` (integer 1–10), `score_against` (integer 1–10), `verdict` (one sentence), `reasoning` (brief comparative analysis). The scoring rubric covers reasoning quality, evidence, and persuasiveness.

---

### 5. Control Flow

```
START
  │
  ▼
GENERATE advocate_for(@claim)
  → stores @case_for, @case_for_points
  │
  ▼
GENERATE advocate_against(@claim, @case_for)
  → stores @case_against, @case_against_points
  │
  ▼
GENERATE judge_debate(@claim, @case_for, @case_against)
  → stores @winner, @score_for, @score_against, @verdict, @reasoning
  │
  ▼
END  (results available in shared state for caller to read)
```

The flow is purely linear. There are no WHILE loops, no EVALUATE branches, and no non-trivial RETURN status tokens. Each node fails fast with retry (up to 3 attempts, 10-second back-off) if the LLM call or YAML parse raises an exception.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Given a natural-language claim, orchestrate two LLM advocates and one LLM judge to produce a scored, reasoned verdict on which side of the debate is stronger." --mode workflow

# Step 2 — compile to any target
spl3 splc compile debate.spl --lang python/pocketflow
spl3 splc compile debate.spl --lang python/langgraph
spl3 splc compile debate.spl --lang go
```