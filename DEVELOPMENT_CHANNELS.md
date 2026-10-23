# PasswortGenerator – Stable / Unstable

## Stable (main)
- main bleibt der veröffentlichte, freigegebene Stand.
- Öffentliches GitHub-Release und automatische Updates nutzen nur Stable.
- Linux-AppImage und Windows-Installer erscheinen nur nach ausdrücklicher Stable-Freigabe.
- Keine unfertigen Funktionen direkt auf main entwickeln.
- Die nächste Versionsnummer wird nur für ein gemeinsam freigegebenes Release vergeben.

## Unstable (unstable)
- Jede neue Funktion, jedes neue Design und Fehlerkorrekturen zuerst hier entwickeln.
- Auf jedem Push prüfen Linux und Windows die Änderungen.
- Der Preview-Workflow erzeugt herunterladbare **GitHub-Actions-Artefakte**, ausdrücklich **keine Releases, Tags oder Änderungen auf main**.
- Linux: PasswortGenerator-UNSTABLE-x86_64.AppImage direkt ausführen, nicht per Stable-install.sh installieren.
- Windows: PasswortGenerator-UNSTABLE-Setup-x64.exe mit eigenem AppId, Program-Files-Ordner und eigenen Verknüpfungen, damit Stable erhalten bleibt.
- Die Testanwendung zeigt [UNSTABLE] im Fenstertitel, nutzt separate lokale Einstellungen und lässt keine Stable-Updates oder -Rollbacks zu.
- Die Datei release_channel.py bleibt im Git-Code bei CHANNEL = 'stable'. Nur das Unstable-CI ersetzt dies vorübergehend während des Test-Builds im Runner.

## Unstable herunterladen
1. GitHub > Actions > Unstable Preview – Linux & Windows.
2. Einen erfolgreichen Lauf auf Branch unstable auswählen.
3. Unter Artifacts die Linux- oder Windows-Testversion herunterladen.
4. Testen und Feedback geben. Verbesserungen bleiben auf unstable.

## Erst nach deiner Freigabe Stable veröffentlichen
1. Alle vereinbarten Verbesserungen bündeln und auf beiden Plattformen testen.
2. Erst nach ausdrücklicher Freigabe einen Pull Request von unstable nach main zusammenführen.
3. Einmalig die nächste Stable-Version festlegen und die regulären Linux-/Windows-Releases erzeugen.
4. Prüfen, dass AppImage, Windows-Installer und Prüfsummen im selben Release liegen.
5. Unstable mit dem neuen Stable-Stand aktualisieren.

**Wichtig:** Das Repository ist öffentlich, also ist auch Quellcode auf dem Branch unstable öffentlich lesbar. Nur die Auslieferung als Stable-Release wird zurückgehalten. Für tatsächlich nichtöffentlichen Quellcode wäre ein separates privates Repository erforderlich.
