# PasswortGenerator – Arbeitsregeln für künftige Änderungen

## Gewünschter Ablauf (Projektvorgabe)
Der Projektinhaber möchte, dass freigegebene Änderungen **ohne zusätzliche Rückfrage** getestet und direkt auf GitHub übertragen werden.

**Wichtig: Alle gemeinsam besprochenen und zur Umsetzung freigegebenen Funktionen gehören in EIN gemeinsames Versionsrelease.** Nicht für jede einzelne Funktion oder kleinere Anpassung eine neue Versionsnummer bzw. einen separaten Release-Schritt vergeben. Erst den gesamten vereinbarten Umfang umsetzen, zusammen testen und dann **einmal** die nächste Versionsnummer vergeben. Fehlerkorrekturen vor dem Release innerhalb desselben Schritts erledigen. Die vereinbarten Features bleiben bis zur gemeinsamen Veröffentlichung im selben Paket.

**Nur besprechen ist noch keine Freigabe zur Implementierung.** Wenn der Projektinhaber ausdrücklich eine Umsetzung startet (z. B. „los“ oder „umsetzen“), die zuvor gemeinsam vereinbarten und freigegebenen Änderungen als Paket behandeln. Bei ausdrücklich nur auf eine Funktion beschränkten Aufträgen ausschließlich diese umsetzen.

1. Den aktuellen GitHub-Stand und `version.py` lesen, vorhandene Funktionen erhalten und gewünschte Änderung für Linux und Windows konsistent umsetzen.
2. Den kompletten freigegebenen Änderungsumfang für **eine** gemeinsame neue Versionsnummer bündeln. Den 100-Schritte-Plan nur für tatsächlich gemeinsam veröffentlichte Entwicklungsreleases verwenden (`0.01.0` bis `0.99.0`, dann `1.0.0`). Ist ein Release noch nicht erfolgreich, dieselbe Nummer reparieren, statt weiterzuspringen.
3. Zugehörige Tests aktualisieren; **keine feste APP_VERSION im Test erwarten**. Wo möglich vor dem Push Syntax, Unit- und Qt-Offscreen-Tests durchführen.
4. `README.md` und `RELEASE_NOTES.md` anpassen, Code auf GitHub in `main` pushen und Linux-/Windows-GitHub-Actions auslösen.
5. **GitHub Actions bis zum Ergebnis prüfen.** Bei Build- oder Testfehlern die Logs auswerten, den Fehler beheben und beide Plattformen erneut bauen. Nur als erfolgreich oder veröffentlicht bezeichnen, wenn die Runs erfolgreich sind und ein GitHub Release mit **AppImage und Windows-Installer** tatsächlich existiert.
6. Im Chat zum Schluss Versionsnummer, Testergebnis, Links auf GitHub Release oder fehlgeschlagene Jobs und gegebenenfalls offen gebliebene Probleme angeben.

Die Update-Prüfung in der App, der Changelog, das Glass-Design, die Passwortsicherheit, der Installationspfad auf Windows und die Sicherung der vorherigen AppImage-Version dürfen nicht unbeabsichtigt entfernt werden.
