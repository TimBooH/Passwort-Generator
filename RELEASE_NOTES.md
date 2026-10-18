# PasswortGenerator v1.2.0

Die Linux-Version zieht in das neue Repository **TimBooH/Passwort-Generator** um.

## Neu
- **Benutzerinstallation** mit `install.sh`: KDE-/CachyOS-Menüeintrag mit Icon, ohne Root-Rechte.
- **Update herunterladen** lädt neue AppImages direkt aus den GitHub Releases dieses Repositorys.
- Bei Installation über `install.sh` wird die installierte Datei nach Download und SHA-256-Prüfung atomar ersetzt (neuer Start notwendig).
- Ohne Benutzerinstallation landet das neue AppImage im Downloadordner.
- Automatische und manuelle Updateprüfung, Fortschrittsanzeige und Fehlermeldungen.
- Farbauswahl für Hintergrund und Text, auf Wunsch eigene Farben, Speicherung durch Qt.
- Überarbeitetes README und Tests, automatisierte Builds und Release-Veröffentlichung.

## Installieren
Lade `install.sh` herunter und starte `bash install.sh`. Der Installer lädt die neueste AppImage-Version und erstellt einen Eintrag im Anwendungsmenü.

Alternativ das AppImage direkt starten: `chmod +x PasswortGenerator-x86_64.AppImage && ./PasswortGenerator-x86_64.AppImage`.
