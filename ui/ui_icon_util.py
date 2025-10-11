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


# ---------- Dice icons with star overlays ----------
def dice_icon_with_stars(image_path: Optional[str], size: int, stars: int = 0, label_text: Optional[str] = None) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)

    base = None
    if image_path:
        base = QPixmap(image_path)
        if not base.isNull():
            base = base.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)

    if base and not base.isNull():
        # center the base icon
        x = (size - base.width()) // 2
        y = (size - base.height()) // 2
        painter.drawPixmap(x, y, base)
    else:
        # simple placeholder if no image with contrasting color + label
        painter.setPen(Qt.NoPen)
        bg = _stable_color_from_key(label_text or "dice")
        painter.setBrush(QBrush(bg))
        r = int(size * 0.18)
        painter.drawRoundedRect(0, 0, size, size, r, r)
        # label text (e.g., d8)
        if label_text:
            painter.setPen(QPen(QColor("#ffffff")))
            f = QFont(); f.setBold(True); f.setPointSize(int(size * 0.33))
            painter.setFont(f)
            painter.drawText(0, 0, size, size, Qt.AlignCenter, label_text)

    if stars and stars > 0:
        # Badge at bottom-right with count
        is_red = stars > 5
        bg = QColor("#ff5555" if is_red else "#ffca6b")
        fg = QColor("#1b1d3e")
        pad = int(size * 0.06)
        h = int(size * 0.32)
        w = int(size * 0.52)
        x = size - w - pad
        y = size - h - pad
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(x, y, w, h, int(h*0.35), int(h*0.35))
        # text
        painter.setPen(QPen(fg))
        f = QFont()
        f.setBold(True)
        f.setPointSize(max(8, int(h * 0.45)))
        painter.setFont(f)
        painter.drawText(x, y, w, h, Qt.AlignCenter, f"★{stars}")

    painter.end()
    return pm


def dice_icon_with_badges(image_path: Optional[str], size: int, *, stars: int = 0, level: Optional[int] = None, label_text: Optional[str] = None) -> QPixmap:
    """Extended icon renderer that supports both star and level badges.
    - Stars badge bottom-right (gold 1-5, red 6-10)
    - Level badge top-left (blue by default; black when level >= 100 to indicate prestige-ready)
    - label_text draws center text on placeholder (e.g., d8)
    """
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    base = None
    if image_path:
        base = QPixmap(image_path)
        if not base.isNull():
            base = base.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)

    # draw base
    if base and not base.isNull():
        x = (size - base.width()) // 2
        y = (size - base.height()) // 2
        painter.drawPixmap(x, y, base)
    else:
        painter.setPen(Qt.NoPen)
        bg = _stable_color_from_key(label_text or "dice")
        painter.setBrush(QBrush(bg))
        r = int(size * 0.18)
        painter.drawRoundedRect(0, 0, size, size, r, r)
        if label_text:
            painter.setPen(QPen(QColor("#ffffff")))
            f = QFont(); f.setBold(True); f.setPointSize(int(size * 0.33))
            painter.setFont(f)
            painter.drawText(0, 0, size, size, Qt.AlignCenter, label_text)

    # Stars badge (bottom-right)
    if stars and stars > 0:
        is_red = stars > 5
        bg = QColor("#ff5555" if is_red else "#ffca6b")
        fg = QColor("#1b1d3e")
        pad = int(size * 0.06)
        h = int(size * 0.32)
        w = int(size * 0.52)
        x = size - w - pad
        y = size - h - pad
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(x, y, w, h, int(h*0.35), int(h*0.35))
        painter.setPen(QPen(fg))
        f = QFont(); f.setBold(True); f.setPointSize(max(8, int(h * 0.45)))
        painter.setFont(f)
        painter.drawText(x, y, w, h, Qt.AlignCenter, f"★{stars}")

    # Level badge (top-left)
    if level is not None:
        pad = int(size * 0.06)
        h = int(size * 0.30)
        w = int(size * 0.58)
        x = pad
        y = pad
        bg = QColor("#000000") if level >= 100 else QColor("#2b6be3")
        fg = QColor("#ffffff")
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(x, y, w, h, int(h*0.35), int(h*0.35))
        painter.setPen(QPen(fg))
        f = QFont(); f.setBold(True); f.setPointSize(max(8, int(h * 0.45)))
        painter.setFont(f)
        painter.drawText(x, y, w, h, Qt.AlignCenter, f"Lv {level}")

    painter.end()
    return pm
