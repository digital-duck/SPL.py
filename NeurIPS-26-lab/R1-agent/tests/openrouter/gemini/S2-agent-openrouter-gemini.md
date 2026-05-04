# S2 Agent Openrouter Gemini Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/gemini/S1-agent-openrouter-gemini-1-spec.md --adapter openrouter --model google/gemini-3-flash-preview -o /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/gemini/S2-agent-openrouter-gemini.mmd`

## Mermaid Diagram

```mermaid
    flowchart TD
    Start([Start]) --> InitVars[Initialize Question and Context]
    InitVars --> DecideAction[DecideAction Logical Function]
    DecideAction --> EvaluateAction{Evaluate Action}
    EvaluateAction -->|search| WebSearch[CALL Web Search Tool]
    WebSearch --> UpdateContext[Update Research Context]
    UpdateContext --> DecideAction
    EvaluateAction -->|answer| AnswerQuestion[AnswerQuestion Logical Function]
    AnswerQuestion --> OutputResult[Synthesize Final Response]
    OutputResult --> End([Return status=done])
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/gemini/S2-agent-openrouter-gemini.mmd -o S2-agent-openrouter-gemini.spl`
4. Validate: `spl3 validate S2-agent-openrouter-gemini.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
