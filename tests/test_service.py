import pytest
from opensituas import base, service


@pytest.mark.parametrize(
    "fn", [service.report_records, service.count_records, service.report_info]
)
def test_latest_date_and_timeout(report_backend, fn):
    fn("61", timeout=7.0)
    assert report_backend["calls"][-1][1]["pdata"] == ["31/05/2026"]
    assert report_backend["calls"][-1][2] == 7.0


@pytest.mark.parametrize("fn", [service.report_records, service.count_records])
def test_explicit_date(report_backend, fn):
    fn(61, date="01/01/2020")
    assert report_backend["calls"][-1][1]["pdata"] == ["01/01/2020"]


def test_range_and_invalid_date_pattern(report_backend):
    entry = report_backend["entry"]
    for key in ("SPOOL_LINK", "COUNT_LINK"):
        entry[key] = entry[key].replace(
            "pdata=01/01/1948", "pdatada=17/03/1861&pdataa=31/05/2026"
        )
    for fn in (service.report_records, service.count_records):
        fn(61)
        query = report_backend["calls"][-1][1]
        assert query["pdatada"] == ["17/03/1861"]
        assert query["pdataa"] == ["31/05/2026"]
        fn(61, date_from="01/01/2000", date_to="31/12/2020")
        query = report_backend["calls"][-1][1]
        assert query["pdatada"] == ["01/01/2000"]
        assert query["pdataa"] == ["31/12/2020"]
        assert "pdata" not in query
        with pytest.raises(base.SituasError):
            fn(61, date="01/01/2020")


def test_catalog_filters_and_refresh(report_backend):
    rows = service.catalog_records(
        "comuni", ambito="amministrative", unita="comune", refresh=True
    )
    assert rows == [
        {
            "pfun": "61",
            "titolo": "Comuni - Elenco",
            "validità": "01/01/1948 - 31/05/2026",
            "analisi": "DATA",
            "ambito": "Unità amministrative",
            "unità": "Comune",
            "parametri": "pdata",
        }
    ]
    assert report_backend["refresh"] is True
    assert service.catalog_records("inesistente") == []


def test_raw_results_and_metadata(report_backend):
    assert service.report_records(61) == report_backend["rows"]
    assert service.count_records(61) == [{"NUM_ROWS": "2"}]
    assert service.report_info(61) == {
        "pfun": 61,
        "report": "Comuni - Elenco",
        "descrizione": "Elenco comuni",
        "colonne": [
            {
                "colonna": "PRO_COM_T",
                "label": "Codice",
                "tipo": "VARCHAR2",
                "guida": "Codice ISTAT",
            }
        ],
    }
