"""Builtin command implementations.

Each builtin: (args, state, vfs, io) -> CommandResult
All filesystem interactions go through VFS.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from agentsh.runtime.result import CommandResult

if TYPE_CHECKING:
    from agentsh.exec.redirs import IOContext
    from agentsh.runtime.state import ShellState
    from agentsh.vfs.filesystem import VirtualFilesystem

BuiltinFn = Callable[
    ["list[str]", "ShellState", "VirtualFilesystem", "IOContext"],
    CommandResult,
]


def builtin_echo(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement echo builtin."""
    # Handle -n flag (no trailing newline)
    no_newline = False
    output_args = args

    if args and args[0] == "-n":
        no_newline = True
        output_args = args[1:]

    text = " ".join(output_args)
    if not no_newline:
        text += "\n"
    io.stdout.write(text)
    return CommandResult(exit_code=0)


def builtin_printf(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement printf builtin (simplified)."""
    if not args:
        return CommandResult(exit_code=0)

    fmt = args[0]
    fmt_args = args[1:]

    # Simple format string handling
    result = _simple_printf(fmt, fmt_args)
    io.stdout.write(result)
    return CommandResult(exit_code=0)


def _simple_printf(fmt: str, args: list[str]) -> str:
    """Simple printf-style formatting."""
    result = ""
    arg_idx = 0
    i = 0
    while i < len(fmt):
        if fmt[i] == "\\" and i + 1 < len(fmt):
            escape = fmt[i + 1]
            if escape == "n":
                result += "\n"
            elif escape == "t":
                result += "\t"
            elif escape == "\\":
                result += "\\"
            elif escape == '"':
                result += '"'
            else:
                result += "\\" + escape
            i += 2
        elif fmt[i] == "%" and i + 1 < len(fmt):
            spec = fmt[i + 1]
            arg = args[arg_idx] if arg_idx < len(args) else ""
            arg_idx += 1
            if spec == "s":
                result += arg
            elif spec == "d":
                try:
                    result += str(int(arg))
                except ValueError:
                    result += "0"
            elif spec == "%":
                result += "%"
                arg_idx -= 1  # %% doesn't consume an argument
            else:
                result += "%" + spec
            i += 2
        else:
            result += fmt[i]
            i += 1
    return result


def builtin_cd(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement cd builtin. Changes cwd if target is a VFS directory."""
    if not args:
        target = state.get_var("HOME") or "/"
    elif args[0] == "-":
        target = state.get_var("OLDPWD") or state.cwd
    else:
        target = args[0]

    abs_path = vfs.resolve(target, state.cwd)

    if not vfs.exists(abs_path):
        io.stderr.write(f"cd: {target}: No such file or directory\n")
        return CommandResult(exit_code=1)

    if not vfs.is_dir(abs_path):
        io.stderr.write(f"cd: {target}: Not a directory\n")
        return CommandResult(exit_code=1)

    old_cwd = state.cwd
    state.cwd = abs_path
    state.set_var("OLDPWD", old_cwd)
    state.set_var("PWD", abs_path)
    return CommandResult(exit_code=0)


def builtin_pwd(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement pwd builtin."""
    io.stdout.write(state.cwd + "\n")
    return CommandResult(exit_code=0)


def builtin_export(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement export builtin."""
    if not args:
        # Print all exported variables
        for name, value in sorted(state.exported_env.items()):
            io.stdout.write(f'declare -x {name}="{value}"\n')
        return CommandResult(exit_code=0)

    for arg in args:
        if "=" in arg:
            name, value = arg.split("=", 1)
            state.export_var(name, value)
        else:
            state.export_var(arg)

    return CommandResult(exit_code=0)


def builtin_unset(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement unset builtin."""
    for name in args:
        if name in ("-v", "-f"):
            continue
        state.scope.unset(name)
        state.exported_env.pop(name, None)

    return CommandResult(exit_code=0)


def builtin_true(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    return CommandResult(exit_code=0)


def builtin_false(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    return CommandResult(exit_code=1)


def builtin_exit(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement exit builtin."""
    code = 0
    if args:
        try:
            code = int(args[0])
        except ValueError:
            io.stderr.write(f"exit: {args[0]}: numeric argument required\n")
            code = 2
    raise SystemExit(code)


def builtin_test(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement test/[ builtin.

    Delegates to :class:`BoolEvaluator` for the actual evaluation logic.
    """
    from agentsh.exec.bool_eval import BoolEvaluator

    if args and args[-1] == "]":
        args = args[:-1]

    if not args:
        return CommandResult(exit_code=1)

    evaluator = BoolEvaluator(state, vfs)
    result = evaluator.eval_test(args)
    return CommandResult(exit_code=0 if result else 1)


def builtin_read(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement read builtin (basic)."""
    line = io.stdin.readline()
    if not line:
        return CommandResult(exit_code=1)

    line = line.rstrip("\n")

    if not args:
        state.set_var("REPLY", line)
    elif len(args) == 1:
        state.set_var(args[0], line)
    else:
        parts = line.split(None, len(args) - 1)
        for i, name in enumerate(args):
            state.set_var(name, parts[i] if i < len(parts) else "")

    return CommandResult(exit_code=0)


def builtin_shift(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement shift builtin."""
    n = 1
    if args:
        try:
            n = int(args[0])
        except ValueError:
            io.stderr.write(f"shift: {args[0]}: numeric argument required\n")
            return CommandResult(exit_code=1)

    if n > len(state.positional_params):
        io.stderr.write("shift: shift count out of range\n")
        return CommandResult(exit_code=1)

    state.positional_params = state.positional_params[n:]
    return CommandResult(exit_code=0)


def builtin_return(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement return builtin."""
    code = 0
    if args:
        try:
            code = int(args[0])
        except ValueError:
            code = 1
    raise ReturnSignal(code)


class ReturnSignal(Exception):
    """Signal to return from a function or sourced script."""

    def __init__(self, exit_code: int) -> None:
        self.exit_code = exit_code
        super().__init__()


def builtin_set(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement set builtin (basic option handling)."""
    if not args:
        for name, value in sorted(state.scope.flatten().items()):
            io.stdout.write(f"{name}={value}\n")
        return CommandResult(exit_code=0)

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            state.positional_params = list(args[i + 1 :])
            break
        elif arg.startswith("-") or arg.startswith("+"):
            enable = arg[0] == "-"
            for ch in arg[1:]:
                if ch == "o" and i + 1 < len(args):
                    i += 1
                    _apply_set_o(state, args[i], enable)
                else:
                    _apply_set_flag(state, ch, enable)
        i += 1

    return CommandResult(exit_code=0)


def _apply_set_flag(state: ShellState, ch: str, enable: bool) -> None:
    """Apply a single set flag character."""
    if ch == "e":
        state.options.errexit = enable
    elif ch == "u":
        state.options.nounset = enable
    elif ch == "x":
        state.options.xtrace = enable
    elif ch == "f":
        state.options.noglob = enable


def _apply_set_o(state: ShellState, opt: str, enable: bool) -> None:
    """Apply a set -o / +o option."""
    if opt == "pipefail":
        state.options.pipefail = enable


def builtin_local(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement local builtin (simplified — just sets variables)."""
    for arg in args:
        if "=" in arg:
            name, value = arg.split("=", 1)
            state.set_var(name, value)
        # Declare without value
        elif state.get_var(arg) is None:
            state.set_var(arg, "")
    return CommandResult(exit_code=0)


def builtin_declare(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement declare builtin (simplified)."""
    return builtin_local(args, state, vfs, io)


# ---------------------------------------------------------------------------
# Module-level state for builtins that need persistent storage
# ---------------------------------------------------------------------------

_ALIASES: dict[str, str] = {}
_READONLY: set[str] = set()
_TRAPS: dict[str, str] = {}
_umask_value: int = 0o022


# ---------------------------------------------------------------------------
# alias / unalias
# ---------------------------------------------------------------------------


def builtin_alias(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement alias builtin.

    With no arguments, print all defined aliases.
    With NAME=VALUE arguments, define aliases.
    """
    if not args:
        for name, value in sorted(_ALIASES.items()):
            io.stdout.write(f"alias {name}='{value}'\n")
        return CommandResult(exit_code=0)

    rc = 0
    for arg in args:
        if "=" in arg:
            name, value = arg.split("=", 1)
            _ALIASES[name] = value
        elif arg in _ALIASES:
            io.stdout.write(f"alias {arg}='{_ALIASES[arg]}'\n")
        else:
            io.stderr.write(f"alias: {arg}: not found\n")
            rc = 1
    return CommandResult(exit_code=rc)


def builtin_unalias(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement unalias builtin.

    -a removes all aliases.  Otherwise remove named aliases.
    """
    if not args:
        io.stderr.write("unalias: usage: unalias [-a] name [name ...]\n")
        return CommandResult(exit_code=2)

    if "-a" in args:
        _ALIASES.clear()
        return CommandResult(exit_code=0)

    rc = 0
    for name in args:
        if name in _ALIASES:
            del _ALIASES[name]
        else:
            io.stderr.write(f"unalias: {name}: not found\n")
            rc = 1
    return CommandResult(exit_code=rc)


# ---------------------------------------------------------------------------
# type
# ---------------------------------------------------------------------------


def builtin_type(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement type builtin.

    Print what each NAME resolves to: alias, function, builtin, or not found.
    """
    if not args:
        return CommandResult(exit_code=0)

    rc = 0
    for name in args:
        if name in _ALIASES:
            io.stdout.write(f"{name} is aliased to '{_ALIASES[name]}'\n")
        elif name in state.functions:
            io.stdout.write(f"{name} is a function\n")
        elif name in BUILTINS:
            io.stdout.write(f"{name} is a shell builtin\n")
        else:
            io.stderr.write(f"type: {name}: not found\n")
            rc = 1
    return CommandResult(exit_code=rc)


# ---------------------------------------------------------------------------
# readonly
# ---------------------------------------------------------------------------


def builtin_readonly(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement readonly builtin.

    Mark variables as readonly.  With NAME=VALUE, set and mark.
    With no args, print all readonly variables.
    """
    if not args:
        for name in sorted(_READONLY):
            val = state.get_var(name) or ""
            io.stdout.write(f'declare -r {name}="{val}"\n')
        return CommandResult(exit_code=0)

    for arg in args:
        if "=" in arg:
            name, value = arg.split("=", 1)
            if name in _READONLY:
                io.stderr.write(f"readonly: {name}: readonly variable\n")
                return CommandResult(exit_code=1)
            state.set_var(name, value)
            _READONLY.add(name)
        else:
            _READONLY.add(arg)

    return CommandResult(exit_code=0)


# ---------------------------------------------------------------------------
# let
# ---------------------------------------------------------------------------


def builtin_let(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement let builtin.

    Evaluate arithmetic expressions.  Return 0 if last result != 0, else 1.
    """
    if not args:
        io.stderr.write("let: expression expected\n")
        return CommandResult(exit_code=2)

    from agentsh.exec.arith_eval import ArithEvaluator

    arith = io.executor.arith_ev if io.executor is not None else ArithEvaluator(state)

    last_result = 0
    for expr in args:
        last_result = arith.eval_expr(expr)

    # let returns 0 if last result is non-zero, 1 if zero
    return CommandResult(exit_code=0 if last_result != 0 else 1)


# ---------------------------------------------------------------------------
# getopts
# ---------------------------------------------------------------------------


def builtin_getopts(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement getopts builtin (basic).

    Usage: getopts OPTSTRING NAME [ARGS...]
    Sets NAME to current option, OPTARG to argument, OPTIND to index.
    """
    if len(args) < 2:
        io.stderr.write("getopts: usage: getopts optstring name [arg ...]\n")
        return CommandResult(exit_code=2)

    optstring = args[0]
    varname = args[1]
    opt_args = args[2:] if len(args) > 2 else list(state.positional_params)

    optind_str = state.get_var("OPTIND") or "1"
    try:
        optind = int(optind_str)
    except ValueError:
        optind = 1

    # Convert to 0-based index (OPTIND is 1-based)
    idx = optind - 1

    if idx >= len(opt_args):
        state.set_var(varname, "?")
        return CommandResult(exit_code=1)

    current = opt_args[idx]
    if not current.startswith("-") or current in {"-", "--"}:
        state.set_var(varname, "?")
        return CommandResult(exit_code=1)

    opt_char = current[1] if len(current) > 1 else "?"

    if opt_char in optstring:
        state.set_var(varname, opt_char)
        # Check if this option expects an argument
        opt_pos = optstring.index(opt_char)
        if opt_pos + 1 < len(optstring) and optstring[opt_pos + 1] == ":":
            # Argument expected
            if len(current) > 2:
                # Argument is part of same string: -fVALUE
                state.set_var("OPTARG", current[2:])
            elif idx + 1 < len(opt_args):
                state.set_var("OPTARG", opt_args[idx + 1])
                optind += 1
            else:
                io.stderr.write(f"getopts: option requires an argument -- {opt_char}\n")
                state.set_var(varname, "?")
                state.set_var("OPTIND", str(optind + 1))
                return CommandResult(exit_code=0)
        else:
            state.set_var("OPTARG", "")
    else:
        io.stderr.write(f"getopts: illegal option -- {opt_char}\n")
        state.set_var(varname, "?")

    state.set_var("OPTIND", str(optind + 1))
    return CommandResult(exit_code=0)


# ---------------------------------------------------------------------------
# hash
# ---------------------------------------------------------------------------


def builtin_hash(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement hash builtin (virtual no-op).

    -r clears the (virtual) hash table.  Named commands print 'not found'.
    """
    if not args or args == ["-r"]:
        return CommandResult(exit_code=0)

    rc = 0
    for name in args:
        if name == "-r":
            continue
        io.stderr.write(f"hash: {name}: not found\n")
        rc = 1
    return CommandResult(exit_code=rc)


# ---------------------------------------------------------------------------
# help
# ---------------------------------------------------------------------------

_BUILTIN_HELP: dict[str, str] = {
    "echo": "echo [-n] [arg ...] — write arguments to standard output",
    "printf": "printf FORMAT [ARG ...] — formatted output",
    "cd": "cd [dir] — change working directory",
    "pwd": "pwd — print working directory",
    "export": "export [NAME=VALUE ...] — set export attribute for variables",
    "unset": "unset [NAME ...] — unset variables",
    "true": "true — return success",
    "false": "false — return failure",
    "exit": "exit [N] — exit the shell",
    "test": "test EXPR — evaluate conditional expression",
    "[": "[ EXPR ] — evaluate conditional expression",
    "read": "read [NAME ...] — read a line from stdin",
    "shift": "shift [N] — shift positional parameters",
    "return": "return [N] — return from a function",
    "set": "set [option ...] [-- arg ...] — set shell options and positional params",
    "local": "local [NAME=VALUE ...] — define local variables",
    "declare": "declare [NAME=VALUE ...] — declare variables",
    "alias": "alias [NAME=VALUE ...] — define or display aliases",
    "unalias": "unalias [-a] NAME ... — remove aliases",
    "type": "type NAME ... — display information about command type",
    "readonly": "readonly [NAME=VALUE ...] — mark variables as readonly",
    "let": "let EXPR ... — evaluate arithmetic expressions",
    "getopts": "getopts OPTSTRING NAME [ARGS ...] — parse option arguments",
    "hash": "hash [-r] [NAME ...] — remember command locations (virtual no-op)",
    "help": "help [COMMAND] — display help for builtins",
    "eval": "eval [ARG ...] — execute arguments as a shell command",
    "exec": "exec COMMAND [ARG ...] — replace shell with command",
    "trap": "trap [ACTION] [SIGNAL ...] — trap signals (virtual)",
    "ulimit": "ulimit [-a] [-n N] — display or set resource limits (virtual)",
    "umask": "umask [MODE] — display or set file creation mask",
    "wait": "wait [PID ...] — wait for background jobs (no-op)",
    "jobs": "jobs — list background jobs (none in virtual shell)",
    "bg": "bg [JOB] — resume job in background (no-op)",
    "fg": "fg [JOB] — resume job in foreground (no-op)",
    "times": "times — display process times (virtual)",
    "source": "source FILE — execute commands from file",
    ".": ". FILE — execute commands from file",
}


def builtin_help(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement help builtin.

    With no args, list all builtins.  With a command name, show its help.
    """
    if not args:
        io.stdout.write("Shell builtins:\n")
        for name in sorted(BUILTINS):
            io.stdout.write(f"  {name}\n")
        return CommandResult(exit_code=0)

    rc = 0
    for name in args:
        if name in _BUILTIN_HELP:
            io.stdout.write(f"{_BUILTIN_HELP[name]}\n")
        elif name in BUILTINS:
            io.stdout.write(f"{name}: no help available\n")
        else:
            io.stderr.write(f"help: no help topics match '{name}'\n")
            rc = 1
    return CommandResult(exit_code=rc)


# ---------------------------------------------------------------------------
# eval
# ---------------------------------------------------------------------------


def builtin_eval(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement eval builtin.

    Join args with spaces, parse and execute as a script.
    """
    if not args:
        return CommandResult(exit_code=0)

    script = " ".join(args)

    if io.executor is None:
        io.stderr.write("eval: no executor available\n")
        return CommandResult(exit_code=1)

    from agentsh.parser.frontend import parse_script
    from agentsh.parser.normalize import normalize

    parse_result = parse_script(script)
    if parse_result.has_errors:
        io.stderr.write("eval: syntax error\n")
        return CommandResult(exit_code=2)

    program, _ = normalize(parse_result.root_node, script)
    return io.executor.execute_node(program, io)


# ---------------------------------------------------------------------------
# exec — run command in virtual shell (no real process replacement)
# ---------------------------------------------------------------------------


def builtin_exec(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement the exec builtin.

    In the virtual shell, just run the command (no process replacement).
    """
    if not args:
        return CommandResult(exit_code=0)

    if io.executor is None:
        io.stderr.write("exec: no executor available\n")
        return CommandResult(exit_code=1)

    return io.executor.execute_argv(args, io)


# ---------------------------------------------------------------------------
# trap
# ---------------------------------------------------------------------------


def builtin_trap(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement trap builtin (virtual).

    Store trap handlers but do not actually handle signals.
    With no args, print current traps.
    """
    if not args:
        for signal, action in sorted(_TRAPS.items()):
            io.stdout.write(f"trap -- '{action}' {signal}\n")
        return CommandResult(exit_code=0)

    if len(args) == 1:
        # Single arg — treat as signal name to reset
        _TRAPS.pop(args[0], None)
        return CommandResult(exit_code=0)

    action = args[0]
    for signal in args[1:]:
        if action == "-":
            _TRAPS.pop(signal, None)
        else:
            _TRAPS[signal] = action

    return CommandResult(exit_code=0)


# ---------------------------------------------------------------------------
# ulimit
# ---------------------------------------------------------------------------


def builtin_ulimit(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement ulimit builtin (virtual).

    Print virtual resource limits.
    """
    if not args or "-a" in args:
        io.stdout.write("core file size          (blocks, -c) unlimited\n")
        io.stdout.write("data seg size           (kbytes, -d) unlimited\n")
        io.stdout.write("file size               (blocks, -f) unlimited\n")
        io.stdout.write("max locked memory       (kbytes, -l) unlimited\n")
        io.stdout.write("max memory size         (kbytes, -m) unlimited\n")
        io.stdout.write("open files                      (-n) 1024\n")
        io.stdout.write("pipe size            (512 bytes, -p) 8\n")
        io.stdout.write("stack size              (kbytes, -s) 8192\n")
        io.stdout.write("cpu time               (seconds, -t) unlimited\n")
        io.stdout.write("max user processes              (-u) unlimited\n")
        io.stdout.write("virtual memory          (kbytes, -v) unlimited\n")
        return CommandResult(exit_code=0)

    i = 0
    while i < len(args):
        if args[i] == "-n":
            if i + 1 < len(args):
                # Setting open files limit (virtual no-op)
                i += 2
            else:
                io.stdout.write("1024\n")
                i += 1
        else:
            i += 1

    return CommandResult(exit_code=0)


# ---------------------------------------------------------------------------
# umask
# ---------------------------------------------------------------------------


def builtin_umask(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement umask builtin.

    Get or set the file creation mask.
    """
    global _umask_value  # noqa: PLW0603

    if not args:
        io.stdout.write(f"{_umask_value:04o}\n")
        return CommandResult(exit_code=0)

    try:
        _umask_value = int(args[0], 8)
    except ValueError:
        io.stderr.write(f"umask: {args[0]}: invalid octal number\n")
        return CommandResult(exit_code=1)

    return CommandResult(exit_code=0)


# ---------------------------------------------------------------------------
# wait / jobs / bg / fg
# ---------------------------------------------------------------------------


def builtin_wait(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement wait builtin (no-op — no background processes)."""
    return CommandResult(exit_code=0)


def builtin_jobs(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement jobs builtin (no background jobs in virtual shell)."""
    return CommandResult(exit_code=0)


def builtin_bg(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement bg builtin (no-op)."""
    return CommandResult(exit_code=0)


def builtin_fg(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement fg builtin (no-op)."""
    return CommandResult(exit_code=0)


# ---------------------------------------------------------------------------
# times
# ---------------------------------------------------------------------------


def builtin_times(
    args: list[str], state: ShellState, vfs: VirtualFilesystem, io: IOContext
) -> CommandResult:
    """Implement times builtin (virtual — always zero)."""
    io.stdout.write("0m0.000s 0m0.000s\n")
    io.stdout.write("0m0.000s 0m0.000s\n")
    return CommandResult(exit_code=0)


# Registry of all builtins
BUILTINS: dict[str, BuiltinFn] = {
    "echo": builtin_echo,
    "printf": builtin_printf,
    "cd": builtin_cd,
    "pwd": builtin_pwd,
    "export": builtin_export,
    "unset": builtin_unset,
    "true": builtin_true,
    "false": builtin_false,
    "exit": builtin_exit,
    "test": builtin_test,
    "[": builtin_test,
    "read": builtin_read,
    "shift": builtin_shift,
    "return": builtin_return,
    "set": builtin_set,
    "local": builtin_local,
    "declare": builtin_declare,
    "alias": builtin_alias,
    "unalias": builtin_unalias,
    "type": builtin_type,
    "readonly": builtin_readonly,
    "let": builtin_let,
    "getopts": builtin_getopts,
    "hash": builtin_hash,
    "help": builtin_help,
    "eval": builtin_eval,
    "exec": builtin_exec,
    "trap": builtin_trap,
    "ulimit": builtin_ulimit,
    "umask": builtin_umask,
    "wait": builtin_wait,
    "jobs": builtin_jobs,
    "bg": builtin_bg,
    "fg": builtin_fg,
    "times": builtin_times,
}
