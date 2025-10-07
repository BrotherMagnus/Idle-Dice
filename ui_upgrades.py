from __future__ import annotations
from typing import Optional, Dict
from PySide6 import QtWidgets, QtCore, QtGui

CATEGORIES = {
    "global": "Global",
    "dice": "Dice",
    "buildings": "Buildings",
    "slots": "Slots",
    "roulette": "Roulette",
}

class UpgradesDialog(QtWidgets.QDialog):
    def __init__(self, game, parent=None, *, category_filter: Optional[str] = None, title: Optional[str] = None):
        super().__init__(parent)
        self.game = game
        self.setWindowTitle(title or "Upgrades")
        self.resize(640, 600)

        # Remember selection per category so refreshes don't kill it
        self._sel_key_by_cat: Dict[str, Optional[str]] = {}

        root = QtWidgets.QVBoxLayout(self)

        self.tabs = QtWidgets.QTabWidget()
        root.addWidget(self.tabs)

        if category_filter:
            label = CATEGORIES.get(category_filter, category_filter.title())
            self._add_tab(category_filter, label)
        else:
            for key, label in CATEGORIES.items():
                self._add_tab(key, label)

        # Footer buttons
        close_btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        close_btns.rejected.connect(self.reject)
        root.addWidget(close_btns)

        # Periodic refresh (selection will be preserved)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(800)
        self._timer.timeout.connect(self.refresh_all)
        self._timer.start()

        self._apply_theme()
        self.refresh_all()

    # ---------- Styling ----------
    def _apply_theme(self):
        self.setStyleSheet("""
            QDialog { background:#0f1020; color:#e8e8ff; }
            QTabWidget::pane { border: 1px solid #2a2d5c; }
            QTabBar::tab { background:#1c1e3a; padding:8px 14px; color:#e8e8ff; }
            QTabBar::tab:selected { background:#2a2d5c; }
            QListWidget { background:#141531; border:1px solid #2a2d5c; }
            QListWidget::item { padding:6px; }
            QListWidget::item:selected { background:#2a2d5c; color:#fff; }
            QPushButton { background:#2a2d5c; border-radius:10px; padding:8px 12px; }
            QPushButton:hover { background:#343879; }
            QComboBox { background:#1c1e3a; border:1px solid #2a2d5c; border-radius:8px; padding:4px 8px; color:#e8e8ff; }
            QLabel.hint { color:#9aa0c3; font-size:12px; }
        """)

    # ---------- Tab creation ----------
    def _add_tab(self, cat_key: str, label: str):
        page = QtWidgets.QWidget()
        page.setProperty("category", cat_key)
        v = QtWidgets.QVBoxLayout(page)

        # Top bar: current gold + quantity selector
        top_bar = QtWidgets.QHBoxLayout()
        gold_lbl = QtWidgets.QLabel("")
        gold_lbl.setObjectName(f"gold_{cat_key}")
        gold_lbl.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        qty_lbl = QtWidgets.QLabel("Buy:")
        qty = QtWidgets.QComboBox()
        qty.setObjectName(f"qty_{cat_key}")
        qty.addItems(["1x", "10x", "MAX"])
        qty.setFixedWidth(90)

        top_bar.addWidget(gold_lbl, 1)
        top_bar.addStretch(1)
        top_bar.addWidget(qty_lbl)
        top_bar.addWidget(qty)
        v.addLayout(top_bar)

        # Upgrades list
        lst = QtWidgets.QListWidget()
        lst.setObjectName(f"list_{cat_key}")
        lst.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        lst.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        lst.setUniformItemSizes(True)  # smoother redraws
        # Single-click => make it the current row immediately
        lst.clicked.connect(lambda idx, L=lst: L.setCurrentRow(idx.row()))
        # Track selection so we can restore it after refresh
        lst.currentItemChanged.connect(lambda cur, _prev, cat=cat_key: self._remember_selection(cat, cur))
        # Double-click buys 1×
        lst.itemDoubleClicked.connect(lambda it, cat=cat_key: self._buy_item(cat, it, mode="1x"))
        v.addWidget(lst)

        # Action buttons
        row = QtWidgets.QHBoxLayout()
        buy_btn = QtWidgets.QPushButton("Buy Selected")
        buy_btn.clicked.connect(lambda _, cat=cat_key: self._buy_selected(cat))
        row.addWidget(buy_btn)

        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_all)
        row.addWidget(refresh_btn)

        v.addLayout(row)

        # Hotkey hint
        hint = QtWidgets.QLabel("Enter=Buy • Shift+Enter=10× • Ctrl+Enter=MAX")
        hint.setAlignment(QtCore.Qt.AlignCenter)
        hint.setProperty("class", "hint")
        v.addWidget(hint)

        self.tabs.addTab(page, label)

    # ---------- Refresh ----------
    def refresh_all(self):
        for i in range(self.tabs.count()):
            page = self.tabs.widget(i)
            cat = page.property("category")
            self._refresh_tab(cat)

    def _page_widgets(self, cat: str):
        """Return (page, list, qty_combo, gold_label) or (None, None, None, None)."""
        page = None
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if w.property("category") == cat:
                page = w
                break
        if not page:
            return None, None, None, None
        lst: QtWidgets.QListWidget = page.findChild(QtWidgets.QListWidget, f"list_{cat}")
        qty: QtWidgets.QComboBox = page.findChild(QtWidgets.QComboBox, f"qty_{cat}")
        gold_lbl: QtWidgets.QLabel = page.findChild(QtWidgets.QLabel, f"gold_{cat}")
        return page, lst, qty, gold_lbl

    def _refresh_tab(self, cat: str):
        page, lst, qty, gold_lbl = self._page_widgets(cat)
        if not page or not lst:
            return

        # Show current currencies
        if gold_lbl:
            gold_lbl.setText(f"Gold: {int(self.game.gold)}   Diamonds: {self.game.diamonds}")

        # Remember selected key (if any) before we rebuild
        prev_key = self._sel_key_by_cat.get(cat)

        lst.model().layoutAboutToBeChanged.emit() if lst.model() else None
        lst.clear()

        ups = self.game.visible_upgrades(cat)
        # Sort: affordable first, then by cost
        ups.sort(key=lambda u: (not self.game.can_buy(u), u.cost()))

        # Rebuild items
        target_row = 0
        for idx, u in enumerate(ups):
            parts = [u.name, f"Lv {u.level}/{u.max_level}", f"Cost: {u.cost()}"]
            flags = []
            if u.locked: flags.append("LOCKED")
            if u.disabled: flags.append("DISABLED")
            if u.level >= u.max_level: flags.append("MAX")
            if flags:
                parts.append("[" + ", ".join(flags) + "]")

            item = QtWidgets.QListWidgetItem("  |  ".join(parts))
            item.setData(QtCore.Qt.UserRole, u.key)
            # Keep items selectable/enabled regardless of affordability
            item.setFlags(item.flags() | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            if not self.game.can_buy(u):
                item.setForeground(QtGui.QBrush(QtGui.QColor("#9aa0c3")))  # grey tint
            lst.addItem(item)

            # If this is the previously selected key, remember row to restore
            if prev_key and u.key == prev_key:
                target_row = idx

        lst.model().layoutChanged.emit() if lst.model() else None

        # Restore selection if we had one; otherwise leave it unselected
        if lst.count() > 0 and prev_key is not None:
            lst.setCurrentRow(target_row)

    # ---------- Selection memory ----------
    def _remember_selection(self, cat: str, cur_item: QtWidgets.QListWidgetItem | None):
        key = cur_item.data(QtCore.Qt.UserRole) if cur_item else None
        self._sel_key_by_cat[cat] = key

    # ---------- Buying ----------
    def _get_upgrade_by_key(self, key: str):
        return next((u for u in self.game.upgrades if u.key == key), None)

    def _buy_item(self, cat: str, item: QtWidgets.QListWidgetItem, mode: str = "1x"):
        if not item:
            return
        key = item.data(QtCore.Qt.UserRole)
        up = self._get_upgrade_by_key(key)
        if not up:
            return
        self._buy_loop(up, mode)
        # Keep selection on the same key after buying
        self._sel_key_by_cat[cat] = key
        self.refresh_all()

    def _buy_selected(self, cat: str):
        page, lst, qty, _gold_lbl = self._page_widgets(cat)
        if not page or not lst:
            return

        it = lst.currentItem()
        if not it:
            sel = lst.selectedItems()
            if sel:
                it = sel[0]
        # As a final fallback, restore last remembered selection
        if not it and lst.count() > 0:
            remembered = self._sel_key_by_cat.get(cat)
            if remembered is not None:
                for i in range(lst.count()):
                    if lst.item(i).data(QtCore.Qt.UserRole) == remembered:
                        lst.setCurrentRow(i)
                        it = lst.item(i)
                        break

        if not it:
            QtWidgets.QToolTip.showText(self.mapToGlobal(self.rect().center()), "Select an upgrade first")
            return

        mode = qty.currentText() if qty else "1x"  # "1x" | "10x" | "MAX"
        self._buy_item(cat, it, mode)

    def _buy_loop(self, up, mode: str):
        # Determine attempts
        times = 1 if mode == "1x" else (10 if mode == "10x" else 10**9)

        bought = 0
        for _ in range(times):
            if not self.game.can_buy(up):
                break
            if not self.game.buy(up):
                break
            bought += 1

        # Feedback
        if bought == 0:
            QtWidgets.QToolTip.showText(
                self.mapToGlobal(self.rect().center()),
                "Can't buy yet (insufficient gold, disabled, or at max level)."
            )
        else:
            QtWidgets.QToolTip.showText(
                self.mapToGlobal(self.rect().center()),
                f"Purchased {bought}× {up.name}"
            )

    # ---------- Hotkeys ----------
    def _current_cat(self) -> str | None:
        page = self.tabs.currentWidget()
        return page.property("category") if page else None

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        # Enter = Buy; Shift+Enter = 10×; Ctrl+Enter = MAX
        if e.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            cat = self._current_cat()
            if not cat:
                return super().keyPressEvent(e)

            mode = "1x"
            mods = e.modifiers()
            if mods & QtCore.Qt.ControlModifier:
                mode = "MAX"
            elif mods & QtCore.Qt.ShiftModifier:
                mode = "10x"

            page, lst, qty, _gold = self._page_widgets(cat)
            if not page or not lst:
                return

            # If nothing selected, try to select first item
            if not lst.currentItem() and lst.count() > 0:
                lst.setCurrentRow(0)

            # Temporarily set the tab's combo to chosen mode, call Buy Selected, then restore
            old = qty.currentText() if qty else None
            if qty:
                qty.setCurrentText(mode)
            self._buy_selected(cat)
            if qty and old is not None:
                qty.setCurrentText(old)
            return  # handled

        return super().keyPressEvent(e)
