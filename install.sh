#!/usr/bin/env bash
# Benutzerinstallation für KDE Plasma, CachyOS und andere Linux-Desktops.
set -euo pipefail

REPO='TimBooH/Passwort-Generator'
APPIMAGE_NAME='PasswortGenerator-x86_64.AppImage'
BASE_URL="https://github.com/${REPO}/releases/latest/download"
INSTALL_DIR="${HOME}/.local/opt/passwort-generator"
APPIMAGE_TARGET="${INSTALL_DIR}/PasswortGenerator.AppImage"
DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
DESKTOP_DIR="${DATA_HOME}/applications"
ICON_DIR="${DATA_HOME}/icons/hicolor/scalable/apps"
DESKTOP_FILE="${DESKTOP_DIR}/de.timbooh.passwortgenerator.desktop"
ICON_FILE="${ICON_DIR}/de.timbooh.passwortgenerator.svg"

usage() {
  printf 'Verwendung: %s [--file /pfad/PasswortGenerator.AppImage]\n' "$0"
  printf 'Ohne --file wird die aktuellste Version von GitHub geladen.\n'
}

if [[ "${1:-}" == '--help' || "${1:-}" == '-h' ]]; then
  usage
  exit 0
fi
if [[ $# -ne 0 && ( $# -ne 2 || "${1:-}" != '--file' ) ]]; then
  usage >&2
  exit 2
fi

for path in "$INSTALL_DIR" "$DESKTOP_DIR" "$ICON_DIR"; do
  mkdir -p "$path"
done

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

if [[ $# -eq 2 ]]; then
  SOURCE="${2}"
  if [[ ! -f "$SOURCE" ]]; then
    printf 'AppImage nicht gefunden: %s\n' "$SOURCE" >&2
    exit 1
  fi
else
  SOURCE="$TEMP_DIR/$APPIMAGE_NAME"
  printf 'Lade aktuelle Version von GitHub herunter: %s\n' "$REPO"
  if command -v curl >/dev/null 2>&1; then
    curl --fail --location --retry 3 --silent --show-error \
      "$BASE_URL/$APPIMAGE_NAME" -o "$SOURCE"
    curl --fail --location --retry 3 --silent --show-error \
      "$BASE_URL/SHA256SUMS" -o "$TEMP_DIR/SHA256SUMS"
  elif command -v wget >/dev/null 2>&1; then
    wget --quiet -O "$SOURCE" "$BASE_URL/$APPIMAGE_NAME"
    wget --quiet -O "$TEMP_DIR/SHA256SUMS" "$BASE_URL/SHA256SUMS"
  else
    printf 'Für den Download wird curl oder wget benötigt.\n' >&2
    exit 1
  fi
  (cd "$TEMP_DIR" && sha256sum -c SHA256SUMS)
fi

# Die Datei nur installieren, nicht ausführen. Prüfgrundlage: AppImage ELF-Header.
if [[ "$(head -c 4 "$SOURCE" | od -An -tx1 | tr -d ' \n')" != '7f454c46' ]]; then
  printf 'Datei ist kein gültiges Linux-ELF/AppImage: %s\n' "$SOURCE" >&2
  exit 1
fi

TEMP_APPIMAGE="${INSTALL_DIR}/.PasswortGenerator.AppImage.new.$$"
trap 'rm -f "$TEMP_APPIMAGE"; rm -rf "$TEMP_DIR"' EXIT
install -m 0755 "$SOURCE" "$TEMP_APPIMAGE"
mv -f "$TEMP_APPIMAGE" "$APPIMAGE_TARGET"

cat > "$ICON_FILE" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <rect width="256" height="256" rx="52" fill="#142c47"/>
  <path d="M80 112V85a48 48 0 0 1 96 0v27" fill="none" stroke="#6bddc4" stroke-width="18" stroke-linecap="round"/>
  <rect x="55" y="108" width="146" height="111" rx="24" fill="#f1f6fc"/>
  <circle cx="128" cy="157" r="13" fill="#142c47"/>
  <path d="M128 167v24" stroke="#142c47" stroke-width="12" stroke-linecap="round"/>
  <circle cx="193" cy="60" r="10" fill="#6bddc4"/>
</svg>
SVG

cat > "$DESKTOP_FILE" <<DESKTOP
[Desktop Entry]
Type=Application
Version=1.0
Name=PasswortGenerator
GenericName=Passwortgenerator
Comment=Sichere Passwörter lokal erstellen
Exec="${APPIMAGE_TARGET}"
TryExec=${APPIMAGE_TARGET}
Icon=de.timbooh.passwortgenerator
Terminal=false
StartupNotify=true
Categories=Utility;Security;
DESKTOP
chmod 0644 "$DESKTOP_FILE"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi
if command -v kbuildsycoca6 >/dev/null 2>&1; then
  kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
fi

printf '\nPasswortGenerator installiert!\n'
printf 'Startmenü: PasswortGenerator\n'
printf 'AppImage: %s\n' "$APPIMAGE_TARGET"
printf 'Deinstallation: ./uninstall.sh\n'
