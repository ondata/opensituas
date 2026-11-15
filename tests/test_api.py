import pandas as pd
import pytest

import opensituas as situas
from opensituas import base


def test_public_names():
    for name in (
        "catalog",
        "info",
        "get",
        "count",
        "storia",
        "cerca_codice",
        "app",
        "main",
    ):
        assert callable(getattr(situas, name))
    assert situas.SituasError is base.SituasError


def test_catalog_and_info(report_backend):
    frame = situas.catalog(
        "comuni", ambito="amministrative", unita="comune", refresh=True
    )
    assert isinstance(frame, pd.DataFrame)
    assert list(frame.columns) == [
        "pfun",
        "titolo",
        "validità",
        "analisi",
        "ambito",
        "unità",
        "parametri",
    ]
    assert frame.iloc[0]["pfun"] == "61"
    assert report_backend["refresh"] is True
    assert isinstance(situas.info(61), dict)
    assert situas.info(61)["colonne"][0]["colonna"] == "PRO_COM_T"
    report_backend["catalog"] = []
    empty = situas.catalog()
    assert empty.empty
    assert list(empty.columns) == [
        "pfun",
        "titolo",
        "validità",
        "analisi",
        "ambito",
        "unità",
        "parametri",
    ]


def test_report_values_order_and_empty(report_backend):
    report_backend["rows"][0]["TESTO_NUMERICO"] = "001"
    frame = situas.get("61", date="01/01/2020", timeout=4.0)
    assert isinstance(frame, pd.DataFrame)
    assert frame["PRO_COM_T"].tolist() == ["058091", "001001"]
    assert frame.iloc[0]["TESTO_NUMERICO"] == "001"
    assert frame.iloc[0]["AREA_KMQ"] == 1287.36
    assert pd.isna(frame.iloc[1]["AREA_KMQ"])
    assert list(frame.columns) == ["PRO_COM_T", "COMUNE", "AREA_KMQ", "TESTO_NUMERICO"]
    assert report_backend["calls"][-1][1]["pdata"] == ["01/01/2020"]
    assert report_backend["calls"][-1][2] == 4.0
    report_backend["rows"] = []
    report_backend["calls"].clear()
    assert situas.get(61).empty
    assert len(report_backend["calls"]) == 1


@pytest.mark.parametrize("value,expected", [(0, 0), (2, 2), ("0", 0), (" 2 ", 2)])
def test_count_valid(report_backend, value, expected):
    report_backend["count"] = [{"NUM_ROWS": value}]
    assert situas.count(61) == expected
    assert type(situas.count(61)) is int
    assert all(
        path.endswith("reportspooljsoncount") for path, _, _ in report_backend["calls"]
    )


@pytest.mark.parametrize(
    "rows",
    [
        [],
        [{}],
        [{"NUM_ROWS": None}],
        [{"NUM_ROWS": True}],
        [{"NUM_ROWS": 1.5}],
        [{"NUM_ROWS": -1}],
        [{"NUM_ROWS": "abc"}],
        [{"NUM_ROWS": "1.5"}],
        [{"NUM_ROWS": 1}, {"NUM_ROWS": 2}],
    ],
)
def test_count_invalid(report_backend, rows):
    report_backend["count"] = rows
    with pytest.raises(situas.SituasError, match="conteggio"):
        situas.count(61)


def test_errors_are_silent(report_backend, monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise base.SituasError("guasto")

    monkeypatch.setattr(base, "publish_get", fail)
    for fn in (situas.get, situas.count, situas.info):
        with pytest.raises(situas.SituasError, match="guasto"):
            fn(61)
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_storia_order_metadata_and_details(monkeypatch):
    def gateway(service_name):
        if "lov_diffusione" in service_name:
            return {"items": [{"pro_com_t": "058091", "comune": "Roma"}]}
        if "rs_dett_ass" in service_name:
            return {"items": [{"codice": "001001"}]}
        if "rs_dett" in service_name:
            return {"items": [{"norma": "Legge di prova"}]}
        return {
            "items": [
                {"data evento": "01/01/2020", "id_comune_origine": 1},
                {"data evento": "01/01/2000", "id_comune_origine": 1},
            ]
        }

    monkeypatch.setattr(base, "gateway", gateway)
    frame = situas.storia("comune", "Roma", dettaglio=True)
    assert frame["data evento"].tolist() == ["01/01/2000", "01/01/2020"]
    assert frame.attrs["unita"]["code"] == "058091"
    assert frame.iloc[0]["provvedimento"] == [{"norma": "Legge di prova"}]
    assert frame.iloc[0]["unita_coinvolte"] == [{"codice": "001001"}]


def test_storia_empty_and_missing_details(monkeypatch):
    state = {"rows": []}

    def gateway(service_name):
        if "lov_diffusione" in service_name:
            return {"items": [{"pro_com_t": "058091", "comune": "Roma"}]}
        if "rs_dett" in service_name:
            raise base.SituasError("dettagli non disponibili")
        return {"items": state["rows"]}

    monkeypatch.setattr(base, "gateway", gateway)
    frame = situas.storia("comune", "Roma")
    assert frame.empty
    assert frame.attrs["unita"]["code"] == "058091"
    state["rows"] = [{"data evento": "01/01/2020", "id_comune_origine": 1}]
    frame = situas.storia("comune", "Roma", dettaglio=True)
    assert frame.iloc[0]["provvedimento"] == []
    assert frame.iloc[0]["unita_coinvolte"] == []


def test_code_search_and_disambiguation(monkeypatch):
    calls = []

    def gateway(service_name):
        calls.append(service_name)
        if "criterio_lov" in service_name:
            return {
                "resultset": [
                    {"V": "058091 - Roma", "RC": 1},
                    {"V": "000001 - Roma", "RC": 2},
                ]
            }
        return {"resultset": [{"codice": "058091", "nome": "Roma"}]}

    monkeypatch.setattr(base, "gateway", gateway)
    frame = situas.cerca_codice("comune", "Roma")
    assert isinstance(frame, pd.DataFrame)
    assert frame.iloc[0]["codice"] == "058091"
    calls.clear()
    frame = situas.cerca_codice("comune", "Roma", limit=1)
    assert "_ambiguo" in frame.columns
    assert frame.iloc[1]["V"] == "058091 - Roma"
    assert len(calls) == 1
    with pytest.raises(situas.SituasError):
        situas.cerca_codice("comune", "inesistente")


def test_import_has_no_network_output_or_cache_writes(tmp_path):
    import os
    import subprocess
    import sys

    script = """
import socket
import httpx

def blocked(*args, **kwargs):
    raise AssertionError("Rete durante import")

socket.socket.connect = blocked
socket.create_connection = blocked
httpx.Client.request = blocked
httpx.AsyncClient.request = blocked
import opensituas
assert callable(opensituas.catalog)
assert callable(opensituas.get)
assert callable(opensituas.main)
"""
    env = dict(
        os.environ,
        HOME=str(tmp_path),
        XDG_CACHE_HOME=str(tmp_path / ".cache"),
        PYTHONDONTWRITEBYTECODE="1",
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
    assert not (tmp_path / ".cache" / "opensituas").exists()
