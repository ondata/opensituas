"""Test per agent-context e which (logica pura, senza rete)."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from opensituas.cli import _AGENT_CONTEXT, _comando_suggerito, _which_search, app

runner = CliRunner()

# --------------------------------------------------------------------- agent-context


def test_agent_context_valid_json():
    result = runner.invoke(app, ["agent-context"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "schema_version" in data
    assert data["schema_version"] != ""


def test_agent_context_has_commands():
    data = _AGENT_CONTEXT
    names = [c["name"] for c in data["commands"]]
    for expected in ["catalog", "info", "get", "count", "storia", "cerca-codice", "agent-context", "which"]:
        assert expected in names, f"comando '{expected}' mancante in _AGENT_CONTEXT"


def test_agent_context_exit_codes_present():
    commands_with_exit2 = [c for c in _AGENT_CONTEXT["commands"] if "2" in c.get("exit_codes", {})]
    assert len(commands_with_exit2) >= 1


# ----------------------------------------------------------------------------- which


_CATALOG_SAMPLE = [
    {
        "Id report": "61",
        "Titolo report": "Comuni - Elenco",
        "Ambito territoriale": "Unità amministrative",
        "Unità territoriale": "Comune",
        "Analisi temporale": "DATA",
        "Inizio/fine validità report": "01/01/1948 - 31/05/2026",
        "parametri necessari": "pdata",
    },
    {
        "Id report": "50",
        "Titolo report": "Comuni - Variazioni",
        "Ambito territoriale": "Unità amministrative",
        "Unità territoriale": "Comune",
        "Analisi temporale": "PERIODO",
        "Inizio/fine validità report": "17/03/1861 - 31/05/2026",
        "parametri necessari": "pfun, pdatada, pdataa",
    },
    {
        "Id report": "112",
        "Titolo report": "Province - Elenco",
        "Ambito territoriale": "Unità amministrative",
        "Unità territoriale": "Provincia/UTS",
        "Analisi temporale": "DATA",
        "Inizio/fine validità report": "01/01/1948 - 31/05/2026",
        "parametri necessari": "pdata",
    },
]


def test_which_search_match():
    results = _which_search("comuni", _CATALOG_SAMPLE, limit=3)
    assert len(results) >= 1
    assert all("Comune" in r.get("Unità territoriale", "") or "Comuni" in r.get("Titolo report", "") for r in results)


def test_which_search_no_match():
    results = _which_search("xyz_inesistente_abc", _CATALOG_SAMPLE, limit=3)
    assert results == []


def test_which_search_limit():
    results = _which_search("comuni", _CATALOG_SAMPLE, limit=1)
    assert len(results) <= 1


def test_which_search_all_catalog():
    results = _which_search("", _CATALOG_SAMPLE, limit=100)
    assert results == []  # query vuota: nessun token → nessun match


def test_comando_suggerito_data():
    entry = _CATALOG_SAMPLE[0]  # DATA
    cmd = _comando_suggerito(entry)
    assert "--date" in cmd
    assert "61" in cmd
    assert "--from" not in cmd


def test_comando_suggerito_periodo():
    entry = _CATALOG_SAMPLE[1]  # PERIODO
    cmd = _comando_suggerito(entry)
    assert "--from" in cmd
    assert "--to" in cmd
    assert "--date" not in cmd


def test_which_cmd_no_match_exit2():
    result = runner.invoke(app, ["which", "xyz_inesistente_abc"])
    assert result.exit_code == 2


def test_which_cmd_no_args_returns_all(monkeypatch):
    from opensituas import catalog as cat_module
    monkeypatch.setattr(cat_module, "load_catalog", lambda **_: _CATALOG_SAMPLE)
    result = runner.invoke(app, ["-o", "json", "which"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == len(_CATALOG_SAMPLE)
