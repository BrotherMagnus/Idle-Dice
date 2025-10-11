# game.py
from __future__ import annotations
import random, json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, List, Dict

from core.upgrades import UpgradeDef, UPGRADES
from core.achievements import ACHIEVEMENTS, AchvDef
from ops.achievements_ops import (
    list_achievements as ach_list,
    claim_achievement as ach_claim,
    mark_achievements_seen as ach_mark_seen,
)
from core.dice_models import DiceInstance, get_templates, get_sets, DiceTemplate, SetBonusTier
# Delegated modules for separation of concerns
from ops.progression import (
    level_multiplier as prog_level_multiplier,
    apply_stars as prog_apply_stars,
    apply_stars_and_level as prog_apply_stars_and_level,
    level_costs as prog_level_costs,
)
from ops.buildings_ops import get_building_cards
from ops.scrap_ops import (
    salvage as scrap_salvage,
    convert_scrap_to_shards as scrap_convert_scrap_to_shards,
    open_scrap_crate as scrap_open_scrap_crate,
)
from ops.bounties import BountyManager
from ops.team_bonuses import (
    compute_set_counts as tb_compute_set_counts,
    active_set_tiers as tb_active_set_tiers,
    team_totals_with_bonuses as tb_team_totals,
)
from ops.inventory_ops import (
    grant_starter_if_empty as inv_grant_starter_if_empty,
    add_dice as inv_add_dice,
    find_dice as inv_find_dice,
    equip_first_empty as inv_equip_first_empty,
    equip_replace_or_empty as inv_equip_replace_or_empty,
    compact_loadout as inv_compact_loadout,
    merge_duplicates as inv_merge_duplicates,
)
from ops.casino_ops import (
    bet as casino_bet,
    spin_slots as casino_spin_slots,
)
from ops.persistence import (
    game_to_dict as persist_to_dict,
    game_from_dict as persist_from_dict,
)
from ops.shop_ops import list_items as shop_list_items, purchase as shop_purchase, item_details as shop_item_details

SAVE_VERSION = 11
DATA_DIR = Path(__file__).parent / "data"
LEGACY_SAVE = Path(__file__).with_name("savedata.json")
SAVE_PATH = DATA_DIR / "savedata.json"

@dataclass
class Upgrade:
    definition: UpgradeDef
    level: int = 0
    locked: bool = False
    disabled: bool = False

    @property
    def key(self): return self.definition.key
    @property
    def name(self): return self.definition.name
    @property
    def category(self): return self.definition.category
    @property
    def max_level(self): return self.definition.max_level

    # effects
    @property
    def dice_gain(self): return self.definition.dice_gain
    @property
    def animation_speed_mult(self): return self.definition.animation_speed_mult
    @property
    def die_sides_increase(self): return self.definition.die_sides_increase
    @property
    def slots_passive(self): return self.definition.slots_passive
    @property
    def global_gold_mult(self): return self.definition.global_gold_mult
    @property
    def roulette_payout_bonus(self): return self.definition.roulette_payout_bonus
    @property
    def roulette_maxbet_increase(self): return self.definition.roulette_maxbet_increase
    @property
    def roulette_passive(self): return self.definition.roulette_passive
    @property
    def building_gold_ps(self): return self.definition.building_gold_ps
    @property
    def shards_passive(self): return self.definition.shards_passive
    @property
    def scrap_passive(self): return self.definition.scrap_passive
    @property
    def salvage_yield_mult(self): return self.definition.salvage_yield_mult
    @property
    def salvage_cost_discount(self): return self.definition.salvage_cost_discount

    # gating
    @property
    def reveal_after_key(self): return self.definition.reveal_after_key
    @property
    def reveal_after_level(self): return self.definition.reveal_after_level
    @property
    def disabled_when_reached_level(self): return self.definition.disabled_when_reached_level
    @property
    def milestone_key(self): return self.definition.milestone_key
    @property
    def milestone_level(self): return self.definition.milestone_level

    def cost(self) -> int:
        return int(self.definition.base_cost * (self.definition.cost_multiplier ** self.level))

class Game:
    def __init__(self):
        # currencies
        self.gold: float = 0.0
        self.lifetime_gold: float = 0.0
        self.diamonds: int = 0
        self.shards: float = 0.0
        self.scrap: float = 0.0      # placeholder for future scrap
        self.scrap_idle: float = 0.0 # placeholder idle scrap
        # shop state (permanent purchases levels)
        self.shop_levels: Dict[str, int] = {}

        # dice game
        self.base_dice: int = 1
        self.dice_count: int = 1
        self.die_sides: int = 6
        self.animation_speed: float = 1.0

        # slots
        self.slots_unlocked: bool = False
        self.slots_passive_income: float = 0.0

        # roulette
        self.roulette_unlocked: bool = False
        self.roulette_base_max_bet: int = 100
        self.roulette_max_bet: int = 100
        self.roulette_payout_bonus_total: float = 0.0
        self.roulette_passive_income: float = 0.0

        # buildings
        self.buildings_passive_income: float = 0.0

        # global
        self.global_income_mult: float = 1.0
        self.shards_passive_income: float = 0.0

        # --- NEW: loadout-driven economy fields ---
        self.dice_idle_income: float = 0.0
        self.slots_yield_mult: float = 1.0
        self.shards_rate_mult: float = 1.0
        self.team_gold_mult_from_dice: float = 1.0
        self.team_roulette_bonus_from_dice: float = 0.0

        # upgrades
        self.upgrades: list[Upgrade] = [Upgrade(defn) for defn in UPGRADES]

        # collection & loadout
        self.inventory: List[DiceInstance] = []
        self._next_uid: int = 1
        self.loadout: List[int] = [0]*5

        # caches
        self._templates = get_templates()
        self._sets = get_sets()

        self._recompute_stats()

        # --- scrap crate tracking / achievements ---
        self.crates_basic_no_rare: int = 0  # pity counter for Basic crates
        self.crates_opened: Dict[str, int] = {"basic": 0, "advanced": 0, "rare": 0, "legendary": 0}
        self.achievements_claimed: Dict[str, bool] = {}
        self.achievements_seen: Dict[str, bool] = {}

        # --- gameplay counters for achievements ---
        self.counter_dice_plays: int = 0
        self.counter_slots_spins: int = 0
        self.counter_slots_wins: int = 0
        self.counter_roulette_spins: int = 0
        self.counter_roulette_wins: int = 0
        # shard bounties (v2 manager)
        self.bounties = BountyManager()
        # legacy fields kept for backward-compatibility in load() only
        self.bounties_daily_claimed: Dict[str, bool] = {}
        self.bounties_weekly_claimed: Dict[str, bool] = {}
        self.bounties_daily_reset_at: int = 0
        self.bounties_weekly_reset_at: int = 0
        self.bounties_claimed: Dict[str, bool] = {}

    # ---------- collection ----------
    def _grant_starter_if_empty(self):
        inv_grant_starter_if_empty(self)

    def add_dice(self, template_key: str) -> DiceInstance:
        return inv_add_dice(self, template_key)

    def find_dice(self, uid: int) -> Optional[DiceInstance]:
        return inv_find_dice(self, uid)

    def equip_first_empty(self, uid: int) -> bool:
        return inv_equip_first_empty(self, uid)

    def compact_loadout(self):
        inv_compact_loadout(self)

    # Public hook for UI to call after any loadout edits
    def on_loadout_changed(self):
        self._recompute_stats()

    # ---------- team & set bonuses ----------
    def get_loadout_templates(self) -> List[DiceTemplate]:
        out: List[DiceTemplate] = []
        for uid in self.loadout:
            if not uid: continue
            inst = self.find_dice(uid)
            if not inst: continue
            t = self._templates.get(inst.template_key)
            if t:
                out.append(prog_apply_stars_and_level(t, inst.stars, inst.level))
        return out

    def _level_multiplier(self, level: int) -> float:
        return prog_level_multiplier(level)

    def _template_with_stars(self, t: DiceTemplate, stars: int) -> DiceTemplate:
        return prog_apply_stars(t, stars)

    def _template_with_stars_and_level(self, t: DiceTemplate, stars: int, level: int) -> DiceTemplate:
        return prog_apply_stars_and_level(t, stars, level)

    # ---------- leveling costs and actions ----------
    def level_costs(self, inst: DiceInstance) -> tuple[int, int]:
        return prog_level_costs(int(inst.level))

    def can_level(self, inst: DiceInstance) -> bool:
        if inst.level >= 100:
            return False
        s, c = self.level_costs(inst)
        return self.shards >= s and self.scrap >= c

    def level_up(self, inst: DiceInstance, times: int = 1) -> int:
        gained = 0
        for _ in range(times):
            if inst.level >= 100:
                break
            s, c = self.level_costs(inst)
            if self.shards < s or self.scrap < c:
                break
            self.shards -= s
            self.scrap -= c
            inst.level += 1
            gained += 1
            # Milestone reward: every 10 levels grant shard burst (rarity-scaled)
            if inst.level % 10 == 0:
                t = self._templates.get(inst.template_key)
                rarity_bonus = {"Common": 1.0, "Uncommon": 1.5, "Rare": 2.5, "Legendary": 4.0}.get(t.rarity if t else "Common", 1.0)
                burst = 10.0 * inst.level/10 * rarity_bonus  # 10,20,30... times rarity factor
                self.shards += burst
        if gained:
            self.on_loadout_changed()
        return gained

    # --- simple conversions: scrap -> shards (crafting) ---
    def convert_scrap_to_shards(self, scrap_amount: int) -> float:
        return scrap_convert_scrap_to_shards(self, scrap_amount)

    def compute_set_counts(self) -> Dict[str, int]:
        return tb_compute_set_counts(self)

    def active_set_tiers(self) -> List[SetBonusTier]:
        return tb_active_set_tiers(self)

    def team_totals_with_bonuses(self) -> Dict[str, int]:
        return tb_team_totals(self)

    # ---------- buildings helper (for hub) ----------
    def get_building_data(self):
        return get_building_cards(self)

    # ---------- casino gameplay ----------
    def _apply_income(self, gold: int):
        gold2 = int(round(gold * self.global_income_mult))
        self.gold += gold2
        self.lifetime_gold += gold2
        self._check_unlocks()
        return gold2

    def bet(self) -> tuple[list[int], int]:
        return casino_bet(self)

    def spin_slots(self) -> tuple[list[str], int, int]:
        return casino_spin_slots(self)

    # ---------- upgrades ----------

    def _get_by_key(self, key: str) -> Optional[Upgrade]:
        return next((u for u in self.upgrades if u.key == key), None)

    def _apply_reveal_and_disable(self):
        for u in self.upgrades:
            # Reveal chain
            locked = False
            if u.reveal_after_key is not None:
                req = self._get_by_key(u.reveal_after_key)
                if not (req and req.level >= u.reveal_after_level):
                    locked = True

            # NEW: milestone gating (e.g., appears after owning N of a building)
            if u.milestone_key and u.milestone_level:
                base = self._get_by_key(u.milestone_key)
                if not (base and base.level >= u.milestone_level):
                    locked = True

            u.locked = locked
            u.disabled = (u.disabled_when_reached_level is not None and u.level >= u.disabled_when_reached_level)

    def _recompute_stats(self):
        self._apply_reveal_and_disable()

        # dice
        self.dice_count = self.base_dice + sum(u.level * u.dice_gain for u in self.upgrades)
        self.die_sides = 6 + sum(u.level * u.die_sides_increase for u in self.upgrades)
        self.animation_speed = 1.0
        for u in self.upgrades:
            if u.level > 0 and u.animation_speed_mult != 1.0:
                self.animation_speed *= (u.animation_speed_mult ** u.level)

        # slots
        self.slots_passive_income = sum(u.level * u.slots_passive for u in self.upgrades)

        # roulette
        self.roulette_max_bet = self.roulette_base_max_bet + sum(u.level * u.roulette_maxbet_increase for u in self.upgrades)
        self.roulette_payout_bonus_total = sum(u.level * u.roulette_payout_bonus for u in self.upgrades)
        self.roulette_passive_income = sum(u.level * u.roulette_passive for u in self.upgrades)

        # buildings
        # New: building milestone upgrades increase per-unit output of base buildings
        per_unit_bonus: dict[str, float] = {}
        for u in self.upgrades:
            m_key = getattr(u.definition, "milestone_key", None)
            if m_key:
                per_unit_bonus[m_key] = per_unit_bonus.get(m_key, 0.0) + (u.level * u.building_gold_ps)
        total_building_income = 0.0
        for u in self.upgrades:
            if u.category != "buildings":
                continue
            if getattr(u.definition, "milestone_key", None):
                continue
            if u.building_gold_ps <= 0:
                continue
            unit = u.building_gold_ps + per_unit_bonus.get(u.key, 0.0)
            total_building_income += u.level * unit
        self.buildings_passive_income = total_building_income

        # global & shards (from upgrades)
        self.global_income_mult = 1.0
        self.shards_passive_income = 0.0
        self.scrap_idle = 0.0
        self.salvage_yield_mult_total = 1.0
        self.salvage_cost_discount_total = 0.0
        for u in self.upgrades:
            if u.level > 0 and u.global_gold_mult != 1.0:
                self.global_income_mult *= (u.global_gold_mult ** u.level)
            if u.level > 0 and u.shards_passive > 0.0:
                self.shards_passive_income += u.level * u.shards_passive
            if u.level > 0 and u.scrap_passive > 0.0:
                self.scrap_idle += u.level * u.scrap_passive
            if u.level > 0 and u.salvage_yield_mult > 0.0:
                self.salvage_yield_mult_total *= (1.0 + u.salvage_yield_mult) ** u.level
            if u.level > 0 and u.salvage_cost_discount > 0.0:
                self.salvage_cost_discount_total += u.level * u.salvage_cost_discount
        # Cap discount to avoid free salvage
        if self.salvage_cost_discount_total > 0.95:
            self.salvage_cost_discount_total = 0.95

        # --- NEW: apply economy effects from equipped dice ---
        self.team_gold_mult_from_dice = 1.0
        self.dice_idle_income = 0.0
        self.slots_yield_mult = 1.0
        self.team_roulette_bonus_from_dice = 0.0
        self.shards_rate_mult = 1.0

        for t in self.get_loadout_templates():
            self.team_gold_mult_from_dice *= (1.0 + (t.gold_mult_pct or 0.0) / 100.0)
            self.dice_idle_income += (t.idle_gold_ps or 0.0)
            self.slots_yield_mult *= (1.0 + (t.slots_mult_pct or 0.0) / 100.0)
            self.team_roulette_bonus_from_dice += (t.roulette_mult_pct or 0.0) / 100.0
            self.shards_rate_mult *= (1.0 + (t.shard_rate_mult_pct or 0.0) / 100.0)

        self.global_income_mult *= self.team_gold_mult_from_dice
        self.roulette_payout_bonus_total += self.team_roulette_bonus_from_dice
        # Apply permanent shop upgrades
        try:
            lvl_gold = int(self.shop_levels.get('perm_gold_booster', 0))
            if lvl_gold > 0:
                self.global_income_mult *= (1.0 + 0.05 * lvl_gold)
            lvl_shard = int(self.shop_levels.get('perm_shard_rate', 0))
            if lvl_shard > 0:
                self.shards_rate_mult *= (1.0 + 0.10 * lvl_shard)
            lvl_salv = int(self.shop_levels.get('perm_salvage_yield', 0))
            if lvl_salv > 0:
                self.salvage_yield_mult_total *= (1.0 + 0.10 * lvl_salv)
        except Exception:
            pass

    def visible_upgrades(self, category: str):
        return [u for u in self.upgrades if u.category == category and not u.locked]

    def can_buy(self, u: Upgrade) -> bool:
        return (not u.locked and not u.disabled and u.level < u.max_level and self.gold >= u.cost())

    def buy(self, u: Upgrade) -> bool:
        if not self.can_buy(u): return False
        self.gold -= u.cost()
        u.level += 1
        self._recompute_stats()
        return True

    # ---------- unlocks / ticks ----------
    def check_unlocks(self) -> None:
        self._check_unlocks()

    def _check_unlocks(self):
        if not self.slots_unlocked and self.lifetime_gold >= 2000:
            self.slots_unlocked = True
        if not self.roulette_unlocked and self.lifetime_gold >= 10000:
            self.roulette_unlocked = True

    def tick_passive(self):
        gold_ps = 0.0
        gold_ps += self.slots_passive_income
        gold_ps += self.roulette_passive_income
        gold_ps += self.buildings_passive_income
        gold_ps += self.dice_idle_income
        if gold_ps > 0:
            self._apply_income(int(gold_ps))
        if self.shards_passive_income > 0:
            self.shards += self.shards_passive_income * self.shards_rate_mult
        # Scrap passive
        if self.scrap_idle > 0:
            self.scrap += self.scrap_idle

    # ---------- scrap mini-game ----------
    def salvage(self, cost: int, quality_mult: float | None = None) -> tuple[float, int]:
        return scrap_salvage(self, cost, quality_mult)

    # ---------- scrap crates ----------
    def open_scrap_crate(self, tier: str):
        return scrap_open_scrap_crate(self, tier)

    # ---------- shop ----------
    def list_shop_items(self) -> List[dict]:
        return shop_list_items(self)

    def purchase_shop_item(self, key: str):
        res = shop_purchase(self, key)
        if res is True:
            self._recompute_stats()
        return res

    def shop_item_details(self, key: str) -> dict:
        return shop_item_details(self, key)

    def _post_crate_open(self, tier: str, rarity: str) -> None:
        tier = tier.lower()
        self.crates_opened[tier] = self.crates_opened.get(tier, 0) + 1
        # Pity counter update
        if tier == "basic":
            if rarity in ("Rare", "Legendary"):
                self.crates_basic_no_rare = 0
            else:
                self.crates_basic_no_rare += 1
        # No direct rewards here; Achievements are claim-based via UI

    def list_achievements(self) -> List[dict]:
        return ach_list(self)

    def claim_achievement(self, key: str) -> bool:
        return ach_claim(self, key)

    def mark_achievements_seen(self) -> None:
        ach_mark_seen(self)

    # moved to achievements_ops

    # ---------- persistence ----------
    def to_dict(self) -> dict[str, Any]:
        return persist_to_dict(self)

    def from_dict(self, data: dict[str, Any]):
        persist_from_dict(self, data)

    # ---------- shard bounties (via manager) ----------
    def bounties_reset_info(self) -> dict:
        return self.bounties.reset_info()

    def list_bounties(self) -> List[dict]:
        return self.bounties.list(self)

    def claim_bounty(self, key: str) -> bool:
        return self.bounties.claim(self, key)

        # Merge any historical duplicate dice into stars and scrap overflow
        try:
            self.merge_duplicates()
        except Exception:
            pass
        self._recompute_stats()
        self._check_unlocks()

    # ---------- equip helpers for UI ----------
    def equip_replace_or_empty(self, uid: int) -> bool:
        return inv_equip_replace_or_empty(self, uid)

    def save(self, path: Path = SAVE_PATH) -> bool:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8"); return True
        except Exception: return False

    def load(self, path: Path = SAVE_PATH) -> bool:
        try:
            # Prefer new location; fall back to legacy file if present
            if not path.exists() and LEGACY_SAVE.exists():
                self.from_dict(json.loads(LEGACY_SAVE.read_text(encoding="utf-8")))
                # attempt migration on next save
                self._grant_starter_if_empty(); return True
            if not path.exists():
                self._grant_starter_if_empty(); return False
            self.from_dict(json.loads(path.read_text(encoding="utf-8")))
            self._grant_starter_if_empty(); return True
        except Exception:
            self._grant_starter_if_empty(); return False

    def reset(self):
        self.gold = 0.0; self.lifetime_gold = 0.0; self.diamonds = 0; self.shards = 0.0
        self.scrap = 0.0; self.scrap_idle = 0.0
        self.base_dice = 1; self.dice_count = 1; self.die_sides = 6; self.animation_speed = 1.0
        self.slots_unlocked = False; self.slots_passive_income = 0.0
        self.roulette_unlocked = False; self.roulette_max_bet = self.roulette_base_max_bet
        self.roulette_payout_bonus_total = 0.0; self.roulette_passive_income = 0.0
        self.buildings_passive_income = 0.0
        self.global_income_mult = 1.0; self.shards_passive_income = 0.0
        self.dice_idle_income = 0.0; self.slots_yield_mult = 1.0
        self.shards_rate_mult = 1.0; self.team_gold_mult_from_dice = 1.0
        self.team_roulette_bonus_from_dice = 0.0
        for u in self.upgrades: u.level = 0; u.locked = False; u.disabled = False
        self.inventory.clear(); self._next_uid = 1; self.loadout = [0]*5
        self._grant_starter_if_empty(); self._recompute_stats()

    # ---------- maintenance ----------
    def merge_duplicates(self) -> None:
        inv_merge_duplicates(self)
    



