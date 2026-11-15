Architettura

`opensituas` espone CLI e libreria Python sullo stesso strato di esecuzione SITUAS.
La CLI offre stdout strutturato per agenti AI; la libreria restituisce DataFrame
pandas per analisi e notebook. Date, envelope e header sono gestiti dai moduli condivisi.

## Mappa moduli

| Modulo | Ruolo |
|---|---|
| `base.py` | Client HTTP, costanti URL, `gateway()`/`publish_get()`, `rows()`, rilevamento errori |
| `_catalog.py` | Catalogo interno: cache, filtri, lookup per `pfun`, gestione date dai link |
| `service.py` | Operazioni condivise di catalogo, metadati, dati e conteggio su record grezzi |
| `api.py` | Funzioni Python pubbliche e conversione dei risultati tabellari in DataFrame |
| `territorial.py` | Query interattive: `storia` (variazioni) e `cerca_codice` |
| `output.py` | Emissione `table`/`json`/`csv` |
| `cli.py` | App Typer e comandi |

## CLI e libreria

- CLI → `service.py` / `territorial.py` → HTTP → record grezzi → `output.py`.
- Python → `api.py` → stesso servizio / query territoriali → record → DataFrame.

Il servizio condiviso non dipende da pandas né da Typer. La CLI non converte mai
DataFrame in JSON/CSV: conserva gli envelope, i null e i codici originali.
`info()` restituisce un dizionario; `count()` valida il campo `NUM_ROWS` e restituisce
un intero. La CLI mantiene invece il payload grezzo del conteggio.

`opensituas.catalog` è la funzione pubblica; il precedente modulo interno
`catalog.py` è rinominato `_catalog.py` per evitare collisioni negli import.
`storia()` aggiunge i metadati dell'unità in `DataFrame.attrs["unita"]`; i dettagli
annidati restano liste nelle celle e non vengono esplosi in altre righe.

L'API Python non stampa e propaga `SituasError`. La CLI continua a intercettarla,
stampare su stderr e uscire con codice 2. Gli import non effettuano richieste di
rete né scrivono la cache. I timeout espliciti dell'API riguardano solo publish;
catalogo e territoriali mantengono il timeout predefinito esistente.

## Le due basi API

```
                 ┌─ gateway (POST) ──────────────────────────────┐
catalogo ────────┤  situas.istat.it/ShibO2Module/api/Report/      │
storia/variazioni│  ReportByUrl   body {"url":"<servizio>?..."}   │
ricerca-codice   └───────────────────────────────────────────────┘

                 ┌─ publish (GET) ───────────────────────────────┐
dati report ─────┤  situas-servizi.istat.it/publish/              │
                 │  reportspooljson | reportspooljsoncount |      │
                 │  anagrafica_report_metadato_web               │
                 └───────────────────────────────────────────────┘
```

## Invarianti non ovvie

- **Header `Referer` obbligatorio sul gateway.** I servizi `ricercacodice_*` rispondono
  vuoto senza `Referer: https://situas.istat.it/web/`. Inviato su tutte le chiamate gateway.
- **Catalogo solo via gateway.** `get_elenco_microservizi` sul base publish dà 401.
- **Envelope variabile.** `resultset` (reportspooljson, ricercacodice) vs `items`
  (var_get_ua_*, catalogo). Normalizzato da `rows()`.
- **Errori in HTTP 200.** `{"resultset":[{"ERRCODE":"..."}]}` o `{"message":"..."}`:
  letti dal payload da `_check_error()`.
- **Date dai link.** Le voci di catalogo portano `SPOOL_LINK`/`COUNT_LINK`/`INFO_LINK` con
  date valide. `apply_date()` sostituisce solo il parametro data, senza ri-derivarlo.

## Cache

| Cosa | Dove | TTL |
|---|---|---|
| Catalogo | `~/.cache/opensituas/catalog.json` | 7 giorni |
| Snapshot incluso | `opensituas/catalog_snapshot.json` | fallback offline |

## Firme dei servizi territoriali

Tracciate dal traffico reale del portale (3 famiglie: `comuni`, `reg`, `uts`).

- Autocomplete: `var_get_ua_{infix}_lov_diffusione?{nome|codice}=...`
- Storia: `var_get_ua_{infix}_lov_rs?...` (comuni: `procom`+`com`; reg/uts: codice+nome+tipo)
- Dettaglio: `..._lov_rs_dett` / `..._lov_rs_dett_ass` con `mcrvar` (tipo variazione) + `idprovv`
- Ricerca codice: `ricercacodice_criterio` → `_lov?ptipounit=N` → `_res?ptipounit=N&prc=<RC>`
