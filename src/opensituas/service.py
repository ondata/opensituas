"""Operazioni report condivise tra CLI e libreria, su record grezzi."""

from . import _catalog, base
from ._which import search as _which_search

CATALOG_COLUMNS = (
    "pfun",
    "titolo",
    "validità",
    "analisi",
    "ambito",
    "unità",
    "parametri",
)


def catalog_records(
    keyword: str | None = None,
    *,
    ambito: str | None = None,
    unita: str | None = None,
    refresh: bool = False,
) -> list[dict]:
    entries = _catalog.filter_catalog(
        _catalog.load_catalog(refresh=refresh),
        keyword=keyword,
        ambito=ambito,
        unita=unita,
    )
    fields = (
        "Id report",
        "Titolo report",
        "Inizio/fine validità report",
        "Analisi temporale",
        "Ambito territoriale",
        "Unità territoriale",
        "parametri necessari",
    )
    return [
        dict(zip(CATALOG_COLUMNS, (entry.get(field) for field in fields)))
        for entry in entries
    ]


WHICH_COLUMNS = (
    "pfun",
    "titolo",
    "analisi",
    "ambito",
    "unità",
    "comando_suggerito",
)


def comando_suggerito(entry: dict) -> str:
    """Comando opensituas suggerito per il report, con le date di default."""
    pfun = entry.get("Id report", "?")
    if _catalog.is_range(entry):
        val = entry.get("Inizio/fine validità report", "")
        parts = val.split(" - ") if " - " in val else ["", ""]
        date_from = parts[0].strip() or "DD/MM/YYYY"
        date_to = parts[1].strip() or "DD/MM/YYYY"
        return f"opensituas get {pfun} --from {date_from} --to {date_to}"
    default = _catalog.validity_end(entry) or "DD/MM/YYYY"
    return f"opensituas get {pfun} --date {default}"


def which_records(query: str | None = None, *, limit: int = 3) -> list[dict]:
    """Report per una query in linguaggio naturale; senza query tutto il catalogo.

    Solleva ``SituasError`` se la query non trova nessun report.
    """
    items = _catalog.load_catalog()
    if query:
        matched = _which_search(query, items, limit)
        if not matched:
            raise base.SituasError(f"Nessun report corrisponde a '{query}'")
    else:
        matched = items
    fields = ("Id report", "Titolo report", "Analisi temporale", "Ambito territoriale", "Unità territoriale")
    return [
        {**dict(zip(WHICH_COLUMNS, (e.get(f) for f in fields))), "comando_suggerito": comando_suggerito(e)}
        for e in matched
    ]


def report_info(
    pfun: int | str,
    *,
    timeout: float = base.DEFAULT_TIMEOUT,
    catalog: list[dict] | None = None,
) -> dict:
    """Metadati del report; ``catalog`` evita di rileggere cache o gateway."""
    entry = _catalog.get_entry(pfun, catalog)
    link = _catalog.apply_date(
        entry["INFO_LINK"], default_date=_catalog.validity_end(entry)
    )
    data = base.publish_get(link, timeout=timeout)
    return {
        "pfun": pfun,
        "report": data.get("REPORT NAME"),
        "descrizione": data.get("REPORT DESCRIZIONE"),
        "colonne": [
            {
                "colonna": col.get("COLNAME"),
                "label": col.get("LABEL"),
                "tipo": col.get("TYPE"),
                "guida": col.get("GUIDA"),
            }
            for col in data.get("COL_DETAILS", [])
        ],
    }


def _report_rows(
    pfun: int | str,
    link_key: str,
    *,
    date: str | None,
    date_from: str | None,
    date_to: str | None,
    timeout: float,
) -> list[dict]:
    entry = _catalog.get_entry(pfun)
    link = _catalog.apply_date(
        entry[link_key],
        date,
        date_from,
        date_to,
        default_date=_catalog.validity_end(entry),
    )
    return base.rows(base.publish_get(link, timeout=timeout))


def report_records(
    pfun: int | str,
    *,
    date: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    timeout: float = base.DEFAULT_TIMEOUT,
) -> list[dict]:
    return _report_rows(
        pfun,
        "SPOOL_LINK",
        date=date,
        date_from=date_from,
        date_to=date_to,
        timeout=timeout,
    )


def count_records(
    pfun: int | str,
    *,
    date: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    timeout: float = base.DEFAULT_TIMEOUT,
) -> list[dict]:
    return _report_rows(
        pfun,
        "COUNT_LINK",
        date=date,
        date_from=date_from,
        date_to=date_to,
        timeout=timeout,
    )
