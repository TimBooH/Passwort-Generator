# PasswortGenerator

**Sprache / Language:** **Deutsch** | [English](README.en.md)

**Sichere Passwörter und Passphrasen für Windows und Linux – mit anpassbarem Glass-Design.**

[![Release](https://img.shields.io/github/v/release/TimBooH/Passwort-Generator?label=Version)](https://github.com/TimBooH/Passwort-Generator/releases/latest)
[![Linux](https://img.shields.io/github/actions/workflow/status/TimBooH/Passwort-Generator/build-and-release.yml?label=Linux)](https://github.com/TimBooH/Passwort-Generator/actions/workflows/build-and-release.yml)
[![Windows](https://img.shields.io/github/actions/workflow/status/TimBooH/Passwort-Generator/build-windows.yml?label=Windows)](https://github.com/TimBooH/Passwort-Generator/actions/workflows/build-windows.yml)

## Download

| Windows 10/11 (64-Bit) | Linux (x86_64, z. B. CachyOS) |
| --- | --- |
| [**Windows-Installer (.exe)**](https://github.com/TimBooH/Passwort-Generator/releases/download/v0.20.1/PasswortGenerator-Setup-x64.exe) | [**Linux-AppImage**](https://github.com/TimBooH/Passwort-Generator/releases/download/v0.20.1/PasswortGenerator-x86_64.AppImage) |

[Alle Versionen und Installationsskripte](https://github.com/TimBooH/Passwort-Generator/releases/latest)

## Vorschau

![PasswortGenerator mit Glass-Oberfläche](assets/screenshots/passwort-generator.png)

## Funktionen

- **Passwörter:** 8–128 Zeichen, Profile und erweiterte Regeln für Mindestzahlen, Sonderzeichen und ausgeschlossene Zeichen.
- **Passphrasen:** 4–10 Wörter, deutsche oder englische Wortlisten unabhängig von der Programmsprache, Trennzeichen und optionale zweistellige Zufallszahl.
- **Glass-Design:** optimierte Lichtkanten, Fokusmarkierungen, ein kompakter glänzender Generieren-Button, Farbschemas und eigene Hintergrundbilder.
- **Sprache:** Eigene Glaskachel **„Sprache“** direkt unter **„Erscheinungsbild“** in den Einstellungen; Deutsch/Englisch gilt weiterhin für das ganze Programm und wird gespeichert.
- **Update:** automatische Prüfung, Versionsvergleich und Changelog; ältere Version nach Bestätigung wiederherstellen (Linux: AppImage-Sicherung, Windows: geprüfter offizieller Installer).
- **Sicherheit:** Stärkeanalyse mit Entropieschätzung, Privatsphäre-Modus beim Fensterwechsel und optionales Leeren der Zwischenablage nach 30, 60 oder 120 Sekunden.
- **Bedienung:** Tastenkombinationen (Strg+G, Strg+Umschalt+C, Strg+H, Strg+1–4), Sitzungsverlauf, grafische Anleitung und gespeicherte Fenstergröße/-position. Navigation: Passwort → Update → Einstellungen → Info.

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

**Version 0.20.1 · Schritt 20 von 100 bis zur Vollversion 1.0.0.**
[Änderungen](RELEASE_NOTES.md) · [Releases](https://github.com/TimBooH/Passwort-Generator/releases)

*Made by Jon Bovi*
