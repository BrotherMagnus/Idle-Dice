from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import random


Currency = str  # 'gold' | 'scrap' | 'diamonds' | 'shards'


@dataclass(frozen=True)
class ShopItem:
    key: str
    name: str
    category: str  # 'Crates' | 'Upgrades' | 'Packs'
    currency: Currency
    price: int
    description: str
    # optional: for upgrades
    max_level: int = 0
    order: int = 0  # used to order items within a tab


class Shop:
    """Static catalog and purchase helpers.
    Game-specific effects are applied via helper functions below.
    """

    # Diamond crate definitions (rarity weights)
    DIAMOND_CRATE_WEIGHTS: Dict[str, Dict[str, float]] = {
        # premium crates paid with diamonds
        'rare':       {"Rare": 0.90,  "Legendary": 0.10},
        'legendary':  {"Rare": 0.10,  "Legendary": 0.90},
        'prismatic':  {"Rare": 0.25,  "Legendary": 0.75},
    }

    @staticmethod
    def catalog() -> Dict[str, ShopItem]:
        return {
            # ----- Crates (Scrap) -----
            'crate_scrap_basic':      ShopItem('crate_scrap_basic',     'Scrap Crate — Basic',      'Crates',  'scrap',    1_000,  'Basic scrap crate with mostly Common/Uncommon drops.', order=10),
            'crate_scrap_advanced':   ShopItem('crate_scrap_advanced',  'Scrap Crate — Advanced',   'Crates',  'scrap',   10_000,  'Better odds for Rare; small Legendary chance.',        order=11),
            'crate_scrap_rare':       ShopItem('crate_scrap_rare',      'Scrap Crate — Rare',       'Crates',  'scrap',   25_000,  'Guaranteed Rare+, with a chance at Legendary.',        order=12),
            'crate_scrap_legendary':  ShopItem('crate_scrap_legendary', 'Scrap Crate — Legendary',  'Crates',  'scrap',  100_000,  'High chance of Legendary dice.',                      order=13),

            # ----- Crates (Diamonds) -----
            'crate_dia_rare':         ShopItem('crate_dia_rare',        'Diamond Crate — Rare',     'Premium', 'diamonds',      15,  'Premium crate: Mostly Rare with some Legendary.',     order=20),
            'crate_dia_prismatic':    ShopItem('crate_dia_prismatic',   'Diamond Crate — Prismatic','Premium', 'diamonds',      35,  'Premium crate: Weighted to Legendary.',               order=21),
            'crate_dia_legendary':    ShopItem('crate_dia_legendary',   'Diamond Crate — Legendary','Premium', 'diamonds',      60,  'Premium crate: Mostly Legendary rolls.',              order=22),

            # ----- Permanent Upgrades (Diamonds) -----
            'perm_gold_booster':      ShopItem('perm_gold_booster',     'Gold Booster (+5%)',       'Upgrades','diamonds',      20,  'Permanent +5% global gold income. Stacks.', max_level=20, order=100),
            'perm_shard_rate':        ShopItem('perm_shard_rate',       'Shard Rate (+10%)',        'Upgrades','diamonds',      30,  'Permanent +10% shard conversion rate. Stacks.', max_level=15, order=101),
            'perm_salvage_yield':     ShopItem('perm_salvage_yield',    'Salvage Yield (+10%)',     'Upgrades','diamonds',      18,  'Permanent +10% salvage yield. Stacks.', max_level=20, order=102),
        }


def list_items(game) -> List[dict]:
    cat = Shop.catalog()
    out: List[dict] = []
    for k, item in cat.items():
        entry = {
            'key': k,
            'name': item.name,
            'category': item.category,
            'currency': item.currency,
            'price': item.price,
            'description': item.description,
            'order': item.order,
        }
        if item.max_level:
            lvl = int(getattr(game, 'shop_levels', {}).get(k, 0))
            entry['level'] = lvl
            entry['max_level'] = item.max_level
            entry['owned_out'] = (lvl >= item.max_level)
        out.append(entry)
    # sort by category then our explicit order, then name
    out.sort(key=lambda x: (x['category'], x.get('order', 0), x['name']))
    return out


def item_details(game, key: str) -> dict:
    """Return extended details for UI: odds and loot pool size for crates."""
    cat = Shop.catalog()
    item = cat.get(key)
    out = {'key': key}
    if not item:
        return out
    out['name'] = item.name
    out['description'] = item.description
    # crate odds
    if key.startswith('crate_scrap_'):
        tier = key.split('_')[-1]
        weights_by_tier = {
            "basic":    {"Common": 0.82, "Uncommon": 0.16, "Rare": 0.018, "Legendary": 0.002},
            "advanced": {"Common": 0.50, "Uncommon": 0.35, "Rare": 0.12,  "Legendary": 0.03},
            "rare":     {"Common": 0.00, "Uncommon": 0.00, "Rare": 0.85,  "Legendary": 0.15},
            "legendary": {"Common": 0.00, "Uncommon": 0.00, "Rare": 0.10, "Legendary": 0.90},
        }
        weights = weights_by_tier.get(tier, {})
        total = sum(weights.values()) or 1.0
        out['odds'] = {r: round(100.0 * (w/total), 1) for r, w in weights.items() if w > 0}
    elif key.startswith('crate_dia_'):
        t = key.split('_')[-1]
        weights = Shop.DIAMOND_CRATE_WEIGHTS.get(t, {})
        total = sum(weights.values()) or 1.0
        out['odds'] = {r: round(100.0 * (w/total), 1) for r, w in weights.items() if w > 0}
    # pool counts and sample examples of possible drops
    try:
        buckets_count: Dict[str, int] = {}
        buckets_names: Dict[str, List[str]] = {}
        for tmpl in game._templates.values():
            buckets_count[tmpl.rarity] = buckets_count.get(tmpl.rarity, 0) + 1
            buckets_names.setdefault(tmpl.rarity, []).append(tmpl.name)
        out['pool_counts'] = buckets_count
        # Select up to 3 example names per rarity present in odds
        ex: Dict[str, List[str]] = {}
        for r in sorted(buckets_names.keys()):
            names = sorted(buckets_names[r])
            ex[r] = names[:3]
        out['examples'] = ex
    except Exception:
        pass
    return out


def _spend(game, currency: Currency, amount: int) -> bool:
    if amount <= 0:
        return True
    if currency == 'gold':
        if game.gold < amount: return False
        game.gold -= amount; return True
    if currency == 'scrap':
        if game.scrap < amount: return False
        game.scrap -= amount; return True
    if currency == 'diamonds':
        if game.diamonds < amount: return False
        game.diamonds -= amount; return True
    if currency == 'shards':
        if game.shards < amount: return False
        game.shards -= amount; return True
    return False


def _open_crate_by_weights(game, weights: Dict[str, float]) -> Optional[object]:
    """Helper: choose a rarity from weights and add a random dice of that rarity.
    Returns the newly created DiceInstance.
    """
    buckets: Dict[str, list[str]] = {}
    for t in game._templates.values():
        buckets.setdefault(t.rarity, []).append(t.key)
    rarities = [r for r in ("Common", "Uncommon", "Rare", "Legendary") if r in buckets and weights.get(r, 0.0) > 0]
    if not rarities:
        return None
    probs = [weights.get(r, 0.0) for r in rarities]
    total = sum(probs) or 1.0
    probs = [p/total for p in probs]
    r = random.random(); acc = 0.0
    chosen_r = rarities[-1]
    for rr, p in zip(rarities, probs):
        acc += p
        if r <= acc:
            chosen_r = rr; break
    key = random.choice(buckets[chosen_r])
    return game.add_dice(key)


def purchase(game, key: str) -> Optional[object]:
    """Attempt to purchase an item; returns a payload (e.g., DiceInstance) or None.
    On failure (insufficient currency or capped), returns None.
    """
    cat = Shop.catalog()
    item = cat.get(key)
    if not item:
        return None
    # check upgrade cap
    if item.max_level:
        lvl = int(getattr(game, 'shop_levels', {}).get(key, 0))
        if lvl >= item.max_level:
            return None
    # spend
    if not _spend(game, item.currency, item.price):
        return None

    # Apply effect
    if key.startswith('crate_scrap_'):
        # Handled by existing crate system via scrap already spent here? No, we spend via shop so open free.
        tier = key.split('_')[-1]
        # Use scrap odds, but no extra scrap cost (we already charged currency)
        from .scrap_ops import open_scrap_crate
        # Temporarily grant scrap for the crate cost then call open then subtract; to avoid code duplication,
        # we directly mimic selection using the same weights table by calling internal helper when possible.
        # Simpler: call open_scrap_crate by ensuring enough scrap, fund it, then deduct back.
        # But simpler still is to reimplement odds here:
        weights_by_tier = {
            "basic":    {"Common": 0.82, "Uncommon": 0.16, "Rare": 0.018, "Legendary": 0.002},
            "advanced": {"Common": 0.50, "Uncommon": 0.35, "Rare": 0.12,  "Legendary": 0.03},
            "rare":     {"Common": 0.00, "Uncommon": 0.00, "Rare": 0.85,  "Legendary": 0.15},
            "legendary": {"Common": 0.00, "Uncommon": 0.00, "Rare": 0.10, "Legendary": 0.90},
        }
        weights = weights_by_tier.get(tier, weights_by_tier['basic'])
        inst = _open_crate_by_weights(game, weights)
        if inst:
            game._post_crate_open(tier, 'Legendary')  # rarity not needed downstream beyond pity counter; set placeholder
        return inst

    if key.startswith('crate_dia_'):
        t = key.split('_')[-1]
        weights = Shop.DIAMOND_CRATE_WEIGHTS.get(t)
        if not weights:
            return None
        inst = _open_crate_by_weights(game, weights)
        if inst:
            tier_map = {'rare': 'rare', 'legendary': 'legendary', 'prismatic': 'legendary'}
            game._post_crate_open(tier_map.get(t, 'rare'), 'Legendary')
        return inst

    # Permanent upgrades
    levels = getattr(game, 'shop_levels', {})
    cur = int(levels.get(key, 0))
    levels[key] = cur + 1
    game.shop_levels = levels
    # trigger stat recompute in caller
    return True
