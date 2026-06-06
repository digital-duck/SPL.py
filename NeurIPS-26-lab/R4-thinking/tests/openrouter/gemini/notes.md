# R4-thinking / openrouter / gemini — Run Notes

## S2 — text2mmd (2026-05-04)

**First run** produced a diagram that failed to render in the browser preview.

### Root Causes

Three issues were found in the generated `.mmd` file, two of which were gemini model
output quality problems and one was a pre-existing bug in `fix_mermaid_syntax`:

| # | Issue | Source | Fix |
|---|-------|--------|-----|
| 1 | `flowchart TD` had 4-space leading indent | `fix_mermaid_syntax` bug — it added indent to the diagram declaration | Fixed in `spl3/cli.py`: declaration keywords now kept at column 0 |
| 2 | Dotted arrow `-.-->` instead of valid `-.->` | gemini emitted extra dash | Fixed in `spl3/cli.py`: new rule normalises `-.-->`, `-.--->` etc. to `-.->` |
| 3 | Pre-existing bug: `fix_mermaid_syntax` bare-arrow fixer corrupted `-.->` into `-.-->` | `(?<![=\-!])->` matched the `->` in `-.->` (preceded by `.`) | Fixed: added `.` to lookbehind exclusion → `(?<![=\-!.])` |
| 4 | Colon inside unquoted node label `[Parse YAML Output: ...]` | gemini model output | Fixed in `spl3/cli.py`: new rule auto-quotes `[label: text]` → `["label: text"]` |

### Source Code Changes (spl3/cli.py — fix_mermaid_syntax)

All four fixes were committed to `spl3/cli.py`. The post-processor now handles these
cases automatically on future runs, so manual `.mmd` repair should not be needed for
these patterns again.

**Re-run** after code fix succeeded. New diagram is clean:
- `flowchart TD` at column 0
- Colon labels auto-quoted
- Dotted arrow valid
- No subgraph used (gemini simplified the diagram — acceptable for S3)

### Diagram Topology (final S2)

```
Start → Init → CoTStep ⇄ (Parse → Eval →|True| Update → CoTStep)
                                    ↓|False|
                                 Finalize → End
```

The CoT self-loop is correctly represented. The internal LLM_Logic subgraph from the
first run was dropped by gemini on re-run — the simpler flat diagram is fine for S3
(the loop back-edge is what matters).

## Human Checkpoint — S2 review

- [x] CoTStep self-loop (via Update) present
- [x] Decision node `next_thought_needed?` with True/False branches
- [x] Finalize → End exit path present
- [x] Proceeded to S3

---

## S3 — mmd2spl (2026-05-04)

`mmd2spl` ran successfully (no tool failure). The generated `.spl` had three model-output
errors in the content; **source code did not need changes**.

### Issues Found (all gemini model errors)

| # | Issue | Original | Fixed |
|---|-------|----------|-------|
| 1 | Double-brace param interpolation | `{{history}}`, `{{plan}}`, `{{raw_output}}` | `{history}`, `{plan}`, `{raw_output}` — SPL uses single braces |
| 2 | `CALL` used for LLM prompt function | `CALL parse_yaml(...) INTO ...` | `GENERATE parse_yaml(...) INTO ...` — `CALL` is for stdlib tools; `CREATE FUNCTION` bodies require `GENERATE` |
| 3 | Invalid SPL type `STRING` | `STRING` throughout params/IO | `TEXT` — SPL type system has `TEXT`, `INT`, `FLOAT`, `BOOL`; `STRING` is not defined |

**Bonus fix**: `''next_thought_needed''` (double single-quotes in prompt body) simplified
to `'next_thought_needed'`; also replaced `@history + "\n" + @raw_response` string
concatenation (unverified SPL support) with `CALL append_text(@history, @raw_response)`.

### Pattern for Gemini

Gemini consistently uses Python/Jinja2 `{{param}}` template syntax in `CREATE FUNCTION`
bodies instead of SPL's `{param}`. Always check and fix this before S4.

### S3 file status
- [x] `.spl` manually fixed — ready for `spl3 validate` then S4
