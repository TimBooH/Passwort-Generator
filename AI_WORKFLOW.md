# Lokales Codex–Claude-Team

Codex ist Hauptentwickler und prüft Claudes Ergebnisse. Claude ist unabhängiger
Prüfer. `tools/ai_team.py` verbindet die bereits installierten Kommandozeilen-
programme; kein API-Schlüssel oder zusätzliches Python-Paket ist dafür nötig.
Für isolierte Testprozesse wird das auf diesem Rechner vorhandene Linux-Werkzeug
Bubblewrap (`bwrap`) verwendet; fehlt es, stoppt der Runner vor den App-Tests.
Beide Programme benötigen ihre eigene gültige Anmeldung und nutzen die dort
konfigurierten Modelle. Die App-Version bleibt für dieses Werkzeug unverändert.
Der lokale Runner unterstützt ausschließlich Linux. Die Windows-App wird separat
in GitHub Actions gebaut und geprüft. Unter Windows verweigert der Runner den
Start von App-Tests, damit native Benutzereinstellungen nicht verändert werden.

## Einmalige Einrichtung

```bash
claude auth login
codex login
python tools/ai_team.py doctor
```

Für App-Tests Python 3.12 mit den Abhängigkeiten aus `requirements.txt` verwenden.
Eine vorhandene `.venv/bin/python` wird automatisch für Tests ausgewählt.
Bei abgelaufener Anmeldung stoppt der Lauf. Zugangsdaten gehören weder ins
Projekt noch in den Chat. Das Terminal für die einmalige Anmeldung darf danach
geschlossen werden.

## Entwicklungsauftrag und gegenseitige Prüfung

1. Der Nutzer beauftragt Änderungen; Codex setzt ausschließlich den freigegebenen
   Umfang auf `unstable` um. Vorher Projektpfad, Arbeitsbaum und GitHub-Stand prüfen.
2. Codex startet den Prüflauf. Claude liest den Code unabhängig und liefert
   strukturierte Befunde. Codex prüft jeden Befund und sucht zusätzlich selbst
   nach Fehlern. Zurückgewiesene Claude-Befunde müssen im Bericht begründet werden.
3. Mit `--fix` darf Codex bestätigte Fehler korrigieren. Danach beginnen Tests und
   beide Reviews erneut. Standardmäßig höchstens drei Runden, maximal fünf.
   Ohne `--fix` bleibt der komplette Review lesend, abgesehen von Test-/Berichtsdateien.
   Bei widersprüchlichen Bewertungen erhält Claude in der nächsten Runde beide
   Berichte zur erneuten eigenständigen Bewertung. Codex kann ein Nein von Claude
   nicht allein überstimmen; beide müssen den unveränderten Stand freigeben.
4. Nach einer gemeinsamen Freigabe werden die Tests erneut ausgeführt. Der geprüfte
   Dateistand und der Commit werden im Abschlussbericht festgehalten.

```bash
python tools/ai_team.py review --python /pfad/zur/testumgebung/bin/python --fix
```

Der Lauf umfasst alle `test_*.py` sowie die im aktuellen Linux-Abschnitt von
`.github/workflows/unstable.yml` aufgeführten Smoke-Tests in getrennten Prozessen mit
Qt-Offscreen und einem eigenen temporären Ordner je Testprozess. Bubblewrap
stellt das übrige Dateisystem schreibgeschützt bereit; auch die echte
AppImage-Installation bleibt dadurch schreibgeschützt. Er startet weder die
installierte App noch einen Installer. Bei fehlendem Qt, Testfehlern, ungültigen
KI-Antworten, Zeitüberschreitung oder Änderung von Git-Referenzen stoppt er.
Ein unabhängiges Review ist zusätzliche Prüfung, keine Fehlerfreiheitsgarantie.

Ältere, dort nicht mehr aufgeführte Smoke-Skripte und Screenshot-Schreiber werden
nicht automatisch gestartet. Beim Einrichten am 04.11.2026 scheiterte der
zusätzlich versuchte `smoke_first_run_tour_ui.py` zunächst in einer gemeinsam
genutzten Testkonfiguration. In einer frischen Umgebung bestand er unverändert.
Deshalb verwendet der Runner jetzt getrennte Konfigurationsordner pro Prozess;
ein App-Fehler war durch diesen ersten Fehlschlag nicht belegt.

Berichte liegen ausschließlich lokal im ignorierten Ordner `.ai-team/`.
Er enthält die Befunde beider Programme und das Ergebnis der Tests. Parallele
Team-Läufe werden per Sperrverzeichnis verhindert. Nur nach einem tatsächlich
abgebrochenen Lauf darf ein übrig gebliebenes `.ai-team/lock` entfernt werden.

## Commit und Upload

Das Werkzeug erstellt selbst keine Commits. Codex bündelt den freigegebenen
Umfang in einem Commit. Bleibt der geprüfte Dateifingerabdruck dabei identisch,
genügen ein sauberer Arbeitsbaum und genau ein neuer Commit direkt auf dem
geprüften Ausgangscommit: keine
erneuten KI-Reviews oder identischen Testläufe nur wegen des neuen Commits.
Bei tatsächlichen Dateiänderungen ist eine erneute Prüfung erforderlich.

Der Nutzer hat am 04.11.2026 die dauerhafte Freigabe erteilt: Codex darf nach
erfolgreicher Prüfung selbstständig auf `unstable` hochladen und fragt dafür
nicht erneut. `--approved-head` bindet die Ausführung technisch an den exakt
geprüften Commit; die Freigabe dafür liegt durch diese Projektregel bereits vor.
Für `main` und Stable gilt diese Freigabe ausdrücklich nicht.

```bash
python tools/ai_team.py review --python /pfad/zur/testumgebung/bin/python
python tools/ai_team.py publish --approved-head VOLLSTAENDIGER_FREIGEGEBENER_COMMIT
```

`publish` prüft den sauberen Arbeitsbaum, den gespeicherten Dateistand, den
die Commit-Abstammung und den aktuellen GitHub-Branchkopf. Die Review-Basis muss mit GitHub
übereinstimmen. Erlaubt ist ausschließlich ein normaler Vorwärtspush auf
`unstable` im festgelegten Repository. Kein Force-Push, Tag-Push, Branch-Wechsel
oder Stable-Release. Lokale Pre-Push-Hooks bleiben aktiv.

**Nach dem Push bleibt Codex verantwortlich:** GitHub Actions bis zum Ende
verfolgen; Linux- und Windows-Build prüfen; anschließend den rolling
Unstable-Prerelease, beide Installationspakete und die SHA-256-Prüfsummen
kontrollieren. Das lokale Werkzeug wartet nicht selbst auf GitHub Actions.
`main` und öffentliche Stable-Releases benötigen weiterhin eine eigene
ausdrückliche Nutzerfreigabe. Es wird keine Zeitplan-Automation angelegt.

## GitHub-Zugang für normales Git

Die GitHub-Anbindung in Codex und die Anmeldung für lokales `git push` sind
getrennt. Für die unveränderte Übertragung vorhandener Commits benötigt Git
einen eigenen Zugang. Eine normale Browser-Anmeldung mit der offiziellen
GitHub-CLI genügt, ein selbst angelegtes PAT ist nicht nötig:

```bash
.ai-team/bin/gh auth login --hostname github.com --git-protocol https --web
.ai-team/bin/gh auth setup-git --hostname github.com
```

Die offizielle GitHub-CLI wurde lokal unter `.ai-team/bin/gh` installiert und
gegen die veröffentlichten SHA-256-Prüfsummen geprüft. Dieses Programm beim
Bereinigen der Berichte behalten, solange Git es als Credential-Helper nutzt.
Zugangsdaten werden durch die CLI außerhalb des Quellcodes verwaltet.

Technische Grundlage für strukturierte Codex-Prüfungen:
[Offizielle OpenAI-Dokumentation: iterative Prüfschleifen](https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex).
