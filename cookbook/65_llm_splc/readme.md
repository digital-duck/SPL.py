# Recipe 65: LLM-powered SPL Compiler (vibe-splc)

Compiles a `.spl` workflow to a target framework implementation using LLM (`claude_cli`).
Complements the deterministic `splc` compiler — run both and cross-compare to surface gaps
between generated output and the author's intent.

**Supported targets:** `langgraph`, `autogen`, `crewai`  
**Recommended adapter:** `claude_cli`

## How it works

1. Loads the `.spl` source file
2. Generates an idiomatic target framework implementation via LLM
3. Self-reviews the output against the original SPL spec
4. Fixes any gaps found before returning the final implementation

## Fill the §6.2 table gaps

### Recipe 11: debate_arena → CrewAI

```bash
spl3 run cookbook/65_llm_splc/llm_splc.spl \
    --adapter claude_cli \
    --tools cookbook/65_llm_splc/tools.py \
    --param spl_file="cookbook/11_debate_arena/debate_arena.spl" \
    --param target="crewai" \
    --param output_file="cookbook/11_debate_arena/targets/crewai/debate_arena.py"
```

### Recipe 63: parallel_code_review → AutoGen

```bash
spl3 run cookbook/65_llm_splc/llm_splc.spl \
    --adapter claude_cli \
    --tools cookbook/65_llm_splc/tools.py \
    --param spl_file="cookbook/63_parallel_code_review/parallel_code_review.spl" \
    --param target="autogen" \
    --param output_file="cookbook/63_parallel_code_review/targets/autogen/parallel_code_review.py"
```

### Recipe 63: parallel_code_review → CrewAI

```bash
spl3 run cookbook/65_llm_splc/llm_splc.spl \
    --adapter claude_cli \
    --tools cookbook/65_llm_splc/tools.py \
    --param spl_file="cookbook/63_parallel_code_review/parallel_code_review.spl" \
    --param target="crewai" \
    --param output_file="cookbook/63_parallel_code_review/targets/crewai/parallel_code_review.py"
```

## General usage

```bash
spl3 run cookbook/65_llm_splc/llm_splc.spl \
    --adapter claude_cli \
    --tools cookbook/65_llm_splc/tools.py \
    --param spl_file="<path/to/workflow.spl>" \
    --param target="<langgraph|autogen|crewai>" \
    --param output_file="<path/to/output.py>"
```

## Cross-validation with deterministic SPLc

```bash
# Deterministic compile
spl3 splc cookbook/05_self_refine/self_refine.spl --target langgraph \
    --output cookbook/05_self_refine/targets/langgraph/self_refine_det.py

# LLM compile
spl3 run cookbook/65_llm_splc/llm_splc.spl \
    --adapter claude_cli \
    --tools cookbook/65_llm_splc/tools.py \
    --param spl_file="cookbook/05_self_refine/self_refine.spl" \
    --param target="langgraph" \
    --param output_file="cookbook/05_self_refine/targets/langgraph/self_refine_llm.py"

# Diff
diff cookbook/05_self_refine/targets/langgraph/self_refine_det.py \
     cookbook/05_self_refine/targets/langgraph/self_refine_llm.py
```

Gaps in the diff surface implicit logic the author embedded procedurally —
making the declarative intent explicit and auditable.
