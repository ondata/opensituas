"""Strato HTTP per le API SITUAS.

Due basi distinte:

- **Gateway** (`GATEWAY_URL`): proxy POST verso i servizi Oracle ORDS. Riceve
  `{"url": "<nome_servizio>?<query>"}`. Serve per il catalogo (`get_elenco_microservizi`)
  e per tutte le query interattive (`ricercacodice_*`, `var_get_ua_*`).
- **Publish** (`PUBLISH_BASE`): endpoint pubblici GET per i dati dei report
  (`reportspooljson`, `reportspooljsoncount`, `anagrafica_report_metadato_web`).

Particolarità scoperte sul campo:

- I servizi `ricercacodice_*` rispondono vuoto senza un header `Referer` browser-like:
  lo inviamo su **tutte** le chiamate al gateway.
- L'envelope JSON varia: `resultset` (reportspooljson, ricercacodice) oppure `items`
  (var_get_ua_*, catalogo). `rows()` normalizza entrambi.
- Gli errori applicativi arrivano con HTTP 200, come `{"resultset":[{"ERRCODE":"..."}]}`
  oppure `{"message": "..."}`: vanno letti dal payload, non dallo status code.
"""

from __future__ import annotations

import json

import httpx

GATEWAY_URL = "https://situas.istat.it/ShibO2Module/api/Report/ReportByUrl"
PUBLISH_BASE = "https://situas-servizi.istat.it/publish"

DEFAULT_TIMEOUT = 60.0

_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Referer": "https://situas.istat.it/web/",
    "language": "IT",
}


class SituasError(Exception):
    """Errore applicativo restituito dalle API SITUAS."""


def _client(timeout: float) -> httpx.Client:
    return httpx.Client(timeout=timeout, headers=_HEADERS, follow_redirects=True)


def gateway(service: str, timeout: float = DEFAULT_TIMEOUT) -> dict:
    """Invoca un servizio ORDS tramite il gateway report.

    `service` è il nome del servizio con la sua querystring, es.
    ``"ricercacodice_criterio_lov?haRuolo&ptipounit=1"``.
    """
    try:
        with _client(timeout) as client:
            resp = client.post(GATEWAY_URL, content=json.dumps({"url": service}))
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise SituasError(f"Gateway SITUAS irraggiungibile: {exc}") from exc
    return _parse(resp, service)


def publish_get(url: str, timeout: float = DEFAULT_TIMEOUT) -> dict:
    """GET di un URL publish già formato (es. uno SPOOL_LINK del catalogo)."""
    try:
        with _client(timeout) as client:
            resp = client.get(url)
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise SituasError(f"Endpoint SITUAS irraggiungibile: {exc}") from exc
    return _parse(resp, url)


def rows(data: object) -> list[dict]:
    """Estrae la lista di record da un payload SITUAS (envelope `resultset` o `items`)."""
    if isinstance(data, dict):
        for key in ("resultset", "items"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    if isinstance(data, list):
        return data
    return []


def _parse(resp: httpx.Response, ctx: str) -> dict:
    # strict=False: alcuni metadati SITUAS contengono \r\n grezzi dentro le stringhe
    # (caratteri di controllo non escapati), tecnicamente JSON non valido ma tollerabile.
    try:
        data = json.loads(resp.text, strict=False)
    except (json.JSONDecodeError, ValueError) as exc:
        raise SituasError(f"Risposta non-JSON da SITUAS ({ctx[:80]})") from exc
    _check_error(data, ctx)
    return data


def _check_error(data: object, ctx: str) -> None:
    if isinstance(data, dict):
        status = data.get("status")
        if isinstance(status, int) and status >= 400:
            raise SituasError(f"{data.get('title', 'Errore')} (status {status})")
        if "message" in data and "resultset" not in data and "items" not in data:
            raise SituasError(str(data["message"]))
    recs = rows(data)
    if len(recs) == 1 and isinstance(recs[0], dict) and "ERRCODE" in recs[0]:
        raise SituasError(f"{recs[0]['ERRCODE']} ({ctx[:80]})")
