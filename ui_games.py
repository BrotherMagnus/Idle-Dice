# ui_games.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QPushButton, QHBoxLayout, QGridLayout
)
from ui_upgrades import UpgradesDialog

class GamesScreen(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.game = main_window.game

        self.title = QLabel("Games")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 24px; font-weight: 900;")

        self.card_grid = QGridLayout()
        self.card_grid.setHorizontalSpacing(16)
        self.card_grid.setVerticalSpacing(16)

        # Dice (always visible)
        self.dice_card = self._make_card(
            "Dice", "Roll N dice to earn gold.",
            [("Play", self._open_dice), ("Upgrades", lambda: self._open_upgrades("dice"))]
        )
        self.card_grid.addWidget(self.dice_card, 0, 0)

        # Slots (visible once unlocked)
        self.slots_card = self._make_card(
            "Slots", "Spin 3 reels. Jackpots give Diamonds.",
            [("Play", self._open_slots), ("Upgrades", lambda: self._open_upgrades("slots"))]
        )
        self.card_grid.addWidget(self.slots_card, 0, 1)

        # Roulette (added/removed dynamically below)
        self.roulette_card = None  # type: QFrame | None

        unlocks_title = QLabel("Game Unlocks")
        unlocks_title.setAlignment(Qt.AlignCenter)
        unlocks_title.setStyleSheet("font-size:18px; font-weight:800;")

        self.unlocks_lbl = QLabel("")
        self.unlocks_lbl.setAlignment(Qt.AlignCenter)

        back_btn = QPushButton("← Back to Hub")
        back_btn.clicked.connect(self.mw.show_hub)

        root = QVBoxLayout(self)
        root.addWidget(self.title)
        root.addLayout(self.card_grid)
        root.addWidget(self._hline())
        root.addWidget(unlocks_title)
        root.addWidget(self.unlocks_lbl)
        root.addWidget(back_btn)

        self.setStyleSheet("""
            QWidget { background:#0f1020; color:#e8e8ff; font-family: Segoe UI, Arial; }
            QLabel { font-size:14px; }
            QPushButton { background:#2a2d5c; border-radius:10px; padding:8px 12px; }
            QPushButton:hover { background:#343879; }
            QFrame[role="line"] { color:#2a2d5c; }
            QFrame[role="card"] { border:1px solid #2a2d5c; border-radius:12px; padding:12px; }
            QLabel[role="card-title"] { font-weight:800; font-size:16px; }
            QLabel[role="card-desc"] { color:#c9cbe9; }
        """)
        self.refresh()

    def _hline(self):
        f = QFrame()
        f.setProperty("role", "line")
        f.setFrameShape(QFrame.HLine)
        return f

    def _make_card(self, title:str, desc:str, actions:list[tuple[str, callable]]):
        box = QFrame()
        box.setProperty("role", "card")
        v = QVBoxLayout(box)
        t = QLabel(title); t.setProperty("role", "card-title")
        d = QLabel(desc); d.setProperty("role", "card-desc"); d.setWordWrap(True)
        v.addWidget(t); v.addWidget(d)
        btn_row = QHBoxLayout()
        for label, fn in actions:
            b = QPushButton(label); b.clicked.connect(fn); btn_row.addWidget(b)
        v.addLayout(btn_row)
        return box

    def refresh(self):
        # Ensure unlock flags reflect current lifetime totals
        self.game.check_unlocks()

        # Update unlock text
        need_slots = 2000;  have_slots = int(self.game.lifetime_gold)
        need_roul  = 10000; have_roul  = int(self.game.lifetime_gold)
        status = [
            f"Slots: Earn 2,000 lifetime gold — {'Unlocked ✅' if self.game.slots_unlocked else f'Progress {have_slots}/{need_slots}'}",
            f"Roulette: Earn 10,000 lifetime gold — {'Unlocked ✅' if self.game.roulette_unlocked else f'Progress {have_roul}/{need_roul}'}",
        ]
        self.unlocks_lbl.setText("\n".join(status))

        # Show/hide Slots "Play" based on unlock
        for b in self.slots_card.findChildren(QPushButton):
            if b.text() == "Play":
                b.setEnabled(self.game.slots_unlocked)

        # Add or remove Roulette card dynamically
        if self.game.roulette_unlocked and self.roulette_card is None:
            self.roulette_card = self._make_card(
                "Roulette", "Bet on red/black or a number.",
                [("Play", self._open_roulette), ("Upgrades", lambda: self._open_upgrades("roulette"))]
            )
            # place it on next row, first column
            self.card_grid.addWidget(self.roulette_card, 1, 0)

        if not self.game.roulette_unlocked and self.roulette_card is not None:
            self.roulette_card.setParent(None)
            self.roulette_card.deleteLater()
            self.roulette_card = None

        # If present, ensure Roulette Play button is enabled (it will be, since unlocked)
        if self.roulette_card:
            for b in self.roulette_card.findChildren(QPushButton):
                if b.text() == "Play":
                    b.setEnabled(True)

    # actions
    def _open_dice(self): self.mw.show_game(direct_tab="Dice")
    def _open_slots(self): self.mw.show_game(direct_tab="Slots")
    def _open_roulette(self): self.mw.show_game(direct_tab="Roulette")
    def _open_upgrades(self, category: str):
        dlg = UpgradesDialog(self.game, self, category_filter=category, title=f"{category.title()} Upgrades")
        dlg.exec()
        self.refresh()
