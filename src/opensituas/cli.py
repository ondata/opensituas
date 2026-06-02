"""CLI opensituas — interfaccia per le API SITUAS, orchestrabile da agenti AI.

Variabili d'ambiente:
  OPENSITUAS_TIMEOUT   timeout richieste in secondi (default 60)

Flag globale --output table|json|csv. In modalità json/csv l'output è pulito su stdout.
"""

from __future__ import annotations

import json
import os
from enum import Enum
from pathlib import Path
from typing import Optional

import typer

from . import base, catalog, output, territorial


class OutputFormat(str, Enum):
    table = "table"
    json = "json"
    csv = "csv"


_EPILOG = """\
**Per agenti:** usa `-o json` e fai il parsing con `jq`. Exit code `2` = errore API
(messaggio su stderr); `0` = ok. **Workflow:** catalog (trova pfun + validità) → info
(colonne) → get/count. Per l'auto-orientamento: `agent-context` (schema JSON della CLI)
e `which <query>` (discovery report da linguaggio naturale).

**Esempi:**

* `opensituas -o json catalog comuni | jq '.[].pfun'`

* `opensituas -o json info 50`

* `opensituas -o json get 50 --date 12/01/1927`

* `opensituas -o json storia comune Roma`

* `opensituas which "comuni per anno"`
"""

_AGENT_CONTEXT = {
    "schema_version": "1",
    "cli": {
        "name": "opensituas",
        "description": "CLI per il SITUAS (ISTAT). Catalogo report + query territoriali.",
    },
    "commands": [
        {
            "name": "catalog",
            "short": "Elenca i report del catalogo SITUAS (pfun, titolo, validità, analisi).",
            "flags": [
                {"name": "--ambito", "type": "string", "usage": "Filtra per ambito territoriale"},
                {"name": "--unita", "type": "string", "usage": "Filtra per unità territoriale"},
                {"name": "--refresh", "type": "bool", "usage": "Rilegge il catalogo dal gateway"},
            ],
            "exit_codes": {"0": "ok", "2": "errore API"},
        },
        {
            "name": "info",
            "short": "Metadati di un report: descrizione e dettaglio delle colonne.",
            "flags": [],
            "exit_codes": {"0": "ok", "2": "errore API o pfun non trovato"},
        },
        {
            "name": "get",
            "short": "Scarica i dati di un report. Default report DATA: dato più recente (fine validità).",
            "flags": [
                {"name": "--date", "type": "string", "usage": "Data DD/MM/YYYY (report DATA)"},
                {"name": "--from", "type": "string", "usage": "Data inizio DD/MM/YYYY (report PERIODO)"},
                {"name": "--to", "type": "string", "usage": "Data fine DD/MM/YYYY (report PERIODO)"},
                {"name": "--out", "type": "path", "usage": "Salva su file (formato secondo --output)"},
            ],
            "exit_codes": {"0": "ok", "2": "errore API, pfun non trovato o data fuori validità"},
        },
        {
            "name": "count",
            "short": "Numero di righe di un report senza scaricarle.",
            "flags": [
                {"name": "--date", "type": "string", "usage": "Data DD/MM/YYYY (report DATA)"},
                {"name": "--from", "type": "string", "usage": "Data inizio DD/MM/YYYY (report PERIODO)"},
                {"name": "--to", "type": "string", "usage": "Data fine DD/MM/YYYY (report PERIODO)"},
            ],
            "exit_codes": {"0": "ok", "2": "errore API o data fuori validità"},
        },
        {
            "name": "storia",
            "short": "Storia delle variazioni di un'unità territoriale (comune/provincia/regione).",
            "flags": [
                {"name": "--dettaglio", "type": "bool", "usage": "Aggiunge provvedimento e unità coinvolte"},
            ],
            "exit_codes": {"0": "ok", "2": "unità non trovata o ambigua"},
        },
        {
            "name": "cerca-codice",
            "short": "Ricerca codice Istat: codici, denominazioni e periodi di validità.",
            "flags": [
                {"name": "--limit", "type": "int", "usage": "Max corrispondenze da dettagliare (default 20)"},
            ],
            "exit_codes": {"0": "ok", "2": "errore API"},
        },
        {
            "name": "which",
            "short": "Discovery semantica: trova report SITUAS da una query in linguaggio naturale.",
            "flags": [
                {"name": "--limit", "type": "int", "usage": "Max risultati (default 3)"},
            ],
            "exit_codes": {"0": "almeno un match trovato", "2": "nessun report corrisponde alla query"},
        },
        {
            "name": "agent-context",
            "short": "Emette questo JSON versionato per l'auto-orientamento degli agenti AI.",
            "flags": [],
            "exit_codes": {"0": "ok"},
        },
    ],
}

app = typer.Typer(
    help="opensituas — CLI per il SITUAS (ISTAT). Catalogo report + query territoriali.",
    epilog=_EPILOG,
    rich_markup_mode="markdown",
    no_args_is_help=True,
    add_completion=False,
)


def _timeout() -> float:
    return float(os.environ.get("OPENSITUAS_TIMEOUT", base.DEFAULT_TIMEOUT))


@app.callback()
def _main(
    output_mode: OutputFormat = typer.Option(
        OutputFormat.table, "--output", "-o", help="Formato output (table per umani, json/csv per agenti)"
    ),
) -> None:
    output.set_mode(output_mode.value)


def _run(fn):
    """Esegue una funzione gestendo gli errori applicativi SITUAS."""
    try:
        return fn()
    except base.SituasError as exc:
        output.err_console.print(f"[red]Errore:[/red] {exc}")
        raise typer.Exit(2)


# --------------------------------------------------------------------------- catalogo


@app.command(
    "catalog",
    epilog=(
        "**Esempi:**\n\n"
        "* `opensituas -o json catalog comuni`\n\n"
        "* `opensituas catalog --ambito 'Unità statistiche'`\n\n"
        "* `opensituas -o json catalog | jq '.[] | select(.analisi==\"PERIODO\") | .pfun'`"
    ),
)
def catalog_cmd(
    keyword: Optional[str] = typer.Argument(None, help="Filtro sul titolo del report"),
    ambito: Optional[str] = typer.Option(None, "--ambito", "-a", help="Filtra per ambito territoriale"),
    unita: Optional[str] = typer.Option(None, "--unita", "-u", help="Filtra per unità territoriale"),
    refresh: bool = typer.Option(False, "--refresh", help="Rilegge il catalogo dal gateway"),
) -> None:
    """Elenca i report del catalogo (74 microservizi). Mostra anche il periodo di validità."""

    def go():
        items = catalog.load_catalog(refresh=refresh)
        items = catalog.filter_catalog(items, keyword=keyword, ambito=ambito, unita=unita)
        return [
            {
                "pfun": e.get("Id report"),
                "titolo": e.get("Titolo report"),
                "validità": e.get("Inizio/fine validità report"),
                "analisi": e.get("Analisi temporale"),
                "ambito": e.get("Ambito territoriale"),
                "unità": e.get("Unità territoriale"),
                "parametri": e.get("parametri necessari"),
            }
            for e in items
        ]

    output.emit(_run(go), title="Catalogo SITUAS")


app.command("list", hidden=True)(catalog_cmd)


@app.command(
    "info",
    epilog="**Esempio:** `opensituas -o json info 50 | jq '.colonne[].colonna'`",
)
def info_cmd(pfun: int = typer.Argument(..., help="Id report (campo pfun del catalogo)")) -> None:
    """Metadati di un report: descrizione e dettaglio delle colonne."""

    def go():
        entry = catalog.get_entry(pfun)
        link = catalog.apply_date(entry["INFO_LINK"], default_date=catalog.validity_end(entry))
        data = base.publish_get(link, timeout=_timeout())
        cols = data.get("COL_DETAILS", [])
        return {
            "pfun": pfun,
            "report": data.get("REPORT NAME"),
            "descrizione": data.get("REPORT DESCRIZIONE"),
            "colonne": [
                {
                    "colonna": c.get("COLNAME"),
                    "label": c.get("LABEL"),
                    "tipo": c.get("TYPE"),
                    "guida": c.get("GUIDA"),
                }
                for c in cols
            ],
        }

    result = _run(go)
    if output.get_mode() == "table":
        output.console.print(f"[bold]{result['report']}[/bold] (pfun {result['pfun']})")
        output.console.print(result["descrizione"] or "")
        output.emit(result["colonne"], title="Colonne")
    else:
        output.emit(result)


@app.command(
    "get",
    epilog=(
        "Senza `--date` i report DATA restituiscono il dato **più recente** (fine "
        "validità). Per una data storica passa `--date` (dentro la validità mostrata da "
        "`catalog`, altrimenti exit 2: REPORT NON DISPONIBILE).\n\n"
        "**Esempi:**\n\n"
        "* `opensituas -o json get 61` (comuni di oggi)\n\n"
        "* `opensituas -o json get 50 --date 12/01/1927`\n\n"
        "* `opensituas -o csv get 98 --from 17/03/1861 --to 31/05/2026 --out comuni.csv`"
    ),
)
def get_cmd(
    pfun: int = typer.Argument(..., help="Id report"),
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Data DD/MM/YYYY (report a data singola, analisi=DATA)"),
    date_from: Optional[str] = typer.Option(None, "--from", help="Data inizio DD/MM/YYYY (report a intervallo, analisi=PERIODO)"),
    date_to: Optional[str] = typer.Option(None, "--to", help="Data fine DD/MM/YYYY (report a intervallo, analisi=PERIODO)"),
    out: Optional[Path] = typer.Option(None, "--out", help="Salva su file (formato secondo --output)"),
) -> None:
    """Scarica i dati di un report. Default report DATA: dato più recente (fine validità); override con --date / --from/--to."""

    def go():
        entry = catalog.get_entry(pfun)
        link = catalog.apply_date(
            entry["SPOOL_LINK"], date, date_from, date_to,
            default_date=catalog.validity_end(entry),
        )
        return base.rows(base.publish_get(link, timeout=_timeout()))

    rows = _run(go)
    if out:
        mode = output.get_mode()
        text = (
            output.rows_to_csv(rows)
            if mode == "csv"
            else json.dumps(rows, ensure_ascii=False, indent=2)
        )
        if out.parent != Path("."):
            out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        output.err_console.print(f"[green]Salvate {len(rows)} righe in[/green] {out}")
    else:
        output.emit(rows, title=f"Report {pfun}")


@app.command(
    "count",
    epilog=(
        "Senza `--date` i report DATA contano alla **fine validità** (dato più recente); "
        "passa `--date` per una data storica.\n\n"
        "**Esempio:** `opensituas -o json count 61 | jq '.[0].NUM_ROWS'`"
    ),
)
def count_cmd(
    pfun: int = typer.Argument(..., help="Id report"),
    date: Optional[str] = typer.Option(None, "--date", "-d"),
    date_from: Optional[str] = typer.Option(None, "--from"),
    date_to: Optional[str] = typer.Option(None, "--to"),
) -> None:
    """Numero di righe di un report (senza scaricarle). Default report DATA: dato più recente (fine validità)."""

    def go():
        entry = catalog.get_entry(pfun)
        link = catalog.apply_date(
            entry["COUNT_LINK"], date, date_from, date_to,
            default_date=catalog.validity_end(entry),
        )
        return base.rows(base.publish_get(link, timeout=_timeout()))

    output.emit(_run(go), title=f"Conteggio report {pfun}")


# ----------------------------------------------------------------- query territoriali


@app.command(
    "storia",
    epilog=(
        "Se il nome è ambiguo (più unità) il comando esce con codice 2 elencando i codici: "
        "rilancia con un codice.\n\n"
        "**Esempi:**\n\n"
        "* `opensituas -o json storia comune Roma`\n\n"
        "* `opensituas -o json storia provincia 058 --dettaglio`\n\n"
        "* `opensituas -o json storia regione Lazio`"
    ),
)
def storia_cmd(
    tipo: str = typer.Argument(..., help="comune | provincia | regione"),
    query: str = typer.Argument(..., help="Denominazione o codice dell'unità"),
    dettaglio: bool = typer.Option(False, "--dettaglio", help="Aggiunge provvedimento e unità coinvolte"),
) -> None:
    """Storia delle variazioni di un'unità territoriale (storia_ua / variazioni)."""

    def go():
        return territorial.storia(tipo, query, dettaglio=dettaglio)

    result = _run(go)
    if output.get_mode() == "table":
        u = result["unita"]
        label = f"{u['code']} {u['name']}" + (f" [{u['tipo_desc']}]" if u.get("tipo_desc") else "")
        output.emit(result["storia"], title=f"Storia {tipo}: {label}")
    else:
        output.emit(result)


@app.command(
    "cerca-codice",
    epilog="**Esempio:** `opensituas -o json cerca-codice comune Roma`",
)
def cerca_codice_cmd(
    tipo: str = typer.Argument(..., help="comune | provincia | regione"),
    query: str = typer.Argument(..., help="Denominazione o codice da cercare"),
    limit: int = typer.Option(20, "--limit", help="Max corrispondenze da dettagliare"),
) -> None:
    """Ricerca codice Istat: codici, denominazioni e periodi di validità di un'unità."""

    def go():
        return territorial.cerca_codice(tipo, query, limit=limit)

    output.emit(_run(go), title=f"Ricerca codice {tipo}: {query}")


# ------------------------------------------------------------------ agent / discovery


@app.command("agent-context")
def agent_context_cmd() -> None:
    """Emette un JSON versionato con schema CLI per l'auto-orientamento degli agenti AI."""
    import sys

    sys.stdout.write(json.dumps(_AGENT_CONTEXT, ensure_ascii=False, indent=2) + "\n")


def _which_search(query: str, items: list[dict], limit: int) -> list[dict]:
    """Cerca report per token della query su titolo/ambito/unità. Ordina per rilevanza."""
    tokens = [t.lower() for t in query.split() if t]
    results = []
    for entry in items:
        haystack = " ".join([
            entry.get("Titolo report", ""),
            entry.get("Ambito territoriale", ""),
            entry.get("Unità territoriale", ""),
        ]).lower()
        score = sum(1 for t in tokens if t in haystack)
        if score > 0:
            results.append((score, entry))
    results.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in results[:limit]]


def _comando_suggerito(entry: dict) -> str:
    """Restituisce il comando opensituas suggerito con date di default per il report."""
    pfun = entry.get("Id report", "?")
    if catalog.is_range(entry):
        val = entry.get("Inizio/fine validità report", "")
        parts = val.split(" - ") if " - " in val else ["", ""]
        date_from = parts[0].strip() or "DD/MM/YYYY"
        date_to = parts[1].strip() or "DD/MM/YYYY"
        return f"opensituas get {pfun} --from {date_from} --to {date_to}"
    else:
        default = catalog.validity_end(entry) or "DD/MM/YYYY"
        return f"opensituas get {pfun} --date {default}"


@app.command(
    "which",
    epilog=(
        "Senza argomento elenca tutti i report con il comando suggerito.\n\n"
        "Exit code `2` = nessun report corrisponde alla query.\n\n"
        "**Esempi:**\n\n"
        "* `opensituas which 'comuni per anno'`\n\n"
        "* `opensituas which --limit 1 province`\n\n"
        "* `opensituas -o json which 'province cessate'`"
    ),
)
def which_cmd(
    query: Optional[str] = typer.Argument(None, help="Query in linguaggio naturale (es. 'comuni per anno')"),
    limit: int = typer.Option(3, "--limit", help="Max risultati (default 3)"),
) -> None:
    """Trova report SITUAS da una query in linguaggio naturale. Exit 2 se nessun match."""

    def go():
        items = catalog.load_catalog()
        if query:
            matched = _which_search(query, items, limit)
            if not matched:
                raise base.SituasError(f"Nessun report corrisponde a '{query}'")
        else:
            matched = items
        return [
            {
                "pfun": e.get("Id report"),
                "titolo": e.get("Titolo report"),
                "analisi": e.get("Analisi temporale"),
                "ambito": e.get("Ambito territoriale"),
                "unità": e.get("Unità territoriale"),
                "comando_suggerito": _comando_suggerito(e),
            }
            for e in matched
        ]

    output.emit(_run(go), title="Report SITUAS" + (f" per '{query}'" if query else ""))


def main() -> None:
    app()
