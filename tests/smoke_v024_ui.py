"""v0.24.0: batch generation, groups, ambiguity filter and clipboard countdown."""
import os
import tempfile
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ['XDG_CONFIG_HOME'] = tempfile.mkdtemp(prefix='pw-v024-')
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QLineEdit
from main import PasswordWindow
from password_core import SIMILAR_CHARS

QSettings.setDefaultFormat(QSettings.Format.IniFormat)
app = QApplication([])
app.setStyle('Fusion')
window = PasswordWindow(auto_check=False)
window.resize(1100, 790)
window.show()
app.processEvents()
assert window.batch_count_combo.currentData() == 1
assert not window.exclude.isChecked()
assert not window.batch_scroll.isVisible()
window.batch_count_combo.setCurrentIndex(window.batch_count_combo.findData(5))
assert window.settings.value('password/batch_count',type=int) == 5
window.exclude.setChecked(True)
window.generate()
assert len(window._current_batch) == 5
assert len(set(window._current_batch)) == 5
assert all(not (set(p) & set(SIMILAR_CHARS)) for p in window._current_batch)
assert window.batch_scroll.isVisible()
assert not window.single_output_widget.isVisible()
assert len(window._batch_edits) == 5
assert all(e.echoMode() == QLineEdit.EchoMode.Normal for e in window._batch_edits)
old = list(window._current_batch)
window.generate()
assert len(window._history_groups) == 2
assert len(window._history) == 10
assert window._current_batch != old
assert window._history_groups[0]['secrets'] == old
window.batch_count_combo.setCurrentIndex(window.batch_count_combo.findData(20))
assert len(window._current_batch) == 5  # selection itself must not erase
for _ in range(6):
    window.generate()
assert len(window._history) <= 100
assert all(len(g['secrets']) in (5,20) for g in window._history_groups)
assert sum(len(g['secrets']) for g in window._history_groups) == len(window._history)
assert window._history_groups[-1]['secrets'] == window._current_batch
assert len(window._batch_edits) == 20

# The dialog has independently expandable groups and a countdown label.
def inspect_history(dialog):
    assert dialog.objectName() == 'groupedHistoryDialog'
    toggles = dialog.findChildren(__import__('PySide6.QtWidgets',fromlist=['QPushButton']).QPushButton, 'historyGroupToggle')
    assert len(toggles) == len(window._history_groups)
    assert len(dialog.findChildren(QLineEdit,'historyPasswordText')) == len(window._history)
    assert toggles[0].text().startswith('▾')
    assert toggles[1].text().startswith('▸')
    return QDialog.DialogCode.Rejected
with mock.patch.object(QDialog,'exec',autospec=True, side_effect=inspect_history):
    window.show_history()

# Countdowns show in the result area and never clear third-party clipboard data.
secret = window._current_batch[0]
window.copy_secret(secret)
assert window.clipboard_timer.isActive()
assert window.clipboard_countdown_label.isVisible()
assert ':' in window.clipboard_countdown_label.text()
assert window.clipboard_countdown_label.text().startswith('Zwischenablage wird geleert in')
app.clipboard().setText('other clipboard data')
window.clear_copied_password()
assert app.clipboard().text() == 'other clipboard data'
assert not window.clipboard_countdown_label.isVisible()
window.copy_secret(secret)
assert window.clipboard_timer.isActive()
window.clear_copied_password()
assert app.clipboard().text() == ''

# Bad constraints must not destroy existing batch or history.
previous_batch = list(window._current_batch)
previous_groups = len(window._history_groups)
window.upper.setChecked(False)
window.lower.setChecked(False)
window.symbols.setChecked(False)
window.digits.setChecked(False)
with mock.patch.object(QMessageBox,'warning'):
    window.generate()
assert window._current_batch == previous_batch
assert len(window._history_groups) == previous_groups
window.digits.setChecked(True)
window.switch_mode(True)
assert not window.batch_count_combo.isVisible()
window.generate()
assert len(window._history_groups[-1]['secrets']) == 1
assert window._history_groups[-1]['kind'] == 'Passphrase'
assert not window.batch_scroll.isVisible()
window.close()
assert not window._history and not window._history_groups and not window._current_batch
print('v0.24.0 secure batch + grouped 100-entry history + 8-char filter + countdown OK')
