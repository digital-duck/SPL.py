# R3: pocketflow-judge — NDD Round-Trip Experiment

LLM-as-Judge evaluator-optimizer loop. A Generator node creates product descriptions; a Judge node scores them (clarity + persuasiveness, 1–10); feedback drives revision until score ≥ 7 or max 3 attempts.

---

## Environment

Set these 4 vars before running any step. Change ADAPTER / MODEL_ID / MODEL for each of the 4 runs.

```bash
export RECIPE=judge
export ADAPTER=openrouter
export MODEL=qwen
export MODEL_ID=qwen3.6-plus

export BASE=~/projects/digital-duck/SPL.py/NeurIPS-26-lab/R3-$RECIPE
export SRC=$BASE/src/pocketflow-$RECIPE
export OUT=$BASE/tests/$ADAPTER/$MODEL
```

### 4 Model Configurations

| Run | ADAPTER | MODEL_ID | MODEL |
|-----|---------|----------|-------|
| 1 | `claude_cli` | `claude-sonnet-4-6` | `sonnet` |
| 2 | `ollama` | `gemma3` | `gemma3` |
| 3 | `openrouter` | `google/gemini-3-flash-preview` | `gemini` |
| 4 | `openrouter` | `deepseek/deepseek-v4-flash` | `deepseek` |

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
- Generator and Judge nodes both present
- Feedback loop edge from Judge back to Generator is present
- Exit condition (score ≥ 7 or max attempts) represented
- No dangling or duplicate nodes

Fix any errors directly in the `.mmd` file, then proceed.

---

## S3 — `spl3 mmd2spl` → SPL workflow

```bash
spl3 mmd2spl $OUT/S2-$RECIPE-$ADAPTER-$MODEL.mmd \
  --adapter $ADAPTER --model $MODEL_ID \
  -o $OUT/S3-$RECIPE-$ADAPTER-$MODEL.spl
```

Validate before continuing:
```bash
spl3 validate $OUT/S3-$RECIPE-$ADAPTER-$MODEL.spl
```

---

## S3-run — `spl3 run` → smoke-test the SPL workflow

Run the SPL workflow directly (no compilation) to verify the logic executes end-to-end.

```bash
spl3 run $OUT/S3-$RECIPE-$ADAPTER-$MODEL.spl \
  --adapter $ADAPTER --model $MODEL_ID \
  -p "initial_state=Write a one-paragraph description of the RAG pattern in AI systems" \
  2>&1 | tee $OUT/S3-$RECIPE-$ADAPTER-$MODEL-spl-$(date +%Y%m%d_%H%M%S).md
```

Expected: the Generator produces a draft, the Judge evaluates it; if score ≥ 7 returns `status=pass`, otherwise iterates up to 3 times and returns `status=retry`.

---

## ⚠️ HUMAN CHECKPOINT — verify SPL before S4

Inspect the run output and the `.spl` file for qwen silent-bug patterns before compiling:

- [ ] All `CREATE FUNCTION` bodies use `{param}` single-braces (not `{{param}}`)
- [ ] Every function name in a `GENERATE` call has a matching `CREATE FUNCTION` declaration
- [ ] All `WHILE` loop variables are initialised before the loop
- [ ] `CALL` targets are stdlib tools, not LLM-backed `CREATE FUNCTION`s
- [ ] No invented statement keywords (`LOG`, etc.)

Fix any issues in the `.spl` file, then proceed.

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
```

---

## Expected Issues

Steps may not run perfectly on the first attempt — that is expected. Common failure points:

- **S1**: Multi-file recipe; if spec is thin, check that all `.py` files were included
- **S2**: Feedback loop edge is easy to miss; check the back-edge in the diagram carefully
- **S3**: SPL may have syntax errors; run `spl3 validate` and fix before S4
- **S4**: The iterative scoring logic is complex; compiled code may need manual fixes
- **S5**: If S4 output is functionally broken, S5 spec will be poor — fix S4 first

Record issues and fixes in `$OUT/notes.md`.
