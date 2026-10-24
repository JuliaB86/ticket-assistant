"""Statusmodell nach Abschnitt 5 der Spezifikation.

Dies ist die einzige Stelle, an der Statuswechsel geprüft werden. Andere Module
setzen `status` nicht direkt, sondern rufen `pruefe_uebergang` auf.
"""

from collections.abc import Iterable
from enum import StrEnum

from ticket_assistant.domain.fehler import UnzulaessigerStatuswechsel


class PositionsStatus(StrEnum):
    """Status einer Vorgangsposition, Abschnitt 5."""

    OFFEN = "offen"
    WARTET_AUF_INFORMATION = "wartet_auf_information"
    BEI_OWNER = "bei_owner"
    UMGESETZT = "umgesetzt"
    VERIFIZIERT = "verifiziert"
    GESCHLOSSEN = "geschlossen"


class VorgangsStatus(StrEnum):
    """Status eines Vorgangs, abgeleitet aus seinen Positionen, Abschnitt 5."""

    OFFEN = "offen"
    WARTET_AUF_INFORMATION = "wartet_auf_information"
    IN_BEARBEITUNG = "in_bearbeitung"
    GESCHLOSSEN = "geschlossen"


#: Die erlaubten Übergänge aus der Tabelle in Abschnitt 5. Alles andere ist unzulässig,
#: insbesondere `offen` -> `verifiziert` und `offen` -> `geschlossen`.
#: Selbstübergänge sind nicht enthalten und damit ebenfalls unzulässig.
ERLAUBTE_UEBERGAENGE: frozenset[tuple[PositionsStatus, PositionsStatus]] = frozenset(
    {
        (PositionsStatus.OFFEN, PositionsStatus.WARTET_AUF_INFORMATION),
        (PositionsStatus.OFFEN, PositionsStatus.BEI_OWNER),
        (PositionsStatus.WARTET_AUF_INFORMATION, PositionsStatus.BEI_OWNER),
        (PositionsStatus.BEI_OWNER, PositionsStatus.UMGESETZT),
        (PositionsStatus.UMGESETZT, PositionsStatus.VERIFIZIERT),
        (PositionsStatus.UMGESETZT, PositionsStatus.BEI_OWNER),
        (PositionsStatus.VERIFIZIERT, PositionsStatus.GESCHLOSSEN),
    }
)


def ist_erlaubt(von: PositionsStatus, nach: PositionsStatus) -> bool:
    """Gibt zurück, ob der Übergang `von` -> `nach` nach Abschnitt 5 erlaubt ist."""
    return (von, nach) in ERLAUBTE_UEBERGAENGE


def pruefe_uebergang(von: PositionsStatus, nach: PositionsStatus) -> None:
    """Löst `UnzulaessigerStatuswechsel` aus, wenn der Übergang nicht erlaubt ist."""
    if not ist_erlaubt(von, nach):
        raise UnzulaessigerStatuswechsel(von, nach)


def ist_wiedereroeffnung(von: PositionsStatus, nach: PositionsStatus) -> bool:
    """Gibt zurück, ob der Übergang eine Wiedereröffnung nach Abschnitt 13.4 ist.

    Nur bei `umgesetzt` -> `bei_owner` wird der Zähler `wiedereroeffnungen` erhöht.
    """
    return von is PositionsStatus.UMGESETZT and nach is PositionsStatus.BEI_OWNER


def vorgangsstatus_aus_positionen(
    positionen: Iterable[PositionsStatus],
) -> VorgangsStatus:
    """Leitet den Vorgangsstatus aus den Positionsstatus ab, Abschnitt 5.

    Reihenfolge der Prüfung laut Spezifikation:
    alle `geschlossen` -> `geschlossen`, mindestens eine `wartet_auf_information`
    -> `wartet_auf_information`, sonst `in_bearbeitung`, sobald eine Position aktiv ist.
    Sind alle Positionen `offen`, ist der Vorgang `offen`.
    """
    status = list(positionen)
    if not status:
        return VorgangsStatus.OFFEN
    if all(s is PositionsStatus.GESCHLOSSEN for s in status):
        return VorgangsStatus.GESCHLOSSEN
    if any(s is PositionsStatus.WARTET_AUF_INFORMATION for s in status):
        return VorgangsStatus.WARTET_AUF_INFORMATION
    if all(s is PositionsStatus.OFFEN for s in status):
        return VorgangsStatus.OFFEN
    return VorgangsStatus.IN_BEARBEITUNG
