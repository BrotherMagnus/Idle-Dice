# ui_buildings_hub.py
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QPushButton, QFrame
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from ui_upgrades import UpgradesDialog

class BuildingsHub(QWidget):
    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        root = QVBoxLayout(self)
        root.setContentsMargins(10,10,10,10)
        root.setSpacing(12)

        title = QLabel("Your Buildings")
        title.setStyleSheet("font-size:18px; font-weight:800;")
        root.addWidget(title)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        inner = QWidget()
        self.inner_layout = QVBoxLayout(inner)
        self.scroll.setWidget(inner)
        root.addWidget(self.scroll, 1)

        self.refresh()

    def refresh(self):
        for i in reversed(range(self.inner_layout.count())):
            w = self.inner_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        for data in self.game.get_building_data():
            card = self._make_card(data)
            self.inner_layout.addWidget(card)
        self.inner_layout.addStretch(1)

    def _make_card(self, data):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background:#141531;
                border:1px solid #2a2d5c;
                border-radius:12px;
            }
            QLabel { color:#e8e8ff; }
            QPushButton {
                background:#2a2d5c; border-radius:8px; padding:6px 10px;
            }
            QPushButton:hover { background:#343879; }
        """)
        h = QHBoxLayout(frame)
        h.setContentsMargins(10,8,10,8)
        h.setSpacing(10)

        icon = QLabel()
        px = QPixmap(data["icon"]).scaled(64,64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon.setPixmap(px)
        h.addWidget(icon)

        text = QLabel(f"""
            <b>{data['name']}</b><br/>
            Owned: {data['level']}<br/>
            Income: {data['income']:.1f}/s
        """)
        h.addWidget(text, 1)

        btn = QPushButton("View Upgrades")
        btn.clicked.connect(lambda _, k=data["key"]: self._open_upgrades_for(k))
        h.addWidget(btn)
        return frame

    def _open_upgrades_for(self, key: str):
        dlg = UpgradesDialog(self.game, self, category_filter="buildings", title=f"{key} Upgrades")
        dlg.exec()
