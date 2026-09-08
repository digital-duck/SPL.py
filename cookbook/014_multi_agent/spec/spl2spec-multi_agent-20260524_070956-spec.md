## Summary

This workflow orchestrates three specialized AI agents — Researcher, Analyst, and Writer — to collaboratively produce a polished report on any given topic. Each agent has a distinct role: gathering facts, identifying trends and risks, and synthesizing a final narrative. It exists to demonstrate how complex knowledge-work tasks can be decomposed into expert sub-roles using procedural delegation in SPL.

---

## Detailed Specification

### 1. Purpose

Generate a structured, multi-perspective research report on a user-supplied topic by chaining three specialized LLM agents — Researcher, Analyst, and Writer — each building on the previous agent's output.

---

### 2. High-level Description

This workflow implements a **sequential multi-agent pipeline** using SPL `PROCEDURE` declarations for each agent and a central `WORKFLOW` orchestrator that coordinates them via `CALL`. The **Researcher** agent runs two `GENERATE` calls — `research_facts` to surface key facts and `identify_key_themes` to distill themes — then concatenates results into a structured research document. The **Analyst** agent accepts the research output and runs three parallel-semantics `GENERATE` calls — `analyze_trends`, `assess_risks`, and `find_opportunities` — assembling a structured analytical layer. The **Writer** agent closes the pipeline with a three-step iterative drafting loop: `draft_report` produces an initial draft, `critique` generates self-critique feedback, and `revise_report` incorporates that feedback into a final polished document. The orchestrator workflow calls each agent in strict sequence, writes intermediate outputs to disk via `CALL write_file(...)`, and terminates with `RETURN @report WITH status = 'complete'`. Two named exception handlers protect the pipeline: `BudgetExceeded` returns a partial result rather than failing silently, and `HallucinationDetected` triggers a RETRY at reduced temperature (0.1) with a limit of 3 attempts.

---

### 3. SPL ↔ SPL Construct Mapping

| SPL Construct | SPL Equivalent | Notes |
|---|---|---|
| `WORKFLOW multi_agent_report` | `WORKFLOW` | Top-level orchestrator; declares `@topic` and `@log_dir` as INPUT, `@report` as OUTPUT |
| `PROCEDURE researcher(...)` | `PROCEDURE` | Agent 1; encapsulates fact-gathering as a named, reusable sub-unit |
| `PROCEDURE analyst(...)` | `PROCEDURE` | Agent 2; encapsulates trend/risk/opportunity analysis |
| `PROCEDURE writer(...)` | `PROCEDURE` | Agent 3; encapsulates draft–critique–revise loop |
| `GENERATE research_facts(topic) INTO @facts` | `GENERATE ... INTO @var` | LLM call capturing raw research facts |
| `GENERATE identify_key_themes(@facts) INTO @themes` | `GENERATE ... INTO @var` | LLM call extracting themes from prior output |
| `GENERATE analyze_trends(research) INTO @trends` | `GENERATE ... INTO @var` | LLM call for trend analysis |
| `GENERATE assess_risks(research, topic) INTO @risks` | `GENERATE ... INTO @var` | LLM call for risk assessment |
| `GENERATE find_opportunities(...) INTO @opportunities` | `GENERATE ... INTO @var` | LLM call for opportunity identification |
| `GENERATE draft_report(...) INTO @draft` | `GENERATE ... INTO @var` | Initial report draft |
| `GENERATE critique(@draft) INTO @feedback` | `GENERATE ... INTO @var` | Self-critique of the draft |
| `GENERATE revise_report(@draft, @feedback) INTO @final` | `GENERATE ... INTO @var` | Revision incorporating critique feedback |
| `CALL researcher(@topic) INTO @research` | `CALL ... INTO @var` | Delegates to Researcher PROCEDURE; pushes frame, binds OUTPUT |
| `CALL analyst(@research, @topic) INTO @analysis` | `CALL ... INTO @var` | Delegates to Analyst PROCEDURE |
| `CALL writer(@research, @analysis, @topic) INTO @report` | `CALL ... INTO @var` | Delegates to Writer PROCEDURE |
| `CALL write_file(...) INTO NONE` | `CALL` (side-effect) | File I/O tool call; result discarded |
| `@result := @facts \|\| '\n\n...' \|\| @themes` | `@var` (shared state) | In-procedure string concatenation via SPL variable binding |
| `RETURN @report WITH status = 'complete'` | `RETURN ... WITH status=` | Non-trivial terminal status signals successful pipeline completion |
| `EXCEPTION WHEN BudgetExceeded` | `EXCEPTION WHEN` | Returns partial research rather than crashing |
| `EXCEPTION WHEN HallucinationDetected` | `EXCEPTION WHEN` + `RETRY` | Lowers temperature and retries up to 3 times |

---

### 4. Logical Functions / Prompts

**`research_facts(topic)`**
- Role: Entry point for the Researcher agent; queries the LLM for factual content on the topic.
- Key conventions: Output should be structured, citable facts suitable for downstream analysis.

**`identify_key_themes(facts)`**
- Role: Second pass within the Researcher; distills the raw facts into thematic clusters.
- Key conventions: Output is a short enumerated list of themes; feeds into Analyst.

**`analyze_trends(research)`**
- Role: Opens the Analyst agent by identifying directional trends in the research material.
- Key conventions: Forward-looking language; structured by temporal or magnitude dimension.

**`assess_risks(research, topic)`**
- Role: Second Analyst call; surfaces threats, failure modes, and downsides.
- Key conventions: Risk framing (likelihood × impact); topic context used to constrain scope.

**`find_opportunities(research, topic)`**
- Role: Third Analyst call; identifies positive leverage points or gaps in the research.
- Key conventions: Opportunity framing; complements risk output to form balanced analysis.

**`draft_report(topic, research, analysis)`**
- Role: Opens the Writer agent; synthesizes all upstream material into an initial full report.
- Key conventions: Narrative prose; uses topic as title/framing anchor and both upstream documents as body inputs.

**`critique(draft)`**
- Role: Self-evaluation step within the Writer; critiques the draft for gaps, tone, accuracy.
- Key conventions: Returns structured feedback (e.g., numbered issues or sections); designed to feed directly into revision.

**`revise_report(draft, feedback)`**
- Role: Final Writer step; applies critique feedback to produce the publication-ready report.
- Key conventions: Output replaces the draft entirely; incorporates all feedback points.

---

### 5. Control Flow

The orchestrator workflow begins by logging the topic at INFO level, then delegates sequentially to three agents via `CALL`:

1. `CALL researcher(@topic) INTO @research` — Researcher runs two internal `GENERATE` calls and returns concatenated facts + themes. The result is immediately persisted to `research.md`.
2. `CALL analyst(@research, @topic) INTO @analysis` — Analyst runs three internal `GENERATE` calls and returns a structured trends/risks/opportunities document, persisted to `analysis.md`.
3. `CALL writer(@research, @analysis, @topic) INTO @report` — Writer runs a three-step draft → critique → revise sequence internally and returns the final report, persisted to `report.md`.

After all three agents complete, the workflow terminates with `RETURN @report WITH status = 'complete'`, signaling successful pipeline completion to any parent caller.

**Exception paths** interrupt the normal flow at any point:
- `BudgetExceeded` short-circuits before Writer or Analyst completion, returning whatever partial research exists with `status = 'partial_research_only'`.
- `HallucinationDetected` triggers `RETRY WITH temperature = 0.1 LIMIT 3`, re-attempting the offending agent call at a lower temperature before escalating.

There are no `WHILE` loops or `EVALUATE` branches in the top-level control flow; the Writer agent's draft–critique–revise sequence is a linear three-step chain, not an iterative quality gate.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Generate a structured, multi-perspective research report on a user-supplied topic by chaining three specialized LLM agents — Researcher, Analyst, and Writer — each building on the previous agent's output." --mode workflow

# Step 2 — compile to any target
spl3 splc compile multi_agent_report.spl --lang python/pocketflow
spl3 splc compile multi_agent_report.spl --lang python/langgraph
spl3 splc compile multi_agent_report.spl --lang go
```