# Ricerca `which` - 2026-11-15

Problema: `which` cerca solo in titolo/ambito/unità, con sottostringhe e senza parole vuote. Verificati 17 casi (`tmp/which-index/`): sbagliano o non trovano nulla 2 dei 4 esempi documentati (`popolazione` della demo web, `province cessate` di help e README) e le domande su popolazione, superficie, zona altimetrica, montagna, fusioni. Il report 74 «Comuni - Dimensione» non esce per «popolazione e superficie dei comuni».

## Esito

- [x] Fase 1 - test rossi: `tests/test_which_search.py`, 14 rossi su 21 prima del fix (2026-11-15).
- [x] Fase 2 - indice: `scripts/build_which_index.py` → `src/opensituas/which_index.json`, 77 report, 35 KB, presente nella wheel; rigenerazione in `docs/release.md` (entrambi i flussi) e nella skill `release`.
- [x] Fase 3 - ricerca: `src/opensituas/_which.py`; 88 test verdi, ruff pulito; verificato senza rete (indice letto dal pacchetto).
- [x] Fase 4 - documentazione: esempi di help, README e demo web rilanciati con la CLI, primo risultato atteso; «comuni per anno» sostituito; LOG aggiornato.
- [x] Libreria allineata: `opensituas.which()` su `service.which_records`, test di parità con la CLI; README e architettura aggiornati.
- Decisioni: indice incluso nel pacchetto, sinonimi curati con un test ciascuno, consegna via PR.
- Da fare fuori da questo lavoro: aggiornare `catalog_snapshot.json` (74 report contro 77 online).

# Skill `release` - 2026-11-15

- [x] Leggere `docs/release.md` e le release precedenti → verify: procedura e formato note noti
- [x] Scrivere `.claude/skills/release/SKILL.md`, solo invocazione manuale → verify: frontmatter con `disable-model-invocation: true`
- [x] Provare a secco i comandi di verifica (`uv build -o`, `twine check`, import della wheel, API PyPI) → verify: tutti eseguiti in `tmp/`, nessuna pubblicazione; il controllo versione rileva `__version__` 0.1.0 contro 0.1.2

## Review

- Skill committata nel branch `chore/release-skill`.
- Tolto `Bash(twine upload *)` da `settings.local.json` (file locale, non committato).
- `__version__` da `importlib.metadata`; test `tests/test_version.py` rosso prima del fix, verde dopo; 63 test verdi, ruff pulito.
- Trovato: `uv run --with <wheel>` riusa la cache a parità di nome file; aggiunto `--no-cache` nella skill.

# Release opensituas 0.1.0 su PyPI

Segue il flusso di `opensdmx/docs/release.md`. Versione già 0.1.0 in pyproject.

## Fase 1 — Preparazione repo/pacchetto
- [ ] Fix ruff: rimuovere variabile non usata `cfg` in `territorial.py:138`
- [ ] Allinea `pyproject.toml` a opensdmx: `authors`, `keywords`, `classifiers`,
      `[dependency-groups] dev` (pytest, ruff), `[tool.ruff.lint]`, pin `uv_build`
- [ ] Aggiungi `LICENSE` (MIT) — manca
- [ ] Crea `docs/release.md` (adattato da opensdmx)
- [ ] Rendi pubblico il repo: `gh repo edit --visibility public`

## Fase 2 — Verifiche (devono passare)
- [ ] `uv lock`
- [ ] `uv run ruff check src/`
- [ ] `uv run pytest tests/ -v`
- [ ] Aggiorna `LOG.md` con note release

## Fase 3 — Commit, tag, push
- [ ] commit prep release + `git tag v0.1.0`
- [ ] `git push origin main --tags`

## Fase 4 — Pubblicazione
- [ ] `gh release create v0.1.0`
- [ ] `uv build` + `twine upload dist/opensituas-0.1.0*` (confermo prima)
- [ ] `uv tool install --editable .`

## Review — completata
- 0.1.0 pubblicata su PyPI: https://pypi.org/project/opensituas/0.1.0/ (HTTP 200)
- GitHub release v0.1.0 (non-draft) su repo reso PUBLIC
- pyproject allineato a opensdmx; LICENSE MIT + docs/release.md aggiunti
- Fix ruff F841; ruff pulito, 18 test verdi, `twine check` PASSED
- CLI locale reinstallata (opensituas==0.1.0 editable)
