# SPL 3.0 — Feature Roadmap

> Last reviewed against the codebase: **2026-06-10**.
>
> **Current focus (2026-06):** the micro-textbook / neurosymbolic track (§4.5–§4.8).
> Next up: SageMath + Lean verifier backends — see
> [`sage_lean_integration_plan.md`](./sage_lean_integration_plan.md). Long-term aim:
> SPL as a seamless deterministic + probabilistic agentic orchestration language
> for mathematicians' and physicists' daily research workflows.

Suggested features based on a full review of the codebase, the NeurIPS-26 experiment
protocol, and gaps observed during the `spl3 compare` / `spl3 vibe` implementation.
These are not committed — they are candidates for future discussion.

Items are grouped by theme and ranked roughly by value-to-effort within each group.
Items marked ✅ are already implemented.

---

## 1. Experiment & Research Automation

### ✅ Ablation pipeline (S7–S10)

The full S1–S10 pipeline — IR path (S1–S6) plus vibe ablation baseline (S7–S10) —
is implemented and running. Key commands:

- `spl3 vibe --spec <S1-spec.md>` — spec-driven mode (S7): full spec used verbatim,
  no section filtering, no Mermaid or SPL IR steps. Mutually exclusive with `--description`.
- `spl3 compare S6-ir-diff.md S9-vibe-diff.md` — meta-compare of the two compare
  reports to produce ΔIR = S6 − S9 (S10).
- **VibeSCOPE NeurIPS Lab page** (`37_🧪_NeurIPS_Lab.py`) — supervised UI runner
  for all 10 steps with status indicators, inline output display, and step chaining.
- **VibeSCOPE Ablation page** (`39_📊_Ablation.py`) — reads persisted S6/S9/S10
  compare files from disk, extracts Structure/Logic/Quality/Overall scores, renders
  paper-aligned score matrix and LaTeX export.

---

### ✅ 1.1 `spl3 experiment run` — batch experiment runner

Running 15 (5 recipes × 3 models) experiments today requires manually invoking each
pipeline step. A single command could drive the whole matrix:

```bash
spl3 experiment run \
  --recipes R1-agent R2-rag R3-judge R4-thinking R5-research \
  --adapters claude_cli openrouter \
  --models claude-sonnet-4-6 qwen/qwen3.6-plus google/gemini-3-flash-preview \
  --pipeline S1,S2,S3,S4,S5,S6 \
  --out-dir NeurIPS-26-lab
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

### ✅ 1.2 `spl3 experiment report` — aggregate compare scores into a leaderboard

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

** [Put-Off] **

```bash
spl3 compare S1-agent-spec.md tests/*/S5-agent-*-spec.md --mode llm --format csv
```

Compare a single reference file against a glob of generated files in one pass.
Currently requires running `spl3 compare` once per pair.

---

## 2. Pipeline Convenience

### ✅ `spl3 spl2mmd` — `.spl` → Mermaid diagram

Fully implemented. Deterministic AST-driven transpiler — no LLM required. Generates
`.mmd`, `.md`, `.html`, `.svg`, `.png` (optional), and `.pdf` (optional via `mmdc`).
Every workflow, procedure, loop, branch, and exception handler is rendered from the
parsed syntax tree. See §10 of the USER-GUIDE for full documentation.

---

### ✅ `text2mmd` and `vibe --description` — spec file preprocessing

When a spec file is passed to `text2mmd` or `vibe --description`, the content is
pre-processed before being sent to the LLM:

1. Extract `## Summary` and `### 1. Purpose` sections if present.
2. Else extract numbered sections `## 0.` / `## 1.` (from `splc describe` output).
3. Else ask the LLM to produce a concise 3–6 sentence workflow summary as fallback.

This focuses the prompt on high-level intent and avoids context-window overload
from large spec files.

---

### ✅ `spl3 vibe --spec` — spec-driven coding (DODA / ablation S7)

New `--spec SPEC_FILE` option for `spl3 vibe`. Uses the full spec file verbatim —
no section filtering, no summarization. The complete document is the authoritative
requirement. Prompt header: `# Functional Specification` (vs `# Requirement to Implement`
for `--description`). Mutually exclusive with `--description` / positional arg.

This is the NeurIPS S7 ablation mode: same S1 spec as the IR pipeline, but code
generated directly without going through Mermaid or SPL IR. Also the foundation
for DODA migrations — port any existing codebase by reverse-engineering a spec
and vibing to a new target.

---

### ✅ `spl3 cache` — Layer 2 content cache

Persistent content cache for expensive LLM generations (micro-textbook sections,
notebook cells). Provenance tiers, TTL semantics, cascading invalidation along the
concept graph (`invalidate vector` → invalidates `span`, `eigenpair`, …), and
export/import for team sharing without a live remote store. CLI: `spl3 cache
stats|list|show|invalidate|promote|export|import`. See USER-GUIDE §18 and
`docs/DEV/spl3-cache.md`.

---

### 2.1 `spl3 pipeline` — run a named multi-step pipeline in one command

** [Put-Off] **

Rather than chaining shell commands, let the user define a named pipeline in a config
file and execute it:

```bash
spl3 pipeline run ndd-full --recipe agent --adapter claude_cli -m claude-sonnet-4-6
```

Where `ndd-full` maps to S1→S2→S3→S4→S5→S6. Intermediate outputs are auto-named
and passed between steps. Supports `--from-step S3` to resume from a checkpoint.

---

### 2.2 Streaming output for long LLM calls

** [Put-Off] **

All `spl3` commands that call an LLM block until the full response arrives. For large
files (`splc compile`, `vibe` on a long spec), this can feel like a hang.

Add `--stream` flag (or make it the default where the adapter supports it) so tokens
print as they arrive. Already possible with most adapters — just needs to be plumbed
through `compile_llm_code` and `cmd_vibe`.

---

## 3. Compare / Metrics Enhancements

### ✅ `spl3 compare --format html` — 3-panel side-by-side report

Fully implemented. Renders a self-contained HTML report with:
- Left panel: File 1 (Mermaid diagrams rendered live; images embedded; code shown as-is)
- Right panel: File 2 (same)
- Bottom panel: synthesis verdict (colour-coded banner) + collapsible tier details

See §12 of the USER-GUIDE for full documentation.

---

### ✅ 3.1 `--mode rouge` — ROUGE score

ROUGE-L and ROUGE-1/2 are standard summarisation metrics, well-suited to comparing
spec documents where semantic overlap at the n-gram level matters. Lighter than
`bert-score` (no model download), faster, fully deterministic.

```bash
spl3 compare spec1.md spec2.md --mode rouge
```

Optional dependency: `pip install rouge-score` (installed in `spl123` env).

---

### 3.2 Composite `--mode all` with weighted score

** [Put-Off] **

When multiple modes are requested, compute a single **composite Intent Entropy score**
Δ*S* as a weighted average of the individual metrics. Weights configurable via
`--weights llm=0.4,vector=0.3,git-diff=0.3`. Gives a single number for experiment
leaderboards without losing the per-mode breakdown.

---

### 3.3 `spl3 compare` — structured JSON diff with change taxonomy

** [Put-Off] **

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

** [Put-Off] **

Deterministic transpilers now cover `go`, `ts`, `python/langgraph`, `python/pocketflow`,
and the three domain micro-textbook targets (`python/linalg`, `python/intro_geometry`,
`python/domain_textbook`). Still LLM-only: `python` (plain), `python/crewai`,
`python/autogen`, `python/liquid`. A deterministic transpiler for the remaining
targets would:
- lower LLM cost (no API call for compilation)
- produce consistent, auditable output
- be unit-testable

The `python/pocketflow` transpiler is the template. `crewai` and `autogen` have
stable enough APIs to map SPL constructs deterministically.

---

### 4.2 `splc` targets: `swift`, `snap`, `edge`

** [Put-Off] **

Already stubs in `SUPPORTED_LANGS` (commented out). Filling these in would widen
deployment targets for mobile and edge use cases. LLM-only transpiler first, then
deterministic if the framework stabilises.

---

### ✅ 4.3 SPL `IMPORT` statement — reusable function libraries

```spl
IMPORT "lib/common_prompts.spl"

WORKFLOW my_agent
  GENERATE common.critique(@draft) INTO @feedback
  ...
```

Fully implemented. Parser (`parser.py`), AST node (`ImportStatement`), recursive loader
with circular-import detection (`_loader.py`), transpiler inlining (`transpiler_langgraph.py`),
and registry dedup (`registry.py`) all handle `IMPORT` transparently. The `.spl` extension
is optional in the import path.

---

### ✅ 4.4 `spl3 validate` — semantic linting beyond syntax

Implemented in `spl3/linter.py`. `validate` now runs both parse-level and semantic checks:

- Undefined variable reference (`@x` used before `GENERATE ... INTO @x`)
- Unreachable code after `RETURN`
- `WHILE` loops with no exit-capable statement and no `max_iterations`
- `CALL` targets not found in `CREATE FUNCTION` declarations or stdlib tools

New options: `--semantic/--no-semantic` (default on), `--strict` (WARNs become fatal).
All checks are static AST passes — no LLM involved.

---

### ✅ 4.5 `SOLVE` / `ASSERT` — neurosymbolic constructs + IPython kernel

New SPL statements for deterministic computation inside an LLM workflow:

```spl
SOLVE @order LIST := productivity_order(@@graph@@, weight=@@payoff_weight@@)
ASSERT reducible(@@graph@@, @@primitives@@) OTHERWISE RETURN @error
```

Backed by a persistent IPython kernel (`spl3 run --kernel`, with `--kernel-scope
session|workflow` and `--kernel-timeout`). Every `CALL run_python(@code)` routes
through the kernel; state (imports, variables, SymPy symbols) persists across steps.
Implemented in `parser.py`, `kernel.py` (out-of-process `jupyter_client` backend +
in-process `KernelSession` fallback); see `docs/DEV/SPL-kernel-execution-design.md`
and `tests/test_solve_assert.py` / `test_kernel.py`. Powers the symbolic-math and
micro-textbook recipes (67–74).

---

### ✅ 4.6 `CREATE TOOL_API` — deterministic tool definitions + library registry

Closes the language duality: `GENERATE fn()` ↔ `CREATE FUNCTION` (LLM) is now matched
by `CALL tool()` ↔ `CREATE TOOL_API ... AS PYTHON $$...$$` (deterministic Python).
Fully implemented across language, generation (`mmd2spl`/`text2spl` emit TOOL_API for
deterministic ops), and tooling: `spl3 tool-api list|promote|remove` manages a stdlib
tool registry, and validated workflow tools can be promoted into it. See
`docs/DEV/spl3-tool-api.md`.

---

### ✅ 4.7 Domain micro-textbook targets — parameterized `python/<domain>` engine

Three deterministic `.ipynb` compile targets: `python/linalg`, `python/intro_geometry`,
and the generic `python/domain_textbook` (domain supplied as a YAML concept graph,
resolved at runtime via `graph_lib`). Includes style profiles, concept-graph tooling
(`scripts/concept_graph.py` — inspect, visualize, share, compose hybrid multi-domain
graphs), and cookbook recipes 69–74 (notebook gen, linalg core concepts, micro-textbook,
intro geometry, domain textbook). The `transpiler_linalg.py` → `transpiler_domain_*.py`
generalization landed 2026-06-07.

---

### 4.8 Verifier ladder — SageMath + Lean 4 backends for `SOLVE`/`ASSERT`

**Priority: current focus.** Full design in
[`sage_lean_integration_plan.md`](./sage_lean_integration_plan.md). Zero parser/AST
changes — both are pure backend work behind the existing constructs:

- **SageMath (Part A):** make the kernel spec configurable
  (`kernel.py` hardcodes `kernel_name="python3"` today; Sage ships a `sagemath`
  Jupyter kernel spec). Add `verifier: "sage"` to the domain-graph vocabulary,
  `DomainConfig.kernel_name`, and `.ipynb` kernelspec emission. Unlocks
  `python/classical_mechanics` (SageManifolds), richer geometry verifiers, and
  future GAP/PARI/Singular domains. Small lift.
- **Lean 4 + mathlib (Part B):** kernel-resident `lean_bridge` client talking to a
  persistent `leanprover-community/repl` process. Statement checking → proof
  checking → `OTHERWISE RETRY` repair loop with Lean errors fed back. Introduces a
  new trust tier `machine_proved` above `machine_verified` — CAS checks *instances*,
  Lean checks *statements*. Larger lift; strictly optional dependency.

**Why this matters beyond the micro-textbook:** the verifier ladder
(NumPy → SymPy/Sage → Lean) behind the same two constructs is the concrete form of
SPL's ambition — seamless deterministic + probabilistic orchestration that no
agent framework offers at the language level, aimed at researchers' daily
draft → falsify → formalize → cite loops.

---

## 5. Developer Experience

### ✅ 5.1 VS Code extension — SPL syntax highlighting + validate-on-save

The `spl-llm` VS Code extension (`SPL-LLM/spl-llm/`) provides:
- `.spl` syntax highlighting via TextMate grammar (keywords, `@variables`, `$$...$$` prompt bodies, f-strings, `-- comments`)
- `spl3 validate` on save with inline error squiggles (severity: ERROR / WARNING)
- Hover docs for all SPL 3.0 keywords (WORKFLOW, IMPORT, GENERATE, CALL PARALLEL, COMMIT, EVALUATE, WHILE, EXCEPTION, …)
- Two commands: **SPL: Validate Current File** and **SPL: Validate Current File (with semantic checks)**
- Settings: `spl-llm.validateOnSave`, `spl-llm.semanticValidation`, `spl-llm.spl3Path`
- Packaged as `spl-llm-0.0.4.vsix` — install with `code --install-extension spl-llm-0.0.4.vsix`

---

### ~~5.2 `spl3 serve` — expose a `.spl` workflow as an HTTP API~~ [Descoped]

VibeSCOPE's FastAPI backend already exposes SPL workflows as HTTP endpoints with
full route, auth, and UI integration. A standalone `spl3 serve` would duplicate
this without adding meaningful value. Descoped in favour of VibeSCOPE as the
canonical HTTP deployment surface.

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
  "input_mode": "spec",
  "spec_sha256": "...",
  "adapter": "claude_cli",
  "model": "claude-sonnet-4-6",
  "rag_enabled": true,
  "rag_k": 3,
  "output_file": "S7-agent-claude_cli-sonnet.py"
}
```

---

## 6. Quality & Testing

### ✅ 6.0 `spl3 test` — pipeline-level workflow tests

Implemented, but as YAML-fixture pipeline tests rather than golden files: each
`workflow.spl` can have a `workflow.test.yaml` declaring test cases (input `params` +
`assert: contains / status`), run via `spl3 test <file-or-dir>`. Executes the real
workflow against a chosen adapter/model.

---

### 6.1 Golden-file regression tests for transpilers

The deterministic transpilers (`go`, `ts`, `pocketflow`, `langgraph`, domain targets)
produce structured code from a fixed `.spl` input. Add a golden-file test harness:

```bash
spl3 test cookbook/05_self_refine/self_refine.spl --lang python/pocketflow --golden
```

Compares transpiler output against a committed `.golden.py` file, fails on diff.
Catches transpiler regressions without running an LLM. Critical as the transpilers
grow more complex. (Partially mitigated today by unit tests such as
`tests/test_transpiler_linalg.py`, but `go`/`ts`/`pocketflow`/`langgraph` have no
output-snapshot coverage.)

---

## 7. DODA — Design Once, Deploy Anywhere

DODA is the long-term vision enabled by Intent Invariance: write a workflow once in
`.spl`, compile and run it on any LLM provider or target runtime without rewriting
logic.

### 7.1 Cross-runtime round-trip tests

Run S1–S6 for Go and TypeScript targets (in addition to Python/PocketFlow) and
compare S6 scores. If scores are consistent across runtimes, Intent Invariance is
runtime-invariant — the `.spl` IR carries the intent regardless of the compilation
target. This strengthens the DODA claim empirically.

---

### ✅ 7.2 Migration pipeline tooling

Currently, porting an existing codebase to a new runtime requires manually chaining:
`splc describe` → `text2mmd` → `mmd2spl` → `splc compile`. A dedicated
`spl3 migrate` command would wrap this into a single reproducible step:

```bash
spl3 migrate ./existing-pocketflow-agent/ \
  --target python/langgraph \
  --adapter claude_cli --model claude-sonnet-4-6 \
  --out-dir ./langgraph-agent/
```

Includes an automatic `spl3 compare` at the end to score migration fidelity.

---

### ✅ 7.3 Multi-judge evaluation

Implemented as `spl3 judge` (package `spl3/judge/`): rubric-based evaluation with
structured verdicts (PASS / FAIL / ESCALATE), per-criterion scores, and reasoning.
Panel mode runs multiple independent judges concurrently — repeat `--llm
ADAPTER:MODEL` and aggregate via `--aggregation majority|confidence_weighted|unanimous`;
`--swap-check` tests order-bias consistency. Cross-provider panels (Claude + Gemini +
Qwen) directly address the intra-provider self-preference risk identified in the
NeurIPS paper. See USER-GUIDE §13.

**Remaining:** systematically run cross-judge consistency analysis on the NeurIPS
S6/S9 results to validate that Intent Drift ΔS is judge-stable (analysis task, not
tooling).

---

## 8. DBOS + Momagrid — Reliable Agentic Compute

**Priority: #1 (production deployment)**

SPL workflows today are single-process, ephemeral — a node crash mid-run loses all progress.
DBOS (Durable Execution on PostgreSQL) makes every step crash-survivable by checkpointing
each `@DBOS.step()` call to Postgres before execution. This is the reliability layer that
makes Momagrid production-worthy.

> **Status 2026-06-10:** No DBOS code in the repo yet (8.1–8.3 all open). Momagrid
> *distribution* has shipped (see ✅ 8.0 below); Momagrid *durability* has not.

### ✅ 8.0 Momagrid Hub workflow registry + Hub-to-Hub peering

The Hub is now the "OS kernel" of the compute grid (`spl3/hub_registry.py`,
`spl3/peer.py`): it maintains a workflow registry (name → definition) shared across
all connected nodes, and `CALL workflow_name()` in a client workflow routes to the
Hub via the existing `POST /tasks` protocol (one schema field extension, no new
endpoints). If a workflow isn't registered locally, the Hub forwards to a peer Hub
via its peer table — Hub-to-Hub WAN routing. CLI: `spl3 register <path>`,
`spl3 registry list`, `spl3 peers list`. The companion `mg` CLI (Go, separate
`digital-duck/momagrid` repo) plus the School Momagrid cheatsheet
(`docs/GUIDE/Momagrid-Cheatsheet.md`) make a classroom grid a two-command setup.

A model-affinity parallelization design for batch experiments (one worker per Ollama
model, file-locked shared log) is drafted in
`cookbook/67_symbolic_math/readme-momagrid.md`.

---

### 8.1 DBOS execution backend for `spl3 run`

Compile `.spl` workflows to DBOS-wrapped Python: each SPL `GENERATE`, `CALL`, and `LOOP`
body becomes a `@DBOS.step()`. Crashes at any point resume from the last committed step —
not from the beginning.

```python
@DBOS.workflow()
def run_self_refine(initial_draft: str) -> str:
    draft = initial_draft
    for _ in range(max_iterations):
        feedback = generate_feedback(draft)   # @DBOS.step
        draft    = apply_feedback(draft, feedback)  # @DBOS.step
        if is_good_enough(draft):              # @DBOS.step
            break
    return draft
```

**Why:** Multi-agent pipelines regularly exceed 10 minutes. Without durability, a network
blip or OOM kill forces a full restart. With DBOS, the workflow resumes mid-loop.

**Integration path:** New `--target python/dbos` in `splc compile`, or a `--durable` flag
that wraps the existing `python/pocketflow` output. No changes to the `.spl` language.

---

### 8.2 Time-travel debugging via DBOS workflow history

DBOS stores the full execution trace in Postgres. After a failure (or for auditing), replay
the workflow step-by-step with the original inputs:

```bash
spl3 replay <workflow-id> --step S4  # rewind to step 4, re-execute forward
```

**Why:** Debugging a failed 30-step agentic pipeline today means adding print statements
and re-running from scratch. Time-travel replay targets the exact failure point.

---

### 8.3 Momagrid reliability — persistent task queues

Momagrid multi-agent coordination currently assumes all agents stay alive. Add a DBOS-backed
task queue so that if an agent crashes mid-task, another Momagrid node picks it up:

```python
@DBOS.step()
def momagrid_dispatch(task: MomagridTask) -> MomagridResult:
    agent = select_agent(task)
    return agent.execute(task)
```

**Why:** Production Momagrid requires at-least-once task delivery. DBOS provides this
without building a custom queue (Kafka, RabbitMQ) — Postgres is the queue.

---

## 9. `spl3 migrate` — Verified LLM Migration Service

**Priority: #2**

Porting an existing codebase to a new runtime today requires manually chaining four commands.
`spl3 migrate` wraps the entire migration pipeline into one reproducible, scored step:

```bash
spl3 migrate ./existing-pocketflow-agent/ \
  --target python/langgraph \
  --adapter claude_cli --model claude-sonnet-4-6 \
  --out-dir ./langgraph-agent/
```

Internally chains:
1. `splc describe` — reverse-engineer spec from source code
2. `text2mmd` — recover Mermaid topology (human checkpoint optional)
3. `mmd2spl` — canonical SPL IR
4. `splc compile --target python/langgraph` — generate target code
5. `spl3 compare` — score migration fidelity, emit `migration-report.md`

The final report answers: *did the migration preserve design intent?* A score < 7.0 flags
the migration for human review before deployment.

**Near-term concrete task:** Migrate all PocketFlow cookbook recipes to SPL cookbook.
Each migration runs `spl3 migrate`, commits the `.spl` + migration report, and seeds
the Code-RAG vector store for that framework.

---

## 10. SPL as "SQL for AI Workflows"

**Priority: #3**

SQL succeeded because it separated *what* (query intent) from *how* (query execution).
SPL is the same bet for AI workflows: separate *what the workflow does* (`.spl`) from
*how it runs* (adapter + target runtime).

### 10.1 SPL Standard Library

A curated set of parameterized `.spl` workflow templates covering the most common
agentic patterns:

```
stdlib/
  patterns/
    self_refine.spl       # iterative draft → critique → revise
    react_agent.spl       # reason → act → observe loop
    chain_of_thought.spl  # sequential reasoning chain
    multi_agent.spl       # coordinator + worker topology
    rag_pipeline.spl      # retrieve → augment → generate
    judge_panel.spl       # multiple independent judges → consensus
```

Import via `IMPORT "stdlib/patterns/self_refine.spl"`. Parameterize via workflow args.
This is the SPL equivalent of the SQL `GROUP BY` / `JOIN` — common operations, standard
spelling, any runtime.

**Partially shipped:** the *deterministic-tool* half exists — the `CREATE TOOL_API`
stdlib registry (`spl3 tool-api list --stdlib`, see ✅ 4.6). The *workflow-pattern*
half (curated `.spl` templates) is still open.

**Concrete task:** Curate LangGraph, AutoGen, and CrewAI recipe repos; translate each
to `.spl`; add to stdlib and seed Code-RAG vector store.

---

### 10.2 SPL Registry — publish and discover workflows

A lightweight registry (hosted or self-hosted) where teams publish validated `.spl` workflows:

```bash
spl3 registry push my-agent.spl --tag v1.2 --license MIT
spl3 registry pull rag-pipeline --version latest
```

Analogous to Docker Hub for containers or PyPI for packages, but for *agentic workflows*.
The registry stores the `.spl` only — the runtime is resolved locally at compile time.

**Partially shipped:** the Momagrid Hub workflow registry with Hub-to-Hub peering
(✅ 8.0) already provides intra-grid publish/discover (`spl3 register`, `spl3 registry
list`). What remains is the *public* hosted registry with versioning, tags, and
licensing.

---

## 11. Enterprise AI Governance Platform

Once Intent Invariance is established empirically (via NeurIPS ablation), ΔS becomes a
compliance metric — not just a research metric.

### 11.1 Policy-gated deployment

Before an AI workflow reaches production, assert:

```yaml
# .spl-policy.yaml
max_intent_drift: 0.15        # ΔS ≤ 0.15 required for green-light
required_judge_models: 2      # at least 2 independent judges
required_human_checkpoint: true  # Mermaid review step mandatory
```

`spl3 gate --policy .spl-policy.yaml S6-compare.json` exits non-zero if policy fails.
Plugs into CI/CD pipelines as a pre-deployment quality gate.

---

### 11.2 Audit trail

Every compiled workflow carries a `splc_manifest.json` (already implemented for `splc compile`).
Extend to cover the full lineage:

```json
{
  "spec_sha256": "...",
  "spl_sha256":  "...",
  "code_sha256": "...",
  "intent_drift_score": 0.08,
  "judge_model": "claude-sonnet-4-6",
  "approved_by": "human@org",
  "approved_at": "2026-05-18T..."
}
```

Satisfies SOC 2 / ISO 42001 AI governance audit requirements without additional tooling.

---

## 12. Federated AI Research Network

### 12.1 Cross-institution experiment sharing

NeurIPS experiments produce structured compare JSON files. A lightweight federation
protocol lets research groups share experiment results without sharing proprietary code:

```bash
spl3 experiment publish --results NeurIPS-26-lab/ --registry research.splhub.org
spl3 experiment pull --paper "Beyond Vibe Coding" --step S6
```

Enables meta-analysis across labs: does ΔIR > 0 hold across institutions, models, and
domains? This is the empirical foundation for SPL as a standard.

---

## 13. Live Intent Monitoring (Operational ΔS)

### 13.1 Production drift detection

Intent Invariance is measured at compile time today. In production, model updates and
prompt drift cause the *same `.spl`* to produce different outputs over time. Monitor this:

```bash
spl3 monitor --workflow my-agent.spl \
  --sample-rate 0.05 \          # score 5% of production runs
  --alert-threshold 0.2 \       # alert if ΔS degrades past 0.2
  --compare-against baseline/   # compare against certified baseline outputs
```

**Why:** LLM providers update models silently (e.g., `claude-3-5-sonnet` point releases).
A workflow certified at ΔS = 0.08 may drift to ΔS = 0.25 after a provider update.
Live monitoring catches this before users report it.

---

## 14. AI Workflow Version Control (Semantic git diff)

### ~~14.1 `spl3 diff`~~ [Descoped]

`spl3 compare file1.spl file2.spl` already covers this — it runs character-level
(`--mode git-diff`), semantic (`--mode llm`), syntactic (`--mode ast-diff`), and
structural tiers, then synthesizes a verdict (EQUIVALENT / REFACTORED / DEGRADED /
DIVERGED). A dedicated `spl3 diff` command would add no distinct value.

---

## Summary Table

| # | Feature | Theme | Effort | Value | Status |
|---|---------|-------|--------|-------|--------|
| — | Ablation pipeline (S7–S10) | Research | — | — | ✅ Done |
| — | `spl2mmd` | Pipeline | — | — | ✅ Done |
| — | `compare --format html` | Reporting | — | — | ✅ Done |
| — | `text2mmd` / `vibe` file preprocessing | Pipeline | — | — | ✅ Done |
| — | `vibe --spec` (spec-driven) | Pipeline | — | — | ✅ Done |
| 1.1 | `spl3 experiment run` | Automation | — | — | ✅ Done |
| 1.2 | `spl3 experiment report` | Automation | — | — | ✅ Done |
| 1.3 | `compare --batch` | Automation | Low | Medium | Planned |
| 2.1 | `spl3 pipeline` | Pipeline | High | Medium | Planned |
| 2.2 | Streaming LLM output | DX | Low | Medium | Planned |
| 3.1 | `--mode rouge` | Metrics | — | — | ✅ Done |
| 3.2 | Composite Δ*S* score | Metrics | Low | Medium | Planned |
| 3.3 | Structured JSON diff taxonomy | Metrics | Medium | Medium | Planned |
| 4.1 | Deterministic crewai/autogen | Compiler | High | Medium | Planned |
| 4.2 | swift/snap/edge targets | Compiler | High | Low | Planned |
| 4.3 | SPL `IMPORT` statement | Language | — | — | ✅ Done |
| 4.4 | Semantic linting in `validate` | Quality | — | — | ✅ Done |
| 4.5 | `SOLVE`/`ASSERT` + IPython kernel | Language | — | — | ✅ Done |
| 4.6 | `CREATE TOOL_API` + tool registry | Language | — | — | ✅ Done |
| 4.7 | Domain micro-textbook targets (`python/<domain>`) | Compiler | — | — | ✅ Done |
| 4.8a | SageMath kernel backend (verifier coverage) | Language | Low | High | **Current focus** |
| 4.8b | Lean 4 + mathlib proof backend (`machine_proved` tier) | Language | High | Very High | **Current focus** |
| 5.1 | VS Code extension | DX | — | — | ✅ Done |
| ~~5.2~~ | ~~`spl3 serve`~~ | DX | — | — | **Descoped** (VibeSCOPE FastAPI covers this) |
| 5.3 | `vibe` provenance manifest | Quality | Low | Medium | Planned |
| — | `spl3 cache` Layer 2 content cache | Pipeline | — | — | ✅ Done |
| 6.0 | `spl3 test` pipeline-level workflow tests | Testing | — | — | ✅ Done |
| 6.1 | Golden-file regression tests | Testing | Medium | Medium | Planned |
| 7.1 | Cross-runtime round-trip tests | DODA | Low | High | Planned |
| 7.2 | `spl3 migrate` pipeline command | DODA | Medium | High | ✅ Done |
| 7.3 | Multi-judge evaluation (`spl3 judge` panel) | Research | — | — | ✅ Done |
| 8.0 | Momagrid Hub registry + Hub-to-Hub peering | Reliability | — | — | ✅ Done |
| 8.1 | DBOS execution backend (`--target python/dbos`) | Reliability | High | Very High | **Priority 1** |
| 8.2 | Time-travel debugging via DBOS | Reliability | Medium | High | Planned |
| 8.3 | Momagrid persistent task queues | Reliability | Medium | Very High | **Priority 1** |
| 9 | `spl3 migrate` verified migration service | DODA | Medium | Very High | **Priority 2** |
| 10.1 | SPL Standard Library | Standardization | Medium | Very High | **Priority 3** — tool half done (✅ 4.6); pattern half open |
| 10.2 | SPL Registry | Standardization | High | High | Partial — Hub registry done (✅ 8.0); public registry open |
| 11.1 | Policy-gated CI/CD deployment | Governance | Medium | High | Planned |
| 11.2 | Audit trail / lineage manifest | Governance | Low | High | Planned |
| 12.1 | Federated experiment sharing | Research | High | Medium | Planned |
| 13.1 | Live intent monitoring (operational ΔS) | Reliability | High | High | Planned |
| ~~14.1~~ | ~~`spl3 diff`~~ | DX | — | — | **Descoped** (`spl3 compare` covers this) |
