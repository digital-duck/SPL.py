## Summary

This workflow takes a topic string and produces a polished, conversational article in three sequential steps: outline generation, per-section drafting, and style rewriting. It exists to demonstrate structured LLM output (YAML parsing) and batch parallelism over a dynamic list of sections. Non-technical stakeholders get a ready-to-publish article from a single topic prompt.

---

## Detailed Specification

### 1. Purpose

Generate a complete, stylistically polished article on any user-supplied topic by orchestrating three sequential LLM calls: structured outline generation, parallel section drafting, and conversational style rewriting.

---

### 2. High-level Description

The workflow is a three-stage linear pipeline with no loops or conditional branches. The first GENERATE call (`generate_outline`) prompts the LLM to produce a YAML-formatted article outline capped at three sections; the response is parsed into a list of section titles and stored in shared state. The second stage uses a CALL PARALLEL block to dispatch one GENERATE call per section title (`write_section_content`), with each call instructed to produce a concise 100-word paragraph using plain language and an analogy; all results accumulate into a combined draft. The final GENERATE call (`apply_style`) receives the full draft and rewrites it in a conversational, rhetorical style with a strong opening and conclusion. Shared state (@vars) threads the topic, parsed section list, draft, and final article across all three stages. The completed article is written to disk via a CALL side-effect and summary metrics are printed to stdout.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW article_writer` | `create_article_flow()` + `Flow(start=outline_node)` | Top-level orchestration unit |
| `CREATE FUNCTION generate_outline` | `GenerateOutline.exec()` prompt string | YAML-fenced output format enforced in prompt |
| `CREATE FUNCTION write_section_content` | `WriteSimpleContent.exec()` prompt string | Called once per section; 100-word cap in prompt |
| `CREATE FUNCTION apply_style` | `ApplyStyle.exec()` prompt string | Conversational rewrite with rhetorical questions |
| `GENERATE generate_outline(...) INTO @outline_yaml` | `call_llm(prompt)` + `yaml.safe_load(...)` in `GenerateOutline.exec()` | Includes inline YAML parse step |
| `CALL PARALLEL ... END` over `@sections` | `BatchNode` (`WriteSimpleContent`) | PocketFlow `BatchNode` fans out over the sections list automatically |
| `GENERATE write_section_content(...) INTO @section_content` | `call_llm(prompt)` inside `WriteSimpleContent.exec(section)` | One LLM call per section |
| `GENERATE apply_style(...) INTO @final_article` | `call_llm(prompt)` in `ApplyStyle.exec()` | Receives assembled draft |
| `@topic`, `@sections`, `@draft`, `@final_article` | `shared["topic"]`, `shared["sections"]`, `shared["draft"]`, `shared["final_article"]` | PocketFlow `shared` dict is SPL's variable scope |
| `CALL write_file(@final_article) INTO @_` | `Path(out).write_text(article)` in `main.py` | Side-effect; no return value consumed |

---

### 4. Logical Functions / Prompts

**`generate_outline`**
- Role: Produce the article's structure before any prose is written.
- Prompt conventions: The prompt demands YAML output wrapped in a fenced code block (` ```yaml ... ``` `). The parser splits on the fence markers and calls `yaml.safe_load`. Section count is capped at 3 via the prompt instruction. No sentinel tokens beyond the YAML fence.

**`write_section_content`**
- Role: Draft one paragraph per section in simple, jargon-free language.
- Prompt conventions: Hard word-limit enforced in prompt ("MAXIMUM 100 WORDS"). Requires one analogy or example per paragraph. Output is plain prose; no structured format. Called in parallel for each section in the outline.

**`apply_style`**
- Role: Unify all section drafts into a single, engaging article.
- Prompt conventions: Instructs the LLM to add rhetorical questions, analogies, and a strong framing introduction and conclusion. Input is the full Markdown draft assembled from all section paragraphs. Output is the final publication-ready article.

---

### 5. Control Flow

```
topic (CLI input)
  → GENERATE generate_outline → @sections (list), @outline (formatted string)
  → CALL PARALLEL write_section_content over each item in @sections
        → each GENERATE call produces (section_title, paragraph)
        → all results merged into @draft (Markdown string)
  → GENERATE apply_style(@draft) → @final_article
  → CALL write_file(@final_article, path=@out)  [side-effect, terminates workflow]
```

There are no loops or conditional branches. All three stages are strictly sequential at the macro level; parallelism exists only within the batch section-drafting stage.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Generate a complete, stylistically polished article on any user-supplied topic by orchestrating three sequential LLM calls: structured outline generation, parallel section drafting, and conversational style rewriting. The first GENERATE call prompts the LLM to produce a YAML-formatted article outline capped at three sections; the response is parsed into a list of section titles and stored in shared state. The second stage uses a CALL PARALLEL block to dispatch one GENERATE call per section title, with each call instructed to produce a concise 100-word paragraph using plain language and an analogy; all results accumulate into a combined draft. The final GENERATE call receives the full draft and rewrites it in a conversational, rhetorical style with a strong opening and conclusion. The completed article is written to disk via a CALL side-effect." --mode workflow

# Step 2 — compile to any target
spl3 splc compile article_writer.spl --lang python/pocketflow
spl3 splc compile article_writer.spl --lang python/langgraph
spl3 splc compile article_writer.spl --lang go
```