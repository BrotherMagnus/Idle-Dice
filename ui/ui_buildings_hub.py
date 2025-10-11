# ui_buildings_hub.py
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QPushButton, QFrame, QComboBox
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer
from .ui_upgrades import UpgradesDialog
from .ui_icon_util import get_building_icon

class BuildingsHub(QWidget):
    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        root = QVBoxLayout(self)
        root.setContentsMargins(10,10,10,10)
        root.setSpacing(12)

        # Top controls: sort
        sort_row = QHBoxLayout()
        sort_lbl = QLabel("Sort:")
        self.sort_combo = QComboBox(); self.sort_combo.addItems(["Original", "Highest", "Lowest"]) 
        self.sort_combo.currentIndexChanged.connect(self.refresh)
        sort_row.addWidget(sort_lbl); sort_row.addWidget(self.sort_combo); sort_row.addStretch(1)
        root.addLayout(sort_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        inner = QWidget()
        self.inner_layout = QVBoxLayout(inner)
        self.scroll.setWidget(inner)
        root.addWidget(self.scroll, 1)

        self.refresh()

        # Periodic refresh to reflect purchases
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()

    def refresh(self):
        for i in reversed(range(self.inner_layout.count())):
            w = self.inner_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        data = self.game.get_building_data()
        # Group by type
        gold = [d for d in data if d.get("type") == "gold"]
        shards = [d for d in data if d.get("type") == "shards"]

        # Apply sort
        mode = (self.sort_combo.currentText() if hasattr(self, 'sort_combo') else "Original").lower()
        def sorter(items):
            if mode.startswith("high"):  # Highest total first
                return sorted(items, key=lambda d: (-d.get("total", 0.0), d["name"]))
            if mode.startswith("low"):   # Lowest total first
                return sorted(items, key=lambda d: (d.get("total", 0.0), d["name"]))
            return sorted(items, key=lambda d: d.get("order", 0))

        gold = sorter(gold)
        shards = sorter(shards)

        if gold:
            hdr = QLabel("Gold Income")
            hdr.setStyleSheet("font-size:14px; font-weight:700; color:#c9cbe9;")
            self.inner_layout.addWidget(hdr)
            for d in gold:
                self.inner_layout.addWidget(self._make_card(d))
        if shards:
            hdr = QLabel("Shards Income")
            hdr.setStyleSheet("font-size:14px; font-weight:700; color:#c9cbe9;")
            self.inner_layout.addWidget(hdr)
            for d in shards:
                self.inner_layout.addWidget(self._make_card(d))
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
        px = get_building_icon(data["key"], data["name"], size=64, source_path=data.get("icon"))
        icon.setPixmap(px)
        h.addWidget(icon)

        unit_label = "Base Income"
        total_label = "Total"
        unit_val = data.get('per_unit', 0.0)
        total_val = data.get('total', 0.0)
        # Append unit
        postfix = "s"  # seconds
        if data.get('type') == 'shards':
            unit_label = "Base Shards"
            total_label = "Total Shards"
        extra = ""
        if data.get('locked'):
            req = data.get('requires') or "Locked"
            extra = f"<br/><span style='color:#ff6b6b'>{req}</span>"
        text = QLabel(f"""
            <b>{data['name']}</b><br/>
            Owned: {data['level']}<br/>
            {unit_label}: {unit_val:.1f}/{postfix}<br/>
            {total_label}: {total_val:.1f}/{postfix}<br/>
            Cost: {data.get('cost', 0)}{extra}
        """)
        h.addWidget(text, 1)

        # Controls: quantity selector + buy buttons + view
        vbtns = QVBoxLayout()

        row_buy = QHBoxLayout()
        qty = QComboBox(); qty.addItems(["1x", "10x", "MAX"]); qty.setFixedWidth(70)
        buy_btn = QPushButton("Buy")
        # Keep enabled for feedback; affordability enforced in logic
        buy_btn.clicked.connect(lambda _, k=data["key"], Q=qty: self._buy_building(k, Q.currentText()))
        row_buy.addWidget(qty)
        row_buy.addWidget(buy_btn)
        vbtns.addLayout(row_buy)

        btn = QPushButton("View Upgrades")
        btn.clicked.connect(lambda _, k=data["key"]: self._open_upgrades_for(k))
        vbtns.addWidget(btn)

        h.addLayout(vbtns)
        if data.get('locked'):
            frame.setStyleSheet(frame.styleSheet() + "\nQFrame { opacity:0.9; } QLabel { color:#9aa0c3; }")
        return frame

    def _open_upgrades_for(self, key: str):
        dlg = UpgradesDialog(self.game, self, category_filter="buildings", title=f"{key} Upgrades", building_filter_key=key)
        dlg.exec()

    def _buy_building(self, key: str, mode: str):
        up = next((u for u in self.game.upgrades if u.key == key), None)
        if not up:
            return
        times = 1 if mode == "1x" else (10 if mode == "10x" else 10**9)
        bought = 0
        for _ in range(times):
            if not self.game.can_buy(up):
                break
            if not self.game.buy(up):
                break
            bought += 1
        # Refresh the panel after purchase
        self.refresh()
