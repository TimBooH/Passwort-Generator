"""Interactive first-start tour with arrows aimed at actual visible controls.

An overlay lives on the main window, no screenshot or modal is created.
Coordinates are converted via the native global mapping and checked against
each real widget's rectangle. Passphrase-only widgets are shown when needed.
"""

from localization import translate
from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QApplication, QPushButton, QWidget


TOUR_STEPS = (
    (0, 'password_mode_button', 'Passwort oder Passphrase',
     'Hier wählst du, ob du ein Passwort oder eine Passphrase erzeugen möchtest.'),
    (0, 'length_slider', 'Länge wählen',
     'Mit diesem Regler bestimmst du die Zeichenlänge beziehungsweise die Wörterzahl.'),
    (0, 'phrase_two_digits', 'Zweistellige Zufallszahl',
     'Diese Option hängt an eine Passphrase eine sichere Zufallszahl von 10 bis 99 an.'),
    (0, 'phrase_separator', 'Trennzeichen',
     'Mit diesem Dropdown wählst du das Zeichen zwischen Wörtern und Zufallszahl.'),
    (0, 'generate_button', 'Neues Passwort generieren',
     'Klicke hier, um ein Passwort zu erzeugen. Das Symbol am Ergebnis kopiert es.'),
    (0, 'history_button', 'Sitzungsverlauf',
     'Hier öffnest du den aufklappbaren Verlauf deiner generierten Passwörter.'),
    (0, 'settings_button', 'Einstellungen & Update',
     'Hier findest du Sprache, Sicherheit, Profile und den Update-Bereich.'),
    (0, 'settings_button', 'Info',
     'Der Bereich Info liegt innerhalb der Einstellungen. Dort kannst du die Tour erneut starten.'),
)


class FirstRunTour(QWidget):
    """Translucent spotlight and pointed arrow to the selected Qt widget."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setObjectName('firstRunTour')
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.original_page = window.tabs.currentIndex()
        self.original_phrase_mode = window._phrase_mode
        self._original_output = window.output.text()
        self._original_length = window.length.value()
        self._original_strength = window.strength_label.text()
        self._original_strength_score = window.strength_bar.value()
        self._original_status = window.status.text()
        self.step_index = 0
        self.finished = False

        self.back_button = QPushButton(translate('← Zurück', window.language), self)
        self.back_button.setObjectName('tourBack')
        self.back_button.clicked.connect(self.previous_step)
        self.skip_button = QPushButton(translate('Überspringen', window.language), self)
        self.skip_button.setObjectName('tourSkip')
        self.skip_button.clicked.connect(self.finish)
        self.next_button = QPushButton(translate('Weiter →', window.language), self)
        self.next_button.setObjectName('tourNext')
        self.next_button.clicked.connect(self.next_step)
        self.setStyleSheet('''
            QPushButton {
                background: #243C58; color: #F4FAFF;
                border: 1px solid #77CBF5; border-radius: 9px;
                font-weight: bold; padding: 4px 9px; min-height: 23px;
            }
            QPushButton:hover { background: #375F82; }
            QPushButton#tourNext { background: #1769AA; }
        ''')
        self.setGeometry(window.rect())
        self.show()
        self.raise_()
        self.go_to_step(0)

    def target_widget(self):
        _page, name, _title, _explanation = TOUR_STEPS[self.step_index]
        return getattr(self.window, name)

    def go_to_step(self, index):
        if self.finished:
            return
        self.step_index = max(0, min(index, len(TOUR_STEPS) - 1))
        page, target_name, _title, _explanation = TOUR_STEPS[self.step_index]
        if self.window.tabs.currentIndex() != page:
            self.window.tabs.setCurrentIndex(page)
        if target_name in ('phrase_two_digits', 'phrase_separator'):
            if not self.window._phrase_mode:
                self.window.switch_mode(True)
        elif page == 0 and target_name not in ('settings_button', 'history_button'):
            if self.window._phrase_mode:
                self.window.switch_mode(False)
        QApplication.processEvents()
        self.resize(self.window.size())
        focus = self._highlight_rect()
        if focus.isEmpty() or not self.target_widget().isVisible():
            raise AssertionError(
                f'Tour-Ziel ist nicht sichtbar: {target_name}, Seite {page}'
            )
        self.back_button.setEnabled(self.step_index > 0)
        self.next_button.setText(
            translate('Fertig ✓', self.window.language)
            if self.step_index == len(TOUR_STEPS) - 1
            else translate('Weiter →', self.window.language)
        )
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
        if self.window._phrase_mode != self.original_phrase_mode:
            self.window.switch_mode(self.original_phrase_mode)
        self.window.length.setValue(self._original_length)
        self.window.output.setText(self._original_output)
        self.window.strength_label.setText(self._original_strength)
        self.window.strength_bar.setValue(self._original_strength_score)
        self.window.status.setText(self._original_status)
        self.window.settings.setValue('first_run_tour_completed', True)
        self.window.tabs.setCurrentIndex(self.original_page)
        self.hide()
        self.window._first_run_tour = None
        self.deleteLater()
        self.window.flush_pending_update_popup()

    def _highlight_rect(self):
        target = self.target_widget()
        origin = self.mapFromGlobal(target.mapToGlobal(QPoint(0, 0)))
        rect = QRect(origin, target.size()).adjusted(-5, -5, 5, 5)
        return rect.intersected(self.rect().adjusted(5, 5, -5, -5))

    def _card_rect(self):
        width = min(485, max(290, self.width() - 22))
        x = max(11, (self.width() - width) // 2)
        height = 155
        focus = self._highlight_rect()
        upper = focus.top() - 14 - height
        lower = self.height() - focus.bottom() - 14 - height
        if lower >= upper:
            y = max(12, self.height() - height - 14)
        else:
            y = 14
        return QRect(x, y, width, height)

    def _arrow_line(self):
        """Arrow tip is on the actual highlight BORDER, never a guessed center."""
        focus = self._highlight_rect()
        card = self._card_rect()
        if card.bottom() < focus.top():
            point_y = focus.top() - 3
            base_y = card.bottom()
        elif card.top() > focus.bottom():
            point_y = focus.bottom() + 3
            base_y = card.top()
        else:
            # A very small window: connect sideways from the nearest edge.
            focus_on_right = focus.center().x() > card.center().x()
            if focus_on_right:
                return (
                    QPointF(card.right(), card.center().y()),
                    QPointF(focus.left() - 3, focus.center().y())
                )
            return (
                QPointF(card.left(), card.center().y()),
                QPointF(focus.right() + 3, focus.center().y())
            )
        x = max(focus.left() + 7,
                min(card.center().x(), focus.right() - 7))
        return QPointF(card.center().x(), base_y), QPointF(x, point_y)

    def _position_buttons(self):
        card = self._card_rect()
        y = card.bottom() - 37
        self.back_button.setGeometry(card.x() + 13, y, 93, 28)
        self.skip_button.setGeometry(card.x() + 111, y, 108, 28)
        self.next_button.setGeometry(card.right() - 108, y, 96, 28)
        for button in (self.back_button, self.skip_button, self.next_button):
            button.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_buttons()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.finish()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Right):
            self.next_step()
        elif event.key() == Qt.Key.Key_Left:
            self.previous_step()
        else:
            return super().keyPressEvent(event)
        event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        focus = self._highlight_rect()
        w, h = self.width(), self.height()
        shadow = QColor(3, 11, 24, 186)
        painter.fillRect(QRect(0, 0, w, max(0, focus.top())), shadow)
        painter.fillRect(QRect(
            0, focus.bottom() + 1, w, max(0, h - focus.bottom() - 1)
        ), shadow)
        painter.fillRect(QRect(
            0, focus.top(), max(0, focus.left()), focus.height()
        ), shadow)
        painter.fillRect(QRect(
            focus.right() + 1, focus.top(),
            max(0, w - focus.right() - 1), focus.height()
        ), shadow)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor('#75E6FA'), 3))
        painter.drawRoundedRect(QRectF(focus), 8, 8)
        card = self._card_rect()
        painter.setPen(QPen(QColor('#6AD6F9'), 2))
        painter.setBrush(QColor(10, 25, 45, 247))
        painter.drawRoundedRect(QRectF(card), 13, 13)
        _page, _name, title, description = TOUR_STEPS[self.step_index]
        painter.setPen(QColor('#87E2FF'))
        painter.setFont(QFont('Sans Serif', 10, QFont.Weight.Bold))
        painter.drawText(
            QRect(card.x() + 16, card.y() + 11, card.width() - 32, 23),
            Qt.AlignmentFlag.AlignLeft,
            f"{('Step' if self.window.language == 'en' else 'Schritt')} "
            f"{self.step_index + 1}/{len(TOUR_STEPS)} · "
            f"{translate(title, self.window.language)}",
        )
        painter.setPen(QColor('#F6FAFF'))
        painter.setFont(QFont('Sans Serif', 10))
        painter.drawText(
            QRect(card.x() + 16, card.y() + 40, card.width() - 32, 73),
            int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
                | Qt.TextFlag.TextWordWrap),
            translate(description, self.window.language),
        )
        start, tip = self._arrow_line()
        vx, vy = tip.x() - start.x(), tip.y() - start.y()
        distance = max(1.0, (vx * vx + vy * vy) ** .5)
        ux, uy = vx / distance, vy / distance
        stem = QPointF(tip.x() - ux * 14, tip.y() - uy * 14)
        painter.setPen(QPen(QColor('#FFE9A7'), 3))
        painter.drawLine(start, stem)
        painter.setBrush(QColor('#FFE9A7'))
        painter.drawPolygon(QPolygonF([
            tip,
            QPointF(stem.x() - uy * 7, stem.y() + ux * 7),
            QPointF(stem.x() + uy * 7, stem.y() - ux * 7),
        ]))
        painter.end()
