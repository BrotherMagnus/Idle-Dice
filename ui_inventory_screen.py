# ui_inventory_screen.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from ui_inventory import InventoryTab
from ui_loadout import LoadoutTab

class InventoryScreen(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.game = main_window.game

        title = QLabel("Inventory & Loadout")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: 800;")

        self.inv = InventoryTab(self.game)
        self.loadout = LoadoutTab(self.game)
        self.inv.equip_requested.connect(self._equip_uid)

        back_btn = QPushButton("← Back to Hub")
        back_btn.clicked.connect(self.mw.show_hub)

        row = QHBoxLayout()
        row.addWidget(self.inv, 2)
        row.addWidget(self.loadout, 3)

        root = QVBoxLayout(self)
        root.addWidget(title)
        root.addLayout(row)
        root.addWidget(back_btn)

        self.setStyleSheet("""
            QWidget { background:#0f1020; color:#e8e8ff; font-family: Segoe UI, Arial; }
            QPushButton { background:#2a2d5c; border-radius:10px; padding:8px 12px; }
            QPushButton:hover { background:#343879; }
        """)

    def refresh(self):
        self.inv.refresh()
        self.loadout.refresh()

    def _equip_uid(self, uid: int):
        if self.game.equip_first_empty(uid):
            self.loadout.refresh()
        else:
            # No modal spam; leave to UX soft-fail
            pass