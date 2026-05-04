# S3-agent-claude_cli-claude — PocketFlow Implementation

Compiled from `S3-agent-claude_cli-claude.spl`.  
Implements a research agent that iteratively searches the web and synthesises an answer using Claude (via `claude_cli`).

---

## Setup

```bash
# 1. Activate the project environment
conda activate spl123

# 2. Install dependencies (PocketFlow + PyYAML)
pip install pocketflow pyyaml

# 3. Ensure the Claude CLI is on your PATH and authenticated
claude --version

# 4. (Optional) Replace the search stub with a real provider
#    Edit search_web_tool() in s3_agent_claude_cli_claude.py
#    e.g. integrate Tavily, SerpAPI, or DuckDuckGo
```

---

## Run

```bash
# As a script
python S3-agent-claude_cli-claude_python_pocketflow.py "Who invented the telephone?"

# As a module (filename contains hyphens, so use importlib)
python -c "
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location(
    'agent', pathlib.Path(__file__).parent / 'S3-agent-claude_cli-claude_python_pocketflow.py'
)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
result = m.run_web_search_agent('What is quantum entanglement?')
print(result)
"
```

---

## Expected output pattern

```
Status     : complete
Iterations : 3

Answer:
Quantum entanglement is a phenomenon where two or more particles become
correlated in such a way that the quantum state of each particle cannot
be described independently of the others...
```

On YAML parse failure after retry:
```
Status     : error
Iterations : 1

Answer:
{'parse_error': 'no YAML fence found in: ...'}
```

On iteration exhaustion (10 loops, no `action: answer`):
```
Status     : max_iterations_reached
Iterations : 10

Answer:
(empty — agent never committed an answer)
```

---

## SPL → PocketFlow construct map

| SPL construct | PocketFlow equivalent | Location in file |
|---|---|---|
| `CREATE FUNCTION f(…) AS $$ … $$` | `PROMPT_TEMPLATE` string constant with `{param}` slots | `DECIDE_ACTION_PROMPT`, `ANSWER_QUESTION_PROMPT` |
| `WORKFLOW web_search_agent` | `build_flow()` + `run_web_search_agent()` | `build_flow`, `run_web_search_agent` |
| `INPUT @question TEXT` | `shared["question"]` set by caller | `run_web_search_agent(question)` |
| `OUTPUT @answer TEXT` | `shared["answer"]` read by caller | `run_web_search_agent` return value |
| `@var := value` | `shared["var"] = value` in `Node.post` | Every node's `post()` |
| `WHILE cond AND iter < 10 DO … END` | `LoopCheckNode` returning `"continue"` / `"exit"`; `search_web -"loop_check">> loop_check` back-edge | `LoopCheckNode`, `build_flow` |
| `GENERATE fn(@a, @b) INTO @var` | `Node.exec` calling `call_llm(prompt.format(…))` | `DecideActionNode`, `AnswerQuestionNode` |
| `CALL tool(@arg) INTO @var` | `Node.exec` calling `tool_tool(arg)` | `ParseYamlNode`, `ForceBlockScalarsNode`, `RetryParseNode`, `SearchWebNode` |
| `EVALUATE @v WHEN contains(…) THEN … ELSE … END` | `Node.post` returning an action string; Flow edges routing to different successor nodes | `ParseYamlNode.post`, `EvaluateDecisionNode.post` |
| Nested `EVALUATE` (retry path) | `RetryParseNode.post` with two return paths (`"error"` / `"evaluate"`) | `RetryParseNode` |
| `RETURN @var WITH status = 'error'` | `shared["status"] = "error"` + terminal action (no successor mapped) | `RetryParseNode.post` |
| `RETURN @answer WITH status = 'complete'` | `shared["status"] = "complete"` + `"done"` terminal action | `AnswerQuestionNode.post` |
| `@iteration := @iteration + 1` | `shared["iteration"] += 1` at start of `DecideActionNode.post` | `DecideActionNode.post` |
| `@context := @context + '…'` | `shared["context"] = context + f"…"` | `SearchWebNode.post` |