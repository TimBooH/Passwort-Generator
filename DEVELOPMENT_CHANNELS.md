# PasswortGenerator – Stable und Unstable

## Zwei Update-Kanäle direkt im Programm

Im Bereich **Update → Update-Kanal** kann man zwischen **Stable** und **Unstable (Test)** wechseln. Der gewählte Kanal wird gespeichert und beim Programmstart sowie alle zwei Stunden geprüft.

- **Stable**: Nur getestete, ausdrücklich freigegebene Versionen. Die GitHub-API `/releases/latest` liefert ausschließlich die regulären Releases. Aktuelle Stable-Version: v0.22.0.
- **Unstable**: Jeder erfolgreiche Push nach `unstable` startet Linux- und Windows-Tests. Erst wenn **beide Builds** erfolgreich waren, werden die beiden fertigen Binärdateien in ein **öffentlich erreichbares GitHub-Prerelease im separaten Repository `TimBooH/Passwort-Generator-Unstable`** mit dem festen Tag `unstable` hochgeladen. Das ist **kein offizielles Stable-Release**; das Haupt-Repository erhält keine neuen Unstable-Releases.
- Die GitHub-Actions-Artefakte bleiben zusätzlich zur Diagnose erhalten. Nutzer müssen jedoch **kein ZIP mehr herunterladen oder entpacken**: Die App bezieht die Dateien direkt aus dem Unstable-Prerelease.
- Jeder Unstable-Build trägt eine eindeutige zwölfstellige Commit-Kennung im Dateinamen. Für Unstable-Versionsvergleiche zählt diese Kennung, nicht die Stable-Versionsnummer.
- Downloads werden anhand der in GitHub veröffentlichten SHA-256-Prüfsumme **und** Dateigröße verifiziert. Nicht verifizierbare/unvollständige Builds werden abgelehnt.
- Kein automatisches Umschalten des Kanals. Für das Installieren von Unstable ist eine zusätzliche Bestätigung erforderlich.

## Stable wird nicht überschrieben

**Linux:** Die Stable-Installation unter `~/.local/opt/passwort-generator/` bleibt erhalten. Unstable bekommt den eigenen Installationsordner `~/.local/opt/passwort-generator-unstable/` sowie eine separate vorherige AppImage-Sicherung. Der integrierte Updater startet die gewünschte Version direkt.

**Windows:** Stable und Unstable haben unterschiedliche Inno-Setup-App-IDs, Program-Files-Ordner und Verknüpfungen. Windows zeigt weiterhin die Administratorbestätigung. Der Updater lädt automatisch den zur Auswahl passenden Installer und öffnet ihn nach der Integritätsprüfung.

**Einstellungen:** Stable und Unstable verwenden unterschiedliche QSettings-Namen. Beide Fenster kennzeichnen ihren Build-Kanal; in Unstable steht `[UNSTABLE]` im Fenstertitel.

## Entwicklung und Freigabe

1. Neue Funktionen und Designänderungen zuerst auf den Git-Branch `unstable`.
2. Automatische Test-Builds auf Linux und Windows. Nach zwei erfolgreichen Builds wird ausschließlich im separaten Test-Repository ein als **UNSTABLE / TESTVERSION** gekennzeichnetes Prerelease aktualisiert, sofern `UNSTABLE_RELEASE_TOKEN` für dieses Repository hinterlegt ist. Das ist ausschließlich ein **Testkanal**, kein öffentlicher Stable-Rollout.
3. Fehler in `unstable` beheben und erneut testen. Keine unfertigen Änderungen auf `main`.
4. Erst nach **ausdrücklicher Stable-Freigabe** alle gemeinsam freigegebenen Änderungen über einen Pull Request in `main` übernehmen und **eine gemeinsame nächste Stable-Version** veröffentlichen.
5. Erst dann erhalten alle Stable-Nutzer das reguläre, über `/releases/latest` angebotene Update.

**Sichtbarkeit:** Der Unstable-Quellcode bleibt im Haupt-Repository auf Branch `unstable`; die Test-Releases werden getrennt unter `TimBooH/Passwort-Generator-Unstable` veröffentlicht. Sie sind als experimentelle Testversion gekennzeichnet und nicht die offizielle Stable-Version. Für geheime Vorabversionen wäre ein privates Repository nötig.

## Erforderliche einmalige Konfiguration der Test-Veröffentlichung

1. Im separaten Test-Repository einen initialen Commit auf `main` erstellen (z. B. eine README).
2. Einen **Fine-grained Personal Access Token** nur für `TimBooH/Passwort-Generator-Unstable` mit `Contents: Read and write` erstellen.
3. Den Token im **Quellcode-Repository** unter `Settings > Secrets and variables > Actions` als Repository-Secret `UNSTABLE_RELEASE_TOKEN` hinterlegen. Token nie in Code, Logs oder Chat einfügen.
4. Einen neuen `unstable`-Build über GitHub Actions prüfen. Bei fehlendem Secret werden die Pakete zwar gebaut, jedoch nicht als Release hochgeladen.
5. Den früheren Unstable-Release im Haupt-Repository erst dann entfernen, wenn der neue Installationsweg tatsächlich erfolgreich funktioniert und alte Stable-Updater berücksichtigt wurden.
