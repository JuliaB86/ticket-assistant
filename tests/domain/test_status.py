"""Tests zum Statusmodell, Abschnitt 5 der Spezifikation.

Geprüft werden alle 36 Paare aus sechs Positionsstatus. Sieben Übergänge sind
erlaubt, 29 sind unzulässig. Selbstübergänge zählen als unzulässig.
"""

import itertools

import pytest

from ticket_assistant.domain.fehler import UnzulaessigerStatuswechsel
from ticket_assistant.domain.status import (
    ERLAUBTE_UEBERGAENGE,
    PositionsStatus,
    VorgangsStatus,
    ist_erlaubt,
    ist_wiedereroeffnung,
    pruefe_uebergang,
    vorgangsstatus_aus_positionen,
)

ALLE_PAARE = list(itertools.product(PositionsStatus, PositionsStatus))
UNERLAUBTE_PAARE = [paar for paar in ALLE_PAARE if paar not in ERLAUBTE_UEBERGAENGE]


def test_anzahl_der_paare_entspricht_der_tabelle():
    assert len(ALLE_PAARE) == 36
    assert len(ERLAUBTE_UEBERGAENGE) == 7
    assert len(UNERLAUBTE_PAARE) == 29


@pytest.mark.parametrize(("von", "nach"), sorted(ERLAUBTE_UEBERGAENGE))
def test_erlaubter_uebergang(von: PositionsStatus, nach: PositionsStatus):
    assert ist_erlaubt(von, nach) is True
    pruefe_uebergang(von, nach)


@pytest.mark.parametrize(("von", "nach"), UNERLAUBTE_PAARE)
def test_unerlaubter_uebergang(von: PositionsStatus, nach: PositionsStatus):
    assert ist_erlaubt(von, nach) is False
    with pytest.raises(UnzulaessigerStatuswechsel) as fehler:
        pruefe_uebergang(von, nach)
    assert fehler.value.von is von
    assert fehler.value.nach is nach


@pytest.mark.parametrize("status", list(PositionsStatus))
def test_selbstuebergang_ist_unzulaessig(status: PositionsStatus):
    assert ist_erlaubt(status, status) is False


@pytest.mark.parametrize(
    "nach", [PositionsStatus.VERIFIZIERT, PositionsStatus.GESCHLOSSEN]
)
def test_offen_fuehrt_nie_direkt_zu_verifiziert_oder_geschlossen(nach: PositionsStatus):
    with pytest.raises(UnzulaessigerStatuswechsel):
        pruefe_uebergang(PositionsStatus.OFFEN, nach)


def test_verifiziert_nur_ueber_umgesetzt_erreichbar():
    vorgaenger = {von for von, nach in ERLAUBTE_UEBERGAENGE if nach is PositionsStatus.VERIFIZIERT}
    assert vorgaenger == {PositionsStatus.UMGESETZT}


def test_geschlossen_nur_ueber_verifiziert_erreichbar():
    vorgaenger = {von for von, nach in ERLAUBTE_UEBERGAENGE if nach is PositionsStatus.GESCHLOSSEN}
    assert vorgaenger == {PositionsStatus.VERIFIZIERT}


@pytest.mark.parametrize(("von", "nach"), ALLE_PAARE)
def test_wiedereroeffnung_nur_bei_umgesetzt_nach_bei_owner(
    von: PositionsStatus, nach: PositionsStatus
):
    erwartet = von is PositionsStatus.UMGESETZT and nach is PositionsStatus.BEI_OWNER
    assert ist_wiedereroeffnung(von, nach) is erwartet


class TestVorgangsstatus:
    """Ableitung des Vorgangsstatus aus den Positionen, Abschnitt 5."""

    def test_ohne_positionen_offen(self):
        assert vorgangsstatus_aus_positionen([]) is VorgangsStatus.OFFEN

    def test_alle_offen_ergibt_offen(self):
        positionen = [PositionsStatus.OFFEN, PositionsStatus.OFFEN]
        assert vorgangsstatus_aus_positionen(positionen) is VorgangsStatus.OFFEN

    def test_alle_geschlossen_ergibt_geschlossen(self):
        positionen = [PositionsStatus.GESCHLOSSEN, PositionsStatus.GESCHLOSSEN]
        assert vorgangsstatus_aus_positionen(positionen) is VorgangsStatus.GESCHLOSSEN

    def test_eine_wartet_auf_information_ergibt_wartet_auf_information(self):
        positionen = [PositionsStatus.BEI_OWNER, PositionsStatus.WARTET_AUF_INFORMATION]
        assert (
            vorgangsstatus_aus_positionen(positionen)
            is VorgangsStatus.WARTET_AUF_INFORMATION
        )

    def test_eine_aktive_position_ergibt_in_bearbeitung(self):
        positionen = [PositionsStatus.OFFEN, PositionsStatus.BEI_OWNER]
        assert vorgangsstatus_aus_positionen(positionen) is VorgangsStatus.IN_BEARBEITUNG

    def test_teilweise_geschlossen_ergibt_in_bearbeitung(self):
        positionen = [PositionsStatus.GESCHLOSSEN, PositionsStatus.VERIFIZIERT]
        assert vorgangsstatus_aus_positionen(positionen) is VorgangsStatus.IN_BEARBEITUNG
