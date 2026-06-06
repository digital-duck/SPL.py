"""SPL 3.0 Parser — extends SPL 2.0 parser with new type system and syntax.

New capabilities over SPL 2.0:
  - NONE / NULL literal  →  Literal(value=None, literal_type='none')
  - { a, b, c }          →  SetLiteral  (no colon → SET; colon → MAP)
  - SET as type annotation  (SET is a keyword token in SPL 2.0; handled here)
  - INT, FLOAT, IMAGE, AUDIO, VIDEO type annotations  (IDENTIFIER tokens)
  - IMPORT 'file.spl'    →  ImportStatement
  - CALL PARALLEL ... END  →  CallParallelStatement
  - CREATE TOOL_API ... AS PYTHON $$ ... $$  →  ToolAPINode

SPL 2.0 backward compatibility is fully preserved:
  - All existing MAP literals { 'k': v } continue to work.
  - {} (empty braces) remains a MAP literal (consistent with Python).
  - All SPL 2.0 type annotations (TEXT, NUMBER, BOOL, LIST, MAP, STORAGE)
    are unchanged.
"""

from __future__ import annotations

from spl.tokens import TokenType
from spl.parser import Parser as SPL2Parser
from spl.ast_nodes import (
    MapLiteral, Parameter, StorageSpec, Expression,
    CallStatement, Condition,
)

from spl3.ast_nodes import (
    NoneLiteral, SetLiteral, ImportStatement,
    CallParallelBranch, CallParallelStatement,
    UnaryOp, CompoundCondition, ToolAPINode,
    SolveStatement, AssertStatement,
)


class SPL3Parser(SPL2Parser):
    """SPL 3.0 recursive descent parser, extending SPL 2.0."""

    # ------------------------------------------------------------------ #
    # Statement dispatch                                                   #
    # ------------------------------------------------------------------ #

    def _parse_statement(self):
        """Dispatch to the appropriate statement parser.

        Handles SPL 3.0 additions:
          IMPORT 'file.spl'
          CREATE TOOL_API ... AS PYTHON $$ ... $$
        before falling through to SPL 2.0 dispatch.
        """
        tok = self._current()

        # IMPORT 'file.spl'
        if tok.type == TokenType.IDENTIFIER and tok.value.lower() == "import":
            return self._parse_import_statement()

        # CREATE TOOL_API ... AS PYTHON $$ ... $$
        # Peek ahead: CREATE followed by an identifier whose value is 'tool_api'
        if tok.type == TokenType.CREATE:
            next_tok = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if (next_tok is not None
                    and next_tok.type == TokenType.IDENTIFIER
                    and next_tok.value.lower() == "tool_api"):
                return self._parse_tool_api()

        # SOLVE @var [TYPE] := python_expr  — deterministic value query via kernel
        if tok.type == TokenType.IDENTIFIER and tok.value.lower() == "solve":
            return self._parse_solve_statement()

        # ASSERT python_expr [OTHERWISE ...]  — deterministic branch via kernel
        if tok.type == TokenType.IDENTIFIER and tok.value.lower() == "assert":
            return self._parse_assert_statement()

        return super()._parse_statement()

    # ------------------------------------------------------------------ #
    # IMPORT statement                                                     #
    # ------------------------------------------------------------------ #

    def _parse_import_statement(self) -> ImportStatement:
        """Parse IMPORT 'file.spl'"""
        self._advance()  # consume 'import' identifier
        path = self._expect(TokenType.STRING).value
        return ImportStatement(path=path)

    # ------------------------------------------------------------------ #
    # CREATE TOOL_API statement                                            #
    # ------------------------------------------------------------------ #

    def _parse_tool_api(self) -> ToolAPINode:
        """Parse CREATE TOOL_API <name>(<params>) RETURNS <type> AS PYTHON $$ <body> $$

        Uses existing token types — no lexer changes required:
          CREATE       TokenType.CREATE
          TOOL_API     two consecutive IDENTIFIER tokens ('tool_api' treated as one name)
          AS           TokenType.AS
          PYTHON       IDENTIFIER token (value 'python') — not a reserved keyword
          $$           TokenType.DOLLAR_DOLLAR
          <body>       TokenType.STRING  (lexer captures everything between $$ ... $$)
        """
        self._expect(TokenType.CREATE)
        # consume 'tool_api' identifier (already peeked in _parse_statement)
        self._advance()

        name = self._expect(TokenType.IDENTIFIER).value

        # parameter list
        self._expect(TokenType.LPAREN)
        parameters = []
        if not self._check(TokenType.RPAREN):
            parameters.append(self._parse_parameter())
            while self._check(TokenType.COMMA):
                self._advance()
                parameters.append(self._parse_parameter())
        self._expect(TokenType.RPAREN)

        # RETURNS <type>
        if self._check(TokenType.RETURN):
            self._advance()
        else:
            self._expect(TokenType.RETURNS)
        return_type = self._expect(TokenType.IDENTIFIER).value

        # AS PYTHON
        self._expect(TokenType.AS)
        runtime_tok = self._expect(TokenType.IDENTIFIER)
        runtime = runtime_tok.value.upper()  # 'PYTHON', future: 'GO', 'TS'

        # $$ <body> $$
        self._expect(TokenType.DOLLAR_DOLLAR)
        body = self._expect(TokenType.STRING).value

        return ToolAPINode(
            name=name,
            parameters=parameters,
            return_type=return_type,
            runtime=runtime,
            python_body=body,
        )

    # ------------------------------------------------------------------ #
    # CALL PARALLEL override                                               #
    # ------------------------------------------------------------------ #

    def _parse_call_statement(self):
        """Parse CALL [PARALLEL] ...

        CALL workflow(@args) INTO @var              → CallStatement (SPL 2.0)
        CALL PARALLEL workflow1(...) INTO @a,       → CallParallelStatement
                      workflow2(...) INTO @b
        END
        """
        self._expect(TokenType.CALL)
        tok = self._current()

        # Detect PARALLEL keyword (comes through as IDENTIFIER)
        if tok.type == TokenType.IDENTIFIER and tok.value.lower() == "parallel":
            self._advance()  # consume 'parallel'
            return self._parse_call_parallel_body()

        # Normal CALL — re-implement (can't call super because we already
        # consumed the CALL token; reconstruct the same logic)
        proc_name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.LPAREN)
        arguments: list[Expression] = []
        if not self._check(TokenType.RPAREN):
            arguments.append(self._parse_call_argument())
            while self._check(TokenType.COMMA):
                self._advance()
                if self._check(TokenType.RPAREN):
                    break  # trailing comma
                arguments.append(self._parse_call_argument())
        self._expect(TokenType.RPAREN)

        target = None
        if self._check(TokenType.INTO):
            self._advance()
            if self._check(TokenType.NONE):
                # INTO NONE — discard result (SPL 3.0 syntax)
                self._advance()
            else:
                self._expect(TokenType.AT)
                target = self._expect_identifier_or_keyword().value

        return CallStatement(
            procedure_name=proc_name,
            arguments=arguments,
            target_variable=target,
        )

    def _parse_call_parallel_body(self) -> CallParallelStatement:
        """Parse the branch list after CALL PARALLEL ... END"""
        branches: list[CallParallelBranch] = []
        while not self._check(TokenType.END) and not self._check(TokenType.EOF):
            branch = self._parse_parallel_branch()
            branches.append(branch)
            if self._check(TokenType.COMMA):
                self._advance()  # optional comma between branches
        self._expect(TokenType.END)
        return CallParallelStatement(branches=branches)

    def _parse_parallel_branch(self) -> CallParallelBranch:
        """Parse a single  workflow_name(@args) INTO @var  branch."""
        name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.LPAREN)
        arguments: list[Expression] = []
        if not self._check(TokenType.RPAREN):
            arguments.append(self._parse_call_argument())
            while self._check(TokenType.COMMA):
                self._advance()
                if self._check(TokenType.RPAREN):
                    break  # trailing comma
                arguments.append(self._parse_call_argument())
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.INTO)
        self._expect(TokenType.AT)
        target = self._expect_identifier_or_keyword().value
        return CallParallelBranch(
            workflow_name=name,
            arguments=arguments,
            target_var=target,
        )

    # ------------------------------------------------------------------ #
    # WHILE condition — supports NOT prefix and AND/OR compounds           #
    # ------------------------------------------------------------------ #

    def _parse_while_condition(self):
        """Parse WHILE condition with SPL 3.0 extensions:
          - NOT <expr>           — boolean negation as a condition
          - <cond> AND/OR <cond> — compound where left side may be a boolean expr

        Falls through to SPL 2.0 for plain comparison conditions.
        """
        # NOT <expr> — boolean condition
        if self._check(TokenType.NOT):
            self._advance()
            operand = self._parse_expression()
            left = UnaryOp(operator='NOT', operand=operand)
            # Check for AND/OR compound
            if self._check_any(TokenType.AND, TokenType.OR):
                logical_op = 'AND' if self._current().type == TokenType.AND else 'OR'
                self._advance()
                right = self._parse_while_condition()  # recursive — handles chains
                return CompoundCondition(operator=logical_op, left=left, right=right)
            return left

        # SPL 2.0 handles plain comparisons; intercept AND/OR after them
        cond = super()._parse_while_condition()
        if self._check_any(TokenType.AND, TokenType.OR):
            logical_op = 'AND' if self._current().type == TokenType.AND else 'OR'
            self._advance()
            right = self._parse_while_condition()
            return CompoundCondition(operator=logical_op, left=cond, right=right)
        return cond

    # ------------------------------------------------------------------ #
    # Expression primary — NONE literal + SET vs MAP disambiguation        #
    # ------------------------------------------------------------------ #

    def _parse_primary(self) -> Expression:
        """Parse a primary expression.

        Intercepts before delegating to SPL 2.0:
          1. NONE / NULL literal tokens (IDENTIFIER with value none/null)
          2. { } brace literals — disambiguates MAP vs SET
        """
        tok = self._current()

        # NOT <expr> — boolean negation
        if tok.type == TokenType.NOT:
            self._advance()
            operand = self._parse_primary()
            return UnaryOp(operator='NOT', operand=operand)

        # NONE / NULL literal
        if tok.type == TokenType.NONE:
            self._advance()
            return NoneLiteral()
        if tok.type == TokenType.IDENTIFIER and tok.value.upper() == "NULL":
            self._advance()
            return NoneLiteral()

        # { } — MAP or SET depending on first element
        if tok.type == TokenType.LBRACE:
            return self._parse_brace_literal()

        # Everything else: SPL 2.0 handles it
        return super()._parse_primary()

    def _parse_brace_literal(self):
        """Parse { } as either a MapLiteral or SetLiteral.

        Disambiguation rule (same as Python):
          {}            → empty MapLiteral
          {key: val}    → MapLiteral  (colon after first element)
          {elem, elem}  → SetLiteral  (comma after first element)
        """
        self._advance()  # consume {

        # Empty braces → MAP (consistent with Python {})
        if self._check(TokenType.RBRACE):
            self._advance()
            return MapLiteral(pairs=[])

        # Parse first element
        first = self._parse_expression()

        if self._check(TokenType.COLON):
            # {key: val, ...} → MAP
            self._advance()  # consume :
            val = self._parse_expression()
            pairs = [(first, val)]
            while self._check(TokenType.COMMA):
                self._advance()
                if self._check(TokenType.RBRACE):
                    break  # trailing comma
                key = self._parse_expression()
                self._expect(TokenType.COLON)
                val = self._parse_expression()
                pairs.append((key, val))
            self._expect(TokenType.RBRACE)
            return MapLiteral(pairs=pairs)

        else:
            # {elem, ...} → SET
            elements = [first]
            while self._check(TokenType.COMMA):
                self._advance()
                if self._check(TokenType.RBRACE):
                    break  # trailing comma
                elements.append(self._parse_expression())
            self._expect(TokenType.RBRACE)
            return SetLiteral(elements=elements)

    # ------------------------------------------------------------------ #
    # Workflow / procedure parameter — handle SET keyword as type          #
    # ------------------------------------------------------------------ #

    # ------------------------------------------------------------------ #
    # SOLVE statement                                                      #
    # ------------------------------------------------------------------ #

    def _parse_solve_statement(self) -> SolveStatement:
        """Parse SOLVE @var [TYPE] := python_expr

        Syntax:
            SOLVE @target_var [TYPE_ANNOTATION] := python_expression
        where python_expression may contain @@varname@@ variable references
        (produced by _parse_python_call_template() from @var tokens).

        Example:
            SOLVE @order LIST := productivity_order(@@graph@@, weight=@@payoff_weight@@)
        """
        self._advance()  # consume 'solve' identifier

        self._expect(TokenType.AT)
        target = self._expect_identifier_or_keyword().value

        # Optional type annotation (TEXT, NUMBER, LIST, etc.)
        target_type = None
        if self._check(TokenType.IDENTIFIER):
            target_type = self._advance().value.upper()

        self._expect(TokenType.ASSIGN)  # :=
        python_template = self._parse_python_call_template()
        return SolveStatement(
            target_variable=target,
            target_type=target_type,
            python_template=python_template,
        )

    # ------------------------------------------------------------------ #
    # ASSERT statement                                                     #
    # ------------------------------------------------------------------ #

    def _parse_assert_statement(self) -> AssertStatement:
        """Parse ASSERT python_expr [OTHERWISE statement_or_block]

        Syntax:
            ASSERT python_expression [OTHERWISE <statement> | DO <stmts> END]
        where python_expression may contain @@varname@@ variable references.

        OTHERWISE is lexed as TokenType.ELSE (backward-compatibility alias).
        The OTHERWISE body is parsed as:
          - A single statement (RETRY, RAISE, GENERATE...INTO, CALL..., etc.)
          - OR a DO...END block for multiple statements.

        Example:
            ASSERT reducible(@@graph@@, @@primitives@@)
                OTHERWISE RETRY
        """
        self._advance()  # consume 'assert' identifier
        python_template = self._parse_python_call_template()

        otherwise_body: list = []
        if self._check(TokenType.ELSE):  # OTHERWISE is lexed as ELSE
            self._advance()  # consume OTHERWISE/ELSE
            if self._check(TokenType.DO):
                self._advance()  # consume DO
                while not self._check_any(TokenType.END, TokenType.EOF):
                    otherwise_body.append(self._parse_statement())
                self._expect(TokenType.END)
            else:
                # Single statement after OTHERWISE
                otherwise_body.append(self._parse_statement())

        return AssertStatement(
            python_template=python_template,
            otherwise_body=otherwise_body,
        )

    # ------------------------------------------------------------------ #
    # Python expression template parser (shared by SOLVE and ASSERT)      #
    # ------------------------------------------------------------------ #

    def _parse_python_call_template(self) -> str:
        """Collect tokens until a statement boundary and rebuild as a Python
        expression template string.

        SPL @var references become @@varname@@ markers so the executor can
        substitute state values at runtime via re.sub().

        Handles token types that commonly appear in Python expressions:
          identifiers, numeric/string literals, parentheses, brackets,
          braces, comparison operators, arithmetic operators, boolean
          keywords (and/or/not), in, True/False/None, and single = for
          keyword arguments.

        Stops at: EOF, SEMICOLON, END, ELSE (OTHERWISE), or any token
        type not recognised as valid inside a Python expression.
        """
        _STOP = {
            TokenType.EOF,
            TokenType.SEMICOLON,
            TokenType.END,
            TokenType.ELSE,   # OTHERWISE
        }
        # Map token type → literal string for tokens that are both SPL
        # keywords and valid Python tokens.
        _KEYWORD_AS_PYTHON: dict[TokenType, str] = {
            TokenType.AND:         " and ",
            TokenType.OR:          " or ",
            TokenType.NOT:         "not ",
            TokenType.IN:          " in ",
            TokenType.TRUE:        "True",
            TokenType.FALSE:       "False",
            TokenType.NONE:        "None",
            # SPL keywords that appear as Python identifier tokens in expressions:
            TokenType.DEFAULT:     "default",
            TokenType.MODEL:       "model",
            TokenType.FORMAT:      "format",
            TokenType.LIMIT:       "limit",
            TokenType.FROM:        "from",
            TokenType.FOR:         "for",
            TokenType.AS:          "as",
            TokenType.RETURN:      "return",
            TokenType.WITH:        "with",
            TokenType.INPUT:       "input",
            TokenType.OUTPUT:      "output",
            TokenType.SELECT:      "select",
            TokenType.ORDER:       "order",
            TokenType.WHERE:       "where",
            TokenType.RESULT:      "result",
            TokenType.STORE:       "store",
            TokenType.CACHE:       "cache",
            TokenType.RETRY:       "retry",
            TokenType.RAISE:       "raise",
            TokenType.CALL:        "call",
            TokenType.INTO:        "into",
            TokenType.SET:         "set",
            TokenType.LOGGING:     "logging",
            TokenType.TO:          "to",
            TokenType.LEVEL:       "level",
            TokenType.GENERATE:    "generate",
            TokenType.EVALUATE:    "evaluate",
            TokenType.WORKFLOW:    "workflow",
            TokenType.ERROR:       "error",
            TokenType.VERSION:     "version",
            TokenType.SCHEMA:      "schema",
            TokenType.COMMIT:      "commit",
        }
        _OP_MAP: dict[TokenType, str] = {
            TokenType.EQ:       "=",
            TokenType.NEQ:      "!=",
            TokenType.GT:       ">",
            TokenType.LT:       "<",
            TokenType.GTE:      ">=",
            TokenType.LTE:      "<=",
            TokenType.PLUS:     "+",
            TokenType.MINUS:    "-",
            TokenType.STAR:     "*",
            TokenType.PERCENT:  "%",
            TokenType.LPAREN:   "(",
            TokenType.RPAREN:   ")",
            TokenType.LBRACKET: "[",
            TokenType.RBRACKET: "]",
            TokenType.LBRACE:   "{",
            TokenType.RBRACE:   "}",
            TokenType.COLON:    ":",
            TokenType.COMMA:    ", ",
            TokenType.DOT:      ".",
        }

        parts: list[str] = []
        paren_depth = 0  # track open parens so we stop after the outermost close
        while True:
            tok = self._current()
            if tok.type in _STOP:
                break
            # After the top-level expression is complete (paren_depth == 0 and we
            # already emitted some content), an IDENTIFIER that is not immediately
            # after a dot/open-paren signals the start of a new SPL statement.
            if paren_depth == 0 and parts and tok.type == TokenType.IDENTIFIER:
                # Allow continuation for binary operators (and/or/in are in
                # _KEYWORD_AS_PYTHON and will be handled below); plain identifiers
                # after a closed expression mark a new statement → stop.
                next_tok = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
                if (tok.value.upper() not in {kw.upper() for kw in ["and", "or", "not", "in"]}
                        and next_tok is not None
                        and next_tok.type not in (TokenType.EQ, TokenType.DOT)):
                    # Plain identifier at depth-0 that is not a binary operator and not
                    # followed by = or . — treat as start of next SPL statement.
                    break
            if tok.type == TokenType.AT:
                # Lookahead: @var := is an SPL assignment — stop the template.
                # @var followed by anything else is a variable reference → @@var@@.
                ahead1 = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
                ahead2 = self.tokens[self.pos + 2] if self.pos + 2 < len(self.tokens) else None
                if (ahead1 is not None
                        and ahead1.type in (TokenType.IDENTIFIER,)
                        and ahead2 is not None
                        and ahead2.type == TokenType.ASSIGN):
                    break  # @var := pattern → new SPL statement, stop template
                self._advance()  # consume @
                try:
                    name_tok = self._expect_identifier_or_keyword()
                    parts.append(f"@@{name_tok.value}@@")
                except Exception:
                    parts.append("@")
            elif tok.type in _KEYWORD_AS_PYTHON:
                self._advance()
                parts.append(_KEYWORD_AS_PYTHON[tok.type])
            elif tok.type in _OP_MAP:
                self._advance()
                s = _OP_MAP[tok.type]
                if tok.type == TokenType.LPAREN:
                    paren_depth += 1
                elif tok.type == TokenType.RPAREN:
                    paren_depth -= 1
                parts.append(s)
            elif tok.type == TokenType.IDENTIFIER:
                parts.append(self._advance().value)
            elif tok.type == TokenType.INTEGER:
                parts.append(str(self._advance().value))
            elif tok.type == TokenType.FLOAT:
                parts.append(str(self._advance().value))
            elif tok.type == TokenType.STRING:
                parts.append(repr(self._advance().value))
            else:
                break  # unrecognised token → end of expression

        return "".join(parts)

    # ------------------------------------------------------------------ #
    # Workflow / procedure parameter — handle SET keyword as type          #
    # ------------------------------------------------------------------ #

    def _parse_workflow_param(self) -> Parameter:
        """Parse @name [type] [DEFAULT value].

        Extends SPL 2.0 to recognise TokenType.SET as a valid type annotation
        (SET is a reserved keyword in SPL 2.0 for the SET @var = expr alias,
        so it arrives as TokenType.SET rather than TokenType.IDENTIFIER).

        All other type annotations (INT, FLOAT, IMAGE, AUDIO, VIDEO, NONE,
        TEXT, NUMBER, BOOL, LIST, MAP) are plain IDENTIFIER tokens and are
        already handled by the SPL 2.0 method.
        """
        self._expect(TokenType.AT)
        name = self._expect_identifier_or_keyword().value
        param_type = None
        default_value = None

        if self._check(TokenType.IDENTIFIER):
            if self._current().value.upper() == "STORAGE":
                self._advance()  # consume STORAGE
                param_type = "STORAGE"
                if self._check(TokenType.LPAREN):
                    self._advance()  # consume (
                    backend = self._expect(TokenType.IDENTIFIER).value
                    self._expect(TokenType.COMMA)
                    path = self._expect(TokenType.STRING).value
                    self._expect(TokenType.RPAREN)
                    default_value = StorageSpec(backend=backend, path=path)
            else:
                param_type = self._advance().value  # TEXT, NUMBER, BOOL, LIST, MAP, INT, FLOAT, IMAGE …

        elif self._check(TokenType.SET):
            # SET is a keyword token, not IDENTIFIER — accept as type annotation
            param_type = self._advance().value  # "set"

        if self._check(TokenType.DEFAULT) or self._check(TokenType.ASSIGN):
            self._advance()
            default_value = self._parse_expression()

        return Parameter(name=name, param_type=param_type, default_value=default_value)
