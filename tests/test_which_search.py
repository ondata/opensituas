"""Test della ricerca `which`: logica su indice di prova e casi reali su catalogo e indice inclusi."""

import pytest

from opensituas import _catalog as catalog
from opensituas.cli import _which_search

_ITEMS = [
    {"Id report": 74, "Titolo report": "Comuni - Dimensione", "Ambito territoriale": "Unità amministrative", "Unità territoriale": "Comune"},
    {"Id report": 66, "Titolo report": "Regione - Dimensione", "Ambito territoriale": "Unità amministrative", "Unità territoriale": "Regione"},
    {"Id report": 112, "Titolo report": "Province-Uts soppresse o cedute a stato estero", "Ambito territoriale": "Unità amministrative", "Unità territoriale": "Provincia/Uts"},
]
_INDEX = {
    "74": ["POP_RES Popolazione residente", "AREA_KMQ Superficie territoriale (kmq)"],
    "66": ["POP_RES Popolazione residente"],
    "112": [],
}


def _ids(query, items=_ITEMS, index=_INDEX, limit=3):
    return [int(e["Id report"]) for e in _which_search(query, items, limit, index=index)]


def test_parole_vuote_ignorate():
    assert _ids("e dei per") == []


def test_colonne_trovano_il_report():
    assert _ids("superficie") == [74]


def test_titolo_pesa_piu_delle_colonne():
    assert _ids("regione popolazione")[0] == 66


def test_pareggio_preferisce_comune():
    assert _ids("popolazione") == [74, 66]


def test_sinonimo_cessate_soppresse():
    assert _ids("province cessate") == [112]


def test_forme_diverse_stessa_radice():
    assert _ids("comune") == _ids("comuni") == [74]


def test_senza_indice_cerca_solo_nei_titoli():
    assert _ids("superficie", index={}) == []


# ------------------------------------------------------------------ casi reali, offline

_CASI_REALI = [
    ("popolazione e superficie dei comuni", 74, 1),
    ("popolazione", 74, 3),
    ("superficie", 74, 3),
    ("province cessate", 112, 3),
    ("zona altimetrica", 73, 1),
    ("montagna", 75, 3),
    ("fusioni", 129, 3),
    ("comuni soppressi", 98, 3),
    ("aree interne", 75, 1),
    ("cambio denominazione", 104, 3),
    ("traslazione codici", 304, 3),
    ("codici istat dei comuni", 61, 3),
    ("nuts", 448, 3),
    ("regioni", 68, 3),
    ("residenti", 74, 3),
    # un caso per ogni sinonimo di _SINONIMI (senza sinonimi il report atteso non esce)
    ("comuni cessati", 98, 1),
    ("abitanti dei comuni", 74, 1),
    ("estensione dei comuni", 74, 1),
]


@pytest.mark.parametrize("query,atteso,entro", _CASI_REALI)
def test_casi_reali(query, atteso, entro):
    items = catalog._bundled()
    trovati = [int(e["Id report"]) for e in _which_search(query, items, entro)]
    assert atteso in trovati, f"{query!r}: atteso {atteso} nei primi {entro}, ottenuto {trovati}"


# ------------------------------------------------------------------ libreria allineata alla CLI


@pytest.fixture
def catalogo_incluso(monkeypatch):
    monkeypatch.setattr(catalog, "load_catalog", lambda **_: catalog._bundled())


def test_libreria_which(catalogo_incluso):
    import opensituas
    from opensituas import service

    df = opensituas.which("popolazione e superficie dei comuni")
    assert list(df.columns) == list(service.WHICH_COLUMNS)
    assert int(df.iloc[0]["pfun"]) == 74
    assert len(opensituas.which("popolazione", limit=1)) == 1
    assert len(opensituas.which()) == len(catalog._bundled())


def test_libreria_which_nessun_risultato(catalogo_incluso):
    import opensituas

    with pytest.raises(opensituas.SituasError):
        opensituas.which("xyz_inesistente_abc")


@pytest.mark.parametrize("args", [["province cessate"], ["popolazione", "--limit", "5"], []])
def test_cli_e_libreria_danno_lo_stesso_risultato(catalogo_incluso, args):
    import json

    from typer.testing import CliRunner

    import opensituas
    from opensituas.cli import app

    result = CliRunner().invoke(app, ["-o", "json", "which", *args])
    assert result.exit_code == 0, result.output
    query = args[0] if args else None
    limit = int(args[2]) if len(args) > 1 else 3
    assert json.loads(result.output) == opensituas.which(query, limit=limit).to_dict("records")
