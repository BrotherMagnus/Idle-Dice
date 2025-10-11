from __future__ import annotations

from typing import Any


def game_to_dict(game) -> dict[str, Any]:
    return {
        "version": game.SAVE_VERSION if hasattr(game, 'SAVE_VERSION') else 0,
        "gold": game.gold,
        "lifetime_gold": game.lifetime_gold,
        "diamonds": game.diamonds,
        "shards": game.shards,
        "scrap": game.scrap,
        "scrap_idle": game.scrap_idle,
        "base_dice": game.base_dice,
        "slots_unlocked": game.slots_unlocked,
        "roulette_unlocked": game.roulette_unlocked,
        "upgrades": [{"key": u.key, "level": u.level} for u in game.upgrades],
        "inv": [
            {
                "uid": d.uid,
                "template_key": d.template_key,
                "level": d.level,
                "stars": getattr(d, 'stars', 0),
            }
            for d in game.inventory
        ],
        "next_uid": game._next_uid,
        "loadout": game.loadout,
        "crates_basic_no_rare": game.crates_basic_no_rare,
        "crates_opened": game.crates_opened,
        "achievements_claimed": game.achievements_claimed,
        "achievements_seen": game.achievements_seen,
        "counter_dice_plays": game.counter_dice_plays,
        "counter_slots_spins": game.counter_slots_spins,
        "counter_slots_wins": game.counter_slots_wins,
        "counter_roulette_spins": game.counter_roulette_spins,
        "counter_roulette_wins": game.counter_roulette_wins,
        # legacy bounty fields retained for backward compatibility
        "bounties_daily_claimed": getattr(game, 'bounties_daily_claimed', {}),
        "bounties_weekly_claimed": getattr(game, 'bounties_weekly_claimed', {}),
        "bounties_daily_reset_at": getattr(game, 'bounties_daily_reset_at', 0),
        "bounties_weekly_reset_at": getattr(game, 'bounties_weekly_reset_at', 0),
        # new bounty manager state
        "bounties_v2": game.bounties.to_dict() if hasattr(game, 'bounties') else {},
        # shop purchases
        "shop_levels": getattr(game, 'shop_levels', {}),
    }


def game_from_dict(game, data: dict[str, Any]) -> None:
    from core.dice_models import DiceInstance  # local import to avoid cycles

    game.gold = float(data.get("gold", 0.0))
    game.lifetime_gold = float(data.get("lifetime_gold", 0.0))
    game.diamonds = int(data.get("diamonds", 0))
    game.shards = float(data.get("shards", 0.0))
    game.scrap = float(data.get("scrap", 0.0))
    game.scrap_idle = float(data.get("scrap_idle", 0.0))
    game.base_dice = int(data.get("base_dice", 1))
    game.slots_unlocked = bool(data.get("slots_unlocked", False))
    game.roulette_unlocked = bool(data.get("roulette_unlocked", False))

    saved_lvls = {rec.get("key"): int(rec.get("level", 0)) for rec in data.get("upgrades", [])}
    for u in game.upgrades:
        if u.key in saved_lvls:
            u.level = saved_lvls[u.key]

    game.inventory.clear()
    for rec in data.get("inv", []):
        game.inventory.append(
            DiceInstance(
                uid=int(rec["uid"]),
                template_key=rec["template_key"],
                level=int(rec.get("level", 1)),
                stars=int(rec.get("stars", 0)),
            )
        )
    game._next_uid = int(data.get("next_uid", len(game.inventory) + 1))
    ld = data.get("loadout", [0, 0, 0, 0, 0])
    game.loadout = [int(x) for x in (ld + [0, 0, 0, 0, 0])[:5]]

    # crates / achievements
    game.crates_basic_no_rare = int(data.get("crates_basic_no_rare", 0))
    try:
        co = data.get("crates_opened", {})
        game.crates_opened = {k: int(v) for k, v in co.items()}
    except Exception:
        game.crates_opened = {"basic": 0, "advanced": 0, "rare": 0, "legendary": 0}
    try:
        ach = data.get("achievements_claimed", {})
        game.achievements_claimed = {str(k): bool(v) for k, v in ach.items()}
    except Exception:
        game.achievements_claimed = {}
    try:
        seen = data.get("achievements_seen", {})
        game.achievements_seen = {str(k): bool(v) for k, v in seen.items()}
    except Exception:
        game.achievements_seen = {}

    # counters
    game.counter_dice_plays = int(data.get("counter_dice_plays", 0))
    game.counter_slots_spins = int(data.get("counter_slots_spins", 0))
    game.counter_slots_wins = int(data.get("counter_slots_wins", 0))
    game.counter_roulette_spins = int(data.get("counter_roulette_spins", 0))
    game.counter_roulette_wins = int(data.get("counter_roulette_wins", 0))

    # bounties: prefer new manager state, fall back to legacy
    try:
        b2 = data.get("bounties_v2")
        if isinstance(b2, dict):
            game.bounties.from_dict(b2)
        else:
            game.bounties_daily_claimed = {str(k): bool(v) for k, v in data.get("bounties_daily_claimed", {}).items()} if isinstance(data.get("bounties_daily_claimed", {}), dict) else {}
            game.bounties_weekly_claimed = {str(k): bool(v) for k, v in data.get("bounties_weekly_claimed", {}).items()} if isinstance(data.get("bounties_weekly_claimed", {}), dict) else {}
            game.bounties_daily_reset_at = int(data.get("bounties_daily_reset_at", 0)) or 0
            game.bounties_weekly_reset_at = int(data.get("bounties_weekly_reset_at", 0)) or 0
            game.bounties.daily_claimed = dict(game.bounties_daily_claimed)
            game.bounties.weekly_claimed = dict(game.bounties_weekly_claimed)
            game.bounties.daily_reset_at = game.bounties_daily_reset_at
            game.bounties.weekly_reset_at = game.bounties_weekly_reset_at
    except Exception:
        pass

    # shop
    try:
        sl = data.get("shop_levels", {}) or {}
        if isinstance(sl, dict):
            game.shop_levels = {str(k): int(v) for k, v in sl.items()}
    except Exception:
        game.shop_levels = {}
