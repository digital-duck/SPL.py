# R5: pocketflow-deep-research — NDD Round-Trip Experiment

Recursive map-reduce research agent. Plans search queries, gathers information in parallel via batch processing, extracts facts, and synthesizes a comprehensive report. Loops back to fill knowledge gaps until the report is complete.

---

## Environment

Set these 4 vars before running any step. Change ADAPTER / MODEL_ID / MODEL for each of the 4 runs.

```bash
export RECIPE=research
export ADAPTER=openrouter                        # adapter name
export MODEL=gemini                              # short name used in output filenames
export MODEL_ID=google/gemini-3-flash-preview    # full model ID passed to --model

export BASE=~/projects/digital-duck/SPL.py/NeurIPS-26-lab/R5-$RECIPE
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
- Plan, Search (parallel batch), Extract, Synthesize nodes all present
- Parallel batch edges correctly shown
- Gap-fill loop back-edge present
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
Web searches use the stdlib `search_web` tool (DuckDuckGo, no API key needed).

> **Note:** Check the WORKFLOW INPUT declarations in the generated `.spl` and adjust `-p` param
> names accordingly. If the model added an output path param, supply it here.

```bash
spl3 run $OUT/S3-$RECIPE-$ADAPTER-$MODEL.spl \
  --adapter $ADAPTER --model $MODEL_ID \
  -p "topic=PocketFlow minimalist LLM framework" \
  2>&1 | tee $OUT/S3-$RECIPE-$ADAPTER-$MODEL-spl-$(date +%Y%m%d_%H%M%S).md
```

Expected: the workflow runs multiple research iterations (plan → search → extract → accumulate), synthesizes a final report, writes output, and returns `status=complete`.

---

## ⚠️ HUMAN CHECKPOINT — verify SPL before S4

Inspect the run output and the `.spl` file for common LLM failure patterns before compiling:

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

> **2026-05-04 (openrouter/gemini run):** S4 file created manually via `cp`. `search_web` stub replaced with real DuckDuckGo; model fixed to `google/gemini-3-flash-preview`; `Workflow` ImportError fixed (class is plain Python, not a PocketFlow subclass).

---

## S4-run — validate compiled PocketFlow code

```bash
# copy to S4 convention if not already done
cp $OUT/targets/python_pocketflow/S3-$RECIPE-$ADAPTER-$MODEL*.py \
   $OUT/targets/python_pocketflow/S4-$RECIPE-$ADAPTER-$MODEL.py

# run — requires OPENROUTER_API_KEY; duckduckgo_search provides real web results
python $OUT/targets/python_pocketflow/S4-$RECIPE-$ADAPTER-$MODEL.py \
  "PocketFlow minimalist LLM framework" \
  report.txt \
  2>&1 | tee $OUT/S4-$RECIPE-$ADAPTER-$MODEL-pf-$(date +%Y%m%d_%H%M%S).md
```

---

> **Human Checkpoint — S4 compiled code:** Run with real test inputs; verify the app works end-to-end.
>
> > **Human Checkpoint Protocol:** (1) Review artifact. (2) Run and test with real inputs — work with AI assistant to diagnose and fix all issues until working. (3) Document every issue and fix in `$OUT/notes.md` before proceeding.

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

> **Human Checkpoint — S6 closure score:** Review the diff report. Trace low scores back to S2 or S3. Document findings in `$OUT/notes.md`.

```

---

## S7 — `spl3 vibe` → direct code (ablation baseline)

Generate code directly from the S1 spec, bypassing Mermaid and SPL IR. Output goes to the `vibe/` folder.

```bash
mkdir -p $OUT/vibe/python_pocketflow

spl3 vibe \
  --description $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  --target python/pocketflow \
  --adapter $ADAPTER --model $MODEL_ID \
  --out-dir $OUT/vibe/python_pocketflow
```

---

## S8 — `spl3 splc describe` → spec3

Convert vibe-generated folder to spec. Same task as S5 (which also describes a folder); spec index is 3 (S1=1, S5=2, S8=3).

> **Human Checkpoint — S7 vibe output:** A model may generate multiple files (.py, README.md, test data). Run the generated code with the same test inputs used in S4.
>
> > **Human Checkpoint Protocol:** (1) Review artifact. (2) Run and test with real inputs — work with AI assistant to diagnose and fix all issues until working. (3) Document every issue and fix in `$OUT/notes.md` before proceeding.

```bash
spl3 splc describe $OUT/vibe/python_pocketflow \
  --adapter $ADAPTER --model $MODEL_ID \
  -o $OUT/S8-$RECIPE-$ADAPTER-$MODEL-3-spec.md
```

---

## S9 — `spl3 compare` → vibe drift score

Compare original spec (S1) vs vibe-generated spec (S8). Judge fixed at claude-opus-4-6.

```bash
spl3 compare \
  $OUT/S1-$RECIPE-$ADAPTER-$MODEL-1-spec.md \
  $OUT/S8-$RECIPE-$ADAPTER-$MODEL-3-spec.md \
  --adapter claude_cli --model claude-opus-4-6 \
  -o $OUT/S9-$RECIPE-$ADAPTER-$MODEL-vibe-diff.md
```

> **Analysis:** Compare S9 vs S6 to quantify IR value-add:
> - **S6 score** = round-trip fidelity **with** IR (full pipeline)
> - **S9 score** = round-trip fidelity **without** IR (vibe baseline)
> - **ΔIR = S6 − S9** = value added by the Mermaid + SPL intermediate representation

---

## S10 — `spl3 compare` → ablation summary

Meta-comparison: full IR diff (S6) vs vibe diff (S9). The judge quantifies ΔIR and explains where the IR steps added value.

```bash
spl3 compare \
  $OUT/S6-$RECIPE-$ADAPTER-$MODEL-spec-diff.md \
  $OUT/S9-$RECIPE-$ADAPTER-$MODEL-vibe-diff.md \
  --adapter claude_cli --model claude-opus-4-6 \
  -o $OUT/S10-$RECIPE-$ADAPTER-$MODEL-ablation.md
```

> **Result:** S10 report contains the structured ablation verdict:
> - **S6 score** = round-trip fidelity with IR (full pipeline)
> - **S9 score** = round-trip fidelity without IR (vibe baseline)
> - **ΔIR = S6 − S9** = IR value-add
>
> Aggregate S10 reports across all 15 runs (5 recipes × 3 models) to produce the NeurIPS ablation table.

---

## Expected Issues

Steps may not run perfectly on the first attempt — that is expected. Common failure points:

- **S1**: This is the most complex recipe (parallel batch + recursive loop); spec may need a re-run with a stronger model if output is shallow
- **S2**: Parallel batch structure is hard for LLMs to render in Mermaid; inspect carefully
- **S3**: SPL parallel constructs (`CALL PARALLEL`) may need manual adjustment
- **S4**: Parallel execution and recursive loop are the hardest to compile correctly; expect manual fixes
- **S5**: If S4 output is functionally broken, S5 spec will be poor — fix S4 first

Record issues and fixes in `$OUT/notes.md`.
