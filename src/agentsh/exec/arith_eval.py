"""Arithmetic evaluator — AST-safe evaluation of shell arithmetic expressions.

Follows the Oils split-evaluator pattern.  Handles ``$(( expr ))``
contexts including integer arithmetic, variable resolution, and all
standard operators.
"""

from __future__ import annotations

import ast
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentsh.runtime.state import ShellState


class ArithEvaluator:
    """Evaluate shell arithmetic expressions to integer values.

    Supports: integer literals, ``+``, ``-``, ``*``, ``/``, ``%``,
    parentheses, unary ``+``/``-``, and variable references (``$name``,
    ``${name}``, or bare identifiers).
    """

    def __init__(self, state: ShellState) -> None:
        self.state = state

    def eval_expr(self, expression: str) -> int:
        """Evaluate *expression* and return an integer result.

        Variable references are resolved against the current
        :class:`ShellState`.  Unknown variables default to ``0``.
        On any parse/evaluation error the result is ``0``.
        """
        expr = self._substitute_variables(expression)

        try:
            tree = ast.parse(expr.strip(), mode="eval")
            return self._walk(tree.body)
        except Exception:
            return 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _substitute_variables(self, expression: str) -> str:
        """Replace ``$var``, ``${var}``, and bare identifiers with values."""

        def _replace(m: re.Match[str]) -> str:
            name = m.group(1) or m.group(2) or m.group(3)
            if name.isdigit():
                idx = int(name)
                if 1 <= idx <= len(self.state.positional_params):
                    val = self.state.positional_params[idx - 1]
                    return val if val.lstrip("-").isdigit() else "0"
                return "0"
            val = self.state.get_var(name) or ""
            return val if val.lstrip("-").isdigit() else "0"

        return re.sub(
            r"\$\{(\w+)\}|\$(\w+)|(?<![0-9])([a-zA-Z_]\w*)(?!\w*\()",
            _replace,
            expression,
        )

    def _walk(self, node: ast.expr) -> int:
        """Recursively evaluate an AST node.  Only arithmetic is allowed."""
        match node:
            case ast.Constant(value=int(v)):
                return v
            case ast.UnaryOp(op=ast.USub(), operand=operand):
                return -self._walk(operand)
            case ast.UnaryOp(op=ast.UAdd(), operand=operand):
                return self._walk(operand)
            case ast.BinOp(left=left, op=op, right=right):
                return self._eval_binop(left, op, right)
            case _:
                raise ValueError(f"Unsupported arithmetic node: {type(node).__name__}")

    def _eval_binop(self, left: ast.expr, op: ast.operator, right: ast.expr) -> int:
        lv = self._walk(left)
        rv = self._walk(right)
        match op:
            case ast.Add():
                return lv + rv
            case ast.Sub():
                return lv - rv
            case ast.Mult():
                return lv * rv
            case ast.FloorDiv():
                return lv // rv if rv != 0 else 0
            case ast.Div():
                return int(lv / rv) if rv != 0 else 0
            case ast.Mod():
                return lv % rv if rv != 0 else 0
            case _:
                raise ValueError(
                    f"Unsupported arithmetic operator: {type(op).__name__}"
                )
