# ui_inventory.py
from __future__ import annotations
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QIcon, QPixmap, QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QAbstractItemView, QMenu, QFrame, QGridLayout, QSizePolicy,
    QComboBox
)
from core.dice_models import get_templates, DiceTemplate
from .ui_icon_util import dice_icon_with_stars, dice_icon_with_badges
from .ui_theme import RARITY_COLORS

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
    return RARITY_COLORS.get(r, "#ffffff")

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
        self.level_lbl = QLabel("Level: 1/100")
        self.level_cost = QLabel("")
        self.level_cost.setStyleSheet("color:#c9cbe9;")

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
        v.addWidget(self.level_lbl)
        v.addWidget(self.level_cost)
        v.addLayout(g)
        v.addStretch(1)

    def show_template(self, t: DiceTemplate, stars: int = 0, *, level: int = 1, cost_shards: int = 0, cost_scrap: int = 0):
        self.icon.clear()
        icon_path = t.resolve_icon_path()
        px = dice_icon_with_badges(str(icon_path) if icon_path else None, 96, stars=stars, level=level, label_text=f"d{t.sides}")
        if not px.isNull():
            self.icon.setPixmap(px)

        self.name.setText(t.name)
        self.meta.setText(f"[<span style='color:{_rarity_color(t.rarity)}'>{t.rarity}</span>] • Set: {t.set_name} • d{t.sides}")
        if stars and stars > 0:
            gold = min(stars, 5); red = max(0, stars-5)
            star_text = ("★"*gold) + ("★"*red)
            color = "#ff5555" if red>0 else "#ffca6b"
            self.badge.setText(f"<span style='color:{color}'>Stars: {stars} {star_text}</span>")
            self.badge.show()
        else:
            self.badge.setText(f"{t.set_name} Set")
            self.badge.show()

        # Level display and next cost
        try:
            self.level_lbl.setText(f"Level: {int(level)}/100")
            if int(level) >= 100:
                self.level_cost.setText("Max")
            else:
                nxt = f"Next cost: {int(cost_shards)} shards"
                if cost_scrap and int(cost_scrap) > 0:
                    nxt += f" + {int(cost_scrap)} scrap"
                self.level_cost.setText(nxt)
        except Exception:
            pass

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

        # Sorting
        sort_bar = QHBoxLayout()
        sort_bar.addWidget(QLabel("Sort:"))
        self.sort_cb = QComboBox(); self.sort_cb.addItems(["Name", "Rarity", "Sides", "Stars", "Level", "Set"]) 
        self.sort_cb.currentIndexChanged.connect(self._on_sort_changed)
        sort_bar.addWidget(self.sort_cb); sort_bar.addStretch(1)

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
        root.addLayout(sort_bar)
        root.addLayout(row)
        # Action bar: Equip on the left, Leveling panel on the right
        action_bar = QHBoxLayout()
        action_bar.addWidget(self.btn_equip)
        action_bar.addStretch(1)

        level_panel = QFrame(); level_panel.setObjectName("levelPanel")
        lp = QVBoxLayout(level_panel)
        lp.setContentsMargins(12,8,12,8)
        lp.setSpacing(6)
        lvl_title = QLabel("Leveling")
        lvl_title.setStyleSheet("font-weight:800;")
        self.cost1_lbl = QLabel("Cost +1: —")
        self.cost10_lbl = QLabel("Cost +10: —")
        cost_row = QHBoxLayout(); cost_row.addWidget(self.cost1_lbl); cost_row.addStretch(1); cost_row.addWidget(self.cost10_lbl)

        btn_row = QHBoxLayout()
        self.btn_level1 = QPushButton("Level Up +1")
        self.btn_level10 = QPushButton("Level Up +10")
        self.btn_prestige = QPushButton("Prestige (coming soon)")
        self.btn_level1.clicked.connect(lambda: self._level_up_selected(1))
        self.btn_level10.clicked.connect(lambda: self._level_up_selected(10))
        btn_row.addWidget(self.btn_level1)
        btn_row.addWidget(self.btn_level10)
        btn_row.addWidget(self.btn_prestige)

        lp.addWidget(lvl_title)
        lp.addLayout(cost_row)
        lp.addLayout(btn_row)
        action_bar.addWidget(level_panel)
        root.addLayout(action_bar)
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
            QFrame#levelPanel {
                background:#141531; border:1px solid #2a2d5c; border-radius:12px;
            }
            QFrame#levelPanel QLabel { color:#e8e8ff; }
            QFrame#levelPanel QPushButton { background:#2a2d5c; border-radius:8px; padding:6px 10px; }
            QFrame#levelPanel QPushButton:hover { background:#343879; }
        """)

    # External: select a UID programmatically and ensure details update
    def select_uid(self, uid: int):
        for i in range(self.listw.count()):
            if self.listw.item(i).data(Qt.UserRole) == uid:
                self.listw.setCurrentRow(i)
                self.listw.scrollToItem(self.listw.item(i))
                return

    # --- Refresh -------------------------------------------------------------
    def refresh(self):
        # Preserve selection and scroll
        cur = self.listw.currentItem()
        cur_uid = cur.data(Qt.UserRole) if cur else None
        sb = self.listw.verticalScrollBar()
        scroll_val = sb.value() if sb else 0
        self.listw.clear()
        had_any = False
        for d in self.game.inventory:
            t = self.templates.get(d.template_key)
            if not t:
                continue
            had_any = True
            # Append stars to name
            stars = getattr(d, 'stars', 0)
            star_suffix = f"  [{t.rarity}]"
            if stars and stars > 0:
                star_suffix += f"  (★{stars})"
            item = QListWidgetItem(f"{t.name}{star_suffix}")
            item.setData(Qt.UserRole, d.uid)
            # Normalize text to use proper star and include level
            proper_suffix = f"  [{t.rarity}]"
            if stars and stars > 0:
                proper_suffix += f"  (★{stars})"
            item.setText(f"{t.name}{proper_suffix}  Lv {getattr(d,'level',1)}")

            icon_path = t.resolve_icon_path()
            px = dice_icon_with_badges(str(icon_path) if icon_path else None, 48, stars=stars, level=getattr(d,'level',1), label_text=f"d{t.sides}")
            if not px.isNull():
                item.setIcon(QIcon(px))

            item.setToolTip(_tooltip_for_template(t))
            self.listw.addItem(item)

        # Restore selection if possible
        if cur_uid is not None:
            for i in range(self.listw.count()):
                if self.listw.item(i).data(Qt.UserRole) == cur_uid:
                    self.listw.setCurrentRow(i)
                    break
        elif had_any and self.listw.count() > 0 and not self.listw.currentItem():
            self.listw.setCurrentRow(0)
        # Restore scroll
        if sb:
            sb.setValue(scroll_val)

    def _on_sort_changed(self):
        try:
            self._sort_inventory()
        except Exception:
            pass
        self.refresh()

    def _sort_inventory(self):
        key = self.sort_cb.currentText()
        def sort_tuple(d):
            t = self.templates.get(d.template_key)
            if not t:
                return (0,)
            return {
                'Name': (t.name,),
                'Rarity': (t.rarity, t.name),
                'Sides': (t.sides, t.name),
                'Stars': (-getattr(d, 'stars',0), t.name),
                'Level': (-getattr(d, 'level',1), t.name),
                'Set': (t.set_name, t.name),
            }.get(key, (t.name,))
        self.game.inventory.sort(key=sort_tuple)

    # --- Interactions --------------------------------------------------------
    def _equip_selected(self):
        it = self.listw.currentItem()
        if not it:
            self.info.setText("Select a die first.")
            return
        uid = it.data(Qt.UserRole)
        # Try equip; show reason if fails
        before = list(self.game.loadout)
        self.equip_requested.emit(uid)
        after = list(self.game.loadout)
        if before == after:
            self.info.setText("Can't equip: either no empty slot or a die with the same sides is already equipped.")

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
                    boosted = self.game._template_with_stars_and_level(t, getattr(d,'stars',0), getattr(d,'level',1))
                    s_cost, c_cost = self.game.level_costs(d)
                    self.details.show_template(
                        boosted,
                        stars=getattr(d, 'stars', 0),
                        level=getattr(d, 'level', 1),
                        cost_shards=s_cost if d.level < 100 else 0,
                        cost_scrap=c_cost if d.level < 100 else 0,
                    )
                    # Update level buttons state and show costs on tooltip
                    can1 = self.game.can_level(d)
                    # Compute +10 aggregate costs preview without spending
                    lvl = d.level; need_s=0; need_c=0; steps=0
                    for _ in range(10):
                        if lvl >= 100: break
                        dummy = type('X',(object,),{'level':lvl})()
                        s,c = self.game.level_costs(dummy)
                        need_s += s; need_c += c; lvl += 1; steps += 1
                    self.btn_level1.setEnabled(can1)
                    self.btn_level10.setEnabled(self.game.shards >= need_s and self.game.scrap >= need_c and steps>0)
                    self.btn_level1.setToolTip(f"Cost: {s_cost} shards" + (f" + {c_cost} scrap" if c_cost>0 else ""))
                    suffix = " (to cap)" if steps<10 else ""
                    self.btn_level10.setToolTip(f"Cost: {need_s} shards" + (f" + {need_c} scrap" if need_c>0 else "") + suffix)
                    # Pulse red cost labels if unaffordable
                    self._pulse_label(self.cost1_lbl, not can1, text=f"Cost +1: {s_cost}" + (f" + {c_cost} scrap" if c_cost>0 else ""))
                    unaff10 = not (self.game.shards >= need_s and self.game.scrap >= need_c and steps>0)
                    self._pulse_label(self.cost10_lbl, unaff10, text=("Cost +10: Max" if steps==0 else f"Cost +10: {need_s}" + (f" + {need_c} scrap" if need_c>0 else "") + suffix))
                break

    def _level_up_selected(self, times: int):
        it = self.listw.currentItem()
        if not it:
            self.info.setText("Select a die first.")
            return
        uid = it.data(Qt.UserRole)
        inst = self.game.find_dice(uid)
        if not inst:
            return
        gained = self.game.level_up(inst, times)
        if gained == 0:
            if inst.level >= 100:
                self.info.setText("Max level reached. Prestige coming soon.")
            else:
                s, c = self.game.level_costs(inst)
                need = f"Need {s} shards" + (f" and {c} scrap" if c>0 else "")
                self.info.setText(f"Can't level. {need}.")
        else:
            self.info.setText(f"Leveled +{gained}. Now Lv {inst.level}.")
        self.refresh()

    # --- helpers ---
    def _pulse_label(self, lbl: QLabel, on: bool, *, text: str):
        try:
            lbl.setText(text)
            if on:
                lbl.setStyleSheet("color:#ff6b6b; font-weight:700;")
                if not hasattr(lbl, '_op_effect'):
                    eff = QGraphicsOpacityEffect(lbl)
                    lbl.setGraphicsEffect(eff)
                    anim = QPropertyAnimation(eff, b'opacity', lbl)
                    anim.setDuration(800)
                    anim.setStartValue(0.5)
                    anim.setEndValue(1.0)
                    anim.setLoopCount(-1)
                    anim.start()
                    lbl._op_effect = eff
                    lbl._op_anim = anim
                else:
                    if hasattr(lbl, '_op_anim'):
                        lbl._op_anim.start()
            else:
                lbl.setStyleSheet("color:#c9cbe9;")
                if hasattr(lbl, '_op_anim'):
                    lbl._op_anim.stop()
                if hasattr(lbl, '_op_effect'):
                    lbl._op_effect.setOpacity(1.0)
        except Exception:
            pass
