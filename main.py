# main.py
import os, sys
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTabWidget, QStackedWidget, QHBoxLayout, QMessageBox
)

from game import Game, SAVE_PATH
from ui_upgrades import UpgradesDialog
from ui_slots import SlotsTab
from ui_mainmenu import MainMenu
from ui_inventory import InventoryTab
from ui_loadout import LoadoutTab
from modes import DiceGame, SlotsGame

QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)

APP_TITLE = "Idle Dice Casino"

class GameScreen(QWidget):
    def __init__(self, main_window: "MainWindow"):
        super().__init__(main_window)
        self.mw = main_window
        self.game = main_window.game

        # Modes
        self.dice_mode = DiceGame(self.game)
        self.slots_mode = SlotsGame(self.game)

        # Currencies bar
        self.bar = QLabel("")
        self.bar.setAlignment(Qt.AlignCenter)
        self.bar.setStyleSheet("font-size: 14px; padding: 6px; background:#141531; border:1px solid #2a2d5c; border-radius:8px;")

        # Tabs
        self.tabs = QTabWidget()
        self.dice_tab = QWidget()
        self.inventory_tab = InventoryTab(self.game)
        self.loadout_tab = LoadoutTab(self.game)
        self.tabs.addTab(self.dice_tab, "Dice")
        self.tabs.addTab(self.inventory_tab, "Inventory")
        self.tabs.addTab(self.loadout_tab, "Loadout")
        # Slots tab added dynamically upon unlock
        self.slots_tab = SlotsTab(self.game, self.slots_mode)

        # Dice HUD
        self.gold_label = QLabel(); self.gold_label.setAlignment(Qt.AlignCenter)
        self.dice_label = QLabel(); self.dice_label.setAlignment(Qt.AlignCenter)
        self.message_label = QLabel("Welcome!"); self.message_label.setAlignment(Qt.AlignCenter)
        self.bet_btn = QPushButton("Bet 🎲"); self.bet_btn.clicked.connect(self.on_bet_clicked)
        self.upgrades_btn = QPushButton("Upgrades"); self.upgrades_btn.clicked.connect(self.on_upgrades)
        self.menu_btn = QPushButton("Main Menu"); self.menu_btn.clicked.connect(self.mw.show_menu)

        dice_layout = QVBoxLayout()
        dice_layout.addWidget(self.gold_label)
        dice_layout.addWidget(self.dice_label)
        dice_layout.addWidget(self.message_label)
        dice_layout.addWidget(self.bet_btn)
        dice_layout.addWidget(self.upgrades_btn)
        dice_layout.addWidget(self.menu_btn)
        self.dice_tab.setLayout(dice_layout)

        # Wire inventory equip -> loadout
        self.inventory_tab.equip_requested.connect(self._equip_uid)

        # Root layout
        root = QVBoxLayout(self)
        root.addWidget(self.bar)
        root.addWidget(self.tabs)
        self.setLayout(root)

        # Theme
        self.setStyleSheet("""
            QWidget { background: #0f1020; color: #e8e8ff; font-family: Segoe UI, Arial; }
            QLabel { font-size: 16px; }
            QPushButton { font-size: 18px; padding: 10px 16px; border-radius: 10px; background: #2a2d5c; }
            QPushButton:hover { background: #343879; }
            QPushButton:pressed { background: #222555; }
            QTabWidget::pane { border: 1px solid #2a2d5c; }
            QTabBar::tab { background: #1c1e3a; padding: 8px 14px; }
            QTabBar::tab:selected { background: #2a2d5c; }
        """)
        self.refresh_all("Good luck!")

    # Equip from Inventory
    def _equip_uid(self, uid: int):
        if self.game.equip_first_empty(uid):
            self.loadout_tab.refresh()
            self.refresh_bar()
        else:
            QMessageBox.information(self, "Loadout", "All slots are full or dice is already equipped.")

    # HUD refreshers
    def refresh_bar(self):
        self.bar.setText(f"Gold: {int(self.game.gold)}  |  Diamonds: {self.game.diamonds}  |  Lifetime: {int(self.game.lifetime_gold)}  |  Passive: {self.game.slots_passive_income:.1f}/s")

    def refresh_all(self, msg=None):
        self.refresh_bar()
        self.gold_label.setText(f"Gold: {int(self.game.gold)} | Diamonds: {self.game.diamonds}")
        self.dice_label.setText(f"Dice: {self.game.dice_count}d{self.game.die_sides}")
        if msg: self.message_label.setText(msg)
        self.inventory_tab.refresh()
        self.loadout_tab.refresh()
        if self.game.slots_unlocked and self.tabs.indexOf(self.slots_tab) == -1:
            self.tabs.addTab(self.slots_tab, "Slots")
        if self.game.slots_unlocked:
            self.slots_tab.refresh()

    # Actions
    def on_bet_clicked(self):
        self.bet_btn.setEnabled(False)
        self.message_label.setText("Rolling...")
        frames = ["1","2","3","4","5","6"]  # consistent; icons optional later
        self._roll_frames = frames
        self._roll_index = 0
        self._roll_timer = QTimer(self)
        self._roll_timer.setInterval(max(30, int(150*self.game.animation_speed)))
        self._roll_timer.timeout.connect(self._roll_anim_step)
        self._roll_timer.start()

    def _roll_anim_step(self):
        self.message_label.setText(self._roll_frames[self._roll_index % len(self._roll_frames)])
        self._roll_index += 1
        if self._roll_index > 6:
            self._roll_timer.stop()
            faces, total = self.mw.dice_mode.play()
            self.refresh_all(f"{len(faces)}d{self.game.die_sides} → {total}")

    def on_upgrades(self):
        dlg = UpgradesDialog(self.game, self)
        dlg.exec()
        self.refresh_all()
        self.mw.save_now()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)

        self.game = Game()
        self.game.load(SAVE_PATH)

        self.stack = QStackedWidget(self)
        self.menu = MainMenu(
            has_save=Path(SAVE_PATH).exists(),
            on_continue=self.start_game,
            on_new_game=self.new_game,
            on_settings=self.open_settings,
            on_quit=self.close,
            parent=self
        )
        self.game_screen = GameScreen(self)

        self.stack.addWidget(self.menu)
        self.stack.addWidget(self.game_screen)

        root = QVBoxLayout(self)
        root.addWidget(self.stack)
        self.setLayout(root)

        # Tick & autosave
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.tick)
        self.timer.start()

        self.resize(860, 560)
        self.show_menu()

    # modes for polymorphism (kept from before)
    @property
    def dice_mode(self):  # used by GameScreen
        from modes import DiceGame
        return DiceGame(self.game)

    def show_menu(self):
        self.stack.setCurrentIndex(0)

    def start_game(self):
        self.stack.setCurrentIndex(1)
        self.game_screen.refresh_all("Welcome back!")

    def new_game(self):
        if QMessageBox.question(self, "Confirm", "Start a new game? This erases current progress.",
                                 QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                if Path(SAVE_PATH).exists():
                    Path(SAVE_PATH).unlink()
            except Exception:
                pass
            self.game.reset()
            self.start_game()

    def open_settings(self):
        from PySide6.QtWidgets import QDialog, QFormLayout, QCheckBox, QPushButton, QHBoxLayout
        dlg = QDialog(self); dlg.setWindowTitle("Settings")
        form = QFormLayout(dlg)
        info = QLabel("Settings (more soon)")
        cb = QCheckBox("Use dice icons in animation (visual only)"); cb.setChecked(False)
        form.addRow(info); form.addRow(cb)
        row = QHBoxLayout(); ok = QPushButton("OK"); cancel = QPushButton("Cancel")
        ok.clicked.connect(dlg.accept); cancel.clicked.connect(dlg.reject)
        row.addStretch(1); row.addWidget(ok); row.addWidget(cancel); form.addRow(row)
        dlg.setStyleSheet("""
            QDialog { background: #0f1020; color: #e8e8ff; }
            QPushButton { background: #2a2d5c; border-radius: 8px; padding: 6px 12px; }
            QPushButton:hover { background: #343879; }
        """)
        dlg.exec()

    def tick(self):
        # passive income
        from modes import SlotsGame
        SlotsGame(self.game).tick_passive()
        if self.stack.currentIndex() == 1:
            self.game_screen.refresh_all()
        self.save_now()

    def save_now(self):
        self.game.save(SAVE_PATH)

    def closeEvent(self, e):
        self.save_now()
        return super().closeEvent(e)

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()
