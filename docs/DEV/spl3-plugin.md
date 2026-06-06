# `/spl3` — Claude Code Plugin for SPL 3.0

A Claude Code **skill** that exposes the full `spl3` CLI as the `/spl3`
slash command.  Once installed, you can type `/spl3 run hello.spl` (or any
other `spl3` sub-command) directly from the Claude Code chat prompt.

---

## Prerequisites

| Requirement | How to check |
|---|---|
| `spl-llm` installed | `spl3 --version` |
| Claude Code installed | `claude --version` |

---

## Install

`SKILL.md` is shipped inside the `spl-llm` package, so there is nothing extra
to clone or download.  One command installs everything:

```bash
spl3 install-skill
```

That command:
1. Copies `SKILL.md` to `~/.claude/skills/spl3/SKILL.md`
2. Appends the registration block to `~/.claude/CLAUDE.md` (creates the file
   if it does not exist)

It is **idempotent** — safe to re-run after upgrading `spl-llm`.

### Project-local install (optional)

To restrict the skill to one project directory instead of all Claude Code
sessions:

```bash
spl3 install-skill --local
```

This writes to `./.claude/` in the current directory instead of `~/.claude/`.

### Preview before installing

```bash
spl3 install-skill --dry-run
```

### Verify

Open a new Claude Code session (or type `/clear`), then:

```
/spl3 --help
```

Claude prints the full `spl3` help.  `spl3` also appears in the "available
skills" list shown at the top of every session.

---

## Uninstall

```bash
rm -rf ~/.claude/skills/spl3
```

Then remove the three-line `# spl3` block from `~/.claude/CLAUDE.md`.

---

## Usage

Once installed, strip the leading `/spl3` and use any `spl3` sub-command:

```
/spl3 run cookbook/01_hello_world/hello.spl
/spl3 run cookbook/01_hello_world/hello.spl --adapter claude
/spl3 describe my_workflow.spl
/spl3 validate my_workflow.spl
/spl3 explain my_workflow.spl
/spl3 text2spl "summarise a list of URLs in parallel"
/spl3 text2mmd "a self-refine loop for code review"
/spl3 spl2mmd my_workflow.spl
/spl3 splc compile my_workflow.spl --lang python/langgraph
/spl3 registry list
/spl3 show
/spl3 configure set adapter ollama
/spl3 vibe "a parallel news digest pipeline"
```

Claude passes your arguments verbatim to the `spl3` CLI and shows you the
output.  If the command writes an output file, Claude offers to open and
review it.

---

## Project-scoped install (optional)

If you want the skill available only when working in this repository (not
globally), install into the project's `.claude/` directory instead:

```bash
mkdir -p .claude/skills/spl3
cp claude/skills/spl3/SKILL.md .claude/skills/spl3/SKILL.md
```

Then add the registration block to `.claude/CLAUDE.md` (the repo-level file)
instead of `~/.claude/CLAUDE.md`.

---

## Repository layout

`SKILL.md` is shipped as **package data** inside the `spl3` Python package
so that `pip install spl-llm` is sufficient — no extra `git clone` needed.

```
spl3/
└── _skill/
    └── SKILL.md      ← edit this file to change plugin behaviour
```

`pyproject.toml` declares it as package data:

```toml
[tool.setuptools.package-data]
"spl3" = ["_skill/SKILL.md"]
```

After editing `spl3/_skill/SKILL.md`, re-run `spl3 install-skill` to push
the update to your global install.

---

## How it works

```
User types:   /spl3 run hello.spl
                    │
                    ▼
         Claude Code reads ~/.claude/CLAUDE.md
         → sees "skill: spl3" registration
                    │
                    ▼
         Skill tool loads ~/.claude/skills/spl3/SKILL.md
                    │
                    ▼
         Claude follows SKILL.md instructions
                    │
                    ▼
         Bash tool runs:  spl3 run hello.spl
                    │
                    ▼
         Output shown in the session
```

No Python code, no entry-point wiring, no package changes.  The skill is
pure Markdown instructions to the Claude AI model.

---

## Extending the skill

To add new behaviour (e.g. a custom shorthand or extra guidance):

1. Edit `spl3/_skill/SKILL.md` in this repo.
2. Re-run the installer to push the update:
   ```bash
   spl3 install-skill
   ```
3. Type `/clear` in Claude Code — no restart needed.

---

## See also

- `spl3 --help` — full CLI reference
- `docs/GUIDE/` — SPL 3.0 user guide
- `cookbook/` — example `.spl` workflows
