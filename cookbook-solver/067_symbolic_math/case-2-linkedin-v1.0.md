# Ten Models, Twenty Math Problems, One Deterministic Engine — 400 Cells Later

We ran 400 cells of symbolic math. The results are worth sharing.

A few weeks ago I published a single-problem experiment: nine models, one
pipeline, one algebra question. The natural response was *"sure, but one
problem isn't a benchmark."* Fair. So we scaled up — 10 models, 20 problems
spanning five difficulty tiers, with an A/B control arm built in — and ran
every combination. Here is what 400 data cells look like.

## The setup

### The problem battery

Twenty problems, five tiers, each testing a distinct region of undergraduate
mathematics:

| Tier | What it tests | Example |
|------|---------------|---------|
| T0 | Single-step differentiation | differentiate x⁴ − 2x² + 1 |
| T1 | Multi-step algebra (expand → diff → factor → solve) | differentiate 3x³ − x, factor, solve |
| T2 | Transcendental functions and limits | find lim(sin x / x) as x→0 |
| T3 | Integration, linear systems, eigenvalues | integrate √(4 − x²) |
| T4 | ODEs, infinite series, complex roots | solve y′ = y, y(0) = 1 |
| T5 | Laplace transforms with round-trip verification | inverse Laplace of s/(s²+4), then verify |

### The pipeline — with an A/B arm

Each problem was run through two arms of the same pipeline:

- **solver=true** (the neurosymbolic arm): the LLM decomposes the problem
  into an ordered list of symbolic operations; **SymPy** — a deterministic
  math engine — executes and verifies each step; the LLM explains the
  verified result in plain English.
- **solver=false** (the LLM-only arm): the LLM answers directly, no symbolic
  kernel, no verification. A clean control.

The A/B design is the key instrument: the gap between a model's score on
`solver=true` versus `solver=false` measures something specific — not raw
intelligence, but the ability to decompose a problem into structured,
executable steps. That decomposition skill turns out to be far from uniform.

### The ten models

| Model | Owner | Type |
|-------|-------|------|
| `sonnet-4-6` | [Anthropic](https://www.anthropic.com) | Frontier API |
| `rnj-1` | [Essential.AI](https://essential.ai) | Open-weight, specialized |
| `qwen2.5`, `qwen3` | [Alibaba](https://qwenlm.github.io) | Open-weight |
| `gemma3`, `gemma4:12b` | [Google](https://ai.google.dev/gemma) | Open-weight |
| `phi3`, `phi4` | [Microsoft](https://azure.microsoft.com/en-us/products/phi) | Open-weight |
| `deepseek-r1` | [DeepSeek](https://www.deepseek.com) | Open-weight, reasoning |
| `lfm2.5` | [Liquid AI](https://www.liquid.ai) | Non-transformer architecture |

All local models (except sonnet-4-6) run via [Ollama](https://ollama.ai) — no API key, no bill.

## The results

| Model | solver=true (20 problems) | solver=false (20 problems) | avg latency (solver) |
|-------|--------------------------|---------------------------|----------------------|
| `sonnet-4-6` | **19/20** | 20/20 | 13.5s |
| `rnj-1` | **15/20** | 20/20 | 4.6s |
| `qwen2.5` | 12/20 | 20/20 | 2.8s |
| `qwen3` | 12/20 | 20/20 | 22.5s |
| `gemma3` | 11/20 | 20/20 | 3.0s |
| `phi3` | 9/20 | 20/20 | 3.4s |
| `lfm2.5` | 7/20 | 15/20 | 7.5s |
| `phi4` | 2/20 | 17/20 | 3.8s |
| `deepseek-r1` | 2/20 | 6/20 | 24.2s |
| `gemma4:12b` | 2/20 | 0/20 | 46.0s |

*Pass criteria: solver=true counts `complete` only (SymPy verified the full
chain); solver=false counts `complete` or `unverified_success` (no kernel by
design).*

## What the numbers actually say

### Claude is the gold standard — but one failure deserves an asterisk

`sonnet-4-6` scored 19/20 on the solver arm. The single failure (p017, an
ODE initial-value problem) was a SymPy library bug — `'list' object has no
attribute 'is_Float'` — not a model error. Claude's decomposition was
textbook-correct; the engine hit an edge case in its own evaluation. A
99/100 model score is being reported as 95/100 here because we hold the
solver-arm to strict verified correctness, and that strictness cuts both ways.

### rnj-1 is the standout open-weight result

Essential.AI's `rnj-1` scores **15/20** on the solver arm at **4.6 seconds
average** — the fastest latency of any model that cleared double-digit verified
passes. It answers `solver=false` at a perfect 20/20, meaning it can reason
through all 20 problems correctly. But more importantly, it can *also*
decompose them into precise, structured symbolic steps that SymPy can execute
without repair — which is a different, harder skill.

That combination — reasoning power *plus* structured planning capability,
running locally in under 5 seconds — is exactly what justifies building a
specialized model rather than relying on a frontier API. A business case built
on "better at the specific task your pipeline actually needs" is far more durable
than "bigger in general."

### The solver=false arm is a trap score

Eight of ten models score 20/20 on `solver=false`. That sounds impressive until
you read what it means: the model answered directly, without any verification,
and the answer *looked* correct. We have no proof it was. This is not a minor
caveat — on the three hardest tiers (T3–T5), several models generate fluent,
confident explanations for answers that a symbolic check would immediately
reject.

The only two models that couldn't fake it on `solver=false` tell you something:
`gemma4:12b` (0/20) failed even the unverified arm, which means the problem
isn't the solver — the model simply can't follow the instruction format. And
`lfm2.5` (15/20) showed inconsistency we've documented before: fluent, confident,
occasionally wrong, no signal to distinguish which.

### phi4's split is a diagnostic, not just a failure

`phi4` scores 2/20 on `solver=true` and 17/20 on `solver=false`. That 15-point
gap is the sharpest in the dataset. It tells a specific story: `phi4` can reason
through problems in free form — its internal chain-of-thought gets the right
answer most of the time — but it cannot follow the narrow, structured
decomposition instruction that the solver arm requires. Markdown fences, extra
prose, wrong field names — the format slips, SymPy rejects the plan, and 17
correct answers become 2 verified ones. The intelligence is there; the
instruction-following precision isn't.

### gemma4:12b fails in both directions

Largest Google open model in this test, slowest (46 seconds average), worst
score — 2/20 verified, 0/20 even unverified. It burns its token budget at both
ends of the pipeline and returns nothing usable. The failure is loud and honest,
which is at least something, but a 46-second timeout that reliably produces
nothing is not a model you route workloads through.

### qwen2.5 is still the quiet efficiency champion

At **2.8 seconds** and 12/20 verified passes, `qwen2.5` remains what it was in
the single-problem test: fast, correct on most problems, zero cost, zero
infrastructure. Released quietly in September 2024, still competitive eighteen
months later. For a student or researcher running locally on modest hardware,
this is the default starting point.

## The A/B gap is the real finding

The single most useful number in this dataset is not any model's total score —
it is the difference between its two arms.

| Model | solver gap (true − false) | What it measures |
|-------|--------------------------|-----------------|
| `phi4` | −15 | Reasons well, decomposes poorly |
| `deepseek-r1` | −4 | Similar: strong internal reasoning, weak structured planning |
| `lfm2.5` | −8 | Inconsistent on both axes |
| `sonnet-4-6` | −1 | Near-perfect on both; gap is a library bug |
| `rnj-1` | −5 | Solid on both; gap reflects genuine hard problems |
| `gemma3` | −9 | Fast and capable on easy tiers; harder problems expose limits |

A model that scores high on `solver=false` but low on `solver=true` is
performing "confident direct reasoning" — which is exactly the failure mode
worth designing against. The pipeline's point is not to make the model smarter;
it is to route the parts that must be exact through an engine that is exact by
construction. A model that cannot stay in that lane cannot benefit from the
architecture, no matter how well it reasons in free form.

## Why scale alone doesn't close this gap

Biology ran this experiment over a timescale no AI lab can replicate. The human
brain isn't the largest brain nature produced — not even close. What set it
apart was never raw size; it was deeper, more layered connectivity — structure,
not scale. Evolution had every opportunity to keep growing brains and let scale
do the work. It didn't, because past a certain point, that isn't where the
returns are.

Statistical learning is, at its core, sophisticated pattern-fitting. That is an
extraordinary capability — and it is *not* "exact symbolic computation," any
more than a brilliant essayist is automatically a reliable accountant. No amount
of additional fitting closes that gap, because it was never a fitting problem
to begin with. `deepseek-r1` is a reasoning-fine-tuned model that scores 2/20
on the solver arm despite solving many of the problems correctly in free form —
the issue is not intelligence, it is the ability to reduce a problem to steps
that a deterministic engine can verify. That is a structural feature of the
pipeline, not a property of any model's parameter count.

Which is the sharper way to say what this pipeline does: **we didn't make the
models better at math — we made it so they never had to be.** The lever worth
pulling isn't always "more parameters, more training, more compute." Sometimes
it is "stop asking the pattern-matcher to do the part of the job that was never
pattern-matching in the first place."

## The equity argument hasn't weakened — it has strengthened

A student in an underdeveloped country, or a curious kid without institutional
resources, has no realistic path to a frontier model API subscription. That is
a luxury, full stop. But `qwen2.5` and `gemma3` run on a modest laptop, cost
nothing, and on this 20-problem battery produce explanations that are correct
and verified by SymPy — the same verification that runs behind Claude's 19/20.
The SPL neurosymbolic architecture is what makes that possible: it routes the
hard computation through SymPy and shrinks the LLM's role to parsing intent
and explaining clearly — exactly what small models already do well.

Correct, verified, step-by-step STEM education, on hardware a student already
owns, at zero marginal cost. Not a minor efficiency gain. The goal.

It is also worth noting who built the open-weight models that made this
accessible. Google invented the Transformer architecture in 2017 ("Attention Is
All You Need", Vaswani et al.) — the foundation that eight of the ten models
here are built on. Alibaba's `qwen2.5` has stood the test of time: still
competitive, still fast, still free eighteen months after a quiet release. And
Liquid AI's `lfm2.5` is a deliberate architectural departure — a
continuous-time neural network rooted in differential equations, not attention
at all — running alongside transformer models in the same pipeline, on the same
problems, evaluated by the same criteria.

## How to reproduce

Every prompt, every token count, every log line is public. Clone and run:

- [recipe #67 SPL script](https://github.com/digital-duck/SPL.py/tree/main/cookbook/67_symbolic_math/sympy_llm.spl)
- [run_experiment.py](https://github.com/digital-duck/SPL.py/blob/main/cookbook/67_symbolic_math/run_experiment.py)
- [experiment log (rerun 20260610)](https://github.com/digital-duck/SPL.py/blob/main/cookbook/67_symbolic_math/logs-spl/case-2-log-rerun-20260610-062904.md)

```bash
git clone https://github.com/digital-duck/SPL.py.git
cd SPL.py
conda create -n spl123 python=3.11 -y && conda activate spl123
pip install -e .

# run a single model on all 20 problems (both arms):
python cookbook/67_symbolic_math/run_experiment.py -m m001

# run all 10 models (400 cells):
python cookbook/67_symbolic_math/run_experiment.py

# explore results in the Streamlit UI:
streamlit run cookbook/67_symbolic_math/app_experiment.py
```

To run local models, install [Ollama](https://ollama.ai) first:

```bash
ollama pull rnj-1
ollama pull qwen2.5
ollama pull gemma3
ollama pull phi4
# ... add others from the model list
```

## What's next

This 400-cell run answers the "one problem isn't a benchmark" objection. The
next question is whether the pattern holds on harder, more compositional
problems — the kind where the decomposition itself requires multiple nested
decisions, not just a flat list of operations.

I'm extending the problem battery now, together with a mathematician
collaborator who is helping curate problems that probe the actual edges of
where symbolic engines and LLMs each fail. The vision stays the same: a system
that is always-correct, always-explained, and within reach of any student with
a laptop — not just those with institutional budgets.

[SPL](https://github.com/digital-duck/SPL.py) is the infrastructure I'm
building to make that real, one recipe at a time.

If you work in STEM education, edtech, open-source AI, or model evaluation —
or if "bigger model" has become the default answer to every capability gap in
your world — I'd be glad to hear whether this resonates, or where you think
it breaks.
