"""Domänenfehler. Keine I/O, keine Abhängigkeit zu FastAPI oder SQLAlchemy."""


class DomaenenFehler(Exception):
    """Basisklasse für alle fachlichen Fehler des Ticket Assistant."""


class UnzulaessigerStatuswechsel(DomaenenFehler):
    """Ein Statuswechsel, den Abschnitt 5 der Spezifikation nicht erlaubt."""

    def __init__(self, von: object, nach: object) -> None:
        self.von = von
        self.nach = nach
        super().__init__(f"Statuswechsel von '{von}' nach '{nach}' ist nicht erlaubt.")
