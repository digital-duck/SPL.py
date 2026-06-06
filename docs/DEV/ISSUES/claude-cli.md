# Claude CLI Adapter — Known Issues

## Issue: Silent `Claude CLI error (exit 1):` with no detail

**Status:** Fixed  
**File:** `spl/adapters/claude_cli.py`  
**Reported:** 2026-05-24

### Symptom

When a step using the `claude_cli` adapter fails (e.g., NeurIPS Lab S01), the error shown is:

```
RuntimeError: Claude CLI error (exit 1):
```

The message ends after the colon — no detail about what went wrong.

### Root Cause

The `claude` CLI writes error messages to **stdout**, not stderr, when it exits with a non-zero code. Examples that reproduce this:

```
$ echo "hi" | claude --print --model invalid-model-xyz --tools ""
There's an issue with the selected model (invalid-model-xyz). It may not exist or
you may not have access to it. Run --model to pick a different model.
$ echo $?
1
```

The adapter decoded `stderr` for the error detail and raised:

```python
raise RuntimeError(f"Claude CLI error (exit {proc.returncode}): {stderr_text}")
```

Since `stderr` was empty, `stderr_text` was `""`, producing the useless message.

### Fix

Use `stderr_text or stdout_text` as the error detail so stdout-written errors are surfaced:

```python
stderr_text = stderr.decode('utf-8', errors='replace').strip()
stdout_text = stdout.decode('utf-8', errors='replace').strip()

if proc.returncode != 0:
    # The claude CLI often writes errors to stdout rather than stderr.
    error_detail = stderr_text or stdout_text or "(no output)"
    ...
    raise RuntimeError(f"Claude CLI error (exit {proc.returncode}): {error_detail}")
```

The same `error_detail` is used for the `ModelOverloaded` rate-limit detection.

### Common Causes of Exit 1

With the fix in place, the error message will now identify the real cause. Typical reasons:

| Message | Cause |
|---------|-------|
| `There's an issue with the selected model (...)` | Model name invalid or not accessible under current subscription |
| `session limit` / `rate limit` / `quota` | Claude Code subscription limit hit — triggers `ModelOverloaded` |
| `(no output)` | Auth token expired; run `claude` interactively to re-authenticate |
