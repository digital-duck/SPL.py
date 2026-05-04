# R2: pocketflow-rag — NDD Round-Trip Experiment

LLM-powered ReAct research agent. Iterative decide→search→accumulate loop using PocketFlow nodes, with a YAML-structured decision output and web search tool.

---

## Environment

Set these 4 vars before running any step. Change ADAPTER / MODEL_ID / MODEL for each of the 4 runs.

### 4 Model Configurations

see more models in `/home/papagame/projects/digital-duck/SPL.py/NeurIPS-26-lab/shortlist-models.md`

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
| 8 | `openrouter` |  'z-ai/glm-5.1' | `z-ai` |



```bash

# ollama
export ADAPTER=ollama
export MODEL=gemma3  
export MODEL_ID=gemma3

# openrouter
export ADAPTER=openrouter

# export MODEL=gpt  
# export MODEL_ID=openai/gpt-5.4   # .spl fail to run

# export MODEL=z-ai
# export MODEL_ID=z-ai/glm-5.1   # failed to generate .spl

# export MODEL=gemini
# export MODEL_ID=google/gemini-3-flash-preview  # ok

export ADAPTER=openrouter
export MODEL=qwen
export MODEL_ID=qwen3.6-plus  # ok

conda activate spl123
# claude_cli
export ADAPTER=claude_cli
export MODEL=sonnet  
export MODEL_ID=claude-sonnet-4-6

export RECIPE=rag
export BASE=~/projects/digital-duck/SPL.py/NeurIPS-26-lab/R2-$RECIPE
export SRC=$BASE/src/pocketflow-$RECIPE
export OUT=$BASE/tests/$ADAPTER/$MODEL
```


---

## S1 — `spl3 splc describe` → spec1

Convert original PocketFlow code to spec. `--include-docs` pulls in `README.md` for original intent context.

```bash

spl3 splc describe $SRC \
  --include-docs \
  --adapter $ADAPTER --model $MODEL_ID \
  -o $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md
```

---

## S2 — `spl3 text2mmd` → Mermaid diagram

```bash
spl3 text2mmd $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  --adapter $ADAPTER --model $MODEL_ID \
  -o $OUT/S2-$RECIPE-$ADAPTER-$MODEL.mmd
```

---

## ⚠️ HUMAN CHECKPOINT — review diagram before S3

Open `$OUT/S2-$RECIPE-$ADAPTER-$MODEL.mmd` and verify:
- All nodes present and correctly labeled
- Edges wired in correct direction
- Back-edge for the iterative loop is present
- No dangling or duplicate nodes

Fix any errors directly in the `.mmd` file, then proceed.

---

## S3 — `spl3 mmd2spl` → SPL workflow

```bash
spl3 mmd2spl $OUT/S2-$RECIPE-$ADAPTER-$MODEL.mmd \
  --adapter $ADAPTER --model $MODEL_ID \
  -o $OUT/S3-$RECIPE-$ADAPTER-$MODEL.spl
```

backup the original .spl script

```bash
cp $OUT/S3-$RECIPE-$ADAPTER-$MODEL.spl $OUT/S3-$RECIPE-$ADAPTER-$MODEL.spl-orig
```

Validate before continuing:

```bash
spl3 validate $OUT/S3-$RECIPE-$ADAPTER-$MODEL.spl
```


## ⚠️ CHECKPOINT

Test the .spl

```bash
spl3 run $OUT/S3-$RECIPE-$ADAPTER-$MODEL.spl \
  --adapter $ADAPTER --model $MODEL_ID \
  --claude-allowed-tools WebSearch \
  --param question="what is machine learning" \
    2>&1 | tee $OUT/S3-$RECIPE-$ADAPTER-$MODEL-spl-$(date +%Y%m%d_%H%M%S).md 

```


---

## S4 — `spl3 splc compile` → Python/PocketFlow

```bash
spl3 splc compile $OUT/S3-$RECIPE-$ADAPTER-$MODEL.spl \
  --lang python/pocketflow --llm \
  --adapter $ADAPTER --model $MODEL_ID \
  --out-dir $OUT/targets/python_pocketflow \
  --overwrite

# rename to S4 convention (splc auto-names output from .spl stem)
mv $OUT/targets/python_pocketflow/S3-$RECIPE-$ADAPTER-$MODEL*.py \
   $OUT/targets/python_pocketflow/S4-$RECIPE-$ADAPTER-$MODEL.py
```

Gemini CLI made change to .py, 

---

## S5 — `spl3 splc describe` → spec2

Convert reconstructed code to spec. No `--include-docs` — reconstructed directory has no README.

```bash
spl3 splc describe $OUT/targets/python_pocketflow/S4-$RECIPE-$ADAPTER-$MODEL.py \
  --adapter $ADAPTER --model $MODEL_ID \
  -o $OUT/S5-$RECIPE-$ADAPTER-$MODEL-2-spec.md
```

---

## S6 — `spl3 compare` → closure score

Judge is fixed at `claude_cli / claude-opus-4-6` regardless of which model generated the specs.

```bash
spl3 compare \
  $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  $OUT/S5-$RECIPE-$ADAPTER-$MODEL-2-spec.md \
  --adapter claude_cli --model claude-opus-4-6 \
  -o $OUT/S6-$RECIPE-$ADAPTER-$MODEL-spec-diff.md

# use gemini as Judge
spl3 compare \
  $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  $OUT/S5-$RECIPE-$ADAPTER-$MODEL-2-spec.md \
  --adapter $ADAPTER --model $MODEL_ID \
  -o $OUT/S6-$RECIPE-$ADAPTER-$MODEL-spec-diff-gemini.md

```

---

## 🧪 ABLATION — `spl3 vibe` → One-Shot Baseline

Mimic "vibe coding" by bypassing the Mermaid and SPL intermediate representations. This establishes the baseline **Intent Entropy** ($\Delta S$) for direct generation.

```bash
# Generate code directly from the S1 spec
spl3 vibe --description $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  --target python/pocketflow \
  --adapter $ADAPTER --model $MODEL_ID \
  -o $OUT/targets/python_pocketflow/S4-$RECIPE-$ADAPTER-$MODEL-vibe.py

# Describe the vibe-coded result
spl3 splc describe $OUT/targets/python_pocketflow/S4-$RECIPE-$ADAPTER-$MODEL-vibe.py \
  --adapter $ADAPTER --model $MODEL_ID \
  -o $OUT/S5-$RECIPE-$ADAPTER-$MODEL-vibe-spec.md

# Compare vibe-coded spec vs original spec
spl3 compare \
  $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  $OUT/S5-$RECIPE-$ADAPTER-$MODEL-vibe-spec.md \
  --adapter claude_cli --model claude-opus-4-6 \
  -o $OUT/S6-$RECIPE-$ADAPTER-$MODEL-vibe-diff.md
```

---

## Expected Issues

Steps may not run perfectly on the first attempt — that is expected. Common failure points:

- **S1**: Multi-file recipe; if spec is thin, check that all `.py` files were included
- **S2**: LLM may generate invalid Mermaid syntax; fix manually before S3
- **S3**: SPL may have syntax errors; run `spl3 validate` and fix before S4
- **S4**: Compiled Python may have import errors or broken node wiring; fix and re-run
- **S5**: If S4 output is functionally broken, S5 spec will be poor — fix S4 first

Record issues and fixes in `$OUT/notes.md`.
