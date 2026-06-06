## Summary

This workflow demonstrates deep procedural composability in SPL: a top-level `WORKFLOW` orchestrates three reusable `PROCEDURE` units that each encapsulate a focused LLM task — explaining, exemplifying, and complexity-calibrating. It transforms a raw topic and target audience into a polished, reading-level-appropriate explanatory article. Content educators, technical writers, and curriculum designers benefit from its modular structure, which lets any inner procedure be replaced or reused independently.

---

## Detailed Specification

### 1. Purpose

Produce a well-structured, audience-calibrated explanatory article on any topic by composing three independently reusable LLM procedures under a single orchestrating workflow.

---

### 2. High-level Description

The `layered_explainer` WORKFLOW accepts a topic, a target audience, and an optional depth parameter, then delegates all sub-tasks to inner PROCEDUREs via CALL. It begins with a direct GENERATE to research the topic into `@overview`, then CALLs `explain_layer` to produce a plain-language explanation styled for the audience. A second CALL to `make_example` generates a concrete illustration grounded in that explanation. A third CALL to `calibrate_complexity` performs quality gating: it internally GENERATEs a reading-level assessment and uses an EVALUATE branch to conditionally simplify the text if it exceeds grade 8 — the only non-linear control flow in the pipeline. The WORKFLOW closes with a final GENERATE that assembles all outputs (`@calibrated_explanation`, `@example`, `@depth`) into a unified `@article`, then RETURNs it WITH `status='complete'` and the resolved audience metadata. Each inner PROCEDURE is self-contained — it declares typed INPUT parameters with optional DEFAULTs, performs exactly one or two GENERATE calls, and RETURNs a TEXT result — making them independently reusable in other workflows.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW layered_explainer` | `WORKFLOW` | Top-level orchestrator; declares `INPUT:` and `OUTPUT:` |
| `PROCEDURE explain_layer` | `PROCEDURE` | Reusable sub-unit; encapsulates one GENERATE call |
| `PROCEDURE make_example` | `PROCEDURE` | Reusable sub-unit; generates a concrete illustration |
| `PROCEDURE calibrate_complexity` | `PROCEDURE` | Reusable sub-unit; contains EVALUATE for conditional simplification |
| `GENERATE research_overview(...)` | `GENERATE ... INTO @var` | Inline LLM call in WORKFLOW body |
| `CALL explain_layer(...) INTO @base_explanation` | `CALL <procedure>(...) INTO @var` | Sub-procedure dispatch; pushes a call frame |
| `CALL make_example(...) INTO @example` | `CALL <procedure>(...) INTO @var` | Sub-procedure dispatch |
| `CALL calibrate_complexity(...) INTO @calibrated_explanation` | `CALL <procedure>(...) INTO @var` | Sub-procedure dispatch; hides internal branching from caller |
| `EVALUATE @reading_level WHEN > target_grade` | `EVALUATE ... WHEN ... THEN ... ELSE ... END` | Semantic branch; LLM judge compares grade level to threshold |
| `RETURN @article WITH status='complete'` | `RETURN @var WITH <k>=<v>` | Non-trivial terminal status; signals successful completion to any caller |
| `@overview`, `@base_explanation`, `@example`, `@calibrated_explanation`, `@article` | SPL `@vars` | Shared state threaded through WORKFLOW body via CALL bindings |
| `style TEXT DEFAULT 'clear and engaging'` | typed parameter with `DEFAULT` | Optional parameter with fallback; resolved at CALL time |

---

### 4. Logical Functions / Prompts

**`research_overview(topic)`**
- Role: Seeds the pipeline with factual background on the topic.
- Conventions: Open-ended research prompt; output is a structured overview stored in `@overview` and passed as `content` to `explain_layer`.

**`explain(content, audience, style)`** *(inside `explain_layer`)*
- Role: Converts raw research into an audience-appropriate plain-language explanation.
- Conventions: The `style` parameter defaults to `'clear and engaging'`; the WORKFLOW overrides it to `'clear, engaging, avoid jargon'` at the CALL site, demonstrating per-call style injection.

**`concrete_example(concept, context, audience)`** *(inside `make_example`)*
- Role: Grounds the abstract explanation in a relatable, real-world example.
- Conventions: Receives both the original `concept` and the full `context` (the base explanation) to ensure the example is coherent with the prose already generated.

**`assess_reading_level(text)`** *(inside `calibrate_complexity`)*
- Role: LLM judge that estimates the reading grade level of input text.
- Conventions: Output is expected to be a numeric grade level or comparable signal; the EVALUATE branch compares it against `target_grade` (default 8).

**`simplify(text, audience)`** *(inside `calibrate_complexity`, conditional path)*
- Role: Rewrites text at a lower complexity when the assessed grade exceeds the threshold.
- Conventions: Only invoked on the EVALUATE true-branch; the ELSE path passes the original text through unchanged.

**`assemble_article(topic, calibrated_explanation, example, depth)`**
- Role: Final synthesis step; stitches all components into a coherent article.
- Conventions: The `depth` parameter (`'standard'` or `'deep'`) is passed through from the top-level WORKFLOW INPUT, giving the assembler control over article length and elaboration.

---

### 5. Control Flow

```
WORKFLOW layered_explainer
│
├── GENERATE research_overview(@topic) → @overview
│
├── CALL explain_layer(content=@overview, audience, style) → @base_explanation
│
├── CALL make_example(concept=@topic, context=@base_explanation, audience) → @example
│
├── CALL calibrate_complexity(text=@base_explanation, audience, target_grade=8)
│       │
│       ├── GENERATE assess_reading_level(@base_explanation) → @reading_level
│       │
│       └── EVALUATE @reading_level
│               WHEN > 8  → GENERATE simplify(...) → @calibrated  → RETURN @calibrated
│               ELSE      → RETURN original text unchanged
│       → @calibrated_explanation
│
├── GENERATE assemble_article(@topic, @calibrated_explanation, @example, @depth) → @article
│
└── RETURN @article WITH status='complete', audience=@audience
```

Execution is linear except for the single EVALUATE inside `calibrate_complexity`, which performs a conditional rewrite. There are no WHILE loops; the pipeline runs exactly once per invocation. The non-trivial `RETURN WITH status='complete'` signals clean termination to any parent workflow that might CALL `layered_explainer` in a larger composition.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Produce a well-structured, audience-calibrated explanatory article on any topic by composing three independently reusable LLM procedures under a single orchestrating workflow." --mode workflow

# Step 2 — compile to any target
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph
spl3 splc compile <output.spl> --lang go
```