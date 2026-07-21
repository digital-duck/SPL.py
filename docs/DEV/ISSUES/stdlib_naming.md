# Stdlib TOOL_API naming standardization

Status: **done, superseded by Round 2**. Round 1 (below) promoted everything
into `~/.spl/tool_apis/` TOOL_API libraries under a `spl_*` naming scheme.
Round 2 discovered a real built-in stdlib already exists (`spl/stdlib.py`,
auto-loaded, no promote step) with significant overlap, and Wen redirected:
merge everything into real stdlib instead, dropping the `spl_*` prefix to
match the existing unprefixed style. **This is what actually shipped** — see
"Round 2 decisions" and "Round 3 — implementation" below. The
`cookbook/tools/stdlib_*.spl` TOOL_API library files from Round 1 were
deleted; nothing is promoted into `~/.spl/tool_apis/` anymore for this batch.

## Background

`~/.spl/tool_apis/` currently has only `stdlib_log.spl` promoted, but
`cookbook/tools/stdlib_*.spl` holds 5 stdlib libraries (`stdlib_log`,
`stdlib_io`, `stdlib_list`, `stdlib_finance`, `stdlib_media`) with
inconsistent naming — no shared prefix, and even `stdlib_log.spl` mixes
`spl_log` with `init_spl_log`. Goal: standardize on `spl_<category>_<action>`
so stdlib helpers are recognizable at a glance and distinguishable from
recipe-local tools.

Separately, several verification/checker recipes (numbered 78–94) each
duplicate the same small set of timing and result-JSON helpers inline
instead of sharing a stdlib version — a second promotion opportunity
discovered while cataloging.

## Final naming (locked in after review)

Wen's feedback resolved all open questions. This is the mapping actually
implemented — the tables further down are kept as the reviewed record but
are superseded by this section where they conflict.

| File (new) | Old name | Final name |
|---|---|---|
| stdlib_io.spl | `load_file` | `spl_io_read` |
| stdlib_io.spl | `write_file` | `spl_io_write` |
| stdlib_list.spl | `get_item` | `spl_list_get_item` |
| stdlib_list.spl | `get_list_length` | `spl_length` (generic — list/set/dict/string, like Python `len()`) |
| stdlib_list.spl | `list_append` | `spl_list_append` |
| stdlib_list.spl | `list_count` | `spl_list_count` |
| stdlib_fin.spl (renamed from stdlib_finance.spl) | `extract_risk_rating` | `spl_fin_risk_rating` |
| stdlib_json.spl (new — split out, generic) | `extract_json_field` | `spl_json_field_get` |
| stdlib_alert.spl (new — split out, generic) | `send_alert` | `spl_alert` |
| stdlib_audio.spl (new — split from stdlib_media.spl) | `convert_audio` | `spl_audio_convert` |
| stdlib_audio.spl | `trim_audio` | `spl_audio_trim` |
| stdlib_audio.spl | `get_audio_duration` | `spl_audio_duration` |
| stdlib_image.spl (new — split from stdlib_media.spl) | `convert_image` | `spl_image_convert` |
| stdlib_image.spl | `resize_image` | `spl_image_resize` |
| stdlib_image.spl | `image_info` | `spl_image_info` |
| stdlib_video.spl (new — split from stdlib_media.spl) | `extract_audio` | `spl_video_extract_audio` |
| stdlib_video.spl | `extract_frame` | `spl_video_extract_frame` |
| stdlib_video.spl | `get_video_duration` | `spl_video_duration` |
| stdlib_video.spl | `video_info` | `spl_video_info` |
| stdlib_log.spl | `init_spl_log` | `spl_log_init` |
| stdlib_log.spl | `spl_log` | `spl_log` (unchanged — log is both category and action) |
| stdlib_time.spl (new, Group B) | `now_ts` | `spl_time_now` |
| stdlib_time.spl | `elapsed_secs` | `spl_time_elapsed` |
| stdlib_time.spl | `monotonic_now` | `spl_time_monotonic` |
| stdlib_result.spl (new, Group B) | `get_status` | `spl_result_status` |
| stdlib_result.spl | `get_error` | `spl_result_error` |
| stdlib_result.spl | `is_ok` | `spl_result_ok` |

`stdlib_media.spl` is retired (split into audio/image/video). `stdlib_finance.spl`
retired in favor of `stdlib_fin.spl` + `stdlib_json.spl` + `stdlib_alert.spl`.

Shadow-exception files (`65_llm_splc/llm_splc.spl`, `72_verify_arxiv_references`,
`22_text2spl_demo/.../review_agent.spl`, `pocketflow/042_nodejs_upgrade_agent/tools.spl`,
`47_arxiv_morning_brief/tools.spl`) are deferred — left untouched in this pass.
This only affects their own local `get_item`/`list_count`/`load_file`/`write_file`
definitions and same-file calls to them; other call sites elsewhere in the repo
are renamed normally.

Group A and Group B land together, in one pass.

## Group A — existing stdlib functions to rename

| File | Current name | Proposed name | CALL sites (.spl, excl. self) | Shadow exceptions (leave alone — local recipe tool of the same name) |
|---|---|---|---|---|
| stdlib_io | `load_file` | `spl_io_load_file` | 2 | `cookbook/65_llm_splc/llm_splc.spl` |
| stdlib_io | `write_file` | `spl_io_write_file` | 74 | `cookbook/65_llm_splc/llm_splc.spl` |
| stdlib_list | `get_item` | `spl_list_get_item` | ~11 | `72_verify_arxiv_references`, `22_text2spl_demo/.../review_agent.spl`, `pocketflow/042_nodejs_upgrade_agent/tools.spl` |
| stdlib_list | `get_list_length` | `spl_list_length` | 3 | — |
| stdlib_list | `list_append` | `spl_list_append` | 9 | — |
| stdlib_list | `list_count` | `spl_list_count` | ~7 | `72_verify_arxiv_references`, `47_arxiv_morning_brief/tools.spl`, `pocketflow/042_nodejs_upgrade_agent/tools.spl` |
| stdlib_finance | `extract_risk_rating` | `spl_finance_risk_rating` | 3 | — |
| stdlib_finance | `extract_json_field` | `spl_json_get_field` (generic, not finance-specific — consider moving out of stdlib_finance) | 3 | — |
| stdlib_finance | `send_alert` | `spl_finance_send_alert` | 3 | — |
| stdlib_media | `convert_audio` | `spl_media_convert_audio` | 2 | — |
| stdlib_media | `trim_audio` | `spl_media_trim_audio` | 1 | — |
| stdlib_media | `get_audio_duration` | `spl_media_audio_duration` | 1 | — |
| stdlib_media | `convert_image` | `spl_media_convert_image` | 2 | — |
| stdlib_media | `resize_image` | `spl_media_resize_image` | 1 | — |
| stdlib_media | `image_info` | `spl_media_image_info` | 1 | — |
| stdlib_media | `extract_audio` | `spl_media_extract_audio` | 2 | — |
| stdlib_media | `extract_frame` | `spl_media_extract_frame` | 2 | — |
| stdlib_media | `get_video_duration` | `spl_media_video_duration` | 1 | — |
| stdlib_media | `video_info` | `spl_media_video_info` | 1 | — |
| stdlib_log | `init_spl_log` | `spl_log_init` | 2 | — |
| stdlib_log | `spl_log` | `spl_log_write` | 2 | — |

`write_file` is the dominant cost at 74 call sites; everything else is 1–11
files.

[WEN] isn't it implied that `load_file` and `write_file` operate on files, let us rename to `spl_io_read` and `spl_io_write`?

[WEN] shorten `finance` to `fin`

[WEN] isn't `send_alert` generic? let us call it `spl_alert`

[WEN] unnecessary to add extra `media` layer, let us name as `spl_audio_<action>`, same for spl_image_<action> and spl_video_<action>

[WEN] keep `spl_log` here `log` is interpreted as both category and action







### Shadow exceptions — why they're excluded

A handful of recipes define their own local `CREATE TOOL_API` with the same
name as a stdlib function, but a different, recipe-specific implementation.
Since TOOL_API resolution is per-file (no cross-file namespace collision),
these are unrelated to the stdlib versions and must not be touched by the
rename:

- `load_file`, `write_file` — locally redefined in `cookbook/65_llm_splc/llm_splc.spl`
- `get_item` — locally redefined in `cookbook/72_verify_arxiv_references/verify_arxiv_references.spl`, `cookbook/22_text2spl_demo/generated-20260527_222233/review_agent.spl`, `cookbook-pocketflow/042_nodejs_upgrade_agent/tools.spl`
- `list_count` — locally redefined in `cookbook/72_verify_arxiv_references/verify_arxiv_references.spl`, `cookbook/47_arxiv_morning_brief/tools.spl`, `cookbook-pocketflow/042_nodejs_upgrade_agent/tools.spl`

[WEN] we will deal with this categoy of refactoring later at lower priority

## Group B — new promotion candidates (currently duplicated inline)

Discovered while reviewing SOLVER-result-checking recipes: the same six
helpers are hand-copied into ~13–14 recipe `.spl` files (numbered
78_constraint_opt through 94_data_eng_text2spl) instead of living in
stdlib.

| Duplicated helper | Proposed stdlib name | Recipes with local copy |
|---|---|---|
| `now_ts()` | `spl_time_now` | 14 |
| `elapsed_secs(start_ts)` | `spl_time_elapsed` | 14 |
| `monotonic_now()` | `spl_time_monotonic` | 14 |
| `get_status(result_json)` | `spl_result_status` | 13 |
| `get_error(result_json)` | `spl_result_error` | 13 |
| `is_ok(result_json)` | `spl_result_ok` | 9 |

Recipes with local copies (base dirs, excluding `mermaid/` duplicates):

`78_constraint_opt`, `79_code_pytest`, `81_graph_reasoning`,
`82_logic_puzzle_solver`, `83_unit_dimensional_check`, `84_sql_verifier`,
`85_property_based_code_verify`, `86_financial_calc_verifier`,
`87_route_optimization`, `90_compsci_physics`, `91_compsci_chemistry`,
`92_compsci_materials`, `93_auto_planning`, `94_data_eng_text2spl`
(`is_ok` only present in a subset of these).

This group is a pure win: deleting duplicated inline definitions and
replacing with `CALL spl_time_now()` etc. reduces code, not just renames it.

[WEN] proceed as planned for this category of refactoring



## Proposed plan (pending go-ahead)

1. Rename definitions in the 5 `cookbook/tools/stdlib_*.spl` files, keeping
   each function's implementation unchanged — only the `CREATE TOOL_API`
   name and the matching top-level `def` name change. Re-promote
   (`spl3 tool-api promote ... --force`) into `~/.spl/tool_apis/`.
2. Create `cookbook/tools/stdlib_time.spl` and `cookbook/tools/stdlib_result.spl`
   for Group B, using the `spl_time_*` / `spl_result_*` names above, and
   promote them.
3. Rewrite `CALL` sites repo-wide per the Group A table, skipping the shadow
   exception files/functions listed above.
4. Delete the 13–14 inline duplicate definitions in Group B recipes and
   replace with `CALL spl_time_now()` / `CALL spl_result_status(...)` / etc.

[WEN] yes to 1-4

## Open questions for review

- `spl_json_get_field`: it's a generic JSON helper living in
  `stdlib_finance.spl` for historical reasons. Move it to a new
  `stdlib_json.spl` (or existing `stdlib_list.spl`?) while renaming, or leave
  it in `stdlib_finance` under the new name and accept the mild
  mis-categorization?

[WEN] it should be renamed as `spl_json_field_get` and `spl_json_field_set`

- Any preference on verb order — e.g. `spl_log_init` vs `spl_init_log`,
  `spl_list_length` vs `spl_length_list`? Table above assumes
  `spl_<category>_<action>` throughout.

[WEN] 
    - we should use `spl_<category>_<action>` as much as possible
    - it should be spl_log_init
    - we should have `spl_length` it can operate on list, set, dict, string, as in python

- Group B naming: `spl_time_now` vs `spl_time_now_ts` (matches original
  `now_ts` more literally); `spl_result_ok` vs `spl_result_is_ok`.

[WEN] I prefer shorter version as in Unix

- Should Group A and Group B land as one PR/commit, or Group B first (pure
  addition, zero call-site risk) and Group A rename as a separate, riskier
  follow-up?

[WEN] in one go

---

## Round 2 — discovered: real built-in stdlib already exists

**This changes the plan.** `spl/stdlib.py` is SPL's actual built-in stdlib —
68 `@spl_tool` Python functions, auto-loaded into every executor at init
(`get_global_tools()` → `_GLOBAL_TOOLS`), zero setup, no promote step. This is
different from `cookbook/tools/stdlib_*.spl` (TOOL_API libraries), which only
become available after a manual `spl3 tool-api promote` into
`~/.spl/tool_apis/` — a per-machine, non-git-tracked step that has already
caused a real incident (`docs/DEV/ISSUES/run_all_test-2026-06-21.md`, Fix 2 —
the promoted TOOL_API `write_file` silently shadowed the real 3-param stdlib
`write_file` and broke append-mode recipes; Fix 6 — `spl_log` simply wasn't
promoted yet on a fresh run).

Wen's direction: move tonight's `spl_*` additions into real stdlib
(`spl/stdlib.py`) so they're auto-loaded like the 68 below — add any new
runtime dependency (ffmpeg, Pillow) to `requirements.txt` rather than keeping
media functions TOOL_API-only. Precedent for stdlib functions with optional
external deps already exists: `web_search` requires `pip install ddgs`,
`http_get` requires `pip install requests` — both documented inline via a
"Requires:" docstring line rather than a hard top-of-file import.

### Existing real stdlib (spl/stdlib.py) — full catalog

| Function | Docstring |
|---|---|
| `to_int(value)` | CAST(value AS INTEGER) |
| `to_float(value)` | CAST(value AS FLOAT) |
| `to_text(value)` | CAST(value AS TEXT) |
| `to_bool(value)` | CAST(value AS BOOLEAN) |
| `upper(value)` | UPPER(value) |
| `lower(value)` | LOWER(value) |
| `trim(value)` | TRIM(value) |
| `ltrim(value)` | LTRIM(value) |
| `rtrim(value)` | RTRIM(value) |
| `length(value)` | LENGTH(value) — char count |
| `len_val(value)` | LEN(value) — polymorphic: string chars, JSON array items, or JSON object keys |
| `substr(value, start, length="-1")` | SUBSTR — 1-based |
| `replace(value, old, new)` | REPLACE |
| `concat(*args)` | CONCAT |
| `instr(value, search)` | INSTR — 1-based index, 0 if not found |
| `lpad(value, width, fill=" ")` | LPAD |
| `rpad(value, width, fill=" ")` | RPAD |
| `split_part(value, delimiter, part, trim="true")` | SPLIT_PART — 1-based |
| `reverse(value)` | REVERSE |
| `like(value, pattern)` | SQL LIKE (%, _) |
| `startswith(value, prefix)` | → 'true'/'false' |
| `endswith(value, suffix)` | → 'true'/'false' |
| `contains(value, substring)` | → 'true'/'false' |
| `regexp_match(value, pattern)` | → 'true' if matches anywhere |
| `abs_val(value)` | ABS |
| `round_val(value, decimals="0")` | ROUND |
| `ceil_val(value)` | CEIL |
| `floor_val(value)` | FLOOR |
| `mod_val(dividend, divisor)` | MOD |
| `power_val(base, exponent)` | POWER |
| `sqrt_val(value)` | SQRT |
| `sign_val(value)` | -1/0/1 |
| `clamp(value, lo, hi)` | constrain to [lo, hi] |
| `coalesce(*args)` | first non-null/non-empty |
| `nullif(value, compare)` | '' if equal, else value |
| `iif(condition, true_val, false_val)` | inline if |
| `isnull(value)` | → 'true' if None/empty |
| `nvl(value, default)` | Oracle-style default |
| `isblank(value)` | → 'true' if empty/whitespace |
| `word_count(value)` | whitespace-delimited tokens |
| `char_count(value)` | chars excluding whitespace |
| `line_count(value)` | newline-separated lines |
| `json_get(json_str, key)` | extract top-level key |
| `json_set(json_str, key, value)` | set top-level key |
| `json_keys(json_str)` | comma-separated top-level keys |
| `json_pretty(json_str)` | pretty-print, 2-space indent |
| `now_iso()` | current UTC ISO-8601 datetime |
| `date_format_val(iso_date, fmt)` | strftime reformat |
| `date_diff_days(date_a, date_b)` | days between two ISO dates |
| `md5_hash(value)` | MD5 hex digest |
| `sha256_hash(value)` | SHA-256 hex digest |
| `list_get(value, index, delimiter=",")` | 1-based element |
| `list_length(value, delimiter=",")` | element count |
| `list_join(value, old_delim, new_delim)` | re-join with new delimiter |
| `list_contains(value, item, delimiter=",")` | → 'true'/'false' |
| `trim_turns(history, max_turns)` | keep last N User/Assistant turn pairs |
| `write_file(file_path, content, mode="w")` | write text to file |
| `read_file(file_path)` | read entire text file |
| `file_exists(file_path)` | → 'true'/'false' |
| `make_dir(dir_path)` | mkdir -p |
| `path_join(*parts)` | OS-separator join |
| `web_search(query)` | DuckDuckGo top-5 (requires `pip install ddgs`) |
| `search_web(query)` | (alias/variant of web_search — check for duplication) |
| `http_get(url, timeout="10")` | fetch URL body (requires `pip install requests`; docstring marks it **deprecated**, scheduled for removal in spl-llm v3.2, in favor of `CREATE TOOL_API` + `import requests`) |
| `run_python(code, timeout="30")` | exec Python in subprocess (docstring marks it **deprecated** too, same v3.2 removal note — kernel-mode `CREATE TOOL_API` is the replacement) |
| `cache_get(concept, rubric_version="v1", params_json="{}")` | Layer 2 content cache read |
| `cache_put(concept, content, badges="", rubric_version="v1", params_json="{}", token_cost="0", verifier="", statement="")` | Layer 2 content cache write |
| `cache_promote(concept, badge, statement="", rubric_version="v1", params_json="{}")` | add trust badge to cache entry |

### Cross-check against tonight's `spl_*` additions

| Tonight's function | Status vs. real stdlib | Action needed |
|---|---|---|
| `spl_io_write` | **Duplicate** of `write_file` (same signature already) | Delete; revert call sites to `write_file` |
| `spl_io_read` | **Duplicate** of `read_file` | Delete; revert call sites to `read_file` |
| `spl_list_get_item` | **Duplicate** of `list_get` (real one is 1-based + delimiter-aware, same idea) | Delete; revert call sites to `list_get` — check 1-based vs 0-based index convention before reverting, tonight's was 0-based |
| `spl_length` | **Duplicate** of `list_length` / `len_val` (`len_val` already covers list/dict/string polymorphically — exactly what was asked for) | Delete; revert call sites to `len_val` or `list_length` depending on need |
| `spl_json_field_get` | **Near-duplicate** of `json_get` | Delete; revert call sites to `json_get` |
| `spl_list_append` | No equivalent | Genuine gap — promote into `spl/stdlib.py` |
| `spl_list_count` | No equivalent (`list_contains` only returns true/false, not a count) | Genuine gap — promote into `spl/stdlib.py` |
| `spl_log_init`, `spl_log` | No equivalent | Genuine gap — promote into `spl/stdlib.py` |
| `spl_time_now`, `spl_time_elapsed`, `spl_time_monotonic` | `now_iso()` exists but different format/purpose (ISO datetime vs. filesystem-safe timestamp / monotonic elapsed) — no true overlap | Genuine gap — promote into `spl/stdlib.py` |
| `spl_result_status`, `spl_result_error`, `spl_result_ok` | Expressible via `json_get(json, "status")` + `coalesce`, but no direct equivalent for the try/except-safe parse-or-default behavior | Borderline — worth keeping as dedicated stdlib functions for the ASSERT-gate ergonomics, or fold into a `json_get`-based EVALUATE pattern in recipes instead |
| `spl_fin_risk_rating`, `spl_alert` | No equivalent, domain-specific (finance) | Promote into `spl/stdlib.py` per Wen's direction (was previously going to stay TOOL_API-only) |
| `spl_audio_*`, `spl_image_*`, `spl_video_*` | No equivalent, requires ffmpeg (system binary, not pip) / Pillow | Promote into `spl/stdlib.py` per Wen's direction — add `Pillow` to `requirements.txt`; ffmpeg is a system binary so still needs a docstring "Requires: ffmpeg" note (same pattern as run_python needing no extra pip package but external tooling) |

### Naming cleanup needed in the real stdlib (Wen: "clean up its naming")

Open for your `[WEN]` tags:

- `search_web` vs `web_search` — two names for what looks like the same thing. Confirm if `search_web` is a true duplicate to remove, or a distinct legacy alias kept for back-compat.
- `length` vs `len_val` vs `list_length` vs `char_count` — four length-flavored functions with overlapping purpose (`length`/`char_count` are near-identical; `len_val` is the polymorphic one`; `list_length` is delimiter-list-specific). Worth consolidating naming so it's obvious which to reach for.
- `abs_val`, `round_val`, `ceil_val`, `floor_val`, `sqrt_val`, `sign_val`, `power_val`, `mod_val` — the `_val` suffix throughout numeric functions seems to exist only to avoid shadowing Python builtins (`abs`, `round`, etc.) inside the module. Keep as-is, or is this also up for renaming?
- `http_get` and `run_python` are marked deprecated in their own docstrings (removal scheduled for spl-llm v3.2) — flag in case that's news, or already known/planned.
- Once tonight's `spl_*` set moves into `spl/stdlib.py`, should they keep the `spl_` prefix (for discoverability / consistency with what's already promoted-and-familiar from tonight), or drop it to match the un-prefixed style of the existing 68 (`write_file`, `list_get`, etc.)? This is the single biggest naming call left — it decides whether the whole `spl_<category>_<action>` scheme from Round 1 survives the merge into real stdlib.

[WEN] 
- use `web_search`
- use `length` for collection including string (as in python)
- in general, keep what exists in stdlib, drop anything we added tonight if already exists in real std

### Round 2 decisions (consolidated)

1. **`search_web` retired in favor of `web_search`** — true duplicate, one survives.
2. **`length` becomes the single polymorphic length function** (string chars /
   JSON array items / JSON object keys — Python `len()` semantics), absorbing
   `len_val`'s implementation. `len_val` is retired as redundant.
   `list_length` (delimited-list-specific) and `char_count`
   (whitespace-excluding count) are semantically distinct from this and stay
   as-is — not part of this consolidation.
3. **Any of tonight's `spl_*` functions that duplicate an existing real-stdlib
   function is dropped**, call sites revert to the real name:
   - `spl_io_write` → dropped, call sites → `write_file`
   - `spl_io_read` → dropped, call sites → `read_file`
   - `spl_list_get_item` → dropped, call sites → `list_get` (index-convention
     fix needed: tonight's was 0-based, real `list_get` is 1-based)
   - `spl_length` → dropped, call sites → `length` (once consolidated per #2)
   - `spl_json_field_get` → dropped, call sites → `json_get`
   - Consequence: `stdlib_io.spl` and `stdlib_json.spl` become empty and are
     deleted; `stdlib_list.spl` keeps only `spl_list_append`/`spl_list_count`.
4. **Genuine gaps move into `spl/stdlib.py`** as real `@spl_tool` functions
   (auto-loaded, no promote step), per the "add deps to requirements.txt"
   direction: `spl_list_append`, `spl_list_count`, `spl_log_init`/`spl_log`,
   `spl_time_now`/`spl_time_elapsed`/`spl_time_monotonic`,
   `spl_result_status`/`spl_result_error`/`spl_result_ok`,
   `spl_fin_risk_rating`, `spl_alert`, `spl_audio_*`/`spl_image_*`/`spl_video_*`
   (add `Pillow` to `requirements.txt`; ffmpeg stays a documented system-binary
   requirement, same pattern as other stdlib functions with external deps).

### Still open — naming of the new functions once merged

Not yet answered: should the genuine-gap functions above keep the `spl_`
prefix, or drop it to match the existing 68's unprefixed style
(`write_file`, `list_get`, `json_get`, ...)? This decides every one of their
final names before implementation — asking directly before proceeding.

Answered: **drop the prefix**, match the existing style.

## Round 3 — implementation (what actually shipped)

`spl/stdlib.py` changes:

- `length(value)` — merged `len_val`'s polymorphic body in (JSON array/object
  → item/key count, else string chars). `len_val` deleted (0 call sites).
- `list_get(value, index, delimiter=",")` — now tries JSON-array parsing
  first, falls back to delimiter split. Still 1-based. (`spl_list_get_item`
  was 0-based; every call site got `+ 1` added during the rename, e.g.
  `CALL list_get(@urls, @i + 1) INTO @url`.)
- `json_get(json_str, key)` — now strips ```` ```json ```` / ```` ``` ````
  fences before parsing, so raw LLM output works directly.
- `search_web` deleted (was a pure alias for `web_search`); 10 call sites in
  `cookbook-pocketflow/` renamed to `web_search`.
- 22 new `@spl_tool` functions added: `list_append`, `list_count`, `log_init`,
  `log`, `time_now`, `time_elapsed`, `time_monotonic`, `result_status`,
  `result_error`, `result_ok`, `fin_risk_rating`, `alert`, `audio_convert`,
  `audio_trim`, `audio_duration`, `image_convert`, `image_resize`,
  `image_info`, `video_extract_audio`, `video_extract_frame`,
  `video_duration`, `video_info`. Total stdlib: 88 functions (was 68).

`pyproject.toml` — added a `media` optional-dependency extra (`Pillow>=10.0`)
for `image_*`; `audio_*`/`video_*` still require the `ffmpeg` system binary,
documented in each function's docstring (same pattern as `run_python`).

Deleted: all 11 `cookbook/tools/stdlib_*.spl` files from Round 1, and their
promoted copies in `~/.spl/tool_apis/` (via `spl3 tool-api remove`).

Repo-wide: 117 `.spl` files under `cookbook/`/`cookbook-pocketflow/` had
`spl_*` names rewritten to the final unprefixed names (simple 1:1 rename for
everything except `list_get`, which needed the index-base fix above).
Verified: module imports cleanly, all 88 tools register via
`get_global_tools()`, smoke-tested `length`/`list_get`/`json_get`/
`list_append`/`list_count`/`time_*`/`result_*`/`fin_risk_rating`/`alert`/
`log_init`/`log` directly, and `spl3 validate` on a sample of touched
recipes shows no new errors (only pre-existing linter warnings that don't
resolve stdlib CALL targets at all — same warnings appear for calls to
long-standing stdlib functions too).

Documented in `docs/GUIDE/USER-GUIDE.md` §4.5 "Standard library & adding
your own tools": explains the two-layer model (real stdlib vs. promoted
TOOL_API libraries), the last-write-wins load-order shadowing risk, the
naming rule (prefix your own TOOL_API helpers to avoid colliding with
current/future stdlib names — unprefixed is reserved for real stdlib), and
that generic helpers should go through a PR into `spl/stdlib.py` rather than
staying as a personally-promoted library.

Not committed yet — pending review.

