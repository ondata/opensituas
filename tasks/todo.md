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
