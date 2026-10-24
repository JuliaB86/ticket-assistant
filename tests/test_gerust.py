"""Smoke-Test: Paketstruktur ist importierbar und die Abhängigkeiten sind installiert."""

import importlib


def test_paketstruktur_ist_importierbar():
    for modul in ("domain", "persistence", "matrix", "ticketing", "api"):
        importlib.import_module(f"ticket_assistant.{modul}")


def test_abhaengigkeiten_sind_verfuegbar():
    for modul in ("fastapi", "sqlalchemy", "pydantic"):
        importlib.import_module(modul)
