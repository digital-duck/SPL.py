# Implementation: Expanded `spl3 compare`

Following the brainstorming session, `spl3 compare` has been refactored to support a multi-mode "Physics Lens" for measuring **Intent Entropy** ($\Delta S$). It moves beyond qualitative LLM scoring to provide deterministic, quantitative metrics.

## Refactored Architecture

The command now supports an extensible `--mode` architecture. You can run one or more modes simultaneously to generate a consolidated report.

```bash
spl3 compare file1 file2 --mode llm --mode vector --mode bert-score --mode ged --mode git-diff
```

### 1. LLM Semantic Analysis (`--mode llm`)
*   **Metric**: Qualitative scoring (1-10) across Structure, Logic, Quality, and Syntax.
*   **Physics Interpretation**: High-level semantic reasoning by a frontier model (Judge).
*   **Implementation**: Uses `_COMPARE_PROMPT` to generate a structured Markdown report.

### 2. Vector Similarity (`--mode vector`)
*   **Metric**: Cosine Similarity ($\cos \theta$) of file embeddings.
*   **Physics Interpretation**: Angular distance between "Intent Vectors" on the semantic manifold.
*   **Implementation**: Uses `dd-embed` to generate embeddings and `numpy` for dot-product normalization.
*   **Config**: Controlled via `--adapter-embed` and `--model-embed`.

### 3. BERTScore (`--mode bert-score`)
*   **Metric**: Precision, Recall, and F1 score based on contextual alignment.
*   **Physics Interpretation**: Measures semantic overlap and paraphrasing robustness.
*   **Implementation**: Uses the `bert-score` library (forced to CPU for stability).

### 4. Graph Edit Distance (`--mode ged`)
*   **Metric**: Minimum operations to transform Topology A into Topology B.
*   **Physics Interpretation**: Topological Entropy. A GED of 0.0 indicates perfect structural symmetry.
*   **Implementation**: Optimized for Mermaid (`.mmd`) files. Uses `networkx` to parse visual syntax into directed graphs and calculates edit distance using `scipy`.

### 5. Git Diff (`--mode git-diff`)
*   **Metric**: Line-by-line character difference.
*   **Physics Interpretation**: Syntactic variance/Mechanical drift.
*   **Implementation**: Reuses `difflib` with support for `unified`, `context`, and `side-by-side` styles.

## New Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--mode` | `llm` | Enable specific metrics (can be repeated) |
| `--adapter-embed` | `ollama` | Adapter for vector/bert-score modes |
| `--model-embed` | `nomic-embed-text` | Model for embedding calculations |
| `--prompt` | `False` | Debug flag to inspect comparison prompt |

## Reporting

Results are consolidated into a single report, available in:
*   **Markdown**: Professional report with tables and diff blocks.
*   **JSON**: Machine-readable metrics for automated ablation analysis.
*   **Text**: Minimalist console output.
