## Context

`cli.py` è basato su Typer. Il catalogo SITUAS (52 report) è già caricato da
`catalog.load_catalog()`. I comandi esistenti seguono il pattern `@app.command` +
`_run(fn)` per la gestione errori. Il package ha già l'epilog agent-friendly e il
flag `--output json`.

## Goals / Non-Goals

**Goals:**
- `agent-context`: JSON versionato (`schema_version`) con nome CLI, versione, lista comandi,
  flag per comando, exit code contract — leggibile da un agente senza parsare `--help`
- `which`: mapping query naturale → report SITUAS pertinenti; restituisce pfun, titolo,
  comando suggerito; exit 0 se match, exit 2 se nessun risultato confidenziale

**Non-Goals:**
- Embedding semantici o modelli ML per `which` — si usa ricerca substring/token sul
  titolo, ambito e unità territoriale già in catalogo
- Introspection ricorsiva di sottocomandi (agent-context copre solo il livello top-level)
- Autenticazione o rate-limit (nessuna chiamata di rete nei due comandi nuovi)

## Decisions

**`agent-context` — schema fisso vs auto-generato da Typer**
Scelta: schema fisso hardcoded in `cli.py`. Alternativa scartata: reflection su Typer
(`app.registered_commands`). Motivazione: la reflection di Typer non espone facilmente
le annotazioni custom (exit code contract, esempi); con uno schema fisso il JSON è
stabile e versionato esplicitamente.

**`which` — ricerca testuale vs fuzzy**
Scelta: tokenizzazione della query + match su titolo/ambito/unità del catalogo, con
ranking per numero di token matched. Alternativa scartata: fuzzy string matching
(dipendenza esterna non necessaria). La qualità è sufficiente per le query tipiche
("comuni per anno", "province soppresse"); l'utente può affinare.

**Output di `which`**
Il risultato è una lista di voci (pfun, titolo, ambito, unità, comando suggerito). Il
"comando suggerito" è sempre `get <pfun>` o `count <pfun>` con nota se il report è a
intervallo (PERIODO) o data singola (DATA). Formato default JSON (coerente con uso da
agenti); flag `--output table` già gestito dall'infrastruttura esistente.

**Exit code 2 per `which` senza match**
Coerente con la convenzione già usata in opensituas (`SituasError` → exit 2). Permette
a uno script/agente di rilevare "nessun report trovato" senza parsare il testo.

## Risks / Trade-offs

- [Schema `agent-context` fisso] → deve essere aggiornato manualmente ad ogni nuovo
  comando. Mitigazione: aggiornamento incluso nel checklist di ogni futura release.
- [Ricerca `which` solo testuale] → query ambigue o in inglese possono non matchare.
  Mitigazione: documentare che i titoli SITUAS sono in italiano; suggerire parole chiave
  dal catalogo nell'help del comando.
