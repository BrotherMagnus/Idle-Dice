# ui_hub.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QHBoxLayout
from .ui_buildings_hub import BuildingsHub

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
        btn_upgrades_global = QPushButton("Global Upgrades")
        btn_settings = QPushButton("Settings")
        btn_shop = QPushButton("Shop")
        self.btn_achievements = QPushButton("Achievements")
        self.btn_bounties = QPushButton("Bounties")
        btn_menu = QPushButton("← Main Menu")

        btn_inventory.clicked.connect(self.mw.show_inventory)
        btn_games.clicked.connect(self.mw.show_games)
        btn_combat.clicked.connect(lambda: None)
        btn_upgrades_global.clicked.connect(self.mw.open_global_upgrades)
        btn_settings.clicked.connect(self.mw.open_settings)
        btn_shop.clicked.connect(self.mw.open_shop)
        self.btn_achievements.clicked.connect(self.mw.open_achievements)
        self.btn_bounties.clicked.connect(self.mw.open_bounties)
        btn_menu.clicked.connect(self.mw.show_menu)

        for b in (btn_inventory, btn_games, btn_combat, btn_upgrades_global, self.btn_achievements, self.btn_bounties, btn_shop, btn_settings, btn_menu):
            b.setMinimumHeight(44)

        grid.addWidget(btn_inventory,        0, 0)
        grid.addWidget(btn_games,            0, 1)
        grid.addWidget(btn_combat,           1, 0)
        grid.addWidget(btn_upgrades_global,  1, 1)
        grid.addWidget(self.btn_achievements,     2, 0)
        grid.addWidget(self.btn_bounties,         2, 1)
        grid.addWidget(btn_shop,             3, 0)
        grid.addWidget(btn_settings,         3, 1)
        grid.addWidget(btn_menu,             4, 0)

        # Left: menu grid, Right: buildings sidebar
        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.addLayout(grid)
        left_l.addStretch(1)

        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.setSpacing(8)
        right_panel = BuildingsHub(self.mw.game, self)
        right_l.addWidget(right_panel, 1)
        right.setMinimumWidth(300)

        body = QHBoxLayout()
        body.addWidget(left, 1)
        body.addWidget(right, 0)

        root = QVBoxLayout(self)
        root.addWidget(title)
        root.addLayout(body)

        self.setStyleSheet("""
            QWidget { background:#0f1020; color:#e8e8ff; font-family: Segoe UI, Arial; }
            QPushButton { background:#2a2d5c; border-radius:12px; padding:10px 16px; font-size:18px; }
            QPushButton:hover { background:#343879; }
        """)

    def refresh(self):
        # Show NEW indicator if there are unclaimed achievements
        try:
            achs = self.mw.game.list_achievements()
            new_count = sum(1 for a in achs if a['done'] and not a['claimed'] and not a.get('seen', False))
            claimable_count = sum(1 for a in achs if a['done'] and not a['claimed'])
            label = "Achievements"
            if new_count > 0:
                label += f" ({new_count} NEW)"
            elif claimable_count > 0:
                label += f" ({claimable_count})"
            self.btn_achievements.setText(label)
        except Exception:
            pass
