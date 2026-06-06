"""Helper tools for S3-thinking-claude_cli-sonnet.spl.

Pure data-manipulation CALL functions that manage the thoughts JSON array
and validate/extract YAML fields produced by ChainOfThoughtStep.
"""

from __future__ import annotations
import json
import re
import yaml
from spl.tools import spl_tool


def _strip_fences(text: str) -> str:
    """Strip markdown code fences (```yaml or ```) from LLM output."""
    text = text.strip()
    m = re.match(r'^```(?:yaml)?\s*\n?(.*?)\n?```\s*$', text, flags=re.DOTALL)
    return m.group(1).strip() if m else text


@spl_tool
def format_thoughts_to_text(thoughts_json: str) -> str:
    """Format the JSON thoughts array into a human-readable string."""
    try:
        thoughts = json.loads(thoughts_json)
    except Exception:
        return "(no previous thoughts)"
    if not thoughts:
        return "(no previous thoughts)"
    lines = []
    for i, t in enumerate(thoughts, 1):
        if isinstance(t, dict):
            thinking = t.get("current_thinking", str(t))
        else:
            thinking = str(t)
        lines.append(f"[Thought {i}] {thinking}")
    return "\n".join(lines)


@spl_tool
def extract_last_plan(thoughts_json: str) -> str:
    """Return the next_action_plan from the most recent thought, or empty string."""
    try:
        thoughts = json.loads(thoughts_json)
    except Exception:
        return ""
    if not thoughts:
        return ""
    last = thoughts[-1]
    if isinstance(last, dict):
        return str(last.get("next_action_plan", ""))
    return ""


@spl_tool
def validate_yaml_fields(yaml_text: str) -> str:
    """Return 'true' if the YAML contains all required ChainOfThought fields, else 'false'."""
    required = {"current_thinking", "next_action_plan", "next_thought_needed"}
    try:
        data = yaml.safe_load(_strip_fences(yaml_text))
        if isinstance(data, dict) and required.issubset(data.keys()):
            return "true"
    except Exception:
        pass
    return "false"


@spl_tool
def append_thought(thoughts_json: str, thought_data: str) -> str:
    """Append a new thought (YAML string) to the thoughts JSON array. Returns updated JSON."""
    try:
        thoughts = json.loads(thoughts_json)
    except Exception:
        thoughts = []
    try:
        thought = yaml.safe_load(_strip_fences(thought_data))
    except Exception:
        thought = {"raw": thought_data}
    thoughts.append(thought)
    return json.dumps(thoughts)


@spl_tool
def extract_yaml_field(yaml_text: str, field: str) -> str:
    """Extract a single field value from a YAML string. Returns empty string on failure."""
    try:
        data = yaml.safe_load(_strip_fences(yaml_text))
        if isinstance(data, dict):
            value = data.get(field, "")
            if isinstance(value, bool):
                return "true" if value else "false"
            return str(value) if value is not None else ""
    except Exception:
        pass
    return ""


@spl_tool
def print_thought_progress(current_thinking: str, updated_plan: str) -> str:
    """Print a short progress summary to stdout. Returns 'ok'."""
    preview = lambda s: s[:120] + "..." if len(s) > 120 else s
    print(f"\n[Thought] {preview(current_thinking)}")
    print(f"[Plan]    {preview(updated_plan)}")
    return "ok"
