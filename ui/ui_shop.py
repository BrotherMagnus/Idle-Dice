from __future__ import annotations

from PySide6 import QtWidgets, QtCore
from .ui_crate_reveal import CrateRevealDialog
from .ui_theme import RARITY_COLORS
from PySide6.QtGui import QPixmap, QPainter, QColor, QIcon


class ShopDialog(QtWidgets.QDialog):
    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self.setWindowTitle("Shop")
        self.resize(720, 520)

        root = QtWidgets.QVBoxLayout(self)
        self.tabs = QtWidgets.QTabWidget()
        root.addWidget(self.tabs)

        # Build tabs
        self._build_tab('Crates')
        self._build_tab('Premium')
        self._build_tab('Upgrades')

        # Close row
        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        btn_close = QtWidgets.QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        row.addWidget(btn_close)
        root.addLayout(row)

        self.setStyleSheet("""
            QDialog { background:#0f1020; color:#e8e8ff; }
            QListWidget { background:#141531; border:1px solid #2a2d5c; }
            QListWidget::item { padding:8px; }
            QFrame#detail { background:#141531; border:1px solid #2a2d5c; border-radius:12px; }
            QPushButton { background:#2a2d5c; border-radius:8px; padding:8px 12px; }
            QPushButton:hover { background:#343879; }
            QLabel[h1="true"] { font-size:18px; font-weight:800; }
            QLabel[h2="true"] { font-size:14px; font-weight:700; color:#c9cbe9; }
        """)

        self.refresh()

    def _rarity_bar_icon(self, has_odds: dict | None, w: int = 40, h: int = 14) -> QIcon:
        try:
            pm = QPixmap(w, h); pm.fill(QtCore.Qt.transparent)
            if not has_odds:
                return QIcon(pm)
            order = ["Common", "Uncommon", "Rare", "Legendary"]
            painter = QPainter(pm)
            x = 0
            seg = max(1, w // max(1, sum(1 for r in order if has_odds.get(r))))
            for r in order:
                if has_odds.get(r):
                    color = QColor(RARITY_COLORS.get(r, "#ffffff"))
                    painter.fillRect(x, 0, seg-1, h, color)
                    x += seg
            painter.end()
            return QIcon(pm)
        except Exception:
            return QIcon()

    def _build_tab(self, category: str):
        w = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(w)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(8)

        lst = QtWidgets.QListWidget()
        lst.setUniformItemSizes(True)
        lst.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        lst.setMinimumWidth(260)
        lst.currentItemChanged.connect(lambda cur, prev, c=category, l=lst: self._on_select(c, l))
        lay.addWidget(lst, 3)

        detail = QtWidgets.QFrame()
        detail.setObjectName("detail")
        d = QtWidgets.QVBoxLayout(detail)
        title = QtWidgets.QLabel("Select an item"); title.setProperty("h1", True)
        desc = QtWidgets.QLabel(""); desc.setWordWrap(True)
        price = QtWidgets.QLabel(""); price.setProperty("h2", True)
        level = QtWidgets.QLabel("")
        btn_buy = QtWidgets.QPushButton("Buy")
        btn_buy.clicked.connect(lambda c=category, l=lst: self._on_buy(c, l))
        d.addWidget(title)
        d.addWidget(desc)
        d.addWidget(price)
        d.addWidget(level)
        d.addStretch(1)
        d.addWidget(btn_buy, 0, QtCore.Qt.AlignRight)
        lay.addWidget(detail, 5)

        self.tabs.addTab(w, category)
        w._list = lst  # attach for refresh
        # attach detail widgets per-tab so selection updates affect the active tab
        w._title = title; w._desc = desc; w._price = price; w._level = level; w._btn_buy = btn_buy

    def refresh(self):
        items = self.game.list_shop_items()
        by_cat = {}
        for it in items:
            by_cat.setdefault(it['category'], []).append(it)
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            cat = self.tabs.tabText(i)
            lst: QtWidgets.QListWidget = tab._list
            lst.clear()
            recs = sorted(by_cat.get(cat, []), key=lambda r: (r.get('order', 0), r['name']))
            for rec in recs:
                amt = rec['price']
                cur = rec['currency']
                label = f"{rec['name']}  -  {amt:,} {cur}"
                if rec.get('max_level'):
                    label += f"  (Lv {rec.get('level',0)}/{rec['max_level']})"
                it = QtWidgets.QListWidgetItem(label)
                it.setData(QtCore.Qt.UserRole, rec)
                if rec.get('owned_out'):
                    it.setForeground(QtCore.Qt.gray)
                # add rarity bar icon where applicable
                details = self.game.shop_item_details(rec['key']) if hasattr(self.game, 'shop_item_details') else {}
                odds = details.get('odds') if isinstance(details, dict) else None
                if odds:
                    it.setIcon(self._rarity_bar_icon(odds))
                lst.addItem(it)
            if lst.count() > 0 and lst.currentRow() < 0:
                lst.setCurrentRow(0)

    def _on_select(self, category: str, lst: QtWidgets.QListWidget):
        it = lst.currentItem()
        if not it:
            return
        rec = it.data(QtCore.Qt.UserRole)
        tab = lst.parentWidget()
        title = getattr(tab, '_title', None)
        desc_lbl = getattr(tab, '_desc', None)
        price_lbl = getattr(tab, '_price', None)
        level_lbl = getattr(tab, '_level', None)
        btn_buy = getattr(tab, '_btn_buy', None)
        if title: title.setText(rec['name'])
        details = self.game.shop_item_details(rec['key']) if hasattr(self.game, 'shop_item_details') else {}
        desc = rec.get('description', '')
        odds = details.get('odds')
        if odds:
            parts = [f"{r}: {v}%" for r, v in odds.items()]
            desc += "\nRarity odds: " + ", ".join(parts)
        pools = details.get('pool_counts')
        if pools and rec['key'].startswith('crate_'):
            totals = ", ".join([f"{k}: {v}" for k, v in pools.items()])
            desc += f"\nDice pool: {totals}"
        if desc_lbl: desc_lbl.setText(desc)
        if price_lbl: price_lbl.setText(f"Price: {int(rec['price']):,} {rec['currency']}")
        if level_lbl:
            if rec.get('max_level'):
                level_lbl.setText(f"Level: {int(rec.get('level',0))}/{rec['max_level']}")
            else:
                level_lbl.setText("")
        if btn_buy:
            btn_buy.setEnabled(not rec.get('owned_out', False))

    def _on_buy(self, category: str, lst: QtWidgets.QListWidget):
        it = lst.currentItem()
        if not it:
            return
        rec = it.data(QtCore.Qt.UserRole)
        # Confirm
        if QtWidgets.QMessageBox.question(self, "Confirm Purchase", f"Buy {rec['name']} for {int(rec['price']):,} {rec['currency']}?",
                                          QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) != QtWidgets.QMessageBox.Yes:
            return
        res = self.game.purchase_shop_item(rec['key'])
        if not res:
            QtWidgets.QToolTip.showText(self.mapToGlobal(self.rect().center()), "Not enough currency or unavailable")
            return
        # If a crate was opened, show reveal
        if hasattr(res, 'template_key'):
            dlg = CrateRevealDialog(self.game, 'premium', res, self)
            dlg.exec()
        self.refresh()
