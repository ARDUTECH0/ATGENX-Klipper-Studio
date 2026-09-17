# -*- coding: utf-8 -*-
"""Dark theme."""

STYLE = """
* { font-family: 'Segoe UI', 'Noto Sans Arabic', 'Noto Sans', Tahoma, sans-serif; font-size: 13px; color: #e6edf3; }
QMainWindow, QWidget#root { background: #0d1117; }
QWidget#side { background: #161b22; }
QListWidget#nav { background: #161b22; border: none; padding: 8px 0; outline: 0; }
QListWidget, QTreeWidget { background: #0d1117; border: 1px solid #2b3441; border-radius: 8px; outline: 0; }
QTreeWidget::item, QListWidget::item { padding: 3px; }
QTreeWidget::item:selected, QListWidget::item:selected { background: #1f6feb33; color: #e6edf3; }
QToolButton { background: transparent; border: none; border-radius: 6px; padding: 5px 10px; }
QToolButton:hover { background: #21262d; }
QSplitter::handle { background: transparent; }
QListWidget#nav::item { padding: 11px 16px; border-radius: 8px; margin: 2px 8px; color: #8b949e; }
QListWidget#nav::item:selected { background: #1f6feb33; color: #e6edf3; border: none; }
QListWidget#nav::item:hover { background: #1c2430; }
QLabel#brand { font-size: 18px; font-weight: 700; padding: 0 4px; }
QPushButton#card { background: #161b22; border: 1px solid #2b3441; border-radius: 12px; padding: 0; text-align: left; }
QPushButton#card:hover { border-color: #3b8eea; background: #1a2230; }
QLabel#sub { color: #8b949e; padding: 2px 18px 12px; font-size: 11px; }
QLabel#title { font-size: 20px; font-weight: 600; padding: 4px 0; }
QLabel#hint { color: #8b949e; }
QLabel#card { background: #0d1117; border: 1px solid #2b3441; border-radius: 8px; padding: 10px; }
QGroupBox { background: #161b22; border: 1px solid #2b3441; border-radius: 10px; margin-top: 14px; padding: 14px 12px 10px; }
QGroupBox::title { subcontrol-origin: margin; padding: 0 8px; color: #58a6ff; font-weight: 600; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background: #0d1117; border: 1px solid #2b3441; border-radius: 6px; padding: 5px 8px; min-height: 22px; }
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: #58a6ff; }
QComboBox QAbstractItemView { background: #161b22; selection-background-color: #1f6feb55; }
QPushButton { background: #21262d; border: 1px solid #30363d; border-radius: 7px; padding: 7px 16px; }
QPushButton:hover { border-color: #58a6ff; }
QPushButton#primary { background: #238636; border-color: #2ea043; font-weight: 600; }
QPushButton#primary:hover { background: #2ea043; }
QPushButton#danger { background: #3d1418; border-color: #f85149; color: #ffa198; }
QPushButton:disabled { color: #6e7681; border-color: #21262d; }
QPlainTextEdit { background: #0d1117; border: 1px solid #2b3441; border-radius: 8px; font-family: Consolas, 'Cascadia Mono', 'DejaVu Sans Mono', monospace; font-size: 12px; }
QTabWidget::pane { border: 1px solid #2b3441; border-radius: 8px; top: -1px; }
QTabBar::tab { background: #161b22; padding: 7px 16px; border: 1px solid #2b3441; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; margin: 0 1px; color: #8b949e; }
QTabBar::tab:selected { color: #e6edf3; background: #1c2430; }
QTableWidget { background: #0d1117; gridline-color: #2b3441; border: 1px solid #2b3441; border-radius: 8px; }
QHeaderView::section { background: #161b22; border: none; padding: 6px; color: #8b949e; }
QCheckBox::indicator { width: 16px; height: 16px; }
QScrollArea { border: none; background: #0d1117; }
QWidget#page { background: #0d1117; }
QToolBar { background: #161b22; border: none; border-bottom: 1px solid #2b3441; spacing: 6px; padding: 4px; }
QStatusBar { background: #161b22; color: #8b949e; }
a { color: #58a6ff; }
QFrame#helpPanel { background: #11161f; border-left: 1px solid #2b3441; }
QWidget#helpBody { background: #11161f; }
QLabel#helpCaption { color: #6e7681; font-size: 11px; font-weight: 600; letter-spacing: 1px; }
QLabel#helpTitle { font-size: 15px; font-weight: 600; color: #e6edf3; }
QLabel#helpText { color: #b7c3d1; font-size: 13px; line-height: 150%; }
QLabel#helpCfg { background: #0d1117; border: 1px solid #2b3441; border-radius: 6px; padding: 6px 8px; color: #d2a8ff; font-family: Consolas, 'Cascadia Mono', monospace; font-size: 12px; }
QFrame#helpLine { background: #2b3441; }
QFrame#featureCard { background: #161b22; border: 1px solid #2b3441; border-radius: 12px; }
QFrame#featureCard:hover { border-color: #3b8eea; }
QFrame#featureCard[on="true"] { border-color: #2ea04388; background: #13201a; }
QFrame#featureCard QLabel { background: transparent; }
QLabel#featureIcon { font-size: 22px; }
QLabel#featureTitle { font-size: 14px; font-weight: 600; }
QLabel#featureBadge { color: #8b949e; font-size: 11px; }
QLabel#sectionHead { font-size: 15px; font-weight: 600; color: #e6edf3; padding: 6px 0 2px; }
QLabel#subHead { color: #58a6ff; font-weight: 600; padding: 4px 0 0; }
QLabel#mono { font-family: Consolas, 'Cascadia Mono', monospace; color: #d2a8ff; }
QFrame#listBox { background: #161b22; border: 1px solid #2b3441; border-radius: 10px; }
QFrame#listRow { border-bottom: 1px solid #21262d; }
QFrame#listRow:hover { background: #1a2230; }
QPushButton#link { background: transparent; border: none; color: #58a6ff; padding: 2px 0; text-align: left; }
QPushButton#link:hover { color: #79c0ff; text-decoration: underline; }
"""
