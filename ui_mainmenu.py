# ui_mainmenu.py
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox
)

class MainMenu(QWidget):
    def __init__(self, *, has_save: bool, on_continue, on_new_game, on_settings, on_quit, parent=None):
        super().__init__(parent)

        self.on_continue = on_continue
        self.on_new_game = on_new_game
        self.on_settings = on_settings
        self.on_quit = on_quit

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 36, 36, 36)
        root.setSpacing(16)

        title = QLabel("Idle Dice Casino")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 42px; font-weight: 900; letter-spacing: 1px;")
        subtitle = QLabel("Incremental • Idle • Casino")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; opacity: 0.85;")

        btn_continue = QPushButton("Continue")
        btn_continue.setEnabled(has_save)
        btn_continue.clicked.connect(lambda: self.on_continue())

        btn_new = QPushButton("New Game")
        btn_new.clicked.connect(lambda: self.on_new_game())

        btn_settings = QPushButton("Settings")
        btn_settings.clicked.connect(lambda: self.on_settings())

        btn_quit = QPushButton("Quit")
        btn_quit.clicked.connect(lambda: self.on_quit())

        # layout
        root.addStretch(1)
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(20)
        root.addWidget(btn_continue)
        root.addWidget(btn_new)
        root.addWidget(btn_settings)
        root.addWidget(btn_quit)
        root.addStretch(2)

        # theming
        self.setStyleSheet("""
            QWidget { background: #0f1020; color: #e8e8ff; font-family: Segoe UI, Arial; }
            QPushButton { font-size: 18px; padding: 12px 18px; border-radius: 12px; background: #2a2d5c; }
            QPushButton:hover { background: #343879; }
            QPushButton:pressed { background: #222555; }
        """)
