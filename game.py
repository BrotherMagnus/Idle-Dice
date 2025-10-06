# game.py
import random, json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, List, Dict

from upgrades import UpgradeDef, UPGRADES
from dice_models import DiceInstance, get_templates, get_sets, DiceTemplate, SetBonusTier

SAVE_VERSION = 10
SAVE_PATH = Path(__file__).with_name("savedata.json")

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

    # gating
    @property
    def reveal_after_key(self): return self.definition.reveal_after_key
    @property
    def reveal_after_level(self): return self.definition.reveal_after_level
    @property
    def disabled_when_reached_level(self): return self.definition.disabled_when_reached_level

    def cost(self) -> int:
        return int(self.definition.base_cost * (self.definition.cost_multiplier ** self.level))


class Game:
    def __init__(self):
        # currencies
        self.gold: float = 0.0
        self.lifetime_gold: float = 0.0
        self.diamonds: int = 0
        self.shards: float = 0.0  # new currency

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

        # upgrades
        self.upgrades: list[Upgrade] = [Upgrade(defn) for defn in UPGRADES]

        # collection & loadout
        self.inventory: List[DiceInstance] = []
        self._next_uid: int = 1
        self.loadout: List[int] = [0]*6

        # caches
        self._templates = get_templates()
        self._sets = get_sets()

        self._recompute_stats()

    # ---------- collection ----------
    def _grant_starter_if_empty(self):
        if not self.inventory:
            self.add_dice("wooden_d8")
            self.loadout[0] = self.inventory[0].uid

    def add_dice(self, template_key: str) -> DiceInstance:
        inst = DiceInstance(uid=self._next_uid, template_key=template_key)
        self._next_uid += 1
        self.inventory.append(inst)
        return inst

    def find_dice(self, uid: int) -> Optional[DiceInstance]:
        for d in self.inventory:
            if d.uid == uid: return d
        return None

    def equip_first_empty(self, uid: int) -> bool:
        if not self.find_dice(uid): return False
        if uid in self.loadout: return True
        for i in range(len(self.loadout)):
            if self.loadout[i] == 0:
                self.loadout[i] = uid
                return True
        return False

    def compact_loadout(self):
        filtered = [u for u in self.loadout if u]
        self.loadout = filtered + [0]*(6 - len(filtered))

    # ---------- team & set bonuses ----------
    def get_loadout_templates(self) -> List[DiceTemplate]:
        out: List[DiceTemplate] = []
        for uid in self.loadout:
            if not uid: continue
            inst = self.find_dice(uid)
            if not inst: continue
            t = self._templates.get(inst.template_key)
            if t: out.append(t)
        return out

    def compute_set_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for t in self.get_loadout_templates():
            counts[t.set_key] = counts.get(t.set_key, 0) + 1
        return counts

    def active_set_tiers(self) -> List[SetBonusTier]:
        tiers: List[SetBonusTier] = []
        counts = self.compute_set_counts()
        for set_key, cnt in counts.items():
            s = self._sets.get(set_key)
            if not s: continue
            for tier in s.tiers:
                if cnt >= tier.pieces: tiers.append(tier)
        return tiers

    def team_totals_with_bonuses(self) -> Dict[str, int | float]:
        base = {"hp":0, "atk":0, "defense":0, "speed":0}
        for t in self.get_loadout_templates():
            base["hp"] += t.hp; base["atk"] += t.atk
            base["defense"] += t.defense; base["speed"] += t.speed

        flat_add = {"hp":0, "atk":0, "defense":0, "speed":0}
        pct_add = {"hp":0.0, "atk":0.0, "defense":0.0, "speed":0.0}
        for tier in self.active_set_tiers():
            for stat, kind, amt in tier.bonuses:
                if kind == "flat": flat_add[stat] += amt
                else: pct_add[stat] += amt

        final = {}
        for stat in base.keys():
            val = base[stat] + flat_add[stat]
            val = int(round(val * (1 + pct_add[stat]/100.0)))
            final[stat] = val
        return final

    # ---------- casino gameplay ----------
    def _apply_income(self, gold: int):
        gold2 = int(round(gold * self.global_income_mult))
        self.gold += gold2
        self.lifetime_gold += gold2
        self._check_unlocks()
        return gold2

    def bet(self) -> tuple[list[int], int]:
        faces = [random.randint(1, self.die_sides) for _ in range(self.dice_count)]
        total = sum(faces)
        gained = self._apply_income(total)
        return faces, gained

    def spin_slots(self) -> tuple[list[str], int, int]:
        symbols = ["🍒", "🍋", "7️⃣", "💎", "⭐"]
        reels = [random.choice(symbols) for _ in range(3)]
        gold_won = 0; diamonds_won = 0
        if len(set(reels)) == 1:
            if reels[0] == "💎": diamonds_won = 10
            else: gold_won = 500
        elif len(set(reels)) == 2:
            gold_won = 50
        gold_won = self._apply_income(gold_won)
        self.diamonds += diamonds_won
        return reels, gold_won, diamonds_won

    # ---------- upgrades ----------
    def _get_by_key(self, key: str) -> Optional[Upgrade]:
        return next((u for u in self.upgrades if u.key == key), None)

    def _apply_reveal_and_disable(self):
        for u in self.upgrades:
            if u.reveal_after_key is None:
                u.locked = False
            else:
                req = self._get_by_key(u.reveal_after_key)
                u.locked = not (req and req.level >= u.reveal_after_level)
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
        self.buildings_passive_income = sum(u.level * u.building_gold_ps for u in self.upgrades)

        # global
        self.global_income_mult = 1.0
        self.shards_passive_income = 0.0
        for u in self.upgrades:
            if u.level > 0 and u.global_gold_mult != 1.0:
                self.global_income_mult *= (u.global_gold_mult ** u.level)
            if u.level > 0 and u.shards_passive > 0.0:
                self.shards_passive_income += u.level * u.shards_passive

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
        if gold_ps > 0:
            self._apply_income(int(gold_ps))
        if self.shards_passive_income > 0:
            self.shards += self.shards_passive_income

    # ---------- persistence ----------
    def to_dict(self) -> dict[str, Any]:
        return {
            "version": SAVE_VERSION,
            "gold": self.gold, "lifetime_gold": self.lifetime_gold,
            "diamonds": self.diamonds, "shards": self.shards,
            "base_dice": self.base_dice,
            "slots_unlocked": self.slots_unlocked,
            "roulette_unlocked": self.roulette_unlocked,
            "upgrades": [{"key": u.key, "level": u.level} for u in self.upgrades],
            "inv": [{"uid": d.uid, "template_key": d.template_key, "level": d.level} for d in self.inventory],
            "next_uid": self._next_uid,
            "loadout": self.loadout,
        }

    def from_dict(self, data: dict[str, Any]):
        self.gold = float(data.get("gold", 0.0))
        self.lifetime_gold = float(data.get("lifetime_gold", 0.0))
        self.diamonds = int(data.get("diamonds", 0))
        self.shards = float(data.get("shards", 0.0))
        self.base_dice = int(data.get("base_dice", 1))
        self.slots_unlocked = bool(data.get("slots_unlocked", False))
        self.roulette_unlocked = bool(data.get("roulette_unlocked", False))

        saved_lvls = {rec.get("key"): int(rec.get("level", 0)) for rec in data.get("upgrades", [])}
        for u in self.upgrades:
            if u.key in saved_lvls: u.level = saved_lvls[u.key]

        self.inventory.clear()
        for rec in data.get("inv", []):
            self.inventory.append(DiceInstance(uid=int(rec["uid"]),
                                               template_key=rec["template_key"],
                                               level=int(rec.get("level",1))))
        self._next_uid = int(data.get("next_uid", len(self.inventory)+1))
        ld = data.get("loadout", [0,0,0,0,0,0])
        self.loadout = [int(x) for x in (ld + [0,0,0,0,0,0])[:6]]

        self._recompute_stats()
        self._check_unlocks()

    def save(self, path: Path = SAVE_PATH) -> bool:
        try:
            path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8"); return True
        except Exception: return False

    def load(self, path: Path = SAVE_PATH) -> bool:
        try:
            if not path.exists():
                self._grant_starter_if_empty(); return False
            self.from_dict(json.loads(path.read_text(encoding="utf-8")))
            self._grant_starter_if_empty(); return True
        except Exception:
            self._grant_starter_if_empty(); return False

    def reset(self):
        self.gold = 0.0; self.lifetime_gold = 0.0; self.diamonds = 0; self.shards = 0.0
        self.base_dice = 1; self.dice_count = 1; self.die_sides = 6; self.animation_speed = 1.0
        self.slots_unlocked = False; self.slots_passive_income = 0.0
        self.roulette_unlocked = False; self.roulette_max_bet = self.roulette_base_max_bet
        self.roulette_payout_bonus_total = 0.0; self.roulette_passive_income = 0.0
        self.buildings_passive_income = 0.0
        self.global_income_mult = 1.0; self.shards_passive_income = 0.0
        for u in self.upgrades: u.level = 0; u.locked = False; u.disabled = False
        self.inventory.clear(); self._next_uid = 1; self.loadout = [0]*6
        self._grant_starter_if_empty(); self._recompute_stats()
