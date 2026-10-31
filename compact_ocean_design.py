"""Approved compact Ocean Glass v0.24.0 desktop interface.

The reference has a narrow main window, four top actions, a single result
card, two adjacent option cards, one final blue CTA, and no lower toolbar.
Only the real PySide6 widgets are styled here; no browser/mockup layer.
"""


def compact_ocean_stylesheet():
    return """
    QWidget#contentColumn { background: transparent; }
    QFrame#topNav { background: transparent; border: none; }
    QPushButton#compactNavButton {
        color: #DDEAFF; font-size: 13px; font-weight: 600;
        border: 1px solid #175082; border-radius: 9px;
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
            stop:0 rgba(8,36,71,235), stop:1 rgba(4,23,50,230));
        padding: 5px 7px;
        min-height: 38px;
    }
    QPushButton#compactNavButton:hover {
        border: 1px solid #34BFFF;
        background: rgba(12,65,120,235);
    }
    QPushButton#compactNavButton:checked {
        color: #FFFFFF; font-weight: 700; border: 1px solid #54E7FF;
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
            stop:0 #0798FF, stop:1 #0758E8);
    }
    QFrame#passwordOutputCard {
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 rgba(6,37,76,240), stop:1 rgba(4,21,48,240));
        border: 1px solid #1975B8; border-radius: 15px;
    }
    QLabel#oceanOutputCaption {
        color: #F2F7FF; font-size: 16px; font-weight: 700;
        background: transparent; border: none;
    }
    QLineEdit#passwordOutput {
        color: #EAF6FF; font-family: monospace; font-size: 19px;
        background: rgba(0,15,36,245);
        border: 1px solid #165A96; border-radius: 9px; padding: 3px 12px;
    }
    QPushButton#squareAction {
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 #0D3767, stop:1 #082247);
        border: 1px solid #1889D1;
        border-radius: 9px; padding: 5px 6px; min-width: 38px;
    }
    QPushButton#squareAction:hover, QPushButton#squareAction:checked {
        background: #0770DC; border-color: #57E9FF;
    }
    QPushButton#squareAction:focus { border: 2px solid #56C9FF; }
    QLabel#oceanStrengthCaption {
        color: #C7DFFA; font-size: 12px; background: transparent;
    }
    QLabel#oceanStrengthValue {
        color: #30EFCA; font-size: 13px; font-weight: 700;
        background: transparent;
    }
    QProgressBar#strengthBar {
        background: #173A60; border: none; border-radius: 6px;
        min-height: 10px; max-height: 10px;
    }
    QProgressBar#strengthBar::chunk {
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
            stop:0 #29ED96, stop:0.5 #08E7C5, stop:1 #00B9FF);
        border-radius: 6px;
    }
    QLabel#clipboardCountdownLabel {
        color: #05C7FF; font-weight: 750; font-size: 12px;
        background: rgba(6,32,68,220);
        border: 1px solid #146CA6; border-radius: 8px;
        padding: 7px 9px;
    }
    QFrame#oceanOptionPanel, QFrame#oceanLengthPanel {
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 rgba(6,34,67,245), stop:1 rgba(3,21,47,238));
        border: 1px solid #136EA9; border-radius: 13px;
    }
    QLabel#oceanPanelHeading {
        color: #F5F8FF; font-size: 15px; font-weight: 700;
        background: transparent;
    }
    QWidget#passwordPage QCheckBox {
        color: #DBE9FB; font-size: 12px; font-weight: 450; spacing: 8px;
    }
    QPushButton#batchCountChoice {
        color: #E7F5FF; font-size: 13px;
        border: 1px solid #205887; border-radius: 8px;
        background: rgba(18,48,81,225); padding: 5px 3px;
    }
    QPushButton#batchCountChoice:hover {
        border-color: #55CDFF; background: #174A85;
    }
    QPushButton#batchCountChoice:checked {
        color: #FFFFFF; font-weight: 700; border: 1px solid #6BEEFF;
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 #079EFF,stop:1 #0757DB);
    }
    QPushButton#generatePasswordButton {
        color: #FFFFFF; font-size: 18px; font-weight: 700;
        border: 1px solid #3DF2FF; border-radius: 12px;
        padding: 10px 14px;
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
            stop:0 #008AEF,stop:0.5 #075FF5,stop:1 #068CF6);
    }
    QPushButton#generatePasswordButton:hover {
        border: 2px solid #9CFCFF;
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
            stop:0 #00B8FF,stop:1 #156FFF);
    }
    QPushButton#generatePasswordButton:pressed { background: #0A49BA; }
    QDialog#compactSettingsDialog {
        background: #071A32; color: #E8F4FF;
    }
    QFrame#settingsSidebar {
        background: #082340; border: 1px solid #125A91;
        border-radius: 14px;
    }
    QLabel#settingsSidebarHeading {
        font-size: 18px; font-weight: 750; color: #F4F9FF;
        margin-bottom: 5px;
    }
    QLabel#settingsSectionHeading {
        font-size: 20px; font-weight: 750; color: #F4F9FF;
    }
    QPushButton#settingsSectionButton {
        background: transparent; color: #BED4EC;
        border: 1px solid transparent; border-radius: 8px;
        padding: 9px 12px; text-align: left;
    }
    QPushButton#settingsSectionButton:hover {
        color: white; background: rgba(13,79,133,180);
    }
    QPushButton#settingsSectionButton:checked {
        color: white; background: #056DED; border: 1px solid #4BD7FF;
    }
    QLineEdit#batchPasswordText {
        color: #E8F5FF; font-family: monospace;
        background: #071C38; border: 1px solid #17598C;
        border-radius: 8px; padding: 5px;
    }
    QScrollArea#batchResultsScroll { background: transparent; border: none; }
    """;
