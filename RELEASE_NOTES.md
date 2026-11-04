# PasswortGenerator v0.24.0 – Kompakte Oberfläche, Mehrfach-Passwörter und Sicherheitskorrekturen

**Entwicklungsschritt 24 von 100.** Gemeinsamer Release der getesteten Änderungen aus `unstable` für Linux und Windows.

## Deutsch

- **Kompakte Ocean-Glass-Oberfläche:** Neu angeordnetes, kompaktes Hauptfenster mit **Verlauf** und **Einstellungen** oben, Sicherheitsemblem, Versionsanzeige und fünfteiliger Stärkeanzeige.
- **Eigenes Einstellungsfenster:** Erweiterte Passwort-Regeln, Zwischenablageschutz, Sicherheitsanalyse, Update-Bereich mit Kanalwahl und die grafische Erklärung liegen gesammelt in einem separaten Einstellungsfenster.
- **Mehrere Passwörter auf einmal:** Wahlweise 1, 5, 10 oder 20 garantiert unterschiedliche Passwörter mit denselben Regeln erzeugen.
- **Gruppierter Sitzungsverlauf:** Erzeugte Passwörter werden pro Durchgang gruppiert, nur im Arbeitsspeicher gehalten und beim Beenden verworfen.
- **Ähnliche Zeichen ausschließen:** Optional werden leicht verwechselbare Zeichen (`0 O o 1 I l L |`) weggelassen.
- **Countdown der Zwischenablage:** Eine Restzeit zeigt an, wann das kopierte Passwort automatisch entfernt wird.
- **Korrektur – Update-Kanal:** Während eines Update-Downloads lässt sich der Kanal nicht mehr wechseln. Ein Wechsel mitten im Download konnte das Update bisher still abbrechen lassen.
- **Korrektur – Zwischenablage beim Beenden:** Beim Schließen der App, auch beim Neustart nach einem Update, wird ein selbst kopiertes Passwort jetzt gelöscht, sofern das automatische Leeren aktiv ist. Später kopierte Inhalte bleiben unangetastet.
- **Korrektur – Passwortstärke:** Die angezeigte Entropie entspricht jetzt exakt dem Generator, einschließlich Pflichtzeichen und Mindestanzahlen. Bisher wurde die Stärke mit Mindestanzahlen deutlich überschätzt (z. B. Länge 10 mit je 4 Ziffern und Sonderzeichen: 52,9 statt 63,8 Bit, „Mittel“ statt „Stark“).
- **Weitere Funktionen erhalten:** Passphrasen, Profile, Sprache Deutsch/Englisch, getrennte Stable-/Unstable-Installationen, Sicherung der vorherigen AppImage-Version und Prüfung von Dateigröße und SHA-256 bei Updates.

**Stable** ist unter `/releases/latest` verfügbar. **Unstable** bleibt ausdrücklich eine separate Testversion.

## English

- **Compact Ocean Glass interface:** A rearranged, compact main window with **History** and **Settings** at the top, a security emblem, version header and a five-segment strength meter.
- **Separate Settings window:** Advanced password rules, clipboard protection, security analysis, the update panel with channel choice and the illustrated guide are grouped in their own window.
- **Multiple passwords at once:** Generate 1, 5, 10 or 20 guaranteed-unique passwords with the same rules.
- **Grouped session history:** Generated passwords are grouped per run, kept in memory only and discarded on exit.
- **Exclude similar characters:** Optionally omit easily confused characters (`0 O o 1 I l L |`).
- **Clipboard countdown:** A timer shows when the copied password will be cleared automatically.
- **Fix – update channel:** The channel can no longer be switched during an update download; doing so previously could make the update fail silently.
- **Fix – clipboard on exit:** Closing the app, including the restart after an update, now clears a password the app copied, if automatic clearing is enabled. Newer clipboard content is left untouched.
- **Fix – password strength:** The displayed entropy now matches the generator exactly, including mandatory characters and minimum counts. Strength with minimum counts was previously overstated noticeably (e.g. length 10 with 4 digits and 4 symbols: 52.9 instead of 63.8 bits, “Medium” instead of “Strong”).
- **Existing features preserved:** Passphrases, profiles, German/English UI, separate Stable/Unstable installations, backup of the previous AppImage and size and SHA-256 verification of updates.

**Stable** is available at `/releases/latest`. **Unstable** remains an explicitly labelled experimental channel.
