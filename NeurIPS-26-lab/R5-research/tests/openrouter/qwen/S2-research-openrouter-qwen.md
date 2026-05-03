# S2 Research Openrouter Qwen Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/openrouter/qwen/S1-research-openrouter-qwen-1-spec.md --adapter openrouter --model qwen3.6-plus -o /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/openrouter/qwen/S2-research-openrouter-qwen.mmd`

## Mermaid Diagram

```mermaid
flowchart TD
    A[Start: Initialize Shared State] --> B[plan_queries: GENERATE Search Directives]
    B --> C[Parallel CALL Web Search for @queries]
    C --> D[extract_facts: GENERATE & Aggregate Factual Notes]
    D --> E{{WHILE @loop_count < 2}}
    E -->|Yes| F[assess_and_synthesize: GENERATE YAML Decision]
    F -->|Success| G{{EVALUATE Action Field}}
    G -->|research| H[Update @feedback & Increment @loop_count]
    H --> B
    G -->|finalize| I[write_report: GENERATE Final Markdown]
    E -->|No| I
    I --> J[CALL Write File to Disk]
    J --> K[RETURN Report & Metadata]
    K --> L[End]
    F -->|API/Parsing Error| M[EXCEPTION WHEN Handler]
    M --> L
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/openrouter/qwen/S2-research-openrouter-qwen.mmd -o S2-research-openrouter-qwen.spl`
4. Validate: `spl3 validate S2-research-openrouter-qwen.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
