# ui_inventory.py
from __future__ import annotations
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QIcon, QPixmap, QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QAbstractItemView, QMenu, QFrame, QGridLayout, QSizePolicy
)
from dice_models import get_templates, DiceTemplate

# --- Tooltip builder ---------------------------------------------------------
def _tooltip_for_template(t: DiceTemplate) -> str:
    return f"""
    <div style="font-family:'Segoe UI',Arial;">
      <div style="font-weight:700; font-size:13px; margin-bottom:4px;">
        {t.name} &nbsp; <span style="opacity:.8">[{t.rarity}] • Set: {t.set_name} • d{t.sides}</span>
      </div>
      <div style="margin:4px 0; font-size:12px;">
        <b>Combat</b> — HP <b>{t.hp}</b> • ATK <b>{t.atk}</b> • DEF <b>{t.defense}</b> • SPD <b>{t.speed}</b><br/>
        Crit: {t.crit_chance_pct}% • x{t.crit_mult}
      </div>
      <div style="margin:4px 0; font-size:12px;">
        <b>Economy (when equipped)</b><br/>
        Gold Mult: +{t.gold_mult_pct}% • Idle Gold: +{t.idle_gold_ps}/s<br/>
        Slot Yield: +{t.slots_mult_pct}% • Roulette: +{t.roulette_mult_pct}%<br/>
        Shard Rate: +{t.shard_rate_mult_pct}%
      </div>
    </div>
    """.strip()

def _rarity_color(r: str) -> str:
    return {
        "Common": "#9aa0c3",
        "Uncommon": "#7bd389",
        "Rare": "#6bb7ff",
        "Legendary": "#ffca6b",
    }.get(r, "#cfd2ff")

# --- Right-side details panel -------------------------------------------------
class _DetailsPanel(QFrame):
    """Pinned details panel for selected dice."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("role", "details")
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame[role="details"] {
                background:#141531; border:1px solid #2a2d5c; border-radius:12px;
            }
            QLabel[role="h1"] { font-size:16px; font-weight:800; }
            QLabel[role="meta"] { color:#c9cbe9; }
            QLabel[role="stat"] { font-size:13px; }
            QLabel[role="badge"] {
                background:#1e2043; border:1px solid #2a2d5c; border-radius:10px;
                padding:2px 8px; font-size:12px;
            }
        """)
        v = QVBoxLayout(self)
        v.setContentsMargins(14,14,14,14)
        v.setSpacing(10)

        self.icon = QLabel()
        self.icon.setFixedSize(96,96)
        self.icon.setAlignment(Qt.AlignCenter)

        self.name = QLabel("Select a die")
        self.name.setProperty("role", "h1")
        self.meta = QLabel(" ")
        self.meta.setProperty("role", "meta")
        self.badge = QLabel("")
        self.badge.setProperty("role", "badge")
        self.badge.hide()

        g = QGridLayout()
        g.setHorizontalSpacing(12)
        g.setVerticalSpacing(6)
        self.hp = QLabel("HP —"); self.hp.setProperty("role","stat")
        self.atk = QLabel("ATK —"); self.atk.setProperty("role","stat")
        self.defn = QLabel("DEF —"); self.defn.setProperty("role","stat")
        self.spd = QLabel("SPD —"); self.spd.setProperty("role","stat")
        self.crit = QLabel("Crit —"); self.crit.setProperty("role","stat")
        self.eco1 = QLabel("Gold / Idle —"); self.eco1.setProperty("role","stat")
        self.eco2 = QLabel("Slots / Roulette —"); self.eco2.setProperty("role","stat")
        self.eco3 = QLabel("Shards —"); self.eco3.setProperty("role","stat")

        g.addWidget(self.hp,0,0); g.addWidget(self.atk,0,1)
        g.addWidget(self.defn,1,0); g.addWidget(self.spd,1,1)
        g.addWidget(self.crit,2,0,1,2)
        g.addWidget(self.eco1,3,0,1,2)
        g.addWidget(self.eco2,4,0,1,2)
        g.addWidget(self.eco3,5,0,1,2)

        v.addWidget(self.icon, 0, Qt.AlignCenter)
        v.addWidget(self.name)
        v.addWidget(self.meta)
        v.addWidget(self.badge, 0, Qt.AlignLeft)
        v.addLayout(g)
        v.addStretch(1)

    def show_template(self, t: DiceTemplate):
        self.icon.clear()
        icon_path = t.resolve_icon_path()
        if icon_path:
            px = QPixmap(str(icon_path)).scaled(96,96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if not px.isNull():
                self.icon.setPixmap(px)

        self.name.setText(t.name)
        self.meta.setText(f"[<span style='color:{_rarity_color(t.rarity)}'>{t.rarity}</span>] • Set: {t.set_name} • d{t.sides}")
        self.badge.setText(f"{t.set_name} Set")
        self.badge.show()

        self.hp.setText(f"HP <b>{t.hp}</b>")
        self.atk.setText(f"ATK <b>{t.atk}</b>")
        self.defn.setText(f"DEF <b>{t.defense}</b>")
        self.spd.setText(f"SPD <b>{t.speed}</b>")
        self.crit.setText(f"Crit: <b>{t.crit_chance_pct}%</b> • x<b>{t.crit_mult}</b>")
        self.eco1.setText(f"Gold Mult: <b>{t.gold_mult_pct}%</b> • Idle Gold: <b>{t.idle_gold_ps}/s</b>")
        self.eco2.setText(f"Slots Yield: <b>{t.slots_mult_pct}%</b> • Roulette: <b>{t.roulette_mult_pct}%</b>")
        self.eco3.setText(f"Shard Rate: <b>{t.shard_rate_mult_pct}%</b>")

# --- Main inventory tab ------------------------------------------------------
class InventoryTab(QWidget):
    equip_requested = Signal(int)  # uid of dice to equip

    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self.templates = get_templates()

        self.title = QLabel("Inventory — Owned Dice")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 18px; font-weight: 700;")

        row = QHBoxLayout()
        self.listw = QListWidget()
        self.listw.setAlternatingRowColors(True)
        self.listw.setIconSize(QPixmap(48, 48).size())
        self.listw.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.listw.setSelectionMode(QAbstractItemView.SingleSelection)
        self.listw.setStyleSheet("""
            QListWidget { background: #141531; border: 1px solid #2a2d5c; }
            QListWidget::item { padding: 6px; }
            QListWidget::item:selected { background: #2a2d5c; color: #ffffff; }
        """)
        self.listw.itemDoubleClicked.connect(self._equip_from_item)
        self.listw.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listw.customContextMenuRequested.connect(self._open_context)
        self.listw.currentItemChanged.connect(self._update_details_from_selection)

        self.details = _DetailsPanel()
        self.details.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        row.addWidget(self.listw, 2)
        row.addWidget(self.details, 3)

        self.btn_equip = QPushButton("Equip to next empty slot")
        self.btn_equip.clicked.connect(self._equip_selected)

        self.info = QLabel("Tip: single-click to preview, double-click or press the button to equip.")
        self.info.setAlignment(Qt.AlignCenter)

        root = QVBoxLayout(self)
        root.addWidget(self.title)
        root.addLayout(row)
        root.addWidget(self.btn_equip)
        root.addWidget(self.info)

        self.setStyleSheet("""
            QWidget { background: #0f1020; color: #e8e8ff; }
            QToolTip {
                background-color: #1b1d3e;
                color: #e8e8ff;
                border: 1px solid #2a2d5c;
                padding: 6px 8px;
                border-radius: 8px;
            }
        """)

    # --- Refresh -------------------------------------------------------------
    def refresh(self):
        self.listw.clear()
        had_any = False
        for d in self.game.inventory:
            t = self.templates.get(d.template_key)
            if not t:
                continue
            had_any = True
            item = QListWidgetItem(f"{t.name}  [{t.rarity}]")
            item.setData(Qt.UserRole, d.uid)

            icon_path = t.resolve_icon_path()
            if icon_path:
                px = QPixmap(str(icon_path))
                if not px.isNull():
                    item.setIcon(QIcon(px))

            item.setToolTip(_tooltip_for_template(t))
            self.listw.addItem(item)

        if had_any and self.listw.count() > 0 and not self.listw.currentItem():
            self.listw.setCurrentRow(0)

    # --- Interactions --------------------------------------------------------
    def _equip_selected(self):
        it = self.listw.currentItem()
        if not it:
            self.info.setText("Select a die first.")
            return
        uid = it.data(Qt.UserRole)
        self.equip_requested.emit(uid)

    def _equip_from_item(self, item: QListWidgetItem):
        if not item:
            return
        uid = item.data(Qt.UserRole)
        self.equip_requested.emit(uid)

    def _open_context(self, pos: QPoint):
        item = self.listw.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        act_equip = QAction("Equip to next empty slot", self)
        act_equip.triggered.connect(lambda: self._equip_from_item(item))
        menu.addAction(act_equip)
        menu.exec(self.listw.mapToGlobal(pos))

    def _update_details_from_selection(self, cur: QListWidgetItem, _prev: QListWidgetItem):
        if not cur:
            return
        uid = cur.data(Qt.UserRole)
        for d in self.game.inventory:
            if d.uid == uid:
                t = self.templates.get(d.template_key)
                if t:
                    self.details.show_template(t)
                break
