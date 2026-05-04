# S2 Thinking Openrouter Qwen Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R4-thinking/tests/openrouter/qwen/S1-thinking-openrouter-qwen-1-spec.md --adapter openrouter --model qwen3.6-plus -o /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R4-thinking/tests/openrouter/qwen/S2-thinking-openrouter-qwen.mmd`

## Mermaid Diagram

```mermaid
flowchart TD
    A[Initialize Shared Context] --> B{{WHILE next_thought_needed IS true?}}
    B -->|Yes| C[CREATE FUNCTION: GenerateReasoningStep]
    C --> D[GENERATE: Call LLM]
    D --> E{{YAML Parse & Schema Valid?}}
    E -->|Valid| F[EVALUATE: Inspect Flags & Update State]
    E -->|Invalid| G[Graceful Recovery]
    G --> D
    F --> H{{next_thought_needed == true?}}
    H -->|Yes| I[Append Thought & Print Progress]
    I --> B
    H -->|No| J[Extract Final Conclusion]
    J --> K[CALL Side-effect: Persist to Disk]
    K --> L[RETURN Solution & Metadata]
    B -->|No| J
    L --> M[End]
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R4-thinking/tests/openrouter/qwen/S2-thinking-openrouter-qwen.mmd -o S2-thinking-openrouter-qwen.spl`
4. Validate: `spl3 validate S2-thinking-openrouter-qwen.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
