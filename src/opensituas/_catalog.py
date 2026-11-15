"""Catalogo dei report SITUAS (i 74 "microservizi").

Il catalogo si ottiene SOLO via gateway (`get_elenco_microservizi`); il base publish
restituisce 401. Viene cachato in ``~/.cache/opensituas/catalog.json`` (TTL 7 giorni),
con fallback allo snapshot incluso nel package per il primo avvio offline.

Ogni voce espone link pre-compilati con date valide (`SPOOL_LINK`, `COUNT_LINK`,
`INFO_LINK`): sono la **fonte di verità** per la data. Per cambiare data si sostituisce
solo il parametro nel link (vedi `apply_date`), senza ri-derivarla dalla validità.
"""

from __future__ import annotations

import json
import time
from importlib.resources import files
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from . import base

_CACHE_DIR = Path.home() / ".cache" / "opensituas"
_CACHE_FILE = _CACHE_DIR / "catalog.json"
_TTL = 7 * 24 * 3600  # 7 giorni
_SERVICE = "get_elenco_microservizi"


def _bundled() -> list[dict]:
    raw = files("opensituas").joinpath("catalog_snapshot.json").read_text("utf-8")
    return json.loads(raw).get("items", [])


def load_catalog(refresh: bool = False) -> list[dict]:
    """Restituisce il catalogo (lista di voci report).

    Ordine: cache fresca → gateway → cache stantia → snapshot incluso.
    """
    if not refresh and _CACHE_FILE.exists():
        if time.time() - _CACHE_FILE.stat().st_mtime < _TTL:
            return json.loads(_CACHE_FILE.read_text("utf-8"))
    try:
        items = base.gateway(_SERVICE).get("items", [])
        if items:
            _CACHE_DIR.mkdir(parents=True, exist_ok=True)
            _CACHE_FILE.write_text(json.dumps(items, ensure_ascii=False), "utf-8")
            return items
    except base.SituasError:
        pass
    if _CACHE_FILE.exists():
        return json.loads(_CACHE_FILE.read_text("utf-8"))
    return _bundled()


def get_entry(pfun: int | str, catalog: list[dict] | None = None) -> dict:
    """Voce del catalogo per id report (`pfun`)."""
    catalog = catalog if catalog is not None else load_catalog()
    pid = str(pfun)
    for entry in catalog:
        if str(entry.get("Id report")) == pid:
            return entry
    raise base.SituasError(f"Report pfun={pfun} non presente nel catalogo")


def filter_catalog(
    catalog: list[dict],
    keyword: str | None = None,
    ambito: str | None = None,
    unita: str | None = None,
) -> list[dict]:
    """Filtra le voci per parola chiave (sul titolo), ambito e unità territoriale."""

    def match(entry: dict) -> bool:
        if keyword and keyword.lower() not in entry.get("Titolo report", "").lower():
            return False
        if ambito and ambito.lower() not in entry.get("Ambito territoriale", "").lower():
            return False
        if unita and unita.lower() not in entry.get("Unità territoriale", "").lower():
            return False
        return True

    return [e for e in catalog if match(e)]


def is_range(entry: dict) -> bool:
    """True se il report è a intervallo (PERIODO, parametri pdatada/pdataa)."""
    return "pdatada" in entry.get("parametri necessari", "")


def validity_end(entry: dict) -> str | None:
    """Data di fine validità (DD/MM/YYYY) dal campo catalogo, o None se assente."""
    val = entry.get("Inizio/fine validità report", "")
    if " - " in val:
        return val.split(" - ", 1)[1].strip() or None
    return None


def apply_date(
    link: str,
    date: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    default_date: str | None = None,
) -> str:
    """Sostituisce nel link SOLO i parametri data (`pdata` o `pdatada`/`pdataa`).

    Il resto del link (pre-validato dal catalogo) resta intatto. Per i report a data
    singola (DATA), se non si passa ``date`` viene usata ``default_date`` (di norma la
    fine validità, cioè il dato più recente): i link del catalogo portano invece la data
    di *inizio* validità, che darebbe lo snapshot più vecchio. Solleva errore se si
    mescola `--date` con `--from/--to` o si usa il pattern sbagliato per il tipo report.
    """
    if date and (date_from or date_to):
        raise base.SituasError("Usa --date oppure --from/--to, non entrambi")

    parts = urlsplit(link)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    link_is_range = "pdatada" in query or "pdataa" in query

    if link_is_range:
        if date:
            raise base.SituasError(
                "Report a intervallo (PERIODO): usa --from/--to, non --date"
            )
        if date_from:
            query["pdatada"] = date_from
        if date_to:
            query["pdataa"] = date_to
    else:
        if date_from or date_to:
            raise base.SituasError(
                "Report a data singola (DATA): usa --date, non --from/--to"
            )
        if date:
            query["pdata"] = date
        elif default_date:
            query["pdata"] = default_date

    new_query = urlencode(query, safe="/")
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))
