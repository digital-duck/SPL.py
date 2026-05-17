## Summary

This workflow orchestrates three specialized AI agents — a Researcher, an Analyst, and a Writer — to collaboratively produce a polished report on any given topic. Each agent performs a distinct role and passes its output to the next in sequence, enabling procedural decomposition of a complex writing task into focused sub-tasks. Content teams, researchers, and knowledge workers benefit by receiving a structured, multi-perspective report with minimal manual effort.

---

## Detailed Specification

### 1. Purpose

Automatically produce a well-researched, analyzed, and polished written report on a user-supplied topic by chaining three specialized LLM agents in sequence, writing each agent's output to disk for traceability.

---

### 2. High-level Description

This implementation uses the WORKFLOW construct `multi_agent_report` to orchestrate a linear pipeline of three PROCEDURE-based agents, each encapsulating a distinct reasoning role. The Researcher agent invokes two GENERATE calls — `research_facts` to gather key facts and `identify_key_themes` to extract themes — concatenating results into a structured research document. The Analyst agent invokes three GENERATE calls — `analyze_trends`, `assess_risks`, and `find_opportunities` — assembling a structured analysis document covering trends, risks, and opportunities. The Writer agent invokes three GENERATE calls — `draft_report` to produce an initial draft, `critique` to generate self-review feedback, and `revise_report` to apply that feedback — implementing a self-refinement inner loop within a single PROCEDURE. The orchestrator uses CALL to delegate to each agent procedure in sequence and CALL `write_file` to persist each agent's output to `@log_dir` as Markdown files (`research.md`, `analysis.md`, `report.md`). The workflow RETURNS with `status = 'complete'` on success; EXCEPTION handlers catch `BudgetExceeded` (returning partial results with `status = 'partial_research_only'`) and `HallucinationDetected` (triggering RETRY at low temperature up to three times).

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW multi_agent_report` | `WORKFLOW <name>` | Top-level orchestrator; declares `@topic` and `@log_dir` inputs, `@report` output |
| `PROCEDURE researcher/analyst/writer` | `CREATE FUNCTION <name>` | Reusable agent procedures with typed parameters and explicit RETURN |
| `GENERATE research_facts(topic) INTO @facts` | `GENERATE <fn>(...) INTO @<var>` | LLM call; result stored in scoped variable |
| `GENERATE critique(@draft) INTO @feedback` | `GENERATE <fn>(...) INTO @<var>` | Self-critique within Writer; enables self-refinement without an explicit WHILE loop |
| `CALL researcher(@topic) INTO @research` | `CALL <tool>(...) INTO @<var>` | Delegates to agent procedure; result stored for downstream use |
| `CALL write_file(...) INTO NONE` | `CALL <tool>(...) INTO @<var>` | Side-effect tool call; result discarded (`INTO NONE`) |
| `@result := @facts \|\| ... \|\| @themes` | Shared state via SPL `@vars` | In-scope variable assembly; concatenates multiple GENERATE outputs |
| `RETURN @report WITH status = 'complete'` | `RETURN @<var> WITH <k>=<v>` | Non-trivial terminal status driving exception-free success path |
| `EXCEPTION WHEN BudgetExceeded THEN RETURN @research WITH status = 'partial_research_only'` | `EXCEPTION WHEN <Type> THEN` | Named handler; returns partial result with distinct status token |
| `EXCEPTION WHEN HallucinationDetected THEN RETRY WITH temperature = 0.1 LIMIT 3` | `EXCEPTION WHEN <Type> THEN` | Named handler; triggers constrained retry rather than failure |
| `LOGGING ... LEVEL INFO/DEBUG` | *(SPL logging primitive)* | Observability side-effect; not a control-flow construct |

---

### 4. Logical Functions / Prompts

**`research_facts(topic)`**
- Role: Researcher agent, step 1 — broad fact-gathering pass on the topic.
- Key conventions: Open-ended retrieval prompt; output is prose or structured bullet facts.

**`identify_key_themes(facts)`**
- Role: Researcher agent, step 2 — distills raw facts into a concise list of key themes.
- Key conventions: Summarization/extraction prompt; output is a short enumerated list appended to the research document.

**`analyze_trends(research)`**
- Role: Analyst agent, step 1 — identifies directional trends from the research corpus.
- Key conventions: Forward-looking analytical prompt; output is trend prose.

**`assess_risks(research, topic)`**
- Role: Analyst agent, step 2 — surfaces risks and downsides relevant to the topic.
- Key conventions: Critical/adversarial framing; output is risk prose.

**`find_opportunities(research, topic)`**
- Role: Analyst agent, step 3 — identifies positive opportunities or leverage points.
- Key conventions: Optimistic/constructive framing; output is opportunity prose.

**`draft_report(topic, research, analysis)`**
- Role: Writer agent, step 1 — produces an initial full-length report from all upstream inputs.
- Key conventions: Long-form synthesis prompt combining both research and analysis documents.

**`critique(draft)`**
- Role: Writer agent, step 2 — self-reviews the draft to produce actionable feedback.
- Key conventions: Editorial/critic framing; output is structured feedback (e.g., gaps, tone, flow).

**`revise_report(draft, feedback)`**
- Role: Writer agent, step 3 — applies critique feedback to produce the final polished report.
- Key conventions: Revision prompt; output is the final artifact stored in `@report`.

---

### 5. Control Flow

1. **Entry** — WORKFLOW `multi_agent_report` begins with INFO logging, then CALL `researcher(@topic)` → stores result in `@research`.
2. **Side-effect** — CALL `write_file` persists `@research` to `research.md`.
3. **Agent 2** — CALL `analyst(@research, @topic)` → stores result in `@analysis`; CALL `write_file` persists to `analysis.md`.
4. **Agent 3** — CALL `writer(@research, @analysis, @topic)` → internally performs a self-refinement pass (draft → critique → revise) and returns the final text into `@report`; CALL `write_file` persists to `report.md`.
5. **Termination** — RETURN `@report` WITH `status = 'complete'`.
6. **Exception path A** — If `BudgetExceeded` is raised at any point, RETURN `@research` WITH `status = 'partial_research_only'`, yielding whatever research was gathered.
7. **Exception path B** — If `HallucinationDetected` is raised, RETRY the failed step with `temperature = 0.1` up to three times before propagating failure.

There is no top-level WHILE loop; the pipeline is strictly linear. The only iterative behavior is the self-refinement within the Writer PROCEDURE (draft → critique → revise), which is expressed as sequential GENERATE calls rather than an explicit WHILE construct.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Orchestrate three specialized LLM agent procedures \
  (Researcher, Analyst, Writer) in sequence to produce a polished report on a \
  user-supplied topic. The Researcher uses two GENERATE calls to gather facts and \
  extract themes. The Analyst uses three GENERATE calls to analyze trends, assess \
  risks, and find opportunities. The Writer uses three GENERATE calls implementing \
  a self-refinement loop: draft, critique, and revise. The orchestrator CALLS each \
  agent procedure in order, persists each output to disk via CALL write_file, and \
  RETURNS the final report with status='complete'. Handle BudgetExceeded by \
  returning partial results with status='partial_research_only', and handle \
  HallucinationDetected with RETRY at temperature=0.1 up to 3 times." \
  --mode workflow

# Step 2 — compile to any target
spl3 splc compile multi_agent_report.spl --lang python/pocketflow
spl3 splc compile multi_agent_report.spl --lang python/langgraph
spl3 splc compile multi_agent_report.spl --lang go
```