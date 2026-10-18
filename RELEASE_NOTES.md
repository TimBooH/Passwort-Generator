# PasswortGenerator v1.4.0 – Stabilität, Skalierung und Hintergrundbilder

Dieses Update behebt mehrere potenzielle Qt-Absturzursachen und erweitert die Design-Einstellungen.

## Neu
- Hintergrundbild aus lokaler PNG/JPG/WEBP/BMP-Datei auswählen und wieder entfernen
- Sechs Darstellungsmodi: **Ausfüllen, Einpassen, Gestreckt, Zentriert, Originalgröße, Gekachelt**
- Die Auswahl des Bilds und der Modus werden über Qt QSettings gespeichert
- Zentrierter, maximal 940 px breiter Inhaltsbereich für große Monitore und bessere Darstellung bei schmalen Fenstern
- Lokale Fehlerprotokollierung: `~/.local/state/passwort-generator/crash.log`

## Stabilität und Performance
- Ressourcenintensive `QGraphicsDropShadowEffect`-Instanzen der Kacheln entfernt und durch direktes, leichtgewichtiges Zeichnen ersetzt
- Der Glas-Deckkraft-Regler aktualisiert nur die gezeichneten Kacheln statt bei jeder Bewegung das komplette Stylesheet zu setzen
- Bilddateien werden mit Größenbegrenzung einmalig dekodiert, nicht bei jedem Fenster-Resize
- Zusätzliche Tests für Bildausschnitte, Einstellungen, Farbauswahl und zahlreiche Fenstergrößen

## Update
In der installierten Version: **Auf Updates prüfen → Update herunterladen**, danach die App über das KDE-Menü neu öffnen. Alternativ das AppImage unter Assets herunterladen.

**Hinweis:** Ob damit alle Absturzursachen auf jeder CachyOS-/KDE-Konfiguration behoben sind, kann erst ein Test auf der jeweiligen Maschine bestätigen. Bitte im Fehlerfall das lokale crash.log prüfen.
