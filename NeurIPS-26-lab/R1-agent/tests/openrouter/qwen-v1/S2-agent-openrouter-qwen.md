# S2 Agent Openrouter Qwen Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/qwen/S1-agent-openrouter-qwen-1-spec.md --adapter openrouter --model qwen3.6-plus -o /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/qwen/S2-agent-openrouter-qwen.mmd`

## Mermaid Diagram

```mermaid
flowchart TD
    A[Initialize Workflow & Shared State] --> B[GENERATE decide_action]
    B --> C[Parse YAML Output]
    C --> D{{YAML Parsing Successful?}}
    D -->|No| E[EXCEPTION: Repair Block Scalars & Retry]
    E --> C
    D -->|Yes| F{{Action == search?}}
    F -->|Yes| G[CALL search_web]
    G --> H[Append Results to @context]
    H --> B
    F -->|No| I[GENERATE answer_question]
    I --> J[RETURN final answer & metadata]
    J --> K[End]
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/qwen/S2-agent-openrouter-qwen.mmd -o S2-agent-openrouter-qwen.spl`
4. Validate: `spl3 validate S2-agent-openrouter-qwen.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
