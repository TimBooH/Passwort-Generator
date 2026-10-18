#!/usr/bin/env bash
# Entfernt nur die eigene Benutzerinstallation. Gespeicherte Farben bleiben erhalten.
set -euo pipefail

DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
APP_DIR="${HOME}/.local/opt/passwort-generator"
DESKTOP_FILE="${DATA_HOME}/applications/de.timbooh.passwortgenerator.desktop"
ICON_FILE="${DATA_HOME}/icons/hicolor/scalable/apps/de.timbooh.passwortgenerator.svg"

rm -f "${APP_DIR}/PasswortGenerator.AppImage" "${APP_DIR}/PasswortGenerator-previous.AppImage" "$DESKTOP_FILE" "$ICON_FILE"
# Remove only leftover files managed by this application.
if [[ -d "$APP_DIR" ]]; then
  find "$APP_DIR" -maxdepth 1 -type f -name 'PasswortGenerator*.AppImage' -delete
  find "$APP_DIR" -maxdepth 1 -type f -name '.PasswortGenerator-update-*.AppImage' -delete
fi
rmdir "$APP_DIR" 2>/dev/null || true

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${DATA_HOME}/applications" >/dev/null 2>&1 || true
fi
if command -v kbuildsycoca6 >/dev/null 2>&1; then
  kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
fi
printf 'PasswortGenerator wurde aus dem Anwendungsmenü entfernt.\n'
