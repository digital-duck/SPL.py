# Same Problem, Same Pipeline, Nine Models — and Only the Math Agreed

I asked nine different LLMs to solve the exact same math problem, wired into the exact
same pipeline, and watched what came back. The result changed how I think
about the "just use a bigger model" instinct that's become the default answer
to almost everything in AI right now.

## The experimental setup

### The problem

> differentiate 3x³ − x, then factor if needed, finally solve for x.

### The pipeline

Take a workflow that:

- asks an LLM to break a math problem into an ordered list of operations,
- hands each operation to **SymPy** — a deterministic symbolic-math engine, not a language model — for exact computation,
- asks an LLM to explain the verified result in plain English.

### The models

Nine models, spanning frontier APIs to free local weights:

| Model | Owner |
|---|---|
| `sonnet-4-6` | [Anthropic](https://www.anthropic.com) |
| `gemma3`, `gemma4:12b` | [Google](https://ai.google.dev/gemma) |
| `qwen2.5`, `qwen3` | [Alibaba](https://qwenlm.github.io) |
| `phi3`, `phi4` | [Microsoft](https://azure.microsoft.com/en-us/products/phi) |
| `deepseek-r1` | [DeepSeek](https://www.deepseek.com) |
| `lfm2.5` | [Liquid AI](https://www.liquid.ai) |

(Note: `claude_cli` is an SPL adapter which uses Claude Sonnet 4.6 under the hood —
that's what `sonnet-4-6` refers to here and throughout; the raw transcripts log it under its adapter name, `claude_cli`.)

### The answer should never change

By design, we should receive the same answer every time, shown below.

```
d/dx(3x³ − x)         = 9x² − 1
factor(9x² − 1)       = (3x − 1)(3x + 1)
solve((3x−1)(3x+1)=0) = x = −1/3, 1/3
```

## What we actually got: wildly varied results

If the answer never moved, what was the experiment even measuring? Whether
each model could follow a narrow, plain-spoken instruction — *twice*, at
opposite ends of the same pipeline. And on that axis, the spread was enormous:

- **Four models** (`sonnet-4-6` by Anthropic, `gemma3` and `qwen3` and
  `qwen2.5` by Google/Alibaba) did exactly what was asked, cleanly. Two stood
  out: Google's `gemma3` at **6.1 seconds** and Alibaba's `qwen2.5` at
  **7.2 seconds** — both faster than the frontier model, both producing clean,
  well-structured explanations, and both running **free, locally, on consumer
  hardware** via Ollama. No API key. No bill. `qwen2.5` was nearly **3× faster**
  than its own newer sibling `qwen3` on the identical task.
- **One model** (Microsoft's `phi4`) produced garbage wrapper steps — markdown
  code fences that SymPy rejected cleanly — but the three substantive steps
  (diff → factor → solve) ran correctly and the final explanation was fully
  right. The architecture absorbed the noise without any assistance.
- **One model** (Microsoft's `phi3`) hallucinated off-script in a different way
  every run — once generating Python code about boiling water at altitude, once
  treating the polynomial as `exp(x)`. The pipeline ran its steps faithfully on
  whatever `phi3` handed it, but the input was garbage so the output was too.
  Unlike `phi4`, the architecture did *not* recover — `phi3` missed x = ±1/3
  every time.
- **One model** (Google's `gemma4:12b`) burned its entire response budget at
  *both* ends of the pipeline and came back with nothing — `(no COMMIT)`, every
  single run, ~80 seconds wasted for zero usable output. At least that failure
  is loud and honest: nothing to mistake for an answer.
- **Two models** (DeepSeek's `deepseek-r1` and Liquid AI's `lfm2.5`) bypassed
  the pipeline entirely: both burned their full 1,000-token budget on the
  decomposition step without producing a single `expr|op` line — spending every
  token on internal chain-of-thought reasoning instead. SymPy never ran. More
  on this below.

## The ones that made me stop and think

`deepseek-r1` and `lfm2.5` — one a reasoning-fine-tuned transformer, the
other an architecture that isn't a transformer at all — showed the same
failure mode across every run: the decomposition step hit the token ceiling
and returned empty, so the symbolic engine never ran and no chain was ever
verified. And yet both came back with fluent, confident explanations reporting
`Status: complete`.

Here is where it gets interesting. `deepseek-r1` produced the correct answer
every time — its internal reasoning is simply strong enough to solve the
problem without SymPy. `lfm2.5` was less consistent: in one run it correctly
decomposed the problem and ran the full verified pipeline; in another it
bypassed the pipeline and still got the right answer; in a third run it
bypassed the pipeline and gave **the wrong answer** — `x = 0, x = √(1/3),
x = −√(1/3)`, solving the original polynomial `3x³ − x = 0` rather than its
derivative. Fluent, confident, wrong — and `Status: complete`.

That is the failure mode worth designing against. The verified engine would
have caught it immediately. Without it, the wrong answer is
*indistinguishable* from the right one — same format, same confidence, same
status signal. **The system's outward signals looked identical whether SymPy
ran three times over, or never ran at all.** If you're building anything that
reports "done" to a human, that gap is the thing to close — not the wrong
answers that look wrong (those are easy to spot), but the wrong answers that
look exactly right.

## Why I think this matters more broadly

Biology already ran this experiment, over a much longer timescale than any AI
lab has access to. The human brain isn't the largest brain nature produced —
it isn't even close. What set it apart was never raw size; it was *deeper,
more layered connectivity* — structure, not scale. Evolution had every
opportunity to simply keep growing brains and let scale alone do the work.
It didn't, because past a certain point, that isn't where the returns are.
Architecture is.

Statistical learning is, at its core, sophisticated pattern-fitting over data.
That's an extraordinary capability — and it is *not* the same capability as
"exact symbolic computation," any more than a brilliant essayist is
automatically a reliable accountant. No amount of additional fitting closes
that gap, because it was never a fitting problem to begin with. And yet the
industry's reflex when a model falls short is still "wait for the next,
bigger one" — more parameters, more data, more compute, same shape. This
experiment, small as it is, is a clean counter-example to that reflex: put a
*small* model that reliably stays in its lane next to a deterministic engine
that's exact by construction, and you get something a much larger, more
expensive model couldn't deliver on this task — not a close call, but an
outright win on correctness, speed, and cost together.

Which is really the sharper way to say what this whole pipeline does: **we
didn't make the model better at math — we made it so the model never had to
be.** That's a small sentence with a large consequence. It says the lever
worth pulling isn't always "more parameters, more training, more compute" —
sometimes it's "stop asking the pattern-matcher to do the part of the job
that was never pattern-matching in the first place."

It is also worth noting who built the free, open-weight models that made this
accessible. Google invented the Transformer architecture in 2017 ("Attention Is All You
Need", Vaswani et al.) — the foundation eight of the nine models in this
experiment are built on. The ninth, Liquid AI's `lfm2.5`, is a deliberate
departure: a continuous-time neural network rooted in differential equations,
not attention at all. Alibaba's `qwen2.5` was released quietly in September 2024 and has stood
the test of time: still competitive, still fast, still free. That is quality
that does not need marketing to prove itself.

That reframing — *let the LLM plan and explain; let the domain expert
compute* — generalizes far past algebra. Physics, chemistry, structural
engineering, formal logic, financial modeling: anywhere "hard science" has a
deterministic substrate (a simulator, a solver, a verified database, a proof
checker), the same shape applies. The LLM's job shrinks to what it's
*actually* good at, and the part that has to be exact — stays exact.

There is also an equity dimension I care about deeply — and honestly, it is
a large part of why I built SPL in the first place. A student in an
underdeveloped country, or simply a curious kid without institutional
resources, has no realistic path to a frontier model API subscription. That
is a luxury, full stop. But `gemma3` and `qwen2.5` run on a modest laptop,
cost nothing, and on this problem produced explanations indistinguishable in
quality from Claude Sonnet 4.6. The SPL neurosymbolic architecture is what
made that possible: by routing computation through SymPy, it shrinks the
LLM's role to parsing intent and explaining clearly — exactly what small
models already do well. The hard math stays exact by construction, regardless
of which model sits at the top of the pipeline. Correct, verified, step-by-step
STEM education, on hardware a student already owns, at zero marginal cost.
That is not a minor efficiency gain. That is the goal.

## How to reproduce

The full transcripts — every prompt, every token count, every log line — are
public. Clone the repo and run it yourself:

- [recipe #67 SPL script](https://github.com/digital-duck/SPL.py/tree/main/cookbook/67_symbolic_math/sympy_llm.spl)
- [case-2-log-rerun-20260609-011821.md](https://github.com/digital-duck/SPL.py/blob/main/cookbook/67_symbolic_math/logs-spl/case-2-log-rerun-20260609-011821.md)

To run the local models (`gemma3`, `qwen2.5`, `phi3`, `phi4`, etc.), install
[Ollama](https://ollama.ai) — a one-command local model server that runs on
Mac, Linux, and Windows. Once installed, pull the models you want:

```bash
ollama pull gemma3
ollama pull qwen2.5
ollama pull phi4
ollama pull deepseek-r1
# add any others from the model list
```

Then clone the repo and run the experiment:

```bash
git clone https://github.com/digital-duck/SPL.py.git
cd SPL.py
conda create -n spl123 python=3.11 -y && conda activate spl123
pip install -e .
python cookbook/67_symbolic_math/run_experiment.py -p p003 && python cookbook/67_symbolic_math/run_analysis.py
```

## Our next expedition

This recipe lives in an open-source project called [SPL](https://github.com/digital-duck/SPL.py) — a declarative
language for building exactly this kind of "probabilistic ↔ deterministic"
pipeline. Because the workflow is just a script, running it across a *battery*
of STEM problems and a wider model roster is now a parameter sweep, not an
engineering project — and every run produces a machine-checkable trace, so
grading correctness doesn't need a human in the loop.

I'm building out exactly that battery now — together with a mathematician
collaborator who can help curate problems that actually probe the edges of
what symbolic engines and LLMs each do well. The vision is a system that is
always-correct, always-explained, and within reach of any student with a
laptop — not just those with institutional budgets. I'll be sharing more data
as it comes in.

If you work in STEM education, edtech, or open-source AI — or if "bigger
model" has simply become the default answer to every capability gap in your
world — I'd love to hear whether this resonates, or where you think it
breaks. Quality STEM education should not be a luxury. SPL is the
infrastructure I'm building to make that real, one recipe at a time.
