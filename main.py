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
    QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSlider, QSpinBox, QStackedWidget, QTextBrowser,
    QVBoxLayout, QWidget,
)

from diagnostics import CrashReporter, default_state_directory
from glass_ui import GlassBackground, GlossyGlassCard, build_glass_stylesheet, IMAGE_MODES
from neon_style import neon_stylesheet
from theme_colors import COLOR_SCHEMES, SCHEME_MAP, DEFAULT_SCHEME, accent_for_background, preset_colors
from release_history import normalized_releases, compact_changelog
from updater import install_staged_appimage, restart_updated_app, staging_path
from password_core import make_password, make_passphrase, estimate_strength, parse_version
from version import APP_VERSION, is_newer_release, version_status

REPO = 'TimBooH/Passwort-Generator'
REPO_URL = f'https://github.com/{REPO}'
LATEST_RELEASE_API = f'https://api.github.com/repos/{REPO}/releases/latest'
RELEASE_HISTORY_API = f'https://api.github.com/repos/{REPO}/releases?per_page=100'
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
        self.history_reply = None
        self._release_history_loaded = False
        self._history_releases = {}
        self._auto_check = auto_check
        self._phrase_mode = False
        self._history = []  # Session-only, never persisted to QSettings or disk.

        self.setWindowTitle(f'Passwort-Generator v{APP_VERSION}')
        self.resize(850, 865)
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
        content_layout.setContentsMargins(16, 15, 16, 14)
        self.glass_cards = []
        self.secondary_cards = []
        self._compact_options = None
        self._applied_palette = None
        self._restoring = False

        # Compact brand header; all navigation actions move into the left sidebar.
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
        content_layout.addLayout(header)
        content_layout.addSpacing(5)

        # Plain horizontal text buttons in a fixed left sidebar, not
        # rotated vertical QTabBar labels. The QStackedWidget keeps pages
        # alive so passwords, colors, and update state survive navigation.
        workspace = QHBoxLayout()
        workspace.setSpacing(14)
        self.nav_sidebar = QFrame(content)
        self.nav_sidebar.setObjectName('navSidebar')
        self.nav_sidebar.setFixedWidth(158)
        nav_layout = QVBoxLayout(self.nav_sidebar)
        nav_layout.setContentsMargins(9, 15, 9, 12)
        nav_layout.setSpacing(9)
        nav_title = QLabel('MENÜ')
        nav_title.setObjectName('navTitle')
        nav_layout.addWidget(nav_title)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = []
        self.tab_names = ('Passwort', 'Einstellungen', 'Updates')
        for index, (label, icon) in enumerate((
            ('Passwort', '⌑'), ('Einstellungen', '⚙'), ('Updates', '↻'),
        )):
            button = QPushButton(f'{icon}  {label}')
            button.setObjectName('navButton')
            button.setCheckable(True)
            button.setMinimumHeight(43)
            button.setToolTip(label)
            button.setAccessibleName(label)
            self.nav_group.addButton(button)
            nav_layout.addWidget(button)
            button.clicked.connect(lambda checked=False, i=index: self.tabs.setCurrentIndex(i))
            self.nav_buttons.append(button)
        self.nav_buttons[0].setChecked(True)
        nav_layout.addStretch(1)
        nav_footer = QLabel(f'v{APP_VERSION}')
        nav_footer.setObjectName('navFooter')
        nav_layout.addWidget(nav_footer)
        workspace.addWidget(self.nav_sidebar, 0)

        self.tabs = QStackedWidget(content)
        self.tabs.setObjectName('mainPages')
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        workspace.addWidget(self.tabs, 1)
        content_layout.addLayout(workspace, 1)

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
        self.check_layout = check_layout
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
        colors_layout.setSpacing(11)
        scheme_row = QHBoxLayout()
        scheme_row.addWidget(QLabel('Farbschema:'))
        self.scheme_combo = QComboBox()
        self.scheme_combo.setObjectName('colorSchemeCombo')
        for scheme_id, scheme_name, _background, _foreground in COLOR_SCHEMES:
            self.scheme_combo.addItem(scheme_name, scheme_id)
        scheme_row.addWidget(self.scheme_combo, 1)
        colors_layout.addLayout(scheme_row)
        scheme_hint = QLabel('Glass Dark, Glass Light, Neon Blue und weitere Vorlagen.')
        scheme_hint.setWordWrap(True)
        scheme_hint.setObjectName('supportText')
        colors_layout.addWidget(scheme_hint)
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
        accent_label = QLabel('Akzentfarbe – passt sich automatisch dem Hintergrund an:')
        accent_label.setWordWrap(True)
        colors_layout.addWidget(accent_label)
        self.accent_preview = QLabel('Automatisch')
        self.accent_preview.setObjectName('accentPreview')
        self.accent_preview.setMinimumHeight(25)
        colors_layout.addWidget(self.accent_preview)
        colors_note = QLabel('Farbschema und Akzentfarbe werden automatisch gespeichert.')
        colors_note.setWordWrap(True)
        colors_layout.addWidget(colors_note)
        settings_page_layout.addWidget(colors, 0)
        # Background image controls belong to their own glass tile.
        image_card = GlossyGlassCard('HINTERGRUNDBILD')
        self.secondary_cards.append(image_card)
        image_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        image_layout = image_card.body
        image_layout.setSpacing(11)
        # The chosen image stays on disk; only its path and display mode are stored.
        picture_title = QLabel('Eigenes Hintergrundbild')
        picture_title.setObjectName('supportText')
        image_layout.addWidget(picture_title)
        # Vertical actions avoid cramped/overlapping buttons in narrow windows.
        picture_actions = QVBoxLayout()
        picture_actions.setSpacing(7)
        self.choose_background_button = QPushButton('Bild auswählen …')
        self.choose_background_button.clicked.connect(self.choose_background_image)
        picture_actions.addWidget(self.choose_background_button)
        self.clear_background_button = QPushButton('Bild entfernen')
        self.clear_background_button.clicked.connect(self.remove_background_image)
        picture_actions.addWidget(self.clear_background_button)
        image_layout.addLayout(picture_actions)
        self.background_file_label = QLabel('Kein Hintergrundbild ausgewählt')
        self.background_file_label.setObjectName('supportText')
        self.background_file_label.setWordWrap(True)
        image_layout.addWidget(self.background_file_label)
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel('Bilddarstellung:'))
        self.image_mode_combo = QComboBox()
        for label, mode in IMAGE_MODES:
            self.image_mode_combo.addItem(label, mode)
        mode_row.addWidget(self.image_mode_combo, 1)
        image_layout.addLayout(mode_row)


        settings_page_layout.addWidget(image_card, 0)
        settings_page_layout.addStretch(1)

        self.updates_page = QWidget()
        self.updates_page.setObjectName('updatesPage')
        updates_page_layout = QVBoxLayout(self.updates_page)
        updates_page_layout.setSpacing(12)
        updates_page_layout.setContentsMargins(4, 10, 4, 8)

        updates = GlossyGlassCard('UPDATE & VERSION')
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
        updates_page_layout.addWidget(updates, 0)
        # Concise changes and newest-to-oldest chronological history are
        # grouped separately; selecting a version only changes the text.
        history_card = GlossyGlassCard('ÄNDERUNGEN & VERSIONEN')
        self.secondary_cards.append(history_card)
        history_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        history_layout = history_card.body
        history_layout.setSpacing(10)
        self.changelog_title = QLabel('Änderungen der veröffentlichten Version')
        self.changelog_title.setObjectName('supportText')
        self.changelog_title.setWordWrap(True)
        history_layout.addWidget(self.changelog_title)
        self.changelog_view = QTextBrowser()
        self.changelog_view.setObjectName('changelogView')
        self.changelog_view.setOpenExternalLinks(False)
        self.changelog_view.setOpenLinks(False)
        self.changelog_view.setMinimumHeight(100)
        self.changelog_view.setMaximumHeight(155)
        self.changelog_view.setPlainText(
            'Die Änderungen werden beim Öffnen dieser Seite automatisch geladen.'
        )
        history_layout.addWidget(self.changelog_view)

        history_header = QLabel('BISHERIGE VERSIONEN')
        history_header.setObjectName('glassCardTitle')
        history_layout.addWidget(history_header)
        self.release_list = QListWidget()
        self.release_list.setObjectName('releaseList')
        self.release_list.setMinimumHeight(145)
        self.release_list.setMaximumHeight(290)
        self.release_list.currentItemChanged.connect(self.select_release_history)
        history_layout.addWidget(self.release_list)
        self.release_history_status = QLabel('Versionshistorie noch nicht geladen.')
        self.release_history_status.setObjectName('supportText')
        self.release_history_status.setWordWrap(True)
        history_layout.addWidget(self.release_history_status)



        updates_page_layout.addWidget(history_card, 1)
        updates_page_layout.addStretch(0)


        self.tabs.addWidget(self.password_page)
        self.tabs.addWidget(self.settings_page)
        self.tabs.addWidget(self.updates_page)
        self.tabs.setCurrentIndex(0)

        self.status = QLabel('')
        self.status.setObjectName('globalStatus')
        self.status.setWordWrap(True)
        content_layout.addWidget(self.status)

        self.scheme_combo.currentIndexChanged.connect(self.apply_color_scheme)
        self.bg_combo.currentIndexChanged.connect(self.on_manual_color_change)
        self.fg_combo.currentIndexChanged.connect(self.on_manual_color_change)
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

    def build_info_dialog(self):
        """Build a readable manual, with visible author credit at the very top."""
        dialog = QDialog(self)
        dialog.setWindowTitle('Info & Anleitung')
        dialog.resize(610, 630)
        layout = QVBoxLayout(dialog)
        credit = QLabel('Made by Jon Bovi')
        credit.setObjectName('infoCredit')
        credit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credit.setStyleSheet(
            f'color: {accent_for_background(self.bg_combo.currentData() or "#071322")}; '
            'font-size: 22px; font-weight: 850; padding: 10px;'
        )
        layout.addWidget(credit)
        subheading = QLabel(f'Passwort-Generator v{APP_VERSION}  ·  {version_status()}')
        subheading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subheading.setObjectName('supportText')
        layout.addWidget(subheading)

        guide = QTextBrowser(dialog)
        guide.setObjectName('changelogView')
        guide.setReadOnly(True)
        guide.setOpenExternalLinks(False)
        guide.setMarkdown(
            '# Anleitung\n\n'
            '### 1. Sicheres Passwort erstellen\n'
            'Öffne **Passwort**, wähle die gewünschte Länge mit dem Regler oder dem '
            'Zahlenfeld (8–128 Zeichen) und aktiviere die gewünschten Zeichengruppen. '
            'Klicke auf **Passwort generieren**.\n\n'
            '### 2. Passphrase erstellen\n'
            'Wechsle oben auf **Passphrase**. Wähle 4–10 Wörter und klicke auf '
            '**Passphrase generieren**. Die Wörter werden lokal zufällig gewählt '
            'und mit Bindestrichen verbunden.\n\n'
            '### 3. Passwort verwenden\n'
            '**Kopieren** übernimmt das Ergebnis in die Zwischenablage. '
            '**Anzeigen / Verbergen** steuert, ob es im Eingabefeld lesbar ist. '
            'Das Symbol **↻** erstellt ein neues Ergebnis.\n\n'
            '### 4. Stärke und Verlauf\n'
            'Die Stärkeanzeige ist eine grobe mathematische Schätzung, keine '
            'Sicherheitsgarantie. Unter **Verlauf** findest du maximal 20 Ergebnisse '
            'dieser Sitzung. Beim Beenden wird dieser Verlauf verworfen.\n\n'
            '### 5. Farben und Hintergrund\n'
            'Öffne **Einstellungen**. Wähle ein Farbschema wie **Glass Dark**, '
            '**Glass Light** oder **Neon Blue**. Die Akzentfarbe passt sich '
            'automatisch an die Hintergrundfarbe an. Du kannst auch eigene Farben '
            'und Hintergrundbilder verwenden.\n\n'
            '### 6. Updates und ältere Versionen\n'
            'Unter **Updates** siehst du den Changelog und frühere Releases. '
            'Über **Auf Updates prüfen** und anschließend '
            '**Update installieren & neu starten** installierst du eine neue '
            'Version. Dort kannst du auch das lokale Crash-Log öffnen.\n\n'
            '### Datenschutz\n'
            'Passwörter werden auf deinem Gerät erzeugt und nicht hochgeladen. '
            'Beachte, dass andere Anwendungen gegebenenfalls auf den Inhalt '
            'der Systemzwischenablage zugreifen können.'
        )
        layout.addWidget(guide, 1)
        close = QPushButton('Schließen')
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        return dialog

    def show_info(self):
        self.build_info_dialog().exec()

    def on_tab_changed(self, index):
        for position, button in enumerate(self.nav_buttons):
            button.setChecked(position == index)
        if (index == 2 and self._auto_check and not self._release_history_loaded
                and self.history_reply is None):
            self.load_release_history()
        if self.reporter is not None:
            self.reporter.note('NAVIGATE', f'tab={self.tab_names[index]}', force=True)

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
            stored_background = self.settings.value('background_color', '#071322', type=str)
            stored_text = self.settings.value('text_color', '#FFFFFF', type=str)
            saved_scheme = self.settings.value('color_scheme', '', type=str)
            if saved_scheme not in SCHEME_MAP:
                default_pair = preset_colors(DEFAULT_SCHEME)
                saved_scheme = (DEFAULT_SCHEME if
                                (stored_background.upper(), stored_text.upper()) ==
                                (default_pair[0].upper(), default_pair[1].upper())
                                else 'custom')
            scheme_index = self.scheme_combo.findData(saved_scheme)
            self.scheme_combo.setCurrentIndex(max(0, scheme_index))
            preset = preset_colors(saved_scheme)
            background, foreground = preset or (stored_background, stored_text)
            self.select_color(self.bg_combo, background, '#071322')
            self.select_color(self.fg_combo, foreground, '#FFFFFF')
        finally:
            self._restoring = False
        self.settings.remove('glass_opacity')
        self.settings.setValue('color_scheme', self.scheme_combo.currentData())
        self.apply_colors()

    def apply_color_scheme(self, *_):
        if self._restoring:
            return
        scheme = self.scheme_combo.currentData() or DEFAULT_SCHEME
        preset = preset_colors(scheme)
        if preset:
            self._restoring = True
            try:
                self.select_color(self.bg_combo, preset[0], '#071322')
                self.select_color(self.fg_combo, preset[1], '#FFFFFF')
            finally:
                self._restoring = False
        self.settings.setValue('color_scheme', scheme)
        self.apply_colors()

    def on_manual_color_change(self, *_):
        if self._restoring:
            return
        custom_index = self.scheme_combo.findData('custom')
        if custom_index >= 0 and self.scheme_combo.currentIndex() != custom_index:
            self._restoring = True
            try:
                self.scheme_combo.setCurrentIndex(custom_index)
            finally:
                self._restoring = False
        self.settings.setValue('color_scheme', 'custom')
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
        if hasattr(self, 'nav_sidebar'):
            # Keep navigation readable but allow more content width in narrow windows.
            width = 126 if self.width() < 700 else 158
            if self.nav_sidebar.width() != width:
                self.nav_sidebar.setFixedWidth(width)
            # Short labels fit in narrow windows; full names remain in tooltips.
            labels = (('⌑  Passwort', '⚙  Farben', '↻  Updates')
                      if width == 126 else
                      ('⌑  Passwort', '⚙  Einstellungen', '↻  Updates'))
            for button, label in zip(self.nav_buttons, labels):
                if button.text() != label:
                    button.setText(label)
        if hasattr(self, 'check_layout') and hasattr(self, 'upper'):
            compact = self.width() < 730
            if compact != self._compact_options:
                self._compact_options = compact
                boxes = (self.upper, self.lower, self.digits, self.symbols, self.exclude)
                for checkbox in boxes:
                    self.check_layout.removeWidget(checkbox)
                for index, checkbox in enumerate(boxes):
                    row, column = (index, 0) if compact else (
                        (index, 0) if index < 3 else (index - 3, 1)
                    )
                    self.check_layout.addWidget(checkbox, row, column)
        if self.reporter is not None:
            self.reporter.note('RESIZE', f'{self.width()}x{self.height()}')

    def apply_colors(self, *_):
        if self._restoring:
            return
        bg = self.bg_combo.currentData() or '#071322'
        fg = self.fg_combo.currentData() or '#FFFFFF'
        accent = accent_for_background(bg)
        self.background_surface.set_base_color(bg)
        for card in self.glass_cards + self.secondary_cards:
            card.set_glass_color(bg, accent)
        self.accent_preview.setText(f'●  Automatisch: {accent}')
        self.accent_preview.setToolTip('Wird aus der gewählten Hintergrundfarbe berechnet.')
        palette_key = (bg, fg, accent)
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
        # The existing update-check action also refreshes the list.
        # No extra "Versionshistorie laden" button is necessary.
        if self.tabs.currentIndex() == 2 and self.history_reply is None:
            self.load_release_history()
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
            if not self._release_history_loaded and self.release_list.count() == 0:
                note = response.get('body', '')
                if isinstance(note, str) and note.strip():
                    self.changelog_title.setText(f'Kurzüberblick · {latest_version}')
                    self.changelog_view.setPlainText(compact_changelog(note))
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

    def load_release_history(self):
        """Fetch at most 100 public releases asynchronously from GitHub."""
        if self.history_reply is not None:
            return
        self.release_history_status.setText('Lade Versionen von GitHub …')
        self.history_reply = self.network.get(self.make_request(RELEASE_HISTORY_API))
        self.history_reply.finished.connect(self.release_history_finished)

    def release_history_finished(self):
        reply = self.history_reply
        self.history_reply = None
        if reply is None:
            return
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                raise ValueError(reply.errorString())
            raw = bytes(reply.readAll())
            if len(raw) > 2_000_000:
                raise ValueError('Die Antwort von GitHub ist zu groß.')
            payload = json.loads(raw.decode('utf-8'))
            releases = normalized_releases(payload, REPO_URL)
            self._history_releases = {item['tag']: item for item in releases}
            self.release_list.clear()
            for item in releases:
                date = item['date']
                suffix = f' · {date}' if date else ''
                label = QListWidgetItem(item['tag'] + suffix)
                label.setData(Qt.ItemDataRole.UserRole, item['tag'])
                self.release_list.addItem(label)
            self._release_history_loaded = True
            self.release_history_status.setText(
                f'{len(releases)} Version(en) · neueste oben, älteste unten'
            )
            if releases:
                self.release_list.setCurrentRow(0)
            else:
                self.changelog_view.setPlainText('Keine veröffentlichten Versionen gefunden.')
        except (ValueError, TypeError, UnicodeDecodeError, KeyError) as error:
            self.release_history_status.setText(
                f'Versionshistorie nicht verfügbar: {error}'
            )
            if not self._release_history_loaded:
                self.changelog_view.setPlainText(
                    'Die Versionshistorie konnte nicht geladen werden. '
                    'Bitte die Internetverbindung prüfen und erneut versuchen.'
                )
        finally:
            reply.deleteLater()

    def select_release_history(self, current, _previous=None):
        if current is None:
            return
        tag = current.data(Qt.ItemDataRole.UserRole)
        entry = self._history_releases.get(tag)
        if entry is None:
            return
        self.changelog_title.setText(f'Kurzüberblick · {entry["tag"]}')
        self.changelog_view.setPlainText(compact_changelog(entry['body']))

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
