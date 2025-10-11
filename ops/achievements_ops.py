from __future__ import annotations

from typing import List

from core.achievements import ACHIEVEMENTS, AchvDef


def list_achievements(game) -> List[dict]:
    out: List[dict] = []
    for a in ACHIEVEMENTS:
        cur = _achievement_value(game, a)
        stages = a.stages or []
        rewards = a.stage_rewards or []
        if stages and rewards and len(stages) == len(rewards):
            # Show only the next unclaimed stage; when claimed, the next becomes active
            next_idx = None
            for i in range(len(stages)):
                key_i = f"{a.key}:{i+1}"
                if not game.achievements_claimed.get(key_i, False):
                    next_idx = i
                    break
            if next_idx is None:
                # all stages claimed; skip listing to keep UI clean
                continue
            tgt = stages[next_idx]
            key = f"{a.key}:{next_idx+1}"
            name = a.name if next_idx == 0 else f"{a.name} {next_idx+1}"
            out.append({
                "key": key,
                "name": name,
                "desc": a.desc,
                "category": a.category,
                "current": cur,
                "target": tgt,
                "done": cur >= tgt,
                "claimed": bool(game.achievements_claimed.get(key, False)),
                "seen": bool(game.achievements_seen.get(key, False)),
                "reward": rewards[next_idx],
            })
        else:
            out.append({
                "key": a.key,
                "name": a.name,
                "desc": a.desc,
                "category": a.category,
                "current": cur,
                "target": a.target,
                "done": cur >= a.target,
                "claimed": bool(game.achievements_claimed.get(a.key, False)),
                "seen": bool(game.achievements_seen.get(a.key, False)),
                "reward": a.reward_diamonds,
            })
    return out


def claim_achievement(game, key: str) -> bool:
    # Supports stage keys like "builder:1"
    if game.achievements_claimed.get(key, False):
        return False
    # Find definition and stage if applicable
    base_key = key.split(":")[0]
    stage_idx = None
    if ":" in key:
        try:
            stage_idx = int(key.split(":")[1]) - 1
        except Exception:
            stage_idx = None
    a = next((x for x in ACHIEVEMENTS if x.key == base_key), None)
    if not a:
        return False
    target = a.target
    reward = a.reward_diamonds
    if stage_idx is not None and a.stages and a.stage_rewards and 0 <= stage_idx < len(a.stages):
        target = a.stages[stage_idx]
        reward = a.stage_rewards[stage_idx]
    if _achievement_value(game, a) < target:
        return False
    game.achievements_claimed[key] = True
    game.diamonds += reward
    return True


def mark_achievements_seen(game) -> None:
    for a in list_achievements(game):
        if a["done"] and not a["claimed"]:
            game.achievements_seen[a["key"]] = True


def _achievement_value(game, a: AchvDef) -> float:
    t = a.type
    if t == "lifetime_gold":
        return float(game.lifetime_gold)
    if t == "buildings_owned_total":
        total = 0
        for u in game.upgrades:
            if u.category == "buildings" and not getattr(u.definition, "milestone_key", None):
                total += u.level
        return float(total)
    if t == "scrap_total":
        return float(game.scrap)
    if t == "scrap_idle_rate":
        return float(game.scrap_idle)
    if t == "unlock_slots":
        return 1.0 if game.slots_unlocked else 0.0
    if t == "unlock_roulette":
        return 1.0 if game.roulette_unlocked else 0.0
    if t == "crates_basic":
        return float(game.crates_opened.get("basic", 0))
    if t == "crates_advanced":
        return float(game.crates_opened.get("advanced", 0))
    if t == "dice_plays":
        return float(game.counter_dice_plays)
    if t == "slots_spins":
        return float(game.counter_slots_spins)
    if t == "slots_wins":
        return float(game.counter_slots_wins)
    if t == "roulette_spins":
        return float(game.counter_roulette_spins)
    if t == "roulette_wins":
        return float(game.counter_roulette_wins)
    if t == "have_legendary":
        # Determine if inventory has at least one legendary
        try:
            count = 0
            for d in game.inventory:
                tmpl = game._templates.get(d.template_key)
                if tmpl and tmpl.rarity == "Legendary":
                    count += 1
            return float(count)
        except Exception:
            return 0.0
    if t == "shards_total":
        return float(game.shards)
    if t == "crates_total":
        return float(sum(game.crates_opened.values()))
    if t == "inventory_size":
        return float(len(game.inventory))
    if t == "idle_gold_ps":
        g = 0.0
        g += game.slots_passive_income
        g += game.roulette_passive_income
        g += game.buildings_passive_income
        g += game.dice_idle_income
        return float(g)
    return 0.0
