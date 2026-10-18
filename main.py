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
    QApplication, QButtonGroup, QCheckBox, QColorDialog, QComboBox, QDialog,
    QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QMainWindow, QMessageBox, QProgressBar, QPushButton, QScrollArea, QSizePolicy,
    QSlider, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)

from diagnostics import CrashReporter, default_state_directory
from glass_ui import GlassBackground, GlossyGlassCard, build_glass_stylesheet, IMAGE_MODES
from neon_style import neon_stylesheet
from updater import install_staged_appimage, restart_updated_app, staging_path
from password_core import make_password, make_passphrase, estimate_strength, parse_version
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
        self._phrase_mode = False
        self._history = []  # Session-only, never persisted to QSettings or disk.

        self.setWindowTitle(f'Passwort-Generator v{APP_VERSION}')
        self.resize(730, 880)
        self.setMinimumSize(460, 540)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setCentralWidget(scroll)
        root = GlassBackground()
        root.setObjectName('appRoot')
        self.background_surface = root
        scroll.setWidget(root)
        outer_layout = QHBoxLayout(root)
        outer_layout.setContentsMargins(7, 0, 7, 0)
        outer_layout.setSpacing(0)

        content = QWidget(root)
        content.setObjectName('contentColumn')
        content.setMinimumWidth(0)
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        outer_layout.addWidget(content, 1)
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(12, 15, 12, 14)
        self.glass_cards = []
        self._applied_palette = None
        self._restoring = False

        # Logo, heading and settings action follow the reference composition.
        header = QHBoxLayout()
        header.setSpacing(13)
        lock = QLabel('🔒')
        lock.setObjectName('brandLock')
        lock.setFixedSize(73, 73)
        lock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(lock)
        heading = QVBoxLayout()
        heading.setSpacing(3)
        brand = QLabel('Passwort-Generator')
        brand.setObjectName('brandTitle')
        brand.setWordWrap(True)
        heading.addWidget(brand)
        subtitle = QLabel('Stark. Sicher. Einzigartig.')
        subtitle.setObjectName('brandSubtitle')
        heading.addWidget(subtitle)
        header.addLayout(heading, 1)
        self.settings_shortcut = QPushButton('⚙ Einstellungen')
        self.settings_shortcut.setObjectName('headerSettings')
        self.settings_shortcut.setToolTip('Design und Farben öffnen')
        header.addWidget(self.settings_shortcut, 0, Qt.AlignmentFlag.AlignTop)
        content_layout.addLayout(header)
        content_layout.addSpacing(5)

        # Three real pages stay available, with compact tabs at the upper left.
        self.tabs = QTabWidget(content)
        self.tabs.setObjectName('mainTabs')
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setExpanding(False)
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout.addWidget(self.tabs, 1)
        self.settings_shortcut.clicked.connect(lambda: self.tabs.setCurrentIndex(1))

        self.password_page = QWidget()
        self.password_page.setObjectName('passwordPage')
        layout = QVBoxLayout(self.password_page)
        layout.setSpacing(8)
        layout.setContentsMargins(4, 10, 4, 8)

        group = GlossyGlassCard('PASSWORT ERSTELLEN')
        group.header.hide()  # The reference uses its own prominent mode toggle.
        group.highlight.hide()
        self.glass_cards.append(group)
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        group_layout = group.body
        group_layout.setSpacing(12)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(6)
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.password_mode_button = QPushButton('Passwort')
        self.passphrase_mode_button = QPushButton('Passphrase')
        for button in (self.password_mode_button, self.passphrase_mode_button):
            button.setObjectName('modeButton')
            button.setCheckable(True)
            button.setMinimumHeight(35)
            self.mode_group.addButton(button)
            mode_row.addWidget(button, 1)
        self.password_mode_button.setChecked(True)
        self.password_mode_button.clicked.connect(lambda: self.switch_mode(False))
        self.passphrase_mode_button.clicked.connect(lambda: self.switch_mode(True))
        group_layout.addLayout(mode_row)

        password_row = QHBoxLayout()
        password_row.setSpacing(7)
        self.output = QLineEdit()
        self.output.setObjectName('passwordOutput')
        self.output.setReadOnly(True)
        self.output.setEchoMode(QLineEdit.EchoMode.Password)
        self.output.setPlaceholderText('Generiertes Passwort')
        self.output.setMinimumHeight(47)
        self.output.setFont(QFont('Monospace', 12))
        password_row.addWidget(self.output, 1)
        copy_top = QPushButton('⧉')
        copy_top.setObjectName('squareAction')
        copy_top.setToolTip('Passwort kopieren')
        copy_top.setMinimumSize(43, 47)
        copy_top.clicked.connect(self.copy)
        password_row.addWidget(copy_top)
        regenerate = QPushButton('↻')
        regenerate.setObjectName('squareAction')
        regenerate.setToolTip('Neues Passwort erzeugen')
        regenerate.setMinimumSize(43, 47)
        regenerate.clicked.connect(self.generate)
        password_row.addWidget(regenerate)
        group_layout.addLayout(password_row)

        strength_row = QHBoxLayout()
        self.strength_label = QLabel('🛡  Stärke: --')
        self.strength_label.setObjectName('strengthCaption')
        strength_row.addWidget(self.strength_label)
        strength_row.addStretch()
        group_layout.addLayout(strength_row)
        self.strength_bar = QProgressBar()
        self.strength_bar.setObjectName('strengthBar')
        self.strength_bar.setRange(0, 100)
        self.strength_bar.setValue(0)
        self.strength_bar.setTextVisible(False)
        group_layout.addWidget(self.strength_bar)
        group_layout.addSpacing(5)

        length_row = QHBoxLayout()
        length_row.setSpacing(5)
        self.length_label = QLabel('Länge:')
        self.length_label.setObjectName('lengthCaption')
        length_row.addWidget(self.length_label)
        self.length_value = QLabel('20')
        self.length_value.setObjectName('lengthValue')
        length_row.addWidget(self.length_value)
        length_row.addStretch()
        self.length = QSpinBox()
        self.length.setRange(8, 128)
        self.length.setValue(20)
        self.length.setFixedWidth(76)
        self.length.setAccessibleName('Länge des Passworts')
        length_row.addWidget(self.length)
        group_layout.addLayout(length_row)
        self.length_slider = QSlider(Qt.Orientation.Horizontal)
        self.length_slider.setRange(8, 128)
        self.length_slider.setValue(20)
        self.length_slider.setAccessibleName('Länge einstellen')
        self.length.valueChanged.connect(self.length_slider.setValue)
        self.length_slider.valueChanged.connect(self.length.setValue)
        self.length.valueChanged.connect(lambda value: self.length_value.setText(str(value)))
        group_layout.addWidget(self.length_slider)
        group_layout.addSpacing(4)

        self.options_widget = QWidget()
        self.options_widget.setObjectName('passwordOptions')
        check_layout = QGridLayout(self.options_widget)
        check_layout.setContentsMargins(0, 0, 0, 0)
        check_layout.setHorizontalSpacing(9)
        check_layout.setVerticalSpacing(3)
        self.upper = QCheckBox('Großbuchstaben (A–Z)')
        self.lower = QCheckBox('Kleinbuchstaben (a–z)')
        self.digits = QCheckBox('Zahlen (0–9)')
        self.symbols = QCheckBox('Sonderzeichen')
        self.exclude = QCheckBox('Ähnliche Zeichen vermeiden')
        self.exclude.setToolTip('I, l, 1, O und 0 ausschließen')
        for control in (self.upper, self.lower, self.digits, self.symbols, self.exclude):
            control.setChecked(True)
        check_layout.addWidget(self.upper, 0, 0)
        check_layout.addWidget(self.lower, 1, 0)
        check_layout.addWidget(self.digits, 2, 0)
        check_layout.addWidget(self.symbols, 0, 1)
        check_layout.addWidget(self.exclude, 1, 1)
        group_layout.addWidget(self.options_widget)
        group_layout.addStretch(1)

        self.generate_button = QPushButton('🔑  Passwort generieren')
        self.generate_button.setObjectName('primaryButton')
        self.generate_button.setMinimumHeight(58)
        self.generate_button.clicked.connect(self.generate)
        group_layout.addWidget(self.generate_button)

        footer = QHBoxLayout()
        footer.setSpacing(7)
        self.show_button = QPushButton('◉  Anzeigen')
        self.show_button.setObjectName('bottomAction')
        self.show_button.setCheckable(True)
        self.show_button.toggled.connect(self.toggle_visibility)
        footer.addWidget(self.show_button, 1)
        self.history_button = QPushButton('☷  Verlauf')
        self.history_button.setObjectName('bottomAction')
        self.history_button.clicked.connect(self.show_history)
        footer.addWidget(self.history_button, 1)
        self.info_button = QPushButton('ⓘ  Info')
        self.info_button.setObjectName('bottomAction')
        self.info_button.clicked.connect(self.show_info)
        footer.addWidget(self.info_button, 1)
        group_layout.addLayout(footer)
        layout.addWidget(group, 1)

        self.settings_page = QWidget()
        self.settings_page.setObjectName('settingsPage')
        settings_page_layout = QVBoxLayout(self.settings_page)
        settings_page_layout.setSpacing(12)
        settings_page_layout.setContentsMargins(4, 10, 4, 8)

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

        colors_note = QLabel('Farben und Bilddarstellung werden automatisch gespeichert.')
        colors_note.setWordWrap(True)
        colors_layout.addWidget(colors_note)
        settings_page_layout.addWidget(colors, 1)
        settings_page_layout.addStretch(0)

        self.updates_page = QWidget()
        self.updates_page.setObjectName('updatesPage')
        updates_page_layout = QVBoxLayout(self.updates_page)
        updates_page_layout.setSpacing(12)
        updates_page_layout.setContentsMargins(4, 10, 4, 8)

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
        updates_page_layout.addWidget(updates, 1)
        updates_page_layout.addStretch(0)


        self.tabs.addTab(self.password_page, 'Passwort')
        self.tabs.addTab(self.settings_page, 'Einstellungen')
        self.tabs.addTab(self.updates_page, 'Updates')
        self.tabs.setCurrentIndex(0)

        self.status = QLabel('')
        self.status.setObjectName('globalStatus')
        self.status.setWordWrap(True)
        content_layout.addWidget(self.status)

        self.bg_combo.currentIndexChanged.connect(self.apply_colors)
        self.fg_combo.currentIndexChanged.connect(self.apply_colors)
        self.image_mode_combo.currentIndexChanged.connect(self.update_image_mode)
        self.restore_colors()
        self.restore_background_image()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        if auto_check:
            QTimer.singleShot(800, self.check_for_updates)
        if self.reporter is not None:
            self.reporter.note('UI_STARTED', 'neon interface ready', force=True)

    def switch_mode(self, use_passphrase):
        """Switch between a random-character password and a word passphrase."""
        self._phrase_mode = bool(use_passphrase)
        self.password_mode_button.setChecked(not self._phrase_mode)
        self.passphrase_mode_button.setChecked(self._phrase_mode)
        self.options_widget.setVisible(not self._phrase_mode)
        if self._phrase_mode:
            self.length_label.setText('Wörter:')
            self.length.setRange(4, 10)
            self.length_slider.setRange(4, 10)
            self.length.setValue(6)
            self.generate_button.setText('🔑  Passphrase generieren')
            self.output.setPlaceholderText('Generierte Passphrase')
        else:
            self.length_label.setText('Länge:')
            self.length.setRange(8, 128)
            self.length_slider.setRange(8, 128)
            self.length.setValue(20)
            self.generate_button.setText('🔑  Passwort generieren')
            self.output.setPlaceholderText('Generiertes Passwort')
        self.output.clear()
        self.strength_label.setText('🛡  Stärke: --')
        self.strength_bar.setValue(0)
        self.status.setText('')
        if self.reporter is not None:
            self.reporter.note('MODE_CHANGED', 'passphrase' if self._phrase_mode else 'password', force=True)

    def toggle_visibility(self, visible):
        self.output.setEchoMode(
            QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        )
        self.show_button.setText('◉  Verbergen' if visible else '◉  Anzeigen')

    def show_history(self):
        """Show only passwords from this session; never persist history."""
        dialog = QDialog(self)
        dialog.setWindowTitle('Verlauf – nur diese Sitzung')
        dialog.resize(560, 360)
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        explanation = QLabel(
            'Maximal 20 Einträge. Der Verlauf wird beim Schließen der App gelöscht.'
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        entries = QListWidget()
        for kind, secret in reversed(self._history):
            entries.addItem(f'{kind}: {secret}')
        layout.addWidget(entries, 1)
        actions = QHBoxLayout()
        copy_button = QPushButton('Ausgewähltes kopieren')
        copy_button.setEnabled(bool(self._history))

        def copy_selected():
            item = entries.currentRow()
            if item < 0:
                return
            secret = self._history[-1 - item][1]
            QApplication.clipboard().setText(secret)
            dialog.accept()
            self.status.setText('Eintrag aus dem Verlauf kopiert.')

        copy_button.clicked.connect(copy_selected)
        actions.addWidget(copy_button)
        clear_button = QPushButton('Verlauf löschen')

        def clear_history():
            self._history.clear()
            entries.clear()
            copy_button.setEnabled(False)

        clear_button.clicked.connect(clear_history)
        actions.addWidget(clear_button)
        close_button = QPushButton('Schließen')
        close_button.clicked.connect(dialog.accept)
        actions.addWidget(close_button)
        layout.addLayout(actions)
        dialog.exec()

    def show_info(self):
        QMessageBox.information(
            self, 'Über Passwort-Generator',
            f'Passwort-Generator v{APP_VERSION}\n{version_status()}\n\n'
            'Lokal und kryptografisch zufällig generierte Passwörter und Passphrasen.\n'
            'Der Verlauf bleibt nur während dieser Sitzung im Arbeitsspeicher.\n'
            'Generierte Passwörter werden nicht an einen Server übertragen.\n\n'
            'Updates und Crash-Log befinden sich im Reiter „Updates“.',
        )

    def on_tab_changed(self, index):
        if self.reporter is not None:
            self.reporter.note('NAVIGATE', f'tab={self.tabs.tabText(index)}', force=True)

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
        finally:
            self._restoring = False
        # Remove the legacy preference: glass now has one fixed finish.
        self.settings.remove('glass_opacity')
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
        for card in self.glass_cards:
            card.set_glass_color(bg)
        palette_key = (bg, fg)
        if self._applied_palette != palette_key:
            self._applied_palette = palette_key
            # Reapply widget styles only when the color palette changes.
            self.setStyleSheet(build_glass_stylesheet(bg, fg) + '\n' + neon_stylesheet(bg, fg))
            self.settings.setValue('background_color', bg)
            self.settings.setValue('text_color', fg)
            if self.reporter is not None:
                self.reporter.note('PALETTE_CHANGED', f'background={bg}, text={fg}', force=True)

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
            if self._phrase_mode:
                generated = make_passphrase(self.length.value())
                label, score = estimate_strength(
                    generated, phrase_words=self.length.value()
                )
                kind = 'Passphrase'
            else:
                generated = make_password(
                    self.length.value(), use_lower=self.lower.isChecked(),
                    use_upper=self.upper.isChecked(), use_digits=self.digits.isChecked(),
                    use_symbols=self.symbols.isChecked(),
                    exclude_similar=self.exclude.isChecked(),
                )
                alphabet_size = (
                    (26 if self.lower.isChecked() else 0)
                    + (26 if self.upper.isChecked() else 0)
                    + (10 if self.digits.isChecked() else 0)
                    + (23 if self.symbols.isChecked() else 0)
                    - (5 if self.exclude.isChecked() else 0)
                )
                label, score = estimate_strength(
                    generated, pool_size=max(2, alphabet_size)
                )
                kind = 'Passwort'
        except ValueError as error:
            QMessageBox.warning(self, 'Auswahl fehlt', str(error))
            return

        self.output.setText(generated)
        self.strength_label.setText(f'🛡  Stärke: {label}')
        self.strength_bar.setValue(score)
        self.status.setText(f'{kind} erstellt.')
        self._history.append((kind, generated))
        del self._history[:-20]
        if self.reporter is not None:
            self.reporter.note('GENERATED', f'mode={kind.lower()}', force=True)

    def copy(self):
        if self.output.text():
            QApplication.clipboard().setText(self.output.text())
            self.status.setText('In die Zwischenablage kopiert.')

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
