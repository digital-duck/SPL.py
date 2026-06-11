# Neurosymbolic Math in a Structured Prompt Language

*What 400 cells of symbolic math say about open-source models, verified
reasoning, and who gets access to quality STEM education.*

## How this started

A few weeks ago I asked nine different LLMs to solve the exact same algebra
problem — *differentiate 3x³ − x, factor, solve* — wired into the exact same
pipeline. The answer never changes:

```
d/dx(3x³ − x)         = 9x² − 1
factor(9x² − 1)       = (3x − 1)(3x + 1)
solve((3x−1)(3x+1)=0) = x = −1/3, 1/3
```

The results varied wildly anyway. Some models followed the instructions
cleanly. One hallucinated Python code about boiling water at altitude. One
burned its entire token budget and returned nothing. And one gave a fluent,
confident, **wrong** answer — reported as `Status: complete` — that was
indistinguishable in format and tone from the right ones.

The natural objection was: *"sure, but one problem isn't a benchmark."* Fair.
So we scaled up — **10 models, 20 problems spanning five difficulty tiers,
with an A/B control arm built in** — and ran every combination. This is what
400 data cells look like.

## The architecture: neurosymbolic by design

The pipeline is written in [SPL](https://github.com/digital-duck/SPL.py)
(Structured Prompt Language), an open-source declarative language for building
exactly this kind of "probabilistic ↔ deterministic" workflow:

1. An LLM decomposes the math problem into an ordered list of symbolic
   operations.
2. **SymPy** — a deterministic symbolic-math engine, not a language model —
   executes and verifies each step. Exact by design.
3. The LLM explains the verified result in plain English.

The LLM plans and explains; the domain expert computes. The hard math never
passes through a pattern-matcher at all.

Each of the 20 problems ran through two arms:

- **solver=true** (neurosymbolic): decompose → SymPy verifies → explain.
- **solver=false** (LLM-only): the model answers directly. No kernel, no
  verification. A clean control.

The problem battery covers five tiers of undergraduate mathematics — from
single-step differentiation, through limits and transcendental functions,
integration and eigenvalues, ODEs and infinite series, up to Laplace
transforms with round-trip verification.

## The ten models

| Model | Owner | Type |
|-------|-------|------|
| `sonnet-4-6` | [Anthropic](https://www.anthropic.com) | Frontier API |
| `rnj-1` | [Essential AI](https://essential.ai) | Open-weight, specialized |
| `qwen2.5`, `qwen3` | [Alibaba](https://qwenlm.github.io) | Open-weight |
| `gemma3`, `gemma4:12b` | [Google](https://ai.google.dev/gemma) | Open-weight |
| `phi3`, `phi4` | [Microsoft](https://azure.microsoft.com/en-us/products/phi) | Open-weight |
| `deepseek-r1` | [DeepSeek](https://www.deepseek.com) | Open-weight, reasoning |
| `lfm2.5` | [Liquid AI](https://www.liquid.ai) | Non-transformer architecture |

Every model except `sonnet-4-6` runs locally via [Ollama](https://ollama.ai) —
no API key, no bill, on hardware a student already owns.

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

A note on `sonnet-4-6`: we included one frontier model deliberately, as a
quality reference point — and Claude earned it, with the best verified score
in the test. Its single
solver-arm failure (p017, an ODE initial-value problem) was a SymPy library
bug, not a model error — its decomposition was correct. But a reference point
is exactly that: a reference, not a requirement. Every other model in the
table runs free and local, and the architecture works the same either way.

## The standout: rnj-1, a model named after Ramanujan

The most striking open-weight result belongs to a newcomer.
[`rnj-1`](https://www.essential.ai/research/rnj-1) is named after
[**Srinivasa Ramanujan**](https://www.wikiwand.com/en/Srinivasa_Ramanujan) —
the self-taught Indian mathematician who, with no formal training and almost
no resources, produced results that still drive research a century later. A
clerk with a notebook out-thought the best-resourced institutions of his era —
proof that intelligence is distributed everywhere, indifferent to wealth and
power, waiting only for a door to open. It is hard to imagine a more fitting
namesake for what this experiment is about: serious mathematics made
accessible without institutional privilege.

The lineage behind the model is just as striking. Essential AI was founded by
**Ashish Vaswani** — the first author of "Attention Is All You Need" (2017),
the paper that introduced the Transformer architecture underpinning nearly
every model in this experiment. The person who started the transformer era
chose, as his next act, to build an open-weight math model named after
Ramanujan and [publish it on Ollama](https://ollama.com/library/rnj-1) for
anyone to pull and run locally, free.

The model lives up to the name. `rnj-1` scores **15/20** on the verified
solver arm — the best result of any open model in the test — at **4.6 seconds
average**, nearly three times faster than the frontier model. It also scores a
perfect 20/20 on the direct-answer arm. That combination matters: it can
reason through all 20 problems in free form, *and* it can break them into
precise, structured steps that SymPy can run without repair. Those are two
different skills, and the second is rarer.

A specialized open-weight model, running locally, free, in under 5 seconds,
within four problems of a frontier API on verified correctness — that is the
strongest evidence yet that "better at the exact task you need" can be a
smarter bet than "bigger in general."

## The A/B gap is the real finding

The most useful number in this dataset is not any model's total score — it is
the gap between its two arms.

Six of the ten models score a perfect 20/20 on `solver=false`. That sounds impressive
until you read what it means: the model answered directly, without any
verification, and the answer *looked* correct. We have no proof it was. On the
hardest tiers, several models generate fluent, confident explanations for
answers a symbolic check would immediately reject.

`phi4` is the sharpest diagnostic: 17/20 answering directly, 2/20 verified.
The intelligence is there — its free-form reasoning gets the right answer most
of the time — but it cannot follow the narrow, structured decomposition
instruction the solver arm requires. Markdown fences, extra prose, wrong field
names: the format slips, SymPy rejects the plan, and 17 correct answers become
2 verified ones. `deepseek-r1`, a model trained
specially for step-by-step reasoning, fails in a related way: it spends its
whole token budget thinking instead of producing the structured plan.
Reasoning well in free form is not the same skill as reducing a problem to
steps an exact engine can verify.

And that is the failure mode worth designing against — not the wrong answers
that look wrong (those are easy to spot), but the wrong answers that look
exactly right: same format, same confidence, same `Status: complete`. In the
single-problem run, `lfm2.5` once solved the wrong equation entirely and
reported success with full fluency. The verified engine catches that
immediately. Without it, nothing does.

## Why scale alone doesn't close this gap

Biology ran this experiment over a timescale no AI lab can replicate. The
human brain isn't the largest brain nature produced — not even close. What set
it apart was never raw size; it was deeper, more layered connectivity —
structure, not scale. Evolution had every opportunity to keep growing brains
and let scale do the work. It didn't, because past a certain point, that isn't
where the returns are.

Statistical learning is, at its core, sophisticated pattern-fitting. That is
an extraordinary capability — and it is *not* "exact symbolic computation,"
any more than a brilliant essayist is automatically a reliable accountant. No
amount of additional fitting closes that gap, because it was never a fitting
problem to begin with.

Which is the sharper way to say what this pipeline does: **we didn't make the
models better at math — we made it so they never had to be.** The lever worth
pulling isn't always "more parameters, more training, more compute." Sometimes
it is "stop asking the pattern-matcher to do the part of the job that was
never pattern-matching in the first place."

## STEM education is the point

A student in an underdeveloped country, or simply a curious kid without
institutional resources, has no realistic path to a frontier model API
subscription. That is a luxury, full stop. And yet genius has never checked
bank accounts before arriving — Ramanujan is the standing proof that the rich
and powerful are not automatically the gifted, and the gifted are very often
neither rich nor powerful. The next Ramanujan is out there right now, and the
only question is whether the tools reach her.

But `rnj-1`, `qwen2.5`, and `gemma3` run on a modest laptop and cost nothing.
Every answer they deliver through this pipeline is **verified by SymPy — the
same verification that runs behind Claude's 19/20.** And when a model fails,
it fails loudly and visibly — a student never receives a wrong answer dressed
up as a right one. The
neurosymbolic architecture is what makes that possible: by routing computation
through SymPy, it shrinks the LLM's role to parsing intent and explaining
clearly — exactly what small open models already do well. The hard math stays
exact by design, regardless of which model sits at the top of the
pipeline.

Correct, verified, step-by-step STEM education, on hardware a student already
owns, at zero marginal cost. That is not a minor efficiency gain. That is the
goal.

It is also worth honoring who built the open models that make this possible.
Google invented the Transformer architecture in 2017 ("Attention Is All You
Need," Vaswani et al.) — the foundation nearly every model here stands on.
Alibaba's `qwen2.5`, released quietly in September 2024, is still the
efficiency champion eighteen months later: 12/20 verified at 2.8 seconds,
free. Liquid AI's `lfm2.5` is a deliberate architectural departure — a
continuous-time neural network rooted in differential equations, not attention
at all. And Ashish Vaswani — the same Vaswani whose name leads that 2017
paper — chose to name his company's math model after a genius who proved, a
hundred years ago, that talent is distributed everywhere even when resources
are not.

## How to reproduce

Every prompt, every token count, every log line is public. Clone and run:

- [recipe #67 SPL script](https://github.com/digital-duck/SPL.py/tree/main/cookbook/67_symbolic_math/sympy_llm.spl)
- [run_experiment.py](https://github.com/digital-duck/SPL.py/blob/main/cookbook/67_symbolic_math/run_experiment.py)
- [experiment log (rerun 20260610)](https://github.com/digital-duck/SPL.py/blob/main/cookbook/67_symbolic_math/logs-spl/case-2-log-rerun-20260610-062904.md)
- [rnj-1 announcement (Essential AI)](https://www.essential.ai/research/rnj-1) · [rnj-1 on Ollama](https://ollama.com/library/rnj-1)

```bash
git clone https://github.com/digital-duck/SPL.py.git
cd SPL.py
conda create -n spl123 python=3.11 -y && conda activate spl123
pip install -e .

# run a single model on all 20 problems (both arms) — m010 is rnj-1:
python cookbook/67_symbolic_math/run_experiment.py -m m010

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
problems — where the decomposition itself requires nested decisions, not just
a flat list of operations. I'm extending the problem battery now, together
with a mathematician collaborator who is helping curate problems that probe
the actual edges of where symbolic engines and LLMs each fail.

The reframing — *let the LLM plan and explain; let the domain expert compute* —
generalizes far past algebra. Physics, chemistry, structural engineering,
formal logic, financial modeling: anywhere hard science has a deterministic
substrate (a simulator, a solver, a verified database, a proof checker), the
same shape applies.

The vision stays the same: a system that is always-correct, always-explained,
and within reach of any student with a laptop — not just those with
institutional budgets. Quality STEM education should not be a luxury.
[SPL](https://github.com/digital-duck/SPL.py) is the infrastructure I'm
building to make that real, one recipe at a time.

If you work in STEM education, edtech, open-source AI, or model evaluation —
or if "bigger model" has become the default answer to every capability gap in
your world — I'd be glad to hear whether this resonates, or where you think
it breaks.
