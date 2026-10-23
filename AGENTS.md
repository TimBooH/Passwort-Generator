# PasswortGenerator – Arbeitsregeln für künftige Änderungen

## Gewünschter Ablauf (Projektvorgabe)

**Branches:** `main` = freigegebenes Stable; `unstable` = Entwicklung und Test. Unstable-Builds dürfen niemals die Stable-Installation überschreiben oder Stable-Releases erstellen. Details: [DEVELOPMENT_CHANNELS.md](https://github.com/TimBooH/Passwort-Generator/blob/unstable/DEVELOPMENT_CHANNELS.md).
Der Projektinhaber möchte, dass freigegebene neue App-Änderungen **zuerst auf dem Branch `unstable`** umgesetzt und über Test-Builds geprüft werden. Eine Veröffentlichung als Stable auf `main` erfolgt **erst nach ausdrücklicher Freigabe**.

**Wichtig: Alle gemeinsam besprochenen und zur Umsetzung freigegebenen Funktionen gehören in EIN gemeinsames Versionsrelease.** Nicht für jede einzelne Funktion oder kleinere Anpassung eine neue Versionsnummer bzw. einen separaten Release-Schritt vergeben. Erst den gesamten vereinbarten Umfang umsetzen, zusammen testen und dann **einmal** die nächste Versionsnummer vergeben. Fehlerkorrekturen vor dem Release innerhalb desselben Schritts erledigen. Die vereinbarten Features bleiben bis zur gemeinsamen Veröffentlichung im selben Paket.

**Nur besprechen ist noch keine Freigabe zur Implementierung.** Wenn der Projektinhaber ausdrücklich eine Umsetzung startet (z. B. „los“ oder „umsetzen“), die zuvor gemeinsam vereinbarten und freigegebenen Änderungen als Paket behandeln. Bei ausdrücklich nur auf eine Funktion beschränkten Aufträgen ausschließlich diese umsetzen.

1. Den aktuellen GitHub-Stand und `version.py` lesen, vorhandene Funktionen erhalten und gewünschte Änderung für Linux und Windows konsistent umsetzen.
2. Den kompletten freigegebenen Änderungsumfang für **eine** gemeinsame neue Versionsnummer bündeln. Den 100-Schritte-Plan nur für tatsächlich gemeinsam veröffentlichte Entwicklungsreleases verwenden (`0.01.0` bis `0.99.0`, dann `1.0.0`). Ist ein Release noch nicht erfolgreich, dieselbe Nummer reparieren, statt weiterzuspringen.
3. Zugehörige Tests aktualisieren; **keine feste APP_VERSION im Test erwarten**. Wo möglich vor dem Push Syntax, Unit- und Qt-Offscreen-Tests durchführen.
4. Neuen App-Code ausschließlich nach **`unstable`** pushen und dort Linux-/Windows-Test-Artefakte erstellen. Nicht direkt nach `main` pushen, keinen öffentlichen Release oder Tag erstellen. Erst nach ausdrücklicher Stable-Freigabe die fertigen Änderungen per PR nach `main` übernehmen.
5. **Unstable-Builds bis zum Ergebnis prüfen** und Fehler auf `unstable` beheben. Dort niemals GitHub-Releases/Tags erstellen. Nach einer expliziten Stable-Freigabe die regulären Stable-Releases unter `main` prüfen und beide Assets kontrollieren.
6. Im Chat zwischen **Unstable-Test-Build** (GitHub-Actions-Artefakt) und **öffentlichem Stable-Release** unterscheiden; Testergebnis und zutreffende Links nennen.

Die Update-Prüfung in der App, der Changelog, das Glass-Design, die Passwortsicherheit, der Installationspfad auf Windows und die Sicherung der vorherigen AppImage-Version dürfen nicht unbeabsichtigt entfernt werden.
