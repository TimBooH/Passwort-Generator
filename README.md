# PasswortGenerator

**Ein moderner Passwortgenerator für Linux mit anpassbarer Glasoberfläche, lokalen Hintergrundbildern und integrierter Updatefunktion.**

[![Latest Release](https://img.shields.io/github/v/release/TimBooH/Passwort-Generator?label=Release&style=flat-square)](https://github.com/TimBooH/Passwort-Generator/releases/latest)
[![Linux](https://img.shields.io/badge/Plattform-Linux%20x86__64-3B82F6?style=flat-square&logo=linux&logoColor=white)](https://github.com/TimBooH/Passwort-Generator/releases/latest)
[![Build & Release](https://img.shields.io/github/actions/workflow/status/TimBooH/Passwort-Generator/build-and-release.yml?branch=main&label=Build%20%26%20Release&style=flat-square)](https://github.com/TimBooH/Passwort-Generator/actions/workflows/build-and-release.yml)

PasswortGenerator ist eine Desktop-Anwendung für Linux, entwickelt mit **Python und Qt 6 (PySide6)**. Die Passworterzeugung erfolgt lokal mit dem kryptografisch sicheren Python-Modul `secrets`. Eine Internetverbindung ist dafür nicht erforderlich; sie wird lediglich für die optionale Updateprüfung und den Download neuer Versionen benötigt.

**[Neueste Version herunterladen](https://github.com/TimBooH/Passwort-Generator/releases/latest)** · [Installationsanleitung](#installation) · [Updates](#updates) · [Fehlerdiagnose](#fehlerdiagnose)

---

## Funktionen

| Bereich | Möglichkeiten |
| --- | --- |
| **Passwörter** | 8–128 Zeichen; Klein- und Großbuchstaben, Zahlen und Sonderzeichen |
| **Passphrasen** | 4–10 lokal zufällig erzeugte zusammengesetzte Wörter, jeweils 1.024 Möglichkeiten |
| **Zeichenauswahl** | Ähnliche Zeichen optional ausschließen; jede aktivierte Zeichengruppe berücksichtigen |
| **Bedienung** | Längenregler, Passwort anzeigen/verbergen, kopieren und erneut erzeugen |
| **Verlauf** | Letzte 20 Ergebnisse nur während der Sitzung; kopieren oder löschen |
| **Stärke** | Geschätzte Entropie und visuelle Stärkeanzeige |
| **Design** | Farbschemas (Glass Dark, Glass Light, Neon Blue, Violet Glass, Forest Glass), automatische Akzentfarben und eigene Farben |
| **Hintergrundbilder** | Eigene PNG-, JPG-, WEBP- oder BMP-Dateien mit sechs Darstellungsmodi |
| **Updates** | GitHub-Releaseprüfung mit Changelog und bis zu 100 früheren Releases, SHA-256-Verifizierung und Neustart |
| **Diagnose** | Lokales Crash-Protokoll mit Zeitstempel, Versionsnummer und verfügbaren Fehlerdetails |
| **Info** | „Made by Jon Bovi“ und eine integrierte Schritt-für-Schritt-Anleitung |

Der PasswortGenerator wurde nach dem futuristischen dunkelblauen Designentwurf umgestaltet: Schloss-Symbol, blaue Neon-Umrandungen, Passwort/Passphrase-Umschalter, Stärkeanzeige, Längenregler und eine große Generieren-Taste. Die Reiter **Passwort**, **Einstellungen** und **Updates** bleiben oben links erreichbar. Das Einstellungen-Symbol im Kopf führt ebenfalls zu Design & Farben.

## Versionsplan: 100 Schritte bis Version 1.0

Das Projekt verwendet ab sofort ein Entwicklungsschema mit **100 Meilensteinen bis zur ersten Vollversion**:

| Meilenstein | Version | Status |
| --- | --- | --- |
| **1 von 100** | `0.01.0` | Beginn der neuen Entwicklungsreihe |
| **2 von 100** | `0.02.0` | Glas-Deckkraft-Regler entfernt |
| **3 von 100** | `0.03.0` | Drei Reiter |
| **4 von 100** | `0.04.0` | Neon-Design und Passwort/Passphrase |
| **5 von 100** | **`0.05.0`** | **Aktueller Stand: Farbschemas, Changelog und Anleitung** |
| **50 von 100** | `0.50.0` | Halbzeit |
| **99 von 100** | `0.99.0` | Letzter Entwicklungsschritt |
| **100 von 100** | **`1.0.0`** | **Erste Vollversion** |

Die dritte Stelle ist für kleine Korrekturen innerhalb eines Schritts reserviert (z. B. `0.07.1`). Ein Meilenstein wird nur erhöht, wenn bewusst der nächste Entwicklungsschritt veröffentlicht wird.

**Wichtiger einmaliger Umstieg:** Die bisherigen Versionen `1.2.0` bis `1.5.1` stammen aus dem alten Nummerierungssystem und bleiben als historische Releases erhalten. Weil die neue Reihe wieder bei `0.01.0` beginnt, können die alten Apps diese Version beim automatischen Update als niedriger einstufen. **Bitte `0.01.0` einmal über den aktuellen Installer von GitHub installieren.** Anschließend funktionieren die Updates innerhalb der neuen Versionsreihe wieder regulär. Die Installer-Sicherung der vorherigen AppImage-Version bleibt erhalten.

## Download

Die aktuelle Linux-Version findest du unter **[GitHub Releases](https://github.com/TimBooH/Passwort-Generator/releases/latest)**.

| Datei | Zweck |
| --- | --- |
| `PasswortGenerator-x86_64.AppImage` | Portable Linux-Anwendung |
| `install.sh` | Benutzerinstallation mit Anwendungsmenü-Eintrag |
| `uninstall.sh` | Entfernt die installierte Anwendung und den Menüeintrag |
| `SHA256SUMS` | SHA-256-Prüfsumme des AppImages |

**Systemanforderungen:** Linux auf x86_64-Basis, beispielsweise CachyOS mit KDE Plasma. Für die Ausführung von AppImages kann je nach Distribution eine kompatible FUSE-Laufzeit erforderlich sein.

## Installation

### Empfohlen: Installation mit Menüeintrag

1. Lade `install.sh` von der [Release-Seite](https://github.com/TimBooH/Passwort-Generator/releases/latest) herunter.
2. Öffne ein Terminal im Downloadordner.
3. Führe den Installer aus:

   ```bash
   bash install.sh
   ```

Das Skript lädt das aktuelle AppImage herunter, prüft die veröffentlichte SHA-256-Prüfsumme und erstellt einen Eintrag im Linux-Anwendungsmenü. **Für die Benutzerinstallation ist kein `sudo` nötig.** Danach kannst du PasswortGenerator über das KDE-Menü öffnen und an die Taskleiste anheften.

**Bereits heruntergeladenes AppImage installieren:**

```bash
bash install.sh --file ./PasswortGenerator-x86_64.AppImage
```

Bei `--file` wird die angegebene lokale Datei verwendet. Lade sie nur aus einer vertrauenswürdigen Quelle herunter; die Online-Prüfsummenprüfung des Installers findet bei diesem Aufruf nicht statt.

### Portable Nutzung ohne Installation

Lade das AppImage herunter und starte es im entsprechenden Verzeichnis:

```bash
chmod +x PasswortGenerator-x86_64.AppImage
./PasswortGenerator-x86_64.AppImage
```

Hierbei wird kein Anwendungsmenü-Eintrag erstellt.

### Installationspfade

| Komponente | Pfad |
| --- | --- |
| Aktuelle Version | `~/.local/opt/passwort-generator/PasswortGenerator.AppImage` |
| Vorherige Version | `~/.local/opt/passwort-generator/PasswortGenerator-previous.AppImage` |
| Menüeintrag | `~/.local/share/applications/de.timbooh.passwortgenerator.desktop` |
| Programmsymbol | `~/.local/share/icons/hicolor/scalable/apps/de.timbooh.passwortgenerator.svg` |

Die Datei für die vorherige Version wird erst angelegt, wenn eine vorhandene Installation aktualisiert wird.

## Updates

PasswortGenerator prüft beim Start die neueste Veröffentlichung im Repository [TimBooH/Passwort-Generator](https://github.com/TimBooH/Passwort-Generator). Im eigenen Reiter **„Updates“** kannst du die Prüfung über **„Auf Updates prüfen“** jederzeit wiederholen.

### Changelog und frühere Versionen

Der Update-Reiter enthält einen **Changelog** mit den Änderungen der ausgewählten Version und eine **Versionshistorie**. Beim ersten Öffnen des Reiters lädt die App über die GitHub-API bis zu **100 veröffentlichte Releases**. Klicke auf eine Version, um ihre offiziellen Release-Notizen anzuzeigen. Über **„Versionshistorie laden“** kannst du die Liste aktualisieren; **„Release auf GitHub öffnen“** führt zur jeweiligen Release-Seite. Auch ältere Versionen aus dem früheren 1.x-Nummerierungssystem sind in der Liste sichtbar, sofern sie in den letzten 100 Releases enthalten sind.

**Wichtig:** Die Liste dient der Information; ein Anklicken installiert **keine** ältere Version. Ohne Internetverbindung bleibt die Passworterzeugung nutzbar, die Online-Versionshistorie ist dann nicht abrufbar.

1. Wenn eine neue Version verfügbar ist, wähle **„Update installieren & neu starten“**.
2. Das AppImage wird heruntergeladen und anhand der veröffentlichten **Dateigröße und SHA-256-Prüfsumme** überprüft.
3. Bei einer Menü-Installation wird die bisherige Version als `PasswortGenerator-previous.AppImage` gesichert und das aktuelle AppImage ersetzt.
4. Nach erfolgreichem Download und Austausch startet die neue Version automatisch.

**Versionsverwaltung:** Im Installationsordner werden die aktuelle und die unmittelbar vorherige AppImage-Version aufbewahrt. Ältere, zur Anwendung gehörende Versionen werden dort entfernt.

**Portable AppImages:** Wird das Programm ohne Installation gestartet, landet die heruntergeladene Version im Downloadordner und wird von dort neu gestartet. Die `previous`-Sicherung gilt für die reguläre Menü-Installation.

Die App prüft optional auf Updates, **installiert sie aber nur nach deinem Klick**.

## Oberfläche und Hintergrundbilder

Die Navigation befindet sich **oben links** und bietet drei Bereiche:

| Reiter | Inhalt |
| --- | --- |
| **Passwort** | Passwort/Passphrase, Stärkebalken, Längenregler, Zeichengruppen, Anzeigen, Verlauf und Info inklusive Anleitung |
| **Einstellungen** | Design & Farben, eigene Hintergrundbilder und Bilddarstellung |
| **Updates** | Changelog, frühere Versionen, Updateprüfung, Installation und Crash-Log |

Wechsle einfach zwischen den Reitern. Die eingestellten Farben und Hintergrundbilder gelten für alle drei Bereiche.

Im Reiter **„Einstellungen“** unter **„Design & Farben“** wählst du ein **Farbschema**: **Neon Blue**, **Glass Dark**, **Glass Light**, **Violet Glass** oder **Forest Glass**. Die App wählt passende Hintergrund- und Textfarben; die **Akzentfarbe wird automatisch aus dem Hintergrund abgeleitet** und färbt Buttons, Umrandungen, Regler und Schaltkreise passend ein. Bei manuell ausgewählten Hintergrund- oder Textfarben wechselt die Auswahl automatisch zu **„Eigene Farben“**. Das ausgewählte Schema wird lokal gespeichert. Die Glas-Kacheln verwenden eine feste Transparenz ohne Deckkraft-Regler. Die Glasoptik wird innerhalb des Programmfensters dargestellt; eine tatsächliche Unschärfe des Desktops hinter dem Fenster ist nicht erforderlich.

Mit **„Bild auswählen …“** kannst du ein eigenes Hintergrundbild laden und dessen Darstellung festlegen:

| Modus | Darstellung |
| --- | --- |
| **Ausfüllen** | Füllt den verfügbaren Bereich proportional; Bildränder können abgeschnitten werden |
| **Einpassen** | Zeigt das gesamte Bild proportional mit möglichen freien Rändern |
| **Gestreckt** | Passt Breite und Höhe unabhängig an; das Bild kann verzerrt werden |
| **Zentriert (100 %)** | Platziert das Bild ohne weitere Skalierung mittig |
| **Original (links oben)** | Platziert das Bild ohne weitere Skalierung oben links |
| **Gekachelt** | Wiederholt das Bild als Muster |

Mit **„Bild entfernen“** wechselst du zum farbigen Hintergrund zurück. Das Originalbild bleibt an seinem Speicherort; gespeichert wird sein Dateipfad.

**Hinweis zur Bildgröße:** Bilder über 30 MB oder mit extrem großen Abmessungen werden abgelehnt. Große unterstützte Bilder können beim Laden auf maximal 4096 Pixel Kantenlänge reduziert werden. Die Modi „Zentriert“ und „Original“ beziehen sich dann auf diese geladene Auflösung.

## Fehlerdiagnose

Über **„Crash-Log öffnen“** im Reiter **„Updates“** erreichst du das lokale Fehlerprotokoll:

```text
~/.local/state/passwort-generator/crash.log
```

Wenn `XDG_STATE_HOME` gesetzt ist, wird dessen Verzeichnis verwendet. Das Protokoll kann Zeitstempel, App-Version, Prozess-ID, letzte Bedienaktionen, Python-Exceptions, Stacktraces und verfügbare Qt-/Systemmeldungen enthalten.

**Wichtig:** Die zuletzt protokollierte Aktion muss nicht die Ursache des Absturzes sein. Insbesondere bei nativen Qt-, Grafiktreiber- oder Speicherfehlern ist eine eindeutige Diagnose nicht immer möglich.

Bei Problemen unter KDE/Wayland kann testweise ein Start über XWayland helfen, sofern XWayland installiert ist:

```bash
QT_QPA_PLATFORM=xcb ~/.local/opt/passwort-generator/PasswortGenerator.AppImage
```

Falls die Anwendung erneut abstürzt, füge bei einer Fehlermeldung möglichst den relevanten Logabschnitt und die Schritte zur Reproduktion hinzu.

## Deinstallation

Lade `uninstall.sh` aus den [Release-Assets](https://github.com/TimBooH/Passwort-Generator/releases/latest) herunter und starte:

```bash
bash uninstall.sh
```

Der Installer-Eintrag sowie die aktuelle und die vorherige AppImage-Datei werden entfernt. Gespeicherte Benutzereinstellungen bleiben bestehen.

## Entwicklung

### Lokal aus dem Quellcode starten

Benötigt werden **Python 3.11 oder neuer**, ein Linux-Desktop mit Qt-Unterstützung und die von Qt benötigten Systembibliotheken.

```bash
git clone https://github.com/TimBooH/Passwort-Generator.git
cd Passwort-Generator

python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

### Tests

```bash
python -m unittest discover -s tests -v
```

Für zusätzliche GUI- und Update-Integrationstests in einer Umgebung mit Qt:

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=. python tests/smoke_glossy_ui.py
QT_QPA_PLATFORM=offscreen PYTHONPATH=. python tests/smoke_update_gui.py
```

### Build und Release

Das Repository verwendet [GitHub Actions](https://github.com/TimBooH/Passwort-Generator/actions/workflows/build-and-release.yml) mit einem gemeinsamen Job für Tests, AppImage-Build und Veröffentlichung.

Ein automatischer Release-Lauf startet bei einer Änderung von `version.py` auf `main`. Änderungen am Workflow lösen ebenfalls einen Versionscheck aus; ein bereits existierendes Release wird übersprungen. Manuelle Ausführung ist über **Run workflow** möglich.

**Für ein neues Release:** Programmänderungen und Tests abschließen, `APP_VERSION` in `version.py` erhöhen, `RELEASE_NOTES.md` aktualisieren und alles gemeinsam committen. Nach bestandenen Tests werden das AppImage, Installationsskripte und `SHA256SUMS` veröffentlicht. Reine README-Änderungen lösen keinen Release-Build aus.

### Projektstruktur

```text
Passwort-Generator/
├── .github/workflows/build-and-release.yml
├── assets/
├── tests/
│   ├── smoke_glossy_ui.py
│   ├── smoke_update_gui.py
│   └── test_*.py
├── main.py                 # Anwendung und Benutzeroberfläche
├── password_core.py        # Passworterzeugung
├── glass_ui.py             # Glasdesign und Hintergrundbilder
├── updater.py              # AppImage-Aktualisierung und Neustart
├── diagnostics.py          # Lokale Fehlerprotokolle
├── version.py              # Versionsnummer
├── requirements.txt        # Python-Abhängigkeiten
├── install.sh              # Installation und Menüeintrag
├── uninstall.sh            # Deinstallation
├── RELEASE_NOTES.md        # Änderungen pro Veröffentlichung
└── README.md
```

## Sicherheit und Datenschutz

- Passwörter werden **lokal generiert** und nicht an einen Server übertragen.
- Generierte Passwörter werden von der Anwendung nicht dauerhaft gespeichert.
- Für die Updateprüfung werden öffentliche Release-Metadaten von GitHub abgerufen.
- AppImage-Downloads werden vor der Installation anhand der GitHub-Prüfsumme geprüft.
- Crash-Logs bleiben lokal und werden nicht automatisch hochgeladen.
- **Zwischenablage:** Kopierte Passwörter können für andere Programme sichtbar sein, bis sie überschrieben oder aus der Zwischenablage entfernt werden.

---

**Projekt:** [TimBooH/Passwort-Generator](https://github.com/TimBooH/Passwort-Generator) · **[Releases](https://github.com/TimBooH/Passwort-Generator/releases)** · **[Build-Status](https://github.com/TimBooH/Passwort-Generator/actions/workflows/build-and-release.yml)**
