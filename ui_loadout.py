# ui_loadout.py
from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QPushButton, QFrame
from dice_models import get_templates
SLOTS = 6

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

        self.summary = QLabel("Team Summary: -")
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
            if uid:
                inst = self.game.find_dice(uid)
                if not inst:
                    self.slot_labels[i].setText(f"Slot {i+1}: [missing]")
                    self.slot_buttons[i].setEnabled(False)
                    icon_lbl.clear()
                    continue
                t = self.templates.get(inst.template_key)
                self.slot_labels[i].setText(
                    f"Slot {i+1}: {t.name} (d{t.sides}) [{t.rarity}] — HP{t.hp} ATK{t.atk} DEF{t.defense} SPD{t.speed}"
                )
                self.slot_buttons[i].setEnabled(True)
                icon_lbl.clear()
                icon_path = t.resolve_icon_path()
                if icon_path:
                    pix = QPixmap(str(icon_path)).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    if not pix.isNull():
                        icon_lbl.setPixmap(pix)
            else:
                self.slot_labels[i].setText(f"Slot {i+1}: [empty]")
                self.slot_buttons[i].setEnabled(False)
                icon_lbl.clear()

        # Team totals with set bonuses
        totals = self.game.team_totals_with_bonuses()
        self.summary.setText(
            f"Team Totals (after bonuses): HP {totals['hp']} | ATK {totals['atk']} | DEF {totals['defense']} | SPD {totals['speed']}"
        )

        # Active tiers labels
        tiers = self.game.active_set_tiers()
        if tiers:
            self.bonuses_lbl.setText("Active Set Bonuses: " + "  •  ".join(t.label for t in tiers))
        else:
            self.bonuses_lbl.setText("Active Set Bonuses: (none)")

    def _unequip(self, idx: int):
        if idx < 0 or idx >= len(self.game.loadout): return
        self.game.loadout[idx] = 0
        self.game.compact_loadout()
        self.refresh()
