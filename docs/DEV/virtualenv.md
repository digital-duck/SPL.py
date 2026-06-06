# Development Environment Setup

This document describes how to set up the Python development environment for SPL.py.

## Verified Environment
The project has been verified to pass tests using **Python 3.13** on Linux.

```text
============================ 339 passed, 7 skipped, 10 warnings in 33.95s =============================
```

## Creating the Conda Environment

To create a clean environment specifically for this project:

### 1. Create and Activate
```bash
conda create -n spl3py313 python=3.13
conda activate spl3py313
```

### 2. Install Project Dependencies
Run these commands from the project root directory:

```bash
# Install core and dev dependencies in editable mode
pip install -e ".[dev]"

# Install additional RAG and storage dependencies required for tests
pip install faiss-cpu chromadb sentence-transformers
```

## Notes on Dependencies
- **Editable Install**: `pip install -e .` is required to resolve internal `spl` and `spl3` module references and link the `dd-*` digital-duck ecosystem packages.
- **Storage/RAG**: The vector storage tests depend on `faiss-cpu` and `chromadb`.
- **Embeddings**: `sentence-transformers` is required for the Text2SPL and Code-RAG features.
