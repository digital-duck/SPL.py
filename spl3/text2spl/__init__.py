"""Natural language to SPL source code compiler.

Uses an LLM adapter to convert natural language task descriptions
into valid SPL source code.
"""

from __future__ import annotations

import logging

from spl.adapters.base import LLMAdapter
from spl.lexer import Lexer, LexerError
from spl.analyzer import Analyzer, AnalysisError
from spl3.parser import SPL3Parser

_log = logging.getLogger("spl3.text2spl")


SPL2_SYSTEM_PROMPT = """\
You are an expert SPL 3.0 code generator. SPL 3.0 (Structured Prompt Language) is \
a declarative language for orchestrating hybrid deterministic + LLM workflows. \
Given a natural language description of a task, you produce a single self-contained \
SPL 3.0 source file.

Return ONLY the raw SPL 3.0 code. Do not include markdown fences, explanations, \
or commentary.

== REGIME CLASSIFICATION — DO THIS FIRST ==

Before writing any construct, classify each operation in the task:

  DETERMINISTIC (single correct answer expressible as Python code)?
    → CREATE TOOL_API ... AS PYTHON $$ ... $$  +  CALL
  PROBABILISTIC (requires reasoning, judgment, or text generation)?
    → CREATE FUNCTION ... AS $$ <prompt> $$    +  GENERATE

Classical / deterministic — ALWAYS use TOOL_API:
  external API call, HTTP request, data fetch, math/statistics, string manipulation,
  data transformation, file I/O, sorting/filtering, format conversion, any operation
  a developer could unit-test with an exact expected value.

Probabilistic — use CREATE FUNCTION:
  summarization, interpretation, nuanced classification, text generation,
  quality judgment, any operation where "correct" requires reasoning.

Using GENERATE for a deterministic operation is a category error. Use the right regime.

== FILE STRUCTURE (always in this order) ==

1. CREATE TOOL_API blocks   -- deterministic Python tools
2. CREATE FUNCTION blocks   -- LLM prompt templates
3. WORKFLOW block

== SPL 3.0 SYNTAX REFERENCE ==

--- CREATE TOOL_API (deterministic / classical regime) ---

CREATE TOOL_API <name>(<param> TEXT, ...) RETURNS TEXT AS PYTHON $$
import needed_library
def <name>(<param>: str, ...) -> str:
    try:
        # real implementation
        return result_as_string
    except Exception as e:
        return f"error: {e}"
$$;

Rules:
- Every parameter and return value is str.
- The function name inside $$ MUST match the TOOL_API name.
- Return "error: <msg>" on failure — no unhandled exceptions.
- All imports go inside the $$ body.
- Use '' (two single quotes) for apostrophes inside $$ bodies.

--- CREATE FUNCTION (probabilistic / LLM regime) ---

CREATE FUNCTION <name>(<param> TYPE, ...) RETURNS TYPE AS $$
  <natural language prompt — use {param} template slots>
$$;

Rules:
- Parameters have NO @ prefix.
- Use {param} (curly braces) for template slots inside $$ bodies.
- Use '' (two single quotes) for apostrophes inside $$ bodies.

--- WORKFLOW ---

WORKFLOW <name>
  INPUT @<var> <TYPE> := <default>, ...
  OUTPUT @<var> <TYPE>
DO
  -- body
END;

Rules:
- No semicolons after INPUT or OUTPUT lines.
- No nested DO...END; block — DO opens and END; closes the WORKFLOW.

--- Key constructs inside WORKFLOW bodies ---

Variable assignment:     @var := expression;
Deterministic tool call: CALL <tool_api>(@arg1, @arg2) INTO @var;
LLM call:                GENERATE <function>(@arg) INTO @var;
Return:                  RETURN @var WITH status = 'complete';

Conditional branching:
  EVALUATE @var
    WHEN contains('token') THEN
      <statements>
    ELSE
      <statements>
  END;

Looping:
  WHILE @i < @max_iterations DO
    <statements>
    @i := @i + 1;
  END;
  Never hardcode iteration limits. Always:  INPUT @max_iterations INTEGER := N

Exception handling:
  DO
    <statements>
  EXCEPTION
    WHEN <ExceptionType> THEN <statements>
  END;

--- Exception types ---
HallucinationDetected, RefusalToAnswer, ContextLengthExceeded,
ModelOverloaded, QualityBelowThreshold, MaxIterationsReached,
BudgetExceeded, NodeUnavailable

--- Condition syntax ---
Numeric/boolean: @var > 0.8, @var = 'done', @count < 5  (use = not ==)
String content:  EVALUATE @var WHEN contains('token') THEN ...

== STRICT RULES ==

1. RETURN only at the TOP LEVEL of the WORKFLOW body — never inside WHILE or EVALUATE.
   For quality-gated loops: set @i := @max_iterations inside EVALUATE to force exit,
   then RETURN after the loop.

2. Score / numeric comparisons: never use contains("0.8").
   Always gate via a CREATE FUNCTION that returns a categorical token ("done"/"continue"),
   then EVALUATE that token.

3. EVALUATE WHEN clauses use contains() only — never comparison operators.

4. WHILE is for numeric/boolean guards. EVALUATE is for string/semantic branching.

5. @ sigil: ONLY for workflow-level variables (INPUT, OUTPUT, := assignments).
   CREATE FUNCTION / CREATE TOOL_API parameter names have NO @ prefix.

== EXAMPLES ==

Example 1 -- Pure LLM workflow (self-refine loop):

CREATE FUNCTION draft(task TEXT) RETURNS TEXT AS $$
  Write a first draft response to: {task}
$$;

CREATE FUNCTION critique(current TEXT) RETURNS TEXT AS $$
  Review the following and reply with exactly [APPROVED] if no improvements are needed,
  otherwise provide specific actionable feedback.
  Content: {current}
$$;

CREATE FUNCTION refine(current TEXT, feedback TEXT) RETURNS TEXT AS $$
  Improve the following based on the feedback provided.
  Draft: {current}
  Feedback: {feedback}
$$;

WORKFLOW self_refine
  INPUT @task TEXT, @max_iterations INTEGER := 3
  OUTPUT @result TEXT
DO
  @iteration := 0;
  GENERATE draft(@task) INTO @current;
  WHILE @iteration < @max_iterations DO
    GENERATE critique(@current) INTO @feedback;
    EVALUATE @feedback
      WHEN contains('[APPROVED]') THEN
        @iteration := @max_iterations;
      ELSE
        @iteration := @iteration + 1;
        GENERATE refine(@current, @feedback) INTO @current;
    END;
  END;
  RETURN @current WITH status = 'complete', iterations = @iteration;
EXCEPTION
  WHEN BudgetExceeded THEN
    RETURN @current WITH status = 'budget_limit';
END;

Example 2 -- Mixed regime (deterministic data fetch + LLM interpretation):

CREATE TOOL_API get_item(items TEXT, idx TEXT) RETURNS TEXT AS PYTHON $$
def get_item(items: str, idx: str) -> str:
    return [x.strip() for x in items.split(',')][int(idx)]
$$;

CREATE TOOL_API fetch_data(ticker TEXT, years TEXT) RETURNS TEXT AS PYTHON $$
import yfinance as yf, pandas as pd
def fetch_data(ticker: str, years: str) -> str:
    try:
        end = pd.Timestamp.today()
        start = end - pd.DateOffset(years=float(years))
        df = yf.download(ticker, start=start, end=end, auto_adjust=True)
        return 'error: no data' if df.empty else df.to_csv()
    except Exception as e:
        return f'error: {e}'
$$;

CREATE FUNCTION interpret(ticker TEXT, data TEXT) RETURNS TEXT AS $$
  Analyze the OHLCV data for {ticker} and write a 2-sentence summary
  covering trend direction and key risk. Data: {data}
$$;

WORKFLOW market_report
  INPUT @tickers TEXT := 'GOOG,META,MSFT'
  INPUT @years TEXT := '2'
  INPUT @max_tickers INTEGER := 3
  OUTPUT @report TEXT
DO
  @i := 0;
  @report := '';
  WHILE @i < @max_tickers DO
    CALL get_item(@tickers, @i) INTO @ticker;
    CALL fetch_data(@ticker, @years) INTO @data;
    GENERATE interpret(@ticker, @data) INTO @summary;
    @report := @report + @ticker + ': ' + @summary + '\n';
    @i := @i + 1;
  END;
  RETURN @report WITH status = 'complete';
END;

Example 3 -- Classification with exception handling (LLM only):

WORKFLOW safe_classify
  INPUT @text TEXT
  OUTPUT @label TEXT
DO
  DO
    GENERATE classify(@text) INTO @label;
    RETURN @label WITH status = 'complete';
  EXCEPTION
    WHEN HallucinationDetected THEN
      @label := 'unknown';
      RETURN @label WITH status = 'fallback';
    WHEN ModelOverloaded THEN
      RETRY;
  END;
END;
"""


_EXAMPLES_MARKER = "== EXAMPLES =="


_MODE_INSTRUCTIONS = {
    "prompt": (
        "Generate a single PROMPT statement. Do not use WORKFLOW or CREATE FUNCTION "
        "unless absolutely necessary for a helper."
    ),
    "workflow": (
        "Generate a WORKFLOW statement with full control flow. You may also emit "
        "CREATE FUNCTION statements if helper functions are needed."
    ),
    "auto": (
        "Decide whether the task is best expressed as a single PROMPT statement or "
        "a multi-step WORKFLOW (possibly with helper functions). Use PROMPT for "
        "simple one-shot tasks and WORKFLOW for anything that requires iteration, "
        "branching, or multiple generation steps."
    ),
}


class Text2SPL:
    """Compile natural language descriptions into SPL source code."""

    def __init__(
        self,
        adapter: LLMAdapter,
        max_retries: int = 2,
        code_rag=None,          # CodeRAGStore | None
        rag_top_k: int = 4,
        auto_capture: bool = True,
    ) -> None:
        self.adapter = adapter
        self.max_retries = max_retries
        self.code_rag = code_rag
        self.rag_top_k = rag_top_k
        self.auto_capture = auto_capture

    async def compile(self, description: str, mode: str = "auto") -> str:
        """Convert a natural language task description into SPL source code."""
        if mode not in _MODE_INSTRUCTIONS:
            raise ValueError(
                f"Invalid mode {mode!r}. Must be one of: "
                f"{', '.join(sorted(_MODE_INSTRUCTIONS))}"
            )

        system, user_prompt = self.build_prompt(description, mode)

        result = await self.adapter.generate(
            prompt=user_prompt,
            system=system,
            temperature=0.3,
        )

        spl_code = self._strip_fences(result.content.strip())

        # Compile-validate-retry loop: if the generated code is invalid,
        # feed the error back to the LLM for correction
        retry_count = 0
        for _ in range(self.max_retries):
            valid, message = self.validate_output(spl_code)
            if valid:
                break
            retry_count += 1
            _log.debug("Validation failed (attempt %d): %s", retry_count, message)
            fix_prompt = (
                f"The following SPL 2.0 code has an error:\n\n"
                f"```\n{spl_code}\n```\n\n"
                f"Error: {message}\n\n"
                f"Reminder of strict SPL conventions:\n"
                f"- CREATE FUNCTION parameters must NOT have @ prefix (only workflow variables use @)\n"
                f"- CREATE FUNCTION bodies use {{param}} template slots, not @param\n"
                f"- EVALUATE must target a variable: EVALUATE @var WHEN contains('...') THEN\n"
                f"- EVALUATE WHEN clauses use contains() for string matching — never comparison operators\n"
                f"- Numeric comparisons (>=, <, =) belong in WHILE conditions, not EVALUATE WHEN\n\n"
                f"Fix the error and return only the corrected SPL 2.0 code. "
                f"Do not include markdown fences or explanations."
            )
            fix_result = await self.adapter.generate(
                prompt=fix_prompt,
                system=system,
                temperature=0.2,
            )
            spl_code = self._strip_fences(fix_result.content.strip())

        # Auto-capture validated pair into Code-RAG for future retrieval
        valid, _ = self.validate_output(spl_code)
        if valid and self.auto_capture and self.code_rag is not None:
            try:
                self.code_rag.add_pair(
                    description=description,
                    spl_source=spl_code,
                    metadata={"source": "compile", "retries": retry_count},
                )
                _log.debug("Auto-captured pair into Code-RAG: %s", description[:60])
            except Exception as exc:
                _log.warning("Code-RAG auto-capture failed: %s", exc)

        return spl_code

    def build_prompt(self, description: str, mode: str = "auto") -> tuple[str, str]:
        """Construct the system and user prompts without calling the LLM.

        Returns:
            A (system_prompt, user_prompt) tuple.
        """
        if mode not in _MODE_INSTRUCTIONS:
            raise ValueError(f"Invalid mode {mode!r}")

        system = self._build_system_prompt(description)
        user_prompt = (
            f"Task: {description}\n\n"
            f"Mode instruction: {_MODE_INSTRUCTIONS[mode]}\n\n"
            "Generate the SPL 2.0 code now."
        )
        return system, user_prompt

    # ------------------------------------------------------------------
    # System prompt construction
    # ------------------------------------------------------------------

    def _build_system_prompt(self, description: str) -> str:
        """Build the system prompt, replacing static examples with RAG hits.

        Injection order (applied to the base prompt):
          1. Available TOOL_API tools (stdlib + registry) — injected before
             STRICT RULES so the LLM sees what already exists before deciding
             whether to generate CREATE TOOL_API.
          2. Code-RAG examples — replaces the static == EXAMPLES == section
             with retrieved description/source pairs.
        """
        # Start from the static base prompt
        system = SPL2_SYSTEM_PROMPT

        # ── 1. Inject available tools catalog ─────────────────────────────
        try:
            from spl3.tool_api_registry import available_tools_prompt_block
            tools_block = available_tools_prompt_block()
            if tools_block:
                _TOOLS_ANCHOR = "== STRICT RULES =="
                if _TOOLS_ANCHOR in system:
                    system = system.replace(
                        _TOOLS_ANCHOR,
                        tools_block + "\n" + _TOOLS_ANCHOR,
                        1,
                    )
                    _log.debug("text2spl: injected available-tools block into system prompt")
        except Exception as exc:
            _log.debug("text2spl: available-tools injection skipped (%s)", exc)

        # ── 2. Code-RAG example replacement ───────────────────────────────
        if self.code_rag is None or self.code_rag.count() == 0:
            return system

        hits = self.code_rag.retrieve(description, top_k=self.rag_top_k)
        if not hits:
            return system

        # Build dynamic examples block from retrieved pairs
        examples_block = "== EXAMPLES ==\n"
        for i, hit in enumerate(hits, 1):
            label = hit["metadata"].get("name") or hit["description"][:60]
            examples_block += f"\nExample {i} -- {label}:\n\n{hit['spl_source']}\n"

        _log.debug("Code-RAG: injected %d examples for %r", len(hits), description[:50])

        # Swap the static examples section for the retrieved ones
        marker = _EXAMPLES_MARKER
        if marker in system:
            prefix = system[: system.index(marker)]
            return prefix + examples_block
        # Fallback: append retrieved examples after the prompt
        return system + "\n\n" + examples_block

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_output(spl_source: str) -> tuple[bool, str]:
        """Parse and analyse *spl_source* to check if it is valid SPL.

        Returns:
            A ``(valid, message)`` tuple.  When ``valid`` is ``True``,
            *message* is ``"OK"`` (possibly followed by warnings).
            When ``valid`` is ``False``, *message* describes the first
            error encountered.
        """
        # Stage 1: Lexing
        try:
            lexer = Lexer(spl_source)
            tokens = lexer.tokenize()
        except LexerError as exc:
            return False, f"Lexer error: {exc}"

        # Stage 2: Parsing (SPL3Parser accepts := defaults and other SPL3 extensions)
        try:
            parser = SPL3Parser(tokens)
            program = parser.parse()
        except Exception as exc:
            return False, f"Parse error: {exc}"

        # Stage 3: Semantic analysis
        try:
            analyzer = Analyzer()
            analysis = analyzer.analyze(program)
        except AnalysisError as exc:
            return False, f"Analysis error: {exc}"

        # Collect warnings, if any
        if analysis.warnings:
            warnings_text = "; ".join(w.message for w in analysis.warnings)
            return True, f"OK (warnings: {warnings_text})"

        return True, "OK"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Remove markdown code fences if the LLM wrapped its output."""
        lines = text.splitlines()
        if not lines:
            return text

        # Strip leading ```spl or similar
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        # Strip trailing ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        result = "\n".join(lines)
        return Text2SPL._escape_dollar_string_quotes(result)

    @staticmethod
    def _escape_dollar_string_quotes(spl: str) -> str:
        """Escape unbalanced single quotes inside $$ ... $$ blocks as '' (SQL style).

        Prevents VS Code syntax-highlighting breakage when CREATE FUNCTION bodies
        contain natural language with apostrophes (e.g. "user's question").
        Only touches content between $$ delimiters — never touches SPL syntax.
        """
        import re
        def escape_body(m: re.Match) -> str:
            body = m.group(1)
            # Replace a single quote that is NOT already doubled
            body = re.sub(r"'(?!')", "''", body)
            return f"$$\n{body}\n$$"
        return re.sub(r"\$\$\s*\n(.*?)\n\s*\$\$", escape_body, spl, flags=re.DOTALL)
