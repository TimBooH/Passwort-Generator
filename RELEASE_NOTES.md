# PasswortGenerator v0.20.0 – Passwort-Regeln, Passphrasen und Sicherheit

**Entwicklungsschritt 20 von 100.** Alle sechs gemeinsam geplanten Funktionen sind Bestandteil dieses einen Releases.

## Deutsch

- **Erweiterte Passwort-Regeln:** Mindestanzahl für Zahlen und Sonderzeichen (0–20) und frei ausschließbare Zeichen in einem kompakten Dialog. Widersprüchliche Regeln geben eine Fehlermeldung; kryptografisch sichere Erzeugung bleibt erhalten.
- **Deutsche und englische Passphrasen:** Wähle die Wortliste im Passphrase-Modus unabhängig von der Programmsprache. Beide Offline-Wortlisten enthalten jeweils 1.024 mögliche zusammengesetzte Wörter; 4–10 Wörter, Trennzeichen und zweistellige Zufallszahlen funktionieren weiterhin.
- **Sicherheitsanalyse:** Ein Button zeigt die geschätzte Entropie und Stärke ohne irreführende Garantie für eine bestimmte Knackdauer.
- **Tastenkombinationen:** Strg+G (Generieren), Strg+Umschalt+C (Kopieren), Strg+H (Sitzungsverlauf) und Strg+1 bis Strg+4 für die Navigation.
- **Privatsphäre-Modus:** Sichtbare Passwörter bei Fensterwechsel automatisch verbergen; optionale Bestätigung vor dem Öffnen des Sitzungsverlaufs. Beides in der bestehenden Kachel „Sicherheit“.
- **Update rückgängig machen:** Unter Linux wird nach Bestätigung die vorhandene vorherige AppImage-Version sicher zurückgetauscht. Unter Windows kann der Nutzer im Changelog einen älteren Release auswählen; dessen offizieller Installer wird nach Größen- und SHA-256-Prüfung mit UAC und einem sichtbaren Installationsassistenten gestartet. Eine Rückinstallation unter Windows hängt außerdem davon ab, ob der ältere Installer sie erlaubt. Nichts wird ohne Bestätigung installiert.
- Alle neuen Bedienelemente stehen auf **Deutsch und Englisch** zur Verfügung. Die bestehenden vier Seiten, eigenen Glass-Kacheln, Updates, gespeicherten Einstellungen und der Offline-Generator bleiben erhalten.

## English

- **Advanced password rules:** Minimum digit/symbol counts (0–20) and excluded characters in a compact dialog. Invalid combinations cause a clear error while using cryptographically secure randomness.
- **German and English passphrases:** Choose the word language separately from the app language. Each offline compound-word vocabulary has 1,024 possibilities; 4–10 words, separators and an optional two-digit suffix remain available.
- **Strength details:** Estimated entropy and strength explanation without misleading crack-time guarantees.
- **Keyboard shortcuts:** Ctrl+G (generate), Ctrl+Shift+C (copy), Ctrl+H (session history), Ctrl+1–4 (navigation).
- **Privacy:** Automatically hide a shown password when switching away; optionally confirm before opening the session history.
- **Rollback:** Linux can restore the existing previous AppImage after confirmation. Windows can select an older release in the Changelog, download its official installer after size/SHA-256 verification, and launch a visible UAC-approved installer. A Windows downgrade remains subject to the old installer's compatibility and consent.
- All controls work in **German or English**. Existing app pages, Glass tiles, preferences, verified update flow and offline generation remain.
