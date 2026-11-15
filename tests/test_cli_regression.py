import csv
import io
import json

from typer.testing import CliRunner
from opensituas import base, territorial
from opensituas.cli import app

runner = CliRunner()


def test_json_envelopes(report_backend):
    for command, expected in (
        (["get", "61"], report_backend["rows"]),
        (["count", "61"], [{"NUM_ROWS": "2"}]),
    ):
        result = runner.invoke(app, ["-o", "json", *command])
        assert result.exit_code == 0, result.output
        assert json.loads(result.stdout) == expected
    result = runner.invoke(app, ["-o", "json", "info", "61"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["colonne"][0]["colonna"] == "PRO_COM_T"
    result = runner.invoke(app, ["-o", "json", "catalog", "comuni"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == [
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


def test_csv_and_file(report_backend, tmp_path):
    result = runner.invoke(app, ["-o", "csv", "get", "61"])
    assert result.exit_code == 0
    records = list(csv.DictReader(io.StringIO(result.stdout)))
    assert records[0]["PRO_COM_T"] == "058091"
    assert records[1]["AREA_KMQ"] == ""
    for mode in ("csv", "json"):
        path = tmp_path / "exports" / f"comuni.{mode}"
        result = runner.invoke(app, ["-o", mode, "get", "61", "--out", str(path)])
        assert result.exit_code == 0
        assert result.stdout == ""
        if mode == "json":
            assert json.loads(path.read_text()) == report_backend["rows"]
        else:
            assert list(csv.DictReader(io.StringIO(path.read_text()))) == records


def test_storia_and_code_envelopes(monkeypatch):
    payload = {
        "unita": {"code": "058091", "name": "Roma"},
        "storia": [{"data evento": "01/01/2000"}],
    }
    monkeypatch.setattr(territorial, "storia", lambda *a, **k: payload)
    monkeypatch.setattr(
        territorial, "cerca_codice", lambda *a, **k: [{"codice": "058091"}]
    )
    result = runner.invoke(app, ["-o", "json", "storia", "comune", "Roma"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == payload
    result = runner.invoke(app, ["-o", "json", "cerca-codice", "comune", "Roma"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == [{"codice": "058091"}]


def test_cli_timeout_and_error(report_backend, monkeypatch):
    monkeypatch.setenv("OPENSITUAS_TIMEOUT", "9")
    result = runner.invoke(app, ["-o", "json", "get", "61", "--date", "01/01/2020"])
    assert result.exit_code == 0
    assert report_backend["calls"][-1][2] == 9.0
    assert report_backend["calls"][-1][1]["pdata"] == ["01/01/2020"]

    def fail(*args, **kwargs):
        raise base.SituasError("errore di prova")

    monkeypatch.setattr(base, "publish_get", fail)
    result = runner.invoke(app, ["-o", "json", "get", "61"])
    assert result.exit_code == 2
    assert result.stdout == ""
    assert "errore di prova" in result.stderr
