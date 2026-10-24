# Ticket Assistant – Projektkontext

## Zweck
Operations Assistant für Joiner-, Mover-, Leaver- und Access-Prozesse.
Er erkennt den Fall, fragt fehlende Pflichtdaten ab, wählt Owner und Ticketweg
über die Ownership-Matrix, verfolgt den Status und schließt Vorgänge erst bei
erfüllter Definition of Done.

Er vergibt KEINE Berechtigungen. Freigaben liegen immer bei den Ownern.

## Fachliche Quelle
- Spezifikation: `docs/spec.md` (verbindlich, bei Widersprüchen gilt die Spec)
- Beispiel-Matrix: `data/ownership_matrix.example.csv` (Format-Vorlage, keine echten Daten)

## Stack (MVP)
- Python 3.12
- FastAPI (HTTP-API und spätere Dashboard-Anbindung)
- SQLAlchemy 2.x + SQLite (Datei `data/app.db`)
- pytest, ruff, pydantic
- Ticketing: GoTo Resolve Helpdesk, zunächst nur über Mock-Adapter

## Verzeichnisstruktur
- `src/ticket_assistant/domain/`   Statusmodell, Regeln, Validierung (keine I/O)
- `src/ticket_assistant/persistence/` SQLAlchemy-Modelle und Repositories
- `src/ticket_assistant/matrix/`   CSV-Import der Ownership-Matrix
- `src/ticket_assistant/ticketing/` Adapter-Interface und Mock-Implementierung
- `src/ticket_assistant/api/`      FastAPI-Routen
- `tests/`                          spiegelt die Struktur von `src/`

## Leitplanken
- Statuswechsel NUR über die State Machine in `domain/status.py`.
  Kein direktes Setzen von `status` an anderer Stelle.
- Ein Leaver-Vorgang wird nur geschlossen, wenn ALLE Vorgangspositionen
  den Status `verifiziert` haben.
- Der Ticketing-Adapter ist ein Interface. Produktive GoTo-Zugänge werden
  nicht implementiert, bevor die API-Frage geklärt ist.
- Keine Credentials im Repository. Konfiguration über Umgebungsvariablen.
- Jede Aktion (Anlage, Statuswechsel, Matrix-Import, Adapter-Aufruf)
  schreibt einen Eintrag ins Ereignis-Log.
- Personenbezogene Daten nur speichern, soweit im Spec beschrieben.
- Keine LLM-Aufrufe in Phase 1.

## Befehle
- Installation: `pip install -e ".[dev]"`
- Tests: `pytest`
- Lint: `ruff check .`
- Start: `uvicorn ticket_assistant.api.main:app --reload`

## Arbeitsweise
- Vor größeren Änderungen einen Plan vorlegen und auf Freigabe warten.
- Nach jeder Änderung `pytest` und `ruff check .` ausführen.
- Commits klein halten, eine Aufgabe pro Commit.

## Definition of Done
- Tests für alle erlaubten und unerlaubten Statusübergänge sind vorhanden und grün.
- Leaver-Schutzregel ist durch einen Test abgedeckt.
- Matrix-Import lehnt ungültige Zeilen mit verständlicher Fehlermeldung ab.
- `docs/spec.md` stimmt mit dem Code überein.
