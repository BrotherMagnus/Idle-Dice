# ui_inventory.py
from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton
from dice_models import get_templates

class InventoryTab(QWidget):
    equip_requested = Signal(int)  # uid of dice to equip

    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self.templates = get_templates()

        self.title = QLabel("Inventory — Owned Dice")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 18px; font-weight: 700;")

        self.listw = QListWidget()
        self.listw.setAlternatingRowColors(True)
        self.listw.setIconSize(QPixmap(64, 64).size())

        self.btn_equip = QPushButton("Equip to next empty slot")
        self.btn_equip.clicked.connect(self._equip_selected)

        self.info = QLabel("Tip: select a die and click Equip.")
        self.info.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.listw)
        layout.addWidget(self.btn_equip)
        layout.addWidget(self.info)

        self.setStyleSheet("""
            QWidget { background: #0f1020; color: #e8e8ff; }
            QListWidget { background: #141531; border: 1px solid #2a2d5c; }
            QPushButton { background: #2a2d5c; border-radius: 8px; padding: 8px 12px; }
            QPushButton:hover { background: #343879; }
        """)

    def refresh(self):
        self.listw.clear()
        for d in self.game.inventory:
            t = self.templates.get(d.template_key)
            if not t:
                continue
            tag = f"[{t.rarity}] {t.name} (d{t.sides})  |  HP {t.hp}  ATK {t.atk}  DEF {t.defense}  SPD {t.speed}  |  Set: {t.set_name}"
            item = QListWidgetItem(tag)
            item.setData(Qt.UserRole, d.uid)

            icon_path = t.resolve_icon_path()
            if icon_path:
                pix = QPixmap(str(icon_path))
                if not pix.isNull():
                    item.setIcon(QIcon(pix))

            self.listw.addItem(item)

    def _equip_selected(self):
        it = self.listw.currentItem()
        if not it:
            self.info.setText("Select a die first.")
            return
        uid = it.data(Qt.UserRole)
        self.equip_requested.emit(uid)
