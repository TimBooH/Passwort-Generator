# PasswortGenerator – Arbeitsregeln für künftige Änderungen

## Gewünschter Ablauf (Projektvorgabe)
**Verbindlich:** `main` = Stable, `unstable` = Testentwicklung. Siehe [DEVELOPMENT_CHANNELS.md](DEVELOPMENT_CHANNELS.md). Unstable-Builds dürfen niemals öffentliche Releases/Tags anlegen oder die Stable-Installation ersetzen.
Der Projektinhaber möchte, dass freigegebene Änderungen **ohne zusätzliche Rückfrage zuerst auf dem Zweig `unstable`** umgesetzt und dort getestet werden. Für eine Veröffentlichung in **Stable** auf `main` ist danach eine **ausdrückliche Freigabe** erforderlich.

**Wichtig: Alle gemeinsam besprochenen und zur Umsetzung freigegebenen Funktionen gehören in EIN gemeinsames Versionsrelease.** Nicht für jede einzelne Funktion oder kleinere Anpassung eine neue Versionsnummer bzw. einen separaten Release-Schritt vergeben. Erst den gesamten vereinbarten Umfang umsetzen, zusammen testen und dann **einmal** die nächste Versionsnummer vergeben. Fehlerkorrekturen vor dem Release innerhalb desselben Schritts erledigen. Die vereinbarten Features bleiben bis zur gemeinsamen Veröffentlichung im selben Paket.

**Nur besprechen ist noch keine Freigabe zur Implementierung.** Wenn der Projektinhaber ausdrücklich eine Umsetzung startet (z. B. „los“ oder „umsetzen“), die zuvor gemeinsam vereinbarten und freigegebenen Änderungen als Paket behandeln. Bei ausdrücklich nur auf eine Funktion beschränkten Aufträgen ausschließlich diese umsetzen.

1. Den aktuellen GitHub-Stand und `version.py` lesen, vorhandene Funktionen erhalten und gewünschte Änderung für Linux und Windows konsistent umsetzen.
2. Den kompletten freigegebenen Änderungsumfang für **eine** gemeinsame neue Versionsnummer bündeln. Den 100-Schritte-Plan nur für tatsächlich gemeinsam veröffentlichte Entwicklungsreleases verwenden (`0.01.0` bis `0.99.0`, dann `1.0.0`). Ist ein Release noch nicht erfolgreich, dieselbe Nummer reparieren, statt weiterzuspringen.
3. Zugehörige Tests aktualisieren; **keine feste APP_VERSION im Test erwarten**. Wo möglich vor dem Push Syntax, Unit- und Qt-Offscreen-Tests durchführen.
4. Neue App-Änderungen **ausschließlich auf `unstable`** bearbeiten und über `Unstable Preview – Linux & Windows` mit herunterladbaren Test-Artefakten prüfen. `main` erst nach ausdrücklicher Stable-Freigabe per PR aktualisieren; nicht vorher öffentlich veröffentlichen.
5. **Unstable Actions bis zum Ergebnis prüfen.** Fehler auf `unstable` beheben und neu testen. **Kein** Release/Tag und keine Produktiv-Updates während der Testphase. Erst nach Freigabe und Merge nach `main` die regulären Stable-Releases mit AppImage und Windows-Installer erzeugen.
6. Im Chat immer zwischen **Unstable-Test-Build** (GitHub-Actions-Artefakt) und **veröffentlichtem Stable-Release** unterscheiden. Version, Testergebnis und Links angeben.

Die Update-Prüfung in der App, der Changelog, das Glass-Design, die Passwortsicherheit, der Installationspfad auf Windows und die Sicherung der vorherigen AppImage-Version dürfen nicht unbeabsichtigt entfernt werden.
