from __future__ import annotations

from typing import Optional, List, Dict

from core.dice_models import DiceInstance


def grant_starter_if_empty(game) -> None:
    if not game.inventory:
        game.add_dice("wooden_d8")
        game.loadout[0] = game.inventory[0].uid
        game.on_loadout_changed()


def add_dice(game, template_key: str) -> DiceInstance:
    # Merge duplicates into star upgrades; overflow becomes scrap
    existing = next((d for d in game.inventory if d.template_key == template_key), None)
    if existing is not None:
        if existing.stars < 10:
            existing.stars += 1
            game.on_loadout_changed()
            return existing
        else:
            tmpl = game._templates.get(template_key)
            rarity = tmpl.rarity if tmpl else "Common"
            game.scrap += {"Common": 50, "Uncommon": 150, "Rare": 500, "Legendary": 2000}.get(rarity, 50)
            return existing
    inst = DiceInstance(uid=game._next_uid, template_key=template_key)
    game._next_uid += 1
    game.inventory.append(inst)
    return inst


def find_dice(game, uid: int) -> Optional[DiceInstance]:
    for d in game.inventory:
        if d.uid == uid:
            return d
    return None


def equip_first_empty(game, uid: int) -> bool:
    if not find_dice(game, uid):
        return False
    if uid in game.loadout:
        return True
    inst = find_dice(game, uid)
    if not inst:
        return False
    t_new = game._templates.get(inst.template_key)
    if not t_new:
        return False
    # Enforce unique sides in loadout
    sides_in_use = set()
    for u in game.loadout:
        if not u:
            continue
        inst2 = find_dice(game, u)
        if not inst2:
            continue
        t2 = game._templates.get(inst2.template_key)
        if t2:
            sides_in_use.add(t2.sides)
    if t_new.sides in sides_in_use:
        return False
    for i in range(len(game.loadout)):
        if game.loadout[i] == 0:
            game.loadout[i] = uid
            game.on_loadout_changed()
            return True
    return False


def equip_replace_or_empty(game, uid: int) -> bool:
    """Replace an equipped die that has the same number of sides; if none,
    equip to the next empty slot. Keeps the unique-sides rule intact.
    """
    inst = find_dice(game, uid)
    if not inst:
        return False
    t_new = game._templates.get(inst.template_key)
    if not t_new:
        return False
    # If already equipped, nothing to do
    if uid in game.loadout:
        return True
    # Try replace same-sides first
    replace_idx = -1
    for i, u in enumerate(game.loadout):
        if not u:
            continue
        cur = find_dice(game, u)
        if not cur:
            continue
        t_cur = game._templates.get(cur.template_key)
        if t_cur and t_cur.sides == t_new.sides:
            replace_idx = i
            break
    if replace_idx >= 0:
        game.loadout[replace_idx] = uid
        game.on_loadout_changed()
        return True
    # Else, fall back to equipping into an empty slot (will enforce unique sides)
    return equip_first_empty(game, uid)


def compact_loadout(game) -> None:
    filtered = [u for u in game.loadout if u]
    game.loadout = filtered + [0] * (6 - len(filtered))


def merge_duplicates(game) -> None:
    by_key: Dict[str, List[DiceInstance]] = {}
    for d in game.inventory:
        by_key.setdefault(d.template_key, []).append(d)

    changed = False
    for key, items in by_key.items():
        if len(items) <= 1:
            continue
        # Keep lowest uid
        items.sort(key=lambda x: x.uid)
        keep = items[0]
        dups = items[1:]
        add = len(dups)
        current = getattr(keep, 'stars', 0)
        new_total = current + add
        overflow = max(0, new_total - 10)
        keep.stars = min(10, new_total)

        if overflow > 0:
            tmpl = game._templates.get(key)
            rarity = tmpl.rarity if tmpl else "Common"
            scrap_map = {"Common": 50, "Uncommon": 150, "Rare": 500, "Legendary": 2000}
            game.scrap += scrap_map.get(rarity, 50) * overflow

        # Remove duplicates from inventory
        dup_uids = {d.uid for d in dups}
        if dup_uids:
            game.inventory = [d for d in game.inventory if d.uid not in dup_uids]
            changed = True

        # Update loadout: replace dup uids with keep.uid if not already present; otherwise clear slot
        already = keep.uid in game.loadout
        for i, u in enumerate(game.loadout):
            if u in dup_uids:
                game.loadout[i] = (keep.uid if not already else 0)
                already = True

    if changed:
        compact_loadout(game)
        game.on_loadout_changed()
