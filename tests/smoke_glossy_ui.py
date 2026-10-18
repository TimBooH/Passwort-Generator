"""Minimal visual smoke check on CI's headless Qt environment."""

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication
from main import PasswordWindow

app = QApplication([])
window = PasswordWindow()
window.show()
app.processEvents()
preview = window.grab()
assert not preview.isNull(), 'Qt failed to render the window'
assert preview.width() >= 520 and preview.height() >= 590, 'Unexpected render size'
assert len(window.glass_cards) == 3, 'Expected exactly three glossy glass cards'
assert preview.save('glossy-preview.png'), 'Unable to save GUI preview'
window.close()
app.processEvents()
print('Glossy UI smoke test successful; preview saved.', flush=True)
