## S3-research-claude_cli-sonnet — Deep Research (PocketFlow)

### Setup

```bash
# 1. Activate the project environment
conda activate spl123

# 2. Install PocketFlow (if not already present)
pip install pocketflow

# 3. Ensure the claude CLI is on PATH and authenticated
claude --version
```

### Run

```bash
# Positional args: <topic> [output-file]
python S3-research-claude_cli-sonnet_python_pocketflow.py "quantum computing applications" report.txt

python /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-research/tests/claude_cli/sonnet/targets/python_pocketflow/S3-research-claude_cli-sonnet_python_pocketflow.py \
"quantum computing applications" report.txt


# Or import as a library (filename contains hyphens, so use importlib)
python - <<'EOF'
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location(
    'research', pathlib.Path('S3-research-claude_cli-sonnet_python_pocketflow.py')
)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
report = m.run_deep_research("quantum computing applications", "report.txt")
print(report[:500])
EOF
```

### Expected output pattern

```
report.txt written with a multi-section research report.
stdout: full report text (1 000–3 000 words typical).

Console (PocketFlow default logging):
  [InitNode]          ...
  [PlannerNode]       ...
  [LoopCheckNode]     action=continue
  [ExtractQueriesNode]...
  [SearchWebNode]     ...  ← 3 parallel searches
  [ExtractFactsNode]  ...  ← 3 parallel extractions
  [AccumulateNotesNode]...
  [SynthesizerNode]   ...
  [EvaluateDecisionNode] action=finalize | research
  ...
  [WriteFileNode]     written:report.txt
```

The loop runs **at most 3 iterations**. It exits early when the synthesizer emits `DECISION: finalize` or when `loop_count` reaches 2 (forcing `write_concise_report`).

### SPL → PocketFlow construct map

| SPL construct | PocketFlow equivalent | Location |
|---|---|---|
| `CREATE FUNCTION name(...)` | Module-level prompt-template string `NAME_PROMPT` | top of file |
| `WORKFLOW deep_research INPUT/OUTPUT` | `build_flow()` + `run_deep_research()` | `build_flow`, `run_deep_research` |
| `@var := value` | `shared["var"] = value` in `Node.post` | `InitNode.post` |
| `GENERATE fn(...) INTO @var` | `Node.exec` calls `call_llm(PROMPT.format(...))`, `Node.post` writes `shared["var"]` | each `*Node` |
| `WHILE @loop_count < 3 DO` | `LoopCheckNode.post` returns `"done"` / `"continue"` / `"max_loops"` | `LoopCheckNode` |
| `EVALUATE @var WHEN contains("x") THEN … ELSE` | `Node.post` returns different action strings; edges wired with `-"action">>` | `LoopCheckNode`, `EvaluateDecisionNode` |
| `CALL PARALLEL f(@a) INTO @r1, f(@b) INTO @r2 END` | `concurrent.futures.ThreadPoolExecutor(max_workers=3)` inside `Node.exec` | `SearchWebNode`, `ExtractFactsNode` |
| `CALL search_web(@q)` (tool call) | `search_web()` helper function via `subprocess` / claude CLI | `search_web()` |
| `CALL write_file(@out, @report)` (tool call) | `open(path,"w").write(content)` in `WriteFileNode.exec` | `WriteFileNode` |
| `RETURN @report WITH status="complete"` | `shared["report"]` populated; `Flow.run` returns; `write_result` tag set | `WriteFileNode.post` |
| `@loop_count := @loop_count + 1` | `new_count = loop_count + 1` then `shared["loop_count"] = new_count` | `ExtractFeedbackNode` |