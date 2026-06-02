[![PyPI version](https://img.shields.io/pypi/v/opensituas)](https://pypi.org/project/opensituas/)
[![GitHub](https://img.shields.io/badge/github-ondata%2Fopensituas-blue?logo=github)](https://github.com/ondata/opensituas)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ondata/opensituas)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Newsletter](https://img.shields.io/badge/newsletter-ondata-FF6719?logo=substack)](https://ondata.substack.com/)

# opensituas

Qualsiasi analisi geografica sull'Italia parte da qui.

Il **[SITUAS](https://situas.istat.it/)** (ISTAT) è la fonte autoritativa dei codici e delle denominazioni ufficiali
di tutte le unità territoriali italiane — dall'Unità d'Italia a oggi. Contiene la
storia di ogni fusione, ridenominazione e soppressione di comuni, province e regioni.
`opensituas` lo espone come CLI orchestrabile, con output `table`/`json`/`csv` pronto
per `jq`, DuckDB o un agente AI.

opensituas è un'idea di [Alice Corona](https://alice-corona.eu/).

## Cosa puoi fare

- **Ottenere i codici Istat ufficiali** di tutti i comuni, province e regioni a qualsiasi
  data — dalla lista corrente allo snapshot storico del 1861.
- **Arricchire qualsiasi dataset** con popolazione, superficie, zona altimetrica,
  appartenenza a aree interne, classificazione montagna/collina/pianura.
- **Ricostruire la storia di un territorio**: quando è nato il comune di Ledro? Quante
  fusioni ci sono state dal 2010? Quale legge ha cambiato il nome di un comune?
- **Confrontare dataset di anni diversi** senza inciampare sui codici cambiati: la
  traslazione codici mappa ogni comune del 2001 nel corrispondente di oggi.
- **Trovare il bacino economico di riferimento** di un comune tramite i Sistemi Locali
  del Lavoro (SLL), con la specializzazione produttiva dell'area.
- **Usare le classificazioni europee** (Cities, FUA, NUTS3) per confronti con dati
  EUROSTAT: urban/rural, zone costiere, regioni di confine.

## Installazione

```bash
uv tool install opensituas
```

**Nota bene:** `opensituas` funziona ancora meglio accoppiato alla skill dedicata per
qualsiasi agente AI che supporti le skill, che guida l'agente nel discovery del catalogo e nei casi d'uso più comuni:

```bash
npx skills add ondata/opensituas
```

Per i dettagli sull'installazione della skill vedi [docs/skill/README.md](docs/skill/README.md).

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

## Casi d'uso

### Codici ufficiali Istat — la master table per i join

Il punto di partenza di qualsiasi analisi che usa dati pubblici italiani. Il report 61 è
una riga per comune con tutti i livelli gerarchici (ripartizione, regione, provincia, comune)
e le denominazioni ufficiali. Chiave di join universale: `PRO_COM_T` (6 caratteri
alfanumerici, es. `015146`).

```bash
opensituas -o csv get 61 --out comuni.csv              # snapshot corrente
opensituas -o csv get 61 --date 01/01/2000 --out comuni_2000.csv
```

### Popolazione, superficie e caratteristiche per comune

Due report complementari per normalizzare qualsiasi dataset comunale.

```bash
opensituas -o csv get 74 --out comuni_dim.csv     # POP_LEG, POP_RES, AREA_KMQ, anno riferimento
opensituas -o csv get 73 --out comuni_car.csv     # COM_LIT (litoraneo), COM_ISO (isolano), ZONA_ALT
```

`ZONA_ALT`: 1=Montagna interna · 2=Montagna litoranea · 3=Collina interna · 4=Collina
litoranea · 5=Pianura. Join via `PRO_COM_T`.

### Aree interne, montagna e zone di svantaggio

Fondamentale per giornalismo sui piccoli comuni, divario territoriale, accesso ai servizi.

```bash
opensituas -o csv get 75 --out comuni_policy.csv
```

Campi chiave: `AREE_INT_2020` (Polo → Polo intercomunale → Cintura → Intermedio →
Periferico → Ultraperiferico), `MACRO_AI_2020` (due classi: interno/non interno),
`ZONE_MONTANE_2014`, `ZONE_V_NAT_2020` (vincoli naturali), `ZONE_S_SPECIFICI_2014`.

### La storia di un comune — fusioni, rinominazioni, soppressioni

```bash
opensituas storia comune "Ledro" --dettaglio       # nato da fusione: chi, quando, perché
opensituas storia comune "Sesto San Giovanni"
# Tutte le variazioni dal 1991 a oggi con testo del provvedimento:
opensituas -o csv get 129 --out variazioni_1991.csv
# Solo cambi di denominazione, dall'Unità d'Italia:
opensituas -o json get 104 --from 17/03/1861 --to 31/05/2026 | jq '.[].COMUNE'
```

Il report 129 (`Variazioni amministrative e territoriali dal 1991`) è il più ricco:
`DESC_COD_VARIAZIONE` descrive il tipo (fusione, scorporo, cambio nome, cambio codice...),
`TESTO_PROVVEDIMENTO` riporta la norma di riferimento.

### Confrontare dati storici — traslazione codici tra due date

Indispensabile quando si confrontano dataset di anni diversi: le fusioni cambiano i codici.

```bash
# Mapping codici comuni: come erano nel 2001, come sono oggi
opensituas -o csv get 99 --from 21/10/2001 --to 31/12/2024 --out mapping_2001_2024.csv
# Affiancamento completo: chi c'era nel 2011 e nel 2021 (con eventuali blank per nuovi/soppressi)
opensituas -o csv get 298 --from 01/01/2011 --to 01/01/2021 --out confronto_2011_2021.csv
```

### Sistemi Locali del Lavoro e specializzazione produttiva

I SLL raggruppano comuni per bacino di pendolarismo — l'unità di analisi del mercato del
lavoro locale. Il report delle tassonomie ha anche la specializzazione produttiva del SLL.

```bash
opensituas -o csv get 408 --out sll_composizione.csv   # quali comuni appartengono a ogni SLL
opensituas -o csv get 444 --out sll_tassonomie.csv     # CL_DIM, CLASSE_2021_NAME, GRUPPO_2021_NAME
```

`CLASSE_2021_NAME` / `GRUPPO_2021_NAME`: specializzazione produttiva (es. distretto
manifatturiero, turismo, servizi). Utile per confronti tra aree economicamente simili.

### Cities, FUA e NUTS — classificazioni geografiche europee

Per analisi comparate con dati EUROSTAT o europei in genere.

```bash
opensituas -o csv get 414 --out cities_2021.csv      # comuni nelle "Cities" (definizione EUROSTAT)
opensituas -o csv get 446 --out fua_2021.csv         # comuni nelle Zone Urbane Funzionali 2021
opensituas -o csv get 449 --out nuts3.csv            # POP_RES, AREA_KMQ, urban/rural, costiero, confine
```

Il report 449 (`NUTS 3 - Dimensione e classificazioni`) include `COD_URBAN_RURAL` (tipologia
urbano-rurale a livello provinciale), `COD_COASTAL` e `COD_BORDER_REGION` — le classificazioni
standardizzate EUROSTAT per i confronti tra paesi.

---

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

## Altri tool

- **[opensdmx](https://github.com/ondata/opensdmx)** — Statistiche ufficiali da Eurostat, ISTAT, OCSE e altri provider SDMX, senza allucinazioni.
- **[ISTAT MCP Server](https://github.com/ondata/istat_mcp_server)** — Dati statistici ISTAT direttamente nel tuo assistente AI, via protocollo MCP.
- **[CKAN MCP Server](https://github.com/ondata/ckan-mcp-server)** — Qualsiasi portale open data CKAN diventa una conversazione in linguaggio naturale.

## Licenza

MIT
