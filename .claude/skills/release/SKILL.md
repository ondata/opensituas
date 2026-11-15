---
name: release
description: Pubblica una nuova versione di opensituas su GitHub e PyPI seguendo docs/release.md, con controlli bloccanti e una conferma esplicita prima delle azioni irreversibili. Argomento opzionale - patch (default), minor, major oppure una versione esplicita X.Y.Z.
disable-model-invocation: true
argument-hint: "[patch|minor|major|X.Y.Z]"
---

# Release di opensituas

Fonte di verità della procedura: `docs/release.md`. Questa skill la esegue con controlli in più. Se `docs/release.md` e questa skill divergono, fermarsi e segnalarlo invece di scegliere.

Argomento ricevuto: `$ARGUMENTS` (vuoto = `patch`).

## Regole

- Ogni controllo che fallisce **ferma la release**: si riporta l'errore testuale e lo stato raggiunto, non si aggira.
- Nulla di esterno (push, tag remoto, GitHub release, PyPI) prima della conferma del passo 4.
- Dopo la conferma, se un passo fallisce ci si ferma e si dice esattamente cosa è già pubblicato e cosa no: una release a metà va riferita, non riparata in silenzio.
- Non toccare file estranei alla release.

## 1. Controlli preliminari (bloccanti)

```bash
git branch --show-current          # deve essere main
git fetch origin && git status -sb # deve essere "## main...origin/main", senza ahead/behind
git status --porcelain             # nessun file tracciato modificato
```

- File non tracciati: elencarli e chiedere se ignorarli; non vanno nel commit di release.
- Versione corrente: `version` in `pyproject.toml`, unica fonte. `__version__` la legge dai metadati del pacchetto (`importlib.metadata`): non si modifica a mano.
- Calcolare la nuova versione dall'argomento. Verificare che non esista già:
  - `git tag -l vX.Y.Z` vuoto, anche su `git ls-remote --tags origin`
  - `curl -s -o /dev/null -w '%{http_code}' https://pypi.org/pypi/opensituas/X.Y.Z/json` deve dare `404`
- Commit da includere: `git log --oneline vULTIMO..HEAD`. Se è vuoto, fermarsi: non c'è niente da rilasciare.

## 2. Preparazione locale

1. `version = "X.Y.Z"` in `pyproject.toml`.
2. `uv lock`
3. `uv run python scripts/build_which_index.py`: rigenera l'indice delle colonne usato da `which` (richiede rete). Se fallisce per qualche report, fermarsi.
4. `LOG.md`: nuova sezione in testa, con lo **stesso formato di intestazione delle release precedenti** (leggere l'ultima `## ... vX.Y.Z` e imitarla). Se esiste già una sezione con la data di oggi senza versione, aggiungerle la versione invece di duplicarla. Voci brevi, ricavate dai commit del passo 1.
5. Bozza delle note di rilascio GitHub in `tmp/release-notes-vX.Y.Z.md`, in italiano, con la struttura della release precedente (`gh release view vULTIMO --json body --jq .body`).

## 3. Verifiche (bloccanti)

```bash
uv run ruff check src/ tests/
uv run pytest tests/ -q
rm -rf tmp/release-dist && uv build -o tmp/release-dist
twine check tmp/release-dist/*
uv run --isolated --no-project --no-cache --with tmp/release-dist/opensituas-X.Y.Z-py3-none-any.whl \
  python -c "import opensituas; assert opensituas.__version__ == 'X.Y.Z', opensituas.__version__"
```

La build va in `tmp/release-dist`, non in `dist/`: `dist/` contiene le build delle versioni precedenti e un glob sbagliato le ricaricherebbe. `--no-cache` serve perché `uv` riusa una wheel già vista con lo stesso nome file: dopo una correzione e una seconda build, senza, il controllo girerebbe sulla wheel vecchia.

## 4. Conferma (obbligatoria)

Mostrare in un solo messaggio:

- versione vecchia → nuova
- `git diff --stat` dei file cambiati
- la nuova sezione di `LOG.md`
- le note di rilascio
- l'esito dei controlli del passo 3
- i comandi esterni che verranno eseguiti (passo 5)

Poi **chiedere conferma e aspettare**. Senza un sì esplicito ci si ferma qui; le modifiche locali restano, non committate, e si dice come annullarle (`git restore pyproject.toml uv.lock LOG.md src/opensituas/which_index.json`).

## 5. Pubblicazione (solo dopo il sì)

```bash
git add pyproject.toml uv.lock LOG.md src/opensituas/which_index.json
git diff --cached --stat           # solo questi file
git commit -m "chore: bump version to vX.Y.Z"
git tag vX.Y.Z
git push origin main
git push origin vX.Y.Z
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file tmp/release-notes-vX.Y.Z.md
twine upload tmp/release-dist/opensituas-X.Y.Z*
uv tool install --editable . --force
```

`git add` con i file nominati, non `git add -u`: raccoglierebbe modifiche estranee.

## 6. Verifica finale

- `curl -s https://pypi.org/pypi/opensituas/json | jq -r .info.version` → `X.Y.Z` (l'indice può tardare un minuto: riprovare una volta prima di dichiarare un problema)
- `gh release view vX.Y.Z --json isDraft,tagName`
- `opensituas --help` funziona con la CLI reinstallata
- Riepilogo all'utente: link PyPI, link GitHub release, SHA del commit.
