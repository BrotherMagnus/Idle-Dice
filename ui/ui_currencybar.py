# ui_currencybar.py
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from pathlib import Path

def _fmt(n: float | int) -> str:
    try:
        n = float(n)
    except Exception:
        return str(n)
    absn = abs(n)
    if absn >= 1_000_000_000: return f"{n/1_000_000_000:.2f}B"
    if absn >= 1_000_000:     return f"{n/1_000_000:.2f}M"
    if absn >= 1_000:         return f"{n/1_000:.2f}K"
    return f"{int(n):,}"

def _icon(path: str | Path, fallback_emoji: str) -> QLabel:
    lbl = QLabel()
    p = QPixmap(str(path)).scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    if not p.isNull():
        lbl.setPixmap(p); lbl.setFixedSize(20, 20); lbl.setAlignment(Qt.AlignCenter)
    else:
        lbl.setText(fallback_emoji); lbl.setAlignment(Qt.AlignCenter); lbl.setFixedWidth(20)
    return lbl

class CurrencyBar(QWidget):
    """
    [gold] 37.49K  [diamond] 10  [shard] 7,022  [scrap] 0  |  Idle Gold: 231/s  Idle Shards: 0.20/s  Idle Scrap: 0/s
    """
    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game

        h = QHBoxLayout(self)
        h.setContentsMargins(8, 4, 8, 4)
        h.setSpacing(10)

        # Core currencies
        self.gold_icon  = _icon("assets/icons/gold.png", "🟡"); self.gold_amt  = QLabel("0")
        self.dia_icon   = _icon("assets/icons/diamond.png", "💎"); self.dia_amt   = QLabel("0")
        self.shard_icon = _icon("assets/icons/shard.png", "💠");   self.shard_amt = QLabel("0")
        self.scrap_icon = _icon("assets/icons/scrap.png", "⚙️");  self.scrap_amt = QLabel("0")

        for w in (self.gold_icon, self.gold_amt,
                  self.dia_icon, self.dia_amt,
                  self.shard_icon, self.shard_amt,
                  self.scrap_icon, self.scrap_amt):
            h.addWidget(w)

        # Separator
        sep = QLabel("  |  "); sep.setStyleSheet("color:#9aa0c3;"); h.addWidget(sep)

        # Idle readout (auto-expands)
        self.idle_lbl = QLabel("Idle Gold: 0/s   Idle Shards: 0/s   Idle Scrap: 0/s")
        self.idle_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.idle_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        h.addWidget(self.idle_lbl, 1)

        self.setStyleSheet("""
            QWidget { background:#0f1020; color:#e8e8ff; font-size:14px; }
            QLabel { padding:0px; }
        """)

    def refresh(self):
        g = self.game
        # Amounts
        self.gold_amt.setText(_fmt(getattr(g, "gold", 0)))
        self.dia_amt.setText(_fmt(getattr(g, "diamonds", 0)))
        self.shard_amt.setText(_fmt(getattr(g, "shards", 0)))
        self.scrap_amt.setText(_fmt(getattr(g, "scrap", 0)))  # stays 0 until scrap system is added

        # Idle rates
        base_idle_gold_ps = (
            getattr(g, "slots_passive_income", 0.0)
            + getattr(g, "roulette_passive_income", 0.0)
            + getattr(g, "buildings_passive_income", 0.0)
            + getattr(g, "dice_idle_income", 0.0)
        )
        gm = getattr(g, "global_income_mult", 1.0)
        idle_gold_ps = base_idle_gold_ps * gm
        # shards/sec = shards_passive_income * shards_rate_mult (already applied in tick; we show the live rate)
        idle_shards_ps = getattr(g, "shards_passive_income", 0.0) * getattr(g, "shards_rate_mult", 1.0)
        idle_scrap_ps  = getattr(g, "scrap_idle", 0.0)  # placeholder for future scrap system

        self.idle_lbl.setText(
            f"Idle Gold: {_fmt(idle_gold_ps)}/s (x{gm:.2f})   "
            f"Idle Shards: {_fmt(idle_shards_ps)}/s   "
            f"Idle Scrap: {_fmt(idle_scrap_ps)}/s"
        )
