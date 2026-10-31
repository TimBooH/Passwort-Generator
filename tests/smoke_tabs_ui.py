"""Compact top navigation, mode switching, history and settings modal smoke."""
import os
from unittest import mock
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QTabWidget
from main import PasswordWindow

app=QApplication([])
app.setStyle('Fusion')
window=PasswordWindow(auto_check=False)
window.resize(730,760)
window.show()
app.processEvents()
assert window.tabs.count()==4
assert window.password_mode_button.isChecked()
assert not window.passphrase_mode_button.isChecked()
assert window.history_button.isVisible()
assert window.settings_button.isVisible()
assert window.history_button.mapTo(window,QPoint(0,0)).y() < window.password_output_card.mapTo(window,QPoint(0,0)).y()
window.length.setValue(44)
window.generate()
value=window.output.text()
assert len(value)==44
assert window._history[-1] == ('Passwort',value)
window.show_button.setChecked(False)
assert window.output.echoMode()==QLineEdit.EchoMode.Password
window.show_button.setChecked(True)
assert window.output.echoMode()==QLineEdit.EchoMode.Normal
window.copy()
assert app.clipboard().text()==value

def inspect_history(dialog):
    assert dialog.objectName()=='groupedHistoryDialog'
    assert len(dialog.findChildren(QPushButton,'historyGroupToggle')) == 1
    return QDialog.DialogCode.Rejected
with mock.patch.object(QDialog,'exec',new=inspect_history):
    window.history_button.click()

window.settings_button.click()
app.processEvents()
dialog=window._settings_dialog
assert dialog is not None and dialog.isVisible()
assert window._settings_views.currentIndex()==0
assert window.language_combo.isVisible()
assert window.security_card.isVisible()
window._settings_views.setCurrentIndex(1)
app.processEvents()
assert dialog.findChild(QPushButton,'settingsSectionButton') is not None
assert window._settings_views.currentIndex()==1
window._settings_views.setCurrentIndex(3)
app.processEvents()
assert window.check_button.isVisible()
assert window.channel_combo.isVisible()
window.show_info()
app.processEvents()
assert window._settings_views.currentIndex()==4
assert window.info_credit.text()=='Made by Jon Bovi'
window.visual_guide_button.click()
app.processEvents()
assert window.info_detail_stack.findChild(QTabWidget,'visualGuideTabs').count()==3
dialog.close()
app.processEvents()
assert window._settings_dialog is None
assert window.tabs.count()==4

window.passphrase_mode_button.click()
app.processEvents()
assert window._phrase_mode
assert window.length.value()==6
assert window.phrase_options_widget.isVisible()
assert not window.options_widget.isVisible()
window.generate()
phrase=window.output.text()
assert len(phrase.split('-'))==6
window.password_mode_button.click()
app.processEvents()
assert not window._phrase_mode
assert window.options_widget.isVisible()
assert window.length.maximum()==128
for width in (600,730,1000):
    window.resize(width,760)
    app.processEvents()
    assert window.generate_button.isVisible()
    assert window.history_button.isVisible()
    assert window.ocean_options_panel.isVisible()
window.close()
app.processEvents()
print('Compact header navigation, separated settings, grouped history and modes OK')
