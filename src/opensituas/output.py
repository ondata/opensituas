"""Formattazione output multi-formato: table (Rich), json, csv.

Modalità globale impostata da `--output`. In `json` il dato è serializzato fedelmente;
in `table`/`csv` si estrae la lista di record tabellari. Pensato per l'orchestrazione da
agente: `json`/`csv` vanno puliti su stdout, i messaggi diagnostici su stderr.
"""

from __future__ import annotations

import csv
import io
import json
import sys

from rich.console import Console
from rich.table import Table

console = Console()
err_console = Console(stderr=True)

_MODE = {"value": "table"}


def set_mode(mode: str) -> None:
    _MODE["value"] = mode


def get_mode() -> str:
    return _MODE["value"]


def _as_rows(data: object) -> list[dict]:
    if isinstance(data, list):
        return [r if isinstance(r, dict) else {"value": r} for r in data]
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                return [r if isinstance(r, dict) else {"value": r} for r in value]
        return [data]
    return [{"value": data}]


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _columns(rows: list[dict]) -> list[str]:
    cols: list[str] = []
    for row in rows:
        for key in row:
            if key not in cols:
                cols.append(key)
    return cols


def rows_to_csv(rows: list[dict]) -> str:
    if not rows:
        return ""
    cols = _columns(rows)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({c: _cell(row.get(c)) for c in cols})
    return buf.getvalue()


def emit(data: object, title: str | None = None) -> None:
    mode = _MODE["value"]
    if mode == "json":
        sys.stdout.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        return
    rows = _as_rows(data)
    if mode == "csv":
        sys.stdout.write(rows_to_csv(rows))
        return
    _emit_table(rows, title)


def _emit_table(rows: list[dict], title: str | None) -> None:
    if not rows:
        err_console.print("[yellow]Nessun risultato.[/yellow]")
        return
    cols = _columns(rows)
    table = Table(title=title, show_lines=False, header_style="bold cyan")
    for col in cols:
        table.add_column(col, overflow="fold")
    for row in rows:
        table.add_row(*[_cell(row.get(c)) for c in cols])
    console.print(table)
