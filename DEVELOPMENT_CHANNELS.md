# PasswortGenerator – Stable und Unstable (tokenfrei)

## Kanaltrennung
- **Stable:** unverändert im Haupt-Repository über `/releases/latest`. `main` und Stable v0.22.0 nur mit ausdrücklicher Freigabe ändern.
- **Unstable:** Quellcode ausschließlich auf `unstable`. GitHub Actions erstellt und prüft Linux-AppImage und Windows-Installer. Nach Erfolg beider Jobs werden die fertigen Pakete zusammen mit `latest.json` und SHA-256-Prüfsummen im gesonderten Branch `unstable-downloads` **im selben Repository** veröffentlicht.
- **Keine Unstable-GitHub-Releases:** Der Download-Branch ist nicht Teil der Releases-Übersicht. Auch das vorher neu angelegte zweite Repository und `UNSTABLE_RELEASE_TOKEN` werden nicht benötigt. Die Veröffentlichung verwendet das eingebaute, auf dieses Repository beschränkte `GITHUB_TOKEN`.
- **Updater:** `https://raw.githubusercontent.com/TimBooH/Passwort-Generator/unstable-downloads/latest.json`. Die App verifiziert vollständigen Dateinamen, feste Domain/Pfad, SHA-256 sowie Dateigröße der beiden Dateien.
- **Actions-Artefakte:** werden ergänzend für 14 Tage aufgehoben. Download-Branch enthält immer nur den neuesten geprüften Stand.
- **Kanalwechsel:** bleibt explizit in der App und in den Einstellungen gespeichert.

## Installations-Sicherheit
Linux Stable: `~/.local/opt/passwort-generator/` mit eigenem Backup, Linux Unstable: `~/.local/opt/passwort-generator-unstable/` mit separatem Backup. Unter Windows separate Inno-Setup-IDs, Verzeichnisse, Verknüpfungen und UAC-Bestätigung. Keine Überschreibung von Stable durch Unstable. DE/EN, Update-Vorschau und Rollback bleiben erhalten.

## Veröffentlichungsregeln
1. Neue Arbeiten nach `unstable`, niemals auf `main` ohne Freigabe.
2. Automatische vollständige Tests auf Linux und Windows, dann Paketbau und Integritätsprüfung.
3. Nach beiden erfolgreichen Builds automatische Publikation nur auf `unstable-downloads`. Kein neuer GitHub-Release und kein PAT/Extra-Secret.
4. Der Quellcode-Branch `unstable` bleibt vom Download-Branch getrennt.
5. Der alte historische `unstable`-Prerelease im Haupt-Repository bleibt vorerst unverändert, weil bestehende Stable-v0.22.0-Updater noch seine Adresse benutzen. Er wird nicht weiter aktualisiert und kann nach einer ausdrücklich freigegebenen Migration bereinigt werden.

## Warum kein neues Repository?
GitHubs automatisches `GITHUB_TOKEN` besitzt lediglich Schreibzugriff auf das Repository, in dem der Workflow läuft. Eine Veröffentlichung durch den Quellcode-Workflow in ein **anderes** Repository erfordert eine gesonderte Zugriffsberechtigung. Der hier verwendete Download-Branch erfüllt den Wunsch nach testbaren automatischen Builds **ohne** zusätzliche GitHub-Zugangsdaten und ohne Unstable-Einträge in der Release-Übersicht.
