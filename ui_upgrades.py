# ui_upgrades.py
from __future__ import annotations
from typing import Optional, List
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QGridLayout,
    QLabel, QPushButton, QHBoxLayout, QSizePolicy
)
from game import Game, Upgrade

CATEGORY_TITLES = {
    "global":   "Global Upgrades",
    "dice":     "Dice Upgrades",
    "slots":    "Slots Upgrades",
    "roulette": "Roulette Upgrades",
}

class UpgradesDialog(QDialog):
    """
    Shows upgrades by category. If category_filter is None, shows tabs for all categories
    that currently have at least one defined upgrade (even if locked).
    """
    def __init__(self, game: Game, parent=None, category_filter: Optional[str] = None, title: Optional[str] = None):
        super().__init__(parent)
        self.game = game
        self.category_filter = category_filter  # "global" | "dice" | "slots" | "roulette" | None
        self.setWindowTitle(title or CATEGORY_TITLES.get(category_filter, "Upgrades"))
        self.setModal(True)

        root = QVBoxLayout(self)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        # Which categories to show?
        if self.category_filter:
            cats: List[str] = [self.category_filter]
        else:
            # Show all known categories that exist in the game's catalog
            cats = []
            known = {"global", "dice", "slots", "roulette"}
            for c in known:
                # include if the game has any upgrade in this category (locked or not)
                if any(u.category == c for u in self.game.upgrades):
                    cats.append(c)
            # Stable order
            cats.sort(key=["global", "dice", "slots", "roulette"].index)

        # Build tabs
        if not cats:
            # fallback guard: show a single empty tab
            self._add_tab("__none__", "No Upgrades")
        else:
            for cat in cats:
                self._add_tab(cat, CATEGORY_TITLES.get(cat, cat.title()))

        # Footer
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

        # Theme
        self.setStyleSheet("""
            QDialog { background: #0f1020; color: #e8e8ff; }
            QLabel { font-size: 14px; }
            QPushButton {
                background: #2a2d5c; border-radius: 8px; padding: 6px 12px; color: #ffffff;
            }
            QPushButton:hover { background: #343879; }
            QTabWidget::pane { border: 1px solid #2a2d5c; }
            QTabBar::tab { background: #1c1e3a; padding: 8px 14px; }
            QTabBar::tab:selected { background: #2a2d5c; }
        """)

        self.resize(640, 420)
        self.refresh_all()

    # ---- UI construction helpers ----
    def _add_tab(self, category: str, title: str):
        page = QWidget()
        grid = QGridLayout(page)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)

        page.setProperty("category", category)
        page.setProperty("grid", grid)
        page.setProperty("rows", [])

        # Header
        hdr_style = "font-weight: 700;"
        grid.addWidget(self._hdr("Name"),   0, 0)
        grid.addWidget(self._hdr("Level"),  0, 1)
        grid.addWidget(self._hdr("Cost"),   0, 2)
        grid.addWidget(self._hdr("Effect"), 0, 3)
        grid.addWidget(self._hdr("Status"), 0, 4)
        grid.addWidget(self._hdr(""),       0, 5)

        self.tabs.addTab(page, title)

    def _hdr(self, text: str) -> QLabel:
        lbl = QLabel(text); lbl.setStyleSheet("font-weight: 700;")
        return lbl

    # ---- Data -> Text helpers ----
    def _effect_text(self, u: Upgrade) -> str:
        # Dice
        if u.dice_gain: return f"+{u.dice_gain} die/level"
        if u.animation_speed_mult and u.animation_speed_mult != 1.0:
            faster = round((1 - u.animation_speed_mult) * 100)
            return f"Roll speed +{faster}%/lvl"
        if u.die_sides_increase: return f"+{u.die_sides_increase} sides/level"
        # Slots
        if u.slots_passive: return f"+{u.slots_passive:.1f} gold/sec/level"
        # Global
        if u.global_gold_mult and u.global_gold_mult != 1.0:
            pct = round((u.global_gold_mult - 1.0) * 100, 2)
            return f"All income +{pct}%/lvl"
        # Roulette
        if u.roulette_payout_bonus: 
            pct = round(u.roulette_payout_bonus * 100, 2)
            return f"Roulette payouts +{pct}%/lvl"
        if u.roulette_maxbet_increase: 
            return f"Roulette max bet +{u.roulette_maxbet_increase}/lvl"
        return "-"

    def _status_text(self, u: Upgrade) -> str:
        if u.locked: return "Locked"
        if u.disabled: return "Disabled"
        if u.level >= u.max_level: return "Maxed"
        return "Available"

    # ---- Refresh logic ----
    def refresh_all(self):
        for i in range(self.tabs.count()):
            self._refresh_tab(self.tabs.widget(i))

    def _refresh_tab(self, page: QWidget):
        category = page.property("category")
        grid: QGridLayout = page.property("grid")
        rows: list = page.property("rows")

        # clear previous rows
        for r in range(len(rows)):
            for c in range(6):
                item = grid.itemAtPosition(r + 1, c)
                if item and item.widget():
                    item.widget().setParent(None)
        rows.clear()

        if category == "__none__":
            grid.addWidget(QLabel("No upgrades available."), 1, 0, 1, 6)
            return

        # Use only visible (i.e., unlocked) upgrades for this category
        vis = self.game.visible_upgrades(category)
        if not vis:
            # If there ARE upgrades in this category but all are locked, tell the player
            if any(u.category == category for u in self.game.upgrades):
                grid.addWidget(QLabel("No upgrades available yet. Progress to unlock more."), 1, 0, 1, 6)
            else:
                grid.addWidget(QLabel("No upgrades exist for this category."), 1, 0, 1, 6)
            return

        # Populate table
        row_i = 1
        for u in vis:
            name_lbl   = QLabel(u.name)
            lvl_lbl    = QLabel(str(u.level))
            cost_lbl   = QLabel(str(u.cost()))
            eff_lbl    = QLabel(self._effect_text(u))
            status_lbl = QLabel(self._status_text(u))

            buy_btn = QPushButton("Buy")
            buy_btn.setEnabled(self.game.can_buy(u))

            def make_handler(up=u, lvl_lbl=lvl_lbl, cost_lbl=cost_lbl, status_lbl=status_lbl):
                def handler():
                    if self.game.buy(up):
                        # Update inline quickly
                        lvl_lbl.setText(str(up.level))
                        cost_lbl.setText(str(up.cost()))
                        status_lbl.setText(self._status_text(up))
                        buy_btn.setEnabled(self.game.can_buy(up))
                        # Ask parent to refresh HUD if it has a refresh method
                        if self.parent() and hasattr(self.parent(), "refresh_all"):
                            try: self.parent().refresh_all()
                            except Exception: pass
                        # Also refresh other tabs (e.g., reveal/disable logic)
                        self.refresh_all()
                return handler
            buy_btn.clicked.connect(make_handler())

            grid.addWidget(name_lbl,   row_i, 0)
            grid.addWidget(lvl_lbl,    row_i, 1)
            grid.addWidget(cost_lbl,   row_i, 2)
            grid.addWidget(eff_lbl,    row_i, 3)
            grid.addWidget(status_lbl, row_i, 4)
            grid.addWidget(buy_btn,    row_i, 5)
            rows.append((u.key, lvl_lbl, cost_lbl, status_lbl, buy_btn))
            row_i += 1
