Architettura

`opensituas` è prima di tutto uno strato di esecuzione per agenti AI: l'agente legge
stdout e compone i comandi. La complessità (date, envelope, header) è incapsulata nella CLI.

## Mappa moduli

| Modulo | Ruolo |
|---|---|
| `base.py` | Client HTTP, costanti URL, `gateway()`/`publish_get()`, `rows()`, rilevamento errori |
| `catalog.py` | Catalogo report: cache, filtri, lookup per `pfun`, gestione date dai link |
| `territorial.py` | Query interattive: `storia` (variazioni) e `cerca_codice` |
| `output.py` | Emissione `table`/`json`/`csv` |
| `cli.py` | App Typer e comandi |

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
