# SPL 3.0 — Feature Roadmap

Suggested features based on a full review of the codebase, the NeurIPS-26 experiment
protocol, and gaps observed during the `spl3 compare` / `spl3 vibe` implementation.
These are not committed — they are candidates for future discussion.

Items are grouped by theme and ranked roughly by value-to-effort within each group.

---

## 1. Experiment & Research Automation

### 1.1 `spl3 experiment run` — batch experiment runner

Running 15 (5 recipes × 3 models) experiments today requires manually invoking each
pipeline step. A single command could drive the whole matrix:

```bash
spl3 experiment run \
  --recipes R1-agent R2-rag R3-judge R4-thinking R5-research \
  --adapters claude_cli openrouter \
  --models claude-sonnet-4-6 qwen/qwen3.6-plus google/gemini-3-flash-preview \
  --pipeline S1,S2,S3,S4,S5,S6 \
  --base-dir NeurIPS-26-lab
```

Outputs follow the established directory convention:
```
NeurIPS-26-lab/<recipe>/tests/<adapter>/<model-alias>/S<N>-<recipe>-<adapter>-<model>-*
```

Skips already-completed steps (checkpoint / resume). Wraps existing pipeline commands —
no new LLM logic needed.

**Why:** Eliminates 15 × 6 = 90 manual commands. The biggest productivity win on the list.

**Design note:** S4 output lives one level deeper (`targets/python_pocketflow/S4-*.py`)
while S1–S3, S5–S6 are flat. The runner must handle this as a known exception.

---

### 1.2 `spl3 experiment report` — aggregate compare scores into a leaderboard

The experiment is already parameterized as `{recipes}` × `{models}` × `{pipeline-steps}`,
and the file naming convention encodes all three dimensions directly in the path:

```
R1-agent/tests/claude_cli/sonnet/S6-agent-claude_cli-sonnet-spec-diff.json
```

The report command reconstructs the full matrix by globbing `R*/tests/*/*/S6-*-diff.json`
— recipe and model fall out of the path, no metadata file needed. `spl3 compare --format json`
already emits structured scores, so aggregation is just `json.load()` + pivot.

```
| Recipe    | Model   | LLM score | Vector sim | GED  | git-diff lines |
|-----------|---------|-----------|------------|------|----------------|
| agent     | sonnet  | 8.2       | 0.94       | 2.0  | 14             |
| agent     | qwen    | 7.8       | 0.91       | 3.0  | 21             |
| agent     | gemini  | 7.1       | 0.89       | 4.0  | 28             |
...
```

Supports `--format markdown|csv|json`. Directly feeds NeurIPS paper tables.

---

### 1.3 `spl3 compare --batch` — one baseline, many targets

```bash
spl3 compare S1-agent-spec.md tests/*/S5-agent-*-spec.md --mode llm --format csv
```

Compare a single reference file against a glob of generated files in one pass.
Currently requires running `spl3 compare` once per pair.

---

## 2. Pipeline Convenience

### 2.1 `spl3 spl2mmd` — reverse: `.spl` → Mermaid diagram

The pipeline currently has `mmd2spl` but not the reverse. Visualising an existing
`.spl` workflow as a flowchart is useful for documentation, review, and debugging
without going through the full `describe` → `text2mmd` round-trip.

```bash
spl3 spl2mmd workflow.spl -o workflow.mmd --preview
```

Deterministic transpiler (no LLM) — parse the AST, emit Mermaid node-edge syntax.
`WORKFLOW` → flowchart, `WHILE` → loop back-edge, `EVALUATE` → decision diamond.

**Why:** Closes the last gap in the IR ↔ visual round-trip. Pure code, no LLM cost.

---

### 2.2 `spl3 pipeline` — run a named multi-step pipeline in one command

Rather than chaining shell commands, let the user define a named pipeline in a config
file and execute it:

```bash
spl3 pipeline run ndd-full --recipe agent --adapter claude_cli -m claude-sonnet-4-6
```

Where `ndd-full` maps to S1→S2→S3→S4→S5→S6. Intermediate outputs are auto-named
and passed between steps. Supports `--from-step S3` to resume from a checkpoint.

---

### 2.3 Streaming output for long LLM calls

All `spl3` commands that call an LLM block until the full response arrives. For large
files (`splc compile`, `vibe` on a long spec), this can feel like a hang.

Add `--stream` flag (or make it the default where the adapter supports it) so tokens
print as they arrive. Already possible with most adapters — just needs to be plumbed
through `compile_llm_code` and `cmd_vibe`.

---

## 3. Compare / Metrics Enhancements

### 3.1 `--mode rouge` — ROUGE score

ROUGE-L and ROUGE-1/2 are standard summarisation metrics, well-suited to comparing
spec documents where semantic overlap at the n-gram level matters. Lighter than
`bert-score` (no model download), faster, fully deterministic.

```bash
spl3 compare spec1.md spec2.md --mode rouge
```

Optional dependency: `pip install rouge-score`.

---

### 3.2 Composite `--mode all` with weighted score

When multiple modes are requested, compute a single **composite Intent Entropy score**
Δ*S* as a weighted average of the individual metrics. Weights configurable via
`--weights llm=0.4,vector=0.3,git-diff=0.3`. Gives a single number for experiment
leaderboards without losing the per-mode breakdown.

---

### 3.3 `spl3 compare` — structured JSON diff with change taxonomy

Beyond raw metrics, classify the differences into a taxonomy:

```json
{
  "added_constructs": ["EXCEPTION handler"],
  "removed_constructs": ["CALL parallel"],
  "renamed_variables": [{"from": "@draft", "to": "@output"}],
  "semantic_drift_score": 0.12
}
```

Useful for understanding *what kind* of information is lost in the round-trip, not
just *how much*.

---

## 4. Compiler / Transpiler Completeness

### 4.1 Deterministic transpiler for `python/crewai` and `python/autogen`

Currently these targets require `--llm`. A deterministic transpiler would:
- lower LLM cost (no API call for compilation)
- produce consistent, auditable output
- be unit-testable

The `python/pocketflow` transpiler is the template. `crewai` and `autogen` have
stable enough APIs to map SPL constructs deterministically.

---

### 4.2 `splc` targets: `swift`, `snap`, `edge`

Already stubs in `SUPPORTED_LANGS` (commented out). Filling these in would widen
deployment targets for mobile and edge use cases. LLM-only transpiler first, then
deterministic if the framework stabilises.

---

### 4.3 SPL `IMPORT` statement — reusable function libraries

```spl
IMPORT "lib/common_prompts.spl"

WORKFLOW my_agent
  GENERATE common.critique(@draft) INTO @feedback
  ...
```

Allows sharing `CREATE FUNCTION` definitions across workflows without copy-paste.
Requires a small parser change and a file resolver in the runtime. No LLM changes.

---

### 4.4 `spl3 validate` — semantic linting beyond syntax

Current `validate` checks parse-level correctness. Add semantic checks:

- Undefined variable reference (`@x` used before `GENERATE ... INTO @x`)
- Unreachable code after `RETURN`
- `WHILE` loops with no reachable exit condition
- `CALL` targets that reference undefined sub-workflows

These are static analysis passes on the AST — no LLM involved.

---

## 5. Developer Experience

### 5.1 VS Code extension — SPL syntax highlighting + validate-on-save

A `vscode-spl` extension providing:
- `.spl` syntax highlighting (keywords, string literals, `@variables`, `-- comments`)
- `spl3 validate` on save with inline error squiggles
- Hover docs for SPL keywords

The grammar is simple enough for a TextMate grammar file. No language server needed
for v1.

---

### 5.2 `spl3 serve` — expose a `.spl` workflow as an HTTP API

```bash
spl3 serve workflow.spl --port 8080
```

Wraps `spl3 run` in a FastAPI/Flask handler. `POST /run` with a JSON body maps to
`-p key=val` parameters. Useful for embedding SPL workflows into larger applications
without writing a Python wrapper each time.

---

### 5.3 `spl3 vibe` — provenance manifest

`spl3 splc compile` writes a `splc_manifest.json` capturing the source `.spl` hash,
adapter, model, and RAG settings. `spl3 vibe` currently writes no provenance. Adding
a `vibe_manifest.json` would make ablation experiment outputs fully traceable and
comparable to `splc compile` outputs on equal footing.

```json
{
  "vibe_version": "0.1.0",
  "generated_at": "...",
  "description_sha256": "...",
  "adapter": "openrouter",
  "model": "qwen/qwen3.6-plus",
  "rag_enabled": true,
  "rag_k": 3,
  "output_file": "A1-agent-qwen.py"
}
```

---

## 6. Quality & Testing

### 6.1 `spl3 test` — golden-file regression tests for transpilers

The deterministic transpilers (`go`, `ts`, `pocketflow`, `langgraph`) produce
structured code from a fixed `.spl` input. Add a golden-file test harness:

```bash
spl3 test cookbook/05_self_refine/self_refine.spl --lang python/pocketflow
```

Compares transpiler output against a committed `.golden.py` file, fails on diff.
Catches transpiler regressions without running an LLM. Critical as the transpilers
grow more complex.

---

### 6.2 `spl3 compare` — HTML report output

`--format html` for a self-contained HTML report with syntax-highlighted diffs,
collapsible sections, and score visualisations. Makes experiment results easy to
share and review without requiring Markdown rendering. Builds on the existing
`difflib.HtmlDiff` already imported in the codebase.

---

## Summary Table

| # | Feature | Theme | Effort | Value |
|---|---------|-------|--------|-------|
| 1.1 | `spl3 experiment run` | Automation | Medium | Very High |
| 1.2 | `spl3 experiment report` | Automation | Low | High |
| 2.1 | `spl3 spl2mmd` | Pipeline | Low | High |
| 4.3 | SPL `IMPORT` statement | Language | Low | High |
| 4.4 | Semantic linting in `validate` | Quality | Medium | High |
| 1.3 | `compare --batch` | Automation | Low | Medium |
| 2.2 | `spl3 pipeline` | Pipeline | High | Medium |
| 2.3 | Streaming LLM output | DX | Low | Medium |
| 3.1 | `--mode rouge` | Metrics | Low | Medium |
| 3.2 | Composite Δ*S* score | Metrics | Low | Medium |
| 3.3 | Structured JSON diff taxonomy | Metrics | Medium | Medium |
| 4.1 | Deterministic crewai/autogen | Compiler | High | Medium |
| 5.3 | `vibe` provenance manifest | Quality | Low | Medium |
| 6.1 | Golden-file regression tests | Testing | Medium | Medium |
| 5.1 | VS Code extension | DX | High | Medium |
| 5.2 | `spl3 serve` | DX | Medium | Low |
| 4.2 | swift/snap/edge targets | Compiler | High | Low |
| 3.3 | Composite score weights | Metrics | Low | Low |
| 6.2 | HTML report output | Reporting | Low | Low |
