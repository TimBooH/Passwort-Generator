# PasswortGenerator

**Secure passwords and passphrases for Windows and Linux, with a customizable glass-style interface.**

**Language / Sprache:** [Deutsch](README.md) | **English**

[![Release](https://img.shields.io/github/v/release/TimBooH/Passwort-Generator?label=Version)](https://github.com/TimBooH/Passwort-Generator/releases/latest)
[![Linux](https://img.shields.io/github/actions/workflow/status/TimBooH/Passwort-Generator/build-and-release.yml?label=Linux)](https://github.com/TimBooH/Passwort-Generator/actions/workflows/build-and-release.yml)
[![Windows](https://img.shields.io/github/actions/workflow/status/TimBooH/Passwort-Generator/build-windows.yml?label=Windows)](https://github.com/TimBooH/Passwort-Generator/actions/workflows/build-windows.yml)

## Download

| Windows 10/11 (64-bit) | Linux (x86_64, e.g. CachyOS) |
| --- | --- |
| [**Windows installer (.exe)**](https://github.com/TimBooH/Passwort-Generator/releases/download/v0.19.0/PasswortGenerator-Setup-x64.exe) | [**Linux AppImage**](https://github.com/TimBooH/Passwort-Generator/releases/download/v0.19.0/PasswortGenerator-x86_64.AppImage) |

[All releases and installation scripts](https://github.com/TimBooH/Passwort-Generator/releases/latest)

## Preview

![PasswortGenerator with its glass-style interface](assets/screenshots/passwort-generator.png)

## Features

- **Passwords:** 8–128 characters, strength indicator and profiles (Standard, Very secure, Simple and a custom profile).
- **Passphrases:** 4–10 words, configurable separators, and an optional random two-digit number.
- **Glass design:** refined glossy highlights, focus states, color themes and custom wallpapers.
- **Language:** One setting for the entire app, including release notes and update messages. Choose German or English under **Settings → Appearance**; your preference is saved.
- **Updates:** automatic checking with version comparison and a short changes preview, plus the full Changelog below.
- **Security:** optional clipboard clearing after 30, 60 or 120 seconds, only if the copied secret is still there.
- **Usability:** session-only password history, guided tour and saved window size/position. Navigation: Password → Update → Settings → Info.

Passwords are generated locally using Python `secrets`. They are not sent to a server or saved permanently.

## Installation

**Windows:** Download and run the installer. Administrator approval is required; the app is installed to `C:\Program Files\PasswortGenerator`. The installer is not digitally signed, so Windows SmartScreen may show a warning.

**Linux with application-menu entry:** Download `install.sh` from the [latest release](https://github.com/TimBooH/Passwort-Generator/releases/latest) and run it in your downloads folder:

```bash
bash install.sh
```

**Linux without installation:** Run the downloaded AppImage directly:

```bash
chmod +x PasswortGenerator-x86_64.AppImage
./PasswortGenerator-x86_64.AppImage
```

Updates are installed **only after confirmation**. A regular Linux menu installation keeps the previous AppImage as a backup. An internet connection is required for update checks, but not for password generation.

## Development

Built with **Python and PySide6 (Qt 6)**. Run and test locally:

```bash
python -m pip install -r requirements.txt
python main.py
python -m unittest discover -s tests -v
```

Windows installers and Linux AppImages are built using [GitHub Actions](https://github.com/TimBooH/Passwort-Generator/actions).

**Version 0.19.0 · Step 19 of 100 toward the 1.0.0 release.**
[Release notes](RELEASE_NOTES.md) · [Releases](https://github.com/TimBooH/Passwort-Generator/releases)

*Made by Jon Bovi*
