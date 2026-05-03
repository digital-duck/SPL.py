# S2 Agent Openrouter Gpt Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/gpt/S1-agent-openrouter-gpt-1-spec.md --adapter openrouter --model openai/gpt-5.4 -o /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/gpt/S2-agent-openrouter-gpt.mmd`

## Mermaid Diagram

```mermaid
flowchart TD
    A[Start] --> B[Initialize @question, @context, @search_query, @answer]
    B --> C[GENERATE DecideAction with question and context]
    C --> D[Parse and validate YAML output]
    D --> E{{YAML valid?}}
    E -->|No| F[EXCEPTION handle parse error or repair YAML]
    F --> G{{Recovered?}}
    G -->|Yes| D
    G -->|No| N[RETURN failure status metadata]
    E -->|Yes| H{{Action == search?}}
    H -->|Yes| I[Store @search_query]
    I --> J[CALL DuckDuckGo search_web max_results=5]
    J --> K{{Tool call succeeded?}}
    K -->|No| L[EXCEPTION handle tool failure]
    L --> N
    K -->|Yes| M[Append SEARCH and RESULTS block to @context]
    M --> C
    H -->|No| O[Store decision model answer into @context]
    O --> P[GENERATE AnswerQuestion with question and context into @answer]
    P --> Q[RETURN @answer with status done]
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R1-agent/tests/openrouter/gpt/S2-agent-openrouter-gpt.mmd -o S2-agent-openrouter-gpt.spl`
4. Validate: `spl3 validate S2-agent-openrouter-gpt.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
