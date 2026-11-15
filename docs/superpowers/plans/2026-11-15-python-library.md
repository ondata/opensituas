# Libreria Python opensituas — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> Le skill sono state installate da `obra/superpowers` v7.0.2. Esecuzione inline approvata tramite avanzamento del lavoro: non risultano definizioni di subagenti nei percorsi utente/progetto. Worktree isolato e ledger in `tmp/python-library/progress.md`; nessun commit automatico.

**Goal:** Esporre una libreria Python con DataFrame pandas, mantenendo invariati comandi e output della CLI.

**Architecture:** Estrarre le operazioni report in `service.py`, indipendente da pandas e Typer. La CLI consuma i risultati grezzi; `api.py` converte i risultati tabellari in DataFrame. Rinominare il catalogo interno per liberare il nome pubblico `catalog`.

**Tech Stack:** Python >=3.12, httpx, Typer, Rich, pandas >=2.0, pytest, Ruff, uv.

**Spec:** `docs/superpowers/specs/2026-11-15-python-library-design.md`

## Global Constraints

- pandas è una dipendenza ordinaria e i risultati tabellari sono DataFrame.
- Non cambiare il comportamento della CLI.
- Le date restano stringhe `DD/MM/YYYY`, con le regole esistenti.
- Conservare nomi e valori delle colonne del report, senza rinomine automatiche o traduzioni.
- Non convertire codici territoriali in numeri: stringhe come `058091` devono restare identiche.
- Nessuna conversione automatica delle date o dei valori testuali in numeri.
- Non riempire i valori mancanti con zero o stringhe vuote.
- Cache catalogo e fallback offline restano invariati.
- Gli import del package non devono generare richieste di rete, output o scritture di cache.
- Nessuna pubblicazione, push, tag, release o modifica dell'installazione globale in questa fase.
- Non modificare `.claude/`, già presente come directory non tracciata.
- Non aggiornare versioni né correggere discrepanze di versione preesistenti: fuori ambito.

---

## Mappa dei file

| File | Azione e responsabilità |
|---|---|
| `src/opensituas/catalog.py` → `src/opensituas/_catalog.py` | Rinomina; stesso codice cache, lookup e date |
| `src/opensituas/service.py` | Nuovo: catalogo proiettato, metadati, record report e conteggio grezzo |
| `src/opensituas/api.py` | Nuovo: funzioni pubbliche, DataFrame e conteggio intero |
| `src/opensituas/__init__.py` | Esportazioni pubbliche; preservare `app`, `main`, `__version__` |
| `src/opensituas/cli.py` | Delegare al servizio; nessuna modifica a formattazione e comandi agente |
| `tests/conftest.py` | Nuovo: fixture report e trasporto publish fittizio, attivato esplicitamente |
| `tests/test_service.py` | Nuovo: date, timeout, metadati e proiezione catalogo |
| `tests/test_api.py` | Nuovo: tipi pubblici, codici, mancanti, errori e territoriali |
| `tests/test_cli_regression.py` | Nuovo: contratti CLI e assenza di rete nei test |
| `tests/test_logic.py`, `tests/test_agent_which.py` | Aggiornare import al modulo interno; isolare il test which che oggi può accedere alla rete |
| `pyproject.toml`, `uv.lock` | pandas e descrizione CLI/libreria |
| `README.md`, `docs/architecture.md`, `LOG.md` | Installazione, esempi, architettura e cronologia |

`base.py`, `territorial.py` e `output.py` restano invariati, salvo un problema direttamente necessario a soddisfare la specifica: in quel caso fermarsi e motivare la modifica.

## Fase 1 — Servizio condiviso e regressioni CLI

### Task 1: Estrarre le operazioni report senza cambiare i risultati

**Files:** creare `service.py`, `tests/conftest.py`, `tests/test_service.py`; rinominare `catalog.py`; modificare gli import in `cli.py`, `test_logic.py` e `test_agent_which.py`.

**Interfaces:**
- Consumes: `_catalog.load_catalog(refresh=False)`, `filter_catalog`, `get_entry`, `apply_date`, `validity_end`; `base.publish_get(url, timeout=60.0)` e `base.rows(data)`.
- Produces: `service.catalog_records(keyword=None, *, ambito=None, unita=None, refresh=False) -> list[dict]`; `report_info(pfun, *, timeout=60.0) -> dict`; `report_records(pfun, *, date=None, date_from=None, date_to=None, timeout=60.0) -> list[dict]`; `count_records` con la stessa firma di `report_records`.

- [x] **Step 1: Registrare il baseline.** Leggere prima gli help degli strumenti da usare: `uv --help`, `git --help`, `rg --help`, poi gli help dei sottocomandi necessari. Eseguire `git status --short`, `uv run pytest tests/ -q`, `uv run ruff check src/ tests/`. Separare gli eventuali problemi preesistenti dai problemi introdotti. Non modificare il codice prima di aver annotato il risultato nel piano.

- [x] **Step 2: Scrivere fixture e test del servizio.** Creare `tests/conftest.py`:

```python
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
        state["calls"].append((urlsplit(url).path, parse_qs(urlsplit(url).query), timeout))
        if urlsplit(url).path.endswith("reportspooljsoncount"):
            return {"resultset": state["count"]}
        if urlsplit(url).path.endswith("/info"):
            return {
                "REPORT NAME": "Comuni - Elenco",
                "REPORT DESCRIZIONE": "Elenco comuni",
                "COL_DETAILS": [{"COLNAME": "PRO_COM_T", "LABEL": "Codice", "TYPE": "VARCHAR2", "GUIDA": "Codice ISTAT"}],
            }
        return {"resultset": state["rows"]}

    def no_gateway(*args, **kwargs):
        raise AssertionError("Rete non prevista dal test")

    monkeypatch.setattr(_catalog, "load_catalog", load)
    monkeypatch.setattr(base, "publish_get", publish)
    monkeypatch.setattr(base, "gateway", no_gateway)
    return state
```

Creare `tests/test_service.py`:

```python
import pytest
from opensituas import base, service


@pytest.mark.parametrize("fn", [service.report_records, service.count_records, service.report_info])
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
        entry[key] = entry[key].replace("pdata=01/01/1948", "pdatada=17/03/1861&pdataa=31/05/2026")
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
    rows = service.catalog_records("comuni", ambito="amministrative", unita="comune", refresh=True)
    assert rows[0]["pfun"] == "61"
    assert list(rows[0]) == list(service.CATALOG_COLUMNS)
    assert report_backend["refresh"] is True
    assert service.catalog_records("inesistente") == []


def test_raw_results_and_metadata(report_backend):
    assert service.report_records(61) == report_backend["rows"]
    assert service.count_records(61) == [{"NUM_ROWS": "2"}]
    assert service.report_info(61) == {
        "pfun": 61,
        "report": "Comuni - Elenco",
        "descrizione": "Elenco comuni",
        "colonne": [{"colonna": "PRO_COM_T", "label": "Codice", "tipo": "VARCHAR2", "guida": "Codice ISTAT"}],
    }
```

- [x] **Step 3: Eseguire `uv run pytest tests/test_service.py -q`.** Atteso: errore di import, perché il servizio ancora non esiste. Non correggere i test per aggirare il fallimento.

- [x] **Step 4: Rinominare il modulo interno.** Usare `git mv src/opensituas/catalog.py src/opensituas/_catalog.py`. Con `rg 'opensituas\.catalog|from \. import|from opensituas import' src tests` individuare e aggiornare gli import reali: in CLI usare `from . import _catalog as catalog`; nei test `from opensituas import _catalog as catalog` e `_catalog as cat_module`. Nessuno shim `catalog.py`: reintrodurrebbe la collisione.

- [x] **Step 5: Implementare `service.py`.** Aggiungere docstring di modulo e usare questo nucleo; niente import di `api`, pandas, output o CLI:

```python
from . import _catalog, base

CATALOG_COLUMNS = ("pfun", "titolo", "validità", "analisi", "ambito", "unità", "parametri")


def catalog_records(keyword: str | None = None, *, ambito: str | None = None,
                    unita: str | None = None, refresh: bool = False) -> list[dict]:
    entries = _catalog.filter_catalog(
        _catalog.load_catalog(refresh=refresh), keyword=keyword, ambito=ambito, unita=unita,
    )
    fields = ("Id report", "Titolo report", "Inizio/fine validità report", "Analisi temporale",
              "Ambito territoriale", "Unità territoriale", "parametri necessari")
    return [dict(zip(CATALOG_COLUMNS, (entry.get(field) for field in fields))) for entry in entries]


def report_info(pfun: int | str, *, timeout: float = base.DEFAULT_TIMEOUT) -> dict:
    entry = _catalog.get_entry(pfun)
    link = _catalog.apply_date(entry["INFO_LINK"], default_date=_catalog.validity_end(entry))
    data = base.publish_get(link, timeout=timeout)
    return {
        "pfun": pfun,
        "report": data.get("REPORT NAME"),
        "descrizione": data.get("REPORT DESCRIZIONE"),
        "colonne": [
            {"colonna": col.get("COLNAME"), "label": col.get("LABEL"),
             "tipo": col.get("TYPE"), "guida": col.get("GUIDA")}
            for col in data.get("COL_DETAILS", [])
        ],
    }


def _report_rows(pfun: int | str, link_key: str, *, date: str | None,
                 date_from: str | None, date_to: str | None, timeout: float) -> list[dict]:
    entry = _catalog.get_entry(pfun)
    link = _catalog.apply_date(entry[link_key], date, date_from, date_to,
                               default_date=_catalog.validity_end(entry))
    return base.rows(base.publish_get(link, timeout=timeout))


def report_records(pfun: int | str, *, date: str | None = None,
                   date_from: str | None = None, date_to: str | None = None,
                   timeout: float = base.DEFAULT_TIMEOUT) -> list[dict]:
    return _report_rows(pfun, "SPOOL_LINK", date=date, date_from=date_from,
                        date_to=date_to, timeout=timeout)


def count_records(pfun: int | str, *, date: str | None = None,
                  date_from: str | None = None, date_to: str | None = None,
                  timeout: float = base.DEFAULT_TIMEOUT) -> list[dict]:
    return _report_rows(pfun, "COUNT_LINK", date=date, date_from=date_from,
                        date_to=date_to, timeout=timeout)
```

- [x] **Step 6: Verificare il task.** Eseguire `uv run pytest tests/test_service.py tests/test_logic.py -q` e `uv run ruff check src/ tests/`. Atteso: servizio e test logici verdi, senza mutare cache o HTTP. Annotare esito e segnare il task completato.

### Task 2: Collegare la CLI al servizio con test di caratterizzazione

**Files:** modificare `src/opensituas/cli.py`, `tests/test_agent_which.py`; creare `tests/test_cli_regression.py`.

**Interfaces:**
- Consumes: le quattro funzioni del servizio del task 1 e `_catalog` per `which`.
- Produces: stessi comandi, opzioni, ordine delle colonne, JSON, CSV, file ed exit code; `count` resta una lista di record, `storia` resta un oggetto con `unita` e `storia`.

- [x] **Step 1: Scrivere i test CLI prima di cambiare i corpi dei comandi.** Creare il file seguente. Questi sono test di caratterizzazione: devono essere verdi già sulla vecchia CLI.

```python
import csv
import io
import json

from typer.testing import CliRunner
from opensituas import base, service, territorial
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
    assert json.loads(result.stdout) == service.catalog_records("comuni")


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
    payload = {"unita": {"code": "058091", "name": "Roma"}, "storia": [{"data evento": "01/01/2000"}]}
    monkeypatch.setattr(territorial, "storia", lambda *a, **k: payload)
    monkeypatch.setattr(territorial, "cerca_codice", lambda *a, **k: [{"codice": "058091"}])
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
```

- [x] **Step 2: Rendere offline `test_which_cmd_no_match_exit2`.** Aggiungere il parametro `monkeypatch` e, prima di `runner.invoke`, applicare:

```python
from opensituas import _catalog
monkeypatch.setattr(_catalog, "load_catalog", lambda **_: _CATALOG_SAMPLE)
```

Il test `test_which_cmd_no_args_returns_all` usa ora `_catalog as cat_module`, come stabilito nel task 1. Non modificare l'algoritmo `which`.

- [x] **Step 3: Eseguire `uv run pytest tests/test_cli_regression.py tests/test_agent_which.py -q`.** Atteso: verde sul comportamento attuale. Salvare questo checkpoint prima di sostituire i corpi `go`.

- [x] **Step 4: Delegare i quattro comandi.** Importare `service` accanto agli import interni. Conservare le firme Typer e tutta la parte output. Nei rispettivi `go` usare:

```python
# catalog_cmd.go
return service.catalog_records(keyword, ambito=ambito, unita=unita, refresh=refresh)

# info_cmd.go
return service.report_info(pfun, timeout=_timeout())

# get_cmd.go
return service.report_records(pfun, date=date, date_from=date_from,
                              date_to=date_to, timeout=_timeout())

# count_cmd.go
return service.count_records(pfun, date=date, date_from=date_from,
                             date_to=date_to, timeout=_timeout())
```

Non delegare ai futuri DataFrame di `api.py`. Non cambiare `output.py`, l'alias `list`, `_run`, `_timeout`, i comandi territoriali o gli agent command.

- [x] **Step 5: Ripetere i test.** `uv run pytest tests/ -q` e `uv run ruff check src/ tests/`. L'estrazione è conclusa solo con le stesse asserzioni di caratterizzazione verdi.

## Fase 2 — API pubblica pandas

### Task 3: Aggiungere DataFrame, conteggio intero ed esportazioni pubbliche

**Files:** creare `src/opensituas/api.py`, `tests/test_api.py`; modificare `src/opensituas/__init__.py`, `pyproject.toml`, `uv.lock`.

**Interfaces:**
- Consumes: servizio del task 1; `territorial.storia(tipo, query, dettaglio=False) -> dict` e `territorial.cerca_codice(tipo, query, limit=20) -> list[dict]`.
- Produces: `catalog`, `get`, `storia`, `cerca_codice` → `pd.DataFrame`; `info` → `dict`; `count` → `int`; `SituasError`, `app` e `main` disponibili dal package.

- [x] **Step 1: Scrivere `tests/test_api.py`.** Il trasporto report è quello della fixture; per i territoriali sostituire il gateway e mantenere la logica reale di selezione, ordinamento e dettagli.

```python
import pandas as pd
import pytest

import opensituas as situas
from opensituas import base, service


def test_public_names():
    for name in ("catalog", "info", "get", "count", "storia", "cerca_codice", "app", "main"):
        assert callable(getattr(situas, name))
    assert situas.SituasError is base.SituasError


def test_catalog_and_info(report_backend):
    frame = situas.catalog("comuni", ambito="amministrative", unita="comune", refresh=True)
    assert isinstance(frame, pd.DataFrame)
    assert list(frame.columns) == list(service.CATALOG_COLUMNS)
    assert frame.iloc[0]["pfun"] == "61"
    assert report_backend["refresh"] is True
    assert isinstance(situas.info(61), dict)
    assert situas.info(61)["colonne"][0]["colonna"] == "PRO_COM_T"
    report_backend["catalog"] = []
    empty = situas.catalog()
    assert empty.empty
    assert list(empty.columns) == list(service.CATALOG_COLUMNS)


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
    assert all(path.endswith("reportspooljsoncount") for path, _, _ in report_backend["calls"])


@pytest.mark.parametrize("rows", [[], [{}], [{"NUM_ROWS": None}], [{"NUM_ROWS": True}],
                                  [{"NUM_ROWS": 1.5}], [{"NUM_ROWS": -1}],
                                  [{"NUM_ROWS": "abc"}], [{"NUM_ROWS": "1.5"}],
                                  [{"NUM_ROWS": 1}, {"NUM_ROWS": 2}]])
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
        return {"items": [
            {"data evento": "01/01/2020", "id_comune_origine": 1},
            {"data evento": "01/01/2000", "id_comune_origine": 1},
        ]}
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
            return {"resultset": [
                {"V": "058091 - Roma", "RC": 1},
                {"V": "000001 - Roma", "RC": 2},
            ]}
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
```

- [x] **Step 2: Eseguire `uv run pytest tests/test_api.py -q`.** Atteso: errore per pandas assente o funzioni pubbliche mancanti. Annotare il motivo effettivo.

- [x] **Step 3: Aggiungere pandas.** Inserire `"pandas>=2.0"` nelle dipendenze di `pyproject.toml`; cambiare la descrizione in `"CLI e libreria Python per il SITUAS (Sistema Informativo Territoriale delle Unità Amministrative e Statistiche, ISTAT)"`. Eseguire `uv lock` e controllare che le altre dipendenze non subiscano aggiornamenti estranei. Non usare `uv tool install`.

- [x] **Step 4: Implementare `api.py`.** Aggiungere docstring di modulo e una docstring per ciascuna funzione che descriva risultato, date, errori e i limiti pertinenti. Implementazione minima:

```python
import re

import pandas as pd

from . import base, service, territorial


def catalog(keyword: str | None = None, *, ambito: str | None = None,
            unita: str | None = None, refresh: bool = False) -> pd.DataFrame:
    records = service.catalog_records(keyword, ambito=ambito, unita=unita, refresh=refresh)
    return pd.DataFrame(records, columns=service.CATALOG_COLUMNS)


def info(pfun: int | str, *, timeout: float = base.DEFAULT_TIMEOUT) -> dict:
    return service.report_info(pfun, timeout=timeout)


def get(pfun: int | str, *, date: str | None = None,
        date_from: str | None = None, date_to: str | None = None,
        timeout: float = base.DEFAULT_TIMEOUT) -> pd.DataFrame:
    return pd.DataFrame(service.report_records(
        pfun, date=date, date_from=date_from, date_to=date_to, timeout=timeout,
    ))


def count(pfun: int | str, *, date: str | None = None,
          date_from: str | None = None, date_to: str | None = None,
          timeout: float = base.DEFAULT_TIMEOUT) -> int:
    records = service.count_records(
        pfun, date=date, date_from=date_from, date_to=date_to, timeout=timeout,
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
    result = territorial.storia(tipo, query, dettaglio=dettaglio)
    frame = pd.DataFrame(result["storia"])
    frame.attrs["unita"] = result["unita"]
    return frame


def cerca_codice(tipo: str, query: str, *, limit: int = 20) -> pd.DataFrame:
    return pd.DataFrame(territorial.cerca_codice(tipo, query, limit=limit))
```

Non usare `astype(int)`, `to_numeric`, `to_datetime`, `fillna`, `json_normalize` né `explode`. Per `count`, la validazione più restrittiva è solo Python: la CLI conserva `count_records` senza conversioni.

- [x] **Step 5: Aggiornare `__init__.py`.** Conservare la versione attuale senza correggerla in questo task; aggiornare docstring e aggiungere:

```python
from .api import catalog, cerca_codice, count, get, info, storia
from .base import SituasError
from .cli import app, main

__all__ = ["catalog", "info", "get", "count", "storia", "cerca_codice",
           "SituasError", "app", "main"]
```

Tutti gli import interni del catalogo devono ormai passare da `_catalog`, senza importare la funzione pubblica per errore. `service` e `api` non importano il package pubblico.

- [x] **Step 6: Eseguire l'intera verifica funzionale.** `uv run pytest tests/ -q`; `uv run ruff check src/ tests/`. Confermare che l'API ritorni DataFrame e la CLI ancora record grezzi con la stessa suite del task 2.

## Fase 3 — Import, distribuzione e documentazione

### Task 4: Verificare import senza effetti collaterali e wheel

**Files:** estendere `tests/test_api.py`; artefatti temporanei solo in `tmp/python-library/`.

**Interfaces:**
- Consumes: le esportazioni del task 3 e l'entry point `opensituas = "opensituas:main"` già esistente.
- Produces: test ripetibile su processo pulito e wheel verificata con pandas dichiarato.

- [x] **Step 1: Aggiungere il test d'import in un processo nuovo.** Non usare solo `reload`: il package potrebbe essere già caricato dalla raccolta pytest.

```python
def test_import_has_no_network_output_or_cache_writes(tmp_path):
    import os
    import subprocess
    import sys

    script = '''
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
'''
    env = dict(os.environ, HOME=str(tmp_path), XDG_CACHE_HOME=str(tmp_path / ".cache"),
               PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run([sys.executable, "-c", script], env=env,
                            text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
    assert not (tmp_path / ".cache" / "opensituas").exists()
```

- [x] **Step 2: Eseguire `uv run pytest tests/test_api.py::test_import_has_no_network_output_or_cache_writes -q`.** Se fallisce per effetto collaterale nuovo, rimuovere quell'effetto dal percorso d'import invece di allentare l'asserzione. Poi eseguire l'intera suite.

- [x] **Step 3: Costruire la wheel in directory temporanea.** Leggere `uv build --help`, `uv venv --help`, `uv pip install --help`. Eseguire `uv build --out-dir tmp/python-library/dist` e `uv venv tmp/python-library/venv`. Installare con `uv pip install --python tmp/python-library/venv/bin/python tmp/python-library/dist/opensituas-0.1.2-py3-none-any.whl`. La versione del progetto non cambia; se il file prodotto ha un nome differente, usare il nome effettivamente prodotto, non creare duplicati.

- [x] **Step 4: Verificare il pacchetto installato.** Eseguire con l'interprete del venv temporaneo:

```python
from importlib.metadata import requires

import opensituas
from opensituas import _catalog

assert callable(opensituas.catalog)
assert callable(opensituas.get)
assert len(_catalog._bundled()) >= 70
assert any(req.lower().startswith("pandas") for req in requires("opensituas"))
```

Eseguire anche `tmp/python-library/venv/bin/opensituas --help`. Nessuna richiesta a SITUAS è necessaria. Installazione/build possono richiedere il registry per dipendenze: se la rete non è disponibile, documentare la verifica bloccata senza dichiararla riuscita. Non reinstallare la CLI globale e non pubblicare gli artefatti.

### Task 5: Documentare l'uso per operatori e chiudere la review

**Files:** `README.md`, `docs/architecture.md`, `LOG.md`, questa checklist e la specifica.

**Interfaces:**
- Consumes: funzioni e limiti verificati nei task 1–4.
- Produces: istruzioni distinguibili per terminale e Python, esempio riproducibile di join, review con risultati reali.

- [x] **Step 1: Aggiungere al README la sezione libreria.** Conservare il materiale CLI esistente. Specificare installazione con `uv add opensituas` e un blocco Python:

```python
import opensituas

report = opensituas.catalog("comuni")
print(report[["pfun", "titolo"]].head())

comuni = opensituas.get(61)
comuni_2020 = opensituas.get(61, date="01/01/2020")
print(opensituas.count(61))
print(opensituas.info(61)["colonne"])

storia = opensituas.storia("comune", "Roma")
print(storia.attrs["unita"])
print(opensituas.cerca_codice("comune", "Roma"))

roma = comuni.loc[comuni["PRO_COM_T"] == "058091"]
roma.to_csv("roma.csv", index=False)
```

`PRO_COM_T` è documentato nel README attuale e presente nelle fixture; non usare `DEN_REG` o altri campi mai verificati. Spiegare che gli esempi chiamano i servizi ISTAT e che i dati storici non descrivono necessariamente la composizione corrente.

- [x] **Step 2: Aggiungere un join minimale e documentare i limiti.** Usare solo dati di esempio esplicitamente etichettati, senza presentarli come statistiche ufficiali:

```python
import pandas as pd

# Dati dimostrativi locali, non statistiche ISTAT.
misure = pd.DataFrame({"PRO_COM_T": ["058091"], "valore_demo": [10]})
arricchiti = misure.merge(comuni, on="PRO_COM_T", how="left", validate="many_to_one")
```

Spiegare che i codici sono stringhe; anche i file esterni vanno letti con `dtype={"PRO_COM_T": str}`. Illustrare `SituasError` con `try/except`, DataFrame vuoti, `info` come dizionario, `count` come intero, `date_from`/`date_to` per report PERIODO, timeout publish, `attrs` non garantiti dopo export, dettagli non disponibili come liste vuote e marker `_ambiguo` di `cerca_codice`.

- [x] **Step 3: Aggiornare la mappa architetturale.** In `docs/architecture.md` sostituire il riferimento a `catalog.py` con `_catalog.py`, aggiungere `service.py` e `api.py`, e chiarire che la logica condivisa non dipende da Typer/pandas. Descrivere i due percorsi: CLI → servizio → record → output; Python → servizio → record → DataFrame.

- [x] **Step 4: Eseguire la verifica finale.** `uv run pytest tests/ -q`, `uv run ruff check src/ tests/`, `git diff --check`, `git status --short`. Ispezionare il diff dei soli file del piano e verificare che `.claude/` e altri file estranei siano rimasti invariati. Nei documenti usare una riga vuota prima di ogni blocco di codice.

- [x] **Step 5: Aggiornare stato e review.** In `LOG.md` annotare API aggiunte e risultati effettivi di test/lint/build; nella specifica e nel piano spuntare solo le verifiche eseguite. Non eseguire commit, tag o push senza richiesta esplicita. I confini dei task sono checkpoint utili per eventuali commit successivi, non autorizzazioni a pubblicare.

## Review del piano

- [x] Copertura specifica: catalogo e date nel task 1; CLI nel task 2; DataFrame, null, codici, conteggi e territoriali nel task 3; import e wheel nel task 4; esempi e limiti nel task 5.
- [x] Collisione `catalog` risolta con rinomina interna e aggiornamento dei test esistenti.
- [x] Firme condivise coerenti tra servizio, API e chiamate CLI.
- [x] Nessuna conversione pandas nel percorso CLI.
- [x] Nessuna dipendenza opzionale, client aggiuntivo o nuova configurazione globale.
- [x] Esclusi pubblicazione, aggiornamento versione e installazione globale.
- [x] Approvazione del piano prima di iniziare l'implementazione.

## Questioni aperte

Nessuna domanda funzionale. Piano eseguito nel worktree isolato con test a ogni checkpoint; integrazione su main e pubblicazione da decidere separatamente.

## Review finale

- Suite: 62 test passati (baseline 29), senza rete SITUAS; Ruff e `git diff --check` puliti.
- Wheel e sdist costruiti; installazione wheel e comando `--help` verificati in venv dedicato con pandas e snapshot incluso.
- Review: self-review, nessun subagente configurato; non equivale a revisione indipendente.
- Aspettative dei test catalogo rese letterali per evitare confronti con il servizio stesso. Nessun problema critico/importante residuo individuato.
- Nessuna chiamata live SITUAS né matrice completa di versioni Python/pandas eseguita; verifiche locali su Python 3.14.0 e pandas 3.1.1.
- Moduli HTTP, territoriali e output invariati; nessun commit, merge, push, pubblicazione o modifica dell'installazione globale.
