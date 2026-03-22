"""Boolean/test evaluator — implements ``test`` / ``[`` logic.

Follows the Oils split-evaluator pattern.  Extracted from ``builtins.py``
so the evaluation logic can be reused (e.g. inside ``[[ ]]`` in the
future) without depending on the builtin dispatch layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentsh.runtime.state import ShellState
    from agentsh.vfs.filesystem import VirtualFilesystem


class BoolEvaluator:
    """Evaluate POSIX ``test`` expressions against VFS and shell state.

    Supports unary file tests (``-f``, ``-d``, ``-e``, ``-r``, ``-w``,
    ``-x``, ``-s``), string tests (``-z``, ``-n``), string comparison
    (``=``, ``==``, ``!=``), integer comparison (``-eq``, ``-ne``,
    ``-lt``, ``-gt``, ``-le``, ``-ge``), logical operators (``-a``,
    ``-o``, ``!``), and single-argument truth tests.
    """

    def __init__(self, state: ShellState, vfs: VirtualFilesystem) -> None:
        self.state = state
        self.vfs = vfs

    def eval_test(self, args: list[str]) -> bool:
        """Evaluate *args* as a ``test`` expression.

        The caller is responsible for stripping a trailing ``]`` when
        the command was invoked as ``[``.
        """
        if not args:
            return False

        if len(args) == 1:
            return len(args[0]) > 0

        if len(args) == 2:
            return self._eval_unary(args[0], args[1])

        if len(args) == 3:
            return self._eval_binary(args[0], args[1], args[2])

        if len(args) == 4 and args[0] == "!":
            return not self.eval_test(args[1:])

        return False

    # ------------------------------------------------------------------
    # Unary operators
    # ------------------------------------------------------------------

    def _eval_unary(self, op: str, operand: str) -> bool:
        match op:
            case "-f":
                return self.vfs.is_file(self.vfs.resolve(operand, self.state.cwd))
            case "-d":
                return self.vfs.is_dir(self.vfs.resolve(operand, self.state.cwd))
            case "-e":
                return self.vfs.exists(self.vfs.resolve(operand, self.state.cwd))
            case "-z":
                return len(operand) == 0
            case "-n":
                return len(operand) > 0
            case "!":
                return not self.eval_test([operand])
            case "-r" | "-w" | "-x":
                return self.vfs.exists(self.vfs.resolve(operand, self.state.cwd))
            case "-s":
                abs_path = self.vfs.resolve(operand, self.state.cwd)
                if self.vfs.is_file(abs_path):
                    return len(self.vfs.read(abs_path)) > 0
                return False
            case _:
                return False

    # ------------------------------------------------------------------
    # Binary operators
    # ------------------------------------------------------------------

    def _eval_binary(self, left: str, op: str, right: str) -> bool:
        match op:
            case "=" | "==":
                return left == right
            case "!=":
                return left != right
            case "-eq" | "-ne" | "-lt" | "-gt" | "-le" | "-ge":
                return self._eval_integer_cmp(left, op, right)
            case "-a":
                return self.eval_test([left]) and self.eval_test([right])
            case "-o":
                return self.eval_test([left]) or self.eval_test([right])
            case _:
                return False

    def _eval_integer_cmp(self, left: str, op: str, right: str) -> bool:
        try:
            lv, rv = int(left), int(right)
        except ValueError:
            return False

        match op:
            case "-eq":
                return lv == rv
            case "-ne":
                return lv != rv
            case "-lt":
                return lv < rv
            case "-gt":
                return lv > rv
            case "-le":
                return lv <= rv
            case "-ge":
                return lv >= rv
            case _:
                return False
