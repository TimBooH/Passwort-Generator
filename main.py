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
    QApplication, QCheckBox, QColorDialog, QComboBox, QFileDialog, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSlider, QSpinBox, QVBoxLayout, QWidget,
)

from diagnostics import CrashReporter, default_state_directory
from glass_ui import GlassBackground, GlossyGlassCard, build_glass_stylesheet, IMAGE_MODES
from updater import install_staged_appimage, restart_updated_app, staging_path
from password_core import make_password, parse_version
from version import APP_VERSION, is_newer_release, version_status

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
    def __init__(self, auto_check=True, reporter=None):
        super().__init__()
        self.reporter = reporter
        self.settings = QSettings('TimBooH', 'PasswortGenerator')
        self.network = QNetworkAccessManager(self)
        self.check_reply = None
        self.download_reply = None
        self.save_file = None
        self.download_error = None
        self.download_hash = None
        self.download_bytes = 0
        self.download_target = None
        self.download_stage = None
        self.download_installed = False
        self.latest_version = None
        self.latest_asset = None

        self.setWindowTitle(f'PasswortGenerator v{APP_VERSION}')
        self.resize(740, 810)
        self.setMinimumSize(460, 540)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        self.setCentralWidget(scroll)
        root = GlassBackground()
        root.setObjectName('appRoot')
        self.background_surface = root
        scroll.setWidget(root)
        # A centered column stays readable even when the window becomes ultrawide.
        outer_layout = QHBoxLayout(root)
        outer_layout.setContentsMargins(8, 0, 8, 0)
        outer_layout.setSpacing(0)
        content = QWidget()
        content.setObjectName('contentColumn')
        content.setMinimumWidth(0)
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        outer_layout.addWidget(content, 1)
        # All three panels expand with the window, without a fixed maximum width.
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 18, 12, 22)
        self.glass_cards = []
        self._applied_palette = None
        self._restoring = False

        title = QLabel('PASSWORT GENERATOR')
        title.setObjectName('heroTitle')
        title.setFont(QFont('Sans Serif', 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        subtitle = QLabel(f'Sichere Passwörter lokal erstellen  ·  v{APP_VERSION}  ·  {version_status()}')
        subtitle.setWordWrap(True)
        subtitle.setObjectName('heroSubtitle')
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        layout.addSpacing(8)

        group = GlossyGlassCard('PASSWORT ERSTELLEN')
        self.glass_cards.append(group)
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        group_layout = group.body
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
        self.exclude = QCheckBox('Ähnliche Zeichen ausschließen')
        self.exclude.setToolTip('I, l, 1, O und 0 ausschließen')
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
        layout.addWidget(group, 2)

        colors = GlossyGlassCard('DESIGN & FARBEN')
        self.glass_cards.append(colors)
        colors.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        colors_layout = colors.body
        bg_row = QHBoxLayout()
        bg_row.addWidget(QLabel('Hintergrund:'))
        self.bg_combo = QComboBox()
        for label, color in BACKGROUND_COLORS:
            self.bg_combo.addItem(label, color)
        bg_row.addWidget(self.bg_combo, 1)
        bg_custom = QPushButton('Eigene Farbe …')
        bg_custom.clicked.connect(lambda: self.pick_color(self.bg_combo))
        colors_layout.addLayout(bg_row)
        colors_layout.addWidget(bg_custom, 0, Qt.AlignmentFlag.AlignRight)
        fg_row = QHBoxLayout()
        fg_row.addWidget(QLabel('Text:'))
        self.fg_combo = QComboBox()
        for label, color in TEXT_COLORS:
            self.fg_combo.addItem(label, color)
        fg_row.addWidget(self.fg_combo, 1)
        fg_custom = QPushButton('Eigene Farbe …')
        fg_custom.clicked.connect(lambda: self.pick_color(self.fg_combo))
        colors_layout.addLayout(fg_row)
        colors_layout.addWidget(fg_custom, 0, Qt.AlignmentFlag.AlignRight)
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
        # The chosen image stays on disk; only its path and display mode are stored.
        picture_title = QLabel('Eigenes Hintergrundbild')
        picture_title.setObjectName('supportText')
        colors_layout.addWidget(picture_title)
        picture_actions = QHBoxLayout()
        self.choose_background_button = QPushButton('Bild auswählen …')
        self.choose_background_button.clicked.connect(self.choose_background_image)
        picture_actions.addWidget(self.choose_background_button)
        self.clear_background_button = QPushButton('Bild entfernen')
        self.clear_background_button.clicked.connect(self.remove_background_image)
        picture_actions.addWidget(self.clear_background_button)
        colors_layout.addLayout(picture_actions)
        self.background_file_label = QLabel('Kein Hintergrundbild ausgewählt')
        self.background_file_label.setObjectName('supportText')
        self.background_file_label.setWordWrap(True)
        colors_layout.addWidget(self.background_file_label)
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel('Bilddarstellung:'))
        self.image_mode_combo = QComboBox()
        for label, mode in IMAGE_MODES:
            self.image_mode_combo.addItem(label, mode)
        mode_row.addWidget(self.image_mode_combo, 1)
        colors_layout.addLayout(mode_row)

        colors_note = QLabel('Glas-Effekt und Bilddarstellung werden automatisch gespeichert.')
        colors_note.setWordWrap(True)
        colors_layout.addWidget(colors_note)
        layout.addWidget(colors, 3)

        updates = GlossyGlassCard('UPDATES & VERSIONEN')
        self.glass_cards.append(updates)
        updates.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        updates_layout = updates.body
        repo_label = QLabel('GitHub · TimBooH/Passwort-Generator')
        repo_label.setObjectName('supportText')
        updates_layout.addWidget(repo_label)
        self.update_status = QLabel(f'Installiert: v{APP_VERSION} · Noch nicht geprüft')
        self.update_status.setWordWrap(True)
        updates_layout.addWidget(self.update_status)
        update_actions = QVBoxLayout()
        self.check_button = QPushButton('Auf Updates prüfen')
        self.check_button.clicked.connect(self.check_for_updates)
        update_actions.addWidget(self.check_button)
        self.download_button = QPushButton('Update installieren & neu starten')
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
        update_note = QLabel('Nach erfolgreicher Überprüfung startet die neue Version automatisch. '
                             'Die bisherige Version bleibt als previous AppImage erhalten.')
        update_note.setWordWrap(True)
        updates_layout.addWidget(update_note)
        diagnostic_button = QPushButton('Crash-Log öffnen')
        diagnostic_button.clicked.connect(self.open_crash_log)
        updates_layout.addWidget(diagnostic_button)
        layout.addWidget(updates, 2)

        self.status = QLabel('')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch(0)

        self.bg_combo.currentIndexChanged.connect(self.apply_colors)
        self.fg_combo.currentIndexChanged.connect(self.apply_colors)
        # Slider movement redraws only the glass cards, not the whole QSS tree.
        self.glass_slider.valueChanged.connect(self.update_glass_opacity)
        self.image_mode_combo.currentIndexChanged.connect(self.update_image_mode)
        self.restore_colors()
        self.restore_background_image()
        self.generate()
        if auto_check:
            QTimer.singleShot(800, self.check_for_updates)
        if self.reporter is not None:
            self.reporter.note('UI_STARTED', 'interface ready', force=True)

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
        self._restoring = True
        try:
            self.select_color(self.bg_combo, self.settings.value('background_color', '#101827'), '#101827')
            self.select_color(self.fg_combo, self.settings.value('text_color', '#FFFFFF'), '#FFFFFF')
            try:
                saved = int(self.settings.value('glass_opacity', 54))
            except (TypeError, ValueError):
                saved = 54
            self.glass_slider.setValue(max(30, min(85, saved)))
        finally:
            self._restoring = False
        self.apply_colors()

    def pick_color(self, combo):
        selected = QColorDialog.getColor(QColor(combo.currentData()), self, 'Farbe auswählen')
        if selected.isValid():
            self.select_color(combo, selected.name(), '#101827')

    def open_crash_log(self):
        path = self.reporter.path if self.reporter is not None else default_state_directory() / 'crash.log'
        if not path.exists():
            QMessageBox.information(self, 'Crash-Log', 'Noch kein Fehlerprotokoll vorhanden.')
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.reporter is not None:
            self.reporter.note('RESIZE', f'{self.width()}x{self.height()}')

    def apply_colors(self, *_):
        if self._restoring:
            return
        bg = self.bg_combo.currentData() or '#101827'
        fg = self.fg_combo.currentData() or '#FFFFFF'
        self.background_surface.set_base_color(bg)
        self.update_glass_opacity()
        palette_key = (bg, fg)
        if self._applied_palette != palette_key:
            self._applied_palette = palette_key
            # Replacing the complete stylesheet while a slider repaints dozens
            # of frames is expensive and has caused native Qt instability.
            self.setStyleSheet(build_glass_stylesheet(bg, fg, 54))
            self.settings.setValue('background_color', bg)
            self.settings.setValue('text_color', fg)
            if self.reporter is not None:
                self.reporter.note('PALETTE_CHANGED', f'background={bg}, text={fg}', force=True)

    def update_glass_opacity(self, *_):
        if self._restoring:
            return
        value = self.glass_slider.value()
        background = self.bg_combo.currentData() or '#101827'
        for card in self.glass_cards:
            card.set_glass_color(background, value)
        self.glass_value.setText(f'{value} %')
        self.settings.setValue('glass_opacity', value)
        if self.reporter is not None:
            self.reporter.note('GLASS_OPACITY', f'value={value}')

    def restore_background_image(self):
        mode = self.settings.value('background_image_mode', 'cover', type=str)
        index = self.image_mode_combo.findData(mode)
        self.image_mode_combo.setCurrentIndex(index if index >= 0 else 0)
        path = self.settings.value('background_image_path', '', type=str)
        if path:
            try:
                self.background_surface.set_background_image(path)
                self.background_file_label.setText(Path(path).name)
            except (OSError, ValueError):
                self.background_file_label.setText('Gespeichertes Bild nicht gefunden oder ungültig.')
                self.background_surface.clear_background_image()
        self.clear_background_button.setEnabled(self.background_surface.has_background_image())

    def choose_background_image(self):
        selected, _ = QFileDialog.getOpenFileName(
            self, 'Hintergrundbild auswählen', str(Path.home()),
            'Bilder (*.png *.jpg *.jpeg *.webp *.bmp)',
        )
        if not selected:
            return
        try:
            self.background_surface.set_background_image(selected)
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, 'Hintergrundbild nicht geladen', str(error))
            return
        self.background_file_label.setText(Path(selected).name)
        self.clear_background_button.setEnabled(True)
        self.settings.setValue('background_image_path', selected)
        self.status.setText('Hintergrundbild geladen.')
        if self.reporter is not None:
            self.reporter.note('BACKGROUND_LOADED', f'format={Path(selected).suffix.lower()}', force=True)

    def remove_background_image(self):
        self.background_surface.clear_background_image()
        self.background_file_label.setText('Kein Hintergrundbild ausgewählt')
        self.clear_background_button.setEnabled(False)
        self.settings.remove('background_image_path')
        if self.reporter is not None:
            self.reporter.note('BACKGROUND_REMOVED', force=True)

    def update_image_mode(self, *_):
        mode = self.image_mode_combo.currentData() or 'cover'
        self.background_surface.set_image_mode(mode)
        self.settings.setValue('background_image_mode', mode)
        if self.reporter is not None:
            self.reporter.note('BACKGROUND_MODE', f'mode={mode}', force=True)

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
            if not is_newer_release(latest_version, APP_VERSION):
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
        if self.reporter is not None:
            self.reporter.note('UPDATE_DOWNLOAD_START', f'version={self.latest_version}', force=True)
        self.download_installed = INSTALLED_APPIMAGE.is_file() and os.access(INSTALLED_APPIMAGE.parent, os.W_OK)
        if self.download_installed:
            target = INSTALLED_APPIMAGE
        else:
            download_location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
            download_dir = Path(download_location) if download_location else Path.home() / 'Downloads'
            target = download_dir / f'PasswortGenerator-{self.latest_version}-x86_64.AppImage'
        stage = staging_path(target) if self.download_installed else target
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            save_file = QSaveFile(str(stage))
            if not save_file.open(QIODevice.OpenModeFlag.WriteOnly):
                raise OSError(save_file.errorString())
        except OSError as error:
            QMessageBox.warning(self, 'Download nicht möglich', str(error))
            return

        self.save_file = save_file
        self.download_stage = stage
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
        installed_successfully = False
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
                raise OSError(self.save_file.errorString())
            os.chmod(self.download_stage, 0o755)
            if self.download_installed:
                previous = install_staged_appimage(self.download_stage, self.download_target)
                if self.reporter is not None:
                    self.reporter.note(
                        'UPDATE_INSTALLED',
                        f'version={self.latest_version}, previous={bool(previous)}',
                        force=True,
                    )
            else:
                if self.reporter is not None:
                    self.reporter.note(
                        'UPDATE_DOWNLOADED',
                        f'version={self.latest_version}, standalone=True',
                        force=True,
                    )
            installed_successfully = True
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.update_status.setText(
                f'{self.latest_version} installiert. Die aktualisierte App wird neu gestartet …'
            )
            self.download_button.hide()

            # Start a clean process with a short delay; then shut down old Qt.
            try:
                restart_updated_app(self.download_target)
            except (OSError, ValueError) as error:
                if self.reporter is not None:
                    self.reporter.error('UPDATE_RESTART_FAILED', error)
                msg = (
                    f'Update {self.latest_version} installiert, aber der automatische '
                    f'Neustart ist fehlgeschlagen: {error}\n'
                    'Bitte die App über das KDE-Menü erneut öffnen.'
                )
                self.update_status.setText(msg)
                QMessageBox.warning(self, 'Manueller Neustart erforderlich', msg)
            else:
                if self.reporter is not None:
                    self.reporter.note('UPDATE_RESTART', 'old application will exit', force=True)
                QTimer.singleShot(120, QApplication.instance().quit)
        except (ValueError, OSError, TypeError) as error:
            if self.reporter is not None:
                self.reporter.error('UPDATE_FAILED', error)
            if self.save_file is not None and self.save_file.isOpen():
                self.save_file.cancelWriting()
            self.progress_bar.hide()
            self.update_status.setText(f'Download/Installation fehlgeschlagen: {error}')
            QMessageBox.warning(self, 'Update fehlgeschlagen', str(error))
        finally:
            if not installed_successfully and self.download_installed and self.download_stage:
                try:
                    self.download_stage.unlink(missing_ok=True)
                except OSError:
                    pass
            self.save_file = None
            self.download_stage = None
            reply.deleteLater()


if __name__ == '__main__':
    reporter = CrashReporter()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    reporter.log('QT_ENVIRONMENT', f'Qt platform={app.platformName()}')
    window = PasswordWindow(reporter=reporter)
    app.aboutToQuit.connect(reporter.close)
    heartbeat = QTimer()
    heartbeat.setInterval(15000)
    heartbeat.timeout.connect(reporter.heartbeat)
    heartbeat.start()
    window.show()
    try:
        sys.exit(app.exec())
    finally:
        reporter.close()
