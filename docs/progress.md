# Progress

## 2026-03-22: v0.2.0 — Bash syntax expansion

### Stats
- 1641 tests passing (pytest), including 202 differential tests against bash
- All quality gates clean: ruff, pyright (strict), tach, ruff format
- 38 shell builtins + 109 virtual commands
- LangChain tools (parse/plan/run), CLI with parse/plan/run subcommands
- Virtual filesystem, virtual execution, no subprocess anywhere

### New features (6 phases)
1. **Parameter expansion operators**: `${#x}` (length), `${x:0:3}` (substring), `${x/p/r}` and `${x//p/r}` (replace), `${x^}` / `${x^^}` (uppercase), `${x,}` / `${x,,}` (lowercase)
2. **Here-documents and here-strings**: `<<EOF` with expansion, `<<'EOF'` without expansion, `<<-EOF` (tab strip), `<<<word`
3. **C-style for loops**: `for (( i=0; i<n; i++ ))` with full arithmetic statements — assignments, `++`/`--`, compound assigns (`+=`, `-=`, `*=`, `/=`, `%=`), comma expressions
4. **Array variables**: `arr=(a b c)`, `${arr[0]}`, `${arr[@]}`, `${#arr[@]}`, `arr[i]=val`, iteration with `for x in "${arr[@]}"`
5. **`[[ ]]` extended test**: glob matching (`==`), regex matching (`=~`) with `BASH_REMATCH`, `&&`/`||` inside `[[ ]]`, grouping with `( )`, negation
6. **Process substitution**: `<(cmd)` and `>(cmd)` via temporary VFS files

### Arithmetic evaluator extensions
- Comparisons: `<`, `>`, `<=`, `>=`, `==`, `!=`
- Logical: `&&`, `||`, `!`
- Bitwise: `&`, `|`, `^`, `<<`, `>>`
- Ternary: `a ? b : c`
- Power: `**`
- Braced expansions in arithmetic context: `${#arr[@]}`, `${arr[n]}`

### Known limitations
- No interactive mode / REPL
- No streaming events or MCP server
- Process substitution `>(cmd)` creates a placeholder file (full pipe-back deferred)
- No associative arrays (`declare -A`)
- No `select` loops, `coproc`, or job control execution

## 2026-03-22: v0.1.0 — Initial release
- 1537 tests passing (pytest)
- ruff, pyright (strict): clean
- 202 differential tests against bash, 100% pass rate
- Full control flow: if/elif/else, while, until, for-in, case/esac
- Functions, subshells, brace groups, pipelines, and/or lists
- LangChain tools (parse/plan/run) implemented
- CLI with parse/plan/run subcommands
- Virtual filesystem, virtual execution, no subprocess anywhere
