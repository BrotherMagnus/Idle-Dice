from __future__ import annotations
from PySide6 import QtWidgets, QtCore


class BountiesDialog(QtWidgets.QDialog):
    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self.setWindowTitle("Shard Bounties")
        self.resize(520, 420)

        v = QtWidgets.QVBoxLayout(self)
        self.list = QtWidgets.QListWidget()
        self.list.setUniformItemSizes(True)
        v.addWidget(self.list)

        row = QtWidgets.QHBoxLayout()
        close = QtWidgets.QPushButton("Close")
        close.clicked.connect(self.accept)
        row.addStretch(1); row.addWidget(close)
        v.addLayout(row)

        self.setStyleSheet("""
            QDialog { background:#0f1020; color:#e8e8ff; }
            QListWidget { background:#141531; border:1px solid #2a2d5c; }
            QListWidget::item { padding:8px; }
            QPushButton { background:#2a2d5c; border-radius:8px; padding:6px 10px; }
            QPushButton:hover { background:#343879; }
        """)

        self.refresh()

    def refresh(self):
        self.list.clear()
        for b in self.game.list_bounties():
            text = f"{b['name']}  |  {int(min(b['current'], b['target']))}/{int(b['target'])}  |  Reward: {int(b['reward']):,} shards"
            item = QtWidgets.QListWidgetItem(text)
            item.setData(QtCore.Qt.UserRole, b['key'])
            if b['claimed']:
                item.setForeground(QtCore.Qt.gray)
                item.setText(text + "  (Claimed)")
            elif b['done']:
                item.setForeground(QtCore.Qt.green)
                item.setText(text + "  (Ready to claim)")
            self.list.addItem(item)

        # Enable item click to claim if done
        self.list.itemClicked.connect(self._on_click)

    def _on_click(self, it: QtWidgets.QListWidgetItem):
        key = it.data(QtCore.Qt.UserRole)
        # Try to claim if done
        data = next((x for x in self.game.list_bounties() if x['key']==key), None)
        if data and data['done'] and not data['claimed']:
            if self.game.claim_bounty(key):
                QtWidgets.QToolTip.showText(self.mapToGlobal(self.rect().center()), f"Claimed +{int(data['reward']):,} shards!")
                self.refresh()
        else:
            QtWidgets.QToolTip.showText(self.mapToGlobal(self.rect().center()), "Not ready yet")

