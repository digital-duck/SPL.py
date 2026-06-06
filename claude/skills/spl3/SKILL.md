---
name: spl3
description: "Run, author, and manage SPL 3.0 workflows. Use when the user types /spl3 or asks to run, create, describe, validate, or compile an .spl workflow."
trigger: /spl3
---

# /spl3

Access the full SPL 3.0 CLI from inside Claude Code.

## Usage

    /spl3 [--help]                                   # list all commands
    /spl3 run <file.spl> [--adapter <name>]          # execute a workflow
    /spl3 describe <file.spl>                        # plain-English spec for a .spl file or folder
    /spl3 validate <file.spl>                        # check syntax/semantics
    /spl3 explain <file.spl>                         # execution plan (no LLM call)
    /spl3 text2spl "<description>"                   # NL → .spl workflow
    /spl3 text2mmd "<description>"                   # NL → Mermaid diagram
    /spl3 spl2mmd <file.spl>                         # .spl → Mermaid diagram
    /spl3 mmd2spl <file.mmd>                         # Mermaid diagram → SPL workflow
    /spl3 img2mmd <image>                            # extract Mermaid flowchart from an image
    /spl3 img2text <image>                           # extract text/pseudo-code from an image
    /spl3 splc compile <file.spl> --lang <target>    # compile to Python/Go/TS
    /spl3 migrate <src> --lang <target>              # migrate codebase via DODA pipeline
    /spl3 compare <file1> <file2>                    # multi-tier diff with verdict synthesis
    /spl3 experiment <config>                        # batch runner for ablation studies
    /spl3 registry list                              # show registered workflows
    /spl3 register <file.spl>                        # register workflows into Hub
    /spl3 peers list                                 # list peer Hubs
    /spl3 peers add <url>                            # add a peer Hub
    /spl3 code-rag seed <path>                       # seed Code-RAG index
    /spl3 code-rag query "<question>"                # query Code-RAG index
    /spl3 show                                       # list adapters and models
    /spl3 configure set <key> <value>                # persist a config value
    /spl3 configure get <key>                        # read a config value
    /spl3 vibe "<description>"                       # NL → working code + README
    /spl3 install-skill                              # install this Claude Code skill

## What You Must Do When Invoked

Strip the leading `/spl3` from the user's input and pass the rest verbatim
to the `spl3` CLI using the Bash tool.

Examples:

    User types:  /spl3 run cookbook/01_hello_world/hello.spl
    You run:     spl3 run cookbook/01_hello_world/hello.spl

    User types:  /spl3 text2spl "summarise a list of URLs in parallel"
    You run:     spl3 text2spl --description "summarise a list of URLs in parallel"

    User types:  /spl3 --help
    You run:     spl3 --help

After running the command, show the output to the user.

Special case — when the command is `--help` or `help`:
  Run `spl3 --help`, then render the subcommand list as a markdown table
  with two columns (Command | Description), sorted alphabetically by command
  name. Keep the Options block as plain text above the table.

If the command produces an output file (e.g. `spl3 text2spl -o workflow.spl`),
offer to open and review it.

If the user provides no arguments (`/spl3` alone), run `spl3 --help` and
display the result.

## Authoring assistance

If the user asks you to **write** or **edit** an `.spl` workflow (rather than
just run one), follow these rules:

1. Use `spl3 validate` to check syntax after every edit.
2. Suggest `spl3 explain` to preview the execution plan before the first run.
3. Propose a meaningful workflow name that matches the file stem.
4. Remind the user to set an adapter via `spl3 configure set adapter <name>`
   or pass `--adapter <name>` to `spl3 run` if none is configured.

## Common adapters

| Adapter name | Backend |
|---|---|
| `ollama` | Local Ollama server |
| `claude` | Anthropic Claude (API key required) |
| `openai` | OpenAI (API key required) |
| `gemini` | Google Gemini (API key required) |

## Error handling

If `spl3` exits non-zero, show the full stderr output and suggest the most
likely fix (missing adapter config, missing `.spl` file, syntax error, etc.).
