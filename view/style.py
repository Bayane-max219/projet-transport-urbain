"""Thème TRANSPORT : sombre (anthracite) avec accent ambre, onglets en haut."""

COULEURS = {"fond": "#16181d", "panneau": "#20242c", "bordure": "#343b48", "texte": "#e7e5e4",
            "discret": "#9aa3b2", "accent": "#f59e0b", "danger": "#ef4444", "ok": "#22c55e", "bleu": "#38bdf8"}

FEUILLE = """
* { font-family: 'Ubuntu', 'Noto Sans', sans-serif; font-size: 13px; color: #e7e5e4; }
QMainWindow, QFrame#page, QDialog, QMessageBox { background: #16181d; }
QTabWidget::pane { border: none; border-top: 2px solid #343b48; }
QTabBar::tab { background: #16181d; color: #9aa3b2; padding: 12px 20px; border: none; border-bottom: 3px solid transparent; font-weight: bold; }
QTabBar::tab:selected { color: #f59e0b; border-bottom: 3px solid #f59e0b; }
QTabBar::tab:hover { color: #fbbf24; }
QGroupBox { background: #20242c; border: 1px solid #343b48; border-radius: 4px; margin-top: 16px; padding: 14px 10px 8px 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #f59e0b; font-weight: bold; text-transform: uppercase; }
QPushButton { background: #f59e0b; color: #1a1300; border: none; border-radius: 3px; padding: 7px 14px; font-weight: bold; }
QPushButton:hover { background: #fbbf24; }
QPushButton[secondaire="true"] { background: #2c3240; color: #e7e5e4; border: 1px solid #454e5f; }
QPushButton[danger="true"] { background: #ef4444; color: white; }
QLineEdit, QComboBox, QSpinBox, QDateTimeEdit, QDateEdit, QTextBrowser {
    background: #101216; border: 1px solid #454e5f; border-radius: 3px; padding: 4px 6px; selection-background-color: #f59e0b; selection-color: #111; }
QComboBox QAbstractItemView { background: #20242c; selection-background-color: #f59e0b; selection-color: #111; }
QCalendarWidget QWidget { background: #20242c; color: #e7e5e4; }
QTableWidget { background: #1b1e25; alternate-background-color: #20242c; border: 1px solid #343b48; gridline-color: #2a303b; selection-background-color: #8a5a07; selection-color: white; }
QHeaderView::section { background: #2c3240; color: #f59e0b; border: none; border-right: 1px solid #343b48; padding: 7px; font-weight: bold; }
QScrollBar:vertical { background: #16181d; width: 10px; } QScrollBar::handle:vertical { background: #454e5f; border-radius: 5px; }
QStatusBar { color: #9aa3b2; }
#carte { background: #20242c; border: 1px solid #343b48; border-left: 4px solid #f59e0b; border-radius: 3px; }
#carteValeur { font-size: 22px; font-weight: bold; color: #f59e0b; }
#carteTitre { color: #9aa3b2; font-size: 11px; }
#titrePage { font-size: 18px; font-weight: bold; color: #e7e5e4; }
#bandeau { background: #38bdf8; color: #06212e; padding: 6px 10px; font-weight: bold; border-radius: 3px; }
"""
