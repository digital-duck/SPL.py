# Design: `spl3 judge`

> **Status**: Approved — complete. Phase 1 and Phase 2 done; judge→cache `--cache-key` integration done. 69/69 tests pass (conda env `spl123`, Python 3.11.15).

---

## 1. Motivation — `compare` vs `judge`

`spl3 compare` answers: *"how different are these two things?"* — structural diff,
similarity scores, a synthesized `EQUIVALENT|REFACTORED|DEGRADED|DIVERGED` verdict.
It always takes two inputs.

`spl3 judge` answers: *"how good is this thing against criteria?"* — evaluative
verdict against a rubric. It takes one input (or a set of candidates for pairwise
ranking) and explicit evaluation criteria. The two commands are orthogonal.

**Existing prior art in-repo:**
- `NeurIPS-26-lab/R3-judge/` — a completed PocketFlow judge experiment:
  Generator→Judge loop, judge returns `{score 1–10, reasoning, verdict: PASS|FAIL,
  feedback}`, threshold ≥ 7, max 3 retries. This is the reference implementation
  for the single-judge pattern.
- `spl3 compare --mode llm` — LLM semantic tier already uses a judge-like prompt
  (Structure/Logic/Quality/Syntax scores 1–10). `spl3 judge` will generalize and
  decouple this pattern.
- `--judge-adapter` / `--judge-model` flags already present in the NDD pipeline
  (S6/S9/S10 steps) — a judge role is already implicitly wired in.

---

## 2. Open-Source Survey

### 2.1 Framework Landscape

| Framework | License | Key abstraction | Structured verdict | Pluggable backends | Reuse strategy |
|-----------|---------|-----------------|--------------------|--------------------|----------------|
| **DeepEval** | Apache 2.0 | `Metric` class (rubric + LLM call bundled) | JSON test report | Yes — Anthropic, OpenAI, custom | Borrow rubric schema design; do not import as dep |
| **RAGAS** | Apache 2.0 | Claim decomposition → per-claim LLM verify | Numeric scores via structured JSON | Yes — any model with reliable JSON output | Claim-level decomposition pattern useful for `spl-compliance` rubric |
| **Prometheus** | Apache 2.0 | Fine-grained rubric scoring, pairwise ranking | Score + reasoning | Open-source weights (7B, 8×7B) | Use as local judge backend option (no API key) |
| **Verdict** (Haize Labs) | OSS | `Unit` (single LLM call) + `Pipeline` (composition) | Typed schema: numeric/categorical/boolean | Yes — configurable per Unit | Closest design match for panel mode; adopt pipeline composition pattern |
| **OpenAI Evals** | MIT | Eval harness + evaluator registry | JSON schema + rubric grading (1–7) | Primarily OpenAI; LLM judge swappable | Registry pattern for built-in rubrics |
| **LangChain evaluators** | MIT | LLM-as-judge + trajectory eval | Structured via LangSmith | Yes | Trajectory evaluation pattern for multi-step SPL workflows |
| **lm-evaluation-harness** | MIT | Benchmark harness | Per-task metrics | Yes | Inspiration for batch/dataset evaluation mode |
| **Prometheus 2** | Apache 2.0 | Rubric-grounded, avoids GPT-4 dependency | Score (1–5) + critique | Open weights | Drop-in judge for air-gapped / offline environments |

**Decision**: Do not add new framework dependencies. SPL already has a multi-provider
adapter layer covering all major backends. `spl3 judge` will be a thin module that
uses the existing adapter layer — same pattern as `spl3 compare`.

### 2.2 Academic Consensus — Bias and Mitigations

Known failure modes for single-judge LLM evaluation:

| Bias | Description | Mitigation |
|------|-------------|------------|
| **Position bias** | LLM favors first/last response in pairwise ranking | Swap-consistency check: run twice with order reversed; flag disagreement |
| **Verbosity bias** | Longer responses score higher regardless of quality | Criterion-level scoring before overall; criteria must penalize padding |
| **Self-enhancement bias** | Model inflates scores for its own outputs | Panel with diverse model families; never use same model as generator |
| **Agreeableness bias** | LLM avoids explicit negative judgments | Chain-of-thought critique per criterion before verdict; structured output forces reasoning |

**Strongest mitigations** (consensus from Prometheus 2, JudgeBench, LLMs-as-Judges survey 2024):
1. **Chain-of-thought critique first** — judge reasons per criterion before deciding; reduces verbosity and agreeableness inflation
2. **Diverse panel** — Claude + Gemini + Qwen (or open-weight) covers complementary blind spots better than same-family ensemble
3. **Swap consistency** — run pairwise twice, mark inconsistent pair as `LOW_CONFIDENCE`
4. **Structured output** — force score + reasoning + feedback as JSON; prose-only verdicts are not auditable

---

## 3. Core Types

```python
# spl3/judge/types.py

@dataclass
class Rubric:
    name: str                          # "spl-compliance" | "correctness" | custom
    criteria: list[str]                # e.g. ["reducibility", "acyclicity", "completeness"]
    pass_threshold: float              # score >= this → PASS
    weight: dict[str, float]           # per-criterion weight (default: equal)
    prompt_template: str               # injected into judge prompt

@dataclass
class JudgeResult:
    verdict: str                       # "PASS" | "FAIL" | "ESCALATE"
    score: float                       # 0.0 – 10.0
    confidence: str                    # "HIGH" | "MEDIUM" | "LOW"
    reasoning: str                     # chain-of-thought explanation
    feedback: str                      # actionable — feeds RETRY GENERATE loop
    criteria_scores: dict[str, float]  # per-criterion breakdown
    model: str
    adapter: str
    rubric: str

@dataclass
class PanelResult:
    verdict: str                       # aggregated: "PASS" | "FAIL" | "ESCALATE"
    score: float                       # mean of panel scores
    confidence: str                    # degrades when judges disagree
    consensus: str                     # "UNANIMOUS" | "MAJORITY" | "SPLIT"
    individual: list[JudgeResult]      # one per panel member
    dissent: Optional[str]             # summary of minority position if SPLIT
    swap_consistent: Optional[bool]    # None if swap check not run
```

**Key design decision**: `JudgeResult` is a strict superset of the `compare` synthesis
object (`verdict`, `confidence`, `key_finding`). The compare pipeline can adopt
`JudgeResult` for its LLM semantic tier without breaking changes.

---

## 4. Architecture

```
spl3/judge/
├── __init__.py          # exports run_judge, run_panel
├── types.py             # JudgeResult, PanelResult, Rubric
├── engine.py            # run_judge(content, rubric, adapter) → JudgeResult
│                        # run_panel(content, rubric, members) → PanelResult
├── aggregators.py       # majority_vote, confidence_weighted, swap_consistency
├── prompt.py            # build_judge_prompt(content, rubric) → str
├── report.py            # render_judge_report(result) → markdown/json/text
└── rubrics/
    ├── __init__.py      # load_rubric(name) → Rubric
    ├── spl_compliance.yaml    # SPL syntax + semantic correctness
    ├── correctness.yaml       # factual / mathematical correctness
    ├── clarity.yaml           # prose clarity and completeness
    └── ai_review.yaml         # generic AI-generated content review
```

Mirrors `spl3/compare/` exactly — same report.py interface, same output format
options (markdown, json, text), same `--adapter` / `--model` flags.

### 4.1 Single Judge Engine

```python
async def run_judge(
    content: str,
    rubric: Rubric,
    adapter_name: str,
    model: Optional[str] = None,
    swap_check: bool = False,
) -> JudgeResult:
    prompt = build_judge_prompt(content, rubric)
    llm = get_adapter(adapter_name, **({"model": model} if model else {}))
    raw = await llm.generate(prompt)
    result = parse_verdict(raw, rubric, adapter_name, model)
    if swap_check:
        result.swap_consistent = await _run_swap_check(content, rubric, llm, model, result)
    return result
```

The judge prompt enforces chain-of-thought structure:
1. Score each criterion independently (mitigates verbosity bias)
2. State overall score and confidence
3. Give verdict (PASS / FAIL / ESCALATE)
4. Give feedback (actionable, ≤ 3 bullet points — feeds RETRY)

### 4.2 Panel Engine

```python
async def run_panel(
    content: str,
    rubric: Rubric,
    members: list[tuple[str, Optional[str]]],  # [(adapter, model), ...]
    aggregation: str = "majority",              # "majority" | "confidence_weighted" | "unanimous"
    swap_check: bool = False,
) -> PanelResult:
    tasks = [run_judge(content, rubric, a, m, swap_check) for a, m in members]
    results = await asyncio.gather(*tasks)      # CALL PARALLEL — judges run concurrently
    return aggregate(results, aggregation)
```

**Aggregation strategies:**

| Strategy | Verdict rule | Score | Confidence rule |
|----------|-------------|-------|-----------------|
| `majority` | PASS if > 50% say PASS | Mean | HIGH if unanimous; MEDIUM if majority; LOW if split |
| `confidence_weighted` | Weighted by each judge's self-reported confidence | Weighted mean | Inherited from winners |
| `unanimous` | PASS only if all say PASS; else ESCALATE | Min (conservative) | Always HIGH for PASS |

**Split → ESCALATE**: if judges are evenly split (e.g. 1 vs 1 in a 2-member panel),
verdict is `ESCALATE` rather than a coin flip. This surfaces the disagreement for
human review — exactly the right behavior.

---

## 5. CLI Design

```
spl3 judge <file>
    [--criteria BUILTIN|FILE]        rubric name or path to .yaml rubric
    [--llm ADAPTER:MODEL]            judge spec; repeat for panel mode (wins over --adapter/--model)
    [--adapter NAME]                 legacy: single judge adapter (used only if --llm not given)
    [--model MODEL]                  legacy: single judge model   (used only if --llm not given)
    [--aggregation STRATEGY]         majority | confidence_weighted | unanimous
    [--swap-check]                   run swap consistency check
    [--format markdown|json|text]
    [-o OUTPUT_FILE]
```

**`--llm` flag convention:**
- Format: `<adapter>:<model-id>` — e.g. `claude_cli:claude-opus-4-6`, `openrouter:google/gemini-2.5-pro`
- Repeatable (`multiple=True`): one `--llm` → single judge; two or more → panel mode (concurrent)
- **Precedence**: if `--llm` is given, `--adapter`/`--model` are ignored even if also provided
- `--adapter`/`--model` remain supported as the legacy fallback for existing scripts

**Examples:**

```bash
# Single judge, built-in rubric (new style)
spl3 judge output.md --criteria clarity --llm claude_cli:claude-opus-4-6

# Single judge, custom rubric (new style)
spl3 judge my_section.md --criteria ./rubrics/math-check.yaml --llm claude_cli:claude-opus-4-6

# Single judge (legacy style — still works)
spl3 judge output.md --criteria clarity --adapter claude_cli --model claude-opus-4-6

# Panel of three — repeat --llm, runs concurrently
spl3 judge output.md --criteria spl-compliance \
    --llm claude_cli:claude-opus-4-6 \
    --llm openrouter:google/gemini-2.5-pro \
    --llm openrouter:qwen/qwen-max \
    --aggregation majority --swap-check

# NDD pipeline inline — replacing compare LLM tier
spl3 judge S5-spec.md --criteria spl-compliance --llm claude_cli:claude-opus-4-6 -o S6-judge.md
```

**Output (JSON excerpt):**
```json
{
  "verdict": "PASS",
  "score": 8.2,
  "confidence": "HIGH",
  "consensus": "MAJORITY",
  "criteria_scores": { "reducibility": 9.0, "acyclicity": 8.0, "completeness": 7.5 },
  "feedback": "Criterion 'completeness': add output type annotation to WORKFLOW.",
  "swap_consistent": true
}
```

---

## 6. SPL Language Integration

### 6.1 Future verb: `JUDGE`

```spl
# Single judge — evaluates @section against the spl-compliance rubric
JUDGE @section
    AGAINST "spl-compliance"
    INTO @verdict
    OTHERWISE RETRY GENERATE refine_section(@section, @verdict.feedback)

# Panel judge — consensus required
JUDGE @section
    AGAINST "correctness"
    PANEL ["claude_cli:claude-opus-4-6", "openrouter:google/gemini-2.5-pro"]
    AGGREGATION majority
    INTO @verdict
    WHEN @verdict.verdict == "ESCALATE":
        CALL notify_human_review(@section, @verdict.dissent)
```

The `JUDGE` verb lowers to `run_judge` / `run_panel` in the executor. The
`@verdict.feedback` binding feeds directly into the existing `RETRY GENERATE`
repair loop — no new executor logic required beyond the binding.

### 6.2 `ASSERT` + `JUDGE` composition

```spl
# ASSERT delegates the check to a judge when the criterion is non-symbolic
ASSERT quality(@section) >= 7.0
    USING JUDGE adapter="claude_cli" criteria="clarity"
    OTHERWISE RETRY GENERATE refine_section(@section, @verdict.feedback)
```

This closes the gap identified in the micro-textbook design: `ASSERT` is currently
limited to deterministic / symbolic checks. A `USING JUDGE` modifier extends it
to probabilistic quality gates while preserving the ASSERT syntax.

---

## 7. Integration Points

### 7.1 `spl3 compare` — replace LLM semantic tier

The existing `--mode llm` tier in `compare` is a judge in everything but name.
After `spl3/judge/` is built, `compare_semantic()` in
`spl3/compare/tiers/semantic.py` can delegate to `run_judge(rubric="compare-focus")`
and return a `JudgeResult` instead of a raw string. The compare report renders it
identically — no user-facing change.

### 7.2 NDD pipeline — S6/S9/S10 steps

Current: `spl3 compare S1-spec.md S5-spec.md --adapter claude_cli --model claude-opus-4-6`

After: optionally replace or augment with:
```bash
spl3 judge S5-spec.md --criteria spl-compliance --llm claude_cli:claude-opus-4-6
```

`compare` measures fidelity to original spec (two-input diff).
`judge` measures absolute quality of the reconstructed spec (one-input evaluation).
Both signals are useful and complementary — the NDD leaderboard can track both.

### 7.3 Micro-textbook `ai_reviewed` trust tier

The promotion pipeline in the micro-textbook design:
```
machine_generated --(spl3 judge criteria=correctness)--> ai_reviewed
                  --(human review)---------------------> human_verified
                  --(cross-check vs reference)---------  canonical
```

`spl3 judge --criteria correctness` becomes the automated gate between
`machine_generated` and `ai_reviewed`. A panel judge with `--swap-check` raises
the bar to `MEDIUM` confidence minimum before promotion.

### 7.4 `run_python` verifier loop

For the Jupyter kernel integration (§9 of the micro-textbook design), the
symbolic verifier (`verify_math`, `shape_check`) produces a deterministic result.
`spl3 judge` handles the non-symbolic layer — prose quality, intuition, analogy
correctness — that SymPy cannot check. The two verifiers are complementary:
symbolic catches math errors; judge catches pedagogical errors.

---

## 8. Built-in Rubrics

### `spl-compliance`
Criteria: workflow identity, GENERATE signatures, CALL dependencies, EVALUATE
conditions, EXCEPTION handlers, @variable data flow. Adapted from the `spl` focus
mode already in `spl3/compare/tiers/semantic.py`.

### `correctness`
Criteria: factual accuracy, mathematical correctness, logical consistency,
no contradictions. Used by micro-textbook ai_reviewed tier.

### `clarity`
Criteria: prose clarity, completeness, appropriate level of detail, no ambiguity.

### `ai_review`
Criteria: helpfulness, harmlessness, honesty, task completion. Generic content
quality rubric for general-purpose use.

Custom rubrics are YAML files with `name`, `criteria`, `pass_threshold`, `weight`,
and `prompt_template` fields — loadable via `--criteria path/to/rubric.yaml`.

---

## 9. Implementation Plan

### Phase 1 — Single judge, CLI, built-in rubrics ✅ Done
- [x] `spl3/judge/types.py` — `JudgeResult`, `Rubric`
- [x] `spl3/judge/prompt.py` — `build_judge_prompt()` with CoT structure
- [x] `spl3/judge/engine.py` — `run_judge()` with structured JSON parsing
- [x] `spl3/judge/rubrics/` — `spl_compliance.yaml`, `correctness.yaml`, `clarity.yaml`, `ai_review.yaml`
- [x] `spl3/judge/report.py` — markdown/json/text render (mirrors compare report pattern)
- [x] `spl3 judge` CLI command in `spl3/cli.py` — with `--llm ADAPTER:MODEL` convention
- [x] Unit tests: single judge, each built-in rubric, parse error handling (39 tests)

### Phase 2 — Panel mode and aggregation ✅ Done
- [x] `spl3/judge/aggregators.py` — `majority_vote`, `confidence_weighted`, `unanimous`
- [x] `PanelResult` type
- [x] `run_panel()` with `asyncio.gather` (CALL PARALLEL)
- [x] `--llm` repeated flag activates panel mode (replaced `--panel`); `--aggregation` flag
- [x] `--swap-check` flag and swap consistency logic (single + panel)
- [x] Tests: panel with echo adapter, all three aggregation strategies, split/unanimous edge cases (28 tests)

### Phase 3 — SPL language integration
- [ ] `JUDGE` verb in lexer/parser/AST
- [ ] Executor lowering to `run_judge` / `run_panel`
- [ ] `@verdict.feedback` binding for RETRY loop
- [ ] `ASSERT ... USING JUDGE` modifier
- [ ] Integration tests via `.spl` fixtures

### Phase 4 — Stack integration
- [ ] Wire `spl3 compare --mode llm` to delegate to `run_judge`
- [ ] NDD pipeline: add `--judge-mode judge|compare|both` flag to `spl3 ndd`
- [ ] Leaderboard: add judge score column alongside compare score
- [ ] Micro-textbook: `ai_review.yaml` rubric tuned to math-content correctness

---

## 10. What Not to Build

- **No new LLM dependencies.** Prometheus weights are interesting for offline use
  but add a heavy dep. Phase 1 uses existing adapters only; Prometheus can be
  added as an optional adapter in a later sprint.
- **No DeepEval/RAGAS import.** Their rubric schema and claim-decomposition
  patterns are worth borrowing as design inspiration, but SPL's adapter layer
  already covers all backends they support. Adding them as deps would import
  framework opinions that conflict with SPL's design.
- **No UI in Phase 1.** The Streamlit UI already has a Review page; a Judge
  panel can be added there after the CLI is stable.
- **No scoring database in Phase 1.** The NDD leaderboard already aggregates
  compare scores from markdown files. Judge scores follow the same pattern —
  no new storage layer needed.
