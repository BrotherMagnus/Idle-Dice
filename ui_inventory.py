# ui_inventory.py
from __future__ import annotations
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QIcon, QPixmap, QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
    QAbstractItemView, QMenu
)
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
        # Make selection unambiguous and obvious
        self.listw.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.listw.setSelectionMode(QAbstractItemView.SingleSelection)
        self.listw.setStyleSheet("""
            QListWidget { background: #141531; border: 1px solid #2a2d5c; }
            QListWidget::item { padding: 6px; }
            QListWidget::item:selected { background: #2a2d5c; color: #ffffff; }
        """)
        # Double-click to equip
        self.listw.itemDoubleClicked.connect(self._equip_from_item)
        # Right-click context menu
        self.listw.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listw.customContextMenuRequested.connect(self._open_context)

        self.btn_equip = QPushButton("Equip to next empty slot")
        self.btn_equip.clicked.connect(self._equip_selected)

        self.info = QLabel("Tip: double-click a die or use the Equip button.")
        self.info.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.listw)
        layout.addWidget(self.btn_equip)
        layout.addWidget(self.info)

        self.setStyleSheet("QWidget { background: #0f1020; color: #e8e8ff; }")

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

    # --- interactions ---
    def _equip_selected(self):
        it = self.listw.currentItem()
        if not it:
            self.info.setText("Select a die first.")
            return
        uid = it.data(Qt.UserRole)
        self.equip_requested.emit(uid)

    def _equip_from_item(self, item: QListWidgetItem):
        if not item: return
        uid = item.data(Qt.UserRole)
        self.equip_requested.emit(uid)

    def _open_context(self, pos: QPoint):
        item = self.listw.itemAt(pos)
        if not item: return
        menu = QMenu(self)
        act_equip = QAction("Equip to next empty slot", self)
        act_equip.triggered.connect(lambda: self._equip_from_item(item))
        menu.addAction(act_equip)
        menu.exec(self.listw.mapToGlobal(pos))
