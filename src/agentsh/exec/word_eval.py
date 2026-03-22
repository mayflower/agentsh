"""Word evaluator — expands shell words through the full expansion pipeline.

Follows the Oils split-evaluator pattern.  Consolidates the expansion
logic previously spread across ``semantics/expand.py`` into a stateful
class that holds references to the VFS, shell state, and (via a
back-pointer) the command evaluator for command-substitution callbacks.

Expansion pipeline:
  tilde -> parameter -> command substitution -> arithmetic
  -> quote removal -> word splitting -> globbing
"""

from __future__ import annotations

import fnmatch as _fnmatch
from typing import TYPE_CHECKING, Protocol

from agentsh.ast.words import (
    ArithmeticExpansionSegment,
    CommandSubstitutionSegment,
    DoubleQuotedSegment,
    GlobSegment,
    LiteralSegment,
    ParameterExpansionSegment,
    SingleQuotedSegment,
    WordSegment,
)

if TYPE_CHECKING:
    from agentsh.ast.nodes import Word
    from agentsh.exec.arith_eval import ArithEvaluator
    from agentsh.runtime.state import ShellState
    from agentsh.vfs.filesystem import VirtualFilesystem


class CommandSubstitutionHook(Protocol):
    """Callable that executes a command string and returns its stdout."""

    def __call__(self, command: str) -> str: ...


class WordEvaluator:
    """Expand shell words to their final string values.

    Holds references to:
      - *state*: the mutable :class:`ShellState`
      - *vfs*: the :class:`VirtualFilesystem` (for globbing and tilde)
      - *arith_ev*: the :class:`ArithEvaluator`
      - *cmdsub_hook*: an optional callback for ``$(...)`` expansion
    """

    def __init__(
        self,
        state: ShellState,
        vfs: VirtualFilesystem,
        arith_ev: ArithEvaluator,
        cmdsub_hook: CommandSubstitutionHook | None = None,
    ) -> None:
        self.state = state
        self.vfs = vfs
        self.arith_ev = arith_ev
        self.cmdsub_hook = cmdsub_hook

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def eval_word(self, word: Word) -> list[str]:
        """Expand a Word into a list of strings (post word-splitting/globbing).

        For unquoted contexts, word splitting and globbing apply.
        For quoted contexts, the result is a single string.
        """
        parts = self._expand_segments(word.segments)
        result_fields = self._word_split_and_join(parts)

        final: list[str] = []
        for field_text, has_glob in result_fields:
            if has_glob:
                matches = self.vfs.glob(field_text, self.state.cwd)
                if matches:
                    final.extend(matches)
                else:
                    final.append(field_text)
            else:
                final.append(field_text)

        return final if final else [""]

    def eval_word_single(self, word: Word) -> str:
        """Expand a Word into a single string (no word splitting/globbing).

        Used for assignment values, redirect targets, etc.
        """
        parts = self._expand_segments(word.segments)
        return "".join(p.text for p in parts)

    # ------------------------------------------------------------------
    # Segment expansion
    # ------------------------------------------------------------------

    def _expand_segments(
        self, segments: tuple[WordSegment, ...]
    ) -> list[_ExpandedPart]:
        parts: list[_ExpandedPart] = []
        for seg in segments:
            parts.extend(self._expand_segment(seg))
        return parts

    def _expand_segment(self, seg: WordSegment) -> list[_ExpandedPart]:
        match seg:
            case LiteralSegment(value=text):
                if text == "~" or text.startswith("~/"):
                    home = self.state.get_var("HOME") or "/"
                    text = home + text[1:]
                return [_ExpandedPart(text=text, quoted=False)]

            case SingleQuotedSegment(value=text):
                return [_ExpandedPart(text=text, quoted=True)]

            case DoubleQuotedSegment(segments=inner_segs):
                inner_parts = self._expand_segments(inner_segs)
                text = "".join(p.text for p in inner_parts)
                return [_ExpandedPart(text=text, quoted=True)]

            case ParameterExpansionSegment():
                return [self._expand_parameter(seg)]

            case CommandSubstitutionSegment(command=command):
                if self.cmdsub_hook is not None:
                    result = self.cmdsub_hook(command)
                    result = result.rstrip("\n")
                    return [_ExpandedPart(text=result, quoted=False)]
                return [_ExpandedPart(text="", quoted=False)]

            case ArithmeticExpansionSegment(expression=expression):
                arith_result = self.arith_ev.eval_expr(expression)
                return [_ExpandedPart(text=str(arith_result), quoted=False)]

            case GlobSegment(pattern=pattern):
                return [_ExpandedPart(text=pattern, quoted=False, is_glob=True)]

            case _:
                return [_ExpandedPart(text="", quoted=False)]

    # ------------------------------------------------------------------
    # Parameter expansion
    # ------------------------------------------------------------------

    def _expand_parameter(self, seg: ParameterExpansionSegment) -> _ExpandedPart:
        name = seg.name

        # Special parameters
        match name:
            case "?":
                return _ExpandedPart(text=str(self.state.last_status), quoted=False)
            case "$":
                return _ExpandedPart(text="1", quoted=False)
            case "#":
                return _ExpandedPart(
                    text=str(len(self.state.positional_params)), quoted=False
                )
            case "0":
                return _ExpandedPart(text="agentsh", quoted=False)
            case "@" | "*":
                return _ExpandedPart(
                    text=" ".join(self.state.positional_params), quoted=False
                )
            case _ if name.isdigit():
                idx = int(name)
                if 1 <= idx <= len(self.state.positional_params):
                    return _ExpandedPart(
                        text=self.state.positional_params[idx - 1], quoted=False
                    )
                return _ExpandedPart(text="", quoted=False)
            case _:
                pass  # fall through to variable lookup

        value = self.state.get_var(name)

        if seg.operator is None:
            return _ExpandedPart(text=value or "", quoted=False)

        return self._apply_parameter_operator(name, value, seg.operator, seg.argument)

    def _apply_parameter_operator(
        self,
        name: str,
        value: str | None,
        op: str,
        argument: str | None,
    ) -> _ExpandedPart:
        arg = self._expand_arg_string(argument or "")

        match op:
            case ":-":
                return _ExpandedPart(text=value if value else arg, quoted=False)
            case "-":
                return _ExpandedPart(text=arg if value is None else value, quoted=False)
            case ":+":
                return _ExpandedPart(text=arg if value else "", quoted=False)
            case "+":
                return _ExpandedPart(
                    text=arg if value is not None else "", quoted=False
                )
            case ":=":
                if not value:
                    self.state.set_var(name, arg)
                    return _ExpandedPart(text=arg, quoted=False)
                return _ExpandedPart(text=value, quoted=False)
            case "=":
                if value is None:
                    self.state.set_var(name, arg)
                    return _ExpandedPart(text=arg, quoted=False)
                return _ExpandedPart(text=value, quoted=False)
            case ":?" | "?":
                check_empty = op == ":?"
                if value is None or (check_empty and not value):
                    msg = arg or f"{name}: parameter null or not set"
                    raise ValueError(msg)
                return _ExpandedPart(text=value, quoted=False)
            case "#":
                return self._strip_prefix(value, arg, greedy=False)
            case "##":
                return self._strip_prefix(value, arg, greedy=True)
            case "%":
                return self._strip_suffix(value, arg, greedy=False)
            case "%%":
                return self._strip_suffix(value, arg, greedy=True)
            case _:
                return _ExpandedPart(text=value or "", quoted=False)

    def _strip_prefix(
        self, value: str | None, pattern: str, *, greedy: bool
    ) -> _ExpandedPart:
        if not value:
            return _ExpandedPart(text=value or "", quoted=False)
        if greedy:
            for i in range(len(value), -1, -1):
                if _fnmatch.fnmatch(value[:i], pattern):
                    return _ExpandedPart(text=value[i:], quoted=False)
        else:
            for i in range(len(value) + 1):
                if _fnmatch.fnmatch(value[:i], pattern):
                    return _ExpandedPart(text=value[i:], quoted=False)
        return _ExpandedPart(text=value, quoted=False)

    def _strip_suffix(
        self, value: str | None, pattern: str, *, greedy: bool
    ) -> _ExpandedPart:
        if not value:
            return _ExpandedPart(text=value or "", quoted=False)
        if greedy:
            for i in range(len(value) + 1):
                if _fnmatch.fnmatch(value[i:], pattern):
                    return _ExpandedPart(text=value[:i], quoted=False)
        else:
            for i in range(len(value), -1, -1):
                if _fnmatch.fnmatch(value[i:], pattern):
                    return _ExpandedPart(text=value[:i], quoted=False)
        return _ExpandedPart(text=value, quoted=False)

    # ------------------------------------------------------------------
    # Helper: expand $VAR inside parameter-expansion arguments
    # ------------------------------------------------------------------

    def _expand_arg_string(self, arg: str) -> str:
        if "$" not in arg:
            return arg
        result = ""
        i = 0
        while i < len(arg):
            if arg[i] == "$" and i + 1 < len(arg):
                if arg[i + 1] == "{":
                    depth = 1
                    j = i + 2
                    while j < len(arg) and depth > 0:
                        if arg[j] == "{":
                            depth += 1
                        elif arg[j] == "}":
                            depth -= 1
                        j += 1
                    inner = arg[i + 2 : j - 1]
                    for inner_op in (
                        ":-",
                        ":+",
                        ":=",
                        ":?",
                        "-",
                        "+",
                        "=",
                        "?",
                    ):
                        idx = inner.find(inner_op)
                        if idx > 0:
                            seg = ParameterExpansionSegment(
                                name=inner[:idx],
                                operator=inner_op,
                                argument=inner[idx + len(inner_op) :],
                            )
                            result += self._expand_parameter(seg).text
                            break
                    else:
                        val = self.state.get_var(inner) or ""
                        result += val
                    i = j
                else:
                    j = i + 1
                    while j < len(arg) and (arg[j].isalnum() or arg[j] == "_"):
                        j += 1
                    name = arg[i + 1 : j]
                    result += self.state.get_var(name) or ""
                    i = j
            else:
                result += arg[i]
                i += 1
        return result

    # ------------------------------------------------------------------
    # Word splitting & IFS handling
    # ------------------------------------------------------------------

    def _word_split_and_join(
        self, parts: list[_ExpandedPart]
    ) -> list[tuple[str, bool]]:
        ifs = self.state.get_var("IFS")
        if ifs is None:
            ifs = " \t\n"

        fields: list[tuple[str, bool]] = []
        current = ""
        current_glob = False

        for part in parts:
            if part.quoted:
                current += part.text
            elif part.is_glob:
                current += part.text
                current_glob = True
            else:
                text = part.text
                if not text:
                    continue
                segments = _split_on_ifs(text, ifs)
                if len(segments) <= 1:
                    current += text
                else:
                    current += segments[0]
                    if current:
                        fields.append((current, current_glob))
                    for seg in segments[1:-1]:
                        if seg:
                            fields.append((seg, False))
                    current = segments[-1]
                    current_glob = False

        if current:
            fields.append((current, current_glob))

        return fields


# ---------------------------------------------------------------------------
# Internal helpers (module-level)
# ---------------------------------------------------------------------------


class _ExpandedPart:
    """A piece of expanded text with quoting metadata."""

    __slots__ = ("is_glob", "quoted", "text")

    def __init__(self, text: str, quoted: bool = False, is_glob: bool = False) -> None:
        self.text = text
        self.quoted = quoted
        self.is_glob = is_glob


def _split_on_ifs(text: str, ifs: str) -> list[str]:
    """Split *text* on IFS characters."""
    if not ifs:
        return [text]

    result: list[str] = []
    current = ""
    for char in text:
        if char in ifs:
            result.append(current)
            current = ""
        else:
            current += char
    result.append(current)
    return result
