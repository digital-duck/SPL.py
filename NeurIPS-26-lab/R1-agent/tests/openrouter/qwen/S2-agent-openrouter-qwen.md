# S2 Agent Openrouter Qwen Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/qwen/S1-agent-openrouter-qwen-1-spec.md --adapter openrouter --model qwen3.6-plus -o /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/qwen/S2-agent-openrouter-qwen.mmd`

## Mermaid Diagram

```mermaid
    flowchart TD
    A([Start]) --> B[Init Shared State]
    B --> C[Invoke Decide Prompt]
    C --> D[Parse YAML Output]
    D -->|Malformed| E[Repair & Retry]
    E --> D
    D -->|Valid| F{Action Token?}
    F -->|search| G[Call Web Search]
    G --> H[Append Results]
    H --> C
    F -->|answer| I[Generate Final Answer]
    I --> J([Return Done])
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/qwen/S2-agent-openrouter-qwen.mmd -o S2-agent-openrouter-qwen.spl`
4. Validate: `spl3 validate S2-agent-openrouter-qwen.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
