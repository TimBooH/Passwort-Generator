# PasswortGenerator

**Sichere Passwörter und Passphrasen für Windows und Linux – mit anpassbarem Glass-Design.**

[![Release](https://img.shields.io/github/v/release/TimBooH/Passwort-Generator?label=Version)](https://github.com/TimBooH/Passwort-Generator/releases/latest)
[![Linux](https://img.shields.io/github/actions/workflow/status/TimBooH/Passwort-Generator/build-and-release.yml?label=Linux)](https://github.com/TimBooH/Passwort-Generator/actions/workflows/build-and-release.yml)
[![Windows](https://img.shields.io/github/actions/workflow/status/TimBooH/Passwort-Generator/build-windows.yml?label=Windows)](https://github.com/TimBooH/Passwort-Generator/actions/workflows/build-windows.yml)

## Download

| Windows 10/11 (64-Bit) | Linux (x86_64, z. B. CachyOS) |
| --- | --- |
| [**Windows-Installer (.exe)**](https://github.com/TimBooH/Passwort-Generator/releases/download/v0.16.0/PasswortGenerator-Setup-x64.exe) | [**Linux-AppImage**](https://github.com/TimBooH/Passwort-Generator/releases/download/v0.16.0/PasswortGenerator-x86_64.AppImage) |

[Alle Versionen und Installationsskripte](https://github.com/TimBooH/Passwort-Generator/releases/latest)

## Vorschau

![PasswortGenerator mit Glass-Oberfläche](assets/screenshots/passwort-generator.png)

## Funktionen

- **Passwörter:** 8–128 Zeichen, wählbare Zeichengruppen und Stärkeanzeige.
- **Passphrasen:** 4–10 Wörter, wählbare Trennzeichen und optional eine zufällige zweistellige Zahl.
- **Glass-Design:** verschiedene Farbschemas, automatische Akzentfarbe und eigene Hintergrundbilder.
- **Update:** automatische Prüfung beim Start und alle 2 Stunden; Versionshistorie und Änderungen im Changelog.
- **Bedienung:** Passwortverlauf während der Sitzung, grafische Anleitung und gespeicherte Fenstergröße/-position.

Passwörter werden lokal mit Python `secrets` erzeugt, nicht an einen Server gesendet und nicht dauerhaft gespeichert.

## Installation

**Windows:** Installer herunterladen und starten. Die Installation erfolgt mit Administratorbestätigung unter `C:\Program Files\PasswortGenerator`. Der Installer ist nicht digital signiert; Windows SmartScreen kann eine Warnung anzeigen.

**Linux mit Menüeintrag:** `install.sh` aus dem [aktuellen Release](https://github.com/TimBooH/Passwort-Generator/releases/latest) herunterladen und im Downloadordner ausführen:

```bash
bash install.sh
```

**Linux ohne Installation:** Heruntergeladenes AppImage direkt starten:

```bash
chmod +x PasswortGenerator-x86_64.AppImage
./PasswortGenerator-x86_64.AppImage
```

Updates werden **nur nach Bestätigung** installiert. Unter Linux bleibt bei einer regulären Menü-Installation die vorherige AppImage-Version als Sicherung erhalten. Für die Updateprüfung wird eine Internetverbindung benötigt, nicht für die Passworterzeugung.

## Entwicklung

Das Projekt basiert auf **Python und PySide6 (Qt 6)**. Lokal starten und testen:

```bash
python -m pip install -r requirements.txt
python main.py
python -m unittest discover -s tests -v
```

Windows-Installer und Linux-AppImage werden über [GitHub Actions](https://github.com/TimBooH/Passwort-Generator/actions) erstellt.

**Version 0.16.0 · Schritt 16 von 100 bis zur Vollversion 1.0.0.**
[Änderungen](RELEASE_NOTES.md) · [Releases](https://github.com/TimBooH/Passwort-Generator/releases)

*Made by Jon Bovi*
