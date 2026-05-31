LOG

## 2026-05-31

- Primo rilascio `opensituas` v0.1.0.
- API SITUAS mappate via curl + agent-browser (tracciamento traffico delle pagine SPA).
- Comandi catalogo: `catalog`/`list`, `info`, `get`, `count` (74 report; date dai link
  pre-validati; envelope `resultset`/`items`; errori in HTTP 200 via `ERRCODE`).
- Comandi territoriali: `storia` (comune/provincia/regione, con `--dettaglio`) e
  `cerca-codice`. Per regioni/uts la storia unisce le forme storiche con lo stesso codice.
- Scoperta chiave: i servizi `ricercacodice_*` richiedono header `Referer`; il catalogo si
  ottiene solo via gateway POST (publish dà 401).
- `ricostruzione-codici` del portale = UI sui report di catalogo `PERIODO` (nessun endpoint
  nuovo), coperta da `get`/`count`.
- Output `table`/`json`/`csv`; cache catalogo 7 giorni + snapshot incluso. 13 test verdi.
