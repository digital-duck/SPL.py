Looking at this Python PocketFlow implementation, I'll analyze it and produce the SPL functional specification:

## 0. High-level Description

This WORKFLOW implements a recursive map-reduce research pipeline with iterative refinement that conducts comprehensive topic research through multiple search iterations. The workflow begins with a CREATE FUNCTION planner that generates diverse search queries for a given topic, followed by a CREATE FUNCTION researcher that performs parallel web searches using CALL operations for each query and extracts relevant facts via GENERATE calls. A CREATE FUNCTION synthesizer then evaluates the collected information using EVALUATE logic to determine if sufficient research has been gathered or if knowledge gaps remain. The control flow uses WHILE loop semantics with a maximum iteration limit of 2, where the synthesizer can branch back to the planner with specific feedback about missing information, or proceed to generate the final research report. The workflow maintains shared state through @variables for topic, queries, notes, feedback, and loop count, with EXCEPTION handling for API failures and search timeouts. Upon completion, the workflow executes RETURN WITH status and delivers a comprehensive markdown research report.

## 1. Purpose

Automates comprehensive topic research by orchestrating iterative web searches and LLM analysis to produce a well-researched markdown report.

## 2. SPL ↔ Python — PocketFlow Construct Mapping

| SPL Construct | Python — PocketFlow Equivalent | Notes |
|---------------|-------------------------------|--------|
| `WORKFLOW <name>` | `Flow(start=planner)` | Workflow definition with entry point |
| `CREATE FUNCTION <name>` | `class XNode(Node): def exec()` | Reusable prompt templates in node classes |
| `GENERATE <fn>(...) INTO @<var>` | `call_llm(prompt)` in node exec() | LLM calls with prompt templates |
| `CALL <tool>(...) INTO @<var>` | `search_web(query)` | Side-effect operations |
| `WHILE <cond> DO ... END` | Loop via `shared["loop_count"]` + node routing | Conditional iteration through node connections |
| `EVALUATE @<var> WHEN ... THEN ... ELSE` | `if exec_res["action"] == "research"` | Branching logic in post() methods |
| `RETURN @<var> WITH <k>=<v>` | `shared["report"] = content` + flow termination | Final output with metadata |
| `EXCEPTION WHEN <Type> THEN ...` | Try/catch in call_llm and search_web utils | Error handling for API failures |
| `@<var>` (shared state) | `shared` dictionary | Cross-node state management |

## 3. Logical Functions / Prompts

**PlannerNode**
- **Role**: Query generation and refinement based on feedback
- **Key conventions**: YAML output format with `queries` array, conditional instruction based on feedback presence
- **Prompt pattern**: Instruction + output format specification using ```yaml blocks

**ResearcherNode** 
- **Role**: Parallel web search and fact extraction (BatchNode for concurrency)
- **Key conventions**: Two-stage process (search + extract), structured output as "Q: {query}\nFacts: {extracted}"
- **Prompt pattern**: Fact extraction with context preservation

**SynthesizerNode**
- **Role**: Gap analysis and report generation with termination logic
- **Key conventions**: YAML output with action field ("research" vs "finalize"), forced termination after 2 loops
- **Prompt pattern**: Conditional branching based on information sufficiency assessment

## 4. Control Flow

Initial step: PlannerNode generates search queries → ResearcherNode performs parallel web searches and fact extraction → SynthesizerNode evaluates information completeness. Loop condition: WHILE loop_count < 2 AND action == "research". Branch logic: EVALUATE synthesizer output WHEN action contains "research" THEN route back to PlannerNode with feedback ELSE proceed to finalization. Termination: RETURN WITH status="complete" when SynthesizerNode outputs action="finalize" or maximum iterations reached.

## 5. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 0 above as text2spl input)
spl3 text2spl --description "This WORKFLOW implements a recursive map-reduce research pipeline with iterative refinement that conducts comprehensive topic research through multiple search iterations. The workflow begins with a CREATE FUNCTION planner that generates diverse search queries for a given topic, followed by a CREATE FUNCTION researcher that performs parallel web searches using CALL operations for each query and extracts relevant facts via GENERATE calls. A CREATE FUNCTION synthesizer then evaluates the collected information using EVALUATE logic to determine if sufficient research has been gathered or if knowledge gaps remain. The control flow uses WHILE loop semantics with a maximum iteration limit of 2, where the synthesizer can branch back to the planner with specific feedback about missing information, or proceed to generate the final research report. The workflow maintains shared state through @variables for topic, queries, notes, feedback, and loop count, with EXCEPTION handling for API failures and search timeouts. Upon completion, the workflow executes RETURN WITH status and delivers a comprehensive markdown research report." --mode workflow

# Step 2 — compile to any target  
spl3 splc compile <output.spl> --lang python/pocketflow
spl3 splc compile <output.spl> --lang python/langgraph  
spl3 splc compile <output.spl> --lang go
```