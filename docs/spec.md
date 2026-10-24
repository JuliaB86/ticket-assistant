# Spezifikation: Ticket Assistant (Phase 1)

## 1. Ziel
Der Assistant begleitet Access-, Joiner-, Mover- und Leaver-Prozesse, macht
Ownership transparent und verfolgt Vorgänge bis zur verifizierten Lösung.
Ticketing-System: GoTo Resolve Helpdesk.

## 2. Scope Phase 1
**Enthalten:**
- Fall `Access Issue` (Pilot)
- Fall `Leaver` (Datenmodell und Schutzregeln, Anlage per API)
- Ownership-Matrix als CSV-Import mit Validierung
- Statusmodell mit State Machine
- Ereignis-Log
- Ticketing-Adapter als Interface, Mock-Implementierung
- REST-API für Vorgänge, Positionen, Status, Matrix-Import
- Einfache Statusübersicht als JSON-Endpunkt

**Nicht enthalten (Phase 1):**
- LLM-Intent-Erkennung
- Automatisches Nachfassen und Eskalation (Phase 2, aber das Statusmodell muss es unterstützen)
- Echte GoTo-API-Anbindung
- Automatische Systemaktionen oder Berechtigungsvergabe
- Dashboard-Oberfläche

Die Fälle `Joiner`, `Mover`, `Shared Mailbox`, `DML`, `dentsu Connect` und `Plattformzugang`
sind in Phase 1 nicht umgesetzt. Das Datenmodell muss sie aber aufnehmen können
(Fallart ist ein Feld, kein Sonderfall im Code).

## 3. Begriffe
- **Vorgang:** Ein Joiner-, Mover-, Leaver- oder Access-Fall für eine Person oder ein Anliegen.
- **Vorgangsposition:** Eine Zeile pro betroffenem System innerhalb eines Vorgangs. Jede Position hat einen eigenen Status.
- **Matrix-Eintrag:** Ein System mit Owner, Ticketweg, SLA und Eskalationsstufen.
- **Ereignis-Log:** Unveränderliches Protokoll aller Aktionen.
- **Owner:** Person oder Team, das über Freigabe und Umsetzung entscheidet.

## 4. Datenmodell

### Vorgang
| Feld | Typ | Pflicht | Hinweis |
|---|---|---|---|
| id | UUID | ja | |
| fallart | Enum | ja | `access_issue`, `leaver`, `joiner`, `mover`, `shared_mailbox`, `dml`, `connect`, `plattformzugang` |
| betroffene_person | Text | nein | Nur wenn für den Fall nötig, siehe Datenschutz |
| anforderer | Text | ja | Wer hat den Vorgang angelegt |
| erstellt_am | Zeitstempel | ja | |
| status | Enum | ja | Abgeleitet aus den Positionen, siehe Abschnitt 5 |
| helpdesk_ticket_id | Text | nein | Referenz zum GoTo-Ticket, sobald angelegt |

### Vorgangsposition
| Feld | Typ | Pflicht | Hinweis |
|---|---|---|---|
| id | UUID | ja | |
| vorgang_id | UUID | ja | Fremdschlüssel |
| system_id | Text | ja | Verweis auf Matrix-Eintrag |
| status | Enum | ja | Statusmodell Abschnitt 5 |
| owner | Text | ja | Aus Matrix übernommen |
| verifiziert_durch | Text | nein | Pflicht beim Übergang nach `verifiziert` |
| verifiziert_am | Zeitstempel | nein | |
| sla_faellig_am | Zeitstempel | nein | Berechnet aus Matrix-SLA |
| wiedereroeffnungen | Ganzzahl | ja | Start 0, steigt bei jedem Übergang `umgesetzt` → `bei_owner` um 1, siehe Abschnitt 13.4 |

### Matrix-Eintrag
| Feld | Typ | Pflicht |
|---|---|---|
| system_id | Text, eindeutig | ja |
| system_name | Text | ja |
| fachlicher_owner | Text | ja |
| technischer_ansprechpartner | Text | ja |
| ticketweg | Text | ja |
| sla_stunden | Ganzzahl > 0 | ja |
| eskalation_stufe1 | Text | ja |
| eskalation_stufe2 | Text | ja |
| aktiv | Boolean | ja |
| freigabe_kunde_noetig | Boolean | ja |
| uebergabepfad | Text | ja |
| berechtigungsarten | Text, kommagetrennt | nein |

### Ereignis-Log
| Feld | Typ |
|---|---|
| id | UUID |
| zeitpunkt | Zeitstempel |
| akteur | Text (Person oder `system`) |
| aktion | Text |
| bezug | Text (Vorgangs- oder Positions-ID) |
| details | JSON |

Das Ereignis-Log wird nicht verändert oder gelöscht, außer durch Aufbewahrungsregeln nach Abschnitt 8.

## 5. Statusmodell

### Status einer Vorgangsposition
- `offen`: Angelegt, noch nicht an den Owner übergeben
- `wartet_auf_information`: Pflichtdaten fehlen, Rückfrage läuft
- `bei_owner`: An den Owner übergeben, Umsetzung läuft
- `umgesetzt`: Owner meldet Umsetzung
- `verifiziert`: Wirkung ist geprüft (siehe Definition of Done je Fall)
- `geschlossen`: Endzustand

### Erlaubte Übergänge
| Von | Nach | Bedingung |
|---|---|---|
| offen | wartet_auf_information | Pflichtdaten fehlen |
| offen | bei_owner | Pflichtdaten vollständig |
| wartet_auf_information | bei_owner | Pflichtdaten nachgeliefert |
| bei_owner | umgesetzt | Owner meldet Umsetzung |
| umgesetzt | verifiziert | Verifikation durch Anforderer oder Prüfung, Name wird gespeichert |
| umgesetzt | bei_owner | Verifikation fehlgeschlagen, zurück an Owner |
| verifiziert | geschlossen | Keine Bedingung über die Verifikation hinaus |

Alle anderen Übergänge sind unzulässig und müssen einen Fehler auslösen.
Insbesondere: `offen` → `verifiziert` oder `offen` → `geschlossen` ist nie erlaubt.

### Status eines Vorgangs
Abgeleitet aus den Positionen:
- Alle Positionen `geschlossen` → Vorgang `geschlossen`
- Mindestens eine Position `wartet_auf_information` → Vorgang `wartet_auf_information`
- Sonst, sobald eine Position aktiv ist → Vorgang `in_bearbeitung`

### Definition of Done je Fall
- **Access Issue:** Anforderer bestätigt, dass der Zugriff funktioniert. Die Bestätigung wird mit Name und Zeitpunkt gespeichert.
- **Leaver:** Jede Position wird einzeln geprüft und als `verifiziert` markiert. Der Vorgang wird NICHT geschlossen, solange eine Position offen ist. Ein Leaver ohne vollständige Verifikation bleibt offen, auch wenn alle Tickets geschlossen sind.

## 6. Pflichtfelder je Fall

### Access Issue
- Betroffene Person (Name oder Kennung)
- Betroffenes System (muss in der Matrix existieren)
- Beschreibung des Problems
- Zugriff funktioniert zuletzt nicht seit (Datum)
- Dringlichkeit (niedrig, mittel, hoch)

### Leaver
- Betroffene Person
- Austrittsdatum
- Liste der betroffenen Systeme (mindestens ein Matrix-Eintrag)
- Anforderer

Fehlende Pflichtfelder führen zu `wartet_auf_information`. Der Assistant fragt gezielt nach den fehlenden Feldern.

## 7. Ownership-Matrix
- Import als CSV mit Semikolon als Trennzeichen und UTF-8
- Spalten gemäß Abschnitt 4
- Validierung: Pflichtfelder gefüllt, `sla_stunden` positiv, `system_id` eindeutig
- Validierung der Pilot-Spalten (Abschnitt 13.5): `freigabe_kunde_noetig` ist ein Boolean, `uebergabepfad` ist gefüllt, `berechtigungsarten` ist optional und enthält kein Semikolon. Das Trennzeichen innerhalb der Zelle ist das Komma, da das Semikolon das Feldtrennzeichen der Datei ist.
- Fehlerhafte Zeilen werden mit Zeilennummer und Grund gemeldet. Ein Import mit Fehlern wird komplett abgelehnt.
- Jeder Import erzeugt einen Ereignis-Log-Eintrag mit Anzahl der Zeilen und Dateiname
- Die Matrix hat einen benannten Owner, der im Projekt festgelegt wird (offen)

## 8. Eskalation und Nachfassen (Phase 2, Vorbereitung in Phase 1)
Die Werte sind Standardvorgaben und in der Matrix oder Konfiguration überschreibbar:
- Erinnerung an den Owner nach 24 Stunden ohne Reaktion
- Eskalation Stufe 1 nach 3 Tagen ohne Umsetzung
- Eskalation Stufe 2 bei SLA-Verletzung
- Leaver-Vorgänge werden mit höherer Priorität eskaliert

In Phase 1 wird nur das Feld `sla_faellig_am` berechnet. Der Scheduler folgt in Phase 2.

Aufbewahrung: Vorgänge mit Personenbezug werden nach Ablauf der Aufbewahrungsfrist gelöscht oder anonymisiert. Die Frist ist offen und muss mit Datenschutz geklärt werden.

## 9. Ticketing-Adapter
Ein Interface mit folgenden Methoden:
- `create_ticket(vorgang) -> ticket_id`
- `update_status(ticket_id, status)`
- `get_ticket(ticket_id) -> TicketInfo`

Phase 1: nur `MockTicketAdapter`, der Aufrufe im Speicher hält und im Ereignis-Log protokolliert.
Die Statuszuordnung zu GoTo Resolve wird später in einem eigenen Mapping gepflegt, nicht im Domain-Code.

## 10. Leitplanken
- Der Assistant vergibt keine Berechtigungen.
- Statuswechsel nur über die State Machine.
- Jede Aktion wird im Ereignis-Log protokolliert.
- Keine personenbezogenen Daten über das Nötige hinaus.
- Keine Credentials im Repository.

## 11. Akzeptanzkriterien Phase 1
1. Ein Access-Issue ohne Pflichtfelder bleibt im Status `wartet_auf_information`, bis alle Felder vorhanden sind.
2. Ein Access-Issue kann nur über `umgesetzt` zu `verifiziert` führen.
3. Ein Leaver mit einer offenen Position lässt sich nicht schließen.
4. Ein Leaver mit allen Positionen `verifiziert` lässt sich schließen.
5. Eine fehlerhafte Matrix-CSV wird vollständig abgelehnt und meldet die Fehlerzeilen.
6. Jeder Statuswechsel erzeugt einen Ereignis-Log-Eintrag.
7. Alle Tests sind grün, `ruff check .` meldet keine Fehler.

## 12. Offene Punkte
- **Verifikation (Abschnitt 5, Übergang `umgesetzt` → `verifiziert`):** Wer darf verifizieren, und wie wird die Identität der verifizierenden Person geprüft? Die Regel „Anforderer oder Prüfung“ und die Identitätsprüfung sind noch nicht definiert. Bis zur Klärung speichert die Anwendung `verifiziert_durch` als Freitext, ohne Rollen- oder Identitätsprüfung.
- **Freigeber bei Apple Managed Accounts (Abschnitt 13.2):** Offen, ob dentsu Digital Delivery oder der Kunde die Freigabe erteilt. Wird nicht als Annahme umgesetzt. Der Wert von `freigabe_kunde_noetig` in der Beispiel-Matrix ist ein Platzhalter und keine Entscheidung.
- **Kanal und Empfänger der Erinnerung (Abschnitt 8, Phase 2):** Offen, ob Erinnerungen über Teams laufen und wer sie erhält (Owner, technischer Ansprechpartner oder Anforderer). In Phase 1 nicht umgesetzt.

## 13. Pilot (CE Hub)

### 13.1 Scope
Organisatorischer Scope ist der CE Hub. dentsu Connect, dentsu Digital Delivery und weitere
zentrale Plattformen gelten als Teil des CE-Hub-Ökosystems. Die Matrix wird im Pilot auf die
häufigsten Access-Themen fokussiert.

### 13.2 Pilot 1: Apple Managed Accounts (Fallart `access_issue`)
Pflichtfelder zusätzlich zu Abschnitt 6:
- Kontoart (persönliche Apple ID oder Managed Apple Account)
- Kunde bzw. Account
- Benötigte Rolle oder Berechtigung

Die Kontoart bestimmt den Ticketweg.

Freigabe: OFFEN, ob dentsu Digital Delivery oder der Kunde freigibt. Dies wird nicht als Annahme
umgesetzt und ist als offener Punkt in Abschnitt 12 geführt.

### 13.3 Pilot 2: Shared Mailbox Access (Fallart `access_issue`)
Pflichtfelder zusätzlich zu Abschnitt 6:
- Mailbox
- Berechtigungsart (`read`, `send_as`, `send_on_behalf`, mehrere möglich)
- Genehmiger, sofern bekannt

### 13.4 Schleifenregel
Ein in GoTo als gelöst markiertes Ticket setzt die Vorgangsposition NICHT auf `verifiziert`.
Sie bleibt auf `umgesetzt`, bis der Anforderer bestätigt.

Meldet der Anforderer, dass das Problem besteht, läuft der bestehende Übergang
`umgesetzt` → `bei_owner`. Das GoTo-Ticket wird wieder geöffnet und verweist auf denselben
Vorgang. Es entsteht kein neuer Vorgang.

Die Position bekommt ein Feld `wiedereroeffnungen` (Ganzzahl, Start 0), das bei jedem solchen
Übergang um 1 steigt. Es werden keine neuen Statuswerte eingeführt.

### 13.5 Matrix-Erweiterung (Abschnitt 4 und 7 angepasst)
Neue Spalten im Matrix-Eintrag:
- `freigabe_kunde_noetig` (Boolean, Pflicht)
- `uebergabepfad` (Text, Pflicht, wer übernimmt bei Nichtzuständigkeit)
- `berechtigungsarten` (Text, optional, Trennzeichen innerhalb der Zelle ist das Komma.
  Ein Semikolon ist nicht erlaubt, da es das Feldtrennzeichen der Datei ist.)

Die Beispieldatei `data/ownership_matrix.example.csv` enthält diese Spalten mit
Platzhalterwerten sowie je eine Zeile für Apple Managed Accounts und Shared Mailbox.

### 13.6 Nicht in Phase 1
- Kundenspezifische Berechtigungen, zum Beispiel Campaign Flow pro Kunde
- Erinnerungen über Teams
- Joiner-Ampel
- Pflichttrainings
