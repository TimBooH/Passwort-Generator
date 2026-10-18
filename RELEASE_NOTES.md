# PasswortGenerator v0.03.0 – Übersichtliche Reiter-Navigation

**Entwicklungsschritt 3 von 100** auf dem Weg zu v1.0.0.

## Neues Oberflächendesign

- Drei Reiter oben links: **Passwort**, **Einstellungen** und **Updates**
- **Passwort:** Passwort erstellen, Länge und Zeichengruppen festlegen, kopieren
- **Einstellungen:** Design & Farben und alle Einstellungen für Hintergrundbilder
- **Updates:** Versionsstatus, Updateprüfung, Installation mit Neustart und Crash-Log
- Die glänzenden Glas-Kacheln und das Hintergrundbild bleiben auf allen Reitern erhalten
- Responsive Größenänderungen und bestehende Farb-/Bildeinstellungen funktionieren weiterhin
- Die Statusanzeige bleibt beim Wechsel zwischen den Reitern sichtbar
- GUI-Tests prüfen Tabwechsel, Bedienbarkeit und Fenster-Skalierung

## Unverändert

- Sichere lokale Passwortgenerierung
- Updates über GitHub mit SHA-256-Prüfung und automatischem Neustart
- Aktuelle und vorherige AppImage-Version werden aufbewahrt
- Lokaler Crash-Log mit Zeitstempel und Versionsnummer
