## 1. Comando `agent-context`

- [x] 1.1 Definire in `cli.py` il dizionario `_AGENT_CONTEXT` con `schema_version`, `cli` (nome, versione, descrizione) e `commands` (lista comandi con `name`, `short`, `flags`, `exit_codes`)
- [x] 1.2 Implementare `@app.command("agent-context")` che stampa `_AGENT_CONTEXT` come JSON su stdout e restituisce exit 0 — nessuna chiamata di rete
- [x] 1.3 Verificare che tutti i comandi principali siano presenti in `commands` (`catalog`, `info`, `get`, `count`, `storia`, `cerca-codice`, `agent-context`, `which`)
- [x] 1.4 Aggiungere test in `tests/` che controlla: output è JSON valido, presenza `schema_version`, presenza di almeno un comando con `exit_codes`

## 2. Comando `which`

- [x] 2.1 Implementare funzione `_which_search(query: str, catalog: list[dict], limit: int) -> list[dict]` in `cli.py` o modulo separato: tokenizza la query, matcha su `Titolo report`, `Ambito territoriale`, `Unità territoriale`, ordina per token matched discendente
- [x] 2.2 Aggiungere funzione `_comando_suggerito(entry: dict) -> str` che restituisce il comando completo con date di default (usa `catalog.validity_end` e `catalog.is_range`)
- [x] 2.3 Implementare `@app.command("which")` con argomento opzionale `query` e flag `--limit` (default 3): senza query lista tutto il catalogo; con query restituisce i match o exit 2 se nessun risultato
- [x] 2.4 Aggiungere test: query con match (`"comuni"`), query senza match (exit 2), `--limit 1`, invocazione senza argomento (lista completa)

## 3. Documentazione e release

- [x] 3.1 Aggiornare `README.md` con i due nuovi comandi (sezione comandi)
- [x] 3.2 Aggiornare `_EPILOG` in `cli.py` con riferimento a `agent-context` e `which`
- [x] 3.3 Aggiornare `LOG.md` con le note della modifica
- [x] 3.4 Verificare `uv run ruff check src/` e `uv run pytest tests/ -v` — entrambi devono passare
