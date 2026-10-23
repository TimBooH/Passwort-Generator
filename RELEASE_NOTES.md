# PasswortGenerator v0.22.0 – Stable / Unstable direkt im Updater

**Entwicklungsschritt 22 von 100.** Eine gemeinsame Stable-Veröffentlichung nach erfolgreichen Tests auf beiden Plattformen.

## Deutsch

- **Update-Kanal auswählbar:** In der bestehenden Kachel „Update & Version“ direkt zwischen **Stable** und **Unstable (Test)** wechseln. Die Auswahl wird gespeichert; die Updateprüfung erfolgt beim Start und anschließend alle zwei Stunden.
- **Unstable ohne ZIP:** Die App erkennt den zuletzt erfolgreichen Test-Build direkt anhand einer Git-Commit-Kennung. Download und Installation erfolgen wie normale Updates mit einem Klick und einer ausdrücklichen Bestätigung für unfertige Testversionen.
- **GitHub-Prerelease:** Unstable-Builds sind öffentlich erreichbare, als **TESTVERSION** gekennzeichnete Prereleases, nicht offizielle Stable-Releases. Erst wenn Linux und Windows beide Tests/Builds bestehen, veröffentlicht GitHub Actions die geprüften Dateien. Stable bleibt bei `/releases/latest` unverändert.
- **Getrennte Installationen:** Unter Linux liegt Unstable neben Stable in `~/.local/opt/passwort-generator-unstable/` und aktualisiert sich künftig selbst. Unter Windows nutzt Unstable eine andere Installer-App-ID, einen separaten Program-Files-Ordner und eigene Verknüpfungen. Stable wird nicht überschrieben.
- **Sichere Downloads:** Strikt geprüfte GitHub-URLs, erwartete Dateinamen, Dateigrößen und SHA-256-Prüfsummen. Keine ausführbare Datei wird installiert, wenn die Verifikation scheitert.
- **Kanal zurückwechseln:** Beim Auswählen von Stable installiert die App den normalen, geprüften Stable-Installer/AppImage. Die andere Installation bleibt bestehen.
- **Zweisprachig:** Deutsch und Englisch im gesamten Update-Bereich. Alle bisherigen Passwortfunktionen, das Ocean-Glass-Design und Einstellungen bleiben erhalten.

**Hinweis:** Unstable-Test-Builds sind bewusst öffentlich abrufbar, aber nicht als offizielle stabile Version freigegeben.

## English

- **Choose update channel:** Switch between **Stable** and **Unstable (test)** directly on the Update page. The choice persists, with startup and two-hour checks.
- **No ZIP downloads:** The app discovers the newest successful test build by its Git commit ID and installs it from GitHub after user confirmation.
- **GitHub prerelease:** The build is clearly labelled **TEST VERSION** and is never the official Stable `/releases/latest`. Both platform builds must pass before preview publication.
- **Separate installations:** Independent Linux AppImage directories and Windows installer app IDs, Program Files paths, and shortcuts; Stable is preserved.
- **Verified downloads:** Exact GitHub release URLs, expected asset names, published byte lengths, and SHA-256 digests are all validated.
- **Return to Stable:** Switching back installs the normal verified Stable package without removing the preview installation.
- **Bilingual interface:** German and English UI, with all existing features and Ocean Glass retained.

**Note:** Preview builds are publicly downloadable, but explicitly experimental and separate from public Stable updates.
