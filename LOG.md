LOG

## 2026-11-15 (2)

- `which` cerca anche nelle colonne dei report: indice `src/opensituas/which_index.json` (nome + etichetta delle colonne di 77 report, 35 KB) incluso nel pacchetto e rigenerato con `scripts/build_which_index.py`, passo aggiunto a `docs/release.md` e alla skill `release`. Prima cercava solo nei titoli: «popolazione e superficie dei comuni» proponeva 129, 307, 50 invece di 74, e due esempi documentati sbagliavano («popolazione» senza risultati, «province cessate» senza il 112).
- Ricerca in `_which.py`: parole vuote italiane ignorate, radice comune (soppresse/soppressi), sinonimi minimi (cessati, fusioni, montagna, abitanti, estensione), titolo 3 punti e colonne 1, a parità prima i report comunali. Nessuna chiamata di rete.
- Test `tests/test_which_search.py` sui 21 casi verificati, rossi prima del fix; 88 test verdi. Esempio «comuni per anno» sostituito: non individuava un report preciso.
- Lo snapshot del catalogo incluso ha 74 report, il catalogo online 77 (466, 467, 469): non aggiornato qui.

## 2026-11-15 — Agent quickstart

- Aggiunta al README la sezione `Agent quickstart`: prompt da incollare in un agente, con verifica o installazione su conferma, lettura dell'help, una chiamata reale (`cerca-codice comune Ledro`, provata a mano il 2026-11-15 con v0.2.0) e regole su date, validità, zeri iniziali e nomi ambigui. Prompt non ancora provato in una sessione pulita di un agente.

## 2026-11-15 — v0.2.0

- Skill `situas-explorer` corretta sui dati reali: `AREE_INT_2020` contiene solo la lettera (`F`, non `F-Ultraperiferico`: il filtro dava zero righe, anche nella demo web), `MACRO_AI_2020` è `I`/`C`, le zone montane sono `0`/`1`, Sesto San Giovanni è `015209` (`015179` è Pregnana Milanese). Non esiste un codice variazione «fusione»: l'esempio sulle fusioni del 2016 ora conta i nuovi comuni `CS` (27), non le righe (313).
- Release v0.2.0: prima versione pubblicata con la libreria Python. Tolta dal README la nota che descriveva l'API come non ancora su PyPI.
- Skill di progetto `release` (`.claude/skills/release/SKILL.md`, invocabile solo a mano con `/release [patch|minor|major|X.Y.Z]`): segue `docs/release.md` con controlli bloccanti (main allineato, tag e versione PyPI liberi, ruff, pytest, `twine check`, versione della wheel installata) e una conferma prima di push, GitHub release e PyPI. Build in `tmp/release-dist` invece di `dist/`. `__version__` era fermo a `0.1.0` con il pacchetto a `0.1.2`: ora lo legge `importlib.metadata`, con test in `tests/test_version.py`. Tolto il permesso automatico `twine upload` da `settings.local.json`: la conferma la chiede la skill.
- Libreria Python nel branch `feat/python-library`: `catalog`, `get`, `storia` e `cerca_codice` restituiscono DataFrame pandas; `info` restituisce un dizionario e `count` un intero validato. Codici testuali e zeri iniziali preservati.
- Servizio condiviso estratto dalla CLI, che conserva output, envelope ed exit code; modulo interno rinominato `_catalog.py` per liberare la funzione pubblica `catalog`.
- Aggiunta dipendenza `pandas>=2.0`, aggiornati README, architettura, specifica e piano. Nessun aggiornamento versione o pubblicazione PyPI.
- Autorizzati commit, push del branch e apertura di una Pull Request verso `main`; merge e release restano esclusi.
- Verifiche: 62 test passati (baseline 29), Ruff pulito; wheel/sdist costruiti e wheel installata in venv temporaneo con snapshot incluso. Review locale senza revisore indipendente; nessuna chiamata live SITUAS. Ambiente test: Python 3.14.0, pandas 3.1.1.

## 2026-06-02 — v0.1.2

- Fix `info`: l'endpoint `INFO_LINK` nel catalogo porta `pdata=<inizio validità>` e
  l'API restituiva i metadati dell'epoca, non quelli attuali. Per pfun 74 (`Comuni -
  Dimensione`) mancavano `AREA_KMQ`, `POP_RES`, `ANNO_POP_RES`, `COD_PROV_STORICO`.
  Fix: `info_cmd` applica ora `apply_date(..., default_date=validity_end(entry))`
  sull'`INFO_LINK`, come già faceva `get_cmd` per lo `SPOOL_LINK`. 15 colonne restituite
  invece di 10 per pfun 74.
- Skill `situas-explorer` arricchita: Fase 2 con snippet jq per nome/tipo/descrizione
  campi; sette casi d'uso per giornalisti e analisti (master table codici, normalizzazione
  comune, aree interne e policy, storia variazioni, traslazione codici tra date, SLL e
  specializzazione produttiva, Cities/FUA/NUTS3 europei).
- README: aggiunta sezione "Casi d'uso" con gli stessi sette scenari e comandi copiabili.

## 2026-06-01 — v0.1.1

- Aggiunti comandi `agent-context` e `which` per l'auto-orientamento degli agenti AI.
  `agent-context` emette un JSON versionato (`schema_version`, `cli`, `commands` con
  flag e exit code contract) senza chiamate di rete. `which <query>` cerca report SITUAS
  per token su titolo/ambito/unità e restituisce `comando_suggerito` con date di default;
  exit 2 se nessun match. 11 nuovi test verdi; ruff pulito.
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
