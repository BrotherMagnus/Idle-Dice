from __future__ import annotations
from typing import Dict, List
from PySide6 import QtWidgets, QtCore

def _fmt_val(v: float, target: float) -> str:
    try:
        if target < 1:
            return f"{v:.1f}/{target}"
        return f"{int(v):,}/{int(target):,}"
    except Exception:
        return f"{v}/{target}"


class AchievementsDialog(QtWidgets.QDialog):
    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self.setWindowTitle("Achievements")
        self.resize(720, 560)

        v = QtWidgets.QVBoxLayout(self)
        self.tabs = QtWidgets.QTabWidget()
        v.addWidget(self.tabs)

        # Build pages per category
        self._pages: Dict[str, QtWidgets.QListWidget] = {}

        btn_row = QtWidgets.QHBoxLayout()
        self.sort_lbl = QtWidgets.QLabel("Sort:")
        self.sort_combo = QtWidgets.QComboBox(); self.sort_combo.addItems(["Default", "Claimable First", "Progress"])
        self.sort_combo.currentIndexChanged.connect(self.refresh)
        btn_row.addWidget(self.sort_lbl); btn_row.addWidget(self.sort_combo)
        btn_row.addStretch(1)
        self.claim_all = QtWidgets.QPushButton("Claim All")
        self.claim_all.clicked.connect(self._claim_all)
        close = QtWidgets.QPushButton("Close")
        close.clicked.connect(self.reject)
        btn_row.addWidget(self.claim_all); btn_row.addWidget(close)
        v.addLayout(btn_row)

        self.setStyleSheet("""
            QDialog { background:#0f1020; color:#e8e8ff; }
            QTabWidget::pane { border: 1px solid #2a2d5c; }
            QTabBar::tab { background:#1c1e3a; padding:8px 14px; color:#e8e8ff; }
            QTabBar::tab:selected { background:#2a2d5c; }
            QListWidget { background:#141531; border:1px solid #2a2d5c; }
            QListWidget::item { padding:8px; }
            QPushButton { background:#2a2d5c; border-radius:10px; padding:8px 12px; }
            QPushButton:hover { background:#343879; }
        """)

        # Initial population after widgets exist
        self.refresh()

    def refresh(self):
        achs = self.game.list_achievements()
        # group by category and also build All
        by_cat: Dict[str, List[dict]] = {}
        for a in achs:
            by_cat.setdefault(a['category'], []).append(a)
        by_cat_all: Dict[str, List[dict]] = {"All": achs[:]}

        # rebuild tabs
        self.tabs.clear(); self._pages.clear()
        for cat in ["All"] + sorted(by_cat.keys()):
            page = QtWidgets.QWidget(); v = QtWidgets.QVBoxLayout(page)
            lst = QtWidgets.QListWidget(); lst.setUniformItemSizes(True)
            lst.setStyleSheet("QListWidget::item { margin: 6px; }")
            items = by_cat_all.get(cat) if cat == "All" else by_cat[cat]
            # Sorting
            mode = self.sort_combo.currentText() if hasattr(self, 'sort_combo') else 'Default'
            if mode == "Claimable First":
                def is_claimable(a): return a['done'] and not a['claimed']
                items = sorted(items, key=lambda x: (not is_claimable(x), x['category'], x['name']))
            elif mode == "Progress":
                # highest percent first
                def pct(a):
                    t = a['target'] or 1
                    return min(1.0, (a['current']/t) if t != 0 else 0)
                items = sorted(items, key=lambda x: (-pct(x), x['name']))
            for a in items:
                cur = a['current']; tgt = a['target']
                # Build a compact, readable row: Title + button on top, description text, progress bar full width

                item = QtWidgets.QListWidgetItem()
                item.setData(QtCore.Qt.UserRole, a['key'])
                item.setSizeHint(QtCore.QSize(0, 96))

                row = QtWidgets.QFrame(); row.setFrameShape(QtWidgets.QFrame.NoFrame)
                rv = QtWidgets.QVBoxLayout(row); rv.setContentsMargins(10,8,10,8); rv.setSpacing(6)

                top = QtWidgets.QHBoxLayout();
                title = QtWidgets.QLabel(a['name'])
                title.setStyleSheet("font-weight:700; font-size:14px;")
                meta = QtWidgets.QLabel(f"Reward: {a['reward']}💎")
                meta.setStyleSheet("color:#c9cbe9; font-size:12px; padding-left:8px;")
                leftwrap = QtWidgets.QHBoxLayout(); leftwrap.addWidget(title); leftwrap.addWidget(meta); leftwrap.addStretch(1)
                top.addLayout(leftwrap, 1)
                btn = QtWidgets.QPushButton("Claim" if a['done'] and not a['claimed'] else ("Claimed" if a['claimed'] else "Claim"))
                btn.setEnabled(a['done'] and not a['claimed'])
                btn.clicked.connect(lambda _=None, k=a['key']: self._claim_one(k))
                top.addWidget(btn)
                if a['done'] and not a['claimed'] and not a.get('seen', False):
                    badge = QtWidgets.QLabel("NEW!")
                    badge.setStyleSheet("color:#ffca6b; font-weight:800; padding-left:8px;")
                    top.addWidget(badge)
                rv.addLayout(top)

                desc = QtWidgets.QLabel(a['desc']); desc.setStyleSheet("color:#c9cbe9;"); desc.setWordWrap(True)
                rv.addWidget(desc)

                # Progress bar across full width
                p = QtWidgets.QProgressBar(); p.setMinimum(0); p.setMaximum(100)
                percent = 0
                if tgt > 0:
                    percent = int(min(100, round((cur / tgt) * 100)))
                p.setValue(percent)
                p.setTextVisible(False)
                barrow = QtWidgets.QHBoxLayout();
                barrow.addWidget(p, 1)
                val = QtWidgets.QLabel(_fmt_val(cur, tgt)); val.setStyleSheet("color:#c9cbe9; padding-left:8px;")
                barrow.addWidget(val)
                rv.addLayout(barrow)

                # Color cue on left border via stylesheet
                if a['claimed']:
                    row.setStyleSheet("QFrame { border-left: 4px solid #6b7280; }")
                elif a['done']:
                    row.setStyleSheet("QFrame { border-left: 4px solid #22c55e; }")
                else:
                    row.setStyleSheet("QFrame { border-left: 4px solid #374151; }")

                lst.addItem(item)
                lst.setItemWidget(item, row)

            # Allow clicking list rows to claim if eligible
            lst.itemClicked.connect(self._on_item_clicked)
            v.addWidget(lst)
            self.tabs.addTab(page, cat)

        self._update_claim_all()

    def closeEvent(self, event):
        # Mark done-but-unclaimed achievements as seen
        try:
            self.game.mark_achievements_seen()
        except Exception:
            pass
        return super().closeEvent(event)

    def _update_claim_all(self):
        achs = self.game.list_achievements()
        any_claimable = any(a['done'] and not a['claimed'] for a in achs)
        self.claim_all.setEnabled(any_claimable)

    def _claim_one(self, key: str):
        if self.game.claim_achievement(key):
            QtWidgets.QToolTip.showText(self.mapToGlobal(self.rect().center()), "Reward claimed!")
        self.refresh()

    def _claim_all(self):
        achs = self.game.list_achievements()
        claimed = 0
        for a in achs:
            if a['done'] and not a['claimed']:
                if self.game.claim_achievement(a['key']):
                    claimed += 1
        if claimed:
            QtWidgets.QToolTip.showText(self.mapToGlobal(self.rect().center()), f"Claimed {claimed} achievements!")
        self.refresh()

    def _on_item_clicked(self, item: QtWidgets.QListWidgetItem):
        key = item.data(QtCore.Qt.UserRole)
        # Try to claim on click if eligible
        achs = {a['key']: a for a in self.game.list_achievements()}
        data = achs.get(key)
        if data and data.get('done') and not data.get('claimed'):
            self._claim_one(key)
