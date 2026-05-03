# NeurIPS-26 Lab — Issue Log

Issues found during experiments. Fixed iteratively with Claude Code CLI.

Format:
```
## [date] [recipe] [model] — short title
- symptom
- fix applied / workaround
- status: open | fixed | wontfix
```

---

## [2026-05-03] R2-rag / claude_cli / sonnet — S2 text2mmd render failure

**Symptom:** Generated `.mmd` failed to render in browser. HTML showed error container.

**Root causes (4):**
1. `\n` inside unquoted node labels (`C[foo\nbar]`) — renders as literal `\n`, not a line break
2. Unicode arrow `→` inside a label (`split texts → chunks`) — breaks Mermaid parser
3. `{{text}}` (hexagon) used for decision nodes — prompt was instructing wrong shape; `{text}` is the correct diamond/rhombus
4. `B --> OW` — edge targeting a subgraph name instead of the first node inside it; first node (`C`) was unreachable

**Fix applied to source (`spl3/cli.py`):**
- `fix_mermaid_syntax()`: added post-processing for `\n` → `<br/>` (with label quoting), Unicode `→` → `->`, removed the broken `{text}` → `{{text}}` conversion that was causing #3
- Prompt: corrected decision node to `{text}` (diamond), added explicit rules against `\n`, Unicode arrows, and subgraph-name edge targets; updated example to match

**Additional issues found on first regeneration:**
5. `-. "text" .-->` — invalid dotted-edge-with-label syntax (correct: `-.->|text|`)
6. `[("text")]` — non-standard cylindrical shape that confuses the parser (correct: `["text"]`)
7. Validator was generating false positives (split regex double-escaped, `{text}` → double-brace rule was backwards). Validator rewritten.

**Status:** fixed at source — regenerated S2 cleanly with no warnings
