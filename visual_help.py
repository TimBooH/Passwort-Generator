"""Interactive illustrated guide using screenshots of the running Qt widgets.

The three screens are captured in memory, never written to disk or uploaded.
The password input stays masked. Works unchanged on Linux and Windows.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QDialog, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QTabWidget, QVBoxLayout, QWidget,
)

SCREENS = (
    (
        '1 · Passwort',
        'PASSWORT / PASSPHRASE',
        'Zwischen Passwort und Passphrase wechseln. Bei Passphrase können '
        'Trennzeichen und eine zufällige zweistellige Zahl gewählt werden. '
        'Mit dem großen Knopf generieren, mit ⧉ kopieren.',
    ),
    (
        '2 · Design',
        'DESIGN & FARBEN',
        'Unter Einstellungen kannst du Glass Dark, Glass Light und weitere '
        'Farbschemas auswählen. Auch eigene Hintergrundbilder sind möglich.',
    ),
    (
        '3 · Updates',
        'UPDATES & VERSIONEN',
        'Hier siehst du Änderungen und frühere Versionen. Wenn ein Update '
        'verfügbar ist, erscheint oben rechts „Updates • NEU“. Nach einem Klick '
        'auf „Update installieren“ lädt und prüft die App die neue Version.',
    ),
)


def create_visual_guide(window, parent=None):
    """Return a dialog containing three REAL Qt page screenshots and captions."""
    dialog = QDialog(parent or window)
    dialog.setObjectName('visualGuideDialog')
    dialog.setWindowTitle('Bildliche Anleitung · PasswortGenerator')
    dialog.resize(780, 680)
    dialog.setMinimumSize(550, 480)
    layout = QVBoxLayout(dialog)
    heading = QLabel('BILDLICHE ANLEITUNG')
    heading.setObjectName('glassCardTitle')
    layout.addWidget(heading)
    summary = QLabel(
        'Drei echte Ansichten deiner App mit Erklärungen. '
        'Zum Wechseln auf Passwort, Design oder Updates klicken.'
    )
    summary.setWordWrap(True)
    layout.addWidget(summary)

    visual_tabs = QTabWidget(dialog)
    visual_tabs.setObjectName('visualGuideTabs')
    layout.addWidget(visual_tabs, 1)

    active = window.tabs.currentIndex()
    previous_block = window.tabs.blockSignals(True)
    try:
        for index, (tab, title, description) in enumerate(SCREENS):
            window.tabs.setCurrentIndex(index)
            QApplication.processEvents()
            # QWidget.grab() draws the actual page; avoids files or fake mockups.
            screenshot = window.tabs.widget(index).grab()
            if screenshot.isNull():
                raise RuntimeError('Die Bildschirmansicht konnte nicht aufgenommen werden.')
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.setSpacing(10)
            title_label = QLabel(title)
            title_label.setObjectName('visualGuideTitle')
            page_layout.addWidget(title_label)
            explanation = QLabel(description)
            explanation.setObjectName('visualGuideDescription')
            explanation.setWordWrap(True)
            page_layout.addWidget(explanation)

            image_label = QLabel()
            image_label.setObjectName(f'visualGuideImage{index}')
            image_label.setAccessibleName(f'Bildschirmansicht {title}')
            image_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            image_label.setPixmap(
                screenshot.scaledToWidth(
                    min(680, max(400, screenshot.width())),
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

            image_scroll = QScrollArea(page)
            image_scroll.setObjectName('visualGuideImageScroll')
            image_scroll.setWidgetResizable(True)
            image_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
            image_scroll.setWidget(image_label)
            page_layout.addWidget(image_scroll, 1)
            visual_tabs.addTab(page, tab)
    finally:
        window.tabs.setCurrentIndex(active)
        window.tabs.blockSignals(previous_block)
        QApplication.processEvents()

    close_row = QHBoxLayout()
    close_row.addStretch()
    close_button = QPushButton('Schließen')
    close_button.clicked.connect(dialog.accept)
    close_row.addWidget(close_button)
    layout.addLayout(close_row)
    return dialog
