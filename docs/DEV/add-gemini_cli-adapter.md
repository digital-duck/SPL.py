# Adding the Gemini CLI Adapter

This document outlines the implementation of the `gemini_cli` adapter, designed for zero-marginal-cost development using the Gemini CLI.

## Implementation Details

The adapter is implemented in `spl/adapters/gemini_cli.py`. It wraps the `gemini` command-line tool, which provides an interactive-first but scriptable interface to Gemini models.

### CLI Invocation Strategy

The adapter uses the following command structure to execute prompts non-interactively:
```bash
echo "your prompt" | gemini -p "" --output-format text --model <model_name>
```
- `-p ""`: Enters non-interactive mode. By passing an empty string to `-p`, it tells the CLI to append the stdin input to the prompt.
- `--output-format text`: Ensures the output is clean text without interactive formatting or shell decorations.
- `--model`: Explicitly targets the requested Gemini model.

### Error Mapping

The adapter monitors `stderr` for common API and CLI limits:
- **Rate Limits / Quota**: If the output contains "rate limit", "quota", or "exhausted", it raises the SPL-native `ModelOverloaded` exception.
- **Other Errors**: Standard CLI failures result in a `RuntimeError` containing the exit code and stderr content.

## Registry Integration

The adapter is registered in `spl/adapters/__init__.py` under the name `gemini_cli`. It is included in both the `dd-llm` bridge providers and the bespoke fallback list.

## Usage

In any SPL workflow or CLI command:
```bash
spl3 run workflow.spl --adapter gemini_cli --model gemini-2.0-flash
```

## Benefits
- **Cost**: No per-token costs during local development (utilizes CLI auth/subscription).
- **Environment**: Reuses existing `gemini` CLI configuration and authenticated sessions.
- **Workflow Compatibility**: Fully supports `EXCEPTION WHEN ModelOverloaded` for robust retry logic.
