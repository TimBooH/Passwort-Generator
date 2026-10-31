# PasswortGenerator – Stable und Unstable

## Zwei Entwicklungsbranches
- **`main`**: Stable-Quellcode. Stable-Releases (aktuell v0.22.0) ausschließlich nach ausdrücklicher Freigabe.
- **`unstable`**: Sämtlicher Test- und Entwicklungsquellcode. Jeder Push startet automatisch Linux- und Windows-Tests und die beiden getrennten Installationspakete. Es werden keine zusätzlichen Branches angelegt.

## Unstable-Release bei jeder erfolgreichen Änderung
Nach **beiden erfolgreichen** Linux-/Windows-Jobs aktualisiert GitHub Actions automatisch genau einen öffentlichen, ausdrücklich mit **Unstable / Testversion** gekennzeichneten GitHub-*Prerelease* mit dem festen Tag `unstable`:
- https://github.com/TimBooH/Passwort-Generator/releases/tag/unstable
- Dateinamen enthalten die ersten zwölf Stellen der Commit-SHA, damit man den jeweiligen Unstable-Build eindeutig erkennt.
- Erst SHA-256- und Größenprüfung beider Pakete, dann Upload der neuen Assets, danach Aktualisierung des Releasetitels. Vorherige Dateien werden erst entfernt, wenn die beiden aktuellen erfolgreich verfügbar sind.
- GitHub Actions benutzt `GITHUB_TOKEN` des *gleichen* Repositories mit `contents: write`; keine zusätzlichen Personal Access Tokens, keine Secrets, keine separate Repo-Veröffentlichung.
- Ein fehlgeschlagener oder abgebrochener Build veröffentlicht **keine** neue Unstable-Version.

## Integrierte Updates
- **Stable**: `https://api.github.com/repos/TimBooH/Passwort-Generator/releases/latest`; GitHub gibt keine Prereleases als `latest` zurück.
- **Unstable**: `https://api.github.com/repos/TimBooH/Passwort-Generator/releases/tags/unstable`; der Updater akzeptiert nur `prerelease=true`, den passenden Commit-Build, die exakten Release-Download-URLs, Dateigröße und SHA-256-Digest.
- Frühere Unstable-App-Versionen mit der alten Manifest-Adresse unter `unstable-downloads` bleiben kompatibel: Der Workflow aktualisiert übergangsweise zusätzlich den gleichnamigen **Git-Tag**, der ausdrücklich *kein Branch* ist.
- Stable und Unstable bleiben separate Installationen: Linux `~/.local/opt/passwort-generator/` und `~/.local/opt/passwort-generator-unstable/` mit getrennten Backups; Windows unterschiedliche Inno-App-IDs, Verzeichnisse, Verknüpfungen und UAC-Dialoge; separate QSettings.
- Die App fragt vor einer Unstable-Installation nach Bestätigung. Der Updater prüft automatisch beim Start und anschließend im Zwei-Stunden-Abstand. Manuelle Updateprüfung bleibt möglich.

## Freigabeprozess
Jede fertig getestete Änderung auf `unstable` führt ohne manuelle Freigabe zu einer aktualisierten **Unstable-Testveröffentlichung**. Für einen offiziellen **Stable-Release** auf `main` ist dagegen weiterhin eine ausdrückliche Freigabe notwendig. Der Release-`unstable` wird als Testversion im selben Repository gelistet, nicht als neues Stable-Release.
