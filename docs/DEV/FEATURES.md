# SPL Feature Log

Tracks significant features added to the `intent-eng` branch.
Each entry records the date, branch, CLI surface, and files changed.

---

## 2026-05-13  `intent-eng`

### 1. `spl3 splc describe --mode rt-inspect` — Deterministic Topology Extraction

**What it does:**
Loads a compiled Python/PocketFlow file via `importlib`, finds the `Flow` object, traverses `node.successors` via BFS, and returns a canonical JSON topology — no LLM required, zero hallucination risk.

**Why it matters:**
Separates *Syntactic drift* (topology mismatch) from *Semantic drift* (prompt/logic mismatch). Forms Gate 3 of the Intent Engineering pipeline.

**Files:**
- `spl3/splc/rt_inspect.py` *(new)* — `inspect_pocketflow_file()`, `canonicalize_node_id()`, `topology_to_mermaid()`
- `spl3/splc/cli.py` — `--mode [llm|rt-inspect]` added to `splc describe`

**Usage:**
```bash
spl3 splc describe targets/python_pocketflow/self_refine.py --mode rt-inspect
spl3 splc describe targets/python_pocketflow/self_refine.py --mode rt-inspect --json
```

**Notes:**
- Auto-mocks third-party imports iteratively (duckduckgo_search, openai, etc.) so the graph-wiring code loads even without installed LLM clients
- Only supports Python/PocketFlow (`.py`); `.go` / `.ts` give a `NotImplementedError` with a clear message and roadmap hint
- `canonicalize_node_id()`: strips `Node` suffix and converts CamelCase → snake_case (`DraftNode` → `draft`) — required for accurate GED comparison with SPL Mermaid

---

### 2. GED Canonicalization — `spl3 compare --mode ged` topology-JSON support

**What it does:**
`compare_ged()` now auto-detects whether each input is a Mermaid string or a rt-inspect topology JSON. JSON inputs are parsed via `parse_topology_json_to_nx()` with canonical node-name normalisation and PocketFlow base-class → SPL node-type mapping.

**Files:**
- `spl3/compare/utils.py` — `parse_topology_json_to_nx()` *(new)*
- `spl3/compare/tiers/ged.py` — `_is_topology_json()` + auto-dispatch

**Usage:**
```bash
spl3 compare --mode ged self_refine.mmd targets/python_pocketflow/self_refine-topology.json
```

---

### 3. `spl3 json2mmd` — Topology JSON → Mermaid

**What it does:**
Converts a rt-inspect topology JSON file to a Mermaid flowchart, with optional `canonicalize_node_id()` normalisation (default on).

**Files:**
- `spl3/cli.py` — `cmd_json2mmd`

**Usage:**
```bash
spl3 json2mmd self_refine-topology.json --stdout
spl3 json2mmd self_refine-topology.json -o self_refine-impl.mmd
spl3 json2mmd self_refine-topology.json --no-canonicalize
```

---

### 4. Streamlit Gate 3 — `8_🔍_RT_Inspect.py`

**What it does:**
Streamlit page for deterministic topology extraction and optional GED Intent Invariance scoring. Three input modes: upload `.py`, enter file path, paste existing JSON. Tabs: Topology Graph (Mermaid CDN), JSON, Mermaid code. Optional GED comparison: paste SPL Mermaid → shows Intent Invariance Score + diagnostic matrix.

**Files:**
- `spl3/ui/streamlit/pages/8_🔍_RT_Inspect.py` *(new)*

---

### 5. `spl3 splc describe` consolidation — `spl3 describe` deprecated

**What it does:**
`spl3 describe` now prints a deprecation notice and delegates to `spl3 splc describe`. `spl3 splc describe` handles both `.spl` inputs (forward direction, uses `_DESCRIBE_PROMPT`) and `.py` inputs with `--mode [llm|rt-inspect]`.

**Files:**
- `spl3/cli.py` — `cmd_describe` deprecated wrapper
- `spl3/splc/cli.py` — `_cmd_describe_spl()`, `_cmd_describe_rt_inspect()`, unified routing

---

### 6. `spl3 --help` truncation fixes

All command first-line descriptions rewritten to fit within 65 chars (Click's display width). Previously several commands showed `...` truncations.

**Fixed commands:** `compare`, `test`, `validate`, `vibe`, `spl2mmd`, `text2mmd`, `img2text`, `splc compile`, `splc describe`

---

### 7. `spl3 spl2mmd` — PNG/SVG/PDF export via `mmdc`

**What it does:**
- `--save-png` (default on): renders via `mmdc` with `--no-sandbox` puppeteer config; HTML now embeds `<img src="*.png">` instead of inline Mermaid — eliminates Mermaid CDN parse errors
- `--save-svg` (new): vector SVG, lossless, ideal for NeurIPS paper figures
- `--save-pdf` (fixed + new `--paper` option): `letter` (US default), `a4`, `a3`, `tabloid`
- PNG is rendered **before** HTML so the HTML always references the static image

**Files:**
- `spl3/cli.py` — `cmd_spl2mmd`, `_mmd_single_html()`, `_save_mmd_formats()`

**Usage:**
```bash
spl3 spl2mmd self_refine.spl --save-svg --save-pdf --paper letter --no-preview
```

---

### 8. Mermaid edge-label escaping fix

**Root cause:**
Mermaid's flowchart parser treats `(`, `[`, `{` inside `|edge-label|` as node-shape delimiters. Labels like `|WHEN contains:(APPROVED)|` caused "Syntax error in text" in Mermaid v11.

**Fix:**
Added `_mmd_edge_label()` in `spl3/spl2mmd.py` that strips all bracket/paren chars `()[]{}` from edge labels. Used by `_edge()` instead of `_mmd_label()`.

**Files:**
- `spl3/spl2mmd.py` — `_mmd_edge_label()` *(new)*, `_edge()` updated

---

### 9. `spl3 ui` / `spl3-ui` — Streamlit launcher

**What it does:**
Launches the Streamlit Knowledge Studio without needing to know the file path. `--page N` passes `?page=N` as a URL query param; `SPL_UI.py` reads `st.query_params["page"]` and shows a sidebar navigation hint.

**Files:**
- `spl3/cli.py` — `cmd_ui`, `_ui_entry`
- `pyproject.toml` — `spl3-ui = "spl3.cli:_ui_entry"` entry point
- `spl3/ui/streamlit/SPL_UI.py` — `_PAGE_MAP`, `st.query_params` block

**Usage:**
```bash
spl3 ui                        # open on :8501
spl3 ui --port 8888 --no-browser   # headless / server
spl3 ui --page 8               # navigate hint to RT-Inspect
spl3-ui --page 9               # standalone, navigate hint to Compare
```

---

### 10. `spl3 pipeline` — End-to-End Intent Engineering Gates

**What it does:**
Runs all four Intent Engineering gates in sequence for a single `.spl` file and prints a gate summary table with Intent Invariance score bar.

```
Gate 1b  spl2mmd      → SPL Mermaid + PNG + SVG
Gate 2   splc compile → target implementation
Gate 3   rt-inspect   → canonical topology JSON
Gate 4   compare ged  → Intent Invariance score
```

**Files:**
- `spl3/cli.py` — `cmd_pipeline`

**Usage:**
```bash
spl3 pipeline self_refine.spl
spl3 pipeline self_refine.spl --target python_langgraph
spl3 pipeline self_refine.spl --no-compile --out-dir targets/python_pocketflow
```

**Example output:**
```
────────────────────────────────────────────────────────────
  SPL Pipeline: self_refine.spl  →  python_pocketflow
────────────────────────────────────────────────────────────
[Gate 1b] spl2mmd …
  ✓ MMD: .../pipeline_out/self_refine.mmd
  ✓ PNG: .../pipeline_out/self_refine.png
[Gate 2] splc compile …
  ✓ impl: .../pipeline_out/python_pocketflow/self_refine.py
[Gate 3] rt-inspect …
  ✓ 8 nodes, 10 edges → .../pipeline_out/self_refine-topology.json
[Gate 4] compare ged …
  ✓ GED=2.0  normalized=0.111  Intent Invariance Score = 8.9/10
────────────────────────────────────────────────────────────
  Intent Invariance Score:   8.9/10  ████████░░
────────────────────────────────────────────────────────────
```

---

### 11. `spl3 diff` — Semantic SPL Diff

**What it does:**
Parses two `.spl` files to Mermaid AST graphs, reports added/removed/kept nodes and edges, and computes Graph Edit Distance between the two versions. Useful for tracking structural changes during iterative SPL refinement.

**Files:**
- `spl3/cli.py` — `cmd_diff`

**Usage:**
```bash
spl3 diff v1.spl v2.spl
spl3 diff v1.spl v2.spl --format json    # machine-readable
spl3 diff v1.spl v2.spl --format mermaid # colour-coded diagram
```

---

### 12. `spl3 test --list` and `spl3 validate --check-coverage`

**What it does:**
Shows which `.spl` files have / lack `.test.yaml` test fixtures. Essential planning tool before a test sprint.

**Files:**
- `spl3/cli.py` — `cmd_test` (`--list` flag), `cmd_validate` (`--check-coverage` + `--dir` flags)

**Usage:**
```bash
spl3 test --list cookbook/              # ✓/✗ coverage per file
spl3 validate --check-coverage --dir cookbook/   # same, exits with missing count
```

---

### 13. Streamlit Compare Page — `9_🔬_Compare.py`

**What it does:**
Streamlit page (Gate 4) for multi-tier Intent Invariance comparison. Inputs: paste Mermaid, load `.spl` file (auto-converted via spl2mmd), paste topology JSON, or load `.py` (auto rt-inspect). Tiers: GED (always), LLM (optional), Vector (optional). Shows Intent Invariance score, GED details, and a 2×2 root-cause diagnostic matrix (GED × LLM score).

**Files:**
- `spl3/ui/streamlit/pages/9_🔬_Compare.py` *(new)*

---

### Summary — Files Changed

| File | Change type |
|---|---|
| `spl3/cli.py` | `json2mmd`, `diff`, `pipeline`, `ui`, `spl2mmd` SVG/PDF/paper, `test --list`, `validate --check-coverage` |
| `spl3/spl2mmd.py` | `_mmd_edge_label()`, edge-label bug fix |
| `spl3/splc/cli.py` | `splc describe` unified routing, SPL/py/rt-inspect modes |
| `spl3/splc/rt_inspect.py` | *(new)* full runtime topology extractor |
| `spl3/compare/utils.py` | `parse_topology_json_to_nx()` |
| `spl3/compare/tiers/ged.py` | `_is_topology_json()`, auto-dispatch |
| `spl3/ui/streamlit/SPL_UI.py` | `st.query_params` page navigation |
| `spl3/ui/streamlit/pages/8_🔍_RT_Inspect.py` | *(new)* Gate 3 Streamlit page |
| `spl3/ui/streamlit/pages/9_🔬_Compare.py` | *(new)* Gate 4 Streamlit page |
| `pyproject.toml` | `spl3-ui` entry point |
| `docs/DEV/stack/claude-review-2026-05-13.md` | *(new)* stack review + gap analysis |
| `cookbook/05_self_refine/self_refine.{mmd,png,svg,pdf,html}` | Regenerated with fixes |
