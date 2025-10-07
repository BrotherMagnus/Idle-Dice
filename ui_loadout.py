# ui_loadout.py
from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QPushButton, QFrame
from dice_models import get_templates, DiceTemplate

SLOTS = 6

def _tooltip_for_template(t: DiceTemplate) -> str:
    return f"""
    <div style="font-family:'Segoe UI',Arial; color:#e8e8ff">
      <div style="font-weight:700; font-size:13px; margin-bottom:4px;">
        {t.name} &nbsp; <span style="opacity:.8">[{t.rarity}] • Set: {t.set_name} • d{t.sides}</span>
      </div>
      <div style="margin:4px 0; font-size:12px;">
        <b>Combat</b> — HP <b>{t.hp}</b> • ATK <b>{t.atk}</b> • DEF <b>{t.defense}</b> • SPD <b>{t.speed}</b><br/>
        <span style="opacity:.9">Crit: {t.crit_chance_pct}% • x{t.crit_mult}</span>
      </div>
      <div style="margin:4px 0; font-size:12px;">
        <b>Economy (when equipped)</b><br/>
        Gold Mult: <b>+{t.gold_mult_pct}%</b> • Idle Gold: <b>+{t.idle_gold_ps}/s</b><br/>
        Slot Yield: <b>+{t.slots_mult_pct}%</b> • Roulette: <b>+{t.roulette_mult_pct}%</b><br/>
        Shard Rate: <b>+{t.shard_rate_mult_pct}%</b>
      </div>
    </div>
    """.strip()

class LoadoutTab(QWidget):
    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self.templates = get_templates()

        self.title = QLabel("Dice Loadout (6 slots)")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 18px; font-weight: 700;")

        self.grid = QGridLayout()
        self.slot_labels = []
        self.slot_icons = []
        self.slot_buttons = []
        for i in range(SLOTS):
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(64, 64)
            icon_lbl.setAlignment(Qt.AlignCenter)

            lbl = QLabel(f"Slot {i+1}: [empty]")
            lbl.setToolTip("")  # gets filled when dice present

            btn = QPushButton("Unequip")
            btn.clicked.connect(lambda _, idx=i: self._unequip(idx))

            self.grid.addWidget(icon_lbl, i, 0)
            self.grid.addWidget(lbl, i, 1)
            self.grid.addWidget(btn, i, 2)

            self.slot_icons.append(icon_lbl)
            self.slot_labels.append(lbl)
            self.slot_buttons.append(btn)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color:#2a2d5c;")

        self.summary = QLabel("Team Totals: -")
        self.summary.setAlignment(Qt.AlignCenter)
        self.bonuses_lbl = QLabel("Active Set Bonuses: (none)")
        self.bonuses_lbl.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addLayout(self.grid)
        layout.addWidget(divider)
        layout.addWidget(self.summary)
        layout.addWidget(self.bonuses_lbl)

        self.setStyleSheet("""
            QWidget { background: #0f1020; color: #e8e8ff; }
            QLabel { font-size: 14px; }
            QPushButton { background: #2a2d5c; border-radius: 8px; padding: 6px 10px; }
            QPushButton:hover { background: #343879; }
        """)

    def refresh(self):
        for i in range(SLOTS):
            uid = self.game.loadout[i] if i < len(self.game.loadout) else 0
            icon_lbl = self.slot_icons[i]
            lbl = self.slot_labels[i]

            if uid:
                inst = self.game.find_dice(uid)
                if not inst:
                    lbl.setText(f"Slot {i+1}: [missing]")
                    lbl.setToolTip("")
                    self.slot_buttons[i].setEnabled(False)
                    icon_lbl.clear()
                    continue

                t = self.templates.get(inst.template_key)
                # Compact line text
                lbl.setText(f"Slot {i+1}: {t.name} [{t.rarity}]")
                lbl.setToolTip(_tooltip_for_template(t))
                self.slot_buttons[i].setEnabled(True)

                icon_lbl.clear()
                icon_path = t.resolve_icon_path()
                if icon_path:
                    pix = QPixmap(str(icon_path)).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    if not pix.isNull():
                        icon_lbl.setPixmap(pix)
            else:
                lbl.setText(f"Slot {i+1}: [empty]")
                lbl.setToolTip("")
                self.slot_buttons[i].setEnabled(False)
                icon_lbl.clear()

        # Team totals with set bonuses
        totals = self.game.team_totals_with_bonuses()
        self.summary.setText(
            f"Team Totals (after bonuses): HP {totals['hp']} | ATK {totals['atk']} | DEF {totals['defense']} | SPD {totals['speed']}"
        )

        # Active tiers labels (keep as before)
        tiers = self.game.active_set_tiers()
        if tiers:
            # If your SetBonusTier has no 'label' attribute, you can summarize counts instead.
            self.bonuses_lbl.setText("Active Set Bonuses: " + "  •  ".join(
                [f"{b.pieces}-piece bonus" for b in tiers]
            ))
        else:
            self.bonuses_lbl.setText("Active Set Bonuses: (none)")

    def _unequip(self, idx: int):
        if idx < 0 or idx >= len(self.game.loadout): return
        self.game.loadout[idx] = 0
        self.game.compact_loadout()
        self.game.on_loadout_changed()   # <— recompute economy immediately
        self.refresh()

