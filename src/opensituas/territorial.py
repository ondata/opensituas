"""Query territoriali interattive: storia/variazioni e ricerca codice.

A differenza del catalogo, questi comandi prendono input "vivo" dell'utente
(nome o codice di un'unità) e NON sono verificati da una voce di catalogo con date
pre-validate. Tutto passa per il gateway report.

Tre famiglie di unità — comune, provincia/uts, regione — con servizi `var_get_ua_*`
per la storia delle variazioni, e servizi `ricercacodice_*` per la ricerca codice.
Le firme dei servizi sono state tracciate dal traffico reale del portale.
"""

from __future__ import annotations

from urllib.parse import quote

from . import base

# Configurazione per tipo unità: nomi servizio, parametri e mappatura dei campi
# restituiti dall'autocomplete (`diffusione`) verso un record normalizzato.
_UNITS: dict[str, dict] = {
    "comune": {
        "infix": "comuni",
        "param_name": "com",
        "param_code": "procom",
        "f_code": "pro_com_t",
        "f_name": "comune",
        "f_tipo": None,
        "f_tipo_desc": None,
        "f_origine": None,  # per i comuni l'id origine arriva dalla riga `rs`
        "origine_in_rs": "id_comune_origine",
        "dett_id_param": "idcomuneorig",
        "ricerca_tipo": 1,
    },
    "provincia": {
        "infix": "uts",
        "param_name": "uts",
        "param_code": "coduts",
        "f_code": "cod_uts",
        "f_name": "denominazione_uts",
        "f_tipo": "tipo uts",
        "f_tipo_desc": "descrizione tipo uts",
        "f_origine": "id_uts_origine",
        "origine_in_rs": None,
        "dett_id_param": "id_uts_origine",
        "ricerca_tipo": 2,
    },
    "regione": {
        "infix": "reg",
        "param_name": "reg",
        "param_code": "codreg",
        "f_code": "cod_regione",
        "f_name": "denominazione regione",
        "f_tipo": "tipo regione",
        "f_tipo_desc": "descrizione tipo regione",
        "f_origine": "id_regione_origine",
        "origine_in_rs": None,
        "dett_id_param": "id_regione_origine",
        "ricerca_tipo": 3,
    },
}

UNIT_TYPES = tuple(_UNITS)


def _cfg(unit_type: str) -> dict:
    try:
        return _UNITS[unit_type]
    except KeyError:
        raise base.SituasError(
            f"Tipo unità '{unit_type}' non valido. Usa: {', '.join(UNIT_TYPES)}"
        ) from None


def resolve_units(unit_type: str, query: str) -> list[dict]:
    """Risolve un nome/codice in candidati normalizzati via autocomplete `diffusione`.

    Ogni candidato: ``{code, name, tipo, tipo_desc, origine}``. Numerico → ricerca per
    codice, altrimenti per denominazione. Deduplica per (codice, tipo).
    """
    cfg = _cfg(unit_type)
    by_code = query.strip().isdigit()
    param = cfg["param_code"] if by_code else cfg["param_name"]
    service = f"var_get_ua_{cfg['infix']}_lov_diffusione?{param}={quote(query)}"
    raw = base.rows(base.gateway(service))

    seen: set[tuple] = set()
    candidates: list[dict] = []
    for r in raw:
        cand = {
            "code": str(r.get(cfg["f_code"], "")).strip(),
            "name": str(r.get(cfg["f_name"], "")).strip(),
            "tipo": r.get(cfg["f_tipo"]) if cfg["f_tipo"] else None,
            "tipo_desc": r.get(cfg["f_tipo_desc"]) if cfg["f_tipo_desc"] else None,
            "origine": r.get(cfg["f_origine"]) if cfg["f_origine"] else None,
        }
        key = (cand["code"], cand["tipo"])
        if key not in seen:
            seen.add(key)
            candidates.append(cand)
    return candidates


def _select_units(unit_type: str, query: str) -> list[dict]:
    """Seleziona le unità per la query.

    Restituisce una lista: di norma un solo elemento, ma per regioni/uts che hanno
    più "forme" storiche con lo stesso codice (es. Lazio Compartimento poi Regione)
    restituisce tutte le forme — la loro storia va unita. Solleva errore solo per
    ambiguità reale (codici diversi = unità diverse)."""
    candidates = resolve_units(unit_type, query)
    if not candidates:
        raise base.SituasError(f"Nessuna unità '{query}' trovata (tipo {unit_type})")
    q = query.strip().lower()
    exact = [c for c in candidates if c["code"].lower() == q or c["name"].lower() == q]
    pool = exact or candidates
    codes = {c["code"] for c in pool}
    if len(codes) > 1:
        listing = "; ".join(
            f"{c['code']} {c['name']}" + (f" [{c['tipo_desc']}]" if c["tipo_desc"] else "")
            for c in pool[:15]
        )
        raise base.SituasError(
            f"'{query}' è ambiguo ({len(codes)} unità). Rilancia con un codice preciso: {listing}"
        )
    return pool


def _event_key(row: dict) -> tuple:
    raw = str(row.get("data evento", "")).strip()
    try:
        d, m, y = raw.split("/")
        return (int(y), int(m), int(d))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def _fetch_rs(unit_type: str, unit: dict) -> list[dict]:
    cfg = _cfg(unit_type)
    code, name, tipo = quote(unit["code"]), quote(unit["name"]), unit["tipo"]
    if unit_type == "comune":
        service = f"var_get_ua_comuni_lov_rs?procom={code}&com={name}"
    elif unit_type == "regione":
        service = f"var_get_ua_reg_lov_rs?&codreg={code}&reg={name}&reg_tipo={tipo}"
    else:  # provincia / uts
        service = f"var_get_ua_uts_lov_rs?&uts={name}&coduts={code}&uts_tipo={tipo}"
    return base.rows(base.gateway(service))


def _fetch_dett(unit_type: str, unit: dict, var_row: dict, associazioni: bool) -> list[dict]:
    cfg = _cfg(unit_type)
    suffix = "rs_dett_ass" if associazioni else "rs_dett"
    mcrvar = quote(str(var_row.get("tipo variazione", "")))
    idprovv = var_row.get("identificativo provvedimento", "")
    # id origine: dalla riga rs (comuni) o dal candidato risolto (reg/uts)
    origine = var_row.get(cfg["origine_in_rs"]) if cfg["origine_in_rs"] else unit["origine"]
    parts = [f"{cfg['dett_id_param']}={origine}", f"mcrvar={mcrvar}", f"idprovv={idprovv}"]
    if unit_type in ("regione", "provincia"):
        tipo_param = "reg_tipo" if unit_type == "regione" else "uts_tipo"
        parts.append(f"{tipo_param}={unit['tipo']}")
    service = f"var_get_ua_{cfg['infix']}_lov_{suffix}?&" + "&".join(parts)
    return base.rows(base.gateway(service))


def storia(unit_type: str, query: str, dettaglio: bool = False) -> dict:
    """Storia delle variazioni di un'unità territoriale.

    Restituisce ``{"unita": {...}, "storia": [...]}``. Con `dettaglio`, a ogni variazione
    aggiunge ``provvedimento`` e ``unita_coinvolte``.
    """
    units = _select_units(unit_type, query)
    storia_rows: list[dict] = []
    for unit in units:
        for row in _fetch_rs(unit_type, unit):
            if dettaglio:
                try:
                    row["provvedimento"] = _fetch_dett(unit_type, unit, row, associazioni=False)
                    row["unita_coinvolte"] = _fetch_dett(unit_type, unit, row, associazioni=True)
                except base.SituasError:
                    row["provvedimento"] = []
                    row["unita_coinvolte"] = []
            storia_rows.append(row)
    storia_rows.sort(key=_event_key)
    return {"unita": units[0], "storia": storia_rows}


def cerca_codice(unit_type: str, query: str, limit: int = 20) -> list[dict]:
    """Ricerca codice Istat: codici, denominazioni e periodi di validità di un'unità.

    Usa la LOV `ricercacodice` (match su "codice - nome") e per ogni corrispondenza
    recupera il dettaglio via `_res`. Oltre `limit` corrispondenze restituisce solo
    l'elenco di disambiguazione (campo `V`).
    """
    cfg = _cfg(unit_type)
    ptipo = cfg["ricerca_tipo"]
    lov = base.rows(base.gateway(f"ricercacodice_criterio_lov?haRuolo&ptipounit={ptipo}"))
    q = query.strip().lower()

    def split(v: str) -> tuple[str, str]:
        code, _, name = str(v).partition(" - ")
        return code.strip().lower(), name.strip().lower()

    # Match esatto su codice o denominazione; in mancanza, ripiega su sottostringa.
    exact = [r for r in lov if q in split(r.get("V", ""))]
    matches = exact or [r for r in lov if q in str(r.get("V", "")).lower()]
    if not matches:
        raise base.SituasError(f"Nessun codice per '{query}' (tipo {unit_type})")
    if len(matches) > limit:
        return [{"_ambiguo": f"{len(matches)} corrispondenze, mostro le prime {limit}"}] + [
            {"V": m.get("V")} for m in matches[:limit]
        ]
    results: list[dict] = []
    for m in matches:
        res = base.rows(
            base.gateway(
                f"ricercacodice_criterio_res?haRuolo&ptipounit={ptipo}&prc={m['RC']}"
            )
        )
        results.extend(res)
    return results
