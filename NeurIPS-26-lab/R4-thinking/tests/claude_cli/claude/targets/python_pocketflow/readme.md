## S3-thinking-claude_cli-sonnet

Chain of Thought reasoning compiled from `S3-thinking-claude_cli-sonnet.spl` to Python / PocketFlow.

### Setup

```bash
conda activate spl123
pip install pocketflow pyyaml
# Claude CLI must be on PATH and authenticated
claude --version
```

### Run

```bash
# Minimal
python S3-thinking-claude_cli-sonnet_python_pocketflow.py "Why is the sky blue?"

# Full options (matching SPL INPUT defaults)
python /home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/R4-thinking/tests/claude_cli/sonnet/targets/python_pocketflow/S3-thinking-claude_cli-sonnet_python_pocketflow.py \
  "Why is fibonacci sequence important?" \
  --max-iterations 5 \
  --trace-file chain_of_thought_trace.md \
  --model claude-sonnet-4-6
```

### Expected Output Pattern

```
[Thinking] Light from the sun contains all visible wavelengths. Rayleigh scattering...
[Plan]     Confirm scattering formula, check observer angle dependency...

[Thinking] Rayleigh scattering scales as 1/λ⁴, so shorter blue wavelengths scatter...
[Plan]     Conclude — scattering asymmetry fully explains the observation...

============================================================
SOLUTION (status=complete)
============================================================
Rayleigh scattering of sunlight by atmospheric molecules preferentially scatters
shorter (blue) wavelengths in all directions, making the sky appear blue to an
observer looking anywhere except directly at the sun.
```

Trace file `chain_of_thought_trace.md` is written incrementally — one `--- Thought N ---` block per iteration.

### SPL → PocketFlow Construct Map

| SPL Construct | PocketFlow / Python Equivalent |
|---|---|
| `WORKFLOW ChainOfThought` | `_build_flow()` assembling three `Node` subclasses into a `Flow` |
| `INPUT @problem TEXT, @max_iterations INT := 5, ...` | `run_s3_thinking_chain_of_thought(problem, max_iterations=5, ...)` parameters; stored in `shared` dict |
| `OUTPUT @solution TEXT` | `shared["solution"]` written by `S3ThinkingFinalizeNode.post`; returned by public API |
| Variable initialization block (`@thoughts := "[]"; ...`) | `S3ThinkingInitNode.exec` populates `shared` with zero-state dict |
| `WHILE cond DO ... END` (outer) | `S3ThinkingThinkNode.prep` checks condition; returns `None` to break, data-dict to continue; `post` routes `"continue"` → self or `"done"` → finalize |
| `WHILE @yaml_valid="false" AND @retry_count<3 DO ... END` (inner) | Python `while` loop inside `S3ThinkingThinkNode.exec` |
| `GENERATE ChainOfThoughtStep(...) INTO @thought_data` | `_call_llm(prompt, model)` via `subprocess.run(["claude", ...])` |
| `CREATE FUNCTION ChainOfThoughtStep(...)` | `_cot_prompt(problem, thoughts_text, last_plan, thought_number)` returning the prompt string |
| `CALL format_thoughts_to_text(@thoughts)` | `_format_thoughts_to_text(thoughts)` |
| `CALL extract_last_plan(@thoughts)` | `_extract_last_plan(thoughts)` |
| `CALL validate_yaml_fields(@thought_data)` | `_validate_yaml_fields(text)` — returns `"true"` / `"false"` |
| `CALL write_file(@trace_file, ..., "a")` | `_write_file(path, content, mode)` |
| `CALL append_thought(@thoughts, @thought_data)` | `_append_thought(thoughts, yaml_text)` — mutates and returns list |
| `CALL extract_yaml_field(@thought_data, "field")` | `_extract_yaml_field(text, field)` |
| `CALL print_thought_progress(...)` | `_print_thought_progress(thinking, plan)` |
| `@solution := @current_thinking; RETURN ... WITH status="complete"` | `S3ThinkingFinalizeNode`: `prep` reads `current_thinking`, `post` writes `solution` + `status="complete"` |
| `EXCEPTION WHEN BudgetExceeded THEN RETURN ... WITH status="budget_limit"` | `except subprocess.CalledProcessError` around `flow.run(shared)`; sets `status="budget_limit"` |
| Node wiring (`init→think→continue→think / done→finalize`) | `init - "think" >> think`, `think - "continue" >> think`, `think - "done" >> finalize` |