# ui_slots.py
import random
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer
from modes import SlotsGame
from game import Game

class SlotsTab(QWidget):
    SYMBOLS = ["🍒", "🍋", "7️⃣", "💎", "⭐"]

    def __init__(self, game: Game, slots_mode: SlotsGame, parent=None):
        super().__init__(parent)
        self.game = game
        self.slots_mode = slots_mode

        layout = QVBoxLayout(self)

        self.info_lbl = QLabel("Slots passive income: 0 gold/sec")
        self.info_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_lbl)

        self.reels_lbl = QLabel("--- --- ---")
        self.reels_lbl.setAlignment(Qt.AlignCenter)
        self.reels_lbl.setStyleSheet("font-size: 36px; font-weight: bold; padding: 12px;")
        layout.addWidget(self.reels_lbl)

        self.result_lbl = QLabel("")
        self.result_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_lbl)

        self.spin_btn = QPushButton("Spin 🎰")
        self.spin_btn.clicked.connect(self.start_spin)
        layout.addWidget(self.spin_btn)

        # Theming
        self.setStyleSheet("""
            QWidget { background: #0f1020; color: #e8e8ff; font-family: Segoe UI, Arial; }
            QLabel { font-size: 16px; }
            QPushButton { font-size: 18px; padding: 10px 16px; border-radius: 10px; background: #2a2d5c; }
            QPushButton:hover { background: #343879; }
            QPushButton:pressed { background: #222555; }
        """)

        self.timer = None
        self.frame_count = 0
        self.setLayout(layout)

    def refresh(self):
        self.info_lbl.setText(
            f"Slots passive income: {self.game.slots_passive_income:.1f} gold/sec | Diamonds: {self.game.diamonds}"
        )

    def start_spin(self):
        self.spin_btn.setEnabled(False)
        self.result_lbl.setText("Spinning...")
        self.frame_count = 0

        self.timer = QTimer(self)
        self.timer.setInterval(100)  # ms between frames
        self.timer.timeout.connect(self._animate_spin)
        self.timer.start()

    def _animate_spin(self):
        self.frame_count += 1
        reels = [random.choice(self.SYMBOLS) for _ in range(3)]
        self.reels_lbl.setText(" ".join(reels))

        if self.frame_count > 10:  # stop after ~1s of animation
            self.timer.stop()
            final_reels, gold_won, diamonds_won = self.slots_mode.play()
            self.reels_lbl.setText(" ".join(final_reels))

            if diamonds_won > 0:
                self.result_lbl.setText(f"💎 JACKPOT! Won {diamonds_won} Diamonds!")
            elif gold_won > 0:
                self.result_lbl.setText(f"✨ Won {gold_won} gold")
            else:
                self.result_lbl.setText("No win, try again!")

            self.refresh()
            self.spin_btn.setEnabled(True)
