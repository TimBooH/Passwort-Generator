# PasswortGenerator – Arbeitsregeln für künftige Änderungen

## Gewünschter Ablauf (Projektvorgabe)
Der Projektinhaber möchte, dass jede fertig implementierte Änderung **ohne zusätzliche Rückfrage** getestet, direkt auf GitHub übertragen und mit der **nächsten Versionsnummer** veröffentlicht wird.

1. Den aktuellen GitHub-Stand und `version.py` lesen, vorhandene Funktionen erhalten und gewünschte Änderung für Linux und Windows konsistent umsetzen.
2. Die nächsten, noch nicht veröffentlichten Versionsschritte gemäß dem 100-Schritte-Plan verwenden (`0.01.0` bis `0.99.0`, dann `1.0.0`). Wenn eine begonnene Version noch kein erfolgreiches Release hat, dieselbe Versionsnummer erst reparieren, statt unnötig weiterzuspringen.
3. Zugehörige Tests aktualisieren; **keine feste APP_VERSION im Test erwarten**. Wo möglich vor dem Push Syntax, Unit- und Qt-Offscreen-Tests durchführen.
4. `README.md` und `RELEASE_NOTES.md` anpassen, Code auf GitHub in `main` pushen und Linux-/Windows-GitHub-Actions auslösen.
5. **GitHub Actions bis zum Ergebnis prüfen.** Bei Build- oder Testfehlern die Logs auswerten, den Fehler beheben und beide Plattformen erneut bauen. Nur als erfolgreich oder veröffentlicht bezeichnen, wenn die Runs erfolgreich sind und ein GitHub Release mit **AppImage und Windows-Installer** tatsächlich existiert.
6. Im Chat zum Schluss Versionsnummer, Testergebnis, Links auf GitHub Release oder fehlgeschlagene Jobs und gegebenenfalls offen gebliebene Probleme angeben.

Die Update-Prüfung in der App, der Changelog, das Glass-Design, die Passwortsicherheit, der Installationspfad auf Windows und die Sicherung der vorherigen AppImage-Version dürfen nicht unbeabsichtigt entfernt werden.
