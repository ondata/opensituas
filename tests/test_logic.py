"""Test della logica pura (senza rete): envelope, errori, gestione date."""

from __future__ import annotations

import httpx
import pytest

from opensituas import base, catalog


def test_rows_resultset():
    assert base.rows({"resultset": [{"a": 1}]}) == [{"a": 1}]


def test_rows_items():
    assert base.rows({"items": [{"b": 2}]}) == [{"b": 2}]


def test_rows_empty():
    assert base.rows({}) == []
    assert base.rows(None) == []


def test_check_errcode_raises():
    with pytest.raises(base.SituasError, match="REPORT NON DISPONIBILE"):
        base._check_error({"resultset": [{"ERRCODE": "REPORT NON DISPONIBILE"}]}, "ctx")


def test_check_message_raises():
    with pytest.raises(base.SituasError):
        base._check_error({"message": "non può essere invocato"}, "ctx")


def test_check_status_raises():
    with pytest.raises(base.SituasError, match="status 500"):
        base._check_error({"status": 500, "title": "errore"}, "ctx")


SPOOL = "https://situas-servizi.istat.it/publish/reportspooljson?pfun=42&pdata=17/03/1861"
RANGE = "https://situas-servizi.istat.it/publish/reportspooljson?pfun=98&pdatada=17/03/1861&pdataa=31/05/2026"


def test_apply_date_default_unchanged():
    assert catalog.apply_date(SPOOL) == SPOOL


def test_apply_date_override_single():
    out = catalog.apply_date(SPOOL, date="01/01/2000")
    assert "pdata=01/01/2000" in out
    assert "pfun=42" in out


def test_apply_date_range_override():
    out = catalog.apply_date(RANGE, date_from="01/01/1900", date_to="31/12/1999")
    assert "pdatada=01/01/1900" in out and "pdataa=31/12/1999" in out


def test_apply_date_wrong_pattern_single():
    with pytest.raises(base.SituasError):
        catalog.apply_date(SPOOL, date_from="01/01/2000")


def test_apply_date_wrong_pattern_range():
    with pytest.raises(base.SituasError):
        catalog.apply_date(RANGE, date="01/01/2000")


def test_apply_date_mutually_exclusive():
    with pytest.raises(base.SituasError):
        catalog.apply_date(SPOOL, date="01/01/2000", date_from="01/01/2000")


def test_parse_tollera_control_chars():
    # SITUAS produce talvolta \r\n grezzi dentro le stringhe (JSON non valido stretto)
    resp = httpx.Response(200, text='{"resultset":[{"x":"riga1\r\nriga2"}]}')
    data = base._parse(resp, "ctx")
    assert data["resultset"][0]["x"] == "riga1\r\nriga2"


def test_bundled_catalog_loads():
    items = catalog._bundled()
    assert len(items) >= 70
    assert all("Id report" in e for e in items)
