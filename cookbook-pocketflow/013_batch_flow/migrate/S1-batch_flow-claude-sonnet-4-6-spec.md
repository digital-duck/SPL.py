## Summary

This workflow batch-processes a fixed set of images by applying multiple visual filters (grayscale, blur, sepia) to each image in turn. It demonstrates how a single-image processing pipeline can be wrapped in a batch loop to handle a Cartesian product of inputs and transforms without duplicating logic. The primary beneficiary is a developer learning how PocketFlow's `BatchFlow` abstraction maps to SPL's iteration and sub-workflow composition patterns.

---

## Detailed Specification

### 1. Purpose

Run a deterministic image-filter pipeline over every combination of three images and three filter types, writing each result to an `output/` directory.

---

### 2. High-level Description

The implementation is structured as two nested workflows: an inner single-image WORKFLOW (`base_flow`) composed of three sequential tool-call steps — load, transform, save — and an outer BatchFlow WORKFLOW that generates a parameter list (nine image × filter pairs) and drives the inner workflow once per pair.

The inner WORKFLOW contains three CALL steps. The first CALL (`LoadImage`) reads a JPEG from `images/` using PIL and deposits the result into shared state (`@image`). The second CALL (`ApplyFilter`) reads `@image` and a `filter` parameter, branches on the filter name to apply one of three PIL transforms, and writes the result into `@filtered_image`. The third CALL (`SaveImage`) constructs an output filename from the image stem and filter name, saves to `output/`, and prints a confirmation. No LLM calls are made anywhere in this pipeline; all steps are deterministic tool operations.

The outer WORKFLOW implements batch dispatch: its `prep` phase produces the full Cartesian product of images × filters as a list of parameter dicts, and BatchFlow iterates over that list, running the inner WORKFLOW once per dict. The `@image` and `@filtered_image` variables in shared state are scoped to each inner run and do not leak across iterations.

There is no WHILE loop, no EVALUATE branch, and no EXCEPTION handler in the current implementation; the filter dispatch in `ApplyFilter` raises a plain `ValueError` for unknown filter names, which propagates as an unhandled exception.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW base_flow` | `create_base_flow()` → `Flow(start=load)` | Inner single-image pipeline |
| `WORKFLOW batch_flow` | `ImageBatchFlow(start=base_flow)` | Outer batch driver; iterates over param list |
| `CREATE FUNCTION load_image` | `LoadImage.exec()` | Pure PIL `Image.open`; no prompt |
| `CREATE FUNCTION apply_filter` | `ApplyFilter.exec()` | Filter dispatch via `if/elif`; no prompt |
| `CREATE FUNCTION save_image` | `SaveImage.exec()` | PIL `image.save`; returns output path |
| `CALL load_image(...) INTO @image` | `LoadImage.post` → `shared["image"] = exec_res` | Side-effect: reads from `images/` |
| `CALL apply_filter(...) INTO @filtered_image` | `ApplyFilter.post` → `shared["filtered_image"] = exec_res` | Pure transform, no I/O |
| `CALL save_image(...) INTO @result` | `SaveImage.exec` → `image.save(output_path)` | Side-effect: writes to `output/` |
| `@image`, `@filtered_image` | `shared["image"]`, `shared["filtered_image"]` | Shared store scoped per batch iteration |
| Batch iteration (implicit loop) | `BatchFlow.prep` returns param list; framework loops | SPL has no native `BATCH`; model as `WHILE params DO CALL base_flow END` |
| `EXCEPTION WHEN ValueError THEN` | `raise ValueError(f"Unknown filter: {filter_type}")` | Not handled in current code; should be added |

---

### 4. Logical Functions / Prompts

**`load_image`**
- Role: Fetch raw image data from disk into shared state before any transformation.
- Key conventions: Accepts `input` param (filename stem); resolves path relative to `images/`; returns PIL `Image` object.

**`apply_filter`**
- Role: Apply a named visual transform to the in-memory image.
- Key conventions: Reads `filter` param; supports `"grayscale"` (convert to L mode), `"blur"` (PIL `BLUR` kernel), `"sepia"` (desaturate + brightness lift). Unknown filter names raise `ValueError`. No sentinel tokens or scoring — purely deterministic.

**`save_image`**
- Role: Persist the transformed image to disk and report the output path.
- Key conventions: Constructs filename as `{stem}_{filter}.jpg`; creates `output/` if absent; prints confirmation to stdout. Return value (the saved path) is available for downstream logging.

---

### 5. Control Flow

```
BatchFlow.prep
  → produces 9 param dicts (3 images × 3 filters)
  → implicit loop over param list:
      For each {input, filter}:
          CALL load_image(input)   INTO @image
          CALL apply_filter(filter, @image) INTO @filtered_image
          CALL save_image(input, filter, @filtered_image) INTO @result
```

There is no WHILE condition, no EVALUATE branch, and no non-trivial RETURN status. The batch terminates when all nine parameter sets are exhausted. Any `ValueError` from an unknown filter name is unhandled and will abort the entire batch run.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Run a deterministic image-filter pipeline over every combination \
of three images and three filter types, writing each result to an output/ directory. \
The workflow has an inner single-image WORKFLOW with three CALL steps (load from disk, \
apply a named filter, save to output/), and an outer batch loop that generates the \
Cartesian product of images × filters and runs the inner workflow once per pair." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile batch_image_filter.spl --lang python/pocketflow
spl3 splc compile batch_image_filter.spl --lang python/langgraph
spl3 splc compile batch_image_filter.spl --lang go
```