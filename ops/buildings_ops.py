from __future__ import annotations

from typing import List, Dict


def get_building_cards(game) -> List[Dict]:
    out = []
    per_unit_bonus: dict[str, float] = {}
    for u in game.upgrades:
        if u.category != "buildings":
            continue
        m_key = getattr(u.definition, "milestone_key", None)
        if m_key:
            per_unit_bonus[m_key] = per_unit_bonus.get(m_key, 0.0) + (u.level * u.building_gold_ps)

    for idx, u in enumerate(game.upgrades):
        if u.category != "buildings":
            continue
        if getattr(u.definition, "milestone_key", None):
            continue
        # Re-evaluate locked state to avoid stale flags
        is_locked = False
        if getattr(u, 'reveal_after_key', None):
            req = game._get_by_key(u.reveal_after_key)
            if not (req and req.level >= u.reveal_after_level):
                is_locked = True
        m_key = getattr(u, 'milestone_key', None)
        m_lvl = getattr(u, 'milestone_level', 0)
        if m_key and m_lvl:
            base = game._get_by_key(m_key)
            if not (base and base.level >= m_lvl):
                is_locked = True
        icon_path = f"assets/icons/buildings/{u.key}.png"
        order = idx
        if u.building_gold_ps > 0:
            per_unit = u.building_gold_ps + per_unit_bonus.get(u.key, 0.0)
            total = per_unit * u.level
            rec = {
                "key": u.key,
                "name": u.name,
                "level": u.level,
                "icon": icon_path,
                "type": "gold",
                "per_unit": per_unit,
                "total": total,
                "order": order,
                "cost": u.cost(),
                "can_buy": game.can_buy(u),
                "locked": is_locked,
            }
            if is_locked and u.reveal_after_key:
                req = game._get_by_key(u.reveal_after_key)
                cur = req.level if req else 0
                name = req.name if req else u.reveal_after_key
                rec["requires"] = f"Requires {u.reveal_after_level} {name} (owned: {cur})"
            out.append(rec)
        elif u.shards_passive > 0:
            per_unit = u.shards_passive
            total = per_unit * u.level
            rec = {
                "key": u.key,
                "name": u.name,
                "level": u.level,
                "icon": icon_path,
                "type": "shards",
                "per_unit": per_unit,
                "total": total,
                "order": order,
                "cost": u.cost(),
                "can_buy": game.can_buy(u),
                "locked": is_locked,
            }
            if is_locked and u.reveal_after_key:
                req = game._get_by_key(u.reveal_after_key)
                cur = req.level if req else 0
                name = req.name if req else u.reveal_after_key
                rec["requires"] = f"Requires {u.reveal_after_level} {name} (owned: {cur})"
            out.append(rec)

    out.sort(key=lambda d: (d.get("order", 0)))
    return out
