from urllib.parse import parse_qs, urlsplit

import pytest


@pytest.fixture
def report_backend(monkeypatch):
    from opensituas import _catalog, base

    root = "https://example.test/publish"
    entry = {
        "Id report": "61",
        "Titolo report": "Comuni - Elenco",
        "Inizio/fine validità report": "01/01/1948 - 31/05/2026",
        "Analisi temporale": "DATA",
        "Ambito territoriale": "Unità amministrative",
        "Unità territoriale": "Comune",
        "parametri necessari": "pdata",
        "SPOOL_LINK": f"{root}/reportspooljson?pfun=61&pdata=01/01/1948",
        "COUNT_LINK": f"{root}/reportspooljsoncount?pfun=61&pdata=01/01/1948",
        "INFO_LINK": f"{root}/info?pfun=61&pdata=01/01/1948",
    }
    state = {
        "entry": entry,
        "catalog": [entry],
        "calls": [],
        "rows": [
            {"PRO_COM_T": "058091", "COMUNE": "Roma", "AREA_KMQ": 1287.36},
            {"PRO_COM_T": "001001", "COMUNE": "Agliè", "AREA_KMQ": None},
        ],
        "count": [{"NUM_ROWS": "2"}],
    }

    def load(refresh=False):
        state["refresh"] = refresh
        return state["catalog"]

    def publish(url, timeout=60.0):
        state["calls"].append(
            (urlsplit(url).path, parse_qs(urlsplit(url).query), timeout)
        )
        if urlsplit(url).path.endswith("reportspooljsoncount"):
            return {"resultset": state["count"]}
        if urlsplit(url).path.endswith("/info"):
            return {
                "REPORT NAME": "Comuni - Elenco",
                "REPORT DESCRIZIONE": "Elenco comuni",
                "COL_DETAILS": [
                    {
                        "COLNAME": "PRO_COM_T",
                        "LABEL": "Codice",
                        "TYPE": "VARCHAR2",
                        "GUIDA": "Codice ISTAT",
                    }
                ],
            }
        return {"resultset": state["rows"]}

    def no_gateway(*args, **kwargs):
        raise AssertionError("Rete non prevista dal test")

    monkeypatch.setattr(_catalog, "load_catalog", load)
    monkeypatch.setattr(base, "publish_get", publish)
    monkeypatch.setattr(base, "gateway", no_gateway)
    return state
