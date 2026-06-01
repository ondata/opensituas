LOG

## 2026-06-01

- Release 0.1.0 su PyPI. `pyproject.toml` allineato a opensdmx: aggiunti `authors`,
  `keywords`, `classifiers`, gruppo `dev` (pytest, ruff), `[tool.ruff.lint]`, pin
  `uv_build`. Aggiunti `LICENSE` (MIT) e `docs/release.md`. Fix ruff `F841` (variabile
  `cfg` non usata in `territorial.py`). Repo reso pubblico. 18 test verdi, ruff pulito.
- Simulazione uso giornalistico: testati end-to-end tutti i comandi con chiamate API reali.
- Fix comportamento data di default: per i report `DATA`, `get`/`count` senza `--date`
  ora usano la **fine** validità (dato più recente), non l'inizio. Prima `count 61` dava i
  comuni del 1948 (7688) invece di oggi (7894). Aggiunte `catalog.validity_end()` e
  parametro `default_date` ad `apply_date`. Help di `get`/`count`, SKILL e README aggiornati.
- Fix `cerca-codice`: per gli omonimi (es. Samone) la LOV ripete lo stesso `RC` su più
  voci; il tool iterava per match e duplicava i record (Samone 12 invece di 6) con chiamate
  di rete ridondanti. Ora deduplica per `RC`: record corretti e metà richieste.
- `docs/tutorial-giornalisti.md`: 5 casi d'uso verificati (serie storica comuni, fusioni e
  cambi nome via `storia`, province soppresse, `cerca-codice`/omonimi, export CSV).
- Test: pytest non era nel venv; reinstallato. Suite da 14 → 18 verdi (4 nuovi su default_date).

## 2026-05-31

- Help ottimizzato per agenti: `--output` come enum (`table|json|csv`, validato), epilog
  top-level con il contratto agente (`-o json`, exit code, workflow), esempi per ogni comando.
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
