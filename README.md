# 🔐 PasswortGenerator

**Ein sicherer Passwortgenerator für Linux – mit stabiler, skalierbarer Glasoberfläche, eigenen Hintergrundbildern, Updateprüfung und Startmenü-Installation.**

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
- **Responsive Glossy-Glas-Panels:** mitwachsende, abgerundete Kacheln mit Qt-eigenen Farbverläufen, feinen Lichtkanten und Glanzeffekten
- **Glas-Deckkraft** mit einem Schieberegler anpassen (30–85 %)
- **Eigene Hintergrundbilder** auswählen und zwischen Ausfüllen, Einpassen, Strecken, Zentriert, Originalgröße und Kacheln wechseln
- **Responsive Fenster-Skalierung:** alle drei Kacheln wachsen und schrumpfen mit der Fenstergröße – ohne feste maximale Breite
- **Stabilität:** keine Python-Zeichenschleife beim Fensterziehen; Hintergrundbilder werden verzögert neu skaliert
- Unterschiedliche **Hintergrund- und Textfarben** wählen oder eine eigene Farbe einstellen
- Farben werden gespeichert und beim nächsten Start wiederhergestellt
- **Automatische und manuelle Updateprüfung** über GitHub Releases
- **Update installieren & neu starten:** SHA-256-geprüfter Download, Sicherung der Vorgängerversion und automatischer Neustart
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
| Aktuelle AppImage-Version | `~/.local/opt/passwort-generator/PasswortGenerator.AppImage` |
| Vorherige AppImage-Version | `~/.local/opt/passwort-generator/PasswortGenerator-previous.AppImage` |
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

## 🔄 Wie funktionieren Updates und der automatische Neustart?

Der PasswortGenerator prüft die neueste Version über die Releases von **TimBooH/Passwort-Generator**. Die Prüfung findet beim Start oder manuell über **„Auf Updates prüfen“** statt.

Wenn eine neuere Version verfügbar ist:

1. Auf **„Update installieren & neu starten“** klicken. Die App lädt das neue Linux-AppImage herunter und zeigt den Fortschritt an.
2. Die Datei wird anhand der von GitHub bereitgestellten **SHA-256-Prüfsumme** und Dateigröße überprüft. Fehlerhafte Downloads werden nicht installiert.
3. **Bei einer Installation mit dem Installer:** Die bisherige Version wird als `PasswortGenerator-previous.AppImage` gesichert. Die neue wird atomar als `PasswortGenerator.AppImage` eingesetzt.
4. Ein neuer Prozess startet die aktualisierte App nach einer kurzen Verzögerung. Die bisherige App schließt sich automatisch.
5. **Bei einem einzeln gestarteten AppImage:** Die neue Version wird in den Downloadordner gespeichert und ebenfalls automatisch gestartet. Eine Sicherung unter `previous` wird nur für die Menü-Installation gepflegt.

**Es bleiben im Installationsordner nur die aktuelle und die unmittelbar vorherige AppImage-Version.** Ältere, vom PasswortGenerator verwaltete AppImage-Dateien in diesem Ordner werden entfernt. Andere Programme oder Dateien im Downloadordner werden nicht gelöscht.

Der Download startet ausschließlich nach deinem Klick. **Es gibt keine unbeaufsichtigten automatischen Installationen.**

## 🎨 Design ändern

Unter **„Design & Farben“** gibt es verschiedene Vorlagen für Hintergrund und Text sowie einen Farbwähler für eigene Farben. Mit **„Glas-Deckkraft“** bestimmst du die Stärke der transparenten Glasflächen. Die Kacheln verwenden Qt-eigene Stylesheets mit glänzenden Farbverläufen, Lichtkanten und abgerundeten Ecken. Beim Verändern der Fenstergröße passt sich jede Kachel an die verfügbare Breite und Höhe an. Der Hintergrund wird ohne eigene Python-PaintEvent-Schleife dargestellt. Farben und Glas-Deckkraft werden lokal über Qt `QSettings` gespeichert. Achte bei eigenen Kombinationen auf guten Kontrast.

**Hinweis:** Das Design erzeugt den Glas-Look innerhalb des App-Fensters. Eine echte Unschärfe des *Desktops hinter dem Fenster* hängt vom KDE/KWin-Compositor ab und wird nicht vorausgesetzt.

## 🖼️ Eigene Hintergrundbilder

Öffne **Design & Farben → Bild auswählen …** und wähle eine PNG-, JPG-, WEBP- oder BMP-Datei.

| Modus | Darstellung |
| --- | --- |
| **Ausfüllen** | Fenster vollständig ausfüllen; überstehende Bildränder werden mittig abgeschnitten |
| **Einpassen** | Ganzes Bild proportional anzeigen; seitliche oder obere Ränder möglich |
| **Gestreckt** | Bild auf Fensterbreite und -höhe dehnen, auch wenn es verzerrt wird |
| **Zentriert (100 %)** | Ohne Skalierung mittig platzieren |
| **Original (links oben)** | Ohne Skalierung an der linken oberen Ecke beginnen |
| **Gekachelt** | Bild in Originalgröße wiederholen |

Mit **Bild entfernen** kehrst du zum animierungsfreien Farbverlauf zurück. Der Bildpfad und der Darstellungsmodus werden gespeichert. Das Originalbild bleibt **auf deinem Rechner** und wird nicht in die App kopiert. Wird die Datei verschoben oder gelöscht, musst du sie erneut auswählen.

**Schutz gegen große Bilder:** Dateien über 30 MB bzw. extrem große Pixelmaße werden nicht angenommen. Größere Bilder können außerdem beim Laden auf maximal 4096 Pixel Kantenlänge verkleinert werden. Damit bezieht sich „Originalgröße“ auf die sicher geladene Vorschauauflösung.

## 🛠️ Abstürze diagnostizieren

Ab **v1.5.0** findest du im Bereich **Updates & Versionen** den Button **„Crash-Log öffnen“**. Das lokale Protokoll liegt unter:

`~/.local/state/passwort-generator/crash.log`

Wenn `$XDG_STATE_HOME` gesetzt ist, verwendet die App dieses Verzeichnis. Das Protokoll enthält:

- **Zeitstempel**, Version, Prozess-ID und Start-/Ende-Ereignisse
- Zuletzt ausgeführte Bedienaktionen, etwa Fenstergröße, Farbänderung und Updatevorgang
- **Python-Fehler mit Exception-Typ, Fehlermeldung und vollständigem Stacktrace**
- Wenn verfügbar, **native Absturzsignale** und Qt/C++-Meldungen aus `stderr`
- Beim nächsten Start einen Hinweis, wenn der vorherige Prozess nicht normal beendet wurde

Die letzte protokollierte Aktion ist ein Anhaltspunkt, aber **nicht zwangsläufig die Absturzursache**. Bei Treiber-, Speicher- und Qt-C++-Fehlern ist die genaue Ursache unter Umständen nicht rekonstruierbar. Auch ein harter Abbruch (z. B. `SIGKILL` oder Stromausfall) kann nur als unerwartetes Ende erkannt werden.

Die Logs werden **nur lokal gespeichert** und enthalten keine generierten Passwörter. Kontrolliere dennoch Dateipfade oder andere technische Daten im Log, bevor du es weitergibst.

Zum Testen einer stabileren Qt-Darstellung unter CachyOS/KDE kannst du die App auch einmal mit `QT_QPA_PLATFORM=xcb` über ein Terminal starten. Dafür muss XWayland verfügbar sein.

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
| Benutzeroberfläche | PySide6-Essentials / Qt 6 |
| Passworterzeugung | Python `secrets` / `SystemRandom` |
| Farbauswahl | Qt `QColorDialog` & `QSettings` |
| Glasdesign | Native Qt-Stylesheets (QSS), ohne Python-`paintEvent` beim Resize |
| Updates | GitHub Releases API via Qt `QNetworkAccessManager` |
| Verifizierung | SHA-256 + erwartete Dateigröße; sicherer Austausch mit previous-Backup |
| Absturzdiagnostik | Python `faulthandler`, versionierte Fehlerlogs und Sitzungsmarker |
| Build | PyInstaller und AppImageKit |
| Release | GitHub Actions |

**Optimierter Release-Prozess (ab v1.5.1):** Ein Release-Build wird ausgelöst, wenn `version.py` auf `main` geändert wird, oder manuell über **Run workflow**. Änderungen an der Workflow-Datei lösen ebenfalls einen kurzen Versionscheck aus; existiert das Release bereits, endet der Lauf ohne Build. Änderungen an README, Tests oder Programmdateien ohne neue Versionsnummer starten keinen vollständigen AppImage-Build.

Alle Änderungen einer neuen Version werden zusammen mit der geänderten `APP_VERSION` **in einem Commit** nach `main` gepusht. GitHub startet dann **genau einen** Build. Dieser verwendet einen einzigen Runner für den Versionscheck, die Tests, das AppImage und die Veröffentlichung – ohne separaten Release-Job, ohne unnötige Artifact-Uploads/-Downloads.

Beschleunigungen: **PySide6-Essentials** statt des großen PySide6-Metapakets, festgelegte Build-Abhängigkeiten, GitHub-`pip`-Cache, nur die nötigen Qt-Grafikbibliotheken mit vorhandenen Paketlisten (Aktualisierung nur bei Bedarf) und keine überflüssigen Zwischenschritte. Existiert das GitHub-Release für diese Versionsnummer bereits, wird der Build **vor der Installation von Abhängigkeiten** übersprungen. Gleichzeitig gestartete Builds auf demselben Branch werden zusammengefasst bzw. ältere Läufe abgebrochen.

**Neues Release erstellen:** Funktionsänderungen und Tests sammeln, `APP_VERSION` erhöhen, `RELEASE_NOTES.md` aktualisieren und **einen gemeinsamen Commit** pushen. Die Release-Assets `PasswortGenerator-x86_64.AppImage`, `install.sh`, `uninstall.sh` und `SHA256SUMS` werden nach bestandenen Tests direkt hochgeladen.

**Hinweis:** Bei reinen Quellcodeänderungen ohne Versionsänderung erfolgt kein automatischer Testlauf mehr. Für eine Veröffentlichung die Versionsnummer daher immer im selben Commit erhöhen. Der Workflow kann bei Bedarf manuell gestartet werden.

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
