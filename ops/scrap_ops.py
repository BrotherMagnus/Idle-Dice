from __future__ import annotations

import random


def salvage(game, cost: int, quality_mult: float | None = None) -> tuple[float, int]:
    eff_cost = int(round(cost * (1.0 - getattr(game, 'salvage_cost_discount_total', 0.0))))
    if eff_cost < 1:
        eff_cost = 1
    if cost <= 0 or game.gold < eff_cost:
        return 0.0, 0
    game.gold -= eff_cost
    base = cost * 0.001
    mult = float(quality_mult) if quality_mult is not None else random.uniform(0.5, 1.5)
    scrap_won = base * mult
    if quality_mult is None and random.random() < 0.01:
        scrap_won *= 10
    diamonds_won = 0
    if random.random() < 0.002:
        diamonds_won = 1
    scrap_won *= getattr(game, 'salvage_yield_mult_total', 1.0)
    game.scrap += scrap_won
    game.diamonds += diamonds_won
    return scrap_won, diamonds_won


def convert_scrap_to_shards(game, scrap_amount: int) -> float:
    if scrap_amount <= 0 or game.scrap < scrap_amount:
        return 0.0
    game.scrap -= scrap_amount
    shards_gained = (scrap_amount / 10.0) * getattr(game, 'shards_rate_mult', 1.0)
    game.shards += shards_gained
    return shards_gained


def open_scrap_crate(game, tier: str):
    tier = (tier or "basic").lower()
    costs = {"basic": 1000, "advanced": 10000, "rare": 25000, "legendary": 100000}
    weights_by_tier = {
        "basic":    {"Common": 0.82, "Uncommon": 0.16, "Rare": 0.018, "Legendary": 0.002},
        "advanced": {"Common": 0.50, "Uncommon": 0.35, "Rare": 0.12,  "Legendary": 0.03},
        "rare":     {"Common": 0.00, "Uncommon": 0.00, "Rare": 0.85,  "Legendary": 0.15},
        "legendary": {"Common": 0.00, "Uncommon": 0.00, "Rare": 0.10, "Legendary": 0.90},
    }
    cost = costs.get(tier, 1000)
    if game.scrap < cost:
        return None
    game.scrap -= cost

    weights = weights_by_tier.get(tier, weights_by_tier["basic"]).copy()
    buckets: dict[str, list[str]] = {}
    for t in game._templates.values():
        buckets.setdefault(t.rarity, []).append(t.key)
    rarities = [r for r in ("Common", "Uncommon", "Rare", "Legendary") if r in buckets]
    probs = [weights.get(r, 0.0) for r in rarities]
    total = sum(probs) or 1.0
    probs = [p/total for p in probs]
    chosen_r = rarities[-1]
    PITY_BASIC_THRESHOLD = 20
    if tier == "basic" and game.crates_basic_no_rare >= PITY_BASIC_THRESHOLD - 1 and "Rare" in rarities:
        chosen_r = "Rare"
    else:
        r = random.random(); acc = 0.0
        for rarity, p in zip(rarities, probs):
            acc += p
            if r <= acc:
                chosen_r = rarity; break
    pool = buckets[chosen_r]
    key = random.choice(pool)
    inst = game.add_dice(key)
    game._post_crate_open(tier, chosen_r)
    return inst

