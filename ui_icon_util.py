from __future__ import annotations
from typing import Optional

from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush, QIcon
from PySide6.QtCore import Qt, QSize, QPoint


def _stable_color_from_key(key: str) -> QColor:
    # Simple stable hash to hue
    total = sum(ord(c) for c in key)
    hue = (total * 37) % 360
    # Convert HSL to QColor; keep saturation/value moderate
    color = QColor()
    color.setHsv(hue, 160, 180)
    return color


def _initials(name: str, count: int = 2) -> str:
    parts = [p for p in name.split() if p]
    if not parts:
        return name[:count].upper()
    letters = "".join(p[0] for p in parts[:count])
    return letters.upper()


def get_building_icon(key: str, name: str, size: int = 64, *, source_path: Optional[str] = None) -> QPixmap:
    # Try file first if provided
    if source_path:
        pm = QPixmap(source_path)
        if not pm.isNull():
            return pm.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    # Placeholder: colored rounded rect with initials
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    bg = _stable_color_from_key(key)
    fg = QColor("#ffffff")

    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(bg))
    radius = int(size * 0.18)
    painter.drawRoundedRect(0, 0, size, size, radius, radius)

    # Text
    txt = _initials(name)
    f = QFont()
    f.setBold(True)
    f.setPointSize(int(size * 0.36))
    painter.setFont(f)
    painter.setPen(QPen(fg))
    painter.drawText(0, 0, size, size, Qt.AlignCenter, txt)

    painter.end()
    return pm


def get_upgrade_icon(up, size: int = 28) -> Optional[QPixmap]:
    # Only set icons for building category by default
    try:
        cat = up.category if hasattr(up, "category") else None
        if cat != "buildings":
            return None
        key = up.key
        name = up.name
        # If it's a milestone, show the base building's icon with a small badge
        m_key = getattr(up.definition, "milestone_key", None)
        base_key = m_key or key
        source_path = f"assets/icons/buildings/{base_key}.png"
        pm = get_building_icon(base_key, name, size=size, source_path=source_path)

        if m_key:
            # Add a small golden star badge
            painter = QPainter(pm)
            painter.setRenderHint(QPainter.Antialiasing)
            r = max(10, int(size * 0.36))
            cx = size - int(r * 0.6)
            cy = int(r * 0.6)
            badge_bg = QColor("#f6c445")
            painter.setBrush(QBrush(badge_bg))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(cx, cy), r // 2, r // 2)
            # Draw star glyph
            star = "★"
            pen = QPen(QColor("#553b00"))
            painter.setPen(pen)
            f = QFont()
            f.setBold(True)
            f.setPointSize(int(r * 0.6))
            painter.setFont(f)
            painter.drawText(cx - r // 2, cy - r // 2, r, r, Qt.AlignCenter, star)
            painter.end()

        return pm
    except Exception:
        return None

