"""An illustrated explanation embedded in the Info page, never a new window.

All three screenshots come from the actual running Qt pages and remain solely
in RAM. Preview widgets scale to the available space without scroll areas.
"""

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
        '2 · Design',
        'Farben und Glas',
        'Unter Einstellungen kannst du „Glass“ für gut sichtbare '
        'Hintergrundbilder oder andere Farbschemas auswählen.',
    ),
    (
        '3 · Update',
        'Updateprüfung und Versionen',
        'Neue Versionen erscheinen oben als „Update • NEU“. '
        'Wähle eine Version im Dropdown, um ihre Änderungen darunter zu lesen.',
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
    try:
        for index, (tab_name, title, description) in enumerate(SCREENS):
            window.tabs.setCurrentIndex(index)
            QApplication.processEvents()
            image = window.tabs.widget(index).grab()
            if image.isNull():
                raise RuntimeError(f'Bildschirmansicht {tab_name} ist leer.')
            page = QWidget()
            page.setObjectName(f'visualGuidePage{index}')
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(5, 4, 5, 4)
            page_layout.setSpacing(2)
            heading = QLabel(f'{title}: {description}')
            heading.setObjectName('visualGuideDescription')
            heading.setWordWrap(True)
            page_layout.addWidget(heading)
            image_label = ScaledScreenshot(image)
            image_label.setObjectName(f'visualGuideImage{index}')
            image_label.setAccessibleName(f'Grafische Ansicht: {tab_name}')
            page_layout.addWidget(image_label, 1)
            tabs.addTab(page, tab_name)
    finally:
        window.tabs.setCurrentIndex(original)
        window.tabs.blockSignals(previous_block)
        QApplication.processEvents()

    return panel
