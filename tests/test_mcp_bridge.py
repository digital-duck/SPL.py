"""Tests for SPL 3.0 MCP bridge integration.

Tests cover:
  - Parser: IMPORT MCP with ONLY/EXCEPT/AS clauses
  - Parser: CREATE TOOL_API ... AS MCP $$ config $$
  - Config parsing: parse_mcp_config()
  - Executor: MCP tools skip gracefully when mcp package unavailable
  - Executor: ImportMCPStatement recognized in AST
"""

import pytest
from spl.lexer import Lexer
from spl3.parser import SPL3Parser
from spl3.ast_nodes import ImportMCPStatement, ToolAPINode


# ── Parser tests ─────────────────────────────────────────────────────────────

class TestImportMCPParsing:

    def _parse(self, source: str):
        tokens = Lexer(source).tokenize()
        return SPL3Parser(tokens).parse()

    def test_basic_import_mcp(self):
        prog = self._parse(
            'IMPORT MCP "filesystem" FROM "npx @mcp/server-fs /tmp"\n'
            'WORKFLOW w\n  OUTPUT @x TEXT\nDO\n  @x := "ok"\n  RETURN @x\nEND\n'
        )
        stmt = prog.statements[0]
        assert isinstance(stmt, ImportMCPStatement)
        assert stmt.server_name == "filesystem"
        assert stmt.command == "npx @mcp/server-fs /tmp"
        assert stmt.only == []
        assert stmt.except_ == []
        assert stmt.prefix == ""

    def test_import_mcp_with_only(self):
        prog = self._parse(
            'IMPORT MCP "fs" FROM "npx server-fs" ONLY read_file, write_file\n'
            'WORKFLOW w\n  OUTPUT @x TEXT\nDO\n  @x := "ok"\n  RETURN @x\nEND\n'
        )
        stmt = prog.statements[0]
        assert isinstance(stmt, ImportMCPStatement)
        assert stmt.only == ["read_file", "write_file"]
        assert stmt.except_ == []

    def test_import_mcp_with_except(self):
        prog = self._parse(
            'IMPORT MCP "github" FROM "npx server-github" EXCEPT delete_branch, create_issue\n'
            'WORKFLOW w\n  OUTPUT @x TEXT\nDO\n  @x := "ok"\n  RETURN @x\nEND\n'
        )
        stmt = prog.statements[0]
        assert isinstance(stmt, ImportMCPStatement)
        assert stmt.only == []
        assert stmt.except_ == ["delete_branch", "create_issue"]

    def test_import_mcp_with_prefix(self):
        prog = self._parse(
            'IMPORT MCP "filesystem" FROM "npx server-fs" AS fs\n'
            'WORKFLOW w\n  OUTPUT @x TEXT\nDO\n  @x := "ok"\n  RETURN @x\nEND\n'
        )
        stmt = prog.statements[0]
        assert isinstance(stmt, ImportMCPStatement)
        assert stmt.prefix == "fs"

    def test_import_mcp_with_only_and_prefix(self):
        prog = self._parse(
            'IMPORT MCP "fs" FROM "npx server-fs" ONLY read_file AS fs\n'
            'WORKFLOW w\n  OUTPUT @x TEXT\nDO\n  @x := "ok"\n  RETURN @x\nEND\n'
        )
        stmt = prog.statements[0]
        assert isinstance(stmt, ImportMCPStatement)
        assert stmt.only == ["read_file"]
        assert stmt.prefix == "fs"

    def test_regular_import_still_works(self):
        """IMPORT 'file.spl' must not break."""
        prog = self._parse(
            'IMPORT "sympolic_tools"\n'
            'WORKFLOW w\n  OUTPUT @x TEXT\nDO\n  @x := "ok"\n  RETURN @x\nEND\n'
        )
        from spl3.ast_nodes import ImportStatement
        stmt = prog.statements[0]
        assert isinstance(stmt, ImportStatement)
        assert stmt.path == "sympolic_tools"


class TestToolAPIMCPParsing:

    def _parse(self, source: str):
        tokens = Lexer(source).tokenize()
        return SPL3Parser(tokens).parse()

    def test_create_tool_api_as_mcp(self):
        prog = self._parse(
            'CREATE TOOL_API read_file(path TEXT) RETURNS TEXT AS MCP $$\n'
            'server: "npx @mcp/server-fs /tmp"\n'
            'tool: "read_file"\n'
            '$$;\n'
            'WORKFLOW w\n  OUTPUT @x TEXT\nDO\n  @x := "ok"\n  RETURN @x\nEND\n'
        )
        stmt = prog.statements[0]
        assert isinstance(stmt, ToolAPINode)
        assert stmt.name == "read_file"
        assert stmt.runtime == "MCP"
        assert "server" in stmt.python_body
        assert "npx" in stmt.python_body

    def test_create_tool_api_as_python_unchanged(self):
        prog = self._parse(
            'CREATE TOOL_API add(a TEXT, b TEXT) RETURNS TEXT AS PYTHON $$\n'
            'def add(a: str, b: str) -> str:\n'
            '    return str(int(a) + int(b))\n'
            '$$;\n'
            'WORKFLOW w\n  OUTPUT @x TEXT\nDO\n  @x := "ok"\n  RETURN @x\nEND\n'
        )
        stmt = prog.statements[0]
        assert isinstance(stmt, ToolAPINode)
        assert stmt.runtime == "PYTHON"


# ── Config parser tests ──────────────────────────────────────────────────────

class TestMCPConfigParsing:

    def test_shorthand_format(self):
        from spl3.mcp_bridge import parse_mcp_config
        config = parse_mcp_config('filesystem: "npx @mcp/server-fs /tmp"')
        assert config["server"] == "filesystem"
        assert config["command"] == "npx @mcp/server-fs /tmp"

    def test_multiline_format(self):
        from spl3.mcp_bridge import parse_mcp_config
        config = parse_mcp_config(
            'server: "npx @mcp/server-fs /tmp"\n'
            'tool: "read_file"\n'
        )
        assert config["server"] == "npx @mcp/server-fs /tmp"
        assert config["tool"] == "read_file"

    def test_comments_ignored(self):
        from spl3.mcp_bridge import parse_mcp_config
        config = parse_mcp_config(
            '# a comment\n'
            'filesystem: "npx server-fs"\n'
        )
        assert config["server"] == "filesystem"

    def test_empty_body(self):
        from spl3.mcp_bridge import parse_mcp_config
        config = parse_mcp_config("")
        assert "server" not in config


# ── MCP availability check ───────────────────────────────────────────────────

class TestMCPAvailability:

    def test_mcp_sdk_importable(self):
        from spl3.mcp_bridge import MCP_AVAILABLE
        assert MCP_AVAILABLE is True, "mcp package should be installed for tests"

    def test_require_mcp_does_not_raise(self):
        from spl3.mcp_bridge import _require_mcp
        _require_mcp()
