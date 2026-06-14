## Summary

This workflow parses an unstructured resume text file into structured YAML data — extracting name, email, work experience, and matching skill indexes against a predefined skill list. It exists to automate the tedious first step of candidate screening: turning a raw text resume into a machine-readable record. Recruiters, ATS integrations, and downstream analytics pipelines all benefit from this normalized output.

---

## Detailed Specification

### 1. Purpose

Given a plain-text resume and a target skill list, extract structured candidate data (name, email, experience entries, and matched skill indexes) into a validated YAML document.

---

### 2. High-level Description

This workflow implements the **structured output** pattern: a single GENERATE call whose prompt enforces a rigid YAML schema, rather than relying on model-native JSON mode. The sole logical function — `ResumeParser` — receives two inputs from shared state: the raw resume text and an indexed list of target skills. Its prompt instructs the LLM to emit *only* YAML, annotated with inline comments that explain each field's source in the resume, with `skill_indexes` expressed as a list of integers drawn from the provided skill index table. The LLM response is extracted from a fenced code block, parsed with a YAML parser, and validated by asserting the presence of `name` and `email` fields; if parsing or validation fails, the node retries up to three times with a ten-second wait (equivalent to an SPL EXCEPTION WHEN `ParseError` handler wrapping the GENERATE call). After a successful parse, a CALL side-effect writes the structured YAML to disk and echoes a formatted summary to stdout. Because all control flow is linear — one node, one LLM call, one output — there are no WHILE loops or EVALUATE branches; the only non-trivial control flow is the retry-on-exception path.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW ResumeParser` | `Flow(start=ResumeParserNode(...)).run(shared)` | Top-level orchestration entry point |
| `CREATE FUNCTION resume_parser_prompt` | `ResumeParserNode.exec()` inline f-string | Embeds `{resume_text}` and `{skill_list}` slots |
| `GENERATE resume_parser_prompt(...) INTO @structured_data` | `call_llm(prompt)` → YAML parse → `exec_res` | Single LLM call; result is the parsed YAML dict |
| `EXCEPTION WHEN ParseError THEN` | `Node(max_retries=3, wait=10)` + implicit retry on `AssertionError` / YAML parse failure | Retry-on-exception is the only non-trivial control flow |
| `CALL write_file(@structured_data) INTO @_` | `Path(out).write_text(yaml.dump(...))` in `main()` post-run | Side-effect; persists YAML to disk |
| `@resume_text`, `@target_skills`, `@structured_data` | `shared["resume_text"]`, `shared["target_skills"]`, `shared["structured_data"]` | PocketFlow shared dict = SPL `@var` namespace |
| `INPUT: resume_text TEXT, target_skills LIST` | CLI `--input` path + `DEFAULT_SKILLS` constant | Boundary inputs resolved before workflow starts |
| `OUTPUT: structured_data YAML` | `shared["structured_data"]` + `--out` file path | Final artifact; also echoed to stdout |

*(No `RETURN WITH status=` row: this is a single-node linear flow; the only exit is success or exhausted retries.)*

---

### 4. Logical Functions / Prompts

#### `resume_parser_prompt`

- **Role:** The sole LLM call in the workflow. Transforms unstructured resume prose into a YAML object with candidate identity fields, work history, and skill index matches.
- **Key prompt conventions:**
  - Opens with `"Output ONLY YAML"` sentinel — suppresses any prose preamble that would break downstream YAML parsing.
  - Provides the skill list as a numbered index table (`0: Team leadership`, `1: CRM software`, …) so the model can reference skills by integer index rather than free text, avoiding string-match normalization.
  - Includes an inline YAML template with `# comment` placeholders to teach the model both the output schema and the annotation convention in a single shot.
  - Response is extracted from a `\`\`\`yaml … \`\`\`` fenced block — the sentinel pair `split("```yaml")[1].split("```")[0]` is the extraction boundary.
  - Structural validation is a two-field assertion: `"name" in result and "email" in result` — minimal guard against hallucinated or truncated output.

---

### 5. Control Flow

```
START
  → load resume_text from file, populate target_skills list
  → GENERATE resume_parser_prompt(resume_text, target_skills) INTO @structured_data
      [on YAML parse failure or missing required fields]
      → EXCEPTION WHEN ParseError THEN retry (up to 3×, 10 s backoff)
      [on 3rd failure] → abort with error
  → CALL write_yaml(@structured_data, out_path)   -- side-effect
  → normalize skill_indexes (int vs dict format)
  → print matched skills to stdout
END
```

The retry-on-exception path is the only branch. There are no WHILE loops (quality gates) or EVALUATE branches (semantic routing). The flow is: one call, validate, write, done.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 2 above as text2spl input)
spl3 text2spl --description "Given a plain-text resume and an indexed target skill list, \
extract structured candidate data (name, email, experience entries, and matched skill indexes) \
into a validated YAML document using a single GENERATE call with a strict YAML-only prompt. \
Include EXCEPTION WHEN ParseError with 3 retries, and a CALL side-effect to write the output \
to disk." --mode workflow

# Step 2 — compile to any target
spl3 splc compile resume_parser.spl --lang python/pocketflow
spl3 splc compile resume_parser.spl --lang python/langgraph
spl3 splc compile resume_parser.spl --lang go
```