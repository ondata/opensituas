---
name: situas-explorer
description: Esplora e interroga il SITUAS (Sistema Informativo Territoriale delle Unità Amministrative e Statistiche, ISTAT) tramite la CLI `opensituas`. Usa questa skill per ottenere elenchi e dati di unità territoriali (ripartizioni, regioni, province/uts, comuni, sistemi locali del lavoro) a una certa data, oppure la storia delle variazioni e i codici Istat di un'unità.
---

# situas-explorer

La CLI `opensituas` espone le API SITUAS in modo orchestrabile. Tutti i comandi
accettano `--output table|json|csv` (`-o`); per il parsing usa `-o json | jq`.

Due famiglie di interrogazioni:

1. **Catalogo report** — tabelle a una data (snapshot) o su intervallo.
2. **Query territoriali** — storia delle variazioni e ricerca codici di una singola unità.

## Fase 1 — Trova il report giusto nel catalogo

Più report condividono lo stesso titolo, distinti **solo dal periodo di validità**:
guarda sempre la colonna `validità` prima di scegliere il `pfun`.

```bash
opensituas -o json catalog "comuni" | jq -r '.[] | "\(.pfun) \(.validità) \(.titolo)"'
opensituas -o json catalog --ambito "Unità statistiche"
```

Campi chiave per voce: `pfun` (id report), `validità`, `analisi` (`DATA` = data singola,
`PERIODO` = intervallo), `parametri` (`pfun - pdata` oppure `pfun - pdatada - pdataa`).

## Fase 2 — Capisci le colonne

```bash
opensituas -o json info 50 | jq '{report, colonne: [.colonne[].colonna]}'
```

## Fase 3 — Scarica i dati

La data di default è quella valida pre-impostata nel catalogo. Per cambiarla:

```bash
opensituas -o json get 50                       # data valida di default
opensituas -o json get 50 --date 12/01/1927     # report DATA: --date DD/MM/YYYY
opensituas -o json count 98 --from 17/03/1861 --to 31/05/2026   # report PERIODO
opensituas -o csv  get 50 --out comuni.csv       # salva su file
```

Se la data è fuori dalla finestra di validità, il comando esce con codice 2 e messaggio
`REPORT NON DISPONIBILE`: scegli una data dentro il periodo mostrato in `catalog`.

## Query territoriali

### Storia delle variazioni di un'unità (storia_ua / variazioni)

```bash
opensituas -o json storia comune Roma
opensituas -o json storia comune 058091 --dettaglio   # + provvedimento e unità coinvolte
opensituas -o json storia regione Lazio               # unisce le forme storiche (es. Compartimento→Regione)
opensituas -o json storia provincia 058               # usa il codice se il nome è ambiguo
```

Tipi: `comune`, `provincia` (uts), `regione`. Se il nome è ambiguo (più unità con codici
diversi) il comando lo segnala con i candidati: rilancia con il codice preciso.

### Ricerca codice Istat

```bash
opensituas -o json cerca-codice comune Roma     # codici, denominazioni, validità
```

## Note operative

- Exit code `2` = errore applicativo SITUAS (messaggio su stderr); `0` = ok.
- Il catalogo è cachato 7 giorni; `opensituas catalog --refresh` lo rilegge.
- `ricostruzione-codici` del portale non ha un endpoint proprio: corrisponde ai report di
  catalogo di tipo `PERIODO` (usali con `get`/`count` e `--from/--to`).
