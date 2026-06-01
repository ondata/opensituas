Todo — tutorial opensituas per giornalisti

## Obiettivo
Simulare l'uso da parte di un giornalista, testare ogni comando con chiamate API
reali, poi scrivere docs/tutorial-giornalisti.md con casi d'uso verificati.

## Fase 1 — Test funzionale ✅
- [x] catalog (json/csv/table)
- [x] info report 61
- [x] count comuni oggi (scoperta: default = inizio validità → fix a fine validità)
- [x] get dati (csv) + verifica conteggio reale
- [x] storia comune (Mappano, Borgo Mantovano, Lonato del Garda)
- [x] storia provincia (Carbonia-Iglesias) / regione
- [x] cerca-codice (Roma, Samone omonimi)
- [x] errore data fuori validità (exit code 2 confermato)

## Fase 2 — Casi d'uso giornalistici ✅
- [x] A: serie storica numero comuni 1948-2026
- [x] B: fusione / scorporo / cambio nome via storia
- [x] C: province/UTS soppresse (Carbonia-Iglesias + report 112)
- [x] D: cerca-codice e omonimi
- [x] E: export CSV per foglio/DataWrapper

## Fase 3 — Fix e docs ✅
- [x] Fix default data report DATA → fine validità (codice + 4 test nuovi)
- [x] Aggiornati help get/count, SKILL.md, README, memoria API
- [x] docs/tutorial-giornalisti.md
- [x] 18 test verdi
- [x] LOG.md

## Review
- Bug #1 (data default): `count 61` dava 7688 (comuni 1948) invece di 7894 (oggi).
  Fix: default = fine validità per report DATA. validity_end copre tutti i 52 report DATA.
- Bug #2 (cerca-codice): duplicava i record per omonimi (Samone 12 invece di 6). Causa
  verificata leggendo il codice: la LOV ripete lo stesso RC su più voci e il tool iterava
  per match invece che per RC distinto (anche chiamate di rete ridondanti). Fix: dedup per
  RC. Verificato: Samone 6 unici, Roma 1, chiamate dimezzate.
- Tutorial: solo Markdown, output reali verificati riga per riga.
- 18 test verdi (catalog.py + territorial.py invariati a livello di API pubblica).
