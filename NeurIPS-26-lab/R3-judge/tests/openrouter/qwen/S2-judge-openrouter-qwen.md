# S2 Judge Openrouter Qwen Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R3-judge/tests/openrouter/qwen/S1-judge-openrouter-qwen-1-spec.md --adapter openrouter --model qwen3.6-plus -o /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R3-judge/tests/openrouter/qwen/S2-judge-openrouter-qwen.mmd`

## Mermaid Diagram

```mermaid
flowchart TD
    A[Start: Initialize @task and @attempts=0] --> B[GENERATE @draft via Generator LLM]
    B --> C[GENERATE @judgment via Judge LLM]
    C --> D{{WHILE @attempts < 3 AND @score < 7}}
    D -->|True| E{{EVALUATE @verdict == PASS OR @score >= 7}}
    E -->|Yes| F[Assign @final_description and Break Loop]
    E -->|No| G[Increment @attempts and Update @feedback]
    G -->|Retry| B
    F --> H[Loop Condition Met or Exhausted]
    D -->|False| H
    H --> I[RETURN @final_description WITH metadata]
    I --> J[CALL write_file Optional SideEffect]
    J --> K[End]
    B -->|Error| L[EXCEPTION Handler: ParseError or Timeout]
    C -->|Error| L
    L --> M[Fallback: Return last valid @draft with status=degraded]
    M --> K
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R3-judge/tests/openrouter/qwen/S2-judge-openrouter-qwen.mmd -o S2-judge-openrouter-qwen.spl`
4. Validate: `spl3 validate S2-judge-openrouter-qwen.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
