# Critical HN-Reader Review of the full-ladder announcement draft

- **Reviewed:** [`hackernews-draft-reviewed-2026-06-11.md`](hackernews-draft-reviewed-2026-06-11.md) (the first full-ladder draft, archived here; it superseded the SymPy-only `hackernews-v0.1.md` and is itself superseded by `hackernews-v0.2.md`)
- **Reviewer hat:** a skeptical Hacker News reader who has seen a hundred "LLM + formal methods" posts
- **Disposition:** every point below is either applied in [`hackernews-v0.2.md`](../hackernews-v0.2.md) or explicitly noted as a judgment call left to the author
- **Context note:** between drafting and this review, recipe 77 landed and was smoke-verified on all three rungs (`symbolic_math.spl`, `neurosymbolic_solver`, the experiment harness). Points that depended on "the recipe doesn't exist yet" are marked **resolved by landing**.

---

## Summary verdict

The draft's bones are right for HN: it leads with engineering, names its own weakest link (the formalization-correspondence gap), and ends with a "not claiming" section. What it lacks is armor on the four fronts HN reliably attacks: trivial demos, missing prior art, "why not just Python," and an aspirational code block that greps as vaporware. All four are fixable without changing the substance.

---

## What already lands well (keep these)

1. **The honest-limits and "what we are not claiming" sections.** HN rewards self-imposed caveats; naming the correspondence gap before a commenter does is exactly right.
2. **The failure row in the receipts table** ("badge withheld, delivery not blocked"). Honest negative results buy more credibility than the positive ones.
3. **The deterministic theorem splice** ("the LLM can fail to prove the statement; it cannot quietly prove a *different* statement"). The single most quotable engineering decision in the piece. Keep it prominent.

---

## Where the comments section will draw blood (ranked by damage)

### 1. "So you proved `n + m = m + n`. Congratulations."
The receipts are toy-level and the draft doesn't own it. Worse, two of the three
`machine_proved` wins are `exact?` citation hits, so the obvious dunk is *"this
is grep over mathlib with extra steps — the system proved nothing."* That is
answerable, but the draft never makes the defense explicit.

**Fix:** add an honest paragraph: the demos exercise plumbing, not mathematics;
the claims are deliberately within mathlib's reach because that is the stated
scope; and for textbook claims a *kernel-checked citation into a curated
library* is precisely the artifact you want — stronger correspondence evidence
than a bespoke proof of a bespoke statement. → **Applied in v0.2** ("Plumbing,
not mathematics").

### 2. No prior-art section — the #1 HN derail.
LLM+Lean is a crowded space: Draft-Sketch-Prove, LeanDojo/ReProver, llmstep,
AlphaProof, Sagredo, Terence Tao's documented workflows. The first comment will
be "no mention of any of this." The draft's claim ("no orchestration framework
we know of offers kernel-checked proof as a language-level verification
primitive") actually survives contact with that literature — those are proving
systems and research tooling, not workflow languages — but only if the author
draws the line himself.

**Fix:** two or three sentences: what exists (LLM↔Lean research tooling; general
orchestrators that can shell out to anything), and what is different here
(verification as a typed language construct with structural provenance, not a
tool call whose result a probabilistic agent interprets). → **Applied in v0.2**
("Prior art, and the actual claim").

### 3. "Why not just Python?"
Guaranteed top-three comment for any DSL announcement, and the draft never
answers it. The answer exists in the design docs (auditable artifact, notebook
carries its runtime, provenance is structural rather than convention) but the
announcement assumes it.

**Fix:** a short section phrased as the question itself, including the honest
counterpoint (if you don't need auditability, a Python script is fine).
→ **Applied in v0.2** ("Why a language and not a Python script?").

### 4. The closing workflow reads as shipped but isn't runnable.
`sage_search(@@claim@@, bound=1000)` does not exist in the repo. "The end state
we want" technically flags it, but the surrounding present tense blurs it, and
HN *will* grep.

**Fix:** label it bluntly — aspirational, this exact file does not run today,
the missing piece is the counterexample-search tool, every other line is
shipped. That sentence converts a vaporware accusation into evidence of
honesty. → **Applied in v0.2.**

### 5. Verifying the LLM with an LLM.
The faithfulness judge is itself probabilistic; "the right tool for the one
probabilistic link" is too cute and reads as turtles all the way down.

**Fix:** tighten to the structural point — the judge is a *gate that can only
withhold a badge, never grant one*; badges are granted by the kernel; and
citation-first exists precisely because named-lemma correspondence does not
depend on the judge. → **Applied in v0.2.**

### 6. The eval surface.
`sympify` / `sage_eval` over LLM-emitted strings is a code-execution surface,
and HN security people are reliable.

**Fix:** one threat-model sentence: local research tool, operator's own model
on the operator's machine, where the kernel already executes arbitrary code by
design — do not point it at untrusted input. → **Applied in v0.2.**

---

## Structural suggestions

### The lede is the wrong story.
The most viral element is buried in section two: *a model produced a complete,
correct-looking, "verified" answer while the verified chain never ran.* That is
concrete, alarming, and screenshot-able. Open with it; let the ladder be the
response to it. The current "claim in one paragraph" is also nine dense lines —
a wall, not a paragraph. → **Applied in v0.2** (new lede: "The bug that
started this").

### Title is ~95 characters; HN truncates at 80.
And "Neurosymbolic" in a title triggers reflexive eye-rolls in that crowd.
Suggested submission titles (the HN title field is independent of the doc H1):

1. `Show HN: SPL – LLM workflows where SymPy/Sage check math, Lean checks claims` (77 chars)
2. `A workflow language where ASSERT can mean "the Lean kernel checked it"` (71 chars)
3. `Kernel-checked Lean proofs as a workflow-language verification primitive` (73 chars)

→ **v0.2 keeps a short descriptive H1**; pick the submission title from the
list above at post time.

### Em-dash density.
A 2026-specific hazard: heavy em-dash prose now pattern-matches to "AI-written"
on HN and spawns its own derail thread. The draft averages several per
paragraph. → **Applied in v0.2** (converted the majority to periods and commas).

### "We" vs "I".
Solo project with a personal mission behind it. HN consistently responds better
to "I built" than to startup-we. → **Applied in v0.2** (first person singular).
Author's call to revert if Digital Duck branding matters more here.

---

## Nits

| Nit | Status |
|---|---|
| `sympolic_tools.spl` will be read as a typo of "symbolic" and mocked | **Author's chosen name** (SymPy + symbolic portmanteau). v0.2 winks at it once in passing so the comment thread doesn't get to "discover" it. |
| "keeps that protocol **byte-for-byte**" — tools were cloned *and widened*; someone will diff | Applied: "unchanged protocol". |
| `--llm claude_cli` vs `--adapter ollama --model gemma3` unexplained inconsistency | Applied: one parenthetical (`--llm ADAPTER[:MODEL]` is shorthand; `--adapter/--model` the legacy spelling). |
| `@var` vs `@@var@@` sigil soup unexplained at first code block | Applied: one-line legend at first SPL snippet. |
| "live mathlib" sounds like a hosted service | Applied: "pinned toolchain (Lean REPL v4.30.0, mathlib pinned by the lake project)". |
| No absolute repo URL anywhere (relative links die if pasted as text) | Applied: canonical URL near the top — https://github.com/digital-duck/SPL.py |
| `lfm2.5` appears with no context for why it matters | Applied: "(a liquid foundation model — not a transformer)". |
| Links to recipe-77 `readme.md` / `symbolic_math.spl` that didn't exist at draft time | **Resolved by landing** — recipe 77 shipped and is smoke-verified on all three rungs; v0.2 cites the real files and real runs. |

---

## The highest-leverage three

If only three changes were possible: (1) open with the silent-unverified-success
story, (2) add the prior-art paragraph, (3) add the "plumbing, not mathematics"
honesty beat. Everything else is polish; those three change whether the
top-voted comment is hostile or curious.

## Pre-submission checklist (first HN post)

- [ ] Submit as **Show HN** linking to the GitHub-rendered `hackernews-v0.2.md` (or the recipe readme) so relative links resolve.
- [ ] Pick a submission title ≤ 80 chars from the list above; don't editorialize in it (HN guidelines).
- [ ] Be present in the thread for the first 2–3 hours; answer the prior-art and why-not-Python comments personally and fast — the author showing up is half of what makes Show HN threads go well.
- [ ] Have the `spl3 cache show <key>` prose↔statement output ready to paste when someone asks "what does machine_proved actually look like."
- [ ] Expect and welcome "this is just X" comments; the v0.2 sections are written so you can answer each with a link to the exact paragraph rather than a rebuttal.
