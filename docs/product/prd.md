
# PRD: Python-basierter Bash-Syntax-Parser und Agent-Executor
## Claude-Code-optimierte Projektfassung mit inkrementellen Prompts

Version: 1.0
Status: Draft / ready for execution
Ziel-Repository: `agentsh`
Primare Sprache: Python 3.12+
Primares Parsing-Frontend: `tree-sitter` + `tree-sitter-bash`
Primares Ziel: Eine kontrollierte Shell-Engine mit Bash-kompatibler Syntaxoberflache, eigener AST/Semantik und policy-gesteuerter Ausfuhrung fur Agent-Workflows.

---

## 1. Produktziel

Wir bauen eine Python-Bibliothek und CLI, die einen definierten Bash-Subset zuverlassig parsen, in einen normierten AST uberfuhren, relevante Shell-Expansionen korrekt modellieren und Kommandos sicher ausfuhren kann. Das System ist **nicht** als dunner Wrapper um `/bin/bash` gedacht, sondern als **kontrollierbare Ausfuhrungs-Engine fur Agents**.

Das System muss drei Betriebsarten unterstutzen:

1. **Parse only**
   Skript analysieren, AST und Diagnoseobjekte liefern.

2. **Plan / Dry-run**
   Geplante Ausfuhrung, Effekte, Risikoindikatoren, Tool- und Dateizugriffe ableiten, ohne reale Anderungen auszufuhren.

3. **Execute**
   Kommandos in einer kontrollierten Runtime ausfuhren, mit Unterscheidung zwischen:
   - Python-Builtins
   - nativen Binaries
   - Agent-Tools / Tool-Backends

---

## 2. Warum dieses Produkt

Agents brauchen haufig eine Shell-artige Kontrollsprache fur:
- dateibasierte Workflows,
- Pipelines,
- kleine Automatisierungen,
- Tool-Orchestrierung,
- replizierbare lokale Aufgaben.

Direktes Ausfuhren beliebiger Shell-Strings uber eine Host-Shell ist dafur ungeeignet, weil:
- Syntax- und Quoting-Fehler schwer nachvollziehbar sind,
- Effekte vorab kaum planbar sind,
- Sicherheitsgrenzen unklar bleiben,
- Builtins, Shell-State und Prozesskontext nicht sauber beobachtbar sind,
- Agent-Tools nicht auf derselben semantischen Ebene wie Shell-Kommandos modelliert werden.

Das Produkt schliesst diese Lucke mit einer Shell-Engine, die **Bash-artig schreibt**, aber **agentisch kontrolliert** arbeitet.

---

## 3. Produktprinzipien

### 3.1 Semantik vor String-Hacking
Shell-Worter werden nicht als rohe Strings behandelt, sondern als strukturierte Segmente mit Quoting- und Expansionskontext.

### 3.2 Parser und Executor sind getrennt
CST/Parsing, AST-Normalisierung, Expansion und Ausfuhrung sind getrennte Schichten.

### 3.3 Security by construction
Kein implizites Delegieren an `shell=True`. Externe Prozesse laufen nur uber explizite Backends und Policies.

### 3.4 Agent-first observability
Jeder relevante Schritt muss inspizierbar sein:
- Parser-Diagnosen,
- AST,
- Expansionsschritte,
- Ausfuhrungsplan,
- State-Mutationen,
- stdout/stderr-Events.

### 3.5 Inkrementelle Lieferbarkeit
Das Produkt wird in strikt testbaren Phasen gebaut; jede Phase muss isoliert nutzlich und releasebar sein.

---

## 4. Zielgruppen und zentrale Use Cases

### 4.1 Zielgruppen
- Agent-Plattform-Teams
- Entwickler von Coding-Agents
- Workflow-/Automation-Teams
- Sicherheitsbewusste Orchestrierungs-Stacks
- Forschungsteams fur Tool-Use und Execution Planning

### 4.2 Primare Use Cases
1. Ein Agent soll ein Shell-Skript lesen und die geplanten Effekte erklaren.
2. Ein Agent soll ein Skript sicher in einer Sandbox ausfuhren.
3. Ein Agent soll Shell-Kommandos mit internen Tools kombinieren.
4. Ein Agent soll Skripte analysieren, transformieren und mit Tests absichern.
5. Ein Agent soll Shell-ahnliche Automatisierungen ausfuhren, ohne volle Bash-Unsicherheit zu ubernehmen.

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
- here-doc syntax (erst Parse + AST, Execution spater gestuft)

### Expansionen (MVP stufenweise)
- literal handling
- quote removal
- tilde expansion
- parameter/variable expansion (`$var`, `${var}`)
- special params (`$?`, `$$`) soweit sinnvoll
- command substitution `$(...)`
- word splitting
- filename expansion / globbing
- ausgewahlte arithmetic expansion (Phase 8 oder spater)

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
- externe Programme uber kontrolliertes Backend
- Tool-Registry fur agentische Kommandos
- Dry-run / Plan-Modus
- Event-Stream / Trace-Modus

### Sicherheit
- keine normale Host-Shell im Default-Path
- Policy-Layer fur Allowlist / Denylist / Risiken
- Timeouts
- Prozessgruppen-Management
- workspace-begrenzte Dateizugriffe im Default-Profil

## 5.2 Nicht im MVP
- interaktive Shell
- Job Control
- Prompt-Rendering / REPL-History
- vollstandige Alias-Semantik
- History expansion
- `coproc`
- `select`
- `trap`-Komplettimplementierung
- volle Bash-Kompatibilitat
- vollstandige Array-Semantik in der ersten Release-Linie
- process substitution im ersten Release
- `[[ ... ]]` mit vollstandiger Bash-Kompatibilitat im ersten Release

---

## 6. Erfolgskriterien

### 6.1 Funktional
- definierter Syntax-Subset wird robust geparst
- AST-Knoten haben stabile Source-Spans
- Plan-Modus produziert strukturierte Effekte
- Executor unterscheidet builtin/native/tool
- mindestens 100 differenzielle Semantik-Tests gegen Bash fur den unterstutzten Subset
- `source` und `cd` verandern den Shell-State korrekt im aktuellen Kontext

### 6.2 Qualitat
- Parser- und Executor-Fehler haben prazise Diagnosen
- alle Ausfuhrungspfade sind testbar
- strikte Typisierung fur Kernmodule
- reproduzierbare Testumgebung
- Dokumentation fur Architektur, Sicherheit und Erweiterung

### 6.3 Sicherheit
- kein `shell=True` im produktiven Pfad
- Policy-Verstösse sind strukturiert erkennbar
- externe Prozesse sind timeout- und killbar
- Dry-run kann riskante Operationen markieren

---

## 7. Nicht-funktionale Anforderungen

### 7.1 Python-Standards
- Python 3.12+
- `dataclasses` oder schlanke Modelle fur AST und Runtime-State
- strikte Typannotationen
- `pytest`, `ruff`, `mypy`

### 7.2 Performance
- Parsen typischer Skripte im niedrigen Millisekundenbereich fur kleine Dateien
- Inkrementelle Reparse-Fahigkeit architektonisch vorbereitet
- Streaming von stdout/stderr ohne Blockade

### 7.3 Erweiterbarkeit
- neue Builtins ohne invasive Anderungen
- neue AST-Knoten ohne Rewrite der gesamten Engine
- Tool-Backends uber Registry/Protocol
- spatere Sandboxes austauschbar

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
- CST in eigene, stabile, produktionsgeeignete AST-Knoten uberfuhren
- nur Semantik-relevante Knoten exponieren
- eigene Diagnostikobjekte aufbauen

#### C. Word-/Expansion-Modell
Aufgabe:
- Shell-Worter in Segmente zerlegen:
  - literal
  - single-quoted literal
  - double-quoted fragment
  - parameter expansion
  - command substitution
  - arithmetic expansion
  - glob candidate
- spatere Expansionen kontextsensitiv ausfuhren

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
- potenzielle Kommandos und Effekte vor der Ausfuhrung ableiten
- Redirection-Ziele erfassen
- native/tool/builtin-Resolution simulieren
- Risiken markieren

#### F. Executor
Aufgabe:
- Builtins direkt im Prozess
- externe Prozesse kontrolliert
- agentische Tools uber Registry

#### G. Security/Policy
Aufgabe:
- auszufuhrende Kommandos und Dateizugriffe gegen Regeln prufen
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
Der produktive AST gehort dem Projekt. Niemals Business-Logik direkt auf dem CST aufbauen.

### 11.3 Eigene Execution-Semantik
Im Default-Profil keine Delegation an eine echte Shell. Kompatibilitats-Fallback nur separat, bewusst und sandboxed.

### 11.4 Tool-Registry
Command resolution in dieser Reihenfolge:
1. Funktion
2. Python-Builtin
3. Agent-Tool
4. externes Binary

### 11.5 Policy-First Execution
Vor jeder echten Ausfuhrung:
- command resolution
- effect scan
- policy check
- execution

---

## 12. Risiken und Gegenmassnahmen

### Risiko 1: Bash-Semantik ist tiefer als der Syntax-Parser
**Problem:** Tree-sitter liefert Syntax, aber nicht automatisch korrekte Shell-Semantik.
**Gegenmassnahme:** Eigener AST + differenzielle Tests gegen Bash.

### Risiko 2: Word-Splitting und Quoting werden falsch modelliert
**Problem:** Haufigste Fehlerquelle bei Shell-Implementierungen.
**Gegenmassnahme:** Word-Segment-Modell, viele Expansion-Fixtures, kein fruhes Flattening.

### Risiko 3: Assignment-Words, Redirections und Here-Docs
**Problem:** Spezialfalle beeinflussen Semantik stark.
**Gegenmassnahme:** Separate Testmatrix und klar isolierte Implementierung.

### Risiko 4: `source`/`.` mutieren aktuellen Kontext
**Problem:** Leicht versehentlich als Subprozess modelliert.
**Gegenmassnahme:** Builtin-Implementierung mit State-Mutation im aktuellen Kontext.

### Risiko 5: Sicherheitslucken bei nativen Kommandos
**Problem:** Unsichere Prozessausfuhrung oder Umgebungsdurchgriff.
**Gegenmassnahme:** strikte Backends, Policy, Timeout, Prozessgruppen, kein `shell=True`.

---

## 13. Teststrategie

## 13.1 Parser-Tests
- gultige Syntax
- ungultige Syntax
- error recovery
- spans
- Round-trip-Aussagen uber Struktur, nicht uber Originalformatierung

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
Vergleiche gegen Bash fur den offiziell unterstutzten Subset:
- stdout
- stderr
- exit code
- side effects (wo reproduzierbar)

## 13.6 Safety-Tests
- blockierte Kommandos
- blockierte Netzwerkpfade
- timeout / kill
- risk scoring im Plan-Modus
