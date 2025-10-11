from __future__ import annotations

from core.dice_models import DiceTemplate


def level_multiplier(level: int) -> float:
    if level <= 1:
        return 1.0
    base = 1.0 + 0.02 * (level - 1)  # +2% per level
    tiers = (level - 1) // 10
    tier_mult = 1.50 ** tiers  # big milestone boosts every 10
    return base * tier_mult


def apply_stars(t: DiceTemplate, stars: int) -> DiceTemplate:
    if not stars or stars <= 0:
        return t
    gold = min(stars, 5)
    red = max(0, stars - 5)
    mult = (1.0 + 0.05 * gold) * (1.0 + 0.10 * red)
    if mult > 3.0:
        mult = 3.0
    return DiceTemplate(
        key=t.key,
        name=t.name,
        set_key=t.set_key,
        set_name=t.set_name,
        rarity=t.rarity,
        sides=t.sides,
        hp=int(round(t.hp * mult)),
        atk=int(round(t.atk * mult)),
        defense=int(round(t.defense * mult)),
        speed=int(round(t.speed * mult)),
        crit_chance_pct=t.crit_chance_pct,
        crit_mult=t.crit_mult,
        gold_mult_pct=round(t.gold_mult_pct * mult, 2),
        idle_gold_ps=round(t.idle_gold_ps * mult, 2),
        slots_mult_pct=round(t.slots_mult_pct * mult, 2),
        roulette_mult_pct=round(t.roulette_mult_pct * mult, 2),
        shard_rate_mult_pct=round(t.shard_rate_mult_pct * mult, 2),
    )


def apply_stars_and_level(t: DiceTemplate, stars: int, level: int) -> DiceTemplate:
    base = apply_stars(t, stars)
    if level <= 1:
        return base
    mult = level_multiplier(level)
    if mult > 8.0:
        mult = 8.0
    rarity_scale_combat = {
        "Common": 1.00,
        "Uncommon": 1.10,
        "Rare": 1.25,
        "Legendary": 1.50,
    }.get(base.rarity, 1.0)
    rarity_scale_econ = {
        "Common": 1.00,
        "Uncommon": 1.15,
        "Rare": 1.40,
        "Legendary": 1.80,
    }.get(base.rarity, 1.0)
    mult *= rarity_scale_combat
    tiers = (level - 1) // 10
    econ_extra = (1.0 + 0.01 * (level - 1)) * (1.25 ** tiers) * rarity_scale_econ
    return DiceTemplate(
        key=base.key,
        name=base.name,
        set_key=base.set_key,
        set_name=base.set_name,
        rarity=base.rarity,
        sides=base.sides,
        hp=int(round(base.hp * mult)),
        atk=int(round(base.atk * mult)),
        defense=int(round(base.defense * mult)),
        speed=int(round(base.speed * mult)),
        crit_chance_pct=base.crit_chance_pct,
        crit_mult=base.crit_mult,
        gold_mult_pct=round(base.gold_mult_pct * mult * econ_extra, 2),
        idle_gold_ps=round(base.idle_gold_ps * mult * econ_extra, 2),
        slots_mult_pct=round(base.slots_mult_pct * mult * econ_extra, 2),
        roulette_mult_pct=round(base.roulette_mult_pct * mult * econ_extra, 2),
        shard_rate_mult_pct=round(base.shard_rate_mult_pct * mult * econ_extra, 2),
    )


def level_costs(level: int) -> tuple[int, int]:
    """Return (shards_cost, scrap_cost) for next level from given level."""
    next_lvl = int(level) + 1
    shards = 5 * (next_lvl ** 2)
    scrap = 100 * next_lvl if next_lvl % 10 == 0 else 0
    return shards, scrap
