# PasswortGenerator v0.01.0 – Start der 100-Schritte-Entwicklung

Mit diesem Release beginnt ein neues, bewusst kleinschrittiges Versionsschema. **Version 1.0.0 ist künftig die erste Vollversion.**

## Neues Versionsschema

- `0.01.0` – Entwicklungsschritt **1 von 100** (diese Version)
- `0.02.0` bis `0.99.0` – Entwicklungsschritte 2–99
- `1.0.0` – Schritt 100, **erste Vollversion**
- Korrektur-Releases erhöhen nur die letzte Stelle, etwa `0.01.1`
- Entwicklungsfortschritt wird in der App neben der Versionsnummer angezeigt

## Übergang von den bisherigen Releases

Die bereits veröffentlichten Versionen `v1.2.0` bis `v1.5.1` gehören zum **alten** Nummerierungssystem und bleiben als Historie erhalten. Bei einem Wechsel auf die neue Reihe kann die automatische Updateprüfung einer alten App `0.01.0` als niedrigere Version behandeln. Deshalb muss **dieser eine Umstieg** über den [aktuellen Installer](https://github.com/TimBooH/Passwort-Generator/releases/latest) erfolgen. Die Installation sichert wie bisher die unmittelbar vorherige AppImage-Version als `previous`.

Innerhalb der neuen `0.xx`-Reihe ist der automatische Updatevergleich angepasst; ältere historische `1.x`-Releases werden nicht als neuer angezeigt.

## Unverändert

- Sichere lokale Passwortgenerierung
- Skalierbare Glossy-Glas-Kacheln und frei auswählbare Hintergrundbilder
- SHA-256-Prüfung der AppImage-Updates mit automatischem Neustart
- Zwei installierte AppImage-Stände: aktuell und `previous`
- Lokale Crash-Logs mit Version und Zeitstempel
- Beschleunigter GitHub-Actions-Workflow für Releases
