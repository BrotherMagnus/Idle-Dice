# ui_roulette.py
import random
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSpinBox, QRadioButton, QButtonGroup

class RouletteTab(QWidget):
    COLORS = {0: "green",
              **{n: ("red" if n in {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36} else "black")
                 for n in range(1,37)}}

    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game

        self.info = QLabel("Roulette — bet on Red/Black or a single number (0-36).")
        self.info.setAlignment(Qt.AlignCenter)

        # Bet controls
        ctl = QHBoxLayout()
        self.bet_amount = QSpinBox(); self.bet_amount.setRange(1, 999999)
        self.bet_amount.setValue(10)
        self.bet_amount.setSingleStep(10)
        ctl.addWidget(QLabel("Bet:")); ctl.addWidget(self.bet_amount)

        # Choice controls
        self.rb_red = QRadioButton("Red")
        self.rb_black = QRadioButton("Black")
        self.rb_number = QRadioButton("Number:")
        self.number_spin = QSpinBox(); self.number_spin.setRange(0,36)
        self.rb_red.setChecked(True)

        self.choice_group = QButtonGroup(self)
        for rb in (self.rb_red, self.rb_black, self.rb_number):
            self.choice_group.addButton(rb)

        row2 = QHBoxLayout()
        row2.addWidget(self.rb_red); row2.addWidget(self.rb_black); row2.addWidget(self.rb_number); row2.addWidget(self.number_spin)

        self.spin_btn = QPushButton("Spin 🧭")
        self.spin_btn.clicked.connect(self.start_spin)

        self.result_lbl = QLabel("—")
        self.result_lbl.setAlignment(Qt.AlignCenter)
        self.result_lbl.setStyleSheet("font-size: 22px; font-weight: 800; padding: 8px;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.info)
        layout.addLayout(ctl)
        layout.addLayout(row2)
        layout.addWidget(self.spin_btn)
        layout.addWidget(self.result_lbl)
        self.setStyleSheet("""
            QWidget { background:#0f1020; color:#e8e8ff; }
            QLabel { font-size:16px; }
            QSpinBox, QRadioButton { font-size:16px; }
            QPushButton { background:#2a2d5c; border-radius:10px; padding:10px 16px; font-size:18px; }
            QPushButton:hover { background:#343879; }
        """)

        self.timer = None; self.frames = 0

    def refresh(self):
        # enforce max bet
        self.bet_amount.setMaximum(max(1, self.game.roulette_max_bet))

    def start_spin(self):
        bet = self.bet_amount.value()
        if bet <= 0 or bet > self.game.roulette_max_bet:
            self.result_lbl.setText(f"Bet must be 1–{self.game.roulette_max_bet}.")
            return
        if bet > self.game.gold:
            self.result_lbl.setText("Not enough gold.")
            return

        # take bet upfront
        self.game.gold -= bet
        self.result_lbl.setText("Spinning...")
        self.spin_btn.setEnabled(False)
        self.frames = 0
        self.timer = QTimer(self)
        self.timer.setInterval(90)
        self.timer.timeout.connect(self._step)
        self.timer.start()

    def _step(self):
        self.frames += 1
        n = random.randint(0,36)
        col = self.COLORS[n]
        self.result_lbl.setText(f"{n} ({col})")
        if self.frames >= 14:
            self.timer.stop()
            self._resolve(n)

    def _resolve(self, number: int):
        color = self.COLORS[number]
        bet = self.bet_amount.value()
        payout_mult = 0.0

        if self.rb_red.isChecked() and color == "red":
            payout_mult = 2.0
        elif self.rb_black.isChecked() and color == "black":
            payout_mult = 2.0
        elif self.rb_number.isChecked() and number == self.number_spin.value():
            payout_mult = 36.0  # 35:1 plus stake

        if payout_mult > 0.0:
            # roulette payout bonus, then global income multiplier applies inside _apply_income
            bonus = 1.0 + self.game.roulette_payout_bonus_total
            winnings_raw = int(bet * payout_mult * bonus)
            gained = int(round(winnings_raw * self.game.global_income_mult))
            self.game.gold += gained
            self.game.lifetime_gold += gained
            # Shards proportional to winnings (with a minimum trickle)
            shards_bonus = max(0.5, gained / 1000.0)
            self.game.shards += shards_bonus
            self.result_lbl.setText(f"Win! {number} ({color})  +{gained} gold  +{shards_bonus:.1f} shards")
            try: self.game.counter_roulette_wins += 1
            except Exception: pass
        else:
            self.result_lbl.setText(f"Lose. {number} ({color})")

        self.spin_btn.setEnabled(True)
        self.refresh()
        try: self.game.counter_roulette_spins += 1
        except Exception: pass
