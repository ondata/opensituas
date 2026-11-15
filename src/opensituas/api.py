"""API Python pubblica: DataFrame per dati tabellari, senza output su console."""

from __future__ import annotations

import re

import pandas as pd

from . import base, service, territorial


def catalog(
    keyword: str | None = None,
    *,
    ambito: str | None = None,
    unita: str | None = None,
    refresh: bool = False,
) -> pd.DataFrame:
    """Elenca i report, filtrando titolo, ambito e unità (sottostringhe).

    Usa cache e fallback offline del catalogo; ``refresh=True`` tenta il gateway.
    Anche senza risultati il DataFrame mantiene le sette colonne del catalogo.
    """
    records = service.catalog_records(
        keyword,
        ambito=ambito,
        unita=unita,
        refresh=refresh,
    )
    return pd.DataFrame(records, columns=service.CATALOG_COLUMNS)


def which(query: str | None = None, *, limit: int = 3) -> pd.DataFrame:
    """Trova i report per una query in linguaggio naturale, come ``opensituas which``.

    Cerca in titolo, unità e colonne dei report. L'indice delle colonne è incluso
    nel pacchetto; il catalogo si carica come in ``catalog()`` (cache, poi gateway,
    poi snapshot incluso), quindi senza cache valida può contattare ISTAT. Senza
    ``query`` restituisce tutto il catalogo. Solleva ``SituasError`` se la query
    non trova nessun report.
    """
    records = service.which_records(query, limit=limit)
    return pd.DataFrame(records, columns=service.WHICH_COLUMNS)


def info(pfun: int | str, *, timeout: float = base.DEFAULT_TIMEOUT) -> dict:
    """Metadati alla fine validità: pfun, report, descrizione, colonne.

    ``colonne`` è una lista di dizionari. ``timeout`` riguarda la richiesta
    publish, non il caricamento del catalogo. Solleva ``SituasError`` per
    report assenti o errori del servizio.
    """
    return service.report_info(pfun, timeout=timeout)


def get(
    pfun: int | str,
    *,
    date: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    timeout: float = base.DEFAULT_TIMEOUT,
) -> pd.DataFrame:
    """Scarica un report in un DataFrame, conservando nomi e codici testuali.

    Date DD/MM/YYYY: ``date`` per DATA (default fine validità), oppure
    ``date_from``/``date_to`` per PERIODO (default dai link del catalogo).
    Un report vuoto restituisce un DataFrame senza colonne. Nessuna conversione
    automatica di stringhe in numeri o date, né riempimento dei mancanti.
    ``timeout`` riguarda solo publish. Solleva ``SituasError`` per errori API,
    report assenti o combinazioni di parametri data incompatibili.
    """
    return pd.DataFrame(
        service.report_records(
            pfun,
            date=date,
            date_from=date_from,
            date_to=date_to,
            timeout=timeout,
        )
    )


def count(
    pfun: int | str,
    *,
    date: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    timeout: float = base.DEFAULT_TIMEOUT,
) -> int:
    """Conta le righe via endpoint dedicato senza scaricare il report.

    Date e timeout seguono ``get``. Restituisce un intero non negativo;
    ``SituasError`` segnala errori API o un conteggio vuoto/non valido,
    distinto da uno zero effettivo.
    """
    records = service.count_records(
        pfun,
        date=date,
        date_from=date_from,
        date_to=date_to,
        timeout=timeout,
    )
    if len(records) != 1 or not isinstance(records[0], dict):
        raise base.SituasError("Risposta di conteggio SITUAS non valida")
    value = records[0].get("NUM_ROWS")
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, str) and re.fullmatch(r"[0-9]+", value.strip()):
        try:
            return int(value.strip())
        except ValueError as exc:
            raise base.SituasError("Risposta di conteggio SITUAS non valida") from exc
    raise base.SituasError("Risposta di conteggio SITUAS non valida")


def storia(tipo: str, query: str, *, dettaglio: bool = False) -> pd.DataFrame:
    """Eventi in ordine cronologico; metadati dell'unità in ``df.attrs['unita']``.

    ``tipo``: comune, provincia o regione; ``query``: nome o codice testuale.
    ``SituasError`` segnala errori API, unità assenti o nomi ambigui.
    Con ``dettaglio=True``, provvedimento e unità coinvolte restano liste nelle
    celle; dettagli non disponibili sono liste vuote, come nella CLI.
    Gli attrs non sono garantiti dopo trasformazioni o esportazioni pandas.
    Usa il timeout territoriale predefinito, non ``OPENSITUAS_TIMEOUT``.
    """
    result = territorial.storia(tipo, query, dettaglio=dettaglio)
    frame = pd.DataFrame(result["storia"])
    frame.attrs["unita"] = result["unita"]
    return frame


def cerca_codice(tipo: str, query: str, *, limit: int = 20) -> pd.DataFrame:
    """Cerca codici e validità per comune, provincia o regione, da nome/codice.

    Oltre ``limit`` criteri distinti restituisce il marker ``_ambiguo`` e le
    voci ``V`` di disambiguazione, non risultati completi. Solleva
    ``SituasError`` se non trova codici o per errori API. Usa il timeout
    territoriale predefinito.
    """
    return pd.DataFrame(territorial.cerca_codice(tipo, query, limit=limit))
