# PasswortGenerator v1.5.1 – Schnellere GitHub-Releases

Dieses Wartungsrelease verbessert den Build- und Veröffentlichungsprozess. An der Bedienung und Passwortgenerierung ändert sich nichts.

## Optimierungen
- Releases nur noch bei neuer Versionsnummer statt bei jedem einzelnen Commit
- Ein gemeinsamer GitHub-Actions-Job für Tests, Linux-AppImage und Veröffentlichung
- Direkte Veröffentlichung, ohne Zwischen-Upload und -Download des AppImages zwischen zwei Jobs
- Schlankeres Qt-Laufzeitpaket **PySide6-Essentials** statt dem großen PySide6-Metapaket (ohne ungenutzte WebEngine- und PDF-Module)
- GitHub pip-Cache für schnellere wiederholte Installationen
- Bestehende Releases werden vor der Installation von Abhängigkeiten erkannt und übersprungen
- Parallele Builds auf demselben Branch werden zusammengefasst, ältere Läufe abgebrochen
- Keine unnötigen vollständigen apt-Updates oder PyInstaller-Clean-Builds bei jedem Release
- Bestehende Sicherheits- und GUI-Tests bleiben Bestandteil des Releases

## Weiterhin enthalten
- Automatischer App-Neustart nach SHA-256-geprüftem Update
- Sicherung als `PasswortGenerator-previous.AppImage`
- Responsive Glas-Kacheln, auswählbare Hintergrundbilder und lokale Crash-Logs

## Veröffentlichung
Neue Versionen werden als einzelner Commit mit aktualisierter `version.py` und `RELEASE_NOTES.md` erstellt. Automatische Builds starten nur bei Änderungen an der Versionsdatei, oder manuell über GitHub Actions.
