# S2 Research Openrouter Gemini Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/openrouter/gemini/S1-research-openrouter-gemini-1-spec.md --adapter openrouter --model google/gemini-3-flash-preview -o /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/openrouter/gemini/S2-research-openrouter-gemini.mmd`

## Mermaid Diagram

```mermaid
    flowchart TD
    Start([Start]) --> Planner[Planner: Generate Queries]
    subgraph MapReduce[Research Phase]
    Researcher["Researcher: Map Queries<br/>to Web Search"]
    ToolCall["Tool: search_web()"]
    Extractor["Extractor: Reduce Results<br/>to Fact Notes"]
    Researcher --> ToolCall
    ToolCall --> Extractor
    end
    Planner --> Researcher
    Extractor --> Synthesizer{Synthesizer:<br/>Evaluate Info}
    Synthesizer -->|Need More Info<br/>AND Loop < 2| Feedback[Generate Feedback]
    Feedback --> Planner
    Synthesizer -->|Sufficient Info<br/>OR Max Loops| Finalize[Finalize Markdown Report]
    Finalize --> End([End])
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/openrouter/gemini/S2-research-openrouter-gemini.mmd -o S2-research-openrouter-gemini.spl`
4. Validate: `spl3 validate S2-research-openrouter-gemini.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
