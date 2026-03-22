
# PRD: Python-basierter Bash-Syntax-Parser und Agent-Executor
## Claude-Code-optimierte Projektfassung mit inkrementellen Prompts

Version: 1.0  
Status: Draft / ready for execution  
Ziel-Repository: `agentsh`  
Primäre Sprache: Python 3.12+  
Primäres Parsing-Frontend: `tree-sitter` + `tree-sitter-bash`  
Primäres Ziel: Eine kontrollierte Shell-Engine mit Bash-kompatibler Syntaxoberfläche, eigener AST/Semantik und policy-gesteuerter Ausführung für Agent-Workflows.

---

## 1. Produktziel

Wir bauen eine Python-Bibliothek und CLI, die einen definierten Bash-Subset zuverlässig parsen, in einen normierten AST überführen, relevante Shell-Expansionen korrekt modellieren und Kommandos sicher ausführen kann. Das System ist **nicht** als dünner Wrapper um `/bin/bash` gedacht, sondern als **kontrollierbare Ausführungs-Engine für Agents**.

Das System muss drei Betriebsarten unterstützen:

1. **Parse only**  
   Skript analysieren, AST und Diagnoseobjekte liefern.

2. **Plan / Dry-run**  
   Geplante Ausführung, Effekte, Risikoindikatoren, Tool- und Dateizugriffe ableiten, ohne reale Änderungen auszuführen.

3. **Execute**  
   Kommandos in einer kontrollierten Runtime ausführen, mit Unterscheidung zwischen:
   - Python-Builtins
   - nativen Binaries
   - Agent-Tools / Tool-Backends

---

## 2. Warum dieses Produkt

Agents brauchen häufig eine Shell-artige Kontrollsprache für:
- dateibasierte Workflows,
- Pipelines,
- kleine Automatisierungen,
- Tool-Orchestrierung,
- replizierbare lokale Aufgaben.

Direktes Ausführen beliebiger Shell-Strings über eine Host-Shell ist dafür ungeeignet, weil:
- Syntax- und Quoting-Fehler schwer nachvollziehbar sind,
- Effekte vorab kaum planbar sind,
- Sicherheitsgrenzen unklar bleiben,
- Builtins, Shell-State und Prozesskontext nicht sauber beobachtbar sind,
- Agent-Tools nicht auf derselben semantischen Ebene wie Shell-Kommandos modelliert werden.

Das Produkt schließt diese Lücke mit einer Shell-Engine, die **Bash-artig schreibt**, aber **agentisch kontrolliert** arbeitet.

---

## 3. Produktprinzipien

### 3.1 Semantik vor String-Hacking
Shell-Wörter werden nicht als rohe Strings behandelt, sondern als strukturierte Segmente mit Quoting- und Expansionskontext.

### 3.2 Parser und Executor sind getrennt
CST/Parsing, AST-Normalisierung, Expansion und Ausführung sind getrennte Schichten.

### 3.3 Security by construction
Kein implizites Delegieren an `shell=True`. Externe Prozesse laufen nur über explizite Backends und Policies.

### 3.4 Agent-first observability
Jeder relevante Schritt muss inspizierbar sein:
- Parser-Diagnosen,
- AST,
- Expansionsschritte,
- Ausführungsplan,
- State-Mutationen,
- stdout/stderr-Events.

### 3.5 Inkrementelle Lieferbarkeit
Das Produkt wird in strikt testbaren Phasen gebaut; jede Phase muss isoliert nützlich und releasebar sein.

---

## 4. Zielgruppen und zentrale Use Cases

### 4.1 Zielgruppen
- Agent-Plattform-Teams
- Entwickler von Coding-Agents
- Workflow-/Automation-Teams
- Sicherheitsbewusste Orchestrierungs-Stacks
- Forschungsteams für Tool-Use und Execution Planning

### 4.2 Primäre Use Cases
1. Ein Agent soll ein Shell-Skript lesen und die geplanten Effekte erklären.
2. Ein Agent soll ein Skript sicher in einer Sandbox ausführen.
3. Ein Agent soll Shell-Kommandos mit internen Tools kombinieren.
4. Ein Agent soll Skripte analysieren, transformieren und mit Tests absichern.
5. Ein Agent soll Shell-ähnliche Automatisierungen ausführen, ohne volle Bash-Unsicherheit zu übernehmen.

---

## 5. Umfang

## 5.1 MVP Scope
Der MVP umfasst:

### Syntax
- simple commands
- assignment words
- quotes (single, double, mixed words)
- redirections
- pipelines
- lists (`;`, newline)
- and/or lists (`&&`, `||`)
- grouping (`{ ...; }`)
- subshells (`( ... )`)
- function definitions (Phase 8)
- here-doc syntax (erst Parse + AST, Execution später gestuft)

### Expansionen (MVP stufenweise)
- literal handling
- quote removal
- tilde expansion
- parameter/variable expansion (`$var`, `${var}`)
- special params (`$?`, `$$`) soweit sinnvoll
- command substitution `$(...)`
- word splitting
- filename expansion / globbing
- ausgewählte arithmetic expansion (Phase 8 oder später)

### Execution
- Builtins:
  - `cd`
  - `pwd`
  - `echo`
  - `printf`
  - `export`
  - `unset`
  - `true`
  - `false`
  - `test`
  - `[`
  - `exit`
  - `.`
  - `source`
- externe Programme über kontrolliertes Backend
- Tool-Registry für agentische Kommandos
- Dry-run / Plan-Modus
- Event-Stream / Trace-Modus

### Sicherheit
- keine normale Host-Shell im Default-Path
- Policy-Layer für Allowlist / Denylist / Risiken
- Timeouts
- Prozessgruppen-Management
- workspace-begrenzte Dateizugriffe im Default-Profil

## 5.2 Nicht im MVP
- interaktive Shell
- Job Control
- Prompt-Rendering / REPL-History
- vollständige Alias-Semantik
- History expansion
- `coproc`
- `select`
- `trap`-Komplettimplementierung
- volle Bash-Kompatibilität
- vollständige Array-Semantik in der ersten Release-Linie
- process substitution im ersten Release
- `[[ ... ]]` mit vollständiger Bash-Kompatibilität im ersten Release

---

## 6. Erfolgskriterien

### 6.1 Funktional
- definierter Syntax-Subset wird robust geparst
- AST-Knoten haben stabile Source-Spans
- Plan-Modus produziert strukturierte Effekte
- Executor unterscheidet builtin/native/tool
- mindestens 100 differenzielle Semantik-Tests gegen Bash für den unterstützten Subset
- `source` und `cd` verändern den Shell-State korrekt im aktuellen Kontext

### 6.2 Qualität
- Parser- und Executor-Fehler haben präzise Diagnosen
- alle Ausführungspfade sind testbar
- strikte Typisierung für Kernmodule
- reproduzierbare Testumgebung
- Dokumentation für Architektur, Sicherheit und Erweiterung

### 6.3 Sicherheit
- kein `shell=True` im produktiven Pfad
- Policy-Verstöße sind strukturiert erkennbar
- externe Prozesse sind timeout- und killbar
- Dry-run kann riskante Operationen markieren

---

## 7. Nicht-funktionale Anforderungen

### 7.1 Python-Standards
- Python 3.12+
- `dataclasses` oder schlanke Modelle für AST und Runtime-State
- strikte Typannotationen
- `pytest`, `ruff`, `mypy`

### 7.2 Performance
- Parsen typischer Skripte im niedrigen Millisekundenbereich für kleine Dateien
- Inkrementelle Reparse-Fähigkeit architektonisch vorbereitet
- Streaming von stdout/stderr ohne Blockade

### 7.3 Erweiterbarkeit
- neue Builtins ohne invasive Änderungen
- neue AST-Knoten ohne Rewrite der gesamten Engine
- Tool-Backends über Registry/Protocol
- spätere Sandboxes austauschbar

---

## 8. Technische Zielarchitektur

```text
script
  -> parser frontend (tree-sitter CST)
  -> AST normalizer
  -> semantic word model
  -> expander
  -> planner / effect analyzer
  -> executor
      -> builtin backend
      -> external process backend
      -> agent tool backend
  -> event stream + result object
```

### 8.1 Schichten

#### A. Parsing Frontend
Aufgabe:
- Bash-Quelltext mit `tree-sitter-bash` parsen
- CST und Fehlerknoten erfassen
- Source-Spans erhalten

#### B. AST-Normalisierung
Aufgabe:
- CST in eigene, stabile, produktionsgeeignete AST-Knoten überführen
- nur Semantik-relevante Knoten exponieren
- eigene Diagnostikobjekte aufbauen

#### C. Word-/Expansion-Modell
Aufgabe:
- Shell-Wörter in Segmente zerlegen:
  - literal
  - single-quoted literal
  - double-quoted fragment
  - parameter expansion
  - command substitution
  - arithmetic expansion
  - glob candidate
- spätere Expansionen kontextsensitiv ausführen

#### D. Runtime-State
Aufgabe:
- `cwd`
- shell vars
- exported env
- functions
- shell options
- positional params
- last status

#### E. Planner
Aufgabe:
- potenzielle Kommandos und Effekte vor der Ausführung ableiten
- Redirection-Ziele erfassen
- native/tool/builtin-Resolution simulieren
- Risiken markieren

#### F. Executor
Aufgabe:
- Builtins direkt im Prozess
- externe Prozesse kontrolliert
- agentische Tools über Registry

#### G. Security/Policy
Aufgabe:
- auszuführende Kommandos und Dateizugriffe gegen Regeln prüfen
- Netzwerk / riskante Befehle / Schreibzugriffe kontrollieren

---

## 9. Kern-Datenmodelle

## 9.1 AST
Empfohlene Basisknoten:

- `Program`
- `Sequence`
- `AndOrList`
- `Pipeline`
- `SimpleCommand`
- `Subshell`
- `Group`
- `FunctionDef`
- `IfCommand`
- `ForCommand`
- `WhileCommand`
- `CaseCommand`
- `Redirection`
- `AssignmentWord`
- `Word`

## 9.2 Word Segments
- `LiteralSegment`
- `SingleQuotedSegment`
- `DoubleQuotedSegment`
- `ParameterExpansionSegment`
- `CommandSubstitutionSegment`
- `ArithmeticExpansionSegment`
- `GlobSegment`

## 9.3 Runtime
- `ShellState`
- `ShellOptions`
- `ExecutionContext`
- `ExecutionPlan`
- `PlannedEffect`
- `ExecutionEvent`
- `CommandResult`
- `PolicyDecision`

---

## 10. Empfohlene Repository-Struktur

```text
agentsh/
  pyproject.toml
  README.md
  CLAUDE.md
  docs/
    product/
      prd.md
      architecture.md
      roadmap.md
    decisions/
      ADR-0001-parser-frontend.md
      ADR-0002-ast-model.md
    progress.md
  status/
    current_phase.json
    test_matrix.json
  src/
    agentsh/
      __init__.py
      api/
        engine.py
      parser/
        frontend.py
        diagnostics.py
        normalize.py
      ast/
        nodes.py
        words.py
        spans.py
      runtime/
        state.py
        options.py
        events.py
        result.py
      semantics/
        expand.py
        resolve.py
        planner.py
      exec/
        builtins.py
        external.py
        redirs.py
        pipelines.py
        compound.py
      policy/
        rules.py
        decisions.py
      sandbox/
        interface.py
      tools/
        registry.py
      cli/
        main.py
  tests/
    parser/
    ast/
    semantics/
    exec/
    integration/
    differential/
  fixtures/
    parser/
    expansion/
    execution/
```

---

## 11. Kernentscheidungen

### 11.1 Parser-Frontend
Verwende `tree-sitter` + `tree-sitter-bash` als Syntax-Frontend.

### 11.2 Eigener AST
Der produktive AST gehört dem Projekt. Niemals Business-Logik direkt auf dem CST aufbauen.

### 11.3 Eigene Execution-Semantik
Im Default-Profil keine Delegation an eine echte Shell. Kompatibilitäts-Fallback nur separat, bewusst und sandboxed.

### 11.4 Tool-Registry
Command resolution in dieser Reihenfolge:
1. Funktion
2. Python-Builtin
3. Agent-Tool
4. externes Binary

### 11.5 Policy-First Execution
Vor jeder echten Ausführung:
- command resolution
- effect scan
- policy check
- execution

---

## 12. Risiken und Gegenmaßnahmen

### Risiko 1: Bash-Semantik ist tiefer als der Syntax-Parser
**Problem:** Tree-sitter liefert Syntax, aber nicht automatisch korrekte Shell-Semantik.  
**Gegenmaßnahme:** Eigener AST + differenzielle Tests gegen Bash.

### Risiko 2: Word-Splitting und Quoting werden falsch modelliert
**Problem:** Häufigste Fehlerquelle bei Shell-Implementierungen.  
**Gegenmaßnahme:** Word-Segment-Modell, viele Expansion-Fixtures, kein frühes Flattening.

### Risiko 3: Assignment-Words, Redirections und Here-Docs
**Problem:** Spezialfälle beeinflussen Semantik stark.  
**Gegenmaßnahme:** Separate Testmatrix und klar isolierte Implementierung.

### Risiko 4: `source`/`.` mutieren aktuellen Kontext
**Problem:** Leicht versehentlich als Subprozess modelliert.  
**Gegenmaßnahme:** Builtin-Implementierung mit State-Mutation im aktuellen Kontext.

### Risiko 5: Sicherheitslücken bei nativen Kommandos
**Problem:** Unsichere Prozessausführung oder Umgebungsdurchgriff.  
**Gegenmaßnahme:** strikte Backends, Policy, Timeout, Prozessgruppen, kein `shell=True`.

---

## 13. Teststrategie

## 13.1 Parser-Tests
- gültige Syntax
- ungültige Syntax
- error recovery
- spans
- Round-trip-Aussagen über Struktur, nicht über Originalformatierung

## 13.2 AST-Tests
- CST -> AST Mapping
- node invariants
- source spans

## 13.3 Expansion-Tests
- quoted vs unquoted
- `${var}` und `$var`
- command substitution
- word splitting
- globbing
- tilde expansion
- here-doc expansion rules in gestuften Phasen

## 13.4 Execution-Tests
- builtins
- pipelines
- redirection order
- cwd mutations
- exported env
- last_status

## 13.5 Differential Tests
Vergleiche gegen Bash für den offiziell unterstützten Subset:
- stdout
- stderr
- exit code
- side effects (wo reproduzierbar)

## 13.6 Safety-Tests
- blockierte Kommandos
- blockierte Netzwerkpfade
- timeout / kill
- risk scoring im Plan-Modus

---

## 14. Meilensteine

### M0 — Repo Bootstrap
Output:
- Projektstruktur
- Tooling
- `CLAUDE.md`
- PRD, Roadmap, Progress-Dateien
- Baseline CI

### M1 — Parser Frontend
Output:
- tree-sitter integration
- parse API
- diagnostics
- fixture tests

### M2 — AST + Word Model
Output:
- normalisierter AST
- spans
- word segments

### M3 — Runtime + Planner Skeleton
Output:
- ShellState
- command resolution skeleton
- effect model

### M4 — Expansion Engine v1
Output:
- variable, tilde, command substitution, splitting, globbing

### M5 — Execution Core
Output:
- simple commands
- pipelines
- redirections
- builtins v1

### M6 — Control Flow
Output:
- and/or lists
- groups
- subshells
- functions
- `source`

### M7 — Policy + Safety
Output:
- policy engine
- risk markers
- execution constraints

### M8 — Differential Compatibility Layer
Output:
- large fixture corpus
- compare-to-bash harness
- compatibility report

### M9 — CLI + Docs + Examples
Output:
- parse / plan / run CLI
- examples
- architecture docs
- release notes

---

## 15. Definition of Done

Ein Release ist fertig, wenn:
1. alle Akzeptanzkriterien der Phase erfüllt sind,
2. neue Architekturentscheidungen als ADR dokumentiert sind,
3. `docs/progress.md` und `status/current_phase.json` aktualisiert wurden,
4. Tests grün laufen,
5. keine bekannten Sicherheitsabkürzungen ohne explizite Dokumentation enthalten sind.

---

## 16. Claude-Code-Betriebsmodell für dieses Projekt

Dieses Projekt soll **Claude Code-freundlich** aufgebaut werden. Das heißt:

- Entscheidungen und Fortschritt müssen in Dateien persistiert werden.
- Jede Session muss den Zustand aus dem Repo rekonstruieren können.
- Jede Phase muss in kleinen, überprüfbaren Schritten umgesetzt werden.
- Prompts müssen klare Deliverables, Verifikationsschritte und Abbruchkriterien enthalten.

### 16.1 Dateien, die Claude Code in jeder Session zuerst lesen soll
- `CLAUDE.md`
- `docs/product/prd.md`
- `docs/product/roadmap.md`
- `docs/progress.md`
- `status/current_phase.json`

### 16.2 Persistente Fortschrittsartefakte
- `docs/progress.md`  
  Freitext-Fortschritt, Risiken, offene Entscheidungen.
- `status/current_phase.json`  
  Maschinenlesbarer Zustand der aktuellen Phase.
- `status/test_matrix.json`  
  Offene/erledigte Testkategorien.
- `docs/decisions/*.md`  
  ADRs für Architekturentscheidungen.

---

## 17. Vorlage für `CLAUDE.md`

```md
# CLAUDE.md

## Projektziel
Dieses Repository implementiert eine Python-Bibliothek und CLI für einen Bash-Syntax-Parser
und einen policy-gesteuerten Agent-Executor.

## Arbeitsregeln
1. Lies zu Beginn jeder Session:
   - docs/product/prd.md
   - docs/product/roadmap.md
   - docs/progress.md
   - status/current_phase.json

2. Arbeite inkrementell.
3. Verändere keine Semantik ohne Tests.
4. Verwende niemals `shell=True` im produktiven Code.
5. Führe externe Kommandos nur über das dafür vorgesehene Backend aus.
6. Halte Parser, AST, Semantik und Executor getrennt.
7. Ergänze bei neuen Designentscheidungen eine ADR-Datei.
8. Aktualisiere nach jeder abgeschlossenen Phase:
   - docs/progress.md
   - status/current_phase.json
   - status/test_matrix.json

## Qualitätsregeln
- Python 3.12+
- Typannotationen verpflichtend
- pytest + ruff + mypy
- kleine, klar benannte Module
- klare Fehlerobjekte statt generischer Exceptions, wo sinnvoll

## Sicherheitsregeln
- Kein `shell=True`
- Keine versteckten Fallbacks auf `/bin/bash`
- Keine stillen Policy-Bypasses
- Riskante Operationen müssen im Plan-Modus sichtbar sein
```

---

## 18. Prompt-Strategie

Jeder Prompt an Claude Code soll:
1. den aktuellen Zustand aus Dateien laden,
2. eine klar begrenzte Phase umsetzen,
3. Tests hinzufügen oder anpassen,
4. Verifikation ausführen,
5. Fortschrittsdateien aktualisieren,
6. am Ende die nächsten Risiken benennen.

Die Prompts unten sind absichtlich **operativ** formuliert und direkt copy-paste-fähig.

---

# 19. Inkrementelle Claude-Code-Prompts

## Prompt 00 — Bootstrap, Tooling und persistente Projektsteuerung

```text
<task>
  <project>
    Implement a new Python project named agentsh: a Bash-syntax parser and policy-governed agent executor.
  </project>

  <session_start>
    Before making changes, read:
    - README.md if it exists
    - CLAUDE.md if it exists
    - any files under docs/
    - any files under status/
  </session_start>

  <objective>
    Bootstrap the repository so future Claude Code sessions can continue work reliably with minimal context loss.
  </objective>

  <requirements>
    1. Create a clean Python 3.12+ project structure under src/agentsh and tests/.
    2. Add pyproject.toml with dependencies and dev tooling for:
       - pytest
       - ruff
       - mypy
       - tree-sitter
       - tree-sitter-bash
    3. Create the following documentation and state files:
       - CLAUDE.md
       - docs/product/prd.md
       - docs/product/roadmap.md
       - docs/progress.md
       - status/current_phase.json
       - status/test_matrix.json
    4. Put the parser/executor architecture, coding rules, and safety rules into CLAUDE.md.
    5. Add a minimal README.md with project purpose, current status, and developer commands.
    6. Add a basic CI-like local verification section to the README.
    7. Initialize placeholder modules that match the target architecture.
  </requirements>

  <constraints>
    - Do not implement parser semantics yet.
    - Keep placeholders minimal but typed.
    - Prefer dataclasses and Protocols where appropriate.
    - Do not introduce heavy frameworks.
  </constraints>

  <deliverables>
    - initial repo structure
    - build/test/lint/typecheck configuration
    - durable project instructions in CLAUDE.md
    - roadmap and current phase tracking
  </deliverables>

  <verification>
    Run:
    - pytest -q
    - ruff check .
    - mypy src
  </verification>

  <output>
    After changes, report:
    1. files created
    2. commands run and their result
    3. remaining gaps
    4. exact recommended next prompt
  </output>
</task>
```

### Akzeptanzkriterien
- Projektstruktur vorhanden
- Tools laufen
- Fortschritts- und Statusdateien existieren
- keine Parserlogik im Bootstrap

---

## Prompt 01 — Parser-Frontend mit tree-sitter

```text
<task>
  <session_start>
    Read:
    - CLAUDE.md
    - docs/product/prd.md
    - docs/product/roadmap.md
    - docs/progress.md
    - status/current_phase.json
  </session_start>

  <objective>
    Implement the parser frontend using tree-sitter and tree-sitter-bash.
  </objective>

  <requirements>
    1. Create a parser frontend module that:
       - loads the Bash grammar
       - parses a source string
       - returns a structured parse result
       - captures syntax diagnostics and error nodes
    2. Add source span support:
       - byte offsets
       - row/column points
    3. Expose a small stable API such as:
       - parse_script(text: str) -> ParseResult
    4. Add parser tests for:
       - simple command
       - quoted arguments
       - pipeline
       - and/or list
       - subshell
       - group
       - malformed syntax with diagnostics
    5. Document any grammar-loading caveats in docs/progress.md.
  </requirements>

  <constraints>
    - Do not build product AST yet.
    - Keep CST handling isolated to parser/frontend.py and parser/diagnostics.py.
    - Do not silently swallow parse errors.
  </constraints>

  <deliverables>
    - tree-sitter parser integration
    - ParseResult model
    - parser tests
    - updated progress and phase files
  </deliverables>

  <verification>
    Run:
    - pytest tests/parser -q
    - ruff check .
    - mypy src
  </verification>

  <output>
    Summarize:
    1. parse API shape
    2. diagnostics behavior
    3. files changed
    4. next-step recommendation
  </output>
</task>
```

### Akzeptanzkriterien
- `parse_script()` liefert strukturierte Ergebnisse
- Syntaxfehler sind diagnostizierbar
- CST ist noch nicht mit Business-Logik vermischt

---

## Prompt 02 — Normalisierter AST und Source-Spans

```text
<task>
  <session_start>
    Read the repository guidance and current status files before coding.
  </session_start>

  <objective>
    Build a normalized project-owned AST layer on top of the tree-sitter CST.
  </objective>

  <requirements>
    1. Define typed AST nodes for:
       - Program
       - Sequence
       - AndOrList
       - Pipeline
       - SimpleCommand
       - Group
       - Subshell
       - Redirection
       - AssignmentWord
       - Word
    2. Every AST node must include a source span.
    3. Implement a normalization pass from CST -> AST for the supported nodes.
    4. Add a lightweight visitor or pattern-friendly API to traverse the AST.
    5. Add tests that assert AST shape for representative shell snippets.
    6. Reject unsupported CST patterns with explicit "unsupported syntax" diagnostics instead of hidden fallbacks.
  </requirements>

  <constraints>
    - Do not implement execution yet.
    - Keep AST free from tree-sitter node objects.
    - Avoid embedding expansion results into AST nodes.
  </constraints>

  <deliverables>
    - ast node models
    - normalize pass
    - AST tests
    - updated roadmap/progress/status
  </deliverables>

  <verification>
    Run:
    - pytest tests/ast -q
    - pytest tests/parser -q
    - ruff check .
    - mypy src
  </verification>

  <output>
    Report:
    1. supported AST nodes
    2. unsupported syntax behavior
    3. invariants enforced
    4. next recommended implementation slice
  </output>
</task>
```

### Akzeptanzkriterien
- produktiver AST ist CST-unabhängig
- Spans sind konsistent
- unsupported syntax wird explizit signalisiert

---

## Prompt 03 — Word-Modell und Shell-Lexem-Semantik

```text
<task>
  <session_start>
    Read CLAUDE.md and status files first.
  </session_start>

  <objective>
    Introduce a semantic word model so shell words are represented as structured segments instead of flat strings.
  </objective>

  <requirements>
    1. Define word segment types for:
       - literal
       - single-quoted
       - double-quoted
       - parameter expansion placeholder
       - command substitution placeholder
       - arithmetic expansion placeholder
    2. Update AST normalization so Word nodes contain ordered segments.
    3. Preserve quote context needed for later expansion rules.
    4. Add tests for mixed words, for example:
       - foo"$BAR"baz
       - '$HOME'
       - "x$(pwd)y"
       - VAR=value cmd
    5. Ensure assignment words remain distinguishable from normal arguments.
  </requirements>

  <constraints>
    - No real expansion yet.
    - Do not flatten words into final strings.
    - Keep placeholders symbolic.
  </constraints>

  <deliverables>
    - structured word model
    - normalization support
    - tests covering quoting edge cases
    - updated progress files
  </deliverables>

  <verification>
    Run:
    - pytest tests/ast -q
    - pytest tests/parser -q
    - ruff check .
    - mypy src
  </verification>

  <output>
    Summarize:
    1. word segment taxonomy
    2. quoting invariants
    3. edge cases covered
    4. next step
  </output>
</task>
```

### Akzeptanzkriterien
- `Word` ist segmentiert statt flach
- Quoting-Kontext bleibt erhalten
- Assignment-Words sind separat modelliert

---

## Prompt 04 — Runtime-State und Command-Resolution-Skelett

```text
<task>
  <session_start>
    Read repository instructions and current state files.
  </session_start>

  <objective>
    Introduce the runtime data model for shell execution and a first command-resolution skeleton.
  </objective>

  <requirements>
    1. Implement typed runtime models for:
       - ShellState
       - ShellOptions
       - ExecutionContext
       - CommandResult
       - ExecutionEvent
    2. Add state fields for:
       - cwd
       - shell_vars
       - exported_env
       - functions
       - positional_params
       - last_status
    3. Implement a command resolution skeleton with the target order:
       - shell function
       - builtin
       - agent tool
       - external binary
    4. Add a ToolRegistry interface / protocol.
    5. Add unit tests for resolution ordering and ShellState initialization.
  </requirements>

  <constraints>
    - Do not execute external commands yet.
    - No builtins implementation yet except placeholders.
    - Keep runtime state serializable where practical.
  </constraints>

  <deliverables>
    - runtime models
    - resolver skeleton
    - tests
    - updated status/progress
  </deliverables>

  <verification>
    Run:
    - pytest tests/exec -q
    - ruff check .
    - mypy src
  </verification>

  <output>
    Report:
    1. runtime model overview
    2. resolution ordering
    3. serialization/typing choices
    4. next-step recommendation
  </output>
</task>
```

### Akzeptanzkriterien
- ShellState ist klar definiert
- Resolution-Reihenfolge ist testbar
- keine echte Prozessausführung im Codepfad

---

## Prompt 05 — Expansion Engine v1

```text
<task>
  <session_start>
    Read the current project files before coding.
  </session_start>

  <objective>
    Implement the first real expansion engine for the supported shell subset.
  </objective>

  <requirements>
    1. Implement expansion passes, at minimum for:
       - tilde expansion
       - parameter / variable expansion
       - selected special parameters such as $? and $$
       - command substitution placeholder handling through a delegated execution hook
       - quote removal
    2. Implement word splitting for unquoted results only.
    3. Implement filename expansion / globbing as a separate explicit step.
    4. Ensure double-quoted and single-quoted behavior differs correctly.
    5. Keep expansion output structured until the last responsible moment.
    6. Add tests for:
       - quoted vs unquoted variable expansion
       - empty and unset values
       - mixed literal + expansion words
       - tilde expansion
       - globbing vs quoted glob patterns
    7. Add a differential test scaffold that can later compare supported cases against Bash.
  </requirements>

  <constraints>
    - Do not implement a full Bash compatibility claim.
    - If semantics are uncertain, fail explicitly and document the limitation.
    - Command substitution should use an injectable hook, not hard-coded shell calls.
  </constraints>

  <deliverables>
    - expansion engine module
    - structured expansion results
    - tests for quoting and splitting
    - differential scaffold
    - updated progress files
  </deliverables>

  <verification>
    Run:
    - pytest tests/semantics -q
    - pytest tests/differential -q
    - ruff check .
    - mypy src
  </verification>

  <output>
    Summarize:
    1. implemented expansions
    2. unsupported semantics
    3. failure behavior
    4. next phase
  </output>
</task>
```

### Akzeptanzkriterien
- Variablen und Tilde werden korrekt expandiert
- Word splitting respektiert Quoting
- Globbing ist eigener Schritt
- unklare Semantik wird nicht versteckt

---

## Prompt 06 — Redirections, Pipelines und externer Executor

```text
<task>
  <session_start>
    Read the project guidance and phase tracking files first.
  </session_start>

  <objective>
    Implement execution of simple commands, pipelines, and redirections through a controlled process backend.
  </objective>

  <requirements>
    1. Implement execution of SimpleCommand for:
       - builtin resolution
       - external command resolution
    2. Implement a controlled external process backend using argv lists only.
    3. Implement stdout/stderr capture and streaming events.
    4. Implement redirections with explicit ordering semantics.
    5. Implement pipeline execution with correct result aggregation for the current feature set.
    6. Add timeout handling and process-group cleanup.
    7. Add tests for:
       - simple external command
       - builtin vs external dispatch
       - pipeline behavior
       - redirection order cases
       - exit status propagation
    8. Ensure all external execution paths are routed through one backend abstraction.
  </requirements>

  <constraints>
    - Do not use shell=True anywhere.
    - Do not bypass the runtime resolver.
    - Keep sandbox/policy decisions as injectable interfaces if not fully implemented yet.
  </constraints>

  <deliverables>
    - external process backend
    - simple command execution
    - pipeline execution
    - redirection handling
    - tests and updated docs
  </deliverables>

  <verification>
    Run:
    - pytest tests/exec -q
    - pytest tests/integration -q
    - ruff check .
    - mypy src
  </verification>

  <output>
    Report:
    1. execution path summary
    2. how redirection ordering is modeled
    3. how timeouts and cleanup work
    4. open risks before builtins expansion
  </output>
</task>
```

### Akzeptanzkriterien
- externer Executor ist zentralisiert
- keine Shell-Delegation
- Pipelines und Redirections haben Tests
- Timeout/Kill sind vorhanden

---

## Prompt 07 — Builtins v1 und `source` / `.`

```text
<task>
  <session_start>
    Load project instructions and current state files before implementation.
  </session_start>

  <objective>
    Implement the first builtin set and ensure current-shell state mutation works correctly.
  </objective>

  <requirements>
    1. Implement builtins:
       - pwd
       - cd
       - echo
       - printf
       - export
       - unset
       - true
       - false
       - test
       - [
       - exit
    2. Implement `.`
       and `source` so a sourced script is parsed and executed in the current shell context.
    3. Ensure state mutations from:
       - cd
       - export
       - unset
       - source
       affect the current shell state, not a subprocess clone.
    4. Add tests for builtin semantics and state mutation.
    5. Add at least one integration test sourcing a local fixture script.
  </requirements>

  <constraints>
    - Source only local workspace files in the default profile.
    - Keep path handling explicit and safe.
    - Fail clearly on unsupported sourcing behavior.
  </constraints>

  <deliverables>
    - builtin implementations
    - source execution path
    - state mutation tests
    - updated progress files
  </deliverables>

  <verification>
    Run:
    - pytest tests/exec -q
    - pytest tests/integration -q
    - ruff check .
    - mypy src
  </verification>

  <output>
    Summarize:
    1. builtins implemented
    2. current-shell mutation behavior
    3. source limitations
    4. next recommended phase
  </output>
</task>
```

### Akzeptanzkriterien
- `cd` und `export` mutieren ShellState
- `source` läuft im aktuellen Kontext
- builtin behavior ist testbar

---

## Prompt 08 — Listen, Gruppen, Subshells und Funktionen

```text
<task>
  <session_start>
    Read CLAUDE.md, roadmap, progress, and current phase files.
  </session_start>

  <objective>
    Implement control-flow-adjacent execution semantics for lists, groups, subshells, and functions.
  </objective>

  <requirements>
    1. Implement:
       - sequence execution
       - and/or short-circuit execution
       - group execution { ...; }
       - subshell execution ( ... )
       - function definitions
       - function invocation through resolver precedence
    2. Ensure subshell execution receives an isolated ShellState copy.
    3. Ensure group execution runs in the current shell context.
    4. Add tests for:
       - && and || behavior
       - group vs subshell state mutation differences
       - function definition and invocation
       - last_status propagation
    5. If arithmetic expansion or function-local scope is partially supported only, document it explicitly.
  </requirements>

  <constraints>
    - Avoid implementing unrelated advanced Bash features in this phase.
    - Keep function semantics explicit; do not fake full Bash compatibility.
  </constraints>

  <deliverables>
    - compound execution layer
    - function support
    - short-circuit semantics
    - tests and docs updates
  </deliverables>

  <verification>
    Run:
    - pytest tests/exec -q
    - pytest tests/integration -q
    - ruff check .
    - mypy src
  </verification>

  <output>
    Report:
    1. control-flow semantics implemented
    2. function behavior summary
    3. remaining incompatibilities
    4. next phase recommendation
  </output>
</task>
```

### Akzeptanzkriterien
- `{}` und `()` unterscheiden sich semantisch
- `&&` / `||` short-circuiten korrekt
- Funktionen sind über Resolver erreichbar

---

## Prompt 09 — Planner, Dry-run und Effektanalyse

```text
<task>
  <session_start>
    Read all persistent project state files before coding.
  </session_start>

  <objective>
    Implement a plan mode that explains what a script would do before it runs.
  </objective>

  <requirements>
    1. Add an ExecutionPlan model with:
       - command steps
       - resolution kind (builtin/tool/external/function)
       - redirections
       - likely file reads/writes
       - environment mutations
       - risk markers
    2. Implement a planner that traverses the AST and produces this plan without executing side effects.
    3. Add event/logging support for:
       - parse
       - normalize
       - expand
       - resolve
       - plan
       - execute
    4. Add tests verifying the plan output for representative scripts.
    5. Add a CLI or API entrypoint for:
       - parse
       - plan
       - run
  </requirements>

  <constraints>
    - Plan mode must not execute external commands.
    - If a value cannot be determined statically, mark it as unknown instead of guessing.
    - Keep the plan structured and machine-readable.
  </constraints>

  <deliverables>
    - planner module
    - effect models
    - parse/plan/run API surface
    - plan tests
    - updated docs
  </deliverables>

  <verification>
    Run:
    - pytest tests/semantics -q
    - pytest tests/integration -q
    - ruff check .
    - mypy src
  </verification>

  <output>
    Summarize:
    1. plan schema
    2. what can and cannot be inferred statically
    3. API/CLI changes
    4. next phase
  </output>
</task>
```

### Akzeptanzkriterien
- Dry-run produziert strukturierte Effekte
- unbekannte Werte werden als unbekannt markiert
- parse/plan/run API ist sichtbar

---

## Prompt 10 — Policy Engine und Sicherheitsgrenzen

```text
<task>
  <session_start>
    Read the repository guidance and status documents first.
  </session_start>

  <objective>
    Add a first-class policy engine that can allow, deny, or warn on execution attempts and risky effects.
  </objective>

  <requirements>
    1. Implement typed policy models for:
       - allow
       - deny
       - warn
    2. Add policy checks for:
       - command allow/deny rules
       - workspace path restrictions
       - suspicious write targets
       - optional network restrictions markers
    3. Ensure policy is consulted before external execution.
    4. Add tests for policy-denied and policy-warned cases.
    5. Make policy decisions visible in plan mode and run mode.
    6. Add explicit configuration points for future sandbox integration.
  </requirements>

  <constraints>
    - Do not fake sandboxing; model interfaces honestly if full isolation is not implemented yet.
    - Denials must be explicit and typed.
    - Avoid hard-coding environment-specific assumptions where possible.
  </constraints>

  <deliverables>
    - policy engine
    - decision models
    - enforcement hooks
    - tests and docs updates
  </deliverables>

  <verification>
    Run:
    - pytest tests/exec -q
    - pytest tests/integration -q
    - ruff check .
    - mypy src
  </verification>

  <output>
    Report:
    1. policy decision model
    2. enforcement path
    3. what remains for true sandboxing
    4. next phase
  </output>
</task>
```

### Akzeptanzkriterien
- Ausführung consultet Policy vorab
- deny/warn sind sauber modelliert
- Plan-Modus zeigt Policy-Signale

---

## Prompt 11 — Differential Tests gegen Bash

```text
<task>
  <session_start>
    Read the current project state before implementation.
  </session_start>

  <objective>
    Build a differential compatibility harness against Bash for the officially supported feature subset.
  </objective>

  <requirements>
    1. Add a fixture-based differential test runner that:
       - runs a supported snippet through agentsh
       - runs the same snippet through bash in a controlled test harness
       - compares stdout, stderr, exit status, and selected side effects
    2. Start with at least 100 representative fixtures covering:
       - quoting
       - variable expansion
       - tilde expansion
       - simple assignments
       - pipelines
       - groups vs subshells
       - builtins where comparison is meaningful
    3. Mark unsupported features explicitly so they are excluded or xfailed for documented reasons.
    4. Generate a compatibility report artifact in docs/ or status/.
  </requirements>

  <constraints>
    - Only compare features officially declared supported.
    - Unsupported Bash features must not silently appear as "passing".
    - Keep fixture metadata explicit.
  </constraints>

  <deliverables>
    - differential harness
    - fixture corpus
    - compatibility report
    - updated progress/status docs
  </deliverables>

  <verification>
    Run:
    - pytest tests/differential -q
    - ruff check .
    - mypy src
  </verification>

  <output>
    Summarize:
    1. fixture coverage
    2. pass/fail categories
    3. known semantic gaps
    4. release readiness assessment
  </output>
</task>
```

### Akzeptanzkriterien
- Fixture-Harness existiert
- unterstützter Subset wird gegen Bash verglichen
- Kompatibilitätslücken sind sichtbar

---

## Prompt 12 — CLI, Doku, Beispiele und Release-Vorbereitung

```text
<task>
  <session_start>
    Read persistent project state and compatibility results first.
  </session_start>

  <objective>
    Prepare the project for first external use by polishing CLI, documentation, examples, and release metadata.
  </objective>

  <requirements>
    1. Finalize a CLI with commands such as:
       - agentsh parse <file>
       - agentsh plan <file>
       - agentsh run <file>
    2. Add end-to-end examples demonstrating:
       - parse-only inspection
       - dry-run planning
       - builtin execution
       - tool-backed command resolution
    3. Write architecture documentation covering:
       - parser frontend
       - AST
       - expansion engine
       - runtime state
       - execution backends
       - policy engine
    4. Add a clear supported-features matrix.
    5. Add a known limitations section.
    6. Update README with installation, quickstart, and safety notes.
    7. Prepare a release checklist and changelog seed.
  </requirements>

  <constraints>
    - Do not overclaim Bash compatibility.
    - Document limitations prominently.
    - Ensure examples match actual tested behavior.
  </constraints>

  <deliverables>
    - usable CLI
    - polished docs
    - examples
    - release checklist
  </deliverables>

  <verification>
    Run:
    - pytest -q
    - ruff check .
    - mypy src
  </verification>

  <output>
    Report:
    1. CLI surface
    2. supported feature matrix
    3. known limitations
    4. release recommendation
  </output>
</task>
```

### Akzeptanzkriterien
- CLI ist benutzbar
- Docs sind ehrlich und vollständig
- unterstützte Features sind explizit
- Release-Checkliste vorhanden

---

## 20. Zusätzliche optionale Meta-Prompts

## Meta-Prompt A — Architekturreview vor größerem Umbau

```text
Review the current architecture against the PRD. Identify:
1. boundary violations between parser, AST, semantics, and execution,
2. hidden shell compatibility assumptions,
3. missing tests for risky semantics,
4. refactor proposals ordered by impact and risk.
Do not make changes yet; produce a concrete implementation plan first.
```

## Meta-Prompt B — Semantik-Lücken systematisch finden

```text
Audit the currently supported shell semantics and list all places where behavior may diverge from Bash for the declared feature subset.
For each divergence, provide:
- severity
- example snippet
- likely root cause
- recommended fix
- test to add
```

## Meta-Prompt C — Sicherheitsreview

```text
Perform a security review of the current executor and policy layers.
Focus on:
- implicit shell delegation
- path traversal
- environment leakage
- unsafe temporary files
- process cleanup
- policy bypasses
Return findings grouped as critical / major / minor, with exact file references and concrete remediations.
```

---

## 21. Empfohlene Arbeitsweise in Claude Code

1. Immer mit Prompt 00 starten, wenn das Repo neu ist.
2. Danach jeweils genau **eine** Phase umsetzen.
3. Nach jeder Phase:
   - Tests grün
   - Fortschrittsdateien aktualisiert
   - nächster Prompt bestimmt
4. Bei Semantik-Unklarheit:
   - kein Raten
   - Test schreiben
   - Limitation dokumentieren
5. Vor Kompatibilitätsbehauptungen:
   - differenziellen Test hinzufügen

---

## 22. Kurzfassung für operative Übergabe

Wenn du nur die praktische Arbeitsanweisung willst, verwende diese Reihenfolge:

1. Prompt 00 — Bootstrap  
2. Prompt 01 — Parser frontend  
3. Prompt 02 — AST  
4. Prompt 03 — Word model  
5. Prompt 04 — Runtime state  
6. Prompt 05 — Expansion engine  
7. Prompt 06 — Executor core  
8. Prompt 07 — Builtins + source  
9. Prompt 08 — Compound execution  
10. Prompt 09 — Planner / dry-run  
11. Prompt 10 — Policy engine  
12. Prompt 11 — Differential tests  
13. Prompt 12 — CLI + docs + release

Damit entsteht ein System, das in jeder Phase nutzbar bleibt und für Claude Code sauber weiterbearbeitbar ist.
