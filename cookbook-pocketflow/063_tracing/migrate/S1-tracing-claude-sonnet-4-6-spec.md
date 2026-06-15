## Summary

This cookbook adds production-grade observability to PocketFlow LLM workflows by integrating Langfuse as a tracing backend. A single `@trace_flow()` decorator automatically instruments every node's `prep`, `exec`, and `post` phase — capturing inputs, outputs, timing, and errors — with zero changes to workflow business logic. Data scientists and ML engineers benefit by gaining full visibility into multi-step LLM pipelines without modifying their core workflow code.

---

## Detailed Specification

### 1. Purpose

Provide zero-intrusion, phase-level distributed tracing for PocketFlow LLM workflows by wrapping each flow class with a Langfuse-backed decorator that records inputs, outputs, latency, and exceptions across every node lifecycle phase.

---

### 2. High-level Description

This implementation wraps a PocketFlow `Flow` or `AsyncFlow` class with the `@trace_flow()` decorator, which intercepts the flow's `run()` (or `run_async()`) entry point and emits a top-level Langfuse trace for each execution. Internally the decorator monkey-patches or subclasses each node's `prep`, `exec`, and `post` methods, turning each phase into a Langfuse span — equivalent to a CALL side-effect in SPL that records observability metadata without altering the primary data path. Shared state (`shared` dict) maps directly to SPL `@vars`: it is the single mutable object passed through every phase and captured as span input/output at each boundary. EXCEPTION handling is automatic — any `ValueError` or unhandled exception raised in `exec` is caught, recorded as a failed span, and re-raised, mirroring an SPL `EXCEPTION WHEN RuntimeError THEN COMMIT WITH STATUS='error'` block. Configuration is loaded via `TracingConfig.from_env()` at decorator application time, supporting optional override of secret keys, host URL, debug flag, and per-phase granularity toggles. Full async support is provided through a parallel instrumentation path for `AsyncNode` / `AsyncFlow`, keeping the same span structure with `await`-safe wrappers. No LLM calls are made by the tracing layer itself; the workflow under observation is responsible for all GENERATE operations.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW TracedFlow` | `@trace_flow() class MyFlow(Flow)` | Decorator wraps the flow class; class name becomes the trace name |
| `CREATE FUNCTION trace_node` | `LangfuseTracer.start_node_span() / end_node_span()` | Reusable span open/close logic applied to every node phase |
| `GENERATE fn(...) INTO @var` | `Node.exec(prep_res)` | The actual LLM call inside the traced workflow; output stored in `exec_res` |
| `CALL record_span(...) INTO @span` | `tracer.start_node_span() / tracer.end_node_span()` | Side-effect CALL to Langfuse; does not alter the primary data flow |
| `@shared` (SPL shared var) | `shared` dict | Single mutable state object threaded through every `prep` / `exec` / `post` |
| `@prep_res` | `prep_res` return value of `Node.prep()` | Intermediate result passed from prep to exec phase |
| `@exec_res` | `exec_res` return value of `Node.exec()` | Intermediate result passed from exec to post phase |
| `EXCEPTION WHEN RuntimeError THEN COMMIT WITH STATUS='error'` | `except Exception: tracer.end_node_span(error=e); raise` | Exceptions are recorded then re-raised; trace is marked failed |
| `TracingConfig` | `TracingConfig.from_env()` | Equivalent to SPL INPUT block — declares all external config parameters |

---

### 4. Logical Functions / Prompts

**`trace_flow` decorator**
- Role: Entry point; wraps a flow class to inject tracing around `run()` / `run_async()`. Starts a top-level Langfuse trace, captures the initial `shared` state as trace input, runs the original flow, captures the final `shared` state as trace output.
- Key conventions: Flow name defaults to `cls.__name__`; optional `session_id` and `user_id` group related traces in the Langfuse dashboard.

**`LangfuseTracer.start_node_span` / `end_node_span`**
- Role: Per-phase span lifecycle management. Called before and after each of `prep`, `exec`, `post`. Records phase name, input data, output data, wall-clock duration, and error details.
- Key conventions: Span names follow the pattern `NodeClassName.phase` (e.g., `MyNode.exec`). Error payloads include exception type and message; stack traces appear in Langfuse's error detail view.

**`TracingConfig`**
- Role: Configuration factory. Reads `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_HOST`, and per-phase toggle env vars. `validate()` returns a boolean so callers can degrade gracefully rather than hard-crash on missing credentials.
- Key conventions: All toggles default to `true`; `POCKETFLOW_TRACING_DEBUG=true` emits verbose stdout logs for local debugging.

---

### 5. Control Flow

Execution begins when `flow.run(shared)` is called on a decorated flow class. The decorator intercepts the call, opens a Langfuse trace, then delegates to the original `run()` which iterates through the node graph. For each node, the patched `prep` phase opens a span, executes the original prep logic, and closes the span with the returned `prep_res`. The same open/execute/close pattern repeats for `exec` and `post`. If `exec` raises, the span closes with `status=error` and the exception propagates normally — no suppression. After the last node's `post` returns, the top-level trace closes with the final `shared` state. For async flows, the identical structure is applied to `prep_async`, `exec_async`, and `post_async` with `await` at each boundary.

---

### 6. How to Regenerate as SPL

```
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Wrap a PocketFlow LLM workflow with phase-level Langfuse
tracing. Use a WORKFLOW that accepts an inner workflow as input, then uses CALL
side-effect operations to record spans before and after each GENERATE call. Capture
shared @vars as span input/output at each GENERATE boundary. Handle EXCEPTION WHEN
RuntimeError by recording a failed span status before re-raising." --mode workflow

# Step 2 — compile to any target
spl3 splc compile tracing_wrapper.spl --lang python/pocketflow
spl3 splc compile tracing_wrapper.spl --lang python/langgraph
spl3 splc compile tracing_wrapper.spl --lang go
```