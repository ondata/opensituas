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
# elenco nomi
opensituas -o json info 50 | jq '[.colonne[].colonna]'
# tabella nome / tipo / descrizione
opensituas -o json info 50 | jq '.colonne[] | {colonna, tipo, guida}'
# vista sintetica per orientarsi rapidamente
opensituas info 50
```

## Fase 3 — Scarica i dati

Per i report `DATA` (snapshot a una data), senza `--date` ottieni il dato **più
recente**: la CLI usa la **fine validità** mostrata in `catalog`. Per una data storica
passa `--date`. (Nota: i link del catalogo portano la data di *inizio* validità; la CLI la
sostituisce di default con la fine, altrimenti otterresti lo snapshot più vecchio.)

```bash
opensituas -o json get 61                       # comuni di OGGI (fine validità)
opensituas -o json get 61 --date 01/01/2000     # report DATA storico: --date DD/MM/YYYY
opensituas -o json count 98 --from 17/03/1861 --to 31/05/2026   # report PERIODO
opensituas -o csv  get 61 --out comuni.csv       # salva su file
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

## Casi d'uso tipici

### Master table codici — join universale con altri dataset

Il report 61 è la riga-per-comune con tutti i livelli gerarchici. Chiave universale:
`PRO_COM_T` (6 caratteri alfanumerici). Usarlo come base per qualsiasi join su dati
pubblici italiani (ISTAT, Ministeri, Open Data PA).

```bash
opensituas -o csv get 61 --out comuni.csv
opensituas -o json get 61 | jq '.[] | {PRO_COM_T, COMUNE, COD_REG, COD_UTS}'
```

---

### Codici geografici e statistici ufficiali (e loro storia)

Il SITUAS è la fonte autoritativa dei codici Istat: ripartizioni, regioni, province/uts,
comuni — dall'Unità d'Italia a oggi.

**Elenco codici e denominazioni a una data:**

```bash
# Report corrente (1948 → oggi): codici di regioni, province, comuni in un'unica tabella
opensituas -o json get 61                          # snapshot alla data più recente
opensituas -o json get 61 --date 01/01/2000        # snapshot storico

# Periodi storici precedenti al 1948
opensituas -o json get 50                          # 1927–1947
opensituas -o json get 51                          # 1861–1927
```

Il report 61 (`Elenco dei codici e delle denominazioni delle unità territoriali`) è il
riferimento principale: contiene codici alfanumerici e numerici di ripartizione, regione,
provincia/uts e comune con tutte le denominazioni ufficiali.

**Storia di una singola unità:**

```bash
opensituas -o json storia comune "Sesto San Giovanni"
opensituas -o json storia comune 015179 --dettaglio   # + provvedimento e unità coinvolte
opensituas -o json storia provincia "Milano"
```

**Variazioni in un intervallo (bulk):**

```bash
# Tutti i comuni con cambio denominazione dal 1861 a oggi
opensituas -o json get 104 --from 17/03/1861 --to 31/05/2026

# Variazioni amministrative e territoriali dei comuni dal 1991
opensituas -o json get 129
```

---

### Dati di normalizzazione per comune

Per arricchire dataset con attributi demografici e territoriali ufficiali. SITUAS fornisce
**popolazione**, **superficie in km²** e **caratteristiche territoriali** per comune.

**Popolazione e superficie (dato censuario):**

```bash
# pfun 74 — Comuni - Dimensione
# Campi chiave: PRO_COM_T, COMUNE, POP_LEG, ANNO_CENSIMENTO, POP_RES, ANNO_POP_RES, AREA_KMQ, ANNO_AREA
opensituas -o csv get 74 --out comuni_dim.csv
```

| Campo | Contenuto | Disponibile da |
|---|---|---|
| `POP_LEG` | Popolazione legale (censimento) | IX Censimento 1951 |
| `POP_RES` | Popolazione residente | 31/12/2001 |
| `AREA_KMQ` | Superficie territoriale in km² | XIV Censimento 2001 |
| `ANNO_CENSIMENTO` / `ANNO_AREA` | Anno di riferimento del dato | — |


**Caratteristiche del territorio:**

```bash
# pfun 73 — Comuni - Caratteristiche del territorio
# Campi chiave: COM_LIT (litoraneo), COM_ISO (isolano), ZONA_ALT (zona altimetrica)
opensituas -o csv get 73 --out comuni_caratteristiche.csv
```

`ZONA_ALT`: 1=Montagna interna, 2=Montagna litoranea, 3=Collina interna,
4=Collina litoranea, 5=Pianura.

**Join tipico su codice comune:**

```bash
# Unisci i due report via PRO_COM_T (codice alfanumerico a 6 caratteri)
opensituas -o csv get 74 --out comuni_pop.csv
opensituas -o csv get 73 --out comuni_car.csv
duckdb -c "SELECT p.*, c.COM_LIT, c.COM_ISO, c.ZONA_ALT
           FROM read_csv('comuni_pop.csv') p
           JOIN read_csv('comuni_car.csv') c USING (PRO_COM_T)"
```

---

### Aree interne e zone di svantaggio — analisi del divario territoriale

pfun 75 (`Comuni - Aree di policy`, dal 2014): associa ogni comune alle principali
classificazioni di policy del territorio italiano.

```bash
opensituas -o csv get 75 --out comuni_policy.csv
# Filtra solo comuni ultraperiferici:
opensituas -o json get 75 | jq '[.[] | select(.AREE_INT_2020 == "F-Ultraperiferico")]'
# Conta comuni per classe aree interne:
opensituas -o json get 75 | jq 'group_by(.AREE_INT_2020) | map({classe: .[0].AREE_INT_2020, n: length})'
```

Campi chiave:

| Campo | Contenuto |
|---|---|
| `AREE_INT_2020` | A-Polo · B-Polo intercomunale · C-Cintura · D-Intermedio · E-Periferico · F-Ultraperiferico |
| `MACRO_AI_2020` | I=Aree interne · NI=Non interno |
| `ZONE_MONTANE_2014` | 1=Totalmente montano · 2=Parzialmente montano · 3=Non montano |
| `ZONE_V_NAT_2020` | Zone con vincoli naturali (non montane) |
| `ZONE_S_SPECIFICI_2014` | Zone con vincoli specifici |

---

### Storia delle variazioni — fusioni, rinominazioni, soppressioni

```bash
# Storia di un singolo comune con provvedimento normativo:
opensituas -o json storia comune "Ledro" --dettaglio
opensituas -o json storia comune "Sesto San Giovanni"
# Tutte le variazioni dal 1991 (il più ricco: tipo, norma, testo):
opensituas -o csv get 129 --out variazioni_1991.csv
# Solo fusioni nel 2016:
opensituas -o json get 129 | jq '[.[] | select(.ANNO == "2016" and (.DESC_COD_VARIAZIONE | contains("fusione")))]'
# Cambi denominazione dall'Unità d'Italia:
opensituas -o json get 104 --from 17/03/1861 --to 31/05/2026 | jq '.[].COMUNE'
# Comuni soppressi (non ricostituiti):
opensituas -o json get 128 | jq 'length'
```

Il report 129 contiene `DESC_COD_VARIAZIONE` (tipo variazione: CS=Costituzione,
FU=Fusione, SC=Scorporo, CD=Cambio denominazione, ...) e `TESTO_PROVVEDIMENTO` con la
descrizione normativa.

---

### Traslazione codici tra due date — analisi longitudinale

Indispensabile quando si confrontano dataset di anni diversi: le fusioni rendono i codici
incompatibili. Questi report restituiscono la corrispondenza cod_inizio → cod_fine.

```bash
# Mapping codici: come erano nel 2001, come sono nel 2024
opensituas -o csv get 99 --from 21/10/2001 --to 31/12/2024 --out mapping_2001_2024.csv
# Affiancamento completo (blank = comune nato o soppresso nel periodo)
opensituas -o csv get 298 --from 01/01/2011 --to 01/01/2021 --out confronto_2011_2021.csv
# Solo i comuni che hanno cambiato codice:
opensituas -o json get 99 --from 01/01/2010 --to 31/12/2024 \
  | jq '[.[] | select(.PRO_COM_T_DT_IN != .PRO_COM_T_DT_FI)]'
```

---

### Sistemi Locali del Lavoro — mercato del lavoro e specializzazione produttiva

I SLL (aggiornati al Censimento 2021) raggruppano comuni per bacino di pendolarismo.
Il report 444 è il più ricco per analisi economiche: contiene la specializzazione produttiva.

```bash
opensituas -o csv get 408 --out sll_composizione.csv   # comuni → SLL (join key: PRO_COM_T)
opensituas -o csv get 444 --out sll_tassonomie.csv     # SLL con classe di pop. e specializzazione
# Tutti gli SLL a vocazione turistica:
opensituas -o json get 444 | jq '[.[] | select(.CLASSE_2021_NAME | contains("tur"))]'
# Distribuzione SLL per specializzazione:
opensituas -o json get 444 | jq 'group_by(.GRUPPO_2021_NAME) | map({gruppo: .[0].GRUPPO_2021_NAME, n: length})'
```

| Campo pfun 444 | Contenuto |
|---|---|
| `CL_DIM` | Classe dimensionale per popolazione |
| `CLASSE_2021_NAME` | Specializzazione produttiva (es. "Manifattura leggera") |
| `GRUPPO_2021_NAME` | Raggruppamento di specializzazione |

---

### Cities, FUA e NUTS — classificazioni geografiche europee

Per analisi comparate con EUROSTAT. Tre livelli: City (nucleo urbano), FUA (area
funzionale), NUTS3 (provincia con classificazioni standardizzate).

```bash
opensituas -o csv get 414 --out cities_2021.csv   # comuni nelle "Cities" EUROSTAT 2021
opensituas -o csv get 446 --out fua_2021.csv      # comuni nelle Zone Urbane Funzionali
opensituas -o csv get 449 --out nuts3.csv         # dimensione + urban/rural + costiero + confine
# Quali province sono classificate come "urbane" in Europa?
opensituas -o json get 449 | jq '[.[] | select(.COD_URBAN_RURAL == "1") | .DEN_NUTS3]'
# Province di confine:
opensituas -o json get 449 | jq '[.[] | select(.COD_BORDER_REGION == "1") | .DEN_NUTS3]'
```

Il report 449 include per ogni NUTS3: `POP_RES`, `AREA_KMQ`, `COD_URBAN_RURAL`
(1=Prevalentemente urbana · 2=Intermedia · 3=Prevalentemente rurale), `COD_COASTAL`,
`COD_BORDER_REGION`.

---

## Note operative

- Exit code `2` = errore applicativo SITUAS (messaggio su stderr); `0` = ok.
- Il catalogo è cachato 7 giorni; `opensituas catalog --refresh` lo rilegge.
- `ricostruzione-codici` del portale non ha un endpoint proprio: corrisponde ai report di
  catalogo di tipo `PERIODO` (usali con `get`/`count` e `--from/--to`).
