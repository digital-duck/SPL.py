# S2 Agent Openrouter Gemini Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/gemini/S1-agent-openrouter-gemini-1-spec.md --adapter openrouter --model google/gemini-3-flash-preview -o /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/gemini/S2-agent-openrouter-gemini.mmd`

## Mermaid Diagram

```mermaid
flowchart TD
    Start[Start Workflow] --> Init[Initialize @context and @question]
    Init --> Decide[GENERATE DecideAction]
    Decide --> Eval{{EVALUATE action}}
    Eval -->|search| Search[CALL search_web_duckduckgo]
    Search --> Update[Append results to @context]
    Update --> Decide
    Eval -->|answer| Answer[GENERATE AnswerQuestion]
    Answer --> Terminate[RETURN final answer and context]
    Terminate --> End[End]
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/gemini/S2-agent-openrouter-gemini.mmd -o S2-agent-openrouter-gemini.spl`
4. Validate: `spl3 validate S2-agent-openrouter-gemini.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
