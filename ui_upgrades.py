# ui_upgrades.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QGridLayout,
    QLabel, QPushButton, QHBoxLayout
)
from game import Game, Upgrade

class UpgradesDialog(QDialog):
    def __init__(self, game: Game, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Upgrades")
        self.game = game
        self.setModal(True)

        root = QVBoxLayout(self)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        self._add_tab("dice", "Dice Upgrades")
        self._add_tab("casino", "Casino Games")

        btn_row = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addStretch(1)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

        self.setStyleSheet("""
            QDialog { background: #0f1020; color: #e8e8ff; }
            QPushButton { background: #2a2d5c; border-radius: 8px; padding: 6px 12px; }
            QPushButton:hover { background: #343879; }
            QLabel { font-size: 14px; }
            QTabWidget::pane { border: 1px solid #2a2d5c; }
            QTabBar::tab { background: #1c1e3a; padding: 8px 14px; }
            QTabBar::tab:selected { background: #2a2d5c; }
        """)

        self.refresh_all()

    def _add_tab(self, category: str, title: str):
        page = QWidget()
        grid = QGridLayout(page)
        page.setProperty("category", category)
        page.setProperty("grid", grid)
        page.setProperty("rows", [])
        # headers
        grid.addWidget(QLabel("<b>Name</b>"), 0, 0)
        grid.addWidget(QLabel("<b>Level</b>"), 0, 1)
        grid.addWidget(QLabel("<b>Cost</b>"), 0, 2)
        grid.addWidget(QLabel("<b>Effect</b>"), 0, 3)
        grid.addWidget(QLabel("<b>Status</b>"), 0, 4)
        grid.addWidget(QLabel(""), 0, 5)
        self.tabs.addTab(page, title)

    def refresh_all(self):
        for i in range(self.tabs.count()):
            self._refresh_tab(self.tabs.widget(i))

    def _effect_text(self, u: Upgrade) -> str:
        if u.dice_gain:
            return f"+{u.dice_gain} die/level"
        if u.animation_speed_mult != 1.0:
            faster = round((1 - u.animation_speed_mult) * 100)
            return f"Roll speed +{faster}%/lvl"
        if u.die_sides_increase:
            return f"+{u.die_sides_increase} sides"
        if u.slots_passive:
            return f"+{u.slots_passive:.1f} gold/sec"
        return "-"

    def _status_text(self, u: Upgrade) -> str:
        if u.locked:
            return "Locked"
        if u.disabled:
            return "Disabled"
        if u.level >= u.max_level:
            return "Maxed"
        return "Available"

    def _refresh_tab(self, page: QWidget):
        category = page.property("category")
        grid: QGridLayout = page.property("grid")
        rows: list = page.property("rows")

        # clear old
        for r in range(len(rows)):
            for c in range(6):
                item = grid.itemAtPosition(r + 1, c)
                if item and item.widget():
                    item.widget().setParent(None)
        rows.clear()

        vis = self.game.visible_upgrades(category)
        if not vis:
            grid.addWidget(QLabel("No upgrades available."), 1, 0, 1, 6)
            return

        for i,u in enumerate(vis, start=1):
            name_lbl = QLabel(u.name)
            lvl_lbl = QLabel(str(u.level))
            cost_lbl = QLabel(str(u.cost()))
            eff_lbl = QLabel(self._effect_text(u))
            status_lbl = QLabel(self._status_text(u))
            buy_btn = QPushButton("Buy")
            buy_btn.setEnabled(self.game.can_buy(u))

            def make_handler(up=u):
                def handler():
                    if self.game.buy(up):
                        if self.parent() and hasattr(self.parent(), "refresh_hud"):
                            self.parent().refresh_hud(msg=f"Purchased {up.name}!")
                        if self.parent() and hasattr(self.parent(), "save_now"):
                            self.parent().save_now()
                        self.refresh_all()
                    else:
                        if self.parent() and hasattr(self.parent(), "refresh_hud"):
                            self.parent().refresh_hud(msg="Cannot buy (locked/disabled/insufficient).")
                return handler
            buy_btn.clicked.connect(make_handler())

            grid.addWidget(name_lbl, i, 0)
            grid.addWidget(lvl_lbl, i, 1)
            grid.addWidget(cost_lbl, i, 2)
            grid.addWidget(eff_lbl, i, 3)
            grid.addWidget(status_lbl, i, 4)
            grid.addWidget(buy_btn, i, 5)
            rows.append((u.key,lvl_lbl,cost_lbl,status_lbl,buy_btn))
