# S2 Agent Openrouter Deepseek Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/deepseek/S1-agent-openrouter-deepseek-1-spec.md --adapter openrouter --model deepseek/deepseek-v4-flash -o /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/deepseek/S2-agent-openrouter-deepseek.mmd`

## Mermaid Diagram

```mermaid
flowchart TD
    A[Start] --> B[DecideAction]
    B --> C{{Action?}}
    C -->|search| D[SearchWeb]
    C -->|answer| E[AnswerQuestion]
    D --> B
    E --> F[End]
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/deepseek/S2-agent-openrouter-deepseek.mmd -o S2-agent-openrouter-deepseek.spl`
4. Validate: `spl3 validate S2-agent-openrouter-deepseek.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
