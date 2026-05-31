"""CLI opensituas — interfaccia per le API SITUAS, orchestrabile da agenti AI.

Variabili d'ambiente:
  OPENSITUAS_TIMEOUT   timeout richieste in secondi (default 60)

Flag globale --output table|json|csv. In modalità json/csv l'output è pulito su stdout.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer

from . import base, catalog, output, territorial

app = typer.Typer(
    help="opensituas — CLI per il SITUAS (ISTAT). Catalogo report + query territoriali.",
    no_args_is_help=True,
    add_completion=False,
)


def _timeout() -> float:
    return float(os.environ.get("OPENSITUAS_TIMEOUT", base.DEFAULT_TIMEOUT))


@app.callback()
def _main(
    output_mode: str = typer.Option(
        "table", "--output", "-o", help="Formato output: table | json | csv"
    ),
) -> None:
    if output_mode not in ("table", "json", "csv"):
        output.err_console.print(
            f"[red]--output non valido:[/red] {output_mode} (usa table|json|csv)"
        )
        raise typer.Exit(2)
    output.set_mode(output_mode)


def _run(fn):
    """Esegue una funzione gestendo gli errori applicativi SITUAS."""
    try:
        return fn()
    except base.SituasError as exc:
        output.err_console.print(f"[red]Errore:[/red] {exc}")
        raise typer.Exit(2)


# --------------------------------------------------------------------------- catalogo


@app.command("catalog")
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


@app.command("info")
def info_cmd(pfun: int = typer.Argument(..., help="Id report")) -> None:
    """Metadati di un report: descrizione e dettaglio delle colonne."""

    def go():
        entry = catalog.get_entry(pfun)
        data = base.publish_get(entry["INFO_LINK"], timeout=_timeout())
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


@app.command("get")
def get_cmd(
    pfun: int = typer.Argument(..., help="Id report"),
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Data DD/MM/YYYY (report a data singola)"),
    date_from: Optional[str] = typer.Option(None, "--from", help="Data inizio (report a intervallo)"),
    date_to: Optional[str] = typer.Option(None, "--to", help="Data fine (report a intervallo)"),
    out: Optional[Path] = typer.Option(None, "--out", help="Salva su file (formato secondo --output)"),
) -> None:
    """Scarica i dati di un report. Default: data valida dal catalogo; override con --date / --from/--to."""

    def go():
        entry = catalog.get_entry(pfun)
        link = catalog.apply_date(entry["SPOOL_LINK"], date, date_from, date_to)
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


@app.command("count")
def count_cmd(
    pfun: int = typer.Argument(..., help="Id report"),
    date: Optional[str] = typer.Option(None, "--date", "-d"),
    date_from: Optional[str] = typer.Option(None, "--from"),
    date_to: Optional[str] = typer.Option(None, "--to"),
) -> None:
    """Numero di righe di un report (senza scaricarle)."""

    def go():
        entry = catalog.get_entry(pfun)
        link = catalog.apply_date(entry["COUNT_LINK"], date, date_from, date_to)
        return base.rows(base.publish_get(link, timeout=_timeout()))

    output.emit(_run(go), title=f"Conteggio report {pfun}")


# ----------------------------------------------------------------- query territoriali


@app.command("storia")
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


@app.command("cerca-codice")
def cerca_codice_cmd(
    tipo: str = typer.Argument(..., help="comune | provincia | regione"),
    query: str = typer.Argument(..., help="Denominazione o codice da cercare"),
    limit: int = typer.Option(20, "--limit", help="Max corrispondenze da dettagliare"),
) -> None:
    """Ricerca codice Istat: codici, denominazioni e periodi di validità di un'unità."""

    def go():
        return territorial.cerca_codice(tipo, query, limit=limit)

    output.emit(_run(go), title=f"Ricerca codice {tipo}: {query}")


def main() -> None:
    app()
