"""First-launch on-screen introduction with highlighted controls and drawn arrows.

Works with ordinary framed Qt windows on Windows and Linux. The overlay never
captures a password, exports screenshots, or generates a password itself.
"""

import math

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QApplication, QPushButton, QWidget


# (page, target attribute on PasswordWindow, heading, explanation)
TOUR_STEPS = (
    (0, 'password_mode_button', 'Passwort und Passphrase',
     'Hier wählst du zwischen einem zufälligen Passwort und einer Passphrase '
     'aus sicheren Wörtern.'),
    (0, 'length_slider', 'Länge bestimmen',
     'Mit dem Regler legst du die Länge fest. Bei Passphrase wählst du '
     'stattdessen die Anzahl der Wörter.'),
    (0, 'passphrase_mode_button', 'Passphrase-Extras',
     'Im Passphrase-Modus kannst du Trennzeichen auswählen und auf Wunsch '
     'eine zufällige zweistellige Zahl anhängen.'),
    (0, 'generate_button', 'Generieren und kopieren',
     'Erstelle dein Passwort mit dieser Taste. Über das Kopiersymbol '
     'neben dem Ergebnis kopierst du es in die Zwischenablage.'),
    (1, 'scheme_combo', 'Design und Glass',
     'Hier findest du die Farbschemas. Das neue Schema „Glass“ lässt '
     'den Hintergrund durch die Glaskacheln durchscheinen.'),
    (0, 'nav_buttons', 'Update-Bereich',
     'Oben rechts gelangst du zu Updates. Beim Start sucht die App '
     'automatisch nach neuen Versionen und meldet sie per Popup.'),
    (0, 'info_nav_button', 'Info und grafische Erklärung',
     'Über Info kannst du die bebilderte Erklärung später erneut '
     'öffnen. Fertig – viel Spaß mit dem PasswortGenerator!'),
)


class FirstRunTour(QWidget):
    """A dimmed see-through overlay with a highlighted target and arrow."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setObjectName('firstRunTour')
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.original_page = window.tabs.currentIndex()
        self.step_index = 0
        self.finished = False

        self.back_button = QPushButton('← Zurück', self)
        self.back_button.setObjectName('tourBack')
        self.back_button.clicked.connect(self.previous_step)
        self.skip_button = QPushButton('Überspringen', self)
        self.skip_button.setObjectName('tourSkip')
        self.skip_button.clicked.connect(self.finish)
        self.next_button = QPushButton('Weiter →', self)
        self.next_button.setObjectName('tourNext')
        self.next_button.clicked.connect(self.next_step)
        self.setStyleSheet('''
            QPushButton {
                background: #243C58; color: #F4FAFF;
                border: 1px solid #77CBF5; border-radius: 9px;
                font-weight: bold; padding: 5px 9px; min-height: 24px;
            }
            QPushButton:hover { background: #375F82; }
            QPushButton#tourNext { background: #1769AA; }
        ''')
        self.setGeometry(window.rect())
        self.show()
        self.raise_()
        self.go_to_step(0)

    def target_widget(self):
        page, name, _title, _description = TOUR_STEPS[self.step_index]
        if name == 'nav_buttons':
            return self.window.nav_buttons[2]
        return getattr(self.window, name)

    def go_to_step(self, index):
        if self.finished:
            return
        self.step_index = max(0, min(index, len(TOUR_STEPS) - 1))
        page = TOUR_STEPS[self.step_index][0]
        if self.window.tabs.currentIndex() != page:
            self.window.tabs.setCurrentIndex(page)
        self.window.scroll_area.verticalScrollBar().setValue(0)
        QApplication.processEvents()
        self.back_button.setEnabled(self.step_index > 0)
        self.next_button.setText(
            'Fertig ✓' if self.step_index == len(TOUR_STEPS) - 1
            else 'Weiter →'
        )
        self.resize(self.window.size())
        self._position_buttons()
        self.raise_()
        self.update()

    def previous_step(self):
        self.go_to_step(self.step_index - 1)

    def next_step(self):
        if self.step_index + 1 >= len(TOUR_STEPS):
            self.finish()
        else:
            self.go_to_step(self.step_index + 1)

    def finish(self):
        if self.finished:
            return
        self.finished = True
        # Set the setting only after explicit completion or skipping.
        self.window.settings.setValue('first_run_tour_completed', True)
        self.window.tabs.setCurrentIndex(self.original_page)
        self.hide()
        self.window._first_run_tour = None
        self.deleteLater()
        self.window.flush_pending_update_popup()

    def _highlight_rect(self):
        target = self.target_widget()
        top_left = target.mapTo(self, QPoint(0, 0))
        target_rect = QRect(top_left, target.size()).adjusted(-5, -5, 5, 5)
        return target_rect.intersected(self.rect().adjusted(6, 6, -6, -6))

    def _card_rect(self):
        width = min(485, max(320, self.width() - 22))
        x = max(11, (self.width() - width) // 2)
        h = 160
        focus = self._highlight_rect()
        if focus.center().y() < self.height() // 2:
            y = max(12, self.height() - h - 18)
        else:
            y = 22
        return QRect(x, y, width, h)

    def _position_buttons(self):
        card = self._card_rect()
        y = card.bottom() - 40
        self.back_button.setGeometry(card.x() + 16, y, 94, 30)
        self.skip_button.setGeometry(card.x() + 119, y, 112, 30)
        self.next_button.setGeometry(card.right() - 117, y, 101, 30)
        for button in (self.back_button, self.skip_button, self.next_button):
            button.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_buttons()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.finish()
            event.accept()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter,
                              Qt.Key.Key_Right):
            self.next_step()
            event.accept()
        elif event.key() == Qt.Key.Key_Left:
            self.previous_step()
            event.accept()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        focus = self._highlight_rect()
        w, h = self.width(), self.height()
        # Four simple bands leave a genuinely transparent hole over the
        # selected control. This is lighter than rasterising a full window.
        shadow = QColor(3, 11, 24, 188)
        painter.fillRect(QRect(0, 0, w, max(0, focus.top())), shadow)
        painter.fillRect(QRect(0, focus.bottom() + 1, w,
                               max(0, h - focus.bottom() - 1)), shadow)
        painter.fillRect(QRect(0, focus.top(), max(0, focus.left()),
                               focus.height()), shadow)
        painter.fillRect(QRect(focus.right() + 1, focus.top(),
                               max(0, w - focus.right() - 1), focus.height()),
                         shadow)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor('#75E6FA'), 3))
        painter.drawRoundedRect(QRectF(focus), 9, 9)

        card = self._card_rect()
        painter.setPen(QPen(QColor('#6AD6F9'), 2))
        painter.setBrush(QColor(10, 25, 45, 246))
        painter.drawRoundedRect(QRectF(card), 15, 15)
        page, _name, title, description = TOUR_STEPS[self.step_index]
        painter.setPen(QColor('#87E2FF'))
        painter.setFont(QFont('Sans Serif', 10, QFont.Weight.Bold))
        painter.drawText(
            QRect(card.x() + 18, card.y() + 11, card.width() - 36, 20),
            Qt.AlignmentFlag.AlignLeft,
            f'Schritt {self.step_index + 1}/{len(TOUR_STEPS)}  ·  {title}',
        )
        painter.setPen(QColor('#F6FAFF'))
        painter.setFont(QFont('Sans Serif', 10))
        painter.drawText(
            QRect(card.x() + 18, card.y() + 39, card.width() - 36, 74),
            int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
                | Qt.TextFlag.TextWordWrap),
            description,
        )
        # Draw a directional arrow between the card and the real widget.
        center = QPointF(focus.center())
        origin = QPointF(card.center().x(),
                         card.top() if card.center().y() > center.y()
                         else card.bottom())
        vx = center.x() - origin.x()
        vy = center.y() - origin.y()
        distance = max(1.0, math.hypot(vx, vy))
        ux, uy = vx / distance, vy / distance
        tip = QPointF(center.x() - ux * 9, center.y() - uy * 9)
        base = QPointF(tip.x() - ux * 14, tip.y() - uy * 14)
        painter.setPen(QPen(QColor('#FFE9A7'), 3))
        painter.drawLine(origin, base)
        painter.setBrush(QColor('#FFE9A7'))
        painter.drawPolygon(QPolygonF([
            tip,
            QPointF(base.x() - uy * 7, base.y() + ux * 7),
            QPointF(base.x() + uy * 7, base.y() - ux * 7),
        ]))
        painter.end()
