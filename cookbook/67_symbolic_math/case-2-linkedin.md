# Same Problem, Same Pipeline, Nine Models — and Only the Math Agreed

I gave nine different LLMs the exact same math problem, wired into the exact
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

We selected the following 9 models: `sonnet-4-6`, `gemma3`, `gemma4:12b`,
`qwen2.5`, `qwen3`, `phi3`, `phi4`, `deepseek-r1`, `lfm2.5`.

*`claude_cli` is an SPL adapter which uses Claude Sonnet 4.6 under the hood —
that's what `sonnet-4-6` refers to here and throughout; the raw transcripts in
`case-2.md` log it under its adapter name, `claude_cli`.*


### The answer should never change

By design, we should receive the same math answer every time, shown below.

```
d/dx(3x³ − x)        = 9x² − 1
factor(9x² − 1)      = (3x − 1)(3x + 1)
solve((3x−1)(3x+1)=0) = x = −1/3, 1/3
```

## What we actually got: wildly varied results

If the answer never moved, what was the experiment even measuring? Whether
each model could follow a narrow, plain-spoken instruction — *twice*, at
opposite ends of the same pipeline. And on that axis, the spread was enormous:

- **Four models** (`sonnet-4-6`, `gemma3`, `qwen3`, `qwen2.5`) did exactly
  what was asked, cleanly, and `qwen2.5` did it in **8.8 seconds** — as fast
  as the frontier model in the lineup, and nearly **3x faster** than its own
  newer-numbered sibling `qwen3` on the identical task.
- **Two models** (`phi3`, `phi4`) wandered off-script mid-pipeline — one
  hallucinated an unrelated integration step complete with `√` and `∫`
  symbols; the other wrapped its output in a markdown code fence that got fed
  to the math engine as if it were an equation. In both cases the engine
  rejected the garbage cleanly, and — this is the part I didn't expect — **the
  final explanation still recovered and landed on the right answer anyway.**
  The architecture absorbed the damage.
- **Two models** (`gemma4:12b`, `deepseek-r1`) simply ran out of road —
  burned their entire response budget at *both* ends of the pipeline and came
  back with nothing. Total time: nearly **a minute and a half**, for zero
  usable output. At least that failure was loud and honest: `(no COMMIT)`,
  nothing to mistake for an answer.

## The one that made me stop and think

One model — `lfm2.5`, an architecture that isn't a transformer at all —
produced *empty* output from the planning step (the same dead end as
`gemma4:12b`), which means the symbolic engine never ran, no chain was ever
verified... and yet the final explanation came back **completely correct**,
fluently narrated, reporting `Status: complete`.

From the outside, that response is *indistinguishable* from one that came out
of the verified pipeline. It's worth being fair here: small math-tuned models
of this kind are sometimes specifically trained on exactly this class of
problem, so this may simply be a model that's *good at this particular
arithmetic* doing it natively — not a lucky guess. I don't know which, and one
data point on a textbook cubic isn't enough to say.

But that's exactly the point worth sitting with: **the system's outward
signals — "complete," a confident paragraph, a plausible number — looked
identical whether the verified engine ran three times over, or never ran at
all.** If you're building anything that reports "done" to a human, that gap is
the thing to design against — not the wrong answers (those are easy to spot),
but the *right-looking* answers that arrived by an unverified path.

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

That reframing — *let the LLM plan and explain; let the domain expert
compute* — generalizes far past algebra. Physics, chemistry, structural
engineering, formal logic, financial modeling: anywhere "hard science" has a
deterministic substrate (a simulator, a solver, a verified database, a proof
checker), the same shape applies. The LLM's job shrinks to what it's
*actually* good at, and the part that has to be exact — stays exact.

## Where this goes next

This recipe lives in an open-source project called [SPL](https://github.com/digital-duck/SPL.py) — a declarative
language for building exactly this kind of "probabilistic ↔ deterministic"
pipeline. Because the workflow is just a
script, running it across a *battery* of STEM problems and a wider model
roster is now a parameter sweep, not an engineering project — and every run
produces a machine-checkable trace, so grading correctness doesn't need a
human in the loop.

I'm building out exactly that battery now — together with a mathematician
collaborator who can help curate problems that actually probe the edges of
what symbolic engines and LLMs each do well — and there's a real case that
this shape of system is *underrated* for STEM education and even early-stage
math research: always-correct, always-explained, at small-model cost. I'll be
sharing more data as it comes in. If "bigger model" has become the default
answer to every capability gap in your world too, I'd love to hear whether
this resonates — or where you think it breaks.

---
*The full transcripts behind this post — every prompt, every token count, every
log line — are public: [`case-2.md`](https://github.com/digital-duck/SPL.py/blob/main/cookbook/67_symbolic_math/case-2.md), part of [recipe 67](https://github.com/digital-duck/SPL.py/tree/main/cookbook/67_symbolic_math) in the SPL cookbook.*
