# 🔐 PasswortGenerator

**Ein sicherer Passwortgenerator für Linux – im modernen Glassmorphism-Look, mit Farbauswahl, Updateprüfung und Startmenü-Installation.**

[![Linux AppImage](https://img.shields.io/badge/Linux-AppImage-238636?logo=linux&logoColor=white)](https://github.com/TimBooH/Passwort-Generator/releases/latest)
[![Release](https://img.shields.io/github/v/release/TimBooH/Passwort-Generator?label=Version)](https://github.com/TimBooH/Passwort-Generator/releases/latest)
[![Build & Release](https://github.com/TimBooH/Passwort-Generator/actions/workflows/build-and-release.yml/badge.svg)](https://github.com/TimBooH/Passwort-Generator/actions/workflows/build-and-release.yml)

Der PasswortGenerator ist eine grafische Desktop-Anwendung auf Basis von **Python** und **PySide6 (Qt 6)**. Die Passwörter werden ausschließlich lokal mit dem kryptografisch sicheren Python-Modul `secrets` erzeugt.

## ✨ Funktionen

- Sichere Passwörter mit **8 bis 128 Zeichen** erzeugen
- **Kleinbuchstaben**, **Großbuchstaben**, **Zahlen** und **Sonderzeichen** auswählen
- Ähnliche Zeichen wie `I`, `l`, `1`, `O` und `0` ausschließen
- Jede aktivierte Zeichengruppe ist im Passwort mindestens einmal enthalten
- Passwort auf Knopfdruck in die Zwischenablage kopieren
- **Glassmorphism-Oberfläche** mit milchig-transparenten Karten, Lichtreflexen, weichen Schatten und abgerundeten Elementen
- **Glas-Deckkraft** mit einem Schieberegler anpassen (30–85 %)
- Unterschiedliche **Hintergrund- und Textfarben** wählen oder eine eigene Farbe einstellen
- Farben werden gespeichert und beim nächsten Start wiederhergestellt
- **Automatische und manuelle Updateprüfung** über GitHub Releases
- **Update herunterladen:** die neue Version wird direkt von GitHub geladen und per SHA-256 geprüft
- **Linux-Installation mit Menüeintrag** (z. B. CachyOS/KDE Plasma), ohne `sudo`

## 📥 Download

**[➡️ Neueste Version und Installer auf GitHub Releases](https://github.com/TimBooH/Passwort-Generator/releases/latest)**

Unter **Assets** findest du:

| Datei | Verwendung |
| --- | --- |
| `PasswortGenerator-x86_64.AppImage` | Direkt ausführbare Linux-App |
| `install.sh` | Installiert die App mit KDE-/Desktop-Menüeintrag |
| `uninstall.sh` | Entfernt die App und den Menüeintrag |
| `SHA256SUMS` | Prüfsumme für die AppImage-Datei |

## 🖥️ Installation mit Anwendungsmenü (CachyOS / KDE Plasma)

1. Lade auf der [Release-Seite](https://github.com/TimBooH/Passwort-Generator/releases/latest) die Datei **`install.sh`** herunter.
2. Öffne das Terminal im Ordner mit der Datei, zum Beispiel `~/Downloads`.
3. Starte:

   ```bash
   bash install.sh
   ```

Das Skript lädt die **neueste AppImage-Version** von GitHub, überprüft die SHA-256-Prüfsumme und richtet die Anwendung für deinen Benutzer ein.

Anschließend findest du **PasswortGenerator** im KDE-Anwendungsmenü. Du kannst den Eintrag auch an die Taskleiste anheften.

Die Installation verwendet **kein `sudo`** und legt die Dateien hier ab:

| Datei | Speicherort |
| --- | --- |
| AppImage | `~/.local/opt/passwort-generator/PasswortGenerator.AppImage` |
| Menüeintrag | `~/.local/share/applications/de.timbooh.passwortgenerator.desktop` |
| Symbol | `~/.local/share/icons/hicolor/scalable/apps/de.timbooh.passwortgenerator.svg` |

Falls das AppImage bereits heruntergeladen wurde, kannst du es auch ohne Netzwerkverbindung installieren (mit der passenden Datei):

```bash
bash install.sh --file ./PasswortGenerator-x86_64.AppImage
```

## ⚡ AppImage ohne Installation starten

```bash
chmod +x PasswortGenerator-x86_64.AppImage
./PasswortGenerator-x86_64.AppImage
```

Voraussetzung: **64-Bit-Linux (x86_64)**. Unter manchen Distributionen wird eine kompatible **FUSE-2-Laufzeit** benötigt.

## 🔄 Wie funktioniert „Update herunterladen“?

Der PasswortGenerator prüft beim Start die neueste veröffentlichte Version unter **`TimBooH/Passwort-Generator`**. Die Prüfung ist auch manuell über **„Auf Updates prüfen“** möglich.

Wenn eine neue Version verfügbar ist:

1. Die App zeigt die neue Versionsnummer an.
2. Ein Klick auf **„Update herunterladen“** startet den Download direkt vom aktuellen GitHub-Release. Der Fortschritt wird angezeigt.
3. Die heruntergeladene Datei wird anhand der von GitHub gelieferten **SHA-256-Prüfsumme** und Dateigröße geprüft.
4. **Bei einer Installation mit `install.sh`:** Die installierte AppImage-Datei wird sicher ersetzt. **App schließen und neu über das Menü starten**, um die neue Version zu verwenden.
5. **Bei einem allein gestarteten AppImage:** Die neue Version wird in deinen Downloadordner gespeichert. Du kannst sie direkt starten oder über `install.sh --file` installieren.

Es werden **keine Updates ungefragt installiert**. Nur die Versionsprüfung erfolgt automatisch; den eigentlichen Download startest du selbst.

## 🎨 Design ändern

Unter **„Design & Farben“** gibt es verschiedene Vorlagen für Hintergrund und Text sowie einen Farbwähler für eigene Farben. Der neue **„Glas-Deckkraft“**-Regler verändert, wie stark die halbtransparenten Milchglas-Karten den farbigen Hintergrund durchscheinen lassen. Die Oberfläche hat zusätzlich sanfte Farbreflexe, abgerundete Ecken und weiche Schatten. Farben und Glas-Deckkraft werden lokal über Qt `QSettings` gespeichert. Achte bei eigenen Kombinationen auf guten Kontrast.

**Hinweis:** Das Design erzeugt den Glas-Look innerhalb des App-Fensters. Eine echte Unschärfe des *Desktops hinter dem Fenster* hängt vom KDE/KWin-Compositor ab und wird nicht vorausgesetzt.

## 🧑‍💻 Aus dem Quellcode starten

Voraussetzungen: Python 3.11 oder neuer und ein Linux-Desktop mit Qt-Unterstützung.

```bash
git clone https://github.com/TimBooH/Passwort-Generator.git
cd Passwort-Generator
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Tests ausführen:

```bash
python -m unittest discover -s tests -v
```

## 🗑️ Deinstallation

Lade `uninstall.sh` von den [Releases](https://github.com/TimBooH/Passwort-Generator/releases/latest) herunter und führe aus:

```bash
bash uninstall.sh
```

Die App und ihr Menüeintrag werden entfernt. Die gespeicherten Farbeingaben bleiben bei Bedarf erhalten.

## 🛠️ Technik & Release-Ablauf

| Bereich | Technologie |
| --- | --- |
| Benutzeroberfläche | PySide6 / Qt 6 |
| Passworterzeugung | Python `secrets` / `SystemRandom` |
| Farbauswahl | Qt `QColorDialog` & `QSettings` |
| Glasdesign | Qt `QPainter`, halbtransparente Qt-Stylesheets und Schatten |
| Updates | GitHub Releases API via Qt `QNetworkAccessManager` |
| Verifizierung | SHA-256 + erwartete Dateigröße |
| Build | PyInstaller und AppImageKit |
| Release | GitHub Actions |

Jeder Push auf `main` startet Tests und den Linux-AppImage-Build. **Wenn die Version in `version.py` neu ist**, wird nach erfolgreichem Build automatisch ein Release mit AppImage, Installer, Deinstaller und Prüfsumme erstellt.

Für neue Versionen: `APP_VERSION` in `version.py` erhöhen, Änderungen testen, committen und nach `main` pushen.

## 🔒 Sicherheit und Privatsphäre

- Passwortgenerierung erfolgt lokal, ohne Übertragung an Server.
- Die App speichert generierte Passwörter nicht dauerhaft.
- Die optionale Updateprüfung ruft öffentliche Release-Metadaten auf GitHub ab.
- Downloads kommen aus den Releases dieses Repositories und werden anhand des GitHub-SHA-256-Digests geprüft.
- **Hinweis:** Kopierte Passwörter sind in der Systemzwischenablage sichtbar, bis deren Inhalt überschrieben oder gelöscht wird.

## 📁 Repository-Struktur

```text
Passwort-Generator/
├── main.py
├── password_core.py
├── glass_ui.py
├── version.py
├── requirements.txt
├── install.sh
├── uninstall.sh
├── RELEASE_NOTES.md
├── assets/
│   └── de.timbooh.passwortgenerator.svg
├── tests/
│   └── test_password_core.py
└── .github/workflows/
    └── build-and-release.yml
```

**Projekt:** [TimBooH/Passwort-Generator](https://github.com/TimBooH/Passwort-Generator) · **Downloads:** [Releases](https://github.com/TimBooH/Passwort-Generator/releases)
