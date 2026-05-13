# Intent Engineering & Vibescope
### A Vision for Deterministic Agentic Software Development

*Synthesized from: Gemini brainstorming session (2026-05-12), Claude review (2026-05-11), and `intent-eng` implementation session (2026-05-13).*

---

## The First Principle

In physics, **energy is a conserved quantity**. The form it takes — kinetic, thermal, electromagnetic, chemical — varies continuously and depends entirely on the coordinate system (the substrate). But the total is invariant. This is not a convention or a design choice. It is the deepest truth we know about the physical world.

**Intent Engineering begins with the same claim applied to software:**

> *Human intent is a conserved quantity in the agentic SDLC.*

The form it takes — natural language, a Mermaid diagram, an SPL specification, a Python class, a Go struct, a TypeScript module — varies with the coordinate system (the target runtime). But the underlying intent must be invariant. When it is not, the system has failed — regardless of whether the code runs.

The `.spl` file is the invariant. Everything else is a projection.

This reframes the entire problem of "vibe coding." The question is not *"did the LLM generate good code?"* The question is *"is the generated code the same program you intended to write?"* Those are different questions, and only the second one is scientifically answerable.

---

## The Problem: The Intent Gap

"Vibe coding" — direct synthesis of software from natural language via LLM — delivers unprecedented velocity. It also introduces a new class of failure: **stochastic drift**.

The LLM is a probabilistic machine. At every transformation step, there is a probability distribution over possible outputs. Most outputs are close to the intent. Some are not. And the developer has no instrument to tell the difference — no conservation law to check, no measurement apparatus, no meter reading.

This is the **Intent Gap**: the unbounded stochastic drift between human requirement and machine execution, invisible to the developer because no reference representation was ever defined.

The verifiable intermediate state is the `.spl` file. The instrument that measures the gap is **Vibescope**.

---

## Vibescope: The Measurement Instrument

**Vibescope** is the metrology layer of Intent Engineering. Its single purpose is to **measure the split between the deterministic and probabilistic components of an agentic workflow**.

Every agentic workflow has two fundamentally different kinds of content:

| Component | Nature | Example |
|---|---|---|
| **Structure** (Bones) | Deterministic | Which nodes exist, how they connect, what the control flow is |
| **Semantics** (Skin) | Probabilistic | What the LLM generates inside each node — prompts, reasoning, outputs |

Structure can be extracted deterministically, without an LLM, by loading the code and walking the graph (`rt-inspect`). Semantics require stochastic inference and cannot be determinized.

The vibescope reading has two channels:

```
Vibescope Reading = { Structural Fidelity (GED),  Semantic Fidelity (LLM score) }
```

- **Structural channel** — Graph Edit Distance between the SPL topology and the rt-inspect topology of the compiled implementation. Zero hallucination, zero LLM cost, computed in milliseconds.
- **Semantic channel** — LLM judge comparison between the SPL specification and the reverse-extracted specification from the implementation.

The **Intent Invariance Score** is the vibescope's needle: `(1 − normalized_GED) × 10`, ranging from 0 (complete structural mismatch) to 10 (perfect structural fidelity). A score above 8 means the implementation's topology matches the design. Below 6 means significant structural drift — the LLM rewired the graph.

---

## The Conservation Law, Formalized

$$\Delta S = T^{-1}(T(I)) - I \approx 0$$

Where:
- $I$ — the original Intent (the `.spl` file, the conserved quantity)
- $T$ — the transformation manifold (SPL → compiled code)
- $T^{-1}$ — the reverse extraction (rt-inspect → topology → spec reconstruction)
- $\Delta S$ — the Intent Drift (what vibescope measures)

This is the round-trip closure test. The **six measurement modes** of the vibescope correspond to six different norms on $\Delta S$:

| Mode | What it measures | Physics analogy |
|---|---|---|
| **GED (topology)** | Structural graph drift | Topological invariance |
| **AST diff** | Syntactic implementation drift | Molecular structure |
| **Vector similarity** | Semantic manifold distance | Displacement in meaning space |
| **LLM judge** | Reasoning and contextual alignment | Observer-level comparison |
| **Character diff** | Surface syntax noise | Brownian motion |
| **Functional (pytest)** | Behavioral parity in the physical world | Empirical verification |

All six are implemented in `spl3 compare`. The vibescope is not a metaphor — it is running code.

---

## The Human Role: Topological Supervisor

The physics framing clarifies the human-AI division of labor.

In a particle accelerator, the physicist does not control individual particle trajectories. They set the boundary conditions (the fields, the geometry, the conservation laws) and measure what comes out. The detector — the vibescope — tells them whether the physics was right.

In Intent Engineering:

- The **human** is the **Topological Supervisor**: defines the conserved quantity (the `.spl` spec, the Mermaid topology), approves the design at Gate 1, and reads the vibescope at Gate 4.
- The **LLM** is the **Transformation Engine**: projects the intent into code, but does not define the intent and cannot verify that it preserved it.
- The **SPL pipeline** is the **measurement apparatus**: deterministic instruments (spl2mmd, rt-inspect, GED) that operate without LLM involvement wherever possible.

The human governs the bones. The AI generates the skin.

---

## The 5-Gate SDLC

| Gate | Name | Instrument | Nature |
|---|---|---|---|
| **1** | Conceptual Audit | `spl3 text2mmd` → Mermaid review | Human approves the topology |
| **2** | Intent Crystallization | `spl3 text2spl` → `.spl` | Intent becomes the conserved form |
| **3** | Synthesis | `spl3 splc compile` → code | Stochastic projection to target runtime |
| **4** | Vibescope Reading | `spl3 pipeline` → GED + score | Deterministic structural fidelity check |
| **5** | Gauge Test | `spl3 pipeline --target go` | Same intent, different coordinate system |

Gate 5 is the gauge invariance test: if the same `.spl` compiles to Python AND Go with Intent Invariance Score > 8 in both, the intent is substrate-independent. The program is not *a Python program that happens to work* — it is a *logical structure instantiated in different coordinate systems*.

---

## The Vibescope Diagnostic Matrix

|  | **High Structural Fidelity** (score ≥ 8) | **Low Structural Fidelity** (score < 6) |
|---|---|---|
| **High Semantic Fidelity** (LLM ≥ 7) | ✅ Intent fully conserved | ⚠ Topology drifted, meaning preserved — structural refactor occurred |
| **Low Semantic Fidelity** (LLM < 7) | ⚠ Structure preserved, meaning drifted — semantic hallucination | ❌ Complete intent failure — recompile from SPL |

---

## The Intent Ledger

Code is a living fossil. It evolves. But today's version control tracks *text mutations*, not *intent mutations*. A refactor that preserves topology but rewrites every function body looks identical to one that completely rewires the graph — both are a wall of `git diff`.

**Intent-versioning driven by vibescope readings:**

- **Intent-Patch** `v1.0.0 → v1.0.1`: GED = 0. Pure surface refactor; topology preserved. `spl3 diff` shows identical node/edge sets.
- **Intent-Minor** `v1.0 → v1.1`: GED small, score > 8. Structural extension (new node or edge added). `spl3 diff` shows additions only.
- **Intent-Major** `v1 → v2`: Score < 8. Topological drift — the intent itself evolved. Requires human Gate 1 review before recompiling.

`spl3 diff` is a semantic changelog, not a text changelog.

---

## What the SPL Stack Already Implements

The framework is not aspirational. It is running today.

| Framework concept | SPL implementation |
|---|---|
| Conserved Intent representation | `.spl` file (DODA principle) |
| Gate 1 — Conceptual Audit | Streamlit pages 0 (Text2Mermaid) + 2 (Review) |
| Gate 2 — Intent Crystallization | `spl3 text2spl` |
| Gate 3 — Synthesis | `spl3 splc compile` → Python / Go / TS / LangGraph |
| Gate 4 — Vibescope | `spl3 pipeline` (rt-inspect + GED + score bar) |
| Gate 5 — Gauge Test | `spl3 pipeline --target go` / `--target python_langgraph` |
| 6-mode spectroscope | `spl3 compare --mode ged/llm/vector/git-diff/ast/vision` |
| Structural diff | `spl3 diff` (node/edge semantic diff, Mermaid output) |
| Fixture coverage | `spl3 test --list`, `spl3 validate --check-coverage` |
| Intent Ledger (partial) | `spl3 diff --format json` → machine-readable delta |
| Full UI surface | `spl3-ui` → 10-page Streamlit Knowledge Studio |

---

## Verified Literature

*(Verified 2026-05-11. Hallucinated references from the original Gemini session are excluded.)*

**YouTube — Intent Engineering vs Context Engineering (Feb 2026)**
[Intent Engineering vs Context Engineering | Which Actually Works?](https://www.youtube.com/watch?v=jia2IcIuhCM)

**Pathmode — Intent Engineering as a discipline (2025–2026)**
"Prompts disappear after the session; specs must be persistent, structured, and versioned." — closest external match to the SPL DODA principle.
- [Intent Engineering: How to Brief AI Agents Without Guessing](https://pathmode.io/glossary/intent-engineering)
- [The Next Product Discipline Isn't Context Engineering. It's Intent Engineering.](https://pathmode.io/blog/intent-engineering-vs-context-engineering)

**arXiv:2603.13173 — Semantic Invariance in Agentic AI (March 2026)**
Defines semantic invariance as LLM agent reasoning remaining stable under semantically equivalent input variations. Tested via eight semantic-preserving transformations across seven foundation models.
- [Semantic Invariance in Agentic AI](https://arxiv.org/abs/2603.13173)

**Product Compass — The Intent Engineering Framework for AI Agents (Jan 2026)**
- [The Intent Engineering Framework for AI Agents](https://www.productcompass.pm/p/intent-engineering-framework-for-ai-agents)

**arXiv:2503.10664 — Semantic Wave Functions**
Uses gauge-field framing for LLM meaning representation. Closest academic work to the gauge invariance analogy.
- [Semantic Wave Functions](https://arxiv.org/abs/2503.10664)

---

## The NeurIPS Deliverable

The paper's core contribution is a runnable number:

```bash
spl3 pipeline cookbook/05_self_refine/self_refine.spl
spl3 pipeline cookbook/05_self_refine/self_refine.spl --target python_langgraph
```

R1–R5 ablation recipes × 2 targets × 3 trials = 30 vibescope readings.

- **Trial variance** quantifies LLM stability per recipe type
- **Cross-target delta** (PocketFlow vs LangGraph) quantifies substrate sensitivity
- **Both scores > 8** = empirical proof of intent conservation across runtimes

That table *is* the NeurIPS empirical contribution. The framework, the metrology, the physics framing — all of it is the narrative around the number.

---

## Closing: From Implementation Anxiety to Topological Sovereignty

The developer using vibe coding today operates under **implementation anxiety**: did the LLM preserve the intent, or did it subtly rewire the graph? There is no way to know without reading every line.

Intent Engineering with vibescope measurement moves the developer to **topological sovereignty**: the design is defined once in the invariant form (`.spl`), the LLM projects it into any runtime, and the vibescope confirms at every step that the projection preserved the intent.

Just as a physicist does not worry that energy will disappear between experiments — the conservation law guarantees it won't — the developer with a vibescope reading of 9.2/10 does not worry that the compiled code is a different program. The measurement says it isn't.

**The `.spl` file is the conserved quantity.
The vibescope is the instrument that proves it.**

---

*不见不散 — See you at the finish line.*
