# PasswortGenerator

**Sprache / Language:** **Deutsch** | [English](README.en.md)

**Sichere Passwörter und Passphrasen für Windows und Linux – mit anpassbarem Glass-Design.**

[![Release](https://img.shields.io/github/v/release/TimBooH/Passwort-Generator?label=Version)](https://github.com/TimBooH/Passwort-Generator/releases/latest)
[![Linux](https://img.shields.io/github/actions/workflow/status/TimBooH/Passwort-Generator/build-and-release.yml?label=Linux)](https://github.com/TimBooH/Passwort-Generator/actions/workflows/build-and-release.yml)
[![Windows](https://img.shields.io/github/actions/workflow/status/TimBooH/Passwort-Generator/build-windows.yml?label=Windows)](https://github.com/TimBooH/Passwort-Generator/actions/workflows/build-windows.yml)

## Download

| Windows 10/11 (64-Bit) | Linux (x86_64, z. B. CachyOS) |
| --- | --- |
| [**Windows-Installer (.exe)**](https://github.com/TimBooH/Passwort-Generator/releases/download/v0.22.0/PasswortGenerator-Setup-x64.exe) | [**Linux-AppImage**](https://github.com/TimBooH/Passwort-Generator/releases/download/v0.22.0/PasswortGenerator-x86_64.AppImage) |

[Alle Versionen und Installationsskripte](https://github.com/TimBooH/Passwort-Generator/releases/latest)

## Vorschau

![Original-Screenshot des PasswortGenerators unter Linux mit Glass-Design](assets/screenshots/passwort-generator-live.png)

*Originalaufnahme der laufenden Linux-Version (Qt/PySide6) im neuen Ocean-Glass-Standarddesign. Das angezeigte Passwort wurde nur für die Vorschau zufällig generiert.*

## Funktionen

- **Passwörter:** 8–128 Zeichen, Profile und erweiterte Regeln für Mindestzahlen, Sonderzeichen und ausgeschlossene Zeichen.
- **Passphrasen:** 4–10 Wörter, deutsche oder englische Wortlisten unabhängig von der Programmsprache, Trennzeichen und optionale zweistellige Zufallszahl.
- **Standarddesign Ocean Glass:** Blau-cyanfarbene Navigation, gläserne Kacheln für **Optionen** und **Passwortlänge**, gut sichtbare Auswahlhäkchen, ein durchgehender Generieren-Button und ein fließender blauer Hintergrund. Die bisherigen Designs bleiben auswählbar.
- **Sprache:** Eigene Glaskachel **„Sprache“** direkt unter **„Erscheinungsbild“** in den Einstellungen; Deutsch/Englisch gilt weiterhin für das ganze Programm und wird gespeichert.
- **Update:** Direkt im Updater zwischen **Stable** und **Unstable** wechseln. Unstable-Testbuilds aktualisieren sich ohne ZIP-Downloads und bleiben separat von Stable installiert; Downloads werden mit SHA-256 geprüft. Versionsvergleich, Changelog und Rollback bleiben.
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

**Version 0.22.0 · Schritt 22 von 100 bis zur Vollversion 1.0.0.**
[Änderungen](RELEASE_NOTES.md) · [Releases](https://github.com/TimBooH/Passwort-Generator/releases)

*Made by Jon Bovi*
