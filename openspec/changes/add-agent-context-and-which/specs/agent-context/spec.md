## ADDED Requirements

### Requirement: CLI emette JSON di introspection per agenti
Il comando `agent-context` SHALL emettere su stdout un oggetto JSON con
`schema_version` (stringa), `cli` (nome, versione, descrizione), e `commands`
(lista comandi con `name`, `short`, `flags`, `exit_codes`). L'output SHALL essere
stabile e non dipendere dallo stato dell'API SITUAS (nessuna chiamata di rete).

#### Scenario: Output default
- **WHEN** si esegue `opensituas agent-context`
- **THEN** viene stampato JSON valido su stdout con campi `schema_version`, `cli`, `commands`
- **THEN** exit code è 0

#### Scenario: Flag --output ignorato o json
- **WHEN** si esegue `opensituas -o json agent-context`
- **THEN** il JSON è identico (il comando è già JSON-only)

#### Scenario: JSON versionato
- **WHEN** si legge il campo `schema_version` dall'output
- **THEN** il valore è una stringa non vuota (es. `"1"`)

### Requirement: JSON include lista comandi con flag e exit code contract
Il campo `commands` SHALL contenere un oggetto per ciascun comando top-level con:
- `name`: nome del comando
- `short`: descrizione breve
- `flags`: lista di flag con `name`, `type`, `usage`
- `exit_codes`: oggetto `{"0": "...", "2": "..."}` per i comandi che usano exit 2

#### Scenario: Presenza dei comandi principali
- **WHEN** si legge il campo `commands` dall'output
- **THEN** sono presenti almeno i comandi: `catalog`, `info`, `get`, `count`, `storia`, `cerca-codice`, `agent-context`, `which`

#### Scenario: Exit code contract per comandi con errore API
- **WHEN** si legge `exit_codes` del comando `get`
- **THEN** contiene chiave `"2"` con descrizione dell'errore API
