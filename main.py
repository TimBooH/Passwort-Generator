"""PasswortGenerator: lokale Passworterzeugung mit Update-Download von GitHub."""

import hashlib
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QIODevice, QSettings, QStandardPaths, Qt, QTimer, QUrl, QSaveFile
from PySide6.QtGui import QColor, QDesktopServices, QFont
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QColorDialog, QComboBox, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSlider, QSpinBox, QVBoxLayout, QWidget,
)

from glass_ui import GlassBackground, apply_glass_shadow, build_glass_stylesheet
from password_core import make_password, parse_version
from version import APP_VERSION

REPO = 'TimBooH/Passwort-Generator'
REPO_URL = f'https://github.com/{REPO}'
LATEST_RELEASE_API = f'https://api.github.com/repos/{REPO}/releases/latest'
RELEASE_DOWNLOAD_PREFIX = f'https://github.com/{REPO}/releases/download/'
RELEASES_URL = f'{REPO_URL}/releases'
APPIMAGE_NAME = 'PasswortGenerator-x86_64.AppImage'
INSTALLED_APPIMAGE = Path.home() / '.local/opt/passwort-generator/PasswortGenerator.AppImage'

BACKGROUND_COLORS = [
    ('Nachtblau', '#101827'), ('Anthrazit', '#20242C'), ('Schwarz', '#111111'),
    ('Dunkelgrün', '#123329'), ('Dunkelrot', '#351A23'), ('Violett', '#2A1D45'),
    ('Hellgrau', '#F1F4F8'), ('Weiß', '#FFFFFF'), ('Sand', '#F5EDDB'),
    ('Eisblau', '#E5F3FA'),
]
TEXT_COLORS = [
    ('Weiß', '#FFFFFF'), ('Hellgrau', '#DAE1EA'), ('Schwarz', '#121820'),
    ('Dunkelblau', '#17355D'), ('Cyan', '#63DDF5'), ('Mint', '#8EF0C2'),
    ('Gelb', '#FFE58A'), ('Rosa', '#FFB9D6'), ('Orange', '#FFBC80'),
]


def contrast_color(hex_color):
    color = QColor(hex_color)
    luminance = 0.2126 * color.redF() + 0.7152 * color.greenF() + 0.0722 * color.blueF()
    return '#151A21' if luminance > 0.58 else '#FFFFFF'


def field_color(hex_color):
    color = QColor(hex_color)
    return color.lighter(135).name() if contrast_color(hex_color) == '#FFFFFF' else color.darker(105).name()


class PasswordWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('TimBooH', 'PasswortGenerator')
        self.network = QNetworkAccessManager(self)
        self.check_reply = None
        self.download_reply = None
        self.save_file = None
        self.download_error = None
        self.download_hash = None
        self.download_bytes = 0
        self.download_target = None
        self.download_installed = False
        self.latest_version = None
        self.latest_asset = None

        self.setWindowTitle(f'PasswortGenerator v{APP_VERSION}')
        self.resize(720, 820)
        self.setMinimumSize(540, 610)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        self.setCentralWidget(scroll)
        root = GlassBackground()
        root.setObjectName('appRoot')
        self.background_surface = root
        scroll.setWidget(root)
        layout = QVBoxLayout(root)
        layout.setSpacing(18)
        layout.setContentsMargins(34, 24, 34, 28)

        title = QLabel('PASSWORT GENERATOR')
        title.setObjectName('heroTitle')
        title.setFont(QFont('Sans Serif', 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        subtitle = QLabel(f'Sichere Passwörter lokal erstellen  ·  v{APP_VERSION}')
        subtitle.setObjectName('heroSubtitle')
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        glass_badge = QLabel('✦  GLASS EDITION  ✦')
        glass_badge.setObjectName('glassTag')
        glass_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(glass_badge, 0, Qt.AlignmentFlag.AlignHCenter)

        group = QGroupBox('Passwort erstellen')
        group.setObjectName('passwordPanel')
        apply_glass_shadow(group)
        group_layout = QVBoxLayout(group)
        self.output = QLineEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(44)
        self.output.setFont(QFont('Monospace', 13))
        group_layout.addWidget(self.output)
        length_row = QHBoxLayout()
        length_row.addWidget(QLabel('Passwortlänge:'))
        self.length = QSpinBox()
        self.length.setRange(8, 128)
        self.length.setValue(20)
        length_row.addWidget(self.length)
        length_row.addStretch()
        group_layout.addLayout(length_row)
        self.lower = QCheckBox('Kleinbuchstaben (a–z)')
        self.upper = QCheckBox('Großbuchstaben (A–Z)')
        self.digits = QCheckBox('Zahlen (0–9)')
        self.symbols = QCheckBox('Sonderzeichen')
        self.exclude = QCheckBox('Ähnliche Zeichen ausschließen (I, l, 1, O, 0)')
        for control in (self.lower, self.upper, self.digits, self.symbols):
            control.setChecked(True)
        for control in (self.lower, self.upper, self.digits, self.symbols, self.exclude):
            group_layout.addWidget(control)
        actions = QHBoxLayout()
        generate_button = QPushButton('Neues Passwort')
        generate_button.setObjectName('primaryButton')
        generate_button.clicked.connect(self.generate)
        actions.addWidget(generate_button)
        copy_button = QPushButton('Kopieren')
        copy_button.clicked.connect(self.copy)
        actions.addWidget(copy_button)
        group_layout.addLayout(actions)
        layout.addWidget(group)

        colors = QGroupBox('Design & Farben')
        colors.setObjectName('appearancePanel')
        apply_glass_shadow(colors)
        colors_layout = QVBoxLayout(colors)
        bg_row = QHBoxLayout()
        bg_row.addWidget(QLabel('Hintergrund:'))
        self.bg_combo = QComboBox()
        for label, color in BACKGROUND_COLORS:
            self.bg_combo.addItem(label, color)
        bg_row.addWidget(self.bg_combo, 1)
        bg_custom = QPushButton('Eigene Farbe …')
        bg_custom.clicked.connect(lambda: self.pick_color(self.bg_combo))
        bg_row.addWidget(bg_custom)
        colors_layout.addLayout(bg_row)
        fg_row = QHBoxLayout()
        fg_row.addWidget(QLabel('Text:'))
        self.fg_combo = QComboBox()
        for label, color in TEXT_COLORS:
            self.fg_combo.addItem(label, color)
        fg_row.addWidget(self.fg_combo, 1)
        fg_custom = QPushButton('Eigene Farbe …')
        fg_custom.clicked.connect(lambda: self.pick_color(self.fg_combo))
        fg_row.addWidget(fg_custom)
        colors_layout.addLayout(fg_row)
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel('Glas-Deckkraft:'))
        self.glass_slider = QSlider(Qt.Orientation.Horizontal)
        self.glass_slider.setRange(30, 85)
        self.glass_slider.setValue(54)
        self.glass_slider.setToolTip('Niedriger = durchscheinendere Glasflächen, höher = milchiger.')
        opacity_row.addWidget(self.glass_slider, 1)
        self.glass_value = QLabel('54 %')
        self.glass_value.setMinimumWidth(40)
        opacity_row.addWidget(self.glass_value)
        colors_layout.addLayout(opacity_row)
        colors_note = QLabel('Milchglas-Panels, sanfte Lichtreflexe und deine eigenen Farben – automatisch gespeichert.')
        colors_note.setWordWrap(True)
        colors_layout.addWidget(colors_note)
        layout.addWidget(colors)

        updates = QGroupBox('Updates · GitHub: TimBooH/Passwort-Generator')
        updates.setObjectName('updatePanel')
        apply_glass_shadow(updates)
        updates_layout = QVBoxLayout(updates)
        self.update_status = QLabel(f'Installiert: v{APP_VERSION} · Noch nicht geprüft')
        self.update_status.setWordWrap(True)
        updates_layout.addWidget(self.update_status)
        update_actions = QHBoxLayout()
        self.check_button = QPushButton('Auf Updates prüfen')
        self.check_button.clicked.connect(self.check_for_updates)
        update_actions.addWidget(self.check_button)
        self.download_button = QPushButton('Update herunterladen')
        self.download_button.setObjectName('primaryButton')
        self.download_button.clicked.connect(self.download_update)
        self.download_button.hide()
        update_actions.addWidget(self.download_button)
        updates_layout.addLayout(update_actions)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        updates_layout.addWidget(self.progress_bar)
        update_note = QLabel('Ein Klick lädt die neue AppImage-Version direkt von GitHub. '
                             'Bei Menü-Installation wird sie ersetzt und ist beim nächsten Start aktiv.')
        update_note.setWordWrap(True)
        updates_layout.addWidget(update_note)
        layout.addWidget(updates)

        self.status = QLabel('')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch()

        self.bg_combo.currentIndexChanged.connect(self.apply_colors)
        self.fg_combo.currentIndexChanged.connect(self.apply_colors)
        self.glass_slider.valueChanged.connect(self.apply_colors)
        self.restore_colors()
        self.generate()
        QTimer.singleShot(800, self.check_for_updates)

    @staticmethod
    def select_color(combo, color, default):
        if not QColor(color).isValid():
            color = default
        normalized = QColor(color).name().upper()
        for index in range(combo.count()):
            if combo.itemData(index).upper() == normalized:
                combo.setCurrentIndex(index)
                return
        combo.addItem(f'Eigene Farbe ({normalized})', normalized)
        combo.setCurrentIndex(combo.count() - 1)

    def restore_colors(self):
        self.select_color(self.bg_combo, self.settings.value('background_color', '#101827'), '#101827')
        self.select_color(self.fg_combo, self.settings.value('text_color', '#FFFFFF'), '#FFFFFF')
        saved_glass = self.settings.value('glass_opacity', 54, type=int)
        self.glass_slider.setValue(max(30, min(85, saved_glass)))
        self.apply_colors()

    def pick_color(self, combo):
        selected = QColorDialog.getColor(QColor(combo.currentData()), self, 'Farbe auswählen')
        if selected.isValid():
            self.select_color(combo, selected.name(), '#101827')

    def apply_colors(self, *_):
        bg = self.bg_combo.currentData() or '#101827'
        fg = self.fg_combo.currentData() or '#FFFFFF'
        opacity = self.glass_slider.value()
        self.background_surface.set_base_color(bg)
        self.setStyleSheet(build_glass_stylesheet(bg, fg, opacity))
        self.glass_value.setText(f'{opacity} %')
        self.settings.setValue('background_color', bg)
        self.settings.setValue('text_color', fg)
        self.settings.setValue('glass_opacity', opacity)

    def generate(self):
        try:
            password = make_password(
                self.length.value(), use_lower=self.lower.isChecked(),
                use_upper=self.upper.isChecked(), use_digits=self.digits.isChecked(),
                use_symbols=self.symbols.isChecked(), exclude_similar=self.exclude.isChecked(),
            )
        except ValueError as error:
            QMessageBox.warning(self, 'Auswahl fehlt', str(error))
            return
        self.output.setText(password)
        self.status.setText('Passwort erstellt.')

    def copy(self):
        if self.output.text():
            QApplication.clipboard().setText(self.output.text())
            self.status.setText('Passwort in die Zwischenablage kopiert.')

    @staticmethod
    def make_request(url):
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b'User-Agent', b'PasswortGenerator-UpdateChecker')
        request.setRawHeader(b'Accept', b'application/vnd.github+json')
        request.setTransferTimeout(30000)
        return request

    def check_for_updates(self):
        if self.check_reply is not None or self.download_reply is not None:
            return
        self.check_button.setEnabled(False)
        self.download_button.hide()
        self.update_status.setText(f'Installiert: v{APP_VERSION} · Prüfe GitHub …')
        self.check_reply = self.network.get(self.make_request(LATEST_RELEASE_API))
        self.check_reply.finished.connect(self.check_finished)

    def check_finished(self):
        reply = self.check_reply
        self.check_reply = None
        self.check_button.setEnabled(True)
        if reply is None:
            return
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                raise ValueError(reply.errorString())
            response = json.loads(bytes(reply.readAll()).decode('utf-8'))
            latest_version = response.get('tag_name', '')
            current_number = parse_version(APP_VERSION)
            newest_number = parse_version(latest_version)
            if newest_number is None or current_number is None:
                raise ValueError('Ungültige Versionsnummer bei GitHub.')
            if newest_number <= current_number:
                self.latest_asset = None
                self.update_status.setText(f'v{APP_VERSION} ist aktuell. Kein Update verfügbar.')
                return
            assets = response.get('assets', [])
            asset = next((item for item in assets if item.get('name') == APPIMAGE_NAME), None)
            if asset is None:
                raise ValueError('Im neuesten Release ist noch kein Linux-AppImage vorhanden.')
            url = asset.get('browser_download_url', '')
            if not url.startswith(RELEASE_DOWNLOAD_PREFIX) or not url.endswith('/' + APPIMAGE_NAME):
                raise ValueError('Der GitHub-Downloadlink ist ungültig.')
            self.latest_asset = asset
            self.latest_version = latest_version
            self.update_status.setText(f'Neue Version {latest_version} verfügbar! Installiert: v{APP_VERSION}')
            self.download_button.show()
        except (ValueError, TypeError, KeyError, UnicodeDecodeError) as error:
            self.latest_asset = None
            self.update_status.setText(f'Updateprüfung fehlgeschlagen: {error}')
        finally:
            reply.deleteLater()

    def download_update(self):
        if self.download_reply is not None or not self.latest_asset:
            return
        self.download_installed = INSTALLED_APPIMAGE.is_file() and os.access(INSTALLED_APPIMAGE.parent, os.W_OK)
        if self.download_installed:
            target = INSTALLED_APPIMAGE
        else:
            download_location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
            download_dir = Path(download_location) if download_location else Path.home() / 'Downloads'
            target = download_dir / f'PasswortGenerator-{self.latest_version}-x86_64.AppImage'
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            save_file = QSaveFile(str(target))
            if not save_file.open(QIODevice.OpenModeFlag.WriteOnly):
                raise OSError(save_file.errorString())
        except OSError as error:
            QMessageBox.warning(self, 'Download nicht möglich', str(error))
            return

        self.save_file = save_file
        self.download_target = target
        self.download_hash = hashlib.sha256()
        self.download_bytes = 0
        self.download_error = None
        self.download_button.setEnabled(False)
        self.check_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.update_status.setText(f'Lade {self.latest_version} von GitHub herunter …')
        self.download_reply = self.network.get(self.make_request(self.latest_asset['browser_download_url']))
        self.download_reply.readyRead.connect(self.read_download_data)
        self.download_reply.downloadProgress.connect(self.on_download_progress)
        self.download_reply.finished.connect(self.download_finished)

    def read_download_data(self):
        if self.download_reply is None or self.save_file is None:
            return
        data = bytes(self.download_reply.readAll())
        if not data:
            return
        if self.save_file.write(data) != len(data):
            self.download_error = 'Die neue Version konnte nicht vollständig gespeichert werden.'
            self.download_reply.abort()
            return
        self.download_hash.update(data)
        self.download_bytes += len(data)

    def on_download_progress(self, received, total):
        if total > 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(min(100, int(100 * received / total)))
        else:
            self.progress_bar.setRange(0, 0)

    def download_finished(self):
        reply = self.download_reply
        if reply is None:
            return
        self.read_download_data()
        self.download_reply = None
        self.download_button.setEnabled(True)
        self.check_button.setEnabled(True)
        try:
            if self.download_error:
                raise ValueError(self.download_error)
            if reply.error() != QNetworkReply.NetworkError.NoError:
                raise ValueError(reply.errorString())
            if self.download_bytes != int(self.latest_asset.get('size', -1)):
                raise ValueError('Die Dateigröße stimmt nicht mit dem GitHub-Release überein.')
            expected_digest = self.latest_asset.get('digest', '')
            if not expected_digest.startswith('sha256:'):
                raise ValueError('GitHub hat keine SHA-256-Prüfsumme für dieses Release bereitgestellt.')
            actual_digest = self.download_hash.hexdigest()
            if actual_digest.lower() != expected_digest.split(':', 1)[1].lower():
                raise ValueError('Die SHA-256-Prüfsumme stimmt nicht überein!')
            if not self.save_file.commit():
                raise ValueError(self.save_file.errorString())
            os.chmod(self.download_target, 0o755)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            if self.download_installed:
                message = (f'{self.latest_version} wurde installiert. Schließe den PasswortGenerator '
                           'und öffne ihn über das Anwendungsmenü erneut.')
            else:
                message = (f'{self.latest_version} wurde gespeichert:\n{self.download_target}\n'
                           'Starte das AppImage oder installiere es mit install.sh --file.')
            self.update_status.setText(message)
            QMessageBox.information(self, 'Update heruntergeladen', message)
            self.download_button.hide()
        except (ValueError, OSError, TypeError) as error:
            if self.save_file is not None:
                self.save_file.cancelWriting()
            self.progress_bar.hide()
            self.update_status.setText(f'Download fehlgeschlagen: {error}')
            QMessageBox.warning(self, 'Update fehlgeschlagen', str(error))
        finally:
            self.save_file = None
            reply.deleteLater()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = PasswordWindow()
    window.show()
    sys.exit(app.exec())
