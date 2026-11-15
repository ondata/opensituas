"""Rigenera src/opensituas/which_index.json: nome ed etichetta delle colonne di ogni report.

Serve a `opensituas which` per trovare i report anche per contenuto (es. popolazione,
superficie), non solo per titolo. Richiede rete: una chiamata `info` per report.

Uso: uv run python scripts/build_which_index.py
"""

import json
import sys
from datetime import date
from pathlib import Path

import opensituas
from opensituas import _catalog as catalog
from opensituas import base

OUT = Path(__file__).resolve().parents[1] / "src" / "opensituas" / "which_index.json"


def main() -> int:
    # Catalogo letto dal gateway senza i ripieghi di load_catalog (cache, snapshot):
    # un catalogo vecchio farebbe sparire dall'indice i report nuovi.
    try:
        items = base.gateway(catalog._SERVICE).get("items", [])
    except base.SituasError as exc:
        print(f"Indice non scritto, catalogo online non disponibile: {exc}", file=sys.stderr)
        return 1
    if not items:
        print("Indice non scritto, il catalogo online è vuoto", file=sys.stderr)
        return 1
    reports, falliti = {}, []
    for entry in items:
        pfun = entry["Id report"]
        try:
            colonne = opensituas.info(pfun)["colonne"]
        except opensituas.SituasError as exc:
            falliti.append(f"{pfun}: {exc}")
            continue
        reports[str(pfun)] = [f"{c['colonna']} {c.get('label') or ''}".strip() for c in colonne]
    if falliti:
        print("Indice non scritto, report falliti:\n" + "\n".join(falliti), file=sys.stderr)
        return 1
    OUT.write_text(
        json.dumps({"generated": date.today().isoformat(), "reports": reports}, ensure_ascii=False, indent=0) + "\n",
        encoding="utf-8",
    )
    print(f"{len(reports)} report scritti in {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
