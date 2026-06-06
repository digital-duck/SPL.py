# S2 Judge Openrouter Qwen Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R3-judge/tests/openrouter/qwen/S1-judge-openrouter-qwen-1-spec.md --adapter openrouter --model qwen3.6-plus -o /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R3-judge/tests/openrouter/qwen/S2-judge-openrouter-qwen.mmd`

## Mermaid Diagram

```mermaid
    flowchart TD
    A([Start]) --> B["Initialize<br/>Shared State"]
    B --> C["GENERATE<br/>generate_description"]
    C --> D["GENERATE<br/>evaluate_description"]
    D --> E{Score >= 7?}
    E -->|Yes| F["RETURN<br/>pass status"]
    E -->|No| G["Increment<br/>@attempts"]
    G --> H["Store<br/>@feedback"]
    H --> I{Attempts < 3?}
    I -->|Yes| C
    I -->|No| F
    F --> J["Persist Shared<br/>State & Score"]
    J --> K([End])
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R3-judge/tests/openrouter/qwen/S2-judge-openrouter-qwen.mmd -o S2-judge-openrouter-qwen.spl`
4. Validate: `spl3 validate S2-judge-openrouter-qwen.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
