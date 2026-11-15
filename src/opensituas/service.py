"""Operazioni report condivise tra CLI e libreria, su record grezzi."""

from . import _catalog, base

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


def report_info(pfun: int | str, *, timeout: float = base.DEFAULT_TIMEOUT) -> dict:
    entry = _catalog.get_entry(pfun)
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
