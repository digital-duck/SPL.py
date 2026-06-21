"""SPL 3.0 MCP bridge — connect to MCP tool servers from SPL workflows.

Provides two integration paths:

1. ``CREATE TOOL_API ... AS MCP $$ config $$`` — individual tool binding
2. ``IMPORT MCP "name" FROM "command"`` — bulk tool discovery

Both paths register async callables into the executor's FunctionRegistry,
so MCP tools are invoked via CALL exactly like Python tools.

Requires: ``pip install mcp`` (optional dependency).
"""

from __future__ import annotations

import asyncio
import logging
import shlex
from dataclasses import dataclass, field
from typing import Any

_log = logging.getLogger("spl3.mcp_bridge")

try:
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client, StdioServerParameters
    from mcp.types import TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


def _require_mcp() -> None:
    if not MCP_AVAILABLE:
        raise RuntimeError(
            "MCP support requires the 'mcp' package. "
            "Install it with: pip install 'spl-llm[mcp]' or pip install mcp"
        )


@dataclass
class MCPServerHandle:
    """A live connection to one MCP server subprocess."""
    name: str
    command: str
    session: Any = None
    _context_stack: list = field(default_factory=list)
    tool_names: list[str] = field(default_factory=list)


class MCPServerPool:
    """Manages MCP server subprocess lifecycles for one executor run."""

    def __init__(self) -> None:
        self._servers: dict[str, MCPServerHandle] = {}
        self._lock = asyncio.Lock()

    async def get_or_start(self, name: str, command: str) -> MCPServerHandle:
        async with self._lock:
            if name in self._servers:
                return self._servers[name]

            _require_mcp()
            handle = MCPServerHandle(name=name, command=command)
            await self._start_server(handle)
            self._servers[name] = handle
            return handle

    async def _start_server(self, handle: MCPServerHandle) -> None:
        parts = shlex.split(handle.command)
        params = StdioServerParameters(command=parts[0], args=parts[1:])

        cm1 = stdio_client(params)
        read_stream, write_stream = await cm1.__aenter__()
        handle._context_stack.append(cm1)

        cm2 = ClientSession(read_stream, write_stream)
        session = await cm2.__aenter__()
        handle._context_stack.append(cm2)

        await session.initialize()
        handle.session = session

        tools_result = await session.list_tools()
        handle.tool_names = [t.name for t in tools_result.tools]
        _log.info(
            "MCP server '%s' started (%d tools): %s",
            handle.name, len(handle.tool_names), ", ".join(handle.tool_names),
        )

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict[str, Any]) -> str:
        handle = self._servers.get(server_name)
        if handle is None or handle.session is None:
            raise RuntimeError(f"MCP server '{server_name}' is not connected")

        result = await handle.session.call_tool(tool_name, arguments=arguments)

        if result.isError:
            texts = []
            for block in result.content:
                if hasattr(block, "text"):
                    texts.append(block.text)
            return f"error: {' '.join(texts) if texts else 'MCP tool returned an error'}"

        texts = []
        for block in result.content:
            if hasattr(block, "text"):
                texts.append(block.text)
        return "\n".join(texts) if texts else ""

    async def shutdown(self) -> None:
        for handle in reversed(list(self._servers.values())):
            for cm in reversed(handle._context_stack):
                try:
                    await cm.__aexit__(None, None, None)
                except Exception as exc:
                    _log.debug("MCP server '%s' cleanup: %s", handle.name, exc)
            _log.debug("MCP server '%s' shut down", handle.name)
        self._servers.clear()


def parse_mcp_config(body: str) -> dict[str, str]:
    """Parse the $$ body $$ of a CREATE TOOL_API ... AS MCP declaration.

    Accepted formats::

        server_name: "command string"

    or multi-line key: value::

        server: "command string"
        tool: "mcp_tool_name"

    Returns dict with keys: 'server', 'command', and optionally 'tool'.
    """
    config: dict[str, str] = {}
    for line in body.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip().lower()
        val = val.strip().strip("\"'")
        config[key] = val

    if "server" not in config:
        # Single-line shorthand:  name: "command"
        for line in body.strip().splitlines():
            line = line.strip()
            if ":" in line:
                key, _, val = line.partition(":")
                config["server"] = key.strip()
                config["command"] = val.strip().strip("\"'")
                break

    if "command" not in config and "server" in config:
        config.setdefault("command", config.get("server", ""))

    return config


def make_mcp_tool_callable(pool: MCPServerPool, server_name: str, tool_name: str):
    """Create an async callable that wraps MCPServerPool.call_tool."""
    async def _call_mcp_tool(*args: str, **kwargs: str) -> str:
        arguments: dict[str, Any] = {}
        arguments.update(kwargs)
        for i, val in enumerate(args):
            arguments[f"arg{i}"] = val
        return await pool.call_tool(server_name, tool_name, arguments)

    _call_mcp_tool.__name__ = tool_name
    _call_mcp_tool.__qualname__ = f"mcp.{server_name}.{tool_name}"
    return _call_mcp_tool
