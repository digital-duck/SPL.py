"""Tests for CREATE TOOL_API — SPL 3.0 deterministic tool definition syntax.

Covers:
  - Parsing: ToolAPINode emitted correctly
  - Execution: exec() + CALL dispatch produces exact results (zero LLM calls)
  - Multiple TOOL_API definitions in one file
  - Error cases: missing function name, exec failure, unsupported runtime
  - Backward compatibility: existing CALL stdlib / GENERATE unaffected
"""
from __future__ import annotations

import asyncio
import pytest

from spl.lexer import Lexer
from spl.analyzer import Analyzer
from spl.adapters.base import GenerationResult
from spl3.parser import SPL3Parser
from spl3.executor import SPL3Executor
from spl3.ast_nodes import ToolAPINode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _StubAdapter:
    """Adapter that records every LLM call so tests can assert none were made."""

    def __init__(self):
        self.calls: list[str] = []

    async def generate(self, prompt, **kw):
        self.calls.append(prompt)
        return GenerationResult(
            content="stub", model="stub", latency_ms=0,
            input_tokens=0, output_tokens=0, total_tokens=0,
        )


def _run(spl: str, params: dict | None = None) -> tuple[object, _StubAdapter]:
    """Parse + execute *spl*, return (WorkflowResult, adapter)."""
    tokens = Lexer(spl).tokenize()
    program = SPL3Parser(tokens).parse()
    analysis = Analyzer().analyze(program)
    adapter = _StubAdapter()
    executor = SPL3Executor(adapter=adapter)

    async def _go():
        return await executor.execute_program(analysis, params=params or {})

    results = asyncio.run(_go())
    return results[0], adapter


# ---------------------------------------------------------------------------
# Parsing tests
# ---------------------------------------------------------------------------

class TestToolAPINode:
    def test_single_tool_api_parsed(self):
        spl = """
CREATE TOOL_API double(n TEXT) RETURNS TEXT AS PYTHON $$
def double(n: str) -> str:
    return str(int(n) * 2)
$$;
WORKFLOW w INPUT @x TEXT := "3" OUTPUT @r TEXT DO
  CALL double(@x) INTO @r;
  RETURN @r WITH status = "complete";
END;
"""
        tokens = Lexer(spl).tokenize()
        program = SPL3Parser(tokens).parse()
        nodes = [s for s in program.statements if isinstance(s, ToolAPINode)]
        assert len(nodes) == 1
        n = nodes[0]
        assert n.name == "double"
        assert n.runtime == "PYTHON"
        assert n.return_type == "TEXT"
        assert len(n.parameters) == 1
        assert n.parameters[0].name == "n"
        assert "def double" in n.python_body

    def test_multiple_tool_apis_parsed(self):
        spl = """
CREATE TOOL_API add(a TEXT, b TEXT) RETURNS TEXT AS PYTHON $$
def add(a: str, b: str) -> str: return str(float(a)+float(b))
$$;
CREATE TOOL_API upper_str(s TEXT) RETURNS TEXT AS PYTHON $$
def upper_str(s: str) -> str: return s.upper()
$$;
WORKFLOW w INPUT @x TEXT OUTPUT @r TEXT DO
  CALL add("1","2") INTO @r;
  RETURN @r WITH status = "complete";
END;
"""
        tokens = Lexer(spl).tokenize()
        program = SPL3Parser(tokens).parse()
        nodes = [s for s in program.statements if isinstance(s, ToolAPINode)]
        assert len(nodes) == 2
        assert {n.name for n in nodes} == {"add", "upper_str"}


# ---------------------------------------------------------------------------
# Execution tests
# ---------------------------------------------------------------------------

class TestToolAPIExecution:
    def test_call_dispatched_to_python_not_llm(self):
        """CALL of a TOOL_API must not consume any LLM tokens."""
        spl = """
CREATE TOOL_API add_nums(a TEXT, b TEXT) RETURNS TEXT AS PYTHON $$
def add_nums(a: str, b: str) -> str:
    return str(float(a) + float(b))
$$;
WORKFLOW w
  INPUT @a TEXT := "10"
  INPUT @b TEXT := "32"
  OUTPUT @result TEXT
DO
  CALL add_nums(@a, @b) INTO @result;
  RETURN @result WITH status = "complete";
END;
"""
        result, adapter = _run(spl)
        assert result.status == "complete"
        assert result.output["result"] == "42.0"
        assert adapter.calls == [], "TOOL_API CALL must not hit the LLM"

    def test_multiple_calls_no_llm(self):
        spl = """
CREATE TOOL_API idx(lst TEXT, i TEXT) RETURNS TEXT AS PYTHON $$
def idx(lst: str, i: str) -> str:
    return lst.split(",")[int(i)].strip()
$$;
CREATE TOOL_API repeat(s TEXT, n TEXT) RETURNS TEXT AS PYTHON $$
def repeat(s: str, n: str) -> str:
    return s * int(n)
$$;
WORKFLOW w
  INPUT @items TEXT := "GOOG,META,MSFT"
  OUTPUT @result TEXT
DO
  CALL idx(@items, "1") INTO @ticker;
  CALL repeat(@ticker, "2") INTO @result;
  RETURN @result WITH status = "complete";
END;
"""
        result, adapter = _run(spl)
        assert result.status == "complete"
        assert result.output["result"] == "METAMETA"
        assert adapter.calls == []

    def test_exact_arithmetic(self):
        """Python arithmetic must be exact — not probabilistic."""
        spl = """
CREATE TOOL_API multiply(a TEXT, b TEXT) RETURNS TEXT AS PYTHON $$
def multiply(a: str, b: str) -> str:
    return str(int(a) * int(b))
$$;
WORKFLOW w INPUT @a TEXT := "7" INPUT @b TEXT := "6" OUTPUT @r TEXT DO
  CALL multiply(@a, @b) INTO @r;
  RETURN @r WITH status = "complete";
END;
"""
        result, adapter = _run(spl)
        assert result.output["r"] == "42"
        assert adapter.calls == []

    def test_tool_api_with_imports(self):
        """Body may include import statements."""
        spl = """
CREATE TOOL_API count_words(text TEXT) RETURNS TEXT AS PYTHON $$
import re
def count_words(text: str) -> str:
    return str(len(re.findall(r'\\w+', text)))
$$;
WORKFLOW w INPUT @t TEXT := "hello world foo" OUTPUT @r TEXT DO
  CALL count_words(@t) INTO @r;
  RETURN @r WITH status = "complete";
END;
"""
        result, adapter = _run(spl)
        assert result.output["r"] == "3"
        assert adapter.calls == []

    def test_tool_api_coexists_with_generate(self):
        """TOOL_API CALL and GENERATE can coexist; only GENERATE hits the LLM."""
        spl = """
CREATE TOOL_API double(n TEXT) RETURNS TEXT AS PYTHON $$
def double(n: str) -> str:
    return str(int(n) * 2)
$$;
CREATE FUNCTION summarize(text TEXT) RETURNS TEXT AS $$
  Summarize: {text}
$$;
WORKFLOW w INPUT @n TEXT := "5" OUTPUT @result TEXT DO
  CALL double(@n) INTO @doubled;
  GENERATE summarize(@doubled) INTO @result;
  RETURN @result WITH status = "complete";
END;
"""
        result, adapter = _run(spl)
        assert result.status == "complete"
        assert result.output["doubled"] == "10"   # exact, no LLM
        assert len(adapter.calls) == 1             # only GENERATE hit the LLM


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestToolAPIErrors:
    def test_missing_function_name_raises(self):
        """Body that does not define a function named after the TOOL_API raises."""
        spl = """
CREATE TOOL_API my_tool(x TEXT) RETURNS TEXT AS PYTHON $$
def wrong_name(x: str) -> str:
    return x
$$;
WORKFLOW w INPUT @x TEXT OUTPUT @r TEXT DO
  CALL my_tool(@x) INTO @r;
  RETURN @r WITH status = "complete";
END;
"""
        with pytest.raises(RuntimeError, match="must define a Python function named 'my_tool'"):
            _run(spl)

    def test_exec_syntax_error_raises(self):
        """Invalid Python in the body raises RuntimeError at load time."""
        spl = """
CREATE TOOL_API bad_tool(x TEXT) RETURNS TEXT AS PYTHON $$
def bad_tool(x: str) -> str
    return x  -- missing colon above
$$;
WORKFLOW w INPUT @x TEXT OUTPUT @r TEXT DO
  CALL bad_tool(@x) INTO @r;
  RETURN @r WITH status = "complete";
END;
"""
        with pytest.raises(RuntimeError, match="failed to compile/exec body"):
            _run(spl)

    def test_unsupported_runtime_skipped_with_warning(self, caplog):
        """Unsupported runtime tag logs a warning and is skipped (not a hard error)."""
        import logging
        spl = """
CREATE TOOL_API go_tool(x TEXT) RETURNS TEXT AS GO $$
func go_tool(x string) string { return x }
$$;
WORKFLOW w INPUT @x TEXT := "hi" OUTPUT @r TEXT DO
  @r := @x;
  RETURN @r WITH status = "complete";
END;
"""
        with caplog.at_level(logging.WARNING, logger="spl.executor"):
            result, _ = _run(spl)
        assert result.status == "complete"
        assert any("GO" in rec.message and "not supported" in rec.message
                   for rec in caplog.records)
