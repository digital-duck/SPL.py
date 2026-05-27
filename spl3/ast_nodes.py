"""SPL 3.0 AST node additions over SPL 2.0.

New nodes:
  SetLiteral            — {a, b, c}  unordered unique collection literal
  ImportStatement       — IMPORT 'file.spl'  multi-file workflow loading
  CallParallelStatement — CALL PARALLEL ... END  concurrent dispatch
  UnaryOp               — NOT <expr>  boolean negation
  CompoundCondition     — <cond> AND/OR <cond>  compound boolean condition
  ToolAPINode           — CREATE TOOL_API ... AS PYTHON $$ ... $$  deterministic tool
"""

from __future__ import annotations
from dataclasses import dataclass, field

# Re-export SPL 2.0 nodes so callers can import from one place.
from spl.ast_nodes import Expression  # noqa: F401


@dataclass
class UnaryOp(Expression):
    """NOT <expr> — boolean negation.

    operator : currently always 'NOT'
    operand  : the expression being negated

    At runtime evaluates operand and returns its boolean inverse.

    Example:
        WHILE NOT @test_passed AND @cycle < @max_cycles DO
    """
    operator: str
    operand: Expression = field(default=None)


@dataclass
class CompoundCondition:
    """<cond> AND/OR <cond> — compound boolean WHILE condition.

    Allows boolean conditions to be joined with AND or OR, where each
    side can be a Condition, UnaryOp, or another CompoundCondition.

    Example:
        WHILE NOT @test_passed AND @cycle < @max_cycles DO
        →  CompoundCondition(
               operator='AND',
               left=UnaryOp('NOT', ParamRef('test_passed')),
               right=Condition(ParamRef('cycle'), '<', Literal(max_cycles))
           )
    """
    operator: str   # 'AND' or 'OR'
    left: object    # Condition | UnaryOp | CompoundCondition | Expression
    right: object


@dataclass
class NoneLiteral(Expression):
    """NONE or NULL literal — first-class null value.

    SPL 2.0's Literal node only accepts str|int|float|bool values.
    NoneLiteral is a dedicated SPL 3.0 node that avoids the type clash
    and makes null intent explicit in the AST.

    At runtime evaluates to the empty string '' — consistent with
    state.get_var() returning '' for undefined variables.

    Usage:
        @result := NONE
        EVALUATE @score WHEN = NONE THEN ...  END
        INPUT: @threshold FLOAT DEFAULT NONE
    """


@dataclass
class SetLiteral(Expression):
    """{ expr, expr, ... } — unordered unique collection literal.

    Parsed when { } contains comma-separated elements with no colons:
      {'python', 'sql', 'linux'}  →  SetLiteral
      {'key': 'val'}              →  MapLiteral  (colon present)
      {}                          →  MapLiteral  (empty — MAP by default)

    At runtime serializes as a sorted, deduplicated JSON array:
      {'b', 'a', 'b'}  →  '["a", "b"]'
    """
    elements: list[Expression] = field(default_factory=list)


@dataclass
class ImportStatement:
    """IMPORT 'file.spl' — load workflow definitions from an external .spl file.

    Resolved at parse time relative to the current file.  All WORKFLOW
    definitions in the imported file are registered alongside the
    importing file's own definitions.

    Example:
        IMPORT 'lib/code_agents.spl'
        IMPORT '../shared/validators.spl'
    """
    path: str


@dataclass
class CallParallelBranch:
    """Single branch inside a CALL PARALLEL block.

    workflow_name : name of the workflow to call
    arguments     : positional argument expressions
    target_var    : caller's INTO @var binding
    """
    workflow_name: str
    arguments: list[Expression] = field(default_factory=list)
    target_var: str = ""


@dataclass
class CallParallelStatement:
    """CALL PARALLEL workflow_a(@x) INTO @a, workflow_b(@y) INTO @b END

    Dispatches multiple sub-workflows concurrently via asyncio.gather.
    The Hub routes each to an available node — same mechanism as
    existing multi-node task dispatch.

    All branches must complete (or fail) before execution continues.
    If any branch fails its WorkflowCompositionError propagates to the
    caller's EXCEPTION WHEN handler.
    """
    branches: list[CallParallelBranch] = field(default_factory=list)


@dataclass
class ToolAPINode:
    """CREATE TOOL_API <name>(<params>) RETURNS <type> AS PYTHON $$ <body> $$

    Declares a deterministic Python tool callable via CALL in any workflow.

    At load time the executor exec()s *python_body* in an isolated namespace,
    extracts the function named *name*, and registers it in _GLOBAL_TOOLS —
    exactly as if it came from a tools.py loaded via --tools.  From CALL's
    dispatch perspective nothing changes.

    Design principle (classical / probabilistic regime):
      Use TOOL_API for operations with a single correct answer — API calls,
      math, data transformation, string manipulation, file I/O.
      Use CREATE FUNCTION (LLM prompt template) for operations that require
      reasoning, judgment, or generation.

    Parameters
    ----------
    name        : tool name; must match the Python function defined in the body
    parameters  : list of Parameter nodes (same as CREATE FUNCTION)
    return_type : declared return type (TEXT, NUMBER, etc.)
    runtime     : runtime tag — currently always 'PYTHON'; future: 'GO', 'TS'
    python_body : the raw Python source text between $$ ... $$

    Example
    -------
    CREATE TOOL_API fetch_stock_data(ticker TEXT, years TEXT) RETURNS TEXT AS PYTHON $$
    import yfinance as yf, pandas as pd

    def fetch_stock_data(ticker: str, years: str) -> str:
        end = pd.Timestamp.today()
        start = end - pd.DateOffset(years=float(years))
        df = yf.download(ticker, start=start, end=end, auto_adjust=True)
        return "error: no data" if df.empty else df.to_csv()
    $$;
    """
    name: str
    parameters: list = field(default_factory=list)   # list[Parameter]
    return_type: str = "TEXT"
    runtime: str = "PYTHON"
    python_body: str = ""
