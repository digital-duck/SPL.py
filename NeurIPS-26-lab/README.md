
# experimental protocol for NeurIPS-2026 NDD round-trip closure test

see `/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab`

Total number of experiments: 5 recipes x 4 models = 20

## workflow

5 Recipes:
	R : {
        R1: agent, 
        R2: rag, 
        R3: judge, 
        R4: thinking, 
        R5: research
    }

stored in env var RECIPE

create sub-folders for each recipe (DONE)
```bash
mkdir -p src tests/claude_cli/sonnet tests/ollama/gemma3 \
    tests/openrouter/gemini tests/openrouter/deepseek  tests/openrouter/claude \
    tests/openrouter/gpt tests/openrouter/qwen  tests/openrouter/z-ai

```


## LLM 

LLM models are accessible via SPL adapters

### 3 Adapters:
	A : {claude_cli, ollama, openrouter}
stored in  env var ADAPTER

### 4 Models:
	M : {sonnet, gemma3, gemini, deepseek}
	Model_ID : {sonnet-4-6, gemma3, google/gemini-3-flash-preview, deepseek/deepseek-v4-flash}
stored in  env var MODEL_ID

see all available models in `/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/shortlist-models.md`

| Run | ADAPTER | MODEL_ID | MODEL |
|-----|---------|----------|-------|
| 1 | `claude_cli` | 'claude-sonnet-4-6' | `sonnet` |
| 2 | `ollama`     | 'gemma3' | `gemma3` |
| 3 | `openrouter` | 'google/gemini-3-flash-preview' | `gemini` |
| 4 | `openrouter` | 'deepseek/deepseek-v4-flash' | `deepseek` |
| 5 | `openrouter` | 'anthropic/claude-sonnet-4.6' | `claude` |
| 5 | `openrouter` | 'anthropic/claude-opus-4.6' | `claude` |
| 6 | `openrouter` | 'openai/gpt-5.4' | `gpt` |
| 7 | `openrouter` | 'qwen/qwen3.6-plus' | `qwen` |
| 7 | `openrouter` | 'qwen/qwen3.6-flash' | `qwen` |
| 7 | `openrouter` | 'qwen/qwen3.6-35b-a3b' | `qwen` |
| 7 | `openrouter` | 'qwen/qwen3.6-max-preview' | `qwen` |
| 7 | `openrouter` | 'qwen/qwen3.6-27b' | `qwen` |
| 8 | `openrouter` | 'z-ai/glm-5.1' | `z-ai` |

## SPL round-trip pipeline steps:

7 steps including Human review of workflow chart

S: {
    S1: spl3 splc describe 
        - convert original pocketflow recipe to spec (--include-docs)
        - output: S1-<recipe>-<adapter>-<model>-1-spec.md

    S2: spl3 text2mmd
        - generate Mermaid chart from Section 0 of spec.md
        - output: S2-<recipe>-<adapter>-<model>.mmd

    Human: review workflow chart

    S3: spl3 mmd2spl
        - convert Mermaid chart to SPL workflow script
        - output: S3-<recipe>-<adapter>-<model>.spl

    S4: spl3 splc --target python/pocketflow --llm
        - compile from .spl into pocketflow python code
        - output: targets/python_pocketflow/S4-<recipe>-<adapter>-<model>.py (there may be multiple files include readme.md)

    S5: spl3 splc describe 
        - convert generated pocketflow python code to spec
        - output: S5-<recipe>-<adapter>-<model>-2-spec.md

    S6: spl3 compare 1-spec.md 2-spec.md
        - semantic compare between 1st generated spec and 2nd generated spec
        - output: S6-<recipe>-<adapter>-<model>-spec-diff.md

}

