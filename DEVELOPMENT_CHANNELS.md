# PasswortGenerator – genau zwei Git-Branches

## Branches
- `main`: Stable-Quellcode; Änderungen und reguläre Releases nur mit ausdrücklicher Freigabe.
- `unstable`: Entwicklung, Linux-/Windows-Tests und getrennte Test-Builds.
- Keine zusätzlichen Branches, insbesondere keinen Branch `unstable-downloads`.

## Automatische Unstable-Downloads
GitHub Actions veröffentlicht nach erfolgreichen Linux- und Windows-Tests die beiden Installer und eine Datei `latest.json` als Git-Snapshot, erreichbar über den beweglichen **Git-Tag** `unstable-downloads`. Ein **Tag ist kein Branch**. Für die automatisierte Veröffentlichung genügt der eingebaute `GITHUB_TOKEN`; zusätzliche Zugangsdaten sind nicht erforderlich.

Der Updater ruft weiterhin `https://raw.githubusercontent.com/TimBooH/Passwort-Generator/unstable-downloads/latest.json` ab. Die Adresse bleibt unverändert, aber `unstable-downloads` ist nun ein **Tag**, kein Branch. Für jede Testinstallation werden erwarteter Dateiname, GitHub-Domain/Pfad, Dateigröße und SHA-256-Prüfsumme geprüft. Der Download ist öffentlich und benötigt keinen Login.

Neue Unstable-Testversionen werden nicht als GitHub-Releases veröffentlicht. GitHub-Actions-Artefakte für die Diagnose bleiben zusätzlich 14 Tage verfügbar.

## Bereinigung und Erhalt historischer Daten
- Nach erfolgreicher Veröffentlichung und Prüfung des neuen Download-Tags löscht der Workflow den früheren Branch `unstable-downloads`.
- Der bestehende Branch `stable-channel-promotion` enthält vier eigene frühere Commits. Vor seinem Entfernen wird seine Commit-Spitze unter dem Archiv-Tag `archive/stable-channel-promotion-20261025` gesichert.
- Die Branchliste wird anschließend auf genau `main` und `unstable` geprüft.

## Stable bleibt unverändert
`main` und Stable v0.22.0 werden bei Unstable-Arbeiten nicht verändert. Der frühere `unstable`-Prerelease wird vorerst nicht gelöscht, damit ältere App-Versionen ihre bisherige Updateadresse nicht verlieren. Er wird nicht weiter aktualisiert.

Linux: getrennte Installationsordner `~/.local/opt/passwort-generator/` und `~/.local/opt/passwort-generator-unstable/`, jeweils mit getrennten Sicherungen. Windows: unterschiedliche Installer-App-IDs, Program-Files-Verzeichnisse und Verknüpfungen sowie UAC-Abfrage. QSettings, Kanalwahl und Rollback bleiben erhalten.
