opensituas

CLI per il **SITUAS** — Sistema Informativo Territoriale delle Unità Amministrative e
Statistiche (ISTAT) — progettata per essere orchestrata da un agente AI: output
strutturato (`table`/`json`/`csv`), errori auto-esplicativi, catalogo cachato.

opensituas è un'idea di [Alice Corona](https://alice-corona.eu/).

## Installazione

```bash
uv tool install opensituas        # CLI a livello di sistema
# oppure, in sviluppo:
uv pip install -e .
```

## Cosa espone SITUAS

Due tipi di interrogazione, entrambi coperti:

1. **Catalogo report** — 74 "microservizi" (report) su unità amministrative e statistiche
   (ripartizioni, regioni, province/uts, comuni, sistemi locali del lavoro, ...). Ogni report
   ha un periodo di validità e restituisce una tabella alla data scelta.
2. **Query territoriali interattive** — storia delle variazioni di un'unità nel tempo
   (`storia`) e ricerca dei codici/denominazioni Istat con periodi di validità (`cerca-codice`).

## Comandi

```bash
# --- catalogo ---
opensituas catalog                          # tutti i report (pfun, titolo, validità, ...)
opensituas catalog "Comuni" --ambito "Unità amministrative"
opensituas --output json catalog "Ripartizioni" | jq '.[].pfun'
opensituas catalog --refresh                # rilegge dal gateway

opensituas info 50                          # descrizione + colonne del report 50
opensituas get 61                           # report DATA: dato più recente (fine validità)
opensituas get 61 --output csv --out comuni.csv
opensituas count 98 --from 17/03/1861 --to 31/05/2026
opensituas get 61 --date 01/01/2020         # snapshot storico; errore chiaro se fuori validità

# --- query territoriali ---
opensituas storia comune Roma               # storia delle variazioni del comune
opensituas storia comune 058091 --dettaglio # + provvedimento e unità coinvolte
opensituas storia regione Lazio
opensituas storia provincia Roma
opensituas cerca-codice comune Roma         # codici/denominazioni + validità

# --- per agenti AI ---
opensituas agent-context                    # JSON versionato: schema CLI (comandi, flag, exit code)
opensituas which "comuni per anno"          # trova report SITUAS da linguaggio naturale
opensituas which --limit 1 province        # max 1 risultato; exit 2 se nessun match
opensituas -o json which "province cessate" | jq '.[].comando_suggerito'
```

## Output per agenti

Il flag globale `--output` (`-o`) vale `table` (default), `json` o `csv`. In `json`/`csv`
l'output su stdout è pulito (i messaggi diagnostici vanno su stderr), pronto per `jq`:

```bash
opensituas -o json storia comune Roma | jq '.storia[] | {data: ."data evento", evento: .variazione}'
opensituas -o csv get 50 > comuni.csv
```

## Come funziona (in breve)

- **Catalogo**: ottenuto via gateway POST (`get_elenco_microservizi`), cachato in
  `~/.cache/opensituas/catalog.json` (TTL 7 giorni), con snapshot incluso come fallback.
- **Dati report**: endpoint pubblici `situas-servizi.istat.it/publish` (`reportspooljson`,
  `reportspooljsoncount`, `anagrafica_report_metadato_web`). Per i report `DATA`, senza
  `--date` la CLI usa la **fine validità** (dato più recente); i link del catalogo
  porterebbero invece la data di *inizio* (snapshot più vecchio). `--date`/`--from`/`--to`
  sostituiscono il parametro data.
- **Query territoriali**: servizi `var_get_ua_*` (storia) e `ricercacodice_*` via gateway.

Dettagli in [docs/architecture.md](docs/architecture.md). Per orchestrazione da agente vedi
[skills/situas-explorer/SKILL.md](skills/situas-explorer/SKILL.md).

## Variabili d'ambiente

| Variabile | Default | Descrizione |
|---|---|---|
| `OPENSITUAS_TIMEOUT` | `60` | Timeout richieste (secondi) |

## Licenza

MIT
