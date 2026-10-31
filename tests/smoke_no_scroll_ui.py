"""No whole-page scrolling or controls below final CTA in compact reference."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QScrollArea
from main import PasswordWindow

app=QApplication([])
app.setStyle('Fusion')
w=PasswordWindow(auto_check=False)
w.show()
app.processEvents()
assert w.centralWidget() is w.background_surface
assert w.findChildren(QScrollArea)==[w.batch_scroll]
assert not w.batch_scroll.isVisible()
assert not hasattr(w,'scroll_area')
assert 'QPushButton#generatePasswordButton' in w.styleSheet()
assert 'QPushButton#primaryButton' in w.styleSheet()
assert w.settings_button.isVisible()
assert w.history_button.isVisible()
assert not w.info_nav_button.isVisible()
assert not w.nav_buttons[2].isVisible()
assert not w.status.isVisible()
for width,height in ((730,760),(610,750),(900,800)):
    w.resize(width,height)
    for _ in range(3): app.processEvents()
    assert w.generate_button.isVisible()
    assert w.generate_button.width()>230
    assert w.generate_button.height()>=55
    for control in (w.generate_button,w.history_button,w.length_slider,w.show_button,w.copy_top_button):
        xy=control.mapTo(w,QPoint(0,0))
        assert xy.x()>=0 and xy.y()>=0,(width,height,control.objectName(),xy)
        assert xy.x()+control.width() <= w.width()+4,(width,height,control.objectName())
        assert xy.y()+control.height() <= w.height()+4,(width,height,control.objectName())
w.show_settings_dialog('update')
app.processEvents()
assert w._settings_views.currentIndex()==3
assert w.changelog_card.isVisible()
assert w.check_button.isVisible()
entries=[{'tag':f'v0.{i:02d}.0','date':'2026-10-18','body':f'- Änderung Nummer {i}'}
         for i in range(50,0,-1)]
w._history_releases={x['tag']:x for x in entries}
w.release_combo.blockSignals(True)
w.release_combo.clear()
for x in entries:
    w.release_combo.addItem(x['tag'],x['tag'])
w.release_combo.blockSignals(False)
w.release_combo.setEnabled(True)
w.release_combo.setCurrentIndex(49)
app.processEvents()
assert w.release_combo.count()==50
assert 'Änderung Nummer 1' in w.changelog_view.toPlainText()
w._settings_dialog.close()
app.processEvents()
assert w.tabs.count()==4
w.close()
print('No page scrolling or footer below Generate; update lives in Settings OK')
