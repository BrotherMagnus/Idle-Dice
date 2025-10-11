# ui_upgrades.py
from __future__ import annotations
from typing import Optional, Dict
from PySide6 import QtWidgets, QtCore, QtGui
from .ui_icon_util import get_upgrade_icon

CATEGORIES = {
    "global": "Global",
    "dice": "Dice",
    "buildings": "Buildings",
    "slots": "Slots",
    "roulette": "Roulette",
    "scrap": "Scrap",
}

class UpgradesDialog(QtWidgets.QDialog):
    def __init__(self, game, parent=None, *, category_filter: Optional[str] = None, title: Optional[str] = None, building_filter_key: Optional[str] = None):
        super().__init__(parent)
        self.game = game
        self.setWindowTitle(title or "Upgrades")
        self.resize(700, 640)

        # Remember selection per category so refreshes don't kill it
        self._sel_key_by_cat: Dict[str, Optional[str]] = {}
        # Optional: when showing building-only view, restrict to a specific base building
        self._building_filter_key: Optional[str] = building_filter_key

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
            /* Dark tooltip so descriptions are readable */
            QToolTip {
                background-color: #1b1d3e;
                color: #e8e8ff;
                border: 1px solid #2a2d5c;
                padding: 6px 8px;
                border-radius: 8px;
            }
            QFrame#infoBox {
                background:#141531; border:1px solid #2a2d5c; border-radius:12px;
            }
            QLabel#infoTitle { font-size:15px; font-weight:800; }
            QLabel#infoDesc { color:#c9cbe9; font-size:13px; }
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
        lst.setUniformItemSizes(True)
        lst.clicked.connect(lambda idx, L=lst: L.setCurrentRow(idx.row()))
        lst.currentItemChanged.connect(lambda cur, _prev, cat=cat_key: self._on_selection_changed(cat, cur))
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

        # Info box (Cookie-Clicker style)
        info = QtWidgets.QFrame()
        info.setObjectName("infoBox")
        info_l = QtWidgets.QVBoxLayout(info)
        info_l.setContentsMargins(12, 10, 12, 10)
        info_title = QtWidgets.QLabel("Select an upgrade")
        info_title.setObjectName("infoTitle")
        info_desc = QtWidgets.QLabel("Hover or select an upgrade to see its details here.")
        info_desc.setObjectName("infoDesc")
        info_desc.setWordWrap(True)
        info_l.addWidget(info_title)
        info_l.addWidget(info_desc)
        v.addWidget(info)

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
        page = None
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if w.property("category") == cat:
                page = w
                break
        if not page:
            return None, None, None, None, None, None
        lst: QtWidgets.QListWidget = page.findChild(QtWidgets.QListWidget, f"list_{cat}")
        qty: QtWidgets.QComboBox = page.findChild(QtWidgets.QComboBox, f"qty_{cat}")
        gold_lbl: QtWidgets.QLabel = page.findChild(QtWidgets.QLabel, f"gold_{cat}")
        info_title: QtWidgets.QLabel = page.findChild(QtWidgets.QLabel, "infoTitle")
        info_desc: QtWidgets.QLabel = page.findChild(QtWidgets.QLabel, "infoDesc")
        return page, lst, qty, gold_lbl, info_title, info_desc

    def _refresh_tab(self, cat: str):
        page, lst, qty, gold_lbl, info_title, info_desc = self._page_widgets(cat)
        if not page or not lst:
            return

        if gold_lbl:
            gold_lbl.setText(f"Gold: {int(self.game.gold)}   Diamonds: {self.game.diamonds}")

        prev_key = self._sel_key_by_cat.get(cat)

        lst.model().layoutAboutToBeChanged.emit() if lst.model() else None
        lst.clear()

        ups = self.game.visible_upgrades(cat)
        # If filtering by a specific building, only include that building and its milestone upgrades
        if cat == "buildings" and self._building_filter_key:
            target = self._building_filter_key
            def _is_for_building(u):
                m_key = getattr(u.definition, "milestone_key", None)
                return (u.key == target) or (m_key == target)
            ups = [u for u in ups if _is_for_building(u)]
        # Otherwise, hide milestone building upgrades from the general Buildings tab
        elif cat == "buildings":
            ups = [u for u in ups if not getattr(u.definition, "milestone_key", None)]
        ups.sort(key=lambda u: (not self.game.can_buy(u), u.cost()))
        # Show icons in buildings category
        if cat == "buildings":
            lst.setIconSize(QtCore.QSize(28, 28))

        target_row = 0
        for idx, u in enumerate(ups):
            parts = [u.name, f"Lv {u.level}/{u.max_level}", f"Cost: {u.cost()}"]
            # Append per-second info where applicable
            ps = 0.0
            if getattr(u, 'slots_passive', 0.0) > 0:
                ps += u.level * u.slots_passive
            if getattr(u, 'roulette_passive', 0.0) > 0:
                ps += u.level * u.roulette_passive
            if getattr(u, 'building_gold_ps', 0.0) > 0:
                ps += u.level * u.building_gold_ps
            if ps > 0:
                parts.append(f"PS: {ps:.1f}/s")
            # Shards passive display
            shards_ps = getattr(u, 'shards_passive', 0.0) * u.level if getattr(u, 'shards_passive', 0.0) > 0 else 0.0
            if shards_ps > 0:
                parts.append(f"Shards: {shards_ps:.1f}/s")
            # Scrap passive display
            scrap_ps = getattr(u, 'scrap_passive', 0.0) * u.level if getattr(u, 'scrap_passive', 0.0) > 0 else 0.0
            if scrap_ps > 0:
                parts.append(f"Scrap: {scrap_ps:.1f}/s")
            flags = []
            if u.locked: flags.append("LOCKED")
            if u.disabled: flags.append("DISABLED")
            if u.level >= u.max_level: flags.append("MAX")
            if flags:
                parts.append("[" + ", ".join(flags) + "]")

            item = QtWidgets.QListWidgetItem("  |  ".join(parts))
            item.setData(QtCore.Qt.UserRole, u.key)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            desc = getattr(u.definition, "description", "") if hasattr(u, "definition") else ""
            if desc: item.setToolTip(desc)
            else:    item.setToolTip(f"{u.name}\nCost: {u.cost()} • Level {u.level}/{u.max_level}")

            if not self.game.can_buy(u):
                item.setForeground(QtGui.QBrush(QtGui.QColor("#9aa0c3")))
            lst.addItem(item)

            if prev_key and u.key == prev_key:
                target_row = idx
        
        # Add icons for buildings in one pass (post population)
        if cat == "buildings":
            lst.setIconSize(QtCore.QSize(28, 28))
            for i in range(lst.count()):
                it = lst.item(i)
                key = it.data(QtCore.Qt.UserRole)
                up = next((x for x in ups if x.key == key), None)
                if up:
                    pm = get_upgrade_icon(up, size=28)
                    if pm is not None:
                        it.setIcon(QtGui.QIcon(pm))

        lst.model().layoutChanged.emit() if lst.model() else None

        if lst.count() > 0 and prev_key is not None:
            lst.setCurrentRow(target_row)
            it = lst.currentItem()
            if it:
                self._on_selection_changed(cat, it)

        if lst.currentItem() is None and info_title and info_desc:
            info_title.setText("Select an upgrade")
            info_desc.setText("Hover or select an upgrade to see its details here.")

    # ---------- Info box update + selection memory ----------
    def _on_selection_changed(self, cat: str, cur_item: QtWidgets.QListWidgetItem | None):
        key = cur_item.data(QtCore.Qt.UserRole) if cur_item else None
        self._sel_key_by_cat[cat] = key

        page, lst, qty, gold_lbl, info_title, info_desc = self._page_widgets(cat)
        if not info_title or not info_desc:
            return
        if not key:
            info_title.setText("Select an upgrade")
            info_desc.setText("Hover or select an upgrade to see its details here.")
            return

        up = self._get_upgrade_by_key(key)
        if not up:
            info_title.setText("Select an upgrade")
            info_desc.setText("Hover or select an upgrade to see its details here.")
            return

        info_title.setText(up.name)
        desc = getattr(up.definition, "description", "") if hasattr(up, "definition") else ""
        if not desc:
            desc = f"Cost: {up.cost()} • Level {up.level}/{up.max_level}"
        else:
            desc += f"<br/><span style='color:#9aa0c3'>Cost: {up.cost()} • Level {up.level}/{up.max_level}</span>"

        m_key = getattr(up.definition, "milestone_key", None)
        m_lvl = getattr(up.definition, "milestone_level", 0)
        if m_key and m_lvl:
            req = self._get_upgrade_by_key(m_key)
            cur = req.level if req else 0
            req_name = (req.name if req else m_key)
            desc += f"<br/><span style='color:#ffca6b'>Requires {m_lvl}× {req_name} (owned: {cur})</span>"

        info_desc.setText(desc)
        info_desc.setTextFormat(QtCore.Qt.RichText)
        info_desc.setWordWrap(True)

    # ---------- Helpers ----------
    def _get_upgrade_by_key(self, key: str):
        return next((u for u in self.game.upgrades if u.key == key), None)

    # ---------- Buying ----------
    def _buy_item(self, cat: str, item: QtWidgets.QListWidgetItem, mode: str = "1x"):
        if not item: return
        key = item.data(QtCore.Qt.UserRole)
        up = self._get_upgrade_by_key(key)
        if not up: return
        self._buy_loop(up, mode)
        self._sel_key_by_cat[cat] = key
        self.refresh_all()

    def _buy_selected(self, cat: str):
        page, lst, qty, _gold_lbl, *_ = self._page_widgets(cat)
        if not page or not lst: return
        it = lst.currentItem()
        if not it:
            sel = lst.selectedItems()
            if sel: it = sel[0]
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
        mode = qty.currentText() if qty else "1x"
        self._buy_item(cat, it, mode)

    def _buy_loop(self, up, mode: str):
        times = 1 if mode == "1x" else (10 if mode == "10x" else 10**9)
        bought = 0
        for _ in range(times):
            if not self.game.can_buy(up): break
            if not self.game.buy(up): break
            bought += 1
        if bought == 0:
            QtWidgets.QToolTip.showText(self.mapToGlobal(self.rect().center()),
                "Can't buy yet (insufficient gold, disabled, or at max level).")
        else:
            QtWidgets.QToolTip.showText(self.mapToGlobal(self.rect().center()),
                f"Purchased {bought}× {up.name}")

    # ---------- Hotkeys ----------
    def _current_cat(self) -> str | None:
        page = self.tabs.currentWidget()
        return page.property("category") if page else None

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        if e.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            cat = self._current_cat()
            if not cat: return super().keyPressEvent(e)
            mode = "1x"
            mods = e.modifiers()
            if mods & QtCore.Qt.ControlModifier: mode = "MAX"
            elif mods & QtCore.Qt.ShiftModifier: mode = "10x"
            page, lst, qty, *_ = self._page_widgets(cat)
            if not page or not lst: return
            if not lst.currentItem() and lst.count() > 0:
                lst.setCurrentRow(0)
            old = qty.currentText() if qty else None
            if qty: qty.setCurrentText(mode)
            self._buy_selected(cat)
            if qty and old is not None: qty.setCurrentText(old)
            return
        return super().keyPressEvent(e)
