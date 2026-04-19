# Consolidation Plan: SPL 1.0 + SPL 2.0 + SPL 3.0 → SPL.py

**Date:** 2026-04-19  
**Goal:** Merge three development repos into a single public repo (`SPL.py`), with SPL30 continuing as the POC/prototyping sandbox.

---

## Repo Inventory (core source only, excluding cookbook and docs)

### SPL 1.0 — `/home/papagame/projects/digital-duck/SPL`
- Package: `spl-llm` v0.1.1, CLI: `spl`
- Source package: `spl/`
- Modules: `lexer`, `parser`, `ast_nodes`, `executor`, `cli`, `analyzer`, `optimizer`, `explain`, `functions`, `token_counter`, `tokens`
- Adapters (5): `base`, `claude_cli`, `cloud_direct`, `ollama`, `openrouter`
- Storage: `chroma`, `memory`, `vector`

### SPL 2.0 — `/home/papagame/projects/digital-duck/SPL20`
- Package: `spl-llm` v2.0.0, CLI: `spl`
- Source package: `spl/` (same namespace, strict superset of 1.0)
- New modules over 1.0: `code_rag`, `config`, `ir`, `stdlib`, `text2spl`, `tools`
- Adapters (14): adds `anthropic`, `azure_openai`, `bedrock`, `dd_llm_bridge`, `deepseek`, `echo`, `google`, `momagrid`, `openai`, `qwen`, `vertex`
- Storage: adds `storage_conn`
- UI: full Streamlit app (`Text2SPL`, `Review`, `Code RAG`, `SPLc`, `Target Review`)

### SPL 3.0 — `/home/papagame/projects/digital-duck/SPL30`
- Package: `spl` v3.0.0-alpha, CLI: `spl3`, depends on `spl-llm>=2.0.0`
- Source package: `spl3/` — **extends SPL 2.0 via inheritance** (`from spl.xxx`)
- New modules: `composer`, `event`, `hub_registry`, `peer`, `registry`, `_loader`, `status`, `types`
- AST extensions: `ImportStatement`, `NoneLiteral`, `SetLiteral`, `CallParallelStatement`
- Parser/Executor: `SPL3Parser(SPL2Parser)`, `SPL3Executor(SPL2Executor)`
- New adapters: `base_multimodal`, `liquid`, `snap`; also has `dd_llm_bridge` (overlap with SPL20)
- Codecs: `audio_codec`, `image_codec`, `video_codec`
- RAG: `rag/index_recipes`, `rag/search` (refactored from flat `code_rag.py`)
- Compiler: `splc/transpiler_go`, `splc/transpiler_ts`, `splc/transpiler_langgraph`
- `text2spl` promoted to subpackage `spl3/text2spl/`
- UI: same Streamlit pages as SPL20 (SPL30's version is current)

---

## Key Findings

1. **SPL 1.0 is fully superseded by SPL 2.0.** All SPL 1.0 modules exist in SPL 2.0 in evolved form. Nothing unique to port.

2. **The SPL 2.0 → SPL 3.0 extension is architecturally clean.** `spl3/` imports `from spl.xxx`, so the two-package layout (`spl/` + `spl3/`) should be preserved verbatim in SPL.py — no merging of the layers.

3. **Two conflicts to resolve:**
   - `dd_llm_bridge.py` exists in both `spl/adapters/` (SPL20) and `spl3/adapters/` (SPL30) — check for divergence, deduplicate.
   - `text2spl` is a flat file in SPL20 (`spl/text2spl.py`) but a subpackage in SPL30 (`spl3/text2spl/`). SPL30 version takes precedence (it extends SPL20's).

4. **Streamlit UI** exists in both repos with identical page structure — take SPL30's version (it is the current one).

---

## Target Structure for SPL.py

```
SPL.py/
  spl/              ← verbatim from SPL20/spl/ (SPL 2.0 runtime)
  spl3/             ← verbatim from SPL30/spl3/ (SPL 3.0 extension layer)
  tests/            ← merged (SPL20: 10 test files, SPL30: 5 test files)
  pyproject.toml    ← unified; entry points: spl (cli:main) + spl3 (cli:main)
  LICENSE
  README.md
```

---

## Implementation Phases

| Phase | Work | Effort |
|---|---|---|
| 1 | Repo init: copy `spl/` from SPL20, `spl3/` from SPL30 | 0.5 day |
| 2 | Unified `pyproject.toml` with both entry points and merged deps, `spl3` as the single command | 0.5 day |
| 3 | Resolve `dd_llm_bridge` duplication across `spl/` and `spl3/` | 0.5 day |
| 4 | Merge test suites, fix import paths, verify all tests pass | 1–2 days |
| 5 | Streamlit UI: confirm SPL30's version is current, copy to `spl3/ui/` | 0.5 day |

**Total: ~3–4 days**

The main risk is Phase 4 — import path assumptions may differ between repos and need adjustment after merging.

---

## Future Workflow: SPL.py as Public Repo + SPL30 as POC Sandbox

### Role of each repo

| Repo | Role | Who touches it |
|---|---|---|
| **SPL.py** | Stable public release. Consumers install from here. PyPI releases cut here. | Graduated, tested features only |
| **SPL30** | POC and prototyping sandbox. New language features, experimental adapters, multimodal work. | Active development, breaking changes OK |

### Migration gate (SPL30 → SPL.py)

A feature graduates from SPL30 to SPL.py when it meets **all three**:

1. **Test coverage** — a unit test or pipeline `.test.yaml` covers the feature.
2. **Cookbook recipe** — at least one `.spl` recipe demonstrates real usage.
3. **No API breakage** — the `spl/` (SPL 2.0) public API is unchanged, and `spl3/` public interfaces are backwards-compatible.

Graduation is a **copy**, not a merge — because the extension contract (see below) keeps layers independent.

### What stays in SPL30

- Experimental adapters (`liquid`, `snap`) until they stabilise
- New multimodal codec experiments
- Draft transpiler targets (`splc/` for new languages)
- In-progress cookbook recipes
- Any `spl<n>/` layer under active development before it is ready for release

### Extension contract: additive layers via `spl<n>`

When a major version bump is needed, the pattern scales by adding a new numbered subpackage in SPL30 first:

```
spl/    ← SPL 2.0 runtime (base, lives in SPL.py)
spl3/   ← extends spl/  via inheritance  (current, lives in SPL.py)
spl4/   ← extends spl3/ via inheritance  (future, prototype in SPL30 first)
spl5/   ← extends spl4/ via inheritance  (further future)
```

Each layer follows the same rules:

- New package `spl<n>/` created in SPL30
- `from spl<n-1>.xxx import BaseClass`, then subclass it — **never import sideways within the same layer**
- **CLI entry point stays `spl3` permanently** — no `spl4`, `spl5` commands. The binary name is a stable user-facing contract; internal versioning is expressed through the package layer, not the command name.
- When stable and gate-checked, copy `spl<n>/` into SPL.py alongside the existing layers; update `spl3/cli.py` to import from the new layer's executor/parser (see CLI architecture below).

The `[tool.setuptools.packages.find]` glob `include = ["spl*"]` in `pyproject.toml` already covers any future `spl4`, `spl5`, etc. — no build config change needed when graduating.

### CLI architecture: `spl3` as permanent stable entry point

Two CLI files exist in the repo — they serve different purposes:

| File | Role |
|---|---|
| `spl/cli.py` | SPL 2.0's own CLI — **internal, not exposed as a command**. The `spl` binary was dropped. |
| `spl3/cli.py` | **The one permanent user-facing entry point.** Wired as `spl3 = "spl3.cli:main"` in `pyproject.toml`. Never changes its address. |

When a new layer `spl<n>/` graduates to SPL.py, `pyproject.toml` is **not touched**. Instead, `spl3/cli.py` is updated to import from `spl<n>/` — it acts as a thin stable dispatcher that always delegates to the highest available layer:

```
# today (spl3 is the top layer)
spl3/cli.py  →  SPL3Executor, SPL3Parser  (from spl3/)

# after spl4 graduates
spl3/cli.py  →  SPL4Executor, SPL4Parser  (from spl4/, which extends spl3/)

# after spl5 graduates
spl3/cli.py  →  SPL5Executor, SPL5Parser  (from spl5/, which extends spl4/)
```

The user always runs `spl3 run ...` and gets the latest runtime transparently. The entry point address in `pyproject.toml` (`spl3.cli:main`) never changes.

### Risks to watch

- **Import drift:** If `spl<n>/` starts importing from its own namespace (`spl<n>.xxx`) instead of the layer below (`spl<n-1>.xxx`), graduation becomes a refactor instead of a copy. Keep imports strictly upward — always from the layer below, never sideways.
- **Version skew:** SPL.py's `spl/` and SPL30's assumed `spl-llm` version must stay in sync. SPL30's `pyproject.toml` should pin a concrete minimum (e.g. `spl-llm>=2.0.0`) and that minimum should be bumped whenever SPL.py cuts a release that changes the `spl/` API.
- **Test debt:** SPL30 tests with wrong import paths (`from spl.xxx` for `spl3`-specific symbols) silently fail collection and give false confidence. New tests in SPL30 must import from the correct `spl<n>.xxx` namespace from day one.
