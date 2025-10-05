# ui_loadout.py
from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QPushButton, QHBoxLayout, QMessageBox
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
        self.slot_buttons = []
        for i in range(SLOTS):
            lbl = QLabel(f"Slot {i+1}: [empty]")
            btn = QPushButton("Unequip")
            btn.clicked.connect(lambda _, idx=i: self._unequip(idx))
            self.grid.addWidget(lbl, i, 0)
            self.grid.addWidget(btn, i, 1)
            self.slot_labels.append(lbl)
            self.slot_buttons.append(btn)

        self.summary = QLabel("Team Summary: -")
        self.summary.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addLayout(self.grid)
        layout.addWidget(self.summary)

        self.setStyleSheet("""
            QWidget { background: #0f1020; color: #e8e8ff; }
            QLabel { font-size: 14px; }
            QPushButton { background: #2a2d5c; border-radius: 8px; padding: 6px 10px; }
            QPushButton:hover { background: #343879; }
        """)

    def refresh(self):
        # Render each slot
        for i in range(SLOTS):
            uid = self.game.loadout[i] if i < len(self.game.loadout) else 0
            if uid:
                inst = self.game.find_dice(uid)
                if not inst:
                    self.slot_labels[i].setText(f"Slot {i+1}: [missing]")
                    self.slot_buttons[i].setEnabled(False)
                    continue
                t = self.templates.get(inst.template_key)
                self.slot_labels[i].setText(f"Slot {i+1}: {t.name} (d{t.sides}) [{t.rarity}] — HP{t.hp} ATK{t.atk} DEF{t.defense} SPD{t.speed}")
                self.slot_buttons[i].setEnabled(True)
            else:
                self.slot_labels[i].setText(f"Slot {i+1}: [empty]")
                self.slot_buttons[i].setEnabled(False)

        # Simple team summary: sum stats
        total_hp = 0; total_atk = 0; total_def = 0; total_spd = 0
        for uid in self.game.loadout:
            inst = self.game.find_dice(uid)
            if not inst: continue
            t = self.templates.get(inst.template_key)
            total_hp += t.hp; total_atk += t.atk; total_def += t.defense; total_spd += t.speed
        self.summary.setText(f"Team Summary: HP {total_hp} | ATK {total_atk} | DEF {total_def} | SPD {total_spd}")

    def _unequip(self, idx: int):
        if idx < 0 or idx >= len(self.game.loadout): return
        self.game.loadout[idx] = 0
        self.game.compact_loadout()
        self.refresh()
