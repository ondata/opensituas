"""Ricerca dei report per `which`: titolo, unità e colonne, con parole vuote e sinonimi.

Le colonne vengono da ``which_index.json`` (incluso nel pacchetto, rigenerato con
``scripts/build_which_index.py``): così «popolazione» trova «Comuni - Dimensione»
anche se la parola non è nel titolo. Questo modulo non fa chiamate di rete: il
catalogo da cercare lo riceve già caricato.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from importlib.resources import files

_STOP = {
    "a", "ad", "al", "ai", "alla", "alle", "anche", "che", "come", "con", "da", "dal", "dai",
    "dalla", "del", "dei", "degli", "della", "delle", "di", "e", "ed", "fra", "gli", "i", "il",
    "in", "la", "le", "lo", "nel", "nei", "nella", "o", "per", "quale", "quali", "quanti",
    "quante", "su", "sui", "tra", "tutti", "tutte", "un", "una", "uno",
}

# Radice della parola cercata → radici con cui compare in titoli e colonne.
_SINONIMI = {
    "cessat": {"soppre", "cedut"},
    "fusion": {"variaz"},
    "montag": {"montan"},
    "abitan": {"popola"},
    "estens": {"superf"},
}

_TITOLO, _COLONNA = 3, 1


def _radice(token: str) -> str:
    if len(token) > 6:
        return token[:6]
    if len(token) > 4 and token[-1] in "aeiou":
        return token[:-1]
    return token


def _radici(testo: str) -> set[str]:
    testo = unicodedata.normalize("NFKD", testo.lower()).encode("ascii", "ignore").decode()
    return {_radice(t) for t in re.findall(r"[a-z0-9]+", testo) if t not in _STOP}


@lru_cache(maxsize=1)
def _indice_incluso() -> dict[str, list[str]]:
    try:
        raw = files("opensituas").joinpath("which_index.json").read_text("utf-8")
    except FileNotFoundError:
        return {}
    return json.loads(raw).get("reports", {})


def search(query: str, items: list[dict], limit: int, index: dict | None = None) -> list[dict]:
    """Report ordinati per rilevanza; a parità prima i report comunali, poi ordine del catalogo."""
    if index is None:
        index = _indice_incluso()
    cercate = [{r} | _SINONIMI.get(r, set()) for r in _radici(query)]
    if not cercate:
        return []
    risultati = []
    for pos, entry in enumerate(items):
        titolo = _radici(" ".join([
            entry.get("Titolo report", ""),
            entry.get("Ambito territoriale", ""),
            entry.get("Unità territoriale", ""),
        ]))
        colonne = _radici(" ".join(index.get(str(entry.get("Id report")), [])))
        score = sum(
            (_TITOLO if varianti & titolo else 0) + (_COLONNA if varianti & colonne else 0)
            for varianti in cercate
        )
        if score:
            comunale = entry.get("Unità territoriale") == "Comune"
            risultati.append((-score, not comunale, pos, entry))
    risultati.sort(key=lambda r: r[:3])
    return [r[3] for r in risultati[:limit]]
