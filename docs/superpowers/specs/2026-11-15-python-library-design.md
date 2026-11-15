# Libreria Python per opensituas

## Obiettivo e decisione

Rendere lo stesso pacchetto utilizzabile da terminale e da Python, con un'esperienza simile a OpenSDMX. Decisione confermata: pandas è una dipendenza ordinaria e i risultati tabellari sono DataFrame. Non cambiare il comportamento della CLI.

## Alternative considerate

- Liste di dizionari: dipendenze leggere, ma conversione manuale per analisi e join.
- Liste con pandas opzionale: flessibili, ma aggiungono un passaggio al caso d'uso principale.
- DataFrame predefiniti: scelta adottata per la comodità di analisti e notebook.

## API pubblica proposta

Le funzioni sono disponibili direttamente da `opensituas` e hanno docstring e annotazioni di tipo.

| Funzione | Parametri | Risultato |
|---|---|---|
| `catalog` | `keyword=None`, keyword-only `ambito=None`, `unita=None`, `refresh=False` | DataFrame con le colonne già esposte dalla CLI: `pfun`, `titolo`, `validità`, `analisi`, `ambito`, `unità`, `parametri` |
| `info` | `pfun`, keyword-only `timeout=60.0` | Dizionario con `pfun`, `report`, `descrizione`, `colonne` (lista di dizionari) |
| `get` | `pfun`, keyword-only `date=None`, `date_from=None`, `date_to=None`, `timeout=60.0` | DataFrame dei record del report |
| `count` | stessi parametri di `get` | Intero, usando l'endpoint di conteggio senza scaricare il report |
| `storia` | `tipo`, `query`, keyword-only `dettaglio=False` | DataFrame degli eventi; metadati dell'unità in `df.attrs["unita"]` |
| `cerca_codice` | `tipo`, `query`, keyword-only `limit=20` | DataFrame dei risultati territoriali |

`pfun` accetta interi e stringhe identificative come il lookup esistente. `tipo` accetta `comune`, `provincia`, `regione`. Le date restano stringhe `DD/MM/YYYY`, con le regole esistenti.

`storia(..., dettaglio=True)` conserva le liste di dizionari `provvedimento` e `unita_coinvolte` nelle celle, senza moltiplicare le righe. Gli attributi pandas sono metadati di comodo: non sono garantiti dopo trasformazioni o esportazioni.

`cerca_codice` mantiene il comportamento attuale oltre il limite: restituisce la segnalazione `_ambiguo` e le voci di disambiguazione `V`, senza presentarle come risultati completi. Tale caso va documentato.

Esportare anche `SituasError`; conservare gli entry point `app` e `main` esistenti. Nessuna API pubblica aggiuntiva per `which` o `agent-context` in questa fase.

## Architettura e flusso dati

- Conservare `base.py` per HTTP, header ed errori, e `territorial.py` per le query territoriali.
- Rinominare il modulo interno `catalog.py` in `_catalog.py`: evita il conflitto tra il sottomodulo e la funzione pubblica `opensituas.catalog`. Aggiornare solo import e riferimenti necessari, inclusi i test.
- Estrarre da `cli.py` le operazioni condivise di catalogo, metadati, download e conteggio in un modulo di servizio che restituisce record/dizionari, indipendente da pandas e Typer.
- Un piccolo modulo `api.py` espone l'interfaccia Python e converte i risultati tabellari in DataFrame. Nessuna nuova classe client o configurazione globale.
- La CLI usa i risultati grezzi dello stesso servizio e le funzioni territoriali esistenti: niente conversioni DataFrame → JSON, che potrebbero alterare null, numeri o codici.
- Gli import del package non devono generare richieste di rete, output o scritture di cache.

Flusso: API Python → servizio condiviso/territorial → HTTP → record → DataFrame; CLI → stesso servizio/territorial → record → output esistente.

## Contratto dei dati

- Conservare nomi e valori delle colonne del report, senza rinomine automatiche o traduzioni.
- Non convertire codici territoriali in numeri: stringhe come `058091` devono restare identiche.
- Nessuna conversione automatica delle date o dei valori testuali in numeri. Pandas può inferire i tipi dei valori già numerici ricevuti dal JSON.
- Non riempire i valori mancanti con zero o stringhe vuote.
- Catalogo vuoto: DataFrame vuoto con le colonne note del catalogo.
- Report o storia senza record: DataFrame vuoto; non aggiungere una chiamata metadati solo per ricostruire le colonne sconosciute.
- Conservare ordine di righe e colonne e l'ordinamento storico esistente.

## Date, cache ed errori

Riutilizzare `apply_date`, i link del catalogo, il default a fine validità per i report DATA e i limiti già presenti nei link per i report PERIODO. `info` conserva il fix che seleziona i metadati alla fine validità.

Cache catalogo e fallback offline restano invariati. La libreria non stampa, non invoca `typer.Exit` e non termina il processo. Gli errori applicativi e HTTP già normalizzati restano `SituasError`; la CLI continua a tradurli in diagnostica su stderr ed exit code 2.

Il timeout esplicito delle funzioni report è passato alla relativa richiesta publish. La CLI conserva `OPENSITUAS_TIMEOUT`. Le richieste di catalogo e territoriali mantengono il timeout attuale: l'estensione della configurazione a tutte le richieste è fuori ambito.

Per `count`, verificare e convertire il campo `NUM_ROWS` in intero; payload di conteggio vuoti o non validi generano `SituasError`, non un falso zero. La CLI conserva il suo envelope grezzo.

Con `dettaglio=True` resta il comportamento esistente che sostituisce dettagli non disponibili con liste vuote; documentarlo senza introdurre nuove politiche di errore.

## Dipendenze e documentazione

Aggiungere `pandas>=2.0` alle dipendenze ordinarie e aggiornare il lockfile. Nessun extra o pacchetto separato.

Aggiornare descrizione del pacchetto, README e mappa architetturale per presentare CLI e libreria. Nel README distinguere `uv tool install opensituas` per il terminale e `uv add opensituas` per un progetto Python.

Esempi: discovery del catalogo, download corrente e storico, conteggio, ricerca codici e storia; filtro e join con nomi di colonna verificati nello snapshot o nelle fixture. Evidenziare preservazione degli zeri iniziali, limiti di ricerca e dettagli mancanti.

## Verifiche e criteri di accettazione

Test senza rete con fixture e monkeypatch:

- Import pubblici e assenza di output/rete all'importazione.
- Tipi di ritorno di tutte le funzioni, filtri e schema del catalogo vuoto.
- DataFrame con codici a zeri iniziali, valori numerici, mancanti e record vuoti.
- Date esplicite/default e intervalli; metadati aggiornati alla fine validità.
- Conteggio intero, zero valido, payload vuoto o malformato.
- Storia ordinata, metadati dell'unità e dettagli annidati.
- Ricerca codici, disambiguazione e propagazione di `SituasError` senza stampe.
- Regressioni CLI: JSON/CSV, envelope di `count` e `storia`, export su file ed exit code.
- Suite esistente e lint verdi; build installabile con dipendenza pandas dichiarata.

Nessuna pubblicazione, push, tag, release o modifica dell'installazione globale in questa fase.

## Fasi e stato

- [x] Esplorazione della struttura attuale e confronto con OpenSDMX.
- [x] Confronto tra alternative e conferma di pandas predefinito.
- [x] Stesura della specifica e revisione di coerenza, ambito e contratti.
- [x] Revisione della specifica da parte dell'utente.
- [x] Piano di implementazione dettagliato approvato prima del codice.
- [x] Implementazione e verifiche nel worktree `tmp/python-library-worktree`.

## Review

La CLI deve restare sui record grezzi; i DataFrame sono il contratto del livello Python. La collisione del nome `catalog` è risolta esplicitamente. Forme di ritorno, casi vuoti e limiti esistenti sono definiti. Nessuna funzionalità non richiesta, né rilascio automatico.

## Questioni aperte

Nessuna domanda funzionale: firme e forme di ritorno approvate, compreso `storia` come DataFrame con metadati in `attrs`. Integrazione e pubblicazione restano azioni separate, non eseguite.
