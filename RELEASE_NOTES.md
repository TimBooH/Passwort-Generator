# PasswortGenerator v0.23.0 – Oberfläche und Updates

**Entwicklungsschritt 23 von 100.** Gemeinsamer Stable-Release der getesteten Änderungen aus `unstable` für Linux und Windows.

## Deutsch

- **Festes Ocean-Glass-Design:** Einheitliches dunkles Qt-Design mit blau-cyanfarbenen Akzenten. Die frühere Erscheinungsbild- und Hintergrundauswahl wurde entfernt.
- **Switches statt Häkchen:** Alle neun Passwort-, Passphrase- und Sicherheitseinstellungen nutzen kleine Ein-/Aus-Schalter. Die zwei Darstellungszustände und die Funktion der Sicherheitsschalter wurden mit grafischen Qt-Tests überprüft.
- **Modernisierte Oberfläche:** Einheitliche Schriftarten, Icons, Abstände und grafische Darstellung unter Linux und Windows.
- **Update-Kanal bleibt gespeichert:** Die Auswahl **Stable** oder **Unstable** überlebt Download, Installation und Neustart. Sonstige Einstellungen beider Installationen bleiben voneinander getrennt.
- **Automatische Unstable-Veröffentlichung:** Nach erfolgreichen Linux- und Windows-Tests aktualisiert GitHub Actions den Unstable-Prerelease ohne zusätzliche Tokens. Die einzigen Branches bleiben `main` und `unstable`.
- **Sichere Updates:** Separate Stable-/Unstable-Installationsorte, Sicherung der vorherigen AppImage-Version, Windows-UAC und Prüfung von Dateiname, Dateigröße und SHA-256.
- **Weitere Funktionen erhalten:** Passwort-/Passphrase-Generierung, Profile und erweiterte Regeln, Sprache Deutsch/Englisch, Sitzungshistorie, Zwischenablageschutz, Versionsvergleich und Changelog.

**Stable** ist unter `/releases/latest` verfügbar. **Unstable** bleibt ausdrücklich eine separate Testversion.

## English

- **Fixed Ocean Glass appearance:** A consistent dark blue/cyan Qt theme with removed appearance and wallpaper selectors.
- **Compact on/off switches:** All nine password, passphrase and security checkboxes use switches, tested in both states.
- **Refined presentation:** Fonts, icons and spacing updated for Linux and Windows.
- **Persistent update channel:** The chosen Stable/Unstable channel survives installation and restart; other preferences remain separate.
- **Automatic Unstable publication:** GitHub Actions updates the rolling prerelease after Linux and Windows pass, without extra tokens. Only `main` and `unstable` branches remain.
- **Safe, isolated updates:** Separate installers and settings, backups, UAC, size and SHA-256 verification.
- **Existing features preserved:** Local password generation, passphrases, profiles, advanced rules, bilingual UI, clipboard privacy and changelog.

**v0.23.0 is a Stable release.** Unstable remains an explicitly labelled experimental channel.
