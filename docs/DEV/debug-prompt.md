# Debugging LLM Prompts

The SPL stack provides a `--prompt` debug flag across all LLM-powered commands. This allows developers to inspect the exact system and user prompts being sent to the adapter without actually triggering an LLM call or incurring API costs.

## Purpose

The `--prompt` flag is essential for:
1. **Troubleshooting**: Seeing how natural language requirements or Mermaid diagrams are being formatted into LLM instructions.
2. **Alignment**: Verifying that RAG examples (few-shots) and reference codebases are being correctly injected into the context.
3. **Cost Efficiency**: Previewing large prompts before execution.

## Supported Commands

The following sub-commands support the `--prompt` flag:

### 1. `spl3 text2mmd`
Inspect the prompt used to generate Mermaid diagrams from natural language.
```bash
spl3 text2mmd "build a rag agent" --adapter claude_cli --prompt
```

### 2. `spl3 mmd2spl`
Inspect the prompt that converts visual Mermaid topology into declarative SPL logic.
```bash
spl3 mmd2spl workflow.mmd --adapter ollama --prompt
```

### 3. `spl3 text2spl`
Inspect the prompt that compiles natural language directly into SPL code.
```bash
spl3 text2spl --description requirement.md --mode workflow --prompt
```

### 4. `spl3 splc compile`
Inspect the prompt used to translate SPL logical views into physical implementations (e.g., Python/PocketFlow).
```bash
spl3 splc compile agent.spl --lang python/pocketflow --llm --prompt
```

### 5. `spl3 describe` and `spl3 splc describe`
Inspect the prompts used to reverse-engineer specs from SPL or implementation files.
```bash
spl3 describe my_agent.spl --prompt
spl3 splc describe targets/python_pocketflow/agent.py --prompt
```

### 6. `spl3 compare`
Inspect the semantic comparison prompt used to measure intent entropy between two files.
```bash
spl3 compare spec1.md spec2.md --prompt
```

### 7. `spl3 vibe`
Inspect the one-shot "vibe coding" prompt, including any injected RAG few-shots or reference codebases.
```bash
spl3 vibe -d "Research agent" --target go --references ./src --prompt
```

## Output Format

When the `--prompt` flag is used, the CLI will output a clearly delimited block containing the **LLM SYSTEM PROMPT** and **LLM USER PROMPT** (where applicable), then exit immediately.

```text
======================================================================
LLM SYSTEM PROMPT:
======================================================================
You are splc, the SPL Compiler...
...

======================================================================
LLM USER PROMPT:
======================================================================
# SPL Source to Compile
...
```
