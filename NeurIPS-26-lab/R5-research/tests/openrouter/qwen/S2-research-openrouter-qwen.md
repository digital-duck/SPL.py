# S2 Research Openrouter Qwen Workflow

Generated with [SPL](https://github.com/digital-duck/SPL) using: `spl3 text2mmd /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/openrouter/qwen/S1-research-openrouter-qwen-1-spec.md --adapter openrouter --model qwen3.6-plus -o /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/openrouter/qwen/S2-research-openrouter-qwen.mmd`

## Mermaid Diagram

```mermaid
    flowchart TD
    A([Start]) --> B["Initialize Context<br/>@topic, @loop_count=0"]
    B --> C["GENERATE plan_queries<br/>Output: @current_queries"]
    C --> D["CALL search_web<br/>For each query"]
    D --> E["GENERATE extract_facts<br/>Distill snippets"]
    E --> F["Aggregate Results<br/>to @notes"]
    F --> G{"EVALUATE<br/>@synthesis_action?"}
    G -->|"research & count < 2"| H["Increment @loop_count<br/>Store @feedback"]
    H --> C
    G -->|finalize| I["CREATE FUNCTION assess_and_report<br/>Generate @report"]
    I --> J["WRITE @report to File<br/>Console Log"]
    J --> K([End])
```

## Usage Options

### For SPL Development
1. Review the workflow diagram above
2. Edit the mermaid code if needed
3. Generate SPL code: `spl3 mmd2spl /home/wengong/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/openrouter/qwen/S2-research-openrouter-qwen.mmd -o S2-research-openrouter-qwen.spl`
4. Validate: `spl3 validate S2-research-openrouter-qwen.spl`

### For General Use
1. Use the `.mmd` file with any Mermaid-compatible tool
2. Copy the diagram code for documentation, presentations, or websites
3. Edit the visual workflow and regenerate as needed

---

**Learn more**: [SPL Repository](https://github.com/digital-duck/SPL) | [Documentation](https://github.com/digital-duck/SPL#readme)
