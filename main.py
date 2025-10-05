# main.py
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QStackedWidget,
    QMessageBox, QDialog, QFormLayout, QCheckBox, QHBoxLayout, QTabWidget
)

from game import Game, SAVE_PATH
from ui_mainmenu import MainMenu
from ui_hub import HubMenu
from ui_games import GamesScreen
from ui_inventory_screen import InventoryScreen
from ui_slots import SlotsTab
from ui_roulette import RouletteTab
from ui_upgrades import UpgradesDialog
from modes import DiceGame, SlotsGame
from settings import load_settings, save_settings

QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)

APP_TITLE = "Idle Dice Casino"

class SettingsDialog(QDialog):
    def __init__(self, main_window: "MainWindow"):
        super().__init__(main_window)
        self.mw = main_window
        self.setWindowTitle("Settings")
        form = QFormLayout(self)
        self.cb_icons = QCheckBox("Use dice icons in animation (visual only)")
        self.cb_icons.setChecked(self.mw.settings.get("use_dice_icons", True))
        form.addRow(self.cb_icons)
        row = QHBoxLayout(); ok = QPushButton("OK"); cancel = QPushButton("Cancel")
        ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        row.addStretch(1); row.addWidget(ok); row.addWidget(cancel); form.addRow(row)
        self.setStyleSheet("""
            QDialog { background:#0f1020; color:#e8e8ff; }
            QLabel, QCheckBox { color:#e8e8ff; font-size:14px; }
            QPushButton { color:#fff; background:#2a2d5c; border-radius:8px; padding:8px 14px; }
            QPushButton:hover { background:#343879; }
        """)
    def apply(self):
        self.mw.settings["use_dice_icons"] = self.cb_icons.isChecked()
        save_settings(self.mw.settings)

class GameScreen(QWidget):
    """Play area: Dice / Slots / Roulette tabs."""
    def __init__(self, main_window: "MainWindow"):
        super().__init__(main_window)
        self.mw = main_window
        self.game = main_window.game
        self.dice_mode = DiceGame(self.game)
        self.slots_mode = SlotsGame(self.game)

        self.tabs = QTabWidget()
        # Dice tab
        dice_tab = QWidget()
        v = QVBoxLayout(dice_tab)
        self.gold_label = QLabel(); self.gold_label.setAlignment(Qt.AlignCenter)
        self.dice_label = QLabel(); self.dice_label.setAlignment(Qt.AlignCenter)
        self.message_label = QLabel("Welcome!"); self.message_label.setAlignment(Qt.AlignCenter)
        self.bet_btn = QPushButton("Bet 🎲"); self.bet_btn.clicked.connect(self.on_bet_clicked)
        self.btn_back = QPushButton("← Back to Games"); self.btn_back.clicked.connect(self.mw.show_games)
        v.addWidget(self.gold_label); v.addWidget(self.dice_label); v.addWidget(self.message_label); v.addWidget(self.bet_btn); v.addWidget(self.btn_back)
        self.tabs.addTab(dice_tab, "Dice")

        # Slots tab (dynamic)
        self.slots_tab = SlotsTab(self.game, self.slots_mode)
        if self.game.slots_unlocked: self.tabs.addTab(self.slots_tab, "Slots")

        # Roulette tab (dynamic)
        self.roulette_tab = RouletteTab(self.game)
        if self.game.roulette_unlocked: self.tabs.addTab(self.roulette_tab, "Roulette")

        root = QVBoxLayout(self); root.addWidget(self.tabs)
        self.setLayout(root)
        self._apply_theme()
        self.refresh_all()

    def _apply_theme(self):
        self.setStyleSheet("""
            QWidget { background:#0f1020; color:#e8e8ff; font-family: Segoe UI, Arial; }
            QLabel { font-size:16px; }
            QPushButton { font-size:18px; padding:10px 16px; border-radius:10px; background:#2a2d5c; }
            QPushButton:hover { background:#343879; }
            QTabWidget::pane { border: 1px solid #2a2d5c; }
            QTabBar::tab { background:#1c1e3a; padding:8px 14px; }
            QTabBar::tab:selected { background:#2a2d5c; }
        """)

    def select_tab(self, title:str):
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == title:
                self.tabs.setCurrentIndex(i); return

    def refresh_all(self):
        self.gold_label.setText(f"Gold: {int(self.game.gold)} | Diamonds: {self.game.diamonds}")
        self.dice_label.setText(f"Dice: {self.game.dice_count}d{self.game.die_sides}")
        if self.game.slots_unlocked and self.tabs.indexOf(self.slots_tab) == -1:
            self.tabs.addTab(self.slots_tab, "Slots")
        if self.game.slots_unlocked: self.slots_tab.refresh()
        if self.game.roulette_unlocked and self.tabs.indexOf(self.roulette_tab) == -1:
            self.tabs.addTab(self.roulette_tab, "Roulette")
        if self.game.roulette_unlocked: self.roulette_tab.refresh()

    def on_bet_clicked(self):
        use_icons = self.mw.settings.get("use_dice_icons", True)
        frames = ["⚀","⚁","⚂","⚃","⚄","⚅"] if use_icons else ["1","2","3","4","5","6"]
        self.message_label.setText("Rolling..."); self.bet_btn.setEnabled(False)
        from PySide6.QtCore import QTimer
        self._frames = frames; self._idx = 0
        self._timer = QTimer(self); self._timer.setInterval(max(30, int(150*self.game.animation_speed)))
        self._timer.timeout.connect(self._anim_step); self._timer.start()

    def _anim_step(self):
        self.message_label.setText(self._frames[self._idx % len(self._frames)])
        self._idx += 1
        if self._idx > 6:
            self._timer.stop()
            faces, total = DiceGame(self.game).play()
            self.refresh_all()
            self.message_label.setText(f"{len(faces)}d{self.game.die_sides} → {total}")
            self.bet_btn.setEnabled(True)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)

        self.settings = load_settings()
        self.game = Game(); self.game.load(SAVE_PATH)

        # Screens
        self.stack = QStackedWidget(self)
        self.menu = MainMenu(has_save=Path(SAVE_PATH).exists(),
                             on_continue=self.show_hub, on_new_game=self.new_game,
                             on_settings=self.open_settings, on_quit=self.close, parent=self)
        self.hub = HubMenu(self)
        self.games = GamesScreen(self)
        self.game_play = GameScreen(self)
        self.inventory_screen = InventoryScreen(self)

        self.stack.addWidget(self.menu)            # 0
        self.stack.addWidget(self.hub)             # 1
        self.stack.addWidget(self.games)           # 2
        self.stack.addWidget(self.game_play)       # 3
        self.stack.addWidget(self.inventory_screen)# 4

        # GLOBAL currency bar (always visible)
        self.currency_bar = QLabel("")
        self.currency_bar.setAlignment(Qt.AlignCenter)
        self.currency_bar.setStyleSheet("font-size:14px; padding:6px; background:#141531; border:1px solid #2a2d5c; border-radius:8px;")

        root = QVBoxLayout(self)
        root.addWidget(self.currency_bar)  # top bar stays on all screens
        root.addWidget(self.stack)
        self.setLayout(root)

        self.setStyleSheet("QWidget { background:#0f1020; color:#e8e8ff; font-family: Segoe UI, Arial; }")

        # Tick & autosave
        self.timer = QTimer(self); self.timer.setInterval(1000)
        self.timer.timeout.connect(self.tick); self.timer.start()

        self.resize(960, 640)
        self.show_menu()
        self._refresh_bar()

    # Navigation helpers
    def show_menu(self): self.stack.setCurrentIndex(0); self._refresh_bar()
    def show_hub(self):  self.stack.setCurrentIndex(1); self._refresh_bar()
    def show_games(self):
        self.games.refresh(); self.stack.setCurrentIndex(2); self._refresh_bar()
    def show_game(self, direct_tab: str | None = None):
        self.game_play.refresh_all()
        if direct_tab: self.game_play.select_tab(direct_tab)
        self.stack.setCurrentIndex(3); self._refresh_bar()
    def show_inventory(self):
        self.inventory_screen.refresh(); self.stack.setCurrentIndex(4); self._refresh_bar()

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.Accepted: dlg.apply()

    def open_global_upgrades(self):
        # Now truly global category
        dlg = UpgradesDialog(self.game, self, category_filter="global", title="Global Upgrades")
        dlg.exec(); self.games.refresh()

    def new_game(self):
        if QMessageBox.question(self, "Confirm", "Start a new game? This erases current progress.",
                                 QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                if Path(SAVE_PATH).exists(): Path(SAVE_PATH).unlink()
            except Exception: pass
            self.game.reset(); self.show_hub(); self._refresh_bar()

    def _refresh_bar(self):
        self.currency_bar.setText(
            f"Gold: {int(self.game.gold)}  |  Diamonds: {self.game.diamonds}  |  Lifetime: {int(self.game.lifetime_gold)}  |  Passive: {self.game.slots_passive_income:.1f}/s"
        )

    # Tick & save
    def tick(self):
        SlotsGame(self.game).tick_passive()
        # screen refresh
        idx = self.stack.currentIndex()
        if idx == 2: self.games.refresh()
        elif idx == 3: self.game_play.refresh_all()
        elif idx == 4: self.inventory_screen.refresh()
        self._refresh_bar()
        self.game.save(SAVE_PATH)

def main():
    app = QApplication(sys.argv)
    w = MainWindow(); w.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()
