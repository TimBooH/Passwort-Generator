"""PasswortGenerator: lokale Passworterzeugung mit Update-Download von GitHub."""

import hashlib
import math
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QByteArray, QEvent, QIODevice, QSettings, QStandardPaths, Qt, QTimer, QUrl, QSaveFile
from PySide6.QtGui import QColor, QFont, QIcon, QKeySequence, QShortcut, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QColorDialog, QComboBox, QDialog,
    QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSlider, QSpinBox, QStackedWidget, QTabWidget,
    QTextBrowser, QVBoxLayout, QWidget,
)

from localization import LANGUAGES, translate
from password_presets import PRESETS, FIELDS, decode_profile, encode_profile, validate_profile
from diagnostics import CrashReporter
from glass_ui import GlassBackground, GlossyGlassCard, build_glass_stylesheet, IMAGE_MODES
from neon_style import neon_stylesheet
from theme_colors import (COLOR_SCHEMES, SCHEME_MAP, DEFAULT_SCHEME, accent_for_background,
                          accessible_text_color, preset_colors)
from release_history import normalized_releases
from release_notes_i18n import release_changelog
from updater import (install_staged_appimage, restart_updated_app,
                     restore_previous_appimage, previous_path, staging_path)
from windows_support import WINDOWS_INSTALLER_NAME, start_verified_windows_installer
from password_core import (PHRASE_SEPARATORS, SYMBOLS, make_password,
                            make_passphrase, estimate_strength,
                            password_entropy_bits, parse_version)
from version import APP_VERSION, is_newer_release, version_status
from release_channel import CHANNEL, BUILD_SHA
from ocean_art import key_icon
from update_channels import (channel_api, select_unstable_asset,
                             has_channel_update, unstable_asset_name)

REPO = 'TimBooH/Passwort-Generator'
REPO_URL = f'https://github.com/{REPO}'
LATEST_RELEASE_API = f'https://api.github.com/repos/{REPO}/releases/latest'
RELEASE_HISTORY_API = f'https://api.github.com/repos/{REPO}/releases?per_page=100'
RELEASE_DOWNLOAD_PREFIX = f'https://github.com/{REPO}/releases/download/'
RELEASES_URL = f'{REPO_URL}/releases'
UPDATE_CHECK_INTERVAL_MS = 2 * 60 * 60 * 1000  # Every two hours while open.
APPIMAGE_NAME = 'PasswortGenerator-x86_64.AppImage'
INSTALLED_APPIMAGE = Path.home() / '.local/opt/passwort-generator/PasswortGenerator.AppImage'
UNSTABLE_APPIMAGE = Path.home() / '.local/opt/passwort-generator-unstable/PasswortGenerator.AppImage'

BACKGROUND_COLORS = [
    ('Nachtblau', '#101827'), ('Anthrazit', '#20242C'), ('Schwarz', '#111111'),
    ('Dunkelgrün', '#123329'), ('Dunkelrot', '#351A23'), ('Violett', '#2A1D45'),
    ('Hellgrau', '#F1F4F8'), ('Weiß', '#FFFFFF'), ('Sand', '#F5EDDB'),
    ('Eisblau', '#E5F3FA'),
]
def contrast_color(hex_color):
    color = QColor(hex_color)
    luminance = 0.2126 * color.redF() + 0.7152 * color.greenF() + 0.0722 * color.blueF()
    return '#151A21' if luminance > 0.58 else '#FFFFFF'


def field_color(hex_color):
    color = QColor(hex_color)
    return color.lighter(135).name() if contrast_color(hex_color) == '#FFFFFF' else color.darker(105).name()


class CurrentPageStack(QStackedWidget):
    """Advertise only the active page's height to the parent scroll area.

    Qt's default QStackedWidget calculates a maximum across all pages. The
    tall Update/history page otherwise forces an unnecessary scrollbar even
    while the much shorter password page is visible.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.currentChanged.connect(lambda _index: self.updateGeometry())

    def sizeHint(self):
        page = self.currentWidget()
        return page.sizeHint() if page is not None else super().sizeHint()

    def minimumSizeHint(self):
        page = self.currentWidget()
        return page.minimumSizeHint() if page is not None else super().minimumSizeHint()


class PasswordWindow(QMainWindow):
    def __init__(self, auto_check=True, reporter=None):
        super().__init__()
        self.reporter = reporter
        # Preview builds must never overwrite stable settings.
        app_settings_name = ('PasswortGenerator-Unstable' if CHANNEL == 'unstable'
                             else 'PasswortGenerator')
        self.settings = QSettings('TimBooH', app_settings_name)
        self.language = self.settings.value('ui/language', 'de', type=str)
        if self.language not in ('de', 'en'):
            self.language = 'de'
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
        self._available_update = None
        self.history_reply = None
        self._release_history_loaded = False
        self._history_releases = {}
        self._latest_release_note = None  # (tag, raw GitHub Markdown)
        self._new_update_note = ''
        self.update_channel = self.settings.value('updates/channel', CHANNEL, type=str)
        if self.update_channel not in ('stable', 'unstable'):
            self.update_channel = CHANNEL
        self._checked_channel = self.update_channel
        self._auto_check = bool(auto_check)
        self._startup_update_check_pending = self._auto_check
        self._pending_update_popup = None
        self._update_popup_dialog = None
        self._first_run_tour = None
        self._phrase_mode = False
        self._last_entropy_bits = 0.0
        self._advanced_rules = {
            'min_digits': self.settings.value('password/min_digits', 0, type=int),
            'min_symbols': self.settings.value('password/min_symbols', 0, type=int),
            'excluded_chars': self.settings.value('password/excluded_chars', '', type=str),
        }
        self._rollback_reply = None
        self._rollback_pending = False
        self._applying_preset = False
        self._clipboard_secret = None
        self._history = []  # Session-only, never persisted to QSettings or disk.

        channel_badge = ' [UNSTABLE]' if CHANNEL == 'unstable' else ''
        self.setWindowTitle(f'Passwort-Generator v{APP_VERSION}{channel_badge}')
        # Widescreen proportions as in the reference; saved geometry still wins.
        self.resize(1120, 750)
        if os.name == 'nt':
            icon_base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
            icon_path = icon_base / 'assets' / 'passwortgenerator.ico'
            if icon_path.is_file():
                self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(510, 680)

        # A native central widget – no scroll area and no hidden scrollbars.
        # Long release histories are navigated in short pages below.
        root = GlassBackground()
        root.setObjectName('appRoot')
        self.background_surface = root
        self.setCentralWidget(root)
        outer_layout = QHBoxLayout(root)
        outer_layout.setContentsMargins(7, 0, 7, 0)
        outer_layout.setSpacing(0)

        content = QWidget(root)
        content.setObjectName('contentColumn')
        content.setMinimumWidth(0)
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        outer_layout.addWidget(content, 1)
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(18, 12, 18, 9)
        self.glass_cards = []
        self.secondary_cards = []
        self._compact_options = None
        self._applied_palette = None
        self._restoring = False
        self._ocean_presentation_state = None

        # Header: compact branding, with four navigation actions at top right.
        header = QHBoxLayout()
        header.setSpacing(12)
        lock = QLabel('🔑')
        self.brand_icon = lock
        lock.setObjectName('brandLock')
        lock.setFixedSize(53, 53)
        lock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(lock)
        heading = QVBoxLayout()
        heading.setSpacing(3)
        brand = QLabel('Passwort-Generator')
        self.brand_title = brand
        brand.setObjectName('brandTitle')
        brand.setWordWrap(True)
        heading.addWidget(brand)
        subtitle = QLabel('Stark. Sicher. Einzigartig.')
        self.brand_subtitle = subtitle
        subtitle.setObjectName('brandSubtitle')
        heading.addWidget(subtitle)
        header.addLayout(heading, 1)
        content_layout.addLayout(header)

        # A separate right-aligned row remains readable at narrow widths.
        self.nav_container = QFrame(content)
        self.nav_container.setObjectName('topNav')
        nav_layout = QHBoxLayout(self.nav_container)
        nav_layout.setContentsMargins(8, 6, 8, 6)
        nav_layout.setSpacing(8)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = []
        self.tab_names = ('Passwort', 'Einstellungen', 'Update', 'Info')
        for index, (label, symbol) in enumerate((
            ('Passwort', '⌑'), ('Einstellungen', '⚙'), ('Update', '↻'),
        )):
            button = QPushButton(f'{symbol}  {label}')
            button.setObjectName('navButton')
            button.setCheckable(True)
            button.setMinimumHeight(44)
            button.setToolTip(label)
            button.setAccessibleName(label)
            self.nav_group.addButton(button)
            nav_layout.addWidget(button, 1)
            button.clicked.connect(
                lambda checked=False, i=index: self.tabs.setCurrentIndex(i)
            )
            self.nav_buttons.append(button)
        # Visual order: Passwort → Update → Einstellungen → Info.
        # Keep original QStackedWidget indices so internal update links work.
        nav_layout.removeWidget(self.nav_buttons[1])
        nav_layout.addWidget(self.nav_buttons[1], 1)
        self.nav_buttons[0].setChecked(True)
        self.info_nav_button = QPushButton('ⓘ  Info')
        self.info_nav_button.setObjectName('infoNavButton')
        self.info_nav_button.setToolTip('Über PasswortGenerator')
        self.info_nav_button.setAccessibleName('Info')
        self.info_nav_button.setMinimumHeight(44)
        self.info_nav_button.setCheckable(True)
        self.nav_group.addButton(self.info_nav_button)
        self.info_nav_button.clicked.connect(self.show_info)
        nav_layout.addWidget(self.info_nav_button, 1)
        content_layout.addWidget(self.nav_container)

        self.tabs = CurrentPageStack(content)
        self.tabs.setObjectName('mainPages')
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout.addWidget(self.tabs, 1)

        self.password_page = QWidget()
        self.password_page.setObjectName('passwordPage')
        layout = QVBoxLayout(self.password_page)
        layout.setSpacing(4)
        layout.setContentsMargins(2, 4, 2, 3)

        group = GlossyGlassCard('PASSWORT ERSTELLEN')
        group.header.hide()  # The reference uses its own prominent mode toggle.
        group.highlight.hide()
        self.glass_cards.append(group)
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        group_layout = group.body
        self.password_group_layout = group_layout
        group_layout.setSpacing(9)
        group.layout().setContentsMargins(19, 14, 19, 14)
        group.layout().setSpacing(3)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)
        self.ocean_hero_icon = QLabel('🔑')
        self.ocean_hero_icon.setObjectName('oceanHeroIcon')
        self.ocean_hero_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ocean_hero_icon.setFixedSize(52, 52)
        mode_row.addWidget(self.ocean_hero_icon)
        self.ocean_hero_icon.hide()
        # The real screenshot-inspired header shares a row with the mode
        # selector; hiding it in compact windows keeps all controls visible.
        self.ocean_heading = QWidget()
        ocean_heading_layout = QVBoxLayout(self.ocean_heading)
        ocean_heading_layout.setContentsMargins(0, 0, 0, 0)
        ocean_heading_layout.setSpacing(1)
        self.ocean_page_title = QLabel('PASSWORT ERSTELLEN')
        self.ocean_page_title.setMinimumHeight(28)
        self.ocean_page_title.setObjectName('oceanPageTitle')
        self.ocean_page_subtitle = QLabel('Erstelle sichere und zufällige Passwörter oder Passphrasen.')
        self.ocean_page_subtitle.setObjectName('oceanPageSubtitle')
        ocean_heading_layout.addWidget(self.ocean_page_title)
        ocean_heading_layout.addWidget(self.ocean_page_subtitle)
        mode_row.addWidget(self.ocean_heading, 1)
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.password_mode_button = QPushButton('Passwort')
        self.passphrase_mode_button = QPushButton('Passphrase')
        for button in (self.password_mode_button, self.passphrase_mode_button):
            button.setObjectName('modeButton')
            button.setCheckable(True)
            button.setMinimumHeight(38)
            self.mode_group.addButton(button)
            mode_row.addWidget(button, 0)
        self.password_mode_button.setChecked(True)
        self.password_mode_button.clicked.connect(lambda: self.switch_mode(False))
        self.passphrase_mode_button.clicked.connect(lambda: self.switch_mode(True))
        group_layout.addLayout(mode_row)
        self.ocean_heading.setVisible(False)

        self.ocean_output_caption = QLabel('Generiertes Passwort')
        self.ocean_output_caption.setObjectName('oceanOutputCaption')
        group_layout.addWidget(self.ocean_output_caption)
        self.ocean_output_caption.hide()

        password_row = QHBoxLayout()
        password_row.setSpacing(7)
        self.output = QLineEdit()
        self.output.setObjectName('passwordOutput')
        self.output.setReadOnly(True)
        self.output.setEchoMode(QLineEdit.EchoMode.Password)
        self._set_placeholder(self.output, 'Generiertes Passwort')
        self.output.setMinimumHeight(43)
        self.output.setFont(QFont('Monospace', 12))
        password_row.addWidget(self.output, 1)
        copy_top = QPushButton('⧉')
        self.copy_top_button = copy_top
        copy_top.setObjectName('squareAction')
        copy_top.setToolTip('Passwort kopieren')
        copy_top.setMinimumSize(41, 43)
        copy_top.clicked.connect(self.copy)
        password_row.addWidget(copy_top)
        regenerate = QPushButton('↻')
        self.regenerate_button = regenerate
        regenerate.setObjectName('squareAction')
        regenerate.setToolTip('Neues Passwort erzeugen')
        regenerate.setMinimumSize(41, 43)
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
        self.analysis_button = QPushButton('ⓘ Analyse')
        self.analysis_button.setObjectName('analysisButton')
        self.analysis_button.setToolTip('Geschätzte Entropie und Sicherheitsbewertung anzeigen')
        self.analysis_button.clicked.connect(self.show_security_analysis)
        strength_row.addWidget(self.analysis_button)
        self.ocean_strength_caption = QLabel('Passwort-Stärke')
        self.ocean_strength_caption.setObjectName('oceanStrengthCaption')
        self.ocean_strength_value = QLabel('--')
        self.ocean_strength_value.setObjectName('oceanStrengthValue')
        strength_row.insertWidget(0, self.ocean_strength_caption)
        strength_row.insertWidget(3, self.ocean_strength_value)
        strength_row.insertWidget(2, self.strength_bar, 1)
        for i in range(strength_row.count() - 1, -1, -1):
            if strength_row.itemAt(i).spacerItem() is not None:
                strength_row.takeAt(i)
        self.ocean_strength_caption.hide()
        self.ocean_strength_value.hide()
        group_layout.addSpacing(2)

        # Build the real options and length panels in their final parents.
        # Never remove/reparent already-owned QLayouts: native Qt needs
        # stable ownership for repeated resizes and safe interpreter cleanup.
        self.ocean_sections = QWidget(group)
        self.ocean_sections.setObjectName('oceanSections')
        sections_row = QHBoxLayout(self.ocean_sections)
        sections_row.setContentsMargins(0, 0, 0, 0)
        sections_row.setSpacing(12)
        self.ocean_options_panel = QFrame(self.ocean_sections)
        self.ocean_options_panel.setObjectName('oceanOptionPanel')
        self.ocean_options_panel.setMinimumWidth(250)
        options_col = QVBoxLayout(self.ocean_options_panel)
        self.ocean_options_layout = options_col
        options_col.setContentsMargins(18, 15, 18, 14)
        options_col.setSpacing(10)
        self.ocean_options_heading = QLabel('Optionen')
        self.ocean_options_heading.setObjectName('oceanPanelHeading')
        options_col.addWidget(self.ocean_options_heading)
        self.ocean_preset_box = QWidget(self.ocean_options_panel)
        preset_box_layout = QVBoxLayout(self.ocean_preset_box)
        preset_box_layout.setContentsMargins(0, 0, 0, 0)

        self.ocean_length_panel = QFrame(self.ocean_sections)
        self.ocean_length_panel.setObjectName('oceanLengthPanel')
        self.ocean_length_panel.setMinimumWidth(150)
        length_col = QVBoxLayout(self.ocean_length_panel)
        length_col.setContentsMargins(18, 15, 18, 14)
        length_col.setSpacing(11)
        self.ocean_length_heading = QLabel('Passwort-Länge')
        self.ocean_length_heading.setObjectName('oceanPanelHeading')
        length_col.addWidget(self.ocean_length_heading)

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
        self.length.setFixedWidth(78)
        self.length.setAccessibleName('Länge des Passworts')
        length_row.addWidget(self.length)
        length_col.addLayout(length_row)
        self.length_slider = QSlider(Qt.Orientation.Horizontal)
        self.length_slider.setObjectName('oceanLengthSlider')
        self.length_slider.setRange(8, 128)
        self.length_slider.setValue(20)
        self.length_slider.setAccessibleName('Länge einstellen')
        self.length.valueChanged.connect(self.length_slider.setValue)
        self.length_slider.valueChanged.connect(self.length.setValue)
        self.length.valueChanged.connect(lambda value: self.length_value.setText(str(value)))
        length_row.addWidget(self.length_slider, 1)
        self.ocean_length_range = QWidget(self.ocean_length_panel)
        range_layout = QHBoxLayout(self.ocean_length_range)
        range_layout.setContentsMargins(2, 0, 2, 0)
        self.ocean_min_label = QLabel('8')
        self.ocean_max_label = QLabel('128')
        range_layout.addWidget(self.ocean_min_label)
        range_layout.addStretch()
        range_layout.addWidget(self.ocean_max_label)
        length_col.addWidget(self.ocean_length_range)
        length_col.addStretch(1)

        # Compact password profiles: settings only, never generated secrets.
        preset_row = QHBoxLayout()
        preset_row.setSpacing(5)
        preset_title = QLabel('Profil:')
        preset_row.addWidget(preset_title)
        self.preset_combo = QComboBox()
        self.preset_combo.setObjectName('passwordPresetCombo')
        for label, key in (('Standard', 'standard'),
                           ('Sehr sicher', 'strong'),
                           ('Einfach', 'simple'),
                           ('Eigenes Profil', 'custom'),
                           ('Manuell', 'manual')):
            self.preset_combo.addItem(label, key)
        self.preset_combo.setCurrentIndex(0)
        preset_row.addWidget(self.preset_combo, 1)
        self.save_preset_button = QPushButton('Profil speichern')
        self.save_preset_button.setObjectName('savePresetButton')
        self.save_preset_button.setToolTip(
            'Aktuelle Passwort-Einstellungen als eigenes Profil speichern'
        )
        self.save_preset_button.clicked.connect(self.save_password_preset)
        preset_row.addWidget(self.save_preset_button)
        preset_box_layout.addLayout(preset_row)

        self.options_widget = QWidget()
        self.options_widget.setObjectName('passwordOptions')
        check_layout = QGridLayout(self.options_widget)
        self.check_layout = check_layout
        check_layout.setContentsMargins(0, 0, 0, 0)
        check_layout.setHorizontalSpacing(9)
        check_layout.setVerticalSpacing(1)
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
        check_layout.addWidget(self.symbols, 3, 0)
        check_layout.addWidget(self.exclude, 0, 1)
        options_col.addWidget(self.options_widget)
        self.rules_button = QPushButton('⚙ Erweiterte Regeln')
        self.rules_button.setObjectName('advancedPasswordRulesButton')
        self.rules_button.clicked.connect(self.show_advanced_rules)
        check_layout.addWidget(self.rules_button, 1, 1)

        # These controls only appear in Passphrase mode. The checkbox adds
        # one cryptographically random 10–99 number, separated as selected.
        self.phrase_options_widget = QWidget()
        self.phrase_options_widget.setObjectName('passphraseOptions')
        phrase_layout = QGridLayout(self.phrase_options_widget)
        phrase_layout.setContentsMargins(0, 0, 0, 0)
        phrase_layout.setHorizontalSpacing(9)
        phrase_layout.setVerticalSpacing(2)
        self.phrase_two_digits = QCheckBox('Zweistellige Zufallszahl anhängen')
        self.phrase_two_digits.setObjectName('phraseTwoDigitNumber')
        self.phrase_two_digits.setToolTip('Fügt am Ende eine zufällige Zahl von 10 bis 99 hinzu.')
        phrase_layout.addWidget(self.phrase_two_digits, 0, 0, 1, 2)
        phrase_layout.addWidget(QLabel('Trennzeichen:'), 1, 0)
        self.phrase_separator = QComboBox()
        self.phrase_separator.setObjectName('phraseSeparator')
        self.phrase_separator.setAccessibleName('Trennzeichen der Passphrase')
        for label, separator in PHRASE_SEPARATORS:
            self.phrase_separator.addItem(label, separator)
        self.phrase_separator.setMinimumWidth(125)
        phrase_layout.addWidget(self.phrase_separator, 1, 1)
        phrase_layout.addWidget(QLabel('Wortliste:'), 2, 0)
        self.phrase_language = QComboBox()
        self.phrase_language.setObjectName('phraseLanguageCombo')
        self.phrase_language.addItem('Deutsch', 'de')
        self.phrase_language.addItem('English', 'en')
        stored_phrase_language = self.settings.value('passphrase/language', 'de', type=str)
        self.phrase_language.setCurrentIndex(max(0, self.phrase_language.findData(stored_phrase_language)))
        self.phrase_language.currentIndexChanged.connect(
            lambda *_: self.settings.setValue('passphrase/language',
                                             self.phrase_language.currentData())
        )
        phrase_layout.addWidget(self.phrase_language, 2, 1)
        phrase_layout.setColumnStretch(1, 1)
        self.phrase_options_widget.hide()
        options_col.addWidget(self.phrase_options_widget)
        options_col.addStretch(1)
        options_col.addWidget(self.ocean_preset_box)
        sections_row.addWidget(self.ocean_options_panel, 18)
        sections_row.addWidget(self.ocean_length_panel, 11)
        group_layout.addWidget(self.ocean_sections, 1)

        self.generate_button = QPushButton('🔑  Passwort generieren')
        # Compact, glossy call-to-action; do not stretch to the card width.
        # The update installer keeps the existing #primaryButton design.
        self.generate_button.setObjectName('generatePasswordButton')
        self.generate_button.setFixedHeight(40)
        self.generate_button.setMaximumWidth(360)
        self.generate_button.setMinimumWidth(235)
        self.generate_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_button.clicked.connect(self.generate)

        footer = QHBoxLayout()
        footer.setSpacing(5)
        self.show_button = QPushButton('◉  Anzeigen')
        self.show_button.setObjectName('bottomAction')
        self.show_button.setCheckable(True)
        self.show_button.toggled.connect(self.toggle_visibility)
        footer.addWidget(self.show_button, 1)
        self.history_button = QPushButton('☷  Verlauf')
        self.history_button.setObjectName('bottomAction')
        self.history_button.clicked.connect(self.show_history)
        footer.addWidget(self.history_button, 1)
        # Keep privacy and session-history actions above the final CTA.
        footer.insertStretch(0, 1)
        self.show_button.setMaximumWidth(130)
        self.history_button.setMaximumWidth(130)
        group_layout.addLayout(footer)
        group_layout.addWidget(
            self.generate_button, 0, Qt.AlignmentFlag.AlignHCenter
        )
        layout.addWidget(group, 1)
        self.preset_combo.currentIndexChanged.connect(self.apply_password_preset)
        self.length.valueChanged.connect(self.mark_password_preset_manual)
        for checkbox in (self.upper, self.lower, self.digits, self.symbols, self.exclude):
            checkbox.toggled.connect(self.mark_password_preset_manual)

        self.settings_page = QWidget()
        self.settings_page.setObjectName('settingsPage')
        settings_page_layout = QVBoxLayout(self.settings_page)
        settings_page_layout.setSpacing(5)
        settings_page_layout.setContentsMargins(3, 4, 3, 3)

        colors = GlossyGlassCard('ERSCHEINUNGSBILD')
        self.appearance_card = colors
        self.glass_cards.append(colors)
        colors.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Tight, top-aligned controls instead of vertically stretched gaps.
        colors.layout().setContentsMargins(13, 6, 13, 7)
        colors.layout().setSpacing(2)
        colors_layout = colors.body
        colors_layout.setSpacing(3)
        scheme_row = QHBoxLayout()
        scheme_row.addWidget(QLabel('Farbschema:'))
        self.scheme_combo = QComboBox()
        self.scheme_combo.setObjectName('colorSchemeCombo')
        for scheme_id, scheme_name, _background, _foreground in COLOR_SCHEMES:
            self.scheme_combo.addItem(scheme_name, scheme_id)
        scheme_row.addWidget(self.scheme_combo, 1)
        colors_layout.addLayout(scheme_row)
        self.scheme_combo.setToolTip(
            'Glass (Hintergrund sichtbar), Glass Dark, Glass Light und weitere Vorlagen.'
        )
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
        accent_label = QLabel('Akzentfarbe – passt sich automatisch dem Hintergrund an:')
        accent_label.setWordWrap(True)
        colors_layout.addWidget(accent_label)
        self.accent_preview = QLabel('Automatisch')
        self.accent_preview.setObjectName('accentPreview')
        self.accent_preview.setMinimumHeight(25)
        colors_layout.addWidget(self.accent_preview)
        # Text and accent colors already explain themselves in the preview.
        # Avoid an extra wrapped line so Security fits without page scrolling.
        # Colors and wallpaper now share a single appearance tile.
        image_heading = QLabel('HINTERGRUNDBILD')
        image_heading.setObjectName('supportText')
        image_heading.setStyleSheet('font-weight: 700;')
        colors_layout.addWidget(image_heading)
        image_layout = colors_layout
        # The chosen image stays on disk; only its path and display mode are stored.
        # Vertical actions avoid cramped/overlapping buttons in narrow windows.
        picture_actions = QVBoxLayout()
        picture_actions.setSpacing(2)
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
        colors_layout.addStretch(1)

        settings_page_layout.addWidget(colors, 1)

        # Language has its own glass tile immediately below Appearance.
        # There is only one language selector for the entire application.
        language_card = GlossyGlassCard('SPRACHE')
        self.language_card = language_card
        self.secondary_cards.append(language_card)
        language_card.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        language_card.layout().setContentsMargins(13, 5, 13, 6)
        language_card.layout().setSpacing(1)
        language_card.body.setSpacing(2)
        self.language_combo = QComboBox()
        self.language_combo.setObjectName('languageCombo')
        self.language_combo.setAccessibleName('Sprache auswählen')
        for name, code in LANGUAGES:
            self.language_combo.addItem(name, code)
        self.language_combo.setCurrentIndex(0 if self.language == 'de' else 1)
        language_card.body.addWidget(self.language_combo)
        settings_page_layout.addWidget(language_card, 0)

        security_card = GlossyGlassCard('SICHERHEIT')
        self.security_card = security_card
        self.secondary_cards.append(security_card)
        security_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        security_card.layout().setContentsMargins(13, 5, 13, 6)
        security_card.layout().setSpacing(1)
        security_card.body.setSpacing(3)
        clipboard_row = QHBoxLayout()
        clipboard_row.setSpacing(6)
        self.clear_clipboard_checkbox = QCheckBox('Zwischenablage automatisch leeren')
        self.clear_clipboard_checkbox.setObjectName('autoClearClipboard')
        self.clear_clipboard_checkbox.setChecked(
            self.settings.value('security/clipboard_auto_clear', True, type=bool)
        )
        clipboard_row.addWidget(self.clear_clipboard_checkbox, 1)
        self.clipboard_timeout_combo = QComboBox()
        self.clipboard_timeout_combo.setObjectName('clipboardTimeoutCombo')
        for caption, seconds in (('30 Sekunden', 30), ('60 Sekunden', 60),
                                 ('2 Minuten', 120)):
            self.clipboard_timeout_combo.addItem(caption, seconds)
        saved_seconds = self.settings.value(
            'security/clipboard_seconds', 60, type=int
        )
        timeout_index = self.clipboard_timeout_combo.findData(saved_seconds)
        self.clipboard_timeout_combo.setCurrentIndex(max(0, timeout_index))
        self.clipboard_timeout_combo.setEnabled(self.clear_clipboard_checkbox.isChecked())
        clipboard_row.addWidget(self.clipboard_timeout_combo)
        security_card.body.addLayout(clipboard_row)
        self.privacy_focus_checkbox = QCheckBox(
            'Passwort beim Fensterwechsel verbergen'
        )
        self.privacy_focus_checkbox.setObjectName('privacyOnDeactivate')
        self.privacy_focus_checkbox.setChecked(
            self.settings.value('security/hide_on_deactivate', True, type=bool)
        )
        self.privacy_focus_checkbox.toggled.connect(
            lambda v: self.settings.setValue('security/hide_on_deactivate', v)
        )
        security_card.body.addWidget(self.privacy_focus_checkbox)
        self.history_confirm_checkbox = QCheckBox(
            'Vor dem Öffnen des Verlaufs bestätigen'
        )
        self.history_confirm_checkbox.setObjectName('confirmPasswordHistory')
        self.history_confirm_checkbox.setChecked(
            self.settings.value('security/confirm_history', False, type=bool)
        )
        self.history_confirm_checkbox.toggled.connect(
            lambda v: self.settings.setValue('security/confirm_history', v)
        )
        security_card.body.addWidget(self.history_confirm_checkbox)
        self.clear_clipboard_checkbox.setToolTip(
            'Nur löschen, solange das kopierte Passwort noch in der Zwischenablage steht.'
        )
        settings_page_layout.addWidget(security_card, 0)

        self.clipboard_timer = QTimer(self)
        self.clipboard_timer.setSingleShot(True)
        self.clipboard_timer.timeout.connect(self.clear_copied_password)
        self.clear_clipboard_checkbox.toggled.connect(self.configure_clipboard_clear)
        self.clipboard_timeout_combo.currentIndexChanged.connect(self.configure_clipboard_clear)

        self.updates_page = QWidget()
        self.updates_page.setObjectName('updatesPage')
        updates_page_layout = QVBoxLayout(self.updates_page)
        updates_page_layout.setSpacing(5)
        updates_page_layout.setContentsMargins(3, 4, 3, 3)

        updates = GlossyGlassCard('UPDATE & VERSION')
        self.glass_cards.append(updates)
        updates.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        updates_layout = updates.body
        updates_layout.setSpacing(4)
        updates.layout().setContentsMargins(13, 7, 13, 9)
        updates.layout().setSpacing(2)
        channel_row = QHBoxLayout()
        channel_row.setSpacing(8)
        self.channel_label = QLabel('Update-Kanal:')
        channel_row.addWidget(self.channel_label)
        self.channel_combo = QComboBox()
        self.channel_combo.setObjectName('updateChannelCombo')
        self.channel_combo.setAccessibleName('Stable oder Unstable auswählen')
        self.channel_combo.addItem('Stable', 'stable')
        self.channel_combo.addItem('Unstable (Test)', 'unstable')
        self.channel_combo.setCurrentIndex(
            self.channel_combo.findData(self.update_channel)
        )
        self.channel_combo.currentIndexChanged.connect(self.change_update_channel)
        channel_row.addWidget(self.channel_combo)
        channel_row.addStretch(1)
        updates_layout.addLayout(channel_row)
        self.update_status = QLabel(f'Installiert: v{APP_VERSION} · Noch nicht geprüft')
        self.update_status.setWordWrap(True)
        updates_layout.addWidget(self.update_status)
        self.update_compare = QLabel('')
        self.update_compare.setObjectName('updateVersionCompare')
        self.update_compare.setWordWrap(True)
        self.update_compare.hide()
        updates_layout.addWidget(self.update_compare)
        self.update_preview = QLabel('')
        self.update_preview.setObjectName('updatePreview')
        self.update_preview.setProperty('_i18n_de_text', '')
        self.update_preview.setWordWrap(True)
        self.update_preview.hide()
        updates_layout.addWidget(self.update_preview)
        update_actions = QHBoxLayout()
        update_actions.setSpacing(6)
        self.check_button = QPushButton('↻ Auf Update prüfen')
        self.check_button.setObjectName('checkUpdateButton')
        self.check_button.setToolTip('Jetzt auf Updates prüfen')
        self.check_button.setFixedWidth(175)
        self.check_button.setMinimumHeight(23)
        self.check_button.clicked.connect(self.check_for_updates)
        update_actions.addWidget(self.check_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.download_button = QPushButton('Update installieren & neu starten')
        self.download_button.setObjectName('primaryButton')
        self.download_button.clicked.connect(self.download_update)
        self.download_button.hide()
        update_actions.addWidget(self.download_button, 0, Qt.AlignmentFlag.AlignLeft)
        update_actions.addStretch(1)
        updates_layout.addLayout(update_actions)
        self.rollback_button = QPushButton('↶ Vorherige Version wiederherstellen')
        self.rollback_button.setObjectName('rollbackButton')
        self.rollback_button.clicked.connect(self.rollback_update)
        self.rollback_button.setToolTip('Nach Bestätigung eine frühere Version wiederherstellen')
        updates_layout.addWidget(self.rollback_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        updates_layout.addWidget(self.progress_bar)
        self.download_button.setToolTip(
            'Download prüfen, nach Bestätigung installieren und anschließend neu starten.'
        )

        updates_page_layout.addWidget(updates, 0)
        # One CHANGELOG tile includes both version selection and release notes.
        changelog_card = GlossyGlassCard('CHANGELOG')
        self.changelog_card = changelog_card
        self.secondary_cards.append(changelog_card)
        changelog_card.setSizePolicy(QSizePolicy.Policy.Expanding,
                                     QSizePolicy.Policy.Expanding)
        changelog_card.layout().setContentsMargins(13, 5, 13, 6)
        changelog_card.layout().setSpacing(1)
        changelog_layout = changelog_card.body
        changelog_layout.setSpacing(3)
        versions_heading = QLabel('BISHERIGE VERSIONEN')
        versions_heading.setObjectName('supportText')
        versions_heading.setStyleSheet('font-weight: 700;')
        changelog_layout.addWidget(versions_heading)
        self.release_combo = QComboBox()
        self.release_combo.setObjectName('releaseVersionCombo')
        self.release_combo.setAccessibleName('Bisherige Versionen auswählen')
        self.release_combo.addItem('Versionen werden geladen …', None)
        self.release_combo.setEnabled(False)
        self.release_combo.currentIndexChanged.connect(self.select_release_history)
        changelog_layout.addWidget(self.release_combo)
        self.release_history_status = QLabel('Versionshistorie noch nicht geladen.')
        self.release_history_status.setObjectName('supportText')
        self.release_history_status.setWordWrap(True)
        changelog_layout.addWidget(self.release_history_status)
        changes_heading = QLabel('ÄNDERUNGEN & VERSIONEN')
        changes_heading.setObjectName('supportText')
        changes_heading.setStyleSheet('font-weight: 700;')
        changelog_layout.addWidget(changes_heading)
        self.changelog_title = QLabel('Änderungen der veröffentlichten Version')
        self.changelog_title.setObjectName('supportText')
        self.changelog_title.setWordWrap(True)
        changelog_layout.addWidget(self.changelog_title)
        self.changelog_view = QTextBrowser()
        self.changelog_view.setObjectName('changelogView')
        self.changelog_view.setOpenExternalLinks(False)
        self.changelog_view.setOpenLinks(False)
        self.changelog_view.setFixedHeight(124)
        self.changelog_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.changelog_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._set_changelog_ui(
            'Die Änderungen werden beim Öffnen dieser Seite automatisch geladen.'
        )
        changelog_layout.addWidget(self.changelog_view)
        changelog_layout.addStretch(1)
        updates_page_layout.addWidget(changelog_card, 1)

        # Info is the fourth built-in page, never a separate modal window.
        self.info_page = QWidget()
        self.info_page.setObjectName('infoPage')
        info_layout = QVBoxLayout(self.info_page)
        info_layout.setContentsMargins(3, 4, 3, 3)
        info_layout.setSpacing(4)
        # Creator credit gets its own tile above the help tile.
        self.info_card = GlossyGlassCard('ÜBER DAS PROGRAMM')
        self.info_card.setObjectName('infoCreatorCard')
        self.info_card.setSizePolicy(QSizePolicy.Policy.Expanding,
                                     QSizePolicy.Policy.Preferred)
        self.info_card.layout().setContentsMargins(16, 9, 16, 11)
        info_layout.addWidget(self.info_card, 0)
        info_body = self.info_card.body
        info_body.setSpacing(6)
        self.info_credit = QLabel('Made by Jon Bovi')
        self.info_credit.setObjectName('infoCredit')
        self.info_credit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_credit.setStyleSheet('font-size: 22px; font-weight: 850;')
        info_body.addWidget(self.info_credit)
        self.info_version = QLabel(
            f'Passwort-Generator v{APP_VERSION} · {version_status()}'
        )
        self.info_version.setObjectName('supportText')
        self.info_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_body.addWidget(self.info_version)
        self.info_description = QLabel(
            'Passwörter und Passphrasen lokal erstellen · Windows und Linux. '
            'Es werden keine erzeugten Passwörter übertragen.'
        )
        self.info_description.setObjectName('supportText')
        self.info_description.setWordWrap(True)
        self.info_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_body.addWidget(self.info_description)

        # A separate Hilfe tile contains the replay tour and illustrated help.
        self.info_help_card = GlossyGlassCard('ANLEITUNG & HILFE')
        self.info_help_card.setObjectName('infoHelpCard')
        self.info_help_card.setSizePolicy(QSizePolicy.Policy.Expanding,
                                          QSizePolicy.Policy.Expanding)
        self.info_help_card.layout().setContentsMargins(16, 9, 16, 11)
        self.secondary_cards.append(self.info_help_card)
        info_layout.addWidget(self.info_help_card, 1)
        help_body = self.info_help_card.body
        help_body.setSpacing(5)
        info_actions = QHBoxLayout()
        info_actions.setSpacing(5)
        self.visual_guide_button = QPushButton('▣ Grafische Erklärung')
        self.visual_guide_button.setObjectName('visualGuideButton')
        self.visual_guide_button.clicked.connect(self.show_visual_guide)
        info_actions.addWidget(self.visual_guide_button, 1)
        self.repeat_tour_button = QPushButton('➜ Tour mit Pfeilen')
        self.repeat_tour_button.setObjectName('repeatTourButton')
        self.repeat_tour_button.clicked.connect(
            lambda: self.show_first_run_tour(force=True)
        )
        info_actions.addWidget(self.repeat_tour_button, 1)
        help_body.addLayout(info_actions)
        self.info_detail_stack = QStackedWidget()
        self.info_detail_stack.setObjectName('infoDetailStack')
        intro_panel = QWidget()
        intro_layout = QVBoxLayout(intro_panel)
        intro_layout.setContentsMargins(4, 10, 4, 4)
        intro_hint = QLabel(
            'Alle Funktionen im Überblick. Wähle „Grafische Erklärung“ '
            'für drei bebilderte Ansichten oder starte die Tour direkt im Fenster.'
        )
        intro_hint.setWordWrap(True)
        intro_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        intro_layout.addWidget(intro_hint)
        intro_layout.addStretch(1)
        self.info_detail_stack.addWidget(intro_panel)
        self._info_visual_loaded = False
        help_body.addWidget(self.info_detail_stack, 1)

        self.tabs.addWidget(self.password_page)
        self.tabs.addWidget(self.settings_page)
        self.tabs.addWidget(self.updates_page)
        self.tabs.addWidget(self.info_page)
        self.tabs.setCurrentIndex(0)

        self.status = QLabel('')
        self.status.setObjectName('globalStatus')
        self.status.setWordWrap(True)
        content_layout.addWidget(self.status)

        self.scheme_combo.currentIndexChanged.connect(self.apply_color_scheme)
        self.bg_combo.currentIndexChanged.connect(self.on_manual_color_change)
        self.image_mode_combo.currentIndexChanged.connect(self.update_image_mode)
        self.language_combo.currentIndexChanged.connect(self.change_language)
        self.restore_colors()
        self.restore_background_image()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        # The startup check and repeating 2-hour timer are both disabled in
        # CI/screenshot modes, so these runs never contact GitHub.
        self.update_timer = QTimer(self)
        self.update_timer.setObjectName('periodicUpdateTimer')
        self.update_timer.setInterval(UPDATE_CHECK_INTERVAL_MS)
        self.update_timer.timeout.connect(self.check_for_updates)
        if self._auto_check:
            self.update_timer.start()
            # Show the first-run introduction before any possible update popup.
            QTimer.singleShot(280, self.show_first_run_tour)
            QTimer.singleShot(800, self.check_for_updates)
        self.on_tab_changed(self.tabs.currentIndex())
        self._translate_interface()
        self.update_navigation_labels()
        self.restore_window_geometry()
        self._shortcuts = []
        for key, callback in (
            ('Ctrl+G', self.generate),
            ('Ctrl+Shift+C', self.copy),
            ('Ctrl+H', self.show_history),
            ('Ctrl+1', lambda: self.tabs.setCurrentIndex(0)),
            ('Ctrl+2', lambda: self.tabs.setCurrentIndex(2)),
            ('Ctrl+3', lambda: self.tabs.setCurrentIndex(1)),
            ('Ctrl+4', self.show_info),
        ):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)
            self._shortcuts.append(shortcut)
        if self.reporter is not None:
            self.reporter.note('UI_STARTED', 'neon interface ready', force=True)

    def _t(self, german):
        """Translate only UI text, never generated secrets or release bodies."""
        return translate(german, self.language)

    def _set_ui(self, widget, german):
        """Remember original German for switching back without losing state."""
        widget.setProperty('_i18n_de_text', german)
        widget.setText(self._t(german))

    def _set_placeholder(self, widget, german):
        widget.setProperty('_i18n_de_placeholder', german)
        widget.setPlaceholderText(self._t(german))

    def _set_changelog_ui(self, german):
        """Local UI state, rather than GitHub notes, changes with the language."""
        self.changelog_view.setProperty('_i18n_de_content', german)
        self.changelog_view.setPlainText(self._t(german))

    def _set_changelog_release(self, body, tag):
        """Render the selected release from its original, unmodified Markdown."""
        self.changelog_view.setProperty('_i18n_de_content', None)
        self.changelog_view.setPlainText(
            release_changelog(body, tag, self.language)
        )

    def _translate_interface(self):
        """Retranslate visible widgets in place; do not rebuild pages or controls."""
        from PySide6.QtWidgets import QAbstractButton

        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QLabel, QAbstractButton)):
                source = widget.property('_i18n_de_text')
                if source is None:
                    source = widget.text()
                    widget.setProperty('_i18n_de_text', source)
                if source:
                    widget.setText(self._t(source))
            for prop, setter, getter in (
                ('_i18n_de_tooltip', widget.setToolTip, widget.toolTip),
                ('_i18n_de_accessible', widget.setAccessibleName, widget.accessibleName),
            ):
                source = widget.property(prop)
                if source is None:
                    source = getter()
                    if source:
                        widget.setProperty(prop, source)
                if source:
                    setter(self._t(source))
            if isinstance(widget, QLineEdit):
                source = widget.property('_i18n_de_placeholder')
                if source is None:
                    source = widget.placeholderText()
                    if source:
                        widget.setProperty('_i18n_de_placeholder', source)
                if source:
                    widget.setPlaceholderText(self._t(source))

        # Never retranslate the release dropdown: its labels come from GitHub.
        # Keep itemData unchanged so saved schemes and separators still work.
        if not hasattr(self, '_i18n_combo_sources'):
            self._i18n_combo_sources = {}
        for combo in (self.scheme_combo, self.bg_combo,
                      self.image_mode_combo, self.phrase_separator,
                      self.preset_combo, self.clipboard_timeout_combo,
                      self.channel_combo):
            originals = self._i18n_combo_sources.get(combo)
            if originals is None or len(originals) != combo.count():
                originals = [combo.itemText(i) for i in range(combo.count())]
                self._i18n_combo_sources[combo] = originals
            for index, source in enumerate(originals):
                label = self._t(source)
                if combo.itemText(index) != label:
                    combo.setItemText(index, label)
        self.update_navigation_labels()

        # Re-render any local Changelog placeholder or error. GitHub data is
        # handled by _set_changelog_release in change_language.
        local_source = self.changelog_view.property('_i18n_de_content')
        if local_source is not None:
            self.changelog_view.setPlainText(self._t(local_source))

    def change_language(self, *_):
        selected = self.language_combo.currentData()
        if selected not in ('de', 'en') or selected == self.language:
            return
        self.language = selected
        self.settings.setValue('ui/language', selected)
        self._translate_interface()
        self.apply_colors()
        self.set_update_indicator(self._available_update)
        self.refresh_update_preview()
        # Changelog is a remote QTextBrowser, not a QLabel. Re-render it
        # immediately in the global UI language, even when already loaded.
        tag = self.release_combo.currentData()
        if tag in self._history_releases:
            self.select_release_history(self.release_combo.currentIndex())
        elif self._latest_release_note is not None:
            latest_tag, body = self._latest_release_note
            self._set_ui(self.changelog_title, f'Kurzüberblick · {latest_tag}')
            self._set_changelog_release(body, latest_tag)
        # Recreate cached screenshots in the newly selected language.
        if self._info_visual_loaded:
            from visual_help import create_visual_guide_panel
            old = self.info_detail_stack.widget(1)
            selected_visual = self.info_detail_stack.currentWidget() is old
            panel = create_visual_guide_panel(self, self.info_detail_stack)
            self.info_detail_stack.addWidget(panel)
            if selected_visual:
                self.info_detail_stack.setCurrentWidget(panel)
            self.info_detail_stack.removeWidget(old)
            old.deleteLater()

    def current_password_profile(self):
        return {
            'length': self.length.value(),
            **{name: getattr(self, name).isChecked() for name in FIELDS},
        }

    def mark_password_preset_manual(self, *_):
        if self._applying_preset or self._phrase_mode:
            return
        manual = self.preset_combo.findData('manual')
        if manual >= 0 and self.preset_combo.currentIndex() != manual:
            self.preset_combo.blockSignals(True)
            self.preset_combo.setCurrentIndex(manual)
            self.preset_combo.blockSignals(False)

    def apply_password_preset(self, *_):
        if self._phrase_mode or self._applying_preset:
            return
        name = self.preset_combo.currentData()
        if name == 'custom':
            profile = decode_profile(
                self.settings.value('profiles/custom_password', '', type=str)
            )
            if profile is None:
                self._set_ui(self.status, 'Noch kein eigenes Profil gespeichert.')
                return
        else:
            profile = PRESETS.get(name)
        if profile is None:
            return
        self._applying_preset = True
        try:
            self.length.setValue(profile['length'])
            for key in FIELDS:
                getattr(self, key).setChecked(profile[key])
        finally:
            self._applying_preset = False
        self._set_ui(self.status, 'Passwort-Profil geladen.')

    def save_password_preset(self):
        if self._phrase_mode:
            return
        profile = validate_profile(self.current_password_profile())
        if profile is None:
            self._set_ui(self.status, 'Bitte gültige Zeichengruppen auswählen.')
            return
        self.settings.setValue('profiles/custom_password', encode_profile(profile))
        index = self.preset_combo.findData('custom')
        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentIndex(index)
        self.preset_combo.blockSignals(False)
        self._set_ui(self.status, 'Eigenes Passwort-Profil gespeichert.')

    def configure_clipboard_clear(self, *_):
        enabled = self.clear_clipboard_checkbox.isChecked()
        self.clipboard_timeout_combo.setEnabled(enabled)
        self.settings.setValue('security/clipboard_auto_clear', enabled)
        self.settings.setValue(
            'security/clipboard_seconds', self.clipboard_timeout_combo.currentData()
        )
        if not enabled:
            self.clipboard_timer.stop()
            self._clipboard_secret = None
        elif self._clipboard_secret:
            self.clipboard_timer.start(self.clipboard_timeout_combo.currentData() * 1000)

    def remember_copied_password(self, secret):
        """Track only our clipboard content, never overwrite newer user copies."""
        self.clipboard_timer.stop()
        self._clipboard_secret = None
        if self.clear_clipboard_checkbox.isChecked() and secret:
            self._clipboard_secret = secret
            self.clipboard_timer.start(self.clipboard_timeout_combo.currentData() * 1000)

    def clear_copied_password(self):
        secret = self._clipboard_secret
        self._clipboard_secret = None
        if secret and self.clear_clipboard_checkbox.isChecked():
            clipboard = QApplication.clipboard()
            if clipboard.text() == secret:
                clipboard.clear()
                self._set_ui(self.status, 'Kopiertes Passwort aus der Zwischenablage entfernt.')

    def show_advanced_rules(self):
        """Compact modal keeps the password page free from vertical scrolling."""
        dialog = QDialog(self)
        dialog.setWindowTitle(self._t('Erweiterte Passwort-Regeln'))
        dialog.setMinimumWidth(345)
        form = QVBoxLayout(dialog)
        rows = QGridLayout()
        minimum_digits = QSpinBox()
        minimum_digits.setRange(0, 20)
        minimum_digits.setObjectName('minDigitsRule')
        minimum_digits.setValue(self._advanced_rules['min_digits'])
        minimum_symbols = QSpinBox()
        minimum_symbols.setRange(0, 20)
        minimum_symbols.setObjectName('minSymbolsRule')
        minimum_symbols.setValue(self._advanced_rules['min_symbols'])
        excluded_chars = QLineEdit(self._advanced_rules['excluded_chars'])
        excluded_chars.setObjectName('excludedCharactersRule')
        excluded_chars.setMaxLength(256)
        rows.addWidget(QLabel(self._t('Mindestens Zahlen:')), 0, 0)
        rows.addWidget(minimum_digits, 0, 1)
        rows.addWidget(QLabel(self._t('Mindestens Sonderzeichen:')), 1, 0)
        rows.addWidget(minimum_symbols, 1, 1)
        rows.addWidget(QLabel(self._t('Zeichen ausschließen:')), 2, 0)
        rows.addWidget(excluded_chars, 2, 1)
        form.addLayout(rows)
        form.addWidget(QLabel(self._t(
            'Die Einstellungen werden lokal gespeichert, keine Passwörter.'
        )))
        buttons = QHBoxLayout()
        cancel = QPushButton(self._t('Abbrechen'))
        apply = QPushButton(self._t('Übernehmen'))
        cancel.clicked.connect(dialog.reject)
        apply.clicked.connect(dialog.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(apply)
        form.addLayout(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = {'min_digits': minimum_digits.value(),
                  'min_symbols': minimum_symbols.value(),
                  'excluded_chars': excluded_chars.text()}
        self._advanced_rules = values
        for name, value in values.items():
            self.settings.setValue('password/' + name, value)
        self.mark_password_preset_manual()
        self._set_ui(self.status, 'Erweiterte Passwort-Regeln gespeichert.')

    def show_security_analysis(self):
        if not self.output.text():
            QMessageBox.information(self, self._t('Sicherheitsanalyse'),
                                    self._t('Bitte zuerst ein Passwort generieren.'))
            return
        text = (
            f'{self._t("Geschätzte Entropie:")} {self._last_entropy_bits:.1f} Bit\n'
            f'{self._t("Passwortstärke:")} {self.strength_label.text()}\n\n'
            + self._t('Eine Schätzung, keine Garantie gegen Passwortdiebstahl.')
        )
        QMessageBox.information(self, self._t('Sicherheitsanalyse'), text)

    def changeEvent(self, event):
        super().changeEvent(event)
        if (event.type() == QEvent.Type.WindowDeactivate
                and hasattr(self, 'privacy_focus_checkbox')
                and self.privacy_focus_checkbox.isChecked()
                and hasattr(self, 'show_button')
                and self.show_button.isChecked()):
            self.show_button.setChecked(False)

    def switch_mode(self, use_passphrase):
        """Switch between a random-character password and a word passphrase."""
        self._phrase_mode = bool(use_passphrase)
        self.password_mode_button.setChecked(not self._phrase_mode)
        self.passphrase_mode_button.setChecked(self._phrase_mode)
        self.options_widget.setVisible(not self._phrase_mode)
        self.rules_button.setVisible(not self._phrase_mode)
        self.phrase_options_widget.setVisible(self._phrase_mode)
        self.preset_combo.setEnabled(not self._phrase_mode)
        self.save_preset_button.setEnabled(not self._phrase_mode)
        if self._phrase_mode:
            self._set_ui(self.length_label, 'Wörter:')
            self.length.setRange(4, 10)
            self.length_slider.setRange(4, 10)
            self.length.setValue(6)
            self._set_ui(self.generate_button, '🔑  Passphrase generieren')
            self._set_ui(self.ocean_page_title, 'PASSPHRASE ERSTELLEN')
            self._set_ui(self.ocean_output_caption, 'Generierte Passphrase')
            self._set_ui(self.ocean_length_heading, 'Passphrase-Wörter')
            self.ocean_min_label.setText('4')
            self.ocean_max_label.setText('10')
            self._set_placeholder(self.output, 'Generierte Passphrase')
        else:
            self._set_ui(self.length_label, 'Länge:')
            self.length.setRange(8, 128)
            self.length_slider.setRange(8, 128)
            self.length.setValue(20)
            self._set_ui(self.generate_button, '🔑  Passwort generieren')
            self._set_ui(self.ocean_page_title, 'PASSWORT ERSTELLEN')
            self._set_ui(self.ocean_output_caption, 'Generiertes Passwort')
            self._set_ui(self.ocean_length_heading, 'Passwort-Länge')
            self.ocean_min_label.setText('8')
            self.ocean_max_label.setText('128')
            self._set_placeholder(self.output, 'Generiertes Passwort')
        self.output.clear()
        self._set_ui(self.strength_label, '🛡  Stärke: --')
        self.strength_bar.setValue(0)
        self._set_ui(self.ocean_strength_value, '--')
        self.update_ocean_presentation()
        self._set_ui(self.status, '')
        if self.reporter is not None:
            self.reporter.note('MODE_CHANGED', 'passphrase' if self._phrase_mode else 'password', force=True)

    def toggle_visibility(self, visible):
        self.output.setEchoMode(
            QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        )
        self._set_ui(self.show_button, '◉  Verbergen' if visible else '◉  Anzeigen')

    def show_history(self):
        """Show only passwords from this session; never persist history."""
        if self.history_confirm_checkbox.isChecked():
            answer = QMessageBox.question(
                self, self._t('Privatsphäre'),
                self._t('Den Passwortverlauf dieser Sitzung anzeigen?'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        dialog = QDialog(self)
        dialog.setWindowTitle(self._t('Verlauf – nur diese Sitzung'))
        dialog.resize(560, 360)
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        explanation = QLabel(
            self._t('Maximal 20 Einträge. Der Verlauf wird beim Schließen der App gelöscht.')
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        entries = QListWidget()
        for kind, secret in reversed(self._history):
            entries.addItem(f'{self._t(kind)}: {secret}')
        layout.addWidget(entries, 1)
        actions = QHBoxLayout()
        copy_button = QPushButton(self._t('Ausgewähltes kopieren'))
        copy_button.setEnabled(bool(self._history))

        def copy_selected():
            item = entries.currentRow()
            if item < 0:
                return
            secret = self._history[-1 - item][1]
            QApplication.clipboard().setText(secret)
            self.remember_copied_password(secret)
            dialog.accept()
            self._set_ui(self.status, 'Eintrag aus dem Verlauf kopiert.')

        copy_button.clicked.connect(copy_selected)
        actions.addWidget(copy_button)
        clear_button = QPushButton(self._t('Verlauf löschen'))

        def clear_history():
            self._history.clear()
            entries.clear()
            copy_button.setEnabled(False)

        clear_button.clicked.connect(clear_history)
        actions.addWidget(clear_button)
        close_button = QPushButton(self._t('Schließen'))
        close_button.clicked.connect(dialog.accept)
        actions.addWidget(close_button)
        layout.addLayout(actions)
        dialog.exec()

    def show_info(self):
        """Open Info as the fourth page inside the existing main window."""
        self.tabs.setCurrentIndex(3)

    def show_visual_guide(self):
        """Show the illustrated three-step help IN the Info page, not a dialog."""
        if not self._info_visual_loaded:
            from visual_help import create_visual_guide_panel
            panel = create_visual_guide_panel(self, self.info_detail_stack)
            self.info_detail_stack.addWidget(panel)
            self._info_visual_loaded = True
        self.info_detail_stack.setCurrentIndex(1)
        self._set_ui(self.visual_guide_button, '← Übersicht')
        # Reuse the same button to return to the compact overview.
        try:
            self.visual_guide_button.clicked.disconnect(self.show_visual_guide)
        except (TypeError, RuntimeError):
            pass
        self.visual_guide_button.clicked.connect(self.show_info_overview)

    def show_info_overview(self):
        self.info_detail_stack.setCurrentIndex(0)
        self._set_ui(self.visual_guide_button, '▣ Grafische Erklärung')
        try:
            self.visual_guide_button.clicked.disconnect(self.show_info_overview)
        except (TypeError, RuntimeError):
            pass
        self.visual_guide_button.clicked.connect(self.show_visual_guide)

    def show_first_run_tour(self, force=False):
        """Start once per user, except when explicitly repeated via Info."""
        if self._first_run_tour is not None or not self.isVisible():
            return
        if not force and self.settings.value(
            'first_run_tour_completed', False, type=bool
        ):
            return
        from first_run_tour import FirstRunTour
        self._first_run_tour = FirstRunTour(self)

    def flush_pending_update_popup(self):
        version = self._pending_update_popup
        self._pending_update_popup = None
        if version:
            QTimer.singleShot(150, lambda: self.show_update_popup(version))

    def show_update_popup(self, version):
        """Nonblocking popup for a new release found by the startup check."""
        if self._first_run_tour is not None:
            self._pending_update_popup = version
            return
        if self._update_popup_dialog is not None:
            return
        popup = QMessageBox(self)
        popup.setObjectName('startupUpdatePopup')
        popup.setIcon(QMessageBox.Icon.Information)
        popup.setWindowTitle(self._t('PasswortGenerator · Update verfügbar'))
        popup.setText(self._t(f'Eine neue Version {version} ist verfügbar!'))
        popup.setInformativeText(self._t(
            f'Du verwendest v{APP_VERSION}. Möchtest du die Aktualisierung '
            'jetzt im Update-Bereich ansehen? Es wird nichts automatisch installiert.'
        ))
        show_button = popup.addButton(
            self._t('Update öffnen'), QMessageBox.ButtonRole.AcceptRole
        )
        popup.addButton(self._t('Später'), QMessageBox.ButtonRole.RejectRole)
        popup.buttonClicked.connect(
            lambda clicked: self.tabs.setCurrentIndex(2)
            if clicked is show_button else None
        )
        popup.finished.connect(
            lambda _result: setattr(self, '_update_popup_dialog', None)
        )
        self._update_popup_dialog = popup
        popup.open()

    def queue_update_popup(self, version):
        if self._first_run_tour is not None:
            self._pending_update_popup = version
        else:
            QTimer.singleShot(0, lambda: self.show_update_popup(version))

    def on_tab_changed(self, index):
        # Each of the four pages is fitted to the window, never scrolled.
        self.tabs.updateGeometry()
        if index == 3:
            self.info_nav_button.setChecked(True)
        elif 0 <= index < len(self.nav_buttons):
            self.nav_buttons[index].setChecked(True)
        if (index == 2 and self._auto_check and not self._release_history_loaded
                and self.history_reply is None):
            self.load_release_history()
        if self.reporter is not None:
            self.reporter.note('NAVIGATE', f'tab={self.tab_names[index]}', force=True)

    def select_color(self, combo, color, default):
        if not QColor(color).isValid():
            color = default
        normalized = QColor(color).name().upper()
        for index in range(combo.count()):
            if combo.itemData(index).upper() == normalized:
                combo.setCurrentIndex(index)
                return
        source = f'Eigene Farbe ({normalized})'
        combo.addItem(self._t(source), normalized)
        if hasattr(self, '_i18n_combo_sources') and combo in self._i18n_combo_sources:
            self._i18n_combo_sources[combo].append(source)
        combo.setCurrentIndex(combo.count() - 1)

    def restore_colors(self):
        self._restoring = True
        try:
            stored_background = self.settings.value(
                'background_color', preset_colors(DEFAULT_SCHEME)[0], type=str
            )
            saved_scheme = self.settings.value('color_scheme', '', type=str)
            # Upgrade legacy untouched default to the new standard once.
            # All manually selected non-default themes and custom colors stay.
            previous_default = ('neon_blue', '#071322')
            if (not self.settings.value('ui/ocean_default_migrated', False, type=bool)
                    and (saved_scheme, stored_background.upper())
                    == (previous_default[0], previous_default[1].upper())):
                saved_scheme = DEFAULT_SCHEME
                self.settings.setValue('ui/ocean_default_migrated', True)
            if saved_scheme not in SCHEME_MAP:
                default_background = preset_colors(DEFAULT_SCHEME)[0]
                saved_scheme = (DEFAULT_SCHEME if
                                stored_background.upper() == default_background.upper()
                                else 'custom')
            index = self.scheme_combo.findData(saved_scheme)
            self.scheme_combo.setCurrentIndex(max(0, index))
            preset = preset_colors(saved_scheme)
            background = preset[0] if preset else stored_background
            self.select_color(self.bg_combo, background, '#071322')
        finally:
            self._restoring = False
        # Text is selected automatically for contrast; old manual preference is obsolete.
        self.settings.remove('text_color')
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
        selected = QColorDialog.getColor(QColor(combo.currentData()), self, self._t('Farbe auswählen'))
        if selected.isValid():
            self.select_color(combo, selected.name(), '#101827')

    def update_ocean_presentation(self):
        """Keep the real two-panel layout usable in all schemes and sizes."""
        ocean = self.scheme_combo.currentData() == 'ocean_glass'
        wide = self.width() >= 780
        state = (ocean, wide, self._phrase_mode)
        # Avoid repeatedly changing Qt child geometry while its parent
        # is being resized; only update when mode or breakpoint changes.
        if state == self._ocean_presentation_state:
            return
        self._ocean_presentation_state = state
        self.ocean_heading.setVisible(ocean and wide)
        self.ocean_hero_icon.setVisible(ocean and wide)
        for widget in (
            self.ocean_output_caption, self.ocean_strength_caption,
            self.ocean_strength_value, self.ocean_options_heading,
            self.ocean_length_heading, self.ocean_length_range,
        ):
            widget.setVisible(ocean)
        self.strength_label.setVisible(not ocean)
        self.length_label.setVisible(not ocean)
        self.length_value.setVisible(not ocean)
        self.ocean_preset_box.setVisible(not self._phrase_mode)
        if ocean and wide:
            # Prevent the enormous empty panels from the previous design.
            self.ocean_sections.setFixedHeight(251 if self._phrase_mode else 228)
            self.ocean_hero_icon.setPixmap(key_icon(30))
            self.brand_icon.setPixmap(key_icon(29))
            self.password_mode_button.setIcon(QIcon(key_icon(22, '#FFFFFF')))
            self.length.setMinimumHeight(50)
            self.length.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.length.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            self.ocean_length_range.layout().setContentsMargins(89, 0, 0, 0)
            self.output.setMinimumHeight(54)
            self.copy_top_button.setMinimumHeight(54)
            self.regenerate_button.setMinimumHeight(54)
        else:
            self.ocean_sections.setMinimumHeight(0)
            self.ocean_sections.setMaximumHeight(16777215)
            self.ocean_hero_icon.setPixmap(QPixmap())
            self.ocean_hero_icon.setText('🔑')
            self.brand_icon.setPixmap(QPixmap())
            self.brand_icon.setText('🔑')
            self.password_mode_button.setIcon(QIcon())
            self.length.setMinimumHeight(0)
            self.length.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
            self.ocean_length_range.layout().setContentsMargins(2, 0, 2, 0)
            self.output.setMinimumHeight(43)
            self.copy_top_button.setMinimumHeight(43)
            self.regenerate_button.setMinimumHeight(43)
        # Give the choices more breathing room on large screens without
        # forcing a scrollbar when the same app is resized narrowly.
        self.check_layout.setVerticalSpacing(13 if ocean and wide else 2)
        self.ocean_options_layout.setSpacing(11 if ocean and wide else 5)
        self.brand_subtitle.setVisible(not ocean)
        self.brand_icon.setFixedSize(44 if ocean else 53, 44 if ocean else 53)
        self._set_ui(
            self.brand_title,
            'PasswortGenerator' if ocean else 'Passwort-Generator',
        )
        self.generate_button.setFixedHeight(57 if ocean and wide else 40)
        self.generate_button.setMaximumWidth(16777215 if ocean else 360)
        self.password_group_layout.setAlignment(
            self.generate_button,
            Qt.AlignmentFlag(0) if ocean else Qt.AlignmentFlag.AlignHCenter,
        )

    def update_navigation_labels(self):
        """Compact top-right text without hiding an available-update marker."""
        compact = self.width() < 720
        labels = ('⌑ Passwort', '⚙ Einstellungen', '↻ Update')
        for index, (button, label) in enumerate(zip(self.nav_buttons, labels)):
            if index == 2 and self._available_update:
                label += ' • NEU'
            localized = self._t(label)
            if button.text() != localized:
                button.setText(localized)

    def set_update_indicator(self, version=None):
        """Show a persistent, contrast-rich update hint on the Update button."""
        self._available_update = version
        button = self.nav_buttons[2]
        button.setProperty('updateAvailable', bool(version))
        button.setToolTip(
            self._t(f'Neue Version {version} verfügbar – zum Installieren öffnen')
            if version else self._t('Nach neuen Versionen suchen')
        )
        self.update_navigation_labels()
        # Qt stylesheet dynamic properties need the affected widget re-polished.
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

    def restore_window_geometry(self):
        """Restore last window size and position on startup, if still valid."""
        stored = self.settings.value('window/geometry')
        if isinstance(stored, QByteArray) and not stored.isEmpty():
            return self.restoreGeometry(stored)
        return False

    def closeEvent(self, event):
        """Keep only window geometry, never secrets or session history."""
        if event.isAccepted():
            self.clipboard_timer.stop()
            self._clipboard_secret = None
            self.settings.setValue('window/geometry', self.saveGeometry())
            self.settings.sync()
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._first_run_tour is not None:
            self._first_run_tour.setGeometry(self.rect())
            self._first_run_tour.update()
        if hasattr(self, 'nav_buttons'):
            self.update_navigation_labels()
        if hasattr(self, 'ocean_sections') and hasattr(self, 'scheme_combo'):
            self.update_ocean_presentation()
        if hasattr(self, 'check_layout') and hasattr(self, 'upper'):
            compact = self.width() < 680
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
        base_background = self.bg_combo.currentData() or '#071322'
        image_color = self.background_surface.wallpaper_color
        actual_background = image_color or base_background
        fg = accessible_text_color(actual_background)
        accent = accent_for_background(actual_background)
        scheme = self.scheme_combo.currentData()
        ocean_mode = scheme == 'ocean_glass'
        glass_mode = scheme in ('glass', 'ocean_glass')
        self.background_surface.set_base_color(base_background)
        self.background_surface.set_ocean_mode(ocean_mode)
        self.background_surface.set_transparent_glass(glass_mode)
        for card in self.glass_cards + self.secondary_cards + [self.info_card]:
            card.set_glass_color(actual_background, accent)
            card.set_glass_mode(glass_mode)
            card.set_ocean_mode(ocean_mode)
        if hasattr(self, 'ocean_sections'):
            self.update_ocean_presentation()
        source = 'Bild' if image_color else 'Hintergrund'
        self._set_ui(self.accent_preview, f'●  Automatisch ({source}): {accent}')
        self.accent_preview.setToolTip(self._t(
            'Kontrastgeprüft und passend zum Hintergrundbild oder zur Hintergrundfarbe.'
        ))
        palette_key = (base_background, actual_background, fg, accent, glass_mode,
                       ocean_mode)
        if self._applied_palette != palette_key:
            self._applied_palette = palette_key
            self.setStyleSheet(
                build_glass_stylesheet(actual_background, fg)
                + '\n' + neon_stylesheet(actual_background, fg, accent,
                                         ocean_theme=ocean_mode)
            )
            self.settings.setValue('background_color', base_background)
            if self.reporter is not None:
                self.reporter.note(
                    'PALETTE_CHANGED',
                    f'background={base_background}, image={"yes" if image_color else "no"}',
                    force=True,
                )

    def restore_background_image(self):
        mode = self.settings.value('background_image_mode', 'cover', type=str)
        index = self.image_mode_combo.findData(mode)
        self.image_mode_combo.setCurrentIndex(index if index >= 0 else 0)
        path = self.settings.value('background_image_path', '', type=str)
        if path:
            try:
                self.background_surface.set_background_image(path)
                self._set_ui(self.background_file_label, Path(path).name)
            except (OSError, ValueError):
                self._set_ui(self.background_file_label, 'Gespeichertes Bild nicht gefunden oder ungültig.')
                self.background_surface.clear_background_image()
        self.clear_background_button.setEnabled(self.background_surface.has_background_image())
        self.apply_colors()

    def choose_background_image(self):
        selected, _ = QFileDialog.getOpenFileName(
            self, self._t('Hintergrundbild auswählen'), str(Path.home()),
            self._t('Bilder (*.png *.jpg *.jpeg *.webp *.bmp)'),
        )
        if not selected:
            return
        try:
            self.background_surface.set_background_image(selected)
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, self._t('Hintergrundbild nicht geladen'), self._t(str(error)))
            return
        self._set_ui(self.background_file_label, Path(selected).name)
        self.clear_background_button.setEnabled(True)
        self.settings.setValue('background_image_path', selected)
        self.apply_colors()
        self._set_ui(self.status, 'Hintergrundbild geladen.')
        if self.reporter is not None:
            self.reporter.note('BACKGROUND_LOADED', f'format={Path(selected).suffix.lower()}', force=True)

    def remove_background_image(self):
        self.background_surface.clear_background_image()
        self._set_ui(self.background_file_label, 'Kein Hintergrundbild ausgewählt')
        self.clear_background_button.setEnabled(False)
        self.settings.remove('background_image_path')
        self.apply_colors()
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
                generated = make_passphrase(
                    self.length.value(),
                    separator=self.phrase_separator.currentData(),
                    add_two_digit_number=self.phrase_two_digits.isChecked(),
                    language=self.phrase_language.currentData(),
                )
                label, score = estimate_strength(
                    generated,
                    phrase_words=self.length.value(),
                    extra_entropy_bits=(math.log2(90) if self.phrase_two_digits.isChecked() else 0),
                )
                self._last_entropy_bits = (
                    self.length.value() * 10.0
                    + (math.log2(90) if self.phrase_two_digits.isChecked() else 0)
                )
                kind = 'Passphrase'
            else:
                generated = make_password(
                    self.length.value(), use_lower=self.lower.isChecked(),
                    use_upper=self.upper.isChecked(), use_digits=self.digits.isChecked(),
                    use_symbols=self.symbols.isChecked(),
                    exclude_similar=self.exclude.isChecked(),
                    **self._advanced_rules,
                )
                self._last_entropy_bits = password_entropy_bits(
                    self.length.value(), use_lower=self.lower.isChecked(),
                    use_upper=self.upper.isChecked(),
                    use_digits=self.digits.isChecked(),
                    use_symbols=self.symbols.isChecked(),
                    exclude_similar=self.exclude.isChecked(),
                    excluded_chars=self._advanced_rules['excluded_chars'],
                )
                # Upper-bound estimate; constrained generation reduces the
                # effective search space, so never claim a crack-time guarantee.
                label, score = estimate_strength(
                    generated,
                    pool_size=max(2, round(2 ** (
                        self._last_entropy_bits / self.length.value()
                    )))
                )
                kind = 'Passwort'
        except ValueError as error:
            QMessageBox.warning(self, self._t('Auswahl fehlt'), self._t(str(error)))
            return

        self.output.setText(generated)
        self._set_ui(self.strength_label, f'🛡  Stärke: {label}')
        self._set_ui(self.ocean_strength_value, label)
        self.strength_bar.setValue(score)
        self._set_ui(self.status, f'{kind} erstellt.')
        self._history.append((kind, generated))
        del self._history[:-20]
        if self.reporter is not None:
            self.reporter.note('GENERATED', f'mode={kind.lower()}', force=True)

    def copy(self):
        if self.output.text():
            QApplication.clipboard().setText(self.output.text())
            self.remember_copied_password(self.output.text())
            self._set_ui(self.status, 'In die Zwischenablage kopiert.')

    @staticmethod
    def make_request(url):
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b'User-Agent', b'PasswortGenerator-UpdateChecker')
        request.setRawHeader(b'Accept', b'application/vnd.github+json')
        request.setTransferTimeout(30000)
        return request

    def change_update_channel(self, *_):
        """Switch feed only; never silently uninstall or replace an app."""
        selected = self.channel_combo.currentData()
        if selected not in ('stable', 'unstable') or selected == self.update_channel:
            return
        self.update_channel = selected
        self.settings.setValue('updates/channel', selected)
        self.latest_asset = None
        self.latest_version = None
        self._new_update_note = ''
        self._available_update = None
        self.set_update_indicator()
        self.download_button.hide()
        self.update_compare.hide()
        self.update_preview.hide()
        self._set_ui(self.update_status, 'Update-Kanal gewechselt · Prüfe GitHub …')
        if self.check_reply is not None:
            self.check_reply.abort()
            # An older reply must never be interpreted as the new channel.
            return
        self.check_for_updates()

    def refresh_update_preview(self):
        """Refresh the bilingual version comparison and two-point summary."""
        if not self.latest_version:
            self.update_compare.hide()
            self.update_preview.hide()
            return
        suffix = ' [UNSTABLE]' if CHANNEL == 'unstable' else ''
        self._set_ui(
            self.update_compare,
            f'Installiert: v{APP_VERSION}{suffix}  →  Neu: {self.latest_version}',
        )
        self.update_compare.show()
        summary = release_changelog(
            self._new_update_note, self.latest_version, self.language, max_items=2
        )
        if self._new_update_note and summary:
            self.update_preview.setText(summary)
            self.update_preview.show()
        else:
            self.update_preview.hide()

    def check_for_updates(self):
        if self.check_reply is not None or self.download_reply is not None:
            return
        # The existing update-check action also refreshes the list.
        # No extra "Versionshistorie laden" button is necessary.
        if self.tabs.currentIndex() == 2 and self.history_reply is None:
            self.load_release_history()
        self.check_button.setEnabled(False)
        self.channel_combo.setEnabled(False)
        self._checked_channel = self.update_channel
        self.download_button.hide()
        self.update_compare.hide()
        self.update_preview.hide()
        self._set_ui(self.update_status, f'Installiert: v{APP_VERSION} · Prüfe GitHub …')
        self.check_reply = self.network.get(self.make_request(channel_api(self._checked_channel)))
        self.check_reply.finished.connect(self.check_finished)

    def check_finished(self):
        reply = self.check_reply
        self.check_reply = None
        self.check_button.setEnabled(True)
        self.channel_combo.setEnabled(True)
        startup_check = self._startup_update_check_pending
        self._startup_update_check_pending = False
        if reply is None:
            return
        if self._checked_channel != self.update_channel:
            reply.deleteLater()
            self.check_for_updates()
            return
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                raise ValueError(reply.errorString())
            response = json.loads(bytes(reply.readAll()).decode('utf-8'))
            if not isinstance(response, dict):
                raise ValueError('Ungültige GitHub-Antwort.')
            if self.update_channel == 'unstable':
                # GitHub prereleases are deliberately excluded from /latest.
                # The prerelease asset is named with its own build SHA.
                build_sha, asset = select_unstable_asset(response, os.name)
                latest_version = 'UNSTABLE ' + build_sha
                update_ready = has_channel_update(
                    'unstable', CHANNEL, build_sha, APP_VERSION,
                    APP_VERSION, BUILD_SHA, is_newer_release,
                )
            else:
                latest_version = response.get('tag_name', '')
                if parse_version(latest_version) is None:
                    raise ValueError('Ungültige Versionsnummer bei GitHub.')
                update_ready = has_channel_update(
                    'stable', CHANNEL, latest_version, APP_VERSION,
                    APP_VERSION, BUILD_SHA, is_newer_release,
                )
                assets = response.get('assets', [])
                artifact_name = (WINDOWS_INSTALLER_NAME if os.name == 'nt'
                                 else APPIMAGE_NAME)
                asset = next(
                    (item for item in assets if isinstance(item, dict)
                     and item.get('name') == artifact_name), None
                )
                if asset is None:
                    raise ValueError(
                        'Im neuesten Release ist noch kein '
                        + ('Windows-Installer.' if os.name == 'nt' else 'Linux-AppImage.')
                    )
                url = asset.get('browser_download_url', '')
                if (url != RELEASE_DOWNLOAD_PREFIX + latest_version + '/'
                        + artifact_name):
                    raise ValueError('Der GitHub-Downloadlink ist ungültig.')
            if not update_ready:
                self.latest_asset = None
                self.latest_version = None
                self._new_update_note = ''
                self.set_update_indicator()
                self.refresh_update_preview()
                self._set_ui(self.update_status,
                             'Dieser Update-Kanal ist bereits aktuell.')
                return
            if self.update_channel == 'stable':
                if not self._release_history_loaded and not self._history_releases:
                    note = response.get('body', '')
                    if isinstance(note, str) and note.strip():
                        self._latest_release_note = (latest_version, note)
                        self._set_ui(self.changelog_title,
                                     f'Kurzüberblick · {latest_version}')
                        self._set_changelog_release(note, latest_version)
            self.latest_asset = asset
            self.latest_version = latest_version
            note = response.get('body', '')
            self._new_update_note = note if isinstance(note, str) else ''
            self.set_update_indicator(latest_version)
            self.refresh_update_preview()
            self._set_ui(self.update_status,
                         f'Neue Version {latest_version} verfügbar! Installiert: v{APP_VERSION}')
            self._set_ui(
                self.download_button,
                ('Testversion installieren & starten'
                 if self.update_channel == 'unstable'
                 else 'Stable installieren & neu starten'),
            )
            self.download_button.show()
            if startup_check:
                self.queue_update_popup(latest_version)
        except (ValueError, TypeError, KeyError, UnicodeDecodeError) as error:
            self.latest_asset = None
            self.latest_version = None
            self._new_update_note = ''
            self.refresh_update_preview()
            self._set_ui(self.update_status, f'Updateprüfung fehlgeschlagen: {error}')
        finally:
            reply.deleteLater()

    def load_release_history(self):
        """Fetch at most 100 public releases asynchronously from GitHub."""
        if self.history_reply is not None:
            return
        self._set_ui(self.release_history_status, 'Lade Versionen von GitHub …')
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
            releases = normalized_releases(json.loads(raw.decode('utf-8')), REPO_URL)
            self._history_releases = {item['tag']: item for item in releases}
            self._release_history_loaded = True
            previous_selection = self.release_combo.currentData()
            self.release_combo.blockSignals(True)
            self.release_combo.clear()
            for entry in releases:
                date_suffix = f" · {entry['date']}" if entry['date'] else ''
                self.release_combo.addItem(entry['tag'] + date_suffix, entry['tag'])
            if not releases:
                self.release_combo.addItem(self._t('Keine veröffentlichten Versionen'), None)
            self.release_combo.setEnabled(bool(releases))
            index = self.release_combo.findData(previous_selection)
            self.release_combo.setCurrentIndex(max(0, index))
            self.release_combo.blockSignals(False)
            self._set_ui(self.release_history_status, 
                f'{len(releases)} Version(en) · neueste zuerst'
            )
            if releases:
                self.select_release_history(self.release_combo.currentIndex())
            else:
                self._set_changelog_ui('Keine veröffentlichten Versionen gefunden.')
        except (ValueError, TypeError, UnicodeDecodeError, KeyError) as error:
            self._set_ui(self.release_history_status, 
                f'Versionshistorie nicht verfügbar: {error}'
            )
            if not self._release_history_loaded:
                self._set_changelog_ui(
                    'Die Versionshistorie konnte nicht geladen werden. '
                    'Bitte die Internetverbindung prüfen und erneut versuchen.'
                )
        finally:
            reply.deleteLater()

    def select_release_history(self, _index):
        """Show short changes for the selected release in the tile below."""
        tag = self.release_combo.currentData()
        entry = self._history_releases.get(tag)
        if entry is None:
            return
        self._set_ui(self.changelog_title, f'Kurzüberblick · {entry["tag"]}')
        self._set_changelog_release(entry['body'], entry['tag'])

    def rollback_update(self):
        """Restore the trusted local AppImage, or a verified older Windows release."""
        if CHANNEL == 'unstable':
            QMessageBox.information(
                self, 'UNSTABLE',
                'Rollback ist in der Testversion deaktiviert, um Stable zu schützen.'
            )
            return
        if self.download_reply is not None or self._rollback_reply is not None:
            return
        if os.name != 'nt':
            backup = previous_path(INSTALLED_APPIMAGE)
            if (not INSTALLED_APPIMAGE.is_file() or not backup.is_file()
                    or INSTALLED_APPIMAGE.is_symlink() or backup.is_symlink()):
                QMessageBox.information(
                    self, self._t('Vorherige Version'),
                    self._t('Keine vorherige AppImage-Version zur Wiederherstellung vorhanden.')
                )
                return
            choice = QMessageBox.question(
                self, self._t('Update rückgängig machen'),
                self._t('Vorherige AppImage-Version wiederherstellen und neu starten?'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if choice != QMessageBox.StandardButton.Yes:
                return
            try:
                restore_previous_appimage(INSTALLED_APPIMAGE)
                restart_updated_app(INSTALLED_APPIMAGE)
            except (ValueError, OSError) as error:
                QMessageBox.warning(self, self._t('Wiederherstellung fehlgeschlagen'),
                                    self._t(str(error)))
                return
            QTimer.singleShot(120, QApplication.instance().quit)
            return
        # Windows: the user selects an older published release in the existing
        # Changelog dropdown. Never execute an untrusted/unchecked setup file.
        selected_tag = self.release_combo.currentData()
        previous_version = parse_version(selected_tag)
        current_version = parse_version(APP_VERSION)
        if (previous_version is None or current_version is None
                or previous_version >= current_version
                or selected_tag not in self._history_releases):
            QMessageBox.information(
                self, self._t('Vorherige Version'),
                self._t('Bitte eine ältere Version im Changelog auswählen.')
            )
            return
        choice = QMessageBox.question(
            self, self._t('Update rückgängig machen'),
            self._t('Den offiziellen Installer der ausgewählten älteren Version laden?')
            + '\n' + str(selected_tag),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if choice != QMessageBox.StandardButton.Yes:
            return
        self._rollback_tag = selected_tag
        request = self.make_request(
            f'https://api.github.com/repos/{REPO}/releases/tags/{selected_tag}'
        )
        self._rollback_reply = self.network.get(request)
        self._rollback_reply.finished.connect(self.rollback_release_finished)

    def rollback_release_finished(self):
        reply = self._rollback_reply
        self._rollback_reply = None
        if reply is None:
            return
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                raise ValueError(reply.errorString())
            raw = bytes(reply.readAll())
            if len(raw) > 2_000_000:
                raise ValueError('Die Antwort von GitHub ist zu groß.')
            release = json.loads(raw.decode('utf-8'))
            tag = self._rollback_tag
            if (not isinstance(release, dict)
                    or release.get('tag_name') != tag or release.get('draft')
                    or not isinstance(release.get('assets'), list)):
                raise ValueError('Ungültige GitHub-Version für die Wiederherstellung.')
            asset = next((a for a in release['assets']
                          if isinstance(a, dict)
                          and a.get('name') == WINDOWS_INSTALLER_NAME), None)
            if asset is None:
                raise ValueError('Kein Windows-Installer in dieser Version vorhanden.')
            url = asset.get('browser_download_url', '')
            if (not isinstance(url, str)
                    or url != (f'{RELEASE_DOWNLOAD_PREFIX}{tag}/'
                               f'{WINDOWS_INSTALLER_NAME}')
                    or not isinstance(asset.get('size'), int)
                    or asset['size'] < 100000
                    or not isinstance(asset.get('digest'), str)
                    or not asset['digest'].startswith('sha256:')):
                raise ValueError('Verifizierbarer Windows-Installer fehlt.')
            self.latest_asset = asset
            self.latest_version = tag
            self._rollback_pending = True
            self.download_update()
        except (OSError, ValueError, UnicodeDecodeError, TypeError) as error:
            QMessageBox.warning(
                self, self._t('Wiederherstellung fehlgeschlagen'), self._t(str(error))
            )
        finally:
            reply.deleteLater()

    def download_update(self):
        if self.download_reply is not None or not self.latest_asset:
            return
        if self.update_channel == 'unstable':
            answer = QMessageBox.question(
                self, self._t('Unstable-Testversion'),
                self._t('Unstable enthält unfertige Funktionen. Separat von Stable installieren?'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        if self.reporter is not None:
            self.reporter.note('UPDATE_DOWNLOAD_START', f'version={self.latest_version}', force=True)
        install_path = (UNSTABLE_APPIMAGE if self.update_channel == 'unstable'
                        else INSTALLED_APPIMAGE)
        self.download_installed = (
            os.name != 'nt' and (
                self.update_channel == 'unstable'
                or (INSTALLED_APPIMAGE.is_file()
                    and os.access(INSTALLED_APPIMAGE.parent, os.W_OK))
            )
        )
        download_location = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        )
        download_dir = Path(download_location) if download_location else Path.home() / 'Downloads'
        if os.name == 'nt':
            target = download_dir / self.latest_asset['name']
        elif self.download_installed:
            target = install_path
        else:
            target = download_dir / f'PasswortGenerator-{self.latest_version}-x86_64.AppImage'
        stage = staging_path(target) if self.download_installed else target
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            save_file = QSaveFile(str(stage))
            if not save_file.open(QIODevice.OpenModeFlag.WriteOnly):
                raise OSError(save_file.errorString())
        except OSError as error:
            QMessageBox.warning(self, self._t('Download nicht möglich'), self._t(str(error)))
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
        self._set_ui(self.update_status, f'Lade {self.latest_version} von GitHub herunter …')
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
            if not isinstance(expected_digest, str) or not expected_digest.startswith('sha256:'):
                raise ValueError('GitHub hat keine SHA-256-Prüfsumme für dieses Release bereitgestellt.')
            actual_digest = self.download_hash.hexdigest()
            if actual_digest.lower() != expected_digest.split(':', 1)[1].lower():
                raise ValueError('Die SHA-256-Prüfsumme stimmt nicht überein!')
            if not self.save_file.commit():
                raise OSError(self.save_file.errorString())
            if os.name == 'nt':
                # The Inno installer closes old files and restarts the updated
                # application after successful installation.
                start_verified_windows_installer(
                    self.download_target, rollback=self._rollback_pending
                )
                if self.reporter is not None:
                    self.reporter.note(
                        'WINDOWS_UPDATE_SETUP_STARTED',
                        f'version={self.latest_version}', force=True,
                    )
                installed_successfully = True
                self.set_update_indicator()
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(100)
                self._set_ui(self.update_status, 
                    'Windows-Installer gestartet. Die App wird für das Update geschlossen …'
                )
                self.download_button.hide()
                QTimer.singleShot(200, QApplication.instance().quit)
                return
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
            self.set_update_indicator()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self._set_ui(self.update_status, 
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
                self._set_ui(self.update_status, msg)
                QMessageBox.warning(self, self._t('Manueller Neustart erforderlich'), self._t(msg))
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
            self._set_ui(self.update_status, f'Download/Installation fehlgeschlagen: {error}')
            QMessageBox.warning(self, self._t('Update fehlgeschlagen'), self._t(str(error)))
        finally:
            if not installed_successfully and self.download_installed and self.download_stage:
                try:
                    self.download_stage.unlink(missing_ok=True)
                except OSError:
                    pass
            self.save_file = None
            self.download_stage = None
            self._rollback_pending = False
            reply.deleteLater()


if __name__ == '__main__':
    reporter = CrashReporter()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    reporter.log('QT_ENVIRONMENT', f'Qt platform={app.platformName()}')
    if '--verify-bundle' in sys.argv:
        # Release CI calls the packaged executable on Windows. This validates
        # Qt plugins, asset paths, icons and top-level navigation without
        # making network requests or exposing generated passwords.
        window = PasswordWindow(auto_check=False, reporter=reporter)
        window.resize(920, 770)
        window.show()
        for _ in range(3):
            app.processEvents()
        healthy = (
            window.tabs.count() == 4
            and window.info_page is window.tabs.widget(3)
            and window.info_nav_button.isVisible()
            and len(window.glass_cards) == 3
            and window.length.value() == 20
        )
        window.close()
        reporter.close()
        sys.exit(0 if healthy else 3)
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
