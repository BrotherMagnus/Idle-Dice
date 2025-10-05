# ui_hub.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout

class HubMenu(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window

        title = QLabel("Hub")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: 900;")

        grid = QGridLayout()
        grid.setHorizontalSpacing(16); grid.setVerticalSpacing(16)

        btn_inventory = QPushButton("Inventory / Loadout")
        btn_games = QPushButton("Games")
        btn_combat = QPushButton("Combat (soon)")
        btn_upgrades = QPushButton("Global Upgrades")
        btn_settings = QPushButton("Settings")
        btn_menu = QPushButton("← Main Menu")

        btn_inventory.clicked.connect(self.mw.show_inventory)
        btn_games.clicked.connect(self.mw.show_games)
        btn_combat.clicked.connect(lambda: None)  # placeholder
        btn_upgrades.clicked.connect(self.mw.open_global_upgrades)
        btn_settings.clicked.connect(self.mw.open_settings)
        btn_menu.clicked.connect(self.mw.show_menu)

        for b in (btn_inventory, btn_games, btn_combat, btn_upgrades, btn_settings, btn_menu):
            b.setMinimumHeight(44)

        grid.addWidget(btn_inventory, 0, 0)
        grid.addWidget(btn_games,     0, 1)
        grid.addWidget(btn_combat,    1, 0)
        grid.addWidget(btn_upgrades,  1, 1)
        grid.addWidget(btn_settings,  2, 0)
        grid.addWidget(btn_menu,      2, 1)

        root = QVBoxLayout(self)
        root.addWidget(title)
        root.addLayout(grid)

        self.setStyleSheet("""
            QWidget { background:#0f1020; color:#e8e8ff; font-family: Segoe UI, Arial; }
            QPushButton { background:#2a2d5c; border-radius:12px; padding:10px 16px; font-size:18px; }
            QPushButton:hover { background:#343879; }
        """)
