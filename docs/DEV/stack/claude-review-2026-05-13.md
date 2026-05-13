# SPL Stack Review — 2026-05-13

*Reviewed by Claude Sonnet 4.6 during the `intent-eng` development session.*

---

## 1. Current Stack Inventory

| Layer | CLI Command | Description |
|---|---|---|
| **Design** | `spl3 text2spl` | NL description → SPL 3.0 source |
| | `spl3 text2mmd` | NL description → Mermaid (pre-SPL review) |
| | `spl3 mmd2spl` | Mermaid flowchart → SPL |
| | `spl3 img2mmd` | Image → Mermaid (multimodal OCR) |
| | `spl3 img2text` | Image → pseudo-code / text |
| **Visualize** | `spl3 spl2mmd` | SPL → Mermaid + PNG/SVG/PDF (AST-direct, no LLM) |
| **Compile** | `spl3 splc compile` | SPL → Python/PocketFlow, Go, TypeScript, LangGraph |
| | `spl3 splc describe` | SPL or .py → plain-English spec (forward or reverse) |
| **Inspect** | `spl3 splc describe --mode rt-inspect` | Deterministic PocketFlow graph topology extraction |
| | `spl3 json2mmd` | rt-inspect topology JSON → Mermaid |
| **Compare** | `spl3 compare --mode ged` | Graph Edit Distance between two Mermaid/topology inputs |
| | `spl3 compare --mode llm` | LLM semantic comparison of two specs |
| | `spl3 compare --mode vector` | Embedding cosine similarity |
| | `spl3 compare --mode git-diff` | Raw text diff |
| **Validate** | `spl3 validate` | Fast syntax-only parse check (no LLM) |
| | `spl3 explain` | Show execution plan without running |
| **Execute** | `spl3 run` | Run orchestrator .spl workflow |
| | `spl3 test` | LLM-executed end-to-end test against .test.yaml fixtures |
| **Knowledge** | `spl3 code-rag` | Code-RAG index management for Text2SPL |
| | `spl3 registry` | Workflow registry (local + Hub) |
| | `spl3 peers` | Hub-to-Hub peering |
| **UI** | `spl3 ui` / `spl3-ui` | Launch Streamlit Knowledge Studio |
| **Utility** | `spl3 show` | List adapters, models, stdlib tools |
| | `spl3 vibe` | NL → working code + README in one pass (no IR) |

### Streamlit Pages
| Page | Description |
|---|---|
| 0 — Text2Mermaid | NL → Mermaid flowchart |
| 1 — Text2SPL | NL → SPL source with review |
| 2 — Review | SPL spec review and editing |
| 3 — Code RAG | Code-RAG index management |
| 4 — SPLc | Compile SPL to target code |
| 5 — Target Review | Review compiled implementation |
| 6 — NeurIPS Lab | R1–R5 ablation experiment runner |
| 7 — Ablation Results | Results visualization |
| 8 — RT-Inspect | Deterministic topology extraction + GED comparison |
| 9 — Compare *(new)* | Multi-tier compare: GED + LLM + vector in one view |

---

## 2. What Is Working Well

**Intent Engineering pipeline is coherent.** The NL→SPL→Mermaid→Compile→rt-inspect→GED chain now exists end-to-end across CLI commands. The core claim of the NeurIPS paper — that topology fidelity between design (SPL Mermaid) and implementation (PocketFlow graph) can be measured deterministically — is fully implemented and testable.

**AST-direct `spl2mmd` is fast and reliable.** No LLM, no hallucination risk in diagram generation. The edge-label escaping fix (removing bracket chars from `|..|` labels) makes the output robust across Mermaid versions.

**Multi-format diagram export.** PNG (raster), SVG (vector, unlimited zoom), PDF (print) are all working via `mmdc` with proper `--no-sandbox` for Linux. The HTML no longer embeds fragile inline Mermaid — it references the static PNG.

**Adapter abstraction.** The `dd-llm` adapter layer makes it straightforward to swap OpenAI / Anthropic / Ollama without changing SPL source.

---

## 3. Identified Gaps

### G1 — No end-to-end pipeline command *(HIGH — needed for NeurIPS ablation)*

Running one ablation recipe requires 4+ separate CLI commands:
```
spl3 spl2mmd recipe.spl --no-preview
spl3 splc compile recipe.spl --target python_pocketflow
spl3 splc describe targets/python_pocketflow/recipe.py --mode rt-inspect
spl3 compare --mode ged recipe.mmd targets/python_pocketflow/recipe-topology.json
```
A `spl3 pipeline <recipe.spl>` command that runs all Intent Engineering gates in sequence and prints a single gate summary table would eliminate friction in the R1–R5 test sprint.

**Status:** Implemented in this session (`spl3 pipeline`).

---

### G2 — Fixture coverage visibility *(MEDIUM — needed before test sprint)*

No way to quickly see which `.spl` files in the cookbook have corresponding `.test.yaml` fixtures. Running `spl3 test` on a file without a fixture gives a confusing error. A `spl3 test --list` and `spl3 validate --check-coverage` that shows ✓/✗ per file would make the test sprint planning clear.

**Status:** Implemented (`spl3 test --list`, `spl3 validate --check-coverage`).

---

### G3 — rt-inspect covers Python/PocketFlow only *(LOW-MEDIUM — future work)*

`spl3 splc compile` generates Go, TypeScript, and LangGraph targets, but `rt-inspect` loads a Python module and walks `node.successors`. There is no equivalent for:
- **Go**: would require parsing the Go AST or using `go/ast`
- **TypeScript**: would require a TS AST parser (e.g., `ts-morph`)
- **LangGraph**: different graph API (`StateGraph.add_node`, `add_edge`)

For NeurIPS ablation (R1–R5), all target implementations are Python/PocketFlow, so this is not a blocker. The gap is documented and the CLI gives a clear error for non-`.py` inputs.

**Recommended future approach:** Per-target inspector plugins — a `rt_inspect_langgraph.py`, `rt_inspect_go.py` registered by target name.

---

### G4 — No semantic SPL diff *(MEDIUM — useful for iterative refinement)*

When SPL is revised iteratively (e.g., `self_refine.spl` vs `self_refine-product_gen.spl`), there is no way to compare them at the workflow level — which nodes were added, removed, or rewired — without reading both files manually. `spl3 diff` parses both files to AST, converts to Mermaid graphs, and shows a node/edge delta table plus GED score.

**Status:** Implemented (`spl3 diff`).

---

### G5 — Streamlit UI has no Compare page *(MEDIUM — important for demo)*

Pages 0–8 cover design/compile/inspect but the GED + Intent Invariance comparison that is central to the NeurIPS paper argument has no UI surface. Non-CLI users (reviewers, collaborators) can't run comparisons. Page 9 — Compare — wires `spl3 compare` GED + LLM tiers into the Streamlit UI.

**Status:** Implemented (`9_🔬_Compare.py`).

---

### G6 — `spl3-ui --page` flag was cosmetic only *(LOW — UX polish)*

The `--page` option accepted a value but only printed a tip message; Streamlit doesn't support URL-based page navigation at launch via CLI. Fixed by:
1. Passing the page name/number as a `?page=` URL fragment in the `--browser` open call
2. Reading `st.query_params` in `SPL_UI.py` to highlight the target page in the sidebar

**Status:** Implemented.

---

## 4. Architecture Notes

### Intent Engineering Gate Model
```
Gate 0  NL description
Gate 1  SPL source (spl3 text2spl / spl3 mmd2spl)
Gate 1b Mermaid review (spl3 spl2mmd → PNG/SVG/PDF)
Gate 2  Compiled implementation (spl3 splc compile)
Gate 3  Runtime topology (spl3 splc describe --mode rt-inspect)
Gate 4  Intent Invariance score (spl3 compare --mode ged)
```
The pipeline command (G1) automates Gates 1b → 2 → 3 → 4 for a given `.spl` file.

### Canonicalization is critical for GED accuracy
PocketFlow class names (`DraftNode`, `CritiqueNode`) must be normalized to SPL node labels (`draft`, `critique`) before GED comparison. The `canonicalize_node_id()` function in `spl3/splc/rt_inspect.py` handles this. Without it, every node appears as a substitution, inflating GED artificially.

### Edge label escaping in Mermaid
Mermaid's flowchart parser treats `(`, `[`, `{` inside `|edge-label|` as node-shape delimiters. The `_mmd_edge_label()` function in `spl3/spl2mmd.py` strips all bracket/paren chars from edge labels. This was the root cause of the "Syntax error in text" error in `self_refine.html`.

---

## 5. Recommended Next Steps (Post-Test Sprint)

1. **G3 extension** — LangGraph rt-inspect (`StateGraph.compile()` + graph introspection via `graph.nodes`, `graph.edges`)
2. **Batch pipeline** — `spl3 pipeline --all cookbook/` to run all R1–R5 recipes and produce a summary CSV for the NeurIPS ablation table
3. **CI integration** — GitHub Actions step that runs `spl3 pipeline` on PR and posts the Intent Invariance score as a PR comment
4. **`spl3 test` fixture generator** — `spl3 test --generate <file.spl>` to scaffold a `.test.yaml` from the SPL spec using the LLM
5. **Memory/persistence integration** — `spl3/memory` SQLite/PostgreSQL layer is built; wire it into `spl3 run` so execution history is queryable via `spl3 history`



 Good night! Great session today — a lot got built and written.                                                            
                                                                                                                            
  Quick summary of what's ready on intent-eng for when you come back to test:                                               
   
  - spl3 pipeline — the one-command vibescope run                                                                           
  - spl3 diff — semantic SPL diff                                                                                         
  - spl3 ui / spl3-ui — Streamlit launcher                                                                                  
  - spl3 test --list / spl3 validate --check-coverage — fixture planning                                                    
  - --save-svg, --save-pdf --paper letter on spl3 spl2mmd                                                                   
  - Streamlit pages 8 (RT-Inspect) and 9 (Compare)                                                                          
  - docs/DEV/intent-engineering.md — the Vibescope vision document                                                          
                                                                                                                            
  Rest well. 不见不散.                     