# PasswortGenerator v1.5.0 – Stabilität, responsive Glas-Kacheln und sichere Updates

Dieses Release konzentriert sich auf die gemeldeten Abstürze beim Fensterziehen und bei Designänderungen sowie auf die neue AppImage-Verwaltung.

## Verbesserte Stabilität
- Kein eigenes Python-`paintEvent` mehr beim Skalieren des Fensters oder des Hintergrundbilds: Qt rendert Glasflächen und Bilder nativ
- Hintergrundbilder werden beim Größenwechsel verzögert und einmalig neu skaliert
- Glas-Kacheln wachsen und schrumpfen mit der Fenstergröße; die alte maximale Inhaltsbreite von 940 Pixeln entfällt
- Bessere Layout-Aufteilung, kompaktere Auswahlfelder und flexiblere Update-Buttons
- Umfangreiche Fenster-, Bildmodus-, Farbwechsel- und Installations-Tests in GitHub Actions

## Neue Updateverwaltung
- **Automatischer Neustart** der neuen App direkt nach erfolgreichem, geprüftem Update
- **Aktuelle Version:** `~/.local/opt/passwort-generator/PasswortGenerator.AppImage`
- **Vorherige Version:** `~/.local/opt/passwort-generator/PasswortGenerator-previous.AppImage`
- Nur diese beiden AppImage-Versionen werden im Installationsordner behalten; ältere eigene Versionen werden entfernt
- Austausch nach Größen- und SHA-256-Prüfung, mit sicherem Zwischenfile und Erhaltung der lauffähigen aktuellen Version bei Installationsfehlern
- Auch `install.sh` und `uninstall.sh` berücksichtigen die previous-Datei
- Bei unabhängig gestarteten AppImages startet der heruntergeladene Nachfolger automatisch, ohne fremde Dateien im Downloadordner zu löschen

## Verbesserte Crash-Logs
- **Crash-Log öffnen** direkt in der App
- Zeitstempel, App-Version, PID, Qt-Plattform, letzte Bedienaktion und Sitzungsende
- Python-Exceptions mit Fehlermeldung und Stacktrace; verfügbare native Signale und Qt-Fehlerausgaben
- Automatische Erkennung eines unerwartet beendeten letzten Starts
- Logdatei: `~/.local/state/passwort-generator/crash.log`

**Wichtiger Hinweis:** Bei nativen Grafiktreiber- und Qt/C++-Abstürzen ist die tatsächliche Ursache nicht immer vollständig aus einem Log ermittelbar. Die Tests reduzieren bekannte Absturzrisiken, ersetzen aber keine Untersuchung eines möglicherweise weiterhin auftretenden Fehlers auf dem konkreten System.

## Installation / Update
Beim bestehenden PasswortGenerator **Auf Updates prüfen → Update installieren & neu starten** auswählen. Nach erfolgreichem Download startet v1.5.0 selbstständig neu. Alternativ `install.sh` aus den Release-Assets ausführen.

Alle generierten Passwörter verbleiben lokal auf dem Gerät.
