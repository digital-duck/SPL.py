"""
spl.stdlib — SPL Standard Library

Built-in tools available in every SPL workflow without --tools.
Mirrors the standard SQL function set so SQL practitioners can use
familiar names directly in CALL statements.

Categories
----------
  Type conversion   : to_int, to_float, to_text, to_bool
  String            : upper, lower, trim, ltrim, rtrim, length,
                      substr, replace, concat, instr, lpad, rpad,
                      split_part, reverse
  Pattern matching  : like, startswith, endswith, contains, regexp_match
  Numeric           : abs_val, round_val, ceil_val, floor_val,
                      mod_val, power_val, sqrt_val, sign_val, clamp
  Conditional       : coalesce, nullif, iif
  Null / empty      : isnull, nvl, isblank
  Aggregate (text)  : word_count, char_count, line_count
  JSON              : json_get, json_set, json_keys, json_length, json_pretty
  Date / time       : now_iso, date_format_val, date_diff_days
  Hashing           : md5_hash, sha256_hash
  List / split      : list_get, list_length, list_join, list_contains, trim_turns
  File I/O          : write_file, read_file, file_exists, make_dir, path_join
  Agentic / Network : web_search, http_get, run_python

All tools accept and return strings (SPL's universal scalar type).
Numeric tools accept numeric strings and return numeric strings so they
compose naturally with EVALUATE WHEN > comparisons.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import re
import datetime
from typing import Any

from spl.tools import spl_tool

# ── Type Conversion ──────────────────────────────────────────────────────────

@spl_tool
def to_int(value: str) -> int:
    """CAST(value AS INTEGER) — convert string to integer (0 on failure)."""
    try:
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        return 0


@spl_tool
def to_float(value: str) -> float:
    """CAST(value AS FLOAT) — convert string to float (0.0 on failure).
    Extracts the first numeric token, so '0.85\\n' and 'score: 0.85' both work.
    """
    if not value:
        return 0.0
    m = re.search(r"-?\d+(?:\.\d+)?", str(value).strip())
    if m:
        try:
            return float(m.group())
        except ValueError:
            pass
    return 0.0


@spl_tool
def to_text(value: Any) -> str:
    """CAST(value AS TEXT) — convert any value to its string representation."""
    if value is None:
        return ""
    return str(value)


@spl_tool
def to_bool(value: str) -> str:
    """CAST(value AS BOOLEAN) — returns 'true' or 'false'.
    Truthy: '1', 'true', 'yes', 'on', 't', 'y' (case-insensitive).
    """
    return "true" if str(value).strip().lower() in {"1", "true", "yes", "on", "t", "y"} else "false"


# ── String Functions ─────────────────────────────────────────────────────────

@spl_tool
def upper(value: str) -> str:
    """UPPER(value) — convert to uppercase."""
    return str(value).upper()


@spl_tool
def lower(value: str) -> str:
    """LOWER(value) — convert to lowercase."""
    return str(value).lower()


@spl_tool
def trim(value: str) -> str:
    """TRIM(value) — remove leading and trailing whitespace."""
    return str(value).strip()


@spl_tool
def ltrim(value: str) -> str:
    """LTRIM(value) — remove leading whitespace."""
    return str(value).lstrip()


@spl_tool
def rtrim(value: str) -> str:
    """RTRIM(value) — remove trailing whitespace."""
    return str(value).rstrip()


@spl_tool
def length(value: str) -> int:
    """LENGTH(value) — number of characters."""
    return len(str(value))


@spl_tool
def len_val(value: Any) -> int:
    """LEN(value) — polymorphic length: string chars, JSON array items, or JSON object keys."""
    s = str(value).strip()
    # Try parsing as JSON first (array or object)
    if (s.startswith('[') and s.endswith(']')) or (s.startswith('{') and s.endswith('}')):
        try:
            obj = json.loads(s)
            return len(obj)
        except (json.JSONDecodeError, TypeError):
            pass
    # Fallback to string length
    return len(s)


@spl_tool
def substr(value: str, start: str, length: str = "-1") -> str:
    """SUBSTR(value, start, length) — 1-based substring.
    If length is -1 (default), returns from start to end of string.
    """
    s = str(value)
    i = int(start) - 1          # convert 1-based to 0-based
    i = max(0, i)
    n = int(length)
    if n < 0:
        return s[i:]
    return s[i:i + n]


@spl_tool
def replace(value: str, old: str, new: str) -> str:
    """REPLACE(value, old, new) — replace all occurrences of old with new."""
    return str(value).replace(str(old), str(new))


@spl_tool
def concat(*args: str) -> str:
    """CONCAT(a, b, ...) — concatenate strings."""
    return "".join(str(a) for a in args)


@spl_tool
def instr(value: str, search: str) -> int:
    """INSTR(value, search) — 1-based index of first occurrence; 0 if not found."""
    idx = str(value).find(str(search))
    return idx + 1 if idx >= 0 else 0


@spl_tool
def lpad(value: str, width: str, fill: str = " ") -> str:
    """LPAD(value, width, fill) — left-pad string to given width."""
    return str(value).rjust(int(width), str(fill)[0] if fill else " ")


@spl_tool
def rpad(value: str, width: str, fill: str = " ") -> str:
    """RPAD(value, width, fill) — right-pad string to given width."""
    return str(value).ljust(int(width), str(fill)[0] if fill else " ")


@spl_tool
def split_part(value: str, delimiter: str, part: str) -> str:
    """SPLIT_PART(value, delimiter, part) — 1-based part after splitting on delimiter."""
    parts = str(value).split(str(delimiter))
    idx = int(part) - 1
    return parts[idx] if 0 <= idx < len(parts) else ""


@spl_tool
def reverse(value: str) -> str:
    """REVERSE(value) — reverse a string."""
    return str(value)[::-1]


# ── Pattern Matching ─────────────────────────────────────────────────────────

@spl_tool
def like(value: str, pattern: str) -> str:
    """LIKE(value, pattern) — SQL LIKE match; % = any chars, _ = any char.
    Returns 'true' or 'false'.
    """
    # Convert SQL wildcards BEFORE re.escape so they don't get escaped,
    # then escape everything else. Use placeholders to preserve intent.
    p = str(pattern)
    parts = re.split(r"(%|_)", p)
    regex = "".join(
        ".*" if tok == "%" else "." if tok == "_" else re.escape(tok)
        for tok in parts
    )
    return "true" if re.fullmatch(regex, str(value), re.IGNORECASE) else "false"


@spl_tool
def startswith(value: str, prefix: str) -> str:
    """STARTSWITH(value, prefix) — returns 'true' or 'false'."""
    return "true" if str(value).startswith(str(prefix)) else "false"


@spl_tool
def endswith(value: str, suffix: str) -> str:
    """ENDSWITH(value, suffix) — returns 'true' or 'false'."""
    return "true" if str(value).endswith(str(suffix)) else "false"


@spl_tool
def contains(value: str, substring: str) -> str:
    """CONTAINS(value, substring) — returns 'true' or 'false'."""
    return "true" if str(substring) in str(value) else "false"


@spl_tool
def regexp_match(value: str, pattern: str) -> str:
    """REGEXP_MATCH(value, pattern) — returns 'true' if pattern matches anywhere."""
    return "true" if re.search(str(pattern), str(value)) else "false"


# ── Numeric Functions ────────────────────────────────────────────────────────

@spl_tool
def abs_val(value: str) -> float:
    """ABS(value) — absolute value."""
    return abs(float(value))


@spl_tool
def round_val(value: str, decimals: str = "0") -> float:
    """ROUND(value, decimals) — round to N decimal places (default 0)."""
    return round(float(value), int(decimals))


@spl_tool
def ceil_val(value: str) -> int:
    """CEIL(value) — smallest integer >= value."""
    return math.ceil(float(value))


@spl_tool
def floor_val(value: str) -> int:
    """FLOOR(value) — largest integer <= value."""
    return math.floor(float(value))


@spl_tool
def mod_val(dividend: str, divisor: str) -> float:
    """MOD(dividend, divisor) — remainder of integer division."""
    return float(dividend) % float(divisor)


@spl_tool
def power_val(base: str, exponent: str) -> float:
    """POWER(base, exponent) — base raised to exponent."""
    return math.pow(float(base), float(exponent))


@spl_tool
def sqrt_val(value: str) -> float:
    """SQRT(value) — square root."""
    return math.sqrt(float(value))


@spl_tool
def sign_val(value: str) -> int:
    """SIGN(value) — returns -1, 0, or 1."""
    v = float(value)
    return 0 if v == 0 else (1 if v > 0 else -1)


@spl_tool
def clamp(value: str, lo: str, hi: str) -> float:
    """CLAMP(value, lo, hi) — constrain value to [lo, hi] range."""
    return max(float(lo), min(float(hi), float(value)))


# ── Conditional Functions ────────────────────────────────────────────────────

@spl_tool
def coalesce(*args: str) -> str:
    """COALESCE(a, b, ...) — return first non-null, non-empty argument."""
    for a in args:
        if a is not None and str(a).strip() != "":
            return str(a)
    return ""


@spl_tool
def nullif(value: str, compare: str) -> str:
    """NULLIF(value, compare) — return '' if value == compare, else value."""
    return "" if str(value) == str(compare) else str(value)


@spl_tool
def iif(condition: str, true_val: str, false_val: str) -> str:
    """IIF(condition, true_val, false_val) — inline if.
    Condition is true when: '1', 'true', 'yes' (case-insensitive).
    """
    truthy = str(condition).strip().lower() in {"1", "true", "yes", "t", "y"}
    return str(true_val) if truthy else str(false_val)


# ── Null / Empty Checks ──────────────────────────────────────────────────────

@spl_tool
def isnull(value: str) -> str:
    """ISNULL(value) — returns 'true' if value is None or empty string."""
    return "true" if (value is None or str(value).strip() == "") else "false"


@spl_tool
def nvl(value: str, default: str) -> str:
    """NVL(value, default) — return default if value is null/empty (Oracle-style)."""
    return str(default) if (value is None or str(value).strip() == "") else str(value)


@spl_tool
def isblank(value: str) -> str:
    """ISBLANK(value) — returns 'true' if value is empty or only whitespace."""
    return "true" if str(value).strip() == "" else "false"


# ── Text Aggregates ──────────────────────────────────────────────────────────

@spl_tool
def word_count(value: str) -> int:
    """Word count — number of whitespace-delimited tokens."""
    return len(str(value).split())


@spl_tool
def char_count(value: str) -> int:
    """Character count excluding whitespace."""
    return len(str(value).replace(" ", "").replace("\n", "").replace("\t", ""))


@spl_tool
def line_count(value: str) -> int:
    """Line count — number of newline-separated lines."""
    return len(str(value).splitlines())


# ── JSON Functions ───────────────────────────────────────────────────────────

@spl_tool
def json_get(json_str: str, key: str) -> str:
    """JSON_GET(json, key) — extract a top-level key from a JSON object string.
    Supports dot notation: 'a.b' extracts json['a']['b'].
    Returns '' if key not found or input is not valid JSON.
    """
    try:
        obj = json.loads(str(json_str))
        for part in str(key).split("."):
            if isinstance(obj, dict):
                obj = obj.get(part, "")
            else:
                return ""
        return str(obj) if obj != "" else ""
    except (json.JSONDecodeError, TypeError):
        return ""


@spl_tool
def json_set(json_str: str, key: str, value: str) -> str:
    """JSON_SET(json, key, value) — set a top-level key and return updated JSON string."""
    try:
        obj = json.loads(str(json_str)) if str(json_str).strip() else {}
    except json.JSONDecodeError:
        obj = {}
    obj[str(key)] = str(value)
    return json.dumps(obj, ensure_ascii=False)


@spl_tool
def json_keys(json_str: str) -> str:
    """JSON_KEYS(json) — return comma-separated list of top-level keys."""
    try:
        obj = json.loads(str(json_str))
        if isinstance(obj, dict):
            return ", ".join(obj.keys())
        return ""
    except (json.JSONDecodeError, TypeError):
        return ""


@spl_tool
def json_pretty(json_str: str) -> str:
    """JSON_PRETTY(json) — pretty-print JSON with 2-space indent."""
    try:
        return json.dumps(json.loads(str(json_str)), indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        return str(json_str)


# ── Date / Time ──────────────────────────────────────────────────────────────

@spl_tool
def now_iso() -> str:
    """NOW() — current UTC datetime as ISO-8601 string: 'YYYY-MM-DDTHH:MM:SS'."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


@spl_tool
def date_format_val(iso_date: str, fmt: str) -> str:
    """DATE_FORMAT(date, format) — reformat an ISO date string using strftime format.
    Example: date_format_val('2026-03-23', '%B %d, %Y') → 'March 23, 2026'
    """
    for parse_fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.datetime.strptime(str(iso_date).strip(), parse_fmt)
            return dt.strftime(str(fmt))
        except ValueError:
            continue
    return str(iso_date)


@spl_tool
def date_diff_days(date_a: str, date_b: str) -> int:
    """DATEDIFF(date_a, date_b) — number of days between two ISO dates (a - b)."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            a = datetime.datetime.strptime(str(date_a).strip(), fmt)
            b = datetime.datetime.strptime(str(date_b).strip(), fmt)
            return (a - b).days
        except ValueError:
            continue
    return 0


# ── Hashing ──────────────────────────────────────────────────────────────────

@spl_tool
def md5_hash(value: str) -> str:
    """MD5(value) — MD5 hex digest (useful for deduplication keys)."""
    return hashlib.md5(str(value).encode()).hexdigest()


@spl_tool
def sha256_hash(value: str) -> str:
    """SHA256(value) — SHA-256 hex digest."""
    return hashlib.sha256(str(value).encode()).hexdigest()


# ── List / Array Helpers ─────────────────────────────────────────────────────

@spl_tool
def list_get(value: str, index: str, delimiter: str = ",") -> str:
    """LIST_GET(value, index, delimiter) — 1-based element from delimited list."""
    parts = str(value).split(str(delimiter))
    idx = int(index) - 1
    return parts[idx].strip() if 0 <= idx < len(parts) else ""


@spl_tool
def list_length(value: str, delimiter: str = ",") -> int:
    """LIST_LENGTH(value, delimiter) — number of elements in delimited list."""
    return len(str(value).split(str(delimiter)))


@spl_tool
def list_join(value: str, old_delim: str, new_delim: str) -> str:
    """LIST_JOIN(value, old_delim, new_delim) — re-join list with a new delimiter."""
    parts = [p.strip() for p in str(value).split(str(old_delim))]
    return str(new_delim).join(parts)


@spl_tool
def list_contains(value: str, item: str, delimiter: str = ",") -> str:
    """LIST_CONTAINS(value, item, delimiter) — 'true' if item is in delimited list."""
    parts = [p.strip() for p in str(value).split(str(delimiter))]
    return "true" if str(item).strip() in parts else "false"


@spl_tool
def trim_turns(history: str, max_turns: str) -> str:
    r"""TRIM_TURNS(history, max_turns) — keep the last N User/Assistant turn pairs.

    Expects history in the format: \nUser: <text>\nAssistant: <text>\nUser: ...
    Returns trimmed history in the same format (zero LLM cost, deterministic).
    """
    n = max(1, int(str(max_turns).strip() or "10"))
    parts = str(history).split("\nUser: ")
    turns = [p for p in parts if p.strip()]
    last_n = turns[-n:] if len(turns) > n else turns
    if not last_n:
        return ""
    return "\nUser: " + "\nUser: ".join(last_n)


# ── File I/O ──────────────────────────────────────────────────────────────────

@spl_tool
def write_file(file_path: str, content: str, mode: str = "w") -> str:
    """WRITE_FILE(file_path, content [, mode]) — write text to a file.

    mode: 'w' (overwrite, default) or 'a' (append).
    Creates parent directories automatically.
    Returns the absolute path written.
    """
    p = pathlib.Path(str(file_path).strip())
    p.parent.mkdir(parents=True, exist_ok=True)
    m = str(mode).strip().lower()
    if m not in ("w", "a"):
        m = "w"
    with p.open(m, encoding="utf-8") as fh:
        fh.write(str(content))
    return str(p.resolve())


@spl_tool
def read_file(file_path: str) -> str:
    """READ_FILE(file_path) — read entire text file and return its content.

    Raises FileNotFoundError (propagated as SPL FileNotFound) if path missing.
    """
    p = pathlib.Path(str(file_path).strip())
    return p.read_text(encoding="utf-8")


@spl_tool
def file_exists(file_path: str) -> str:
    """FILE_EXISTS(file_path) — return 'true' if path exists, else 'false'."""
    return "true" if pathlib.Path(str(file_path).strip()).exists() else "false"


@spl_tool
def make_dir(dir_path: str) -> str:
    """MAKE_DIR(dir_path) — create directory (and parents) if not present.

    Returns the absolute path of the directory.
    """
    p = pathlib.Path(str(dir_path).strip())
    p.mkdir(parents=True, exist_ok=True)
    return str(p.resolve())


@spl_tool
def path_join(*parts: str) -> str:
    """PATH_JOIN(part1, part2, ...) — join path segments with OS separator.

    Returns the joined path as a string.
    """
    return str(pathlib.Path(*[str(p).strip() for p in parts]))


# ── Agentic / Network Tools ───────────────────────────────────────────────────

@spl_tool(name="web_search")
def web_search(query: str) -> str:
    """WEB_SEARCH(query) — search the web via DuckDuckGo, return top-5 results.

    Accepts a plain query string or a YAML/prefixed decision block:
        'search: what is quantum computing'   → extracts the query after 'search:'
        'search_query: ...'                   → extracts the search_query field

    Usage in SPL:
        CALL web_search(@query) INTO @results;
        CALL web_search(@decision) INTO @results;

    Requires: pip install ddgs   (or pip install duckduckgo_search)
    """
    import warnings

    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return "web_search unavailable: install ddgs (pip install ddgs)"

    q = str(query).strip()

    # Extract query from YAML/prefixed decision block if present
    m = re.search(r'search_query\s*:\s*["\']?([^"\'\n]+)["\']?', q)
    if not m:
        m = re.search(r'^search\s*:\s*(.+)$', q, re.MULTILINE | re.IGNORECASE)
    if not m:
        m = re.search(r'(?<!\w)query\s*:\s*["\']?([^"\'\n]+)["\']?', q)
    if m:
        q = m.group(1).strip()

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            results = DDGS().text(q, max_results=5)
        if not results:
            return f"No results found for: {q}"
        lines = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            url   = r.get("href", "")
            body  = r.get("body", "")
            lines.append(f"[{i}] {title}\n    URL: {url}\n    {body}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"Search error: {e}"


@spl_tool(name="search_web")
def search_web(query: str) -> str:
    """SEARCH_WEB(query) — alias for web_search.

    Usage in SPL:
        CALL search_web(@query) INTO @results;
    """
    return web_search(query)


@spl_tool(name="http_get")
def http_get(url: str, timeout: str = "10") -> str:
    """HTTP_GET(url [, timeout]) — fetch a URL and return response body as text.

    Returns the HTTP response body on success, or an error message on failure.
    Timeout is in seconds (default 10).

    Usage in SPL:
        CALL http_get(@url) INTO @html;
        CALL http_get(@url, '30') INTO @response;

    Requires: pip install requests

    Deprecated: use CREATE TOOL_API with `import requests` in the kernel instead.
    Scheduled for removal in spl-llm v3.2.
    """
    try:
        import requests
    except ImportError:
        return "http_get unavailable: install requests (pip install requests)"

    try:
        resp = requests.get(str(url).strip(), timeout=float(timeout))
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"HTTP error: {e}"


@spl_tool(name="run_python")
def run_python(code: str, timeout: str = "30") -> str:
    """RUN_PYTHON(code [, timeout]) — execute Python code in a subprocess.

    Returns stdout on success, or stderr on failure.
    Timeout is in seconds (default 30).

    Usage in SPL:
        CALL run_python(@code_snippet) INTO @output;

    Security note: executes arbitrary code — use only with trusted input.

    Deprecated: with --kernel (now default), deterministic Python belongs in
    CREATE TOOL_API blocks, which execute in the persistent kernel session and
    share state across calls. This subprocess fallback remains for --no-kernel
    mode only. Scheduled for removal in spl-llm v3.2.
    """
    import subprocess
    import sys

    try:
        result = subprocess.run(
            [sys.executable, "-c", str(code)],
            capture_output=True,
            text=True,
            timeout=float(timeout),
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return f"Error (exit {result.returncode}):\n{result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return f"run_python timed out after {timeout}s"
    except Exception as e:
        return f"run_python error: {e}"


# ------------------------------------------------------------------ #
# Layer 2 content cache tools                                          #
# ------------------------------------------------------------------ #

@spl_tool
def cache_get(concept: str, rubric_version: str = "v1", params_json: str = "{}") -> str:
    """Retrieve a verified section from the Layer 2 content cache.

    Returns the cached content string on a hit, or the sentinel string
    "miss" when the concept is not in the cache.

    Usage in SPL:
        CALL cache_get(@concept) INTO @section
        EVALUATE @section:
            WHEN miss:
                CALL build_micro_textbook(@concept) INTO @section
                CALL cache_put(@concept, @section)
    """
    try:
        from spl3.cache import get_content_cache
        params = json.loads(params_json) if params_json else {}
        cache = get_content_cache()
        entry = cache.get(
            concept=concept,
            params=params,
            rubric_version=rubric_version,
            dep_hashes={},
        )
        return entry.content if entry is not None else "miss"
    except Exception:
        return "miss"


@spl_tool
def cache_put(
    concept: str,
    content: str,
    badges: str = "",
    rubric_version: str = "v1",
    params_json: str = "{}",
    token_cost: str = "0",
    verifier: str = "",
    statement: str = "",
) -> str:
    """Store a generated section in the Layer 2 content cache.

    Returns the cache key on success, or an error string on failure.
    `badges` is a comma-separated trust badge set (claim axis:
    machine_verified, machine_proved; exposition axis: ai_reviewed,
    human_verified; empty = machine_generated baseline). `verifier` records
    the engine-of-record that checked the content ("sympy", "sage",
    "lean", ...). `statement` carries the kernel-checked Lean proposition
    backing a machine_proved badge, rendered alongside the prose wherever
    the badge appears.

    Usage in SPL:
        CALL cache_put(@concept, @section) INTO @cache_key
        CALL cache_put(@concept, @section, badges='machine_verified', verifier='sage') INTO @cache_key
        CALL cache_put(@concept, @report, badges='machine_proved', verifier='lean', statement=@lean_stmt) INTO @cache_key
    """
    try:
        from spl3.cache import get_content_cache
        params = json.loads(params_json) if params_json else {}
        badge_set = [b.strip() for b in badges.split(",") if b.strip()]
        # legacy callers passed the old single-ordinal tier in this slot
        if badge_set == ["machine_generated"]:
            badge_set = []
        cache = get_content_cache()
        entry = cache.put(
            concept=concept,
            content=content,
            badges=badge_set,
            params=params,
            rubric_version=rubric_version,
            dep_hashes={},
            token_cost=int(token_cost) if token_cost.isdigit() else 0,
            verifier=verifier,
            statement=statement,
        )
        return entry.key
    except Exception as e:
        return f"cache_put error: {e}"


@spl_tool
def cache_promote(
    concept: str,
    badge: str,
    statement: str = "",
    rubric_version: str = "v1",
    params_json: str = "{}",
) -> str:
    """Add a trust badge to an existing Layer 2 cache entry (B-2/B-4).

    Resolves the entry by the same key derivation cache_get/cache_put use
    (concept + params + rubric version, empty dep hashes) and adds `badge`
    to its set. A non-empty `statement` records the formal statement
    backing the badge — pass the kernel-checked Lean proposition when
    promoting to machine_proved. Returns the new comma-joined badge set on
    success, or an error string ("cache_promote error: ...") on failure —
    including when no entry exists, so callers can fall back to cache_put.

    Usage in SPL:
        CALL cache_promote(@concept, 'machine_proved', statement=@lean_stmt) INTO @badges
        EVALUATE @badges
            WHEN contains("error") THEN
                CALL cache_put(@concept, @report, badges='machine_proved', statement=@lean_stmt)
        END
    """
    try:
        from spl3.cache import get_content_cache, content_key
        params = json.loads(params_json) if params_json else {}
        key = content_key(concept, params, rubric_version, {})
        new_badges = get_content_cache().promote(key, badge, statement=statement)
        return ",".join(new_badges)
    except Exception as e:
        return f"cache_promote error: {e}"
