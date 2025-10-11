from __future__ import annotations

from typing import Dict, List

from core.dice_models import DiceTemplate, SetBonusTier


def compute_set_counts(game) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for t in game.get_loadout_templates():
        counts[t.set_key] = counts.get(t.set_key, 0) + 1
    return counts


def active_set_tiers(game) -> List[SetBonusTier]:
    tiers: List[SetBonusTier] = []
    counts = compute_set_counts(game)
    for set_key, cnt in counts.items():
        s = game._sets.get(set_key)
        if not s:
            continue
        for tier in s.tiers:
            if cnt >= tier.pieces:
                tiers.append(tier)
    return tiers


def team_totals_with_bonuses(game) -> Dict[str, int]:
    base = {"hp": 0, "atk": 0, "defense": 0, "speed": 0}
    for t in game.get_loadout_templates():
        base["hp"] += t.hp
        base["atk"] += t.atk
        base["defense"] += t.defense
        base["speed"] += t.speed

    flat_add = {"hp": 0, "atk": 0, "defense": 0, "speed": 0}
    pct_add = {"hp": 0.0, "atk": 0.0, "defense": 0.0, "speed": 0.0}
    allowed = set(flat_add.keys())
    for tier in active_set_tiers(game):
        for stat, kind, amt in tier.bonuses:
            if stat not in allowed:
                continue
            if kind == "flat":
                flat_add[stat] += amt
            else:
                pct_add[stat] += amt

    final: Dict[str, int] = {}
    for stat in base.keys():
        val = base[stat] + flat_add[stat]
        val = int(round(val * (1 + pct_add[stat] / 100.0)))
        final[stat] = val
    return final
