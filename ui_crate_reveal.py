from __future__ import annotations
from PySide6 import QtWidgets, QtCore, QtGui
from dice_models import get_templates

RARITY_COLORS = {
    "Common": "#9aa0c3",
    "Uncommon": "#62c370",
    "Rare": "#4db6ff",
    "Legendary": "#f6c445",
}


class CrateRevealDialog(QtWidgets.QDialog):
    def __init__(self, game, tier: str, inst, parent=None):
        super().__init__(parent)
        self.game = game
        self.tier = tier
        self.inst = inst
        self.setWindowTitle("Crate Reveal")
        self.resize(420, 320)

        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)

        title = QtWidgets.QLabel(f"{tier.title()} Crate Opened!")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size:18px; font-weight:800;")
        v.addWidget(title)

        frame = QtWidgets.QFrame(); frame.setObjectName("reveal")
        frame.setStyleSheet("QFrame#reveal { background:#141531; border:1px solid #2a2d5c; border-radius:12px; }")
        fv = QtWidgets.QVBoxLayout(frame)

        templates = get_templates()
        t = templates.get(inst.template_key)
        name = t.name if t else inst.template_key
        rarity = t.rarity if t else "Common"
        color = RARITY_COLORS.get(rarity, "#e8e8ff")

        icon = QtWidgets.QLabel("")
        pm = None
        try:
            pm = t.resolve_icon_path().as_posix() if t and t.resolve_icon_path() else None
        except Exception:
            pm = None
        if pm:
            qpm = QtGui.QPixmap(pm)
            if not qpm.isNull():
                qpm = qpm.scaled(96,96, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                icon.setPixmap(qpm)
                icon.setAlignment(QtCore.Qt.AlignCenter)
        fv.addWidget(icon)

        name_lbl = QtWidgets.QLabel(name)
        name_lbl.setAlignment(QtCore.Qt.AlignCenter)
        name_lbl.setStyleSheet(f"font-size:16px; font-weight:700; color:{color};")
        fv.addWidget(name_lbl)

        rarity_lbl = QtWidgets.QLabel(rarity)
        rarity_lbl.setAlignment(QtCore.Qt.AlignCenter)
        rarity_lbl.setStyleSheet(f"color:{color};")
        fv.addWidget(rarity_lbl)

        v.addWidget(frame, 1)

        row = QtWidgets.QHBoxLayout()
        self.btn_again = QtWidgets.QPushButton("Open Another")
        self.btn_close = QtWidgets.QPushButton("Close")
        self.btn_again.clicked.connect(self._again)
        self.btn_close.clicked.connect(self.accept)
        row.addStretch(1); row.addWidget(self.btn_again); row.addWidget(self.btn_close); row.addStretch(1)
        v.addLayout(row)

        self.setStyleSheet("""
            QDialog { background:#0f1020; color:#e8e8ff; }
            QPushButton { background:#2a2d5c; border-radius:10px; padding:8px 12px; }
            QPushButton:hover { background:#343879; }
        """)

    def _again(self):
        inst2 = self.game.open_scrap_crate(self.tier)
        if not inst2:
            QtWidgets.QToolTip.showText(self.mapToGlobal(self.rect().center()), "Not enough scrap")
            return
        # Replace current content
        self.inst = inst2
        # Rebuild dialog by resetting labels
        self.accept()
        # Re-open a new dialog
        dlg = CrateRevealDialog(self.game, self.tier, inst2, self.parent())
        dlg.exec()

