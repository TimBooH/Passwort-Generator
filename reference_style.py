"""One coherent Ocean Glass stylesheet, with a compact layout of the same design."""
from ocean_checkmark import checkmark_png_path


def reference_stylesheet(compact=False):
    sizes = {'nav': 14 if compact else 18, 'mode': 13 if compact else 18,
             'title': 22 if compact else 27, 'subtitle': 13 if compact else 17,
             'output': 22 if compact else 32, 'label': 13 if compact else 17,
             'panel': 15 if compact else 19, 'cta': 18 if compact else 24}
    css = """
/* Ocean Glass: fixed reference appearance, native Qt widgets. */
QWidget { font-family: "Carlito"; }
QWidget#contentColumn {
    border: 1px solid rgba(86,190,255,190); border-radius: 17px;
    background: rgba(4,19,42,90);
}
QLabel#brandTitle { color: #F7FAFF; font-size: 21px; font-weight: 600; }
QLabel#brandLock { background: transparent; border: none; }
QFrame#topNav {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 rgba(4,24,53,225),stop:1 rgba(4,20,47,242));
    border: 1px solid rgba(58,134,213,145); border-radius: 13px;
}
QPushButton#navButton, QPushButton#infoNavButton {
    color: #E4EDFA; background: transparent; border: 1px solid transparent;
    border-radius: 11px; font-size: @nav@px; font-weight: 400; padding: 7px 12px;
}
QPushButton#navButton:hover, QPushButton#infoNavButton:hover {
    background: rgba(26,100,181,120); border: 1px solid rgba(82,200,255,150);
}
QPushButton#navButton:checked, QPushButton#infoNavButton:checked {
    color: white; border: 1px solid #3DDCFF;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #18B7F7,stop:.5 #007EFF,stop:1 #0064F4);
}
QPushButton#modeButton {
    color: #E3EDFC; font-size: @mode@px; font-weight: 400;
    background: rgba(5,26,58,190); border: 1px solid rgba(56,130,204,150);
    border-radius: 11px; padding: 5px 12px;
}
QPushButton#modeButton:checked {
    color: white; border: 1px solid #2CDAFF;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #00BBF5,stop:1 #0060FC);
}
QLabel#oceanHeroIcon {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 rgba(61,112,171,210),stop:1 rgba(18,51,97,205));
    border: 1px solid rgba(128,190,245,145); border-radius: 12px;
}
QLabel#oceanPageTitle { color: #F7FAFF; font-size: @title@px; font-weight: 700; }
QLabel#oceanPageSubtitle { color: #BDCEE5; font-size: @subtitle@px; font-weight: 400; }
QLabel#oceanOutputCaption, QLabel#oceanStrengthCaption {
    color: #F4F7FF; font-size: @label@px; font-weight: 600;
}
QLabel#oceanStrengthValue { color: #17F0AB; font-size: @label@px; font-weight: 600; }
QLineEdit#passwordOutput {
    color: #F4FAFF; font-family: "DejaVu Sans Mono";
    font-size: @output@px; font-weight: 400; letter-spacing: 2px;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 rgba(5,23,47,225),stop:1 rgba(15,49,91,210));
    border: 1px solid rgba(98,162,225,165); border-radius: 12px; padding: 7px 18px;
    selection-background-color: #126AE5;
}
QPushButton#squareAction {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 rgba(27,72,125,210),stop:1 rgba(12,44,86,210));
    border: 1px solid rgba(81,151,223,165); border-radius: 11px;
    min-width: 40px; padding: 5px 7px;
}
QPushButton#squareAction:hover { background: rgba(22,102,181,220); border-color: #6ADFFF; }
QFrame#oceanOptionPanel, QFrame#oceanLengthPanel {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 rgba(7,27,53,200),stop:1 rgba(7,32,63,170));
    border: 1px solid rgba(55,130,203,175); border-radius: 13px;
}
QLabel#oceanPanelHeading { color: #F7F9FF; font-size: @panel@px; font-weight: 600; }
QWidget#passwordPage QCheckBox { color: #E8F0FF; font-size: @label@px; font-weight: 400; spacing: 12px; }
QWidget#passwordPage QCheckBox::indicator { width: 24px; height: 24px; border: 1px solid #5589B9; border-radius: 5px; background: rgba(8,31,59,180); }
QWidget#passwordPage QCheckBox::indicator:checked { image: url("@check@"); border: none; background: transparent; }
QSpinBox { color: #F5F8FF; font-size: 24px; font-weight: 400;
    background: rgba(10,36,75,175); border: 1px solid rgba(73,142,213,150); border-radius: 10px; padding: 4px 6px; }
QSlider#oceanLengthSlider::groove:horizontal { height: 10px; background: #315D91; border-radius: 5px; }
QSlider#oceanLengthSlider::sub-page:horizontal { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00BFEF,stop:1 #0076FE); border-radius: 5px; }
QSlider#oceanLengthSlider::handle:horizontal { width: 23px; margin: -9px 0; background: #EBFBFF; border: 3px solid #43BFFF; border-radius: 14px; }
QProgressBar#strengthBar { background: #265887; border: none; border-radius: 6px; min-height: 12px; max-height: 12px; }
QProgressBar#strengthBar::chunk { background: #16DFA5; border-radius: 6px; }
QPushButton#generatePasswordButton {
    color: white; font-size: @cta@px; font-weight: 700; border: 1px solid #47E9FF; border-radius: 13px;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #008FFF,stop:.5 #006CFF,stop:1 #17DDEB);
}
QPushButton#generatePasswordButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #229EFF,stop:1 #48F1F1); border-color: #B5F8FF;
}
QPushButton#generatePasswordButton:pressed { background: #075BCD; }
QPushButton#generatePasswordButton:focus { border: 2px solid #B5F8FF; }
QPushButton#bottomAction, QPushButton#analysisButton, QPushButton#advancedPasswordRulesButton {
    font-size: 13px; font-weight: 400;
}
"""
    for name, value in sizes.items():
        css = css.replace('@' + name + '@', str(value))
    css = css.replace('@check@', checkmark_png_path() or '')
    if compact:
        css += """
QWidget#passwordPage QCheckBox::indicator { width: 19px; height: 19px; }
QSpinBox { font-size: 19px; }
"""
    return css

