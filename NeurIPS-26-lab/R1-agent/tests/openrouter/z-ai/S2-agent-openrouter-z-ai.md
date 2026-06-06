# S2 Agent Openrouter Z Ai Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/z-ai/S1-agent-openrouter-z-ai-1-spec.md --adapter openrouter --model z-ai/glm-5.1 -o /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/z-ai/S2-agent-openrouter-z-ai.mmd`

## Mermaid Diagram

```mermaid
flowchart TD
    A[Start: Read @question & Init @context] --> B[Generate DecideAction]
    B --> X{{YAML Parsed OK?}}
    X -->|Yes| C{{Action contains search?}}
    X -->|No: YAMLParseError| Y[Retry: Fix block-scalar formatting]
    Y --> Z{{Retry Parsed OK?}}
    Z -->|Yes| C
    Z -->|No| W[Raise ValueError]
    W --> END1[End: Error]
    C -->|search| D[Call search_web_duckduckgo]
    D --> E[Append results to @context]
    E --> B
    C -->|answer| F[Save @decision.answer to @context]
    F --> G[Generate AnswerQuestion]
    G --> H[Return @answer & Write File]
    H --> END2[End: Complete]
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/z-ai/S2-agent-openrouter-z-ai.mmd -o S2-agent-openrouter-z-ai.spl`
4. Validate: `spl3 validate S2-agent-openrouter-z-ai.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
