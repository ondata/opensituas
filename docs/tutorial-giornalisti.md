Tutorial: opensituas per giornalisti

Una guida pratica a `opensituas`, la CLI che interroga il **SITUAS** dell'ISTAT
(Sistema Informativo Territoriale delle Unità Amministrative e Statistiche).
Pensata per chi fa giornalismo di dati: capire quanti e quali sono i comuni, le
province, le regioni d'Italia, come sono cambiati nel tempo, e ricostruire i
codici ISTAT necessari a incrociare altre banche dati.

Tutti i comandi e gli output di questa guida sono stati eseguiti davvero contro le
API SITUAS. I numeri citati valgono alla data indicata.

## A cosa serve

SITUAS è l'anagrafe ufficiale ISTAT della geografia amministrativa italiana, dal
1861 a oggi. Per un giornalista risponde a domande come:

- Quanti comuni ha l'Italia adesso? E vent'anni fa?
- Il comune di cui scrivo è nato da una fusione? Quando? Con quali altri?
- Quali province sono state soppresse e quando?
- Qual è il codice ISTAT di un comune (per agganciarlo a dati elettorali, di
  bilancio, di popolazione)?

## Avvio rapido

```bash
uv tool install opensituas        # installazione di sistema
opensituas --help                 # panoramica comandi
```

I comandi accettano il flag globale `--output` / `-o` con tre valori:

- `table` (default) per leggere a schermo
- `csv` per aprire il risultato in un foglio di calcolo o in DataWrapper
- `json` per filtrare con `jq`

In `json`/`csv` lo stdout è pulito: i messaggi diagnostici vanno su `stderr`, così
puoi mettere in pipe il risultato senza sporcarlo.

## Tre concetti da sapere prima di iniziare

**1. Il catalogo.** SITUAS espone 74 "report" (tabelle). Ognuno ha un `pfun`
(l'identificativo) e un periodo di validità. Il flusso è sempre lo stesso:

```
catalog  (trova il report e il suo pfun)
  → info   (capisci le colonne)
  → get / count  (scarica i dati o contali)
```

**2. Report a DATA e report a PERIODO.** Nel catalogo la colonna `analisi`
distingue:

- `DATA`: fotografia a una singola data (es. "i comuni esistenti al …"). Usi
  `--date GG/MM/AAAA`.
- `PERIODO`: eventi accaduti in un intervallo (es. "comuni soppressi tra … e …").
  Usi `--from` e `--to`.

**3. La data di default (il punto che evita errori in prima pagina).** Per i
report `DATA`, se NON passi `--date`, ottieni il dato **più recente** (la fine del
periodo di validità). Se ti serve una fotografia storica, devi indicare la data
con `--date`. Se la data cade fuori dalla validità, il comando esce con codice 2 e
il messaggio `REPORT NON DISPONIBILE`.

## Caso 1 — Quanti comuni ha l'Italia, e come è cambiato nel tempo

Il report dei comuni dal 1948 a oggi è il `pfun` 61. Per il dato attuale basta
`count` (senza data: prende la fine validità):

```bash
opensituas -o json count 61 | jq '.[0].NUM_ROWS'
# 7894   (al 31/05/2026; differenza minima rispetto al dato ISTAT pubblicato,
#         ~7.896: fissa sempre la data e confronta con il comunicato ISTAT pari data)
```

La parte interessante per un pezzo è la **serie storica**: i comuni sono cresciuti
fino agli anni Novanta e poi sono calati per via delle fusioni.

```bash
for d in 01/01/1948 01/01/1971 01/01/1991 01/01/2001 01/01/2011 01/01/2021 31/05/2026; do
  printf "%s\t" "$d"
  opensituas -o json count 61 --date "$d" | jq -r '.[0].NUM_ROWS'
done
```

Risultato reale:

| Data | Numero comuni |
|---|---|
| 01/01/1948 | 7.688 |
| 01/01/1971 | 8.055 |
| 01/01/1991 | 8.100 |
| 01/01/2001 | 8.100 |
| 01/01/2011 | 8.094 |
| 01/01/2021 | 7.903 |
| 31/05/2026 | 7.894 |

Il picco è intorno al 1991-2001 (8.100); da lì in poi le fusioni hanno ridotto i
comuni di oltre 200 unità. Un grafico a linee di questa tabella è già una notizia.

## Caso 2 — Il "mio" comune: è nato da una fusione? Ha cambiato nome?

Il comando `storia` ricostruisce le variazioni di una singola unità. Funziona con
la denominazione o con il codice ISTAT.

Un comune **nato da una fusione**:

```bash
opensituas -o json storia comune "Borgo Mantovano" \
  | jq -r '.storia[] | [."data evento", .variazione, ."descrizione evento"] | @tsv'
# 01/01/2018  CS-Costituzione  NUOVO COMUNE DI BORGO MANTOVANO COSTITUITO MEDIANTE
#                              FUSIONE DEI SOPPRESSI COMUNI ...
```

Un comune **nato da scorporo** (Mappano, staccato da quattro comuni torinesi):

```bash
opensituas storia comune Mappano
# 18/04/2017  CS-Costituzione  NUOVO COMUNE DI MAPPANO COSTITUITO CON ZONE DI
#   TERRITORIO DISTACCATE DAI COMUNI DI CASELLE TORINESE, BORGARO TORINESE,
#   SETTIMO TORINESE E LEINI, NELLA CITTA' METROPOLITANA DI TORINO
```

Un comune che ha **cambiato nome**:

```bash
opensituas storia comune "Lonato del Garda"
# 17/03/1861  PV-Prima validità       DATA INIZIO SISTEMA
# 02/11/2007  CD-Cambio denominazione NUOVA DENOMINAZIONE LONATO DEL GARDA ASSUNTA
#                                     DAL COMUNE DI LONATO ...
```

Con `--dettaglio` ottieni anche il provvedimento (legge/decreto) e le unità
coinvolte, utili per linkare la fonte normativa nell'articolo:

```bash
opensituas -o json storia comune 001316 --dettaglio | jq '.storia[0].provvedimento'
```

## Caso 3 — Le province che non esistono più

`storia` vale anche per province/UTS e regioni. La provincia di
Carbonia-Iglesias, ad esempio, è durata appena dieci anni:

```bash
opensituas -o json storia provincia "Carbonia-Iglesias" \
  | jq -r '.storia[] | [."data evento", ."descrizione evento"] | @tsv'
# 01/01/2006  ISTITUZIONE DELLA NUOVA PROVINCIA DI CARBONIA-IGLESIAS ...
# 28/04/2016  ISTITUITA LA NUOVA PROVINCIA SUD SARDEGNA CON I COMUNI DISTACCATI
#             DALLE SOPPRESSE PROVINCE DI CARBONIA-IGLESIAS, MEDIO CAMPIDANO,
#             OGLIASTRA E CAGLIARI ...
```

Per l'elenco completo delle province/UTS soppresse o cedute c'è il report 112
(tipo `PERIODO`, copre il 1861-2026):

```bash
opensituas -o json count 112 | jq '.[0].NUM_ROWS'   # 48 soppressioni storiche
opensituas -o csv get 112 --out province_soppresse.csv
```

## Caso 4 — Trovare (e ricostruire) il codice ISTAT

Per incrociare i dati SITUAS con altre banche dati (popolazione, bilanci, voti)
serve il codice ISTAT. `cerca-codice` lo restituisce con i periodi di validità:

```bash
opensituas -o json cerca-codice comune Roma | jq '.[0]'
# { "Codice Istat": "058091", "Denominazione": "Roma",
#   "Data inizio": "15/01/1871", "Data fine": " " }
```

Attenzione agli **omonimi e ai codici cambiati nel tempo**: per i comuni con lo
stesso nome (es. "Samone") `cerca-codice` elenca tutte le forme storiche con il
loro intervallo di validità. Usa "Data inizio"/"Data fine" per capire quale codice
vale all'epoca che ti interessa:

```bash
opensituas -o csv cerca-codice comune Samone
```

Quando un nome è ambiguo, anche `storia` te lo segnala (exit code 2) elencando i
candidati: rilancia il comando con il codice preciso invece del nome.

## Caso 5 — Esportare una tabella per il foglio di calcolo o DataWrapper

`get` con `-o csv` e `--out` salva direttamente su file. Esempio: l'elenco
completo dei comuni di oggi, con codici e gerarchia territoriale.

```bash
opensituas info 61                       # leggi prima le colonne disponibili
opensituas -o csv get 61 --out comuni_oggi.csv
# Salvate 7894 righe in comuni_oggi.csv
```

Il CSV ha codice ripartizione/regione/provincia, codice comune (numerico e
alfanumerico), denominazione italiana e straniera: pronto per una mappa o per un
join con altri dataset comunali.

## Trucchi per il fact-checking

- **Riconcilia sempre i numeri.** Il numero di comuni "di oggi" dipende dalla data
  esatta: `count 61` dà la fine validità. Per un titolo, fissa la data con
  `--date` e confrontala con il comunicato ISTAT corrispondente.
- **Senza `--date` = dato più recente, non storico.** Per le serie storiche passa
  sempre date esplicite.
- **`analisi`: DATA vs PERIODO.** Se sbagli (`--date` su un report PERIODO o
  viceversa) la CLI te lo dice con un errore chiaro.
- **Exit code.** `0` = ok, `2` = errore applicativo SITUAS (messaggio su
  `stderr`). Utile negli script di verifica.
- **Catalogo cachato.** Il catalogo è memorizzato 7 giorni; con
  `opensituas catalog --refresh` lo rileggi dal server.

## Riferimenti

- Elenco completo dei report: `opensituas catalog`
- Dettaglio comandi: `opensituas <comando> --help`
- Come funziona internamente: [architecture.md](architecture.md)
