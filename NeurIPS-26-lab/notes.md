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

---

## [2026-05-03] R2-rag / claude_cli / sonnet — S3 LLM preamble before code fence

**Symptom:** `Validation: FAILED — Lexer error at 3:1: Unexpected character '\`'` — file started with "Let me check the existing SPL files..." prose then `` ```spl ``.

**Root cause:** `mmd2spl` fence-stripper checked only `lines[0]` for the opening fence. When the LLM adds preamble prose before the code block, the fence is on a later line and the check misses it, leaving the preamble + backtick in the output.

**Fix applied to source (`spl3/cli.py` `cmd_mmd2spl`):**
- Replaced `lines[0]` check with `next(i for i, l in enumerate(lines) if re.match(r"^```(spl)?\s*$", ...))` to find the opening fence anywhere in the response
- Updated prompt: added "no preamble, no markdown fences" to output instruction

**Status:** fixed at source — re-run mmd2spl for R2

---

## [2026-05-03] R2-rag / claude_cli / sonnet — S3 two WORKFLOW syntax errors

**Symptom:** `spl3 validate` reported `Parse error at 11:23: Expected DO, got SEMICOLON`.

**Root causes (2):**
1. `INPUT @question TEXT;` — semicolons after INPUT/OUTPUT declarations are invalid; correct syntax has no semicolons and all inputs comma-separated on one line
2. `DO ... END;` body wrapper inside the WORKFLOW, followed by a second `END;` — the WORKFLOW body is simply `DO ... END;` with no nesting; the extra `END;` caused a second parse error

**Root cause of both:** `_MMD2SPL_PROMPT` itself showed `INPUT @question TEXT;` with a semicolon as the example, teaching the LLM the wrong syntax.

**Fix applied to source (`spl3/cli.py` `_MMD2SPL_PROMPT`):**
- Replaced rule #1/2 with a concrete syntax block showing correct WORKFLOW structure: INPUT/OUTPUT before DO, no semicolons, single END; closes the workflow
- Added explicit IMPORTANT notes against semicolons and nested DO...END; wrappers

**Fix applied to file:** Merged INPUT lines, removed semicolons, removed extra END;

**Status:** fixed at source — validate passes

---

## [2026-05-03] R1-agent / claude_cli / claude — S3 mmd2spl truncated output

**Symptom:** `S3-agent-claude_cli-claude.spl` contained only 6 lines, ending mid-way through the first prompt template body.

**Root cause:** `mmd2spl` fence-stripping used a non-greedy regex `r"```spl\s*\n(.*?)\n```"`. When the LLM embeds an inner ` ```yaml ` code block inside a `CREATE FUNCTION` prompt template body, the `.*?` stops at that inner closing ` ``` ` rather than the outer one, discarding the rest of the SPL.

**Fix applied to source (`spl3/cli.py` `cmd_mmd2spl`):**
- Replaced regex fence-stripper with line-based stripping: check first line for `` ```spl `` / `` ``` `` opening, check last line for `` ``` `` closing, trim only those two lines. Inner fences are no longer touched.

**Status:** fixed at source — re-run S3 for R1

---

## [2026-05-03] R1-agent / claude_cli / sonnet — S2 decision node wrong shape

**Symptom:** `C{{Action == 'search'?}}` rendered as a hexagon instead of a diamond in the Mermaid diagram.

**Root cause:** `{{text}}` is Mermaid hexagon shape; `{text}` is the correct diamond/rhombus for decision nodes. The LLM used double-braces.

**Fix applied:** Replaced `{{Action == 'search'?}}` → `{Action == 'search'?}` directly in the .mmd file.

**Status:** fixed

---

## [2026-05-03] R2-rag / claude_cli / sonnet — S2 duplicate START edge

**Symptom:** `START --> A` appeared twice in the .mmd (line 2 and line 32), creating a duplicate edge in the rendered diagram.

**Root cause:** LLM emitted `START --> A` both at the top of the flowchart and again in the cross-subgraph connections section.

**Fix applied:** Removed the redundant `START --> A` from line 32 directly in the .mmd file.

**Status:** fixed

---

## [2026-05-03] R2-rag / S1 (splc describe) — "RETURN default" noise in spec

**Symptom:** S1 spec included "each step RETURNs a `"default"` action token" which propagated into S2 as double-edges labeled `RETURN default` between every node pair.

**Root cause:** `_SPLC_DESCRIBE_PROMPT` instructed the LLM to document all RETURN mappings; PocketFlow's unconditional `return "default"` (linear advance) was treated as a meaningful construct.

**Fix applied to source (`spl3/splc/cli.py`):**
- Added IMPORTANT block in prompt: suppress trivial "default" transitions; only document RETURN when status is non-trivial and drives a real branch/loop
- Updated §0, §2, §4 prompt sections to omit "default" token documentation

**Safety net (`spl3/cli.py` `fix_mermaid_syntax`):**
- Added `re.sub` to strip `|"RETURN default"|` and `|RETURN default|` edge labels from any LLM-generated Mermaid

**Status:** fixed at source
