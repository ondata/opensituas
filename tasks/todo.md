Todo — opensituas

## Fase 1 — Discovery API ✅
- [x] Mappa endpoint catalogo (gateway) e dati (publish)
- [x] Tracciamento traffico pagine SPA con agent-browser (ricerca-codice, storia, variazioni)
- [x] Scoperta header `Referer` per `ricercacodice_*`, envelope variabile, errori HTTP 200

## Fase 2 — CLI catalogo ✅
- [x] `base.py` (gateway/publish, rows, errori), `catalog.py` (cache, filtri, date dai link)
- [x] Comandi `catalog`/`list`, `info`, `get`, `count`
- [x] Output `table`/`json`/`csv`, `--out`, snapshot incluso

## Fase 3 — Query territoriali ✅
- [x] `territorial.py`: `storia` (comune/provincia/regione, `--dettaglio`), `cerca-codice`
- [x] Merge forme storiche reg/uts; disambiguazione su codici diversi

## Fase 4 — Docs e test ✅
- [x] README, architecture, SKILL situas-explorer, LOG
- [x] Test logica pura (13 verdi)

## Possibili estensioni future
- [ ] Comando `which` per capability lookup (se i comandi crescono)
- [ ] Geoglossario (definizioni) come comando dedicato
- [ ] Download swagger ufficiale via comando
