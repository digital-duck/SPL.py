## Summary

This pipeline automates the early stages of B2B outbound sales by loading a list of leads, enriching each with company context, using an LLM to rate their fit for the product, and generating a personalized cold email for every high-scoring prospect. It replaces hours of manual research and drafting with a single command. Sales and growth teams at software companies benefit most, as it turns a raw lead list into ready-to-send outreach in seconds.

---

## Detailed Specification

### 1. Purpose

Generate scored, enriched lead profiles and personalized cold-outreach emails automatically from a raw list of sales prospects.

---

### 2. High-level Description

This workflow is a four-stage linear sales pipeline that processes a list of B2B leads from raw data to ready-to-send cold emails. A `ScrapeLeads` function loads the prospect list from a shared data store (or falls back to sample data), and an `EnrichLeads` function appends company intelligence — funding stage, tech stack, team size — to each record. A `ScoreLeads` function issues a single batched LLM call, instructing the model to rate every lead 1–10 based on their likely need for LLM tooling, seniority, and technical role; the model responds in a structured YAML block that is parsed back into per-lead score and reason fields. A `PersonalizeEmails` function then filters to leads scoring 6 or above and issues one LLM call per qualified prospect, asking the model to write a three-sentence cold email that references a company-specific detail, connects to a likely pain point, and closes with a request for a fifteen-minute call. All intermediate and final results accumulate in a shared state store (`@leads`, `@emails`) that flows through every stage. There is no iterative refinement or conditional branching — the pipeline runs once and writes the finished emails to a Markdown file.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW lead_generation_pipeline` | `create_lead_generation_flow()` + `Flow(start=scrape)` | Top-level orchestration unit |
| `CREATE FUNCTION scrape_leads` | `ScrapeLeads.exec()` | Returns raw lead list; no LLM call |
| `CREATE FUNCTION enrich_leads` | `EnrichLeads.exec()` | Attaches company intel; no LLM call in this implementation |
| `CREATE FUNCTION score_leads` | `ScoreLeads.exec()` | Single batched LLM call; structured YAML output |
| `CREATE FUNCTION personalize_email` | `PersonalizeEmails.exec()` (inner loop) | One LLM call per qualified lead |
| `GENERATE score_leads(...) INTO @scores` | `call_llm(prompt)` in `ScoreLeads.exec` | Returns YAML block; parsed with `yaml.safe_load` |
| `GENERATE personalize_email(...) INTO @email` | `call_llm(prompt)` in `PersonalizeEmails.exec` loop | Called once per hot lead |
| `@leads` (shared variable) | `shared["leads"]` | Mutated in-place across all four stages |
| `@emails` (shared variable) | `shared["emails"]` | Written by `PersonalizeEmails`, read by `main.py` for output |
| `CALL write_file(...) INTO @_` | `Path(out).write_text(...)` in `main.py` | Side-effect: persists emails to Markdown on disk |
| Filter `score >= 6` | `[l for l in shared["leads"] if l["score"] >= 6]` in `PersonalizeEmails.prep` | Qualification gate; maps to an `EVALUATE` or `WHILE` guard in SPL if made explicit |

---

### 4. Logical Functions / Prompts

**`score_leads`**
- **Role:** Batch-scores the entire lead list in one LLM call to minimize latency and token overhead.
- **Prompt conventions:** Injects the product description (`PRODUCT`) and a newline-delimited lead roster. Instructs the model to output *only* a fenced YAML block (sentinel: `` ```yaml `` / `` ``` ``) containing a `scores` list of `{name, score, reason}` objects. The score is an integer 1–10; the reason is a single sentence.
- **Parsing:** Splits on the YAML fence, strips whitespace, and calls `yaml.safe_load`. No regex; relies entirely on the model honoring the fence sentinel.

**`personalize_email`**
- **Role:** Writes a high-conversion cold email tailored to one individual prospect.
- **Prompt conventions:** Receives `name`, `title`, `company`, `enrichment` (company context), and `PRODUCT`. Rules are enumerated inline: reference a company-specific fact, connect to a likely pain, close with a 15-minute call ask, no filler phrases, subject line first. Output is free-form plain text — no structured parsing required.

---

### 5. Control Flow

```
ScrapeLeads
    → loads @leads from shared store (or SAMPLE_LEADS fallback)
EnrichLeads
    → annotates each record in @leads with company intel
ScoreLeads
    → single LLM call → YAML parse → scores merged back into @leads → sorted descending by score
PersonalizeEmails
    → filters @leads where score >= 6 → LLM call per lead → @emails written to shared store
main.py
    → writes @emails to disk as Markdown
```

The pipeline is strictly linear with no loops or conditional branches. The only decision point — the `score >= 6` qualification gate — is a deterministic Python filter, not an LLM-evaluated branch. Execution terminates naturally after `PersonalizeEmails` writes its output.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Generate scored, enriched lead profiles and personalized cold-outreach emails automatically from a raw list of sales prospects." --mode workflow

# Step 2 — compile to any target
spl3 splc compile lead_generation_pipeline.spl --lang python/pocketflow
spl3 splc compile lead_generation_pipeline.spl --lang python/langgraph
spl3 splc compile lead_generation_pipeline.spl --lang go
```