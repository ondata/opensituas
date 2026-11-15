"""Lo script dell'indice `which` non deve riscriverlo se il catalogo online non è disponibile."""

import importlib.util
from pathlib import Path

import pytest

from opensituas import base

_SCRIPT = Path(__file__).parents[1] / "scripts" / "build_which_index.py"


@pytest.fixture
def script(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("build_which_index", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = tmp_path / "which_index.json"
    out.write_text("indice precedente", encoding="utf-8")
    monkeypatch.setattr(mod, "OUT", out)
    monkeypatch.setattr(mod.service, "report_info", lambda pfun, **_: {"colonne": [{"colonna": "X", "label": "x"}]})
    return mod, out


def test_gateway_non_raggiungibile_non_riscrive(script, monkeypatch):
    mod, out = script

    def giu(_service):
        raise base.SituasError("gateway non raggiungibile")

    monkeypatch.setattr(mod.base, "gateway", giu)
    assert mod.main() == 1
    assert out.read_text(encoding="utf-8") == "indice precedente"


def test_catalogo_vuoto_non_riscrive(script, monkeypatch):
    mod, out = script
    monkeypatch.setattr(mod.base, "gateway", lambda _service: {"items": []})
    assert mod.main() == 1
    assert out.read_text(encoding="utf-8") == "indice precedente"


def test_catalogo_online_scrive_indice(script, monkeypatch):
    mod, out = script
    monkeypatch.setattr(mod.base, "gateway", lambda _service: {"items": [{"Id report": 74}]})
    assert mod.main() == 0
    assert '"74"' in out.read_text(encoding="utf-8")


def test_report_nuovo_assente_dalla_cache(tmp_path, monkeypatch):
    """Cache valida ma vecchia: il report nuovo c'è online e deve finire nell'indice."""
    spec = importlib.util.spec_from_file_location("build_which_index", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = tmp_path / "which_index.json"
    monkeypatch.setattr(mod, "OUT", out)
    nuovo = {
        "Id report": 999,
        "INFO_LINK": "https://example.invalid/info?pfun=999&pdata=01/01/2020",
        "Inizio/fine validità report": "01/01/2020 - 31/12/2026",
        "Analisi temporale": "DATA",
    }
    monkeypatch.setattr(mod.base, "gateway", lambda _service: {"items": [nuovo]})
    monkeypatch.setattr(mod.catalog, "load_catalog", lambda **_: [])  # cache senza il report nuovo
    monkeypatch.setattr(
        base, "publish_get", lambda link, timeout=None: {"COL_DETAILS": [{"COLNAME": "POP_RES", "LABEL": "Popolazione"}]}
    )
    assert mod.main() == 0
    assert "POP_RES Popolazione" in out.read_text(encoding="utf-8")
