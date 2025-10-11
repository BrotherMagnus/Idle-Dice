from __future__ import annotations
from PySide6 import QtWidgets, QtCore, QtGui
from .ui_crate_reveal import CrateRevealDialog


class ScrapTab(QtWidgets.QWidget):
    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self._mw = getattr(parent, 'mw', None)
        v = QtWidgets.QVBoxLayout(self)

        self.info = QtWidgets.QLabel("")
        self.info.setAlignment(QtCore.Qt.AlignCenter)

        self.result = QtWidgets.QLabel("")
        self.result.setAlignment(QtCore.Qt.AlignCenter)

        # Mini-game UI: progress bar + Start/Stop
        self.power = QtWidgets.QProgressBar()
        self.power.setRange(0, 100)
        self.power.setValue(0)
        self.power.setFormat("Power: %v")

        legend = QtWidgets.QLabel("Zones: Fail <15 | Poor 15–40 | Good 40–70 | Great 70–85 | Perfect 85+")
        legend.setAlignment(QtCore.Qt.AlignCenter)
        legend.setStyleSheet("color:#c9cbe9; font-size:12px;")

        # Controls
        row = QtWidgets.QHBoxLayout()
        self.cost = QtWidgets.QComboBox()
        self.cost.addItems(["100", "1,000", "10,000", "100,000"])
        self.play = QtWidgets.QPushButton("Start")
        self.play.clicked.connect(self._on_toggle)
        self.quick = QtWidgets.QPushButton("Quick Salvage")
        self.quick.clicked.connect(self._on_quick)
        row.addStretch(1)
        row.addWidget(QtWidgets.QLabel("Cost:"))
        row.addWidget(self.cost)
        row.addWidget(self.play)
        row.addWidget(self.quick)
        row.addStretch(1)

        back = QtWidgets.QPushButton("← Back to Games")
        back.clicked.connect(lambda: getattr(self.parent(), 'mw', None).show_games() if getattr(self.parent(), 'mw', None) else None)

        v.addWidget(self.info)
        v.addWidget(self.power)
        v.addWidget(legend)
        v.addLayout(row)
        v.addWidget(self.result)
        # Shop panel
        shop = QtWidgets.QFrame(); shop_l = QtWidgets.QVBoxLayout(shop)
        shop.setStyleSheet("QFrame { background:#141531; border:1px solid #2a2d5c; border-radius:12px; }")
        shop_title = QtWidgets.QLabel("Scrap Crates Shop"); shop_title.setAlignment(QtCore.Qt.AlignCenter)
        shop_title.setStyleSheet("font-weight:800; font-size:14px;")
        shop_l.addWidget(shop_title)
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_basic = QtWidgets.QPushButton("Buy Basic (1,000 scrap)")
        self.btn_adv = QtWidgets.QPushButton("Buy Advanced (10,000 scrap)")
        self.btn_basic.clicked.connect(lambda: self._buy_crate("basic"))
        self.btn_adv.clicked.connect(lambda: self._buy_crate("advanced"))
        btn_row.addStretch(1); btn_row.addWidget(self.btn_basic); btn_row.addWidget(self.btn_adv); btn_row.addStretch(1)
        shop_l.addLayout(btn_row)
        self.drop_lbl = QtWidgets.QLabel(""); self.drop_lbl.setAlignment(QtCore.Qt.AlignCenter)
        shop_l.addWidget(self.drop_lbl)
        v.addWidget(shop)

        # Converter: Scrap -> Shards
        conv = QtWidgets.QFrame(); conv_l = QtWidgets.QVBoxLayout(conv)
        conv.setStyleSheet("QFrame { background:#141531; border:1px solid #2a2d5c; border-radius:12px; }")
        conv_title = QtWidgets.QLabel("Convert Scrap ➜ Shards (200 scrap = 1 shard; shard rate applies)")
        conv_title.setAlignment(QtCore.Qt.AlignCenter)
        rowc = QtWidgets.QHBoxLayout()
        self.conv_amount = QtWidgets.QComboBox(); self.conv_amount.addItems(["200", "1,000", "5,000", "20,000"])
        btn_conv = QtWidgets.QPushButton("Convert")
        btn_conv.clicked.connect(self._do_convert)
        rowc.addStretch(1); rowc.addWidget(QtWidgets.QLabel("Scrap:")); rowc.addWidget(self.conv_amount); rowc.addWidget(btn_conv); rowc.addStretch(1)
        self.conv_result = QtWidgets.QLabel(""); self.conv_result.setAlignment(QtCore.Qt.AlignCenter)
        conv_l.addWidget(conv_title); conv_l.addLayout(rowc); conv_l.addWidget(self.conv_result)
        v.addWidget(conv)
        v.addStretch(1)
        v.addWidget(back)

        self.setStyleSheet("""
            QWidget { background:#0f1020; color:#e8e8ff; }
            QLabel { font-size:16px; }
            QComboBox { background:#1c1e3a; border:1px solid #2a2d5c; border-radius:8px; padding:4px 8px; color:#e8e8ff; }
            QPushButton { background:#2a2d5c; border-radius:10px; padding:8px 12px; }
            QPushButton:hover { background:#343879; }
        """)

        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(18)
        self._timer.timeout.connect(self._tick)
        self._dir = 1
        self._running = False

        self.refresh()

    def _parse_cost(self) -> int:
        txt = self.cost.currentText().replace(",", "")
        try:
            return int(txt)
        except Exception:
            return 100

    def refresh(self):
        g = self.game
        # Hide legacy crate shop if present (now redundant due to Shop)
        try:
            self._hide_legacy_shop()
        except Exception:
            pass
        info = f"Gold: {int(g.gold):,}   Scrap: {int(g.scrap):,}   Idle Scrap: {g.scrap_idle:.1f}/s"
        self.info.setText(info)
        self.play.setEnabled(g.gold >= self._parse_cost() or self._running)
        self.quick.setEnabled(g.gold >= self._parse_cost() and not self._running)
        # crate buttons removed; no-op here

    def _on_quick(self):
        cost = self._parse_cost()
        if self.game.gold < cost:
            QtWidgets.QToolTip.showText(self.mapToGlobal(self.rect().center()), "Not enough gold")
            self.refresh(); return
        scrap, diamonds = self.game.salvage(cost)
        msg = f"Quick salvage → +{scrap:.1f} scrap"
        if diamonds:
            msg += f" and {diamonds} diamond(s)!"
        self.result.setText(msg)
        self.refresh()

    def _on_toggle(self):
        if not self._running:
            # start
            if self.game.gold < self._parse_cost():
                QtWidgets.QToolTip.showText(self.mapToGlobal(self.rect().center()), "Not enough gold")
                self.refresh(); return
            self._running = True
            self.play.setText("Stop")
            self._dir = 1
            self.power.setValue(0)
            self._timer.start()
        else:
            # stop and resolve
            self._timer.stop()
            self._running = False
            self.play.setText("Start")
            val = self.power.value()
            mult, label = self._zone_multiplier(val)
            cost = self._parse_cost()
            scrap, diamonds = self.game.salvage(cost, quality_mult=mult)
            msg = f"{label}! Power {val} → x{mult:.2f} → +{scrap:.1f} scrap"
            if diamonds:
                msg += f" and {diamonds} diamond(s)!"
            self.result.setText(msg)
            self.refresh()

    def _tick(self):
        v = self.power.value()
        v += self._dir * 3
        if v >= 100:
            v = 100; self._dir = -1
        elif v <= 0:
            v = 0; self._dir = 1
        self.power.setValue(v)

    def _zone_multiplier(self, val: int) -> tuple[float, str]:
        if val >= 85:
            return 2.5, "Perfect"
        if val >= 70:
            return 1.8, "Great"
        if val >= 40:
            return 1.2, "Good"
        if val >= 15:
            return 0.7, "Poor"
        return 0.2, "Fail"

    # ---------- Legacy shop cleanup ----------
    def _hide_legacy_shop(self):
        for frame in self.findChildren(QtWidgets.QFrame):
            labels = frame.findChildren(QtWidgets.QLabel)
            if any(l.text().strip().lower().startswith('scrap crates shop') for l in labels):
                frame.setVisible(False)
                for btn in frame.findChildren(QtWidgets.QPushButton):
                    if btn.text().lower().startswith('buy '):
                        btn.setVisible(False)
                break

    def _do_convert(self):
        amt_txt = self.conv_amount.currentText().replace(",", "")
        try:
            amt = int(amt_txt)
        except Exception:
            amt = 0
        if amt <= 0 or self.game.scrap < amt:
            QtWidgets.QToolTip.showText(self.mapToGlobal(self.rect().center()), "Not enough scrap")
            return
        shards = self.game.convert_scrap_to_shards(amt)
        self.conv_result.setText(f"Converted {amt:,} scrap ➜ +{shards:.2f} shards")
        self.refresh()
