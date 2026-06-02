# Installa la skill situas-explorer

La skill `situas-explorer` abilita l'esplorazione guidata del **[SITUAS](https://situas.istat.it/)** (ISTAT) direttamente nel tuo agente AI, usando la CLI **[opensituas](https://github.com/ondata/opensituas)** come motore.

Le skill si possono installare in diversi modi — consulta la documentazione del tuo agente per le opzioni disponibili. Qui usiamo [skills](https://github.com/vercel-labs/skills), uno strumento che installa una skill in un solo passaggio su più agenti (Claude Code, OpenCode, GitHub Copilot, Codex e altri) in modo unificato.

## Prerequisiti

Node.js (v18+) è necessario solo per il metodo `npx skills` descritto di seguito. Installalo dal gestore di pacchetti del tuo sistema o da [nodejs.org](https://nodejs.org).

## Installazione

Esegui:

```bash
npx skills add ondata/opensituas
```

### Passo 1 — Seleziona gli agenti

L'installer scarica la skill dal repository e chiede per quali agenti installarla. Diversi agenti universali (tra cui Claude Code) sono abilitati per default. Se il tuo agente non è nell'elenco predefinito, scorri fino ad **Additional agents** per trovarlo e selezionarlo.

### Passo 2 — Scegli lo scope di installazione (Global consigliato)

Scegli tra installare per un singolo progetto o globalmente (home directory, disponibile in tutti i progetti). Si consiglia **Global** per avere la skill disponibile ovunque.

### Passo 3 — Symlink (consigliato)

Scegli come installare il file della skill. Si consiglia **Symlink**: invece di copiare il file, viene creato un collegamento simbolico alla sorgente originale. Così qualsiasi aggiornamento alla skill si riflette immediatamente ovunque, senza reinstallare.

### Passo 4 — Conferma

Rivedi e conferma con **Yes** per procedere.

## Alternativa: installazione manuale

Se preferisci non usare `npx skills`, puoi scaricare direttamente la cartella della skill e aggiungerla al tuo agente senza Node.js. La skill si trova in [`skills/situas-explorer/`](../../skills/situas-explorer/) in questo repository — consulta la documentazione del tuo agente per come registrare una cartella skill locale.

## Aggiornamento

Per aggiornare la skill all'ultima versione:

```bash
npx skills update situas-explorer
```

## Utilizzo

Una volta installata, usa `/situas-explorer` negli agenti selezionati per avviare una sessione di esplorazione guidata del SITUAS.

Per esplorare le funzionalità complete della skill prima o dopo l'installazione, consulta la [definizione della skill](../../skills/situas-explorer/SKILL.md).
