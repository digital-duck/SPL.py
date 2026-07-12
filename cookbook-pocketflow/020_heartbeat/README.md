# 020 — Heartbeat (Email Monitor)  *(migrated from PocketFlow)*

**Source:** [pocketflow-heartbeat](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-heartbeat)
**Difficulty:** ★☆☆
**Category:** automation

## What it does

Implements a long-running polling agent that checks an IMAP inbox on a configurable interval, summarizes new emails, and suggests a prioritized action for each. A WHILE loop drives the monitoring cycle: connect to IMAP, fetch unseen messages, run an LLM summarization and action-recommendation pass, log the results, then sleep for the configured interval before the next cycle. The loop exits after a maximum number of cycles or when interrupted.

## Real-world use cases

- **Executive inbox triage**: Continuously scan a high-volume inbox, surfacing action items and flagging urgent messages without human attention on every poll
- **On-call alerting**: Monitor a shared ops or support inbox for critical keywords and suggest escalation actions when specific SLA triggers are detected
- **Business intelligence automation**: Watch for emails from key vendors, clients, or partners and extract structured information (order updates, contract changes) on arrival
- **Compliance monitoring**: Scan regulatory notification inboxes and log summarized alerts with recommended responses for compliance officer review

## Key SPL constructs

- `CREATE TOOL_API fetch_emails(imap_host, imap_user, imap_pass)` — authenticates via IMAP and returns unseen messages as JSON
- `CREATE TOOL_API sleep_interval(seconds)` — deterministic sleep between polling cycles
- `CREATE TOOL_API log_results(log_file, cycle, results)` — appends cycle results to a persistent log file
- `WHILE @cycle < @max_cycles DO` — bounded polling loop
- `GENERATE summarize_and_act(@emails_json)` — produces a summary and suggested action for each new email

## Workflow I/O

**Inputs:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `@imap_host` | TEXT | _(required)_ | IMAP server hostname |
| `@imap_user` | TEXT | _(required)_ | IMAP account username |
| `@imap_pass` | TEXT | _(required)_ | IMAP account password |
| `@interval_seconds` | TEXT | `"60"` | Seconds between polling cycles |
| `@max_cycles` | INTEGER | 10 | Maximum number of polling cycles before exiting |
| `@log_file` | TEXT | _(required)_ | Path to the persistent log file |

**Output:** `@summary TEXT` — summary of the final cycle's processed emails

## Run

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

spl3 run cookbook-pocketflow/020_heartbeat/heartbeat.spl \
    --llm claude_cli:claude-sonnet-4-6
```

## Extend it

- Add an `EVALUATE` branch to send a reply or forward specific emails automatically when the LLM detects high urgency
- Replace the fixed `sleep_interval` with an adaptive poll rate that speeds up when messages arrive frequently
- Use `CALL PARALLEL` to run the LLM summarization over multiple emails simultaneously on busy cycles
- Connect to a notification API (e.g., Slack webhook) via a `CREATE TOOL_API` to forward high-priority summaries in real time

## Migrate artifacts

For a detailed functional description, see the **[Functional Spec](migrate/S1-heartbeat-claude-sonnet-4-6-spec.md)**.

```
migrate/
├── S1-heartbeat-claude-sonnet-4-6-spec.md   # splc describe output
├── S2-heartbeat-claude-sonnet-4-6.mmd       # text2mmd Mermaid diagram
└── S3-heartbeat-claude-sonnet-4-6.spl       # raw mmd2spl output (= heartbeat.spl)
```

tools.spl (if present) — CREATE TOOL_API helpers ported from utils.py.
Recipes whose utils.py only wraps call_llm need no tools.spl.
