"""An illustrated explanation embedded in the Info page, never a new window.

All three screenshots come from the actual running Qt pages and remain solely
in RAM. Preview widgets scale to the available space without scroll areas.
"""

from localization import translate
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication, QLabel, QSizePolicy, QTabWidget, QVBoxLayout, QWidget,
)

SCREENS = (
    (
        '1 · Passwort',
        'Passwort und Passphrase',
        'Modus wählen, Länge einstellen und auf „Generieren“ klicken. '
        'Eine zweistellige Zahl und das Trennzeichen kannst du bei Passphrase wählen.',
    ),
    (
        '2 · Einstellungen',
        'Sprache und Sicherheit',
        'Unter Einstellungen wechselst du zwischen Deutsch und Englisch und '
        'legst den Zwischenablageschutz und die Privatsphäre fest.',
    ),
    (
        '3 · Update',
        'Updateprüfung und Versionen',
        'Updateprüfung und Versionshistorie findest du in Einstellungen > Update. '
        'Im Dropdown kannst du frühere Versionen und ihre Änderungen lesen.',
    ),
)


class ScaledScreenshot(QLabel):
    """Keep a real screenshot proportional without content overflow."""

    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self._original = QPixmap(pixmap)
        self.setObjectName('visualGuideImage')
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(100, 80)
        # Hidden tabs may not receive resizeEvent until first selected.
        # Preload a small valid preview so all three graphics are available.
        if not self._original.isNull():
            self.setPixmap(self._original.scaled(
                480, 270, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._original.isNull() and self.width() > 0 and self.height() > 0:
            preview = self._original.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(preview)


def create_visual_guide_panel(window, parent=None):
    """Return a responsive Info child widget with 3 graphical pages."""
    panel = QWidget(parent)
    panel.setObjectName('inlineVisualGuide')
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(0, 3, 0, 0)
    layout.setSpacing(4)

    tabs = QTabWidget(panel)
    tabs.setObjectName('visualGuideTabs')
    layout.addWidget(tabs, 1)

    original = window.tabs.currentIndex()
    previous_block = window.tabs.blockSignals(True)
    settings_views = getattr(window, '_settings_views', None)
    original_settings_index = (
        settings_views.currentIndex() if settings_views is not None else None
    )
    real_pages = (window.password_page, window.settings_page, window.updates_page)
    try:
        for index, (tab_name, title, description) in enumerate(SCREENS):
            # Settings/Update/Info live in a secondary window in Compact Ocean.
            # Preview the real widgets in whichever stack currently owns them.
            if settings_views is not None:
                settings_views.setCurrentIndex((0, 0, 3)[index])
            else:
                window.tabs.setCurrentIndex(index)
            QApplication.processEvents()
            image = real_pages[index].grab()
            if image.isNull():
                raise RuntimeError(f'Empty screen preview: {tab_name}')
            page = QWidget()
            page.setObjectName(f'visualGuidePage{index}')
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(5, 4, 5, 4)
            page_layout.setSpacing(2)
            heading = QLabel(f'{translate(title, window.language)}: '
                             f'{translate(description, window.language)}')
            heading.setObjectName('visualGuideDescription')
            heading.setWordWrap(True)
            page_layout.addWidget(heading)
            image_label = ScaledScreenshot(image)
            image_label.setObjectName(f'visualGuideImage{index}')
            image_label.setAccessibleName(
                ('Visual preview: ' if window.language == 'en' else 'Grafische Ansicht: ')
                + translate(tab_name, window.language)
            )
            page_layout.addWidget(image_label, 1)
            tabs.addTab(page, translate(tab_name, window.language))
    finally:
        if settings_views is not None:
            settings_views.setCurrentIndex(original_settings_index)
        else:
            window.tabs.setCurrentIndex(original)
        window.tabs.blockSignals(previous_block)
        QApplication.processEvents()

    return panel
