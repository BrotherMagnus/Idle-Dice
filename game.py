# game.py
import random, json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, List

from upgrades import UpgradeDef, UPGRADES
from dice_models import DiceInstance, get_templates

SAVE_VERSION = 7
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

    @property
    def dice_gain(self): return self.definition.dice_gain
    @property
    def animation_speed_mult(self): return self.definition.animation_speed_mult
    @property
    def die_sides_increase(self): return self.definition.die_sides_increase
    @property
    def slots_passive(self): return self.definition.slots_passive

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
        self.gold: float = 0.0
        self.lifetime_gold: float = 0.0
        self.diamonds: int = 0

        # casino dice mode stats (separate from battler dice)
        self.base_dice: int = 1
        self.dice_count: int = 1
        self.die_sides: int = 6
        self.animation_speed: float = 1.0

        # slots
        self.slots_unlocked: bool = False
        self.slots_passive_income: float = 0.0

        # upgrades
        self.upgrades: list[Upgrade] = [Upgrade(defn) for defn in UPGRADES]

        # --- NEW: collection and loadout ---
        self.inventory: List[DiceInstance] = []
        self._next_uid: int = 1
        self.loadout: List[int] = [0, 0, 0, 0, 0, 0]  # store dice uids, 0 = empty

        self._recompute_stats()

    # ---------- Collection ----------
    def _grant_starter_if_empty(self):
        if not self.inventory:
            self.add_dice("common_d6")  # starter
            self.loadout[0] = self.inventory[0].uid

    def add_dice(self, template_key: str) -> DiceInstance:
        inst = DiceInstance(uid=self._next_uid, template_key=template_key)
        self._next_uid += 1
        self.inventory.append(inst)
        return inst

    def find_dice(self, uid: int) -> Optional[DiceInstance]:
        for d in self.inventory:
            if d.uid == uid:
                return d
        return None

    def equip_first_empty(self, uid: int) -> bool:
        if not self.find_dice(uid): return False
        # already equipped?
        if uid in self.loadout: return True
        for i in range(len(self.loadout)):
            if self.loadout[i] == 0:
                self.loadout[i] = uid
                return True
        return False

    def compact_loadout(self):
        # keep order but push zeros to end
        filtered = [u for u in self.loadout if u]
        self.loadout = filtered + [0]*(6 - len(filtered))

    # ---------- Gameplay ----------
    def bet(self) -> tuple[list[int], int]:
        faces = [random.randint(1, self.die_sides) for _ in range(self.dice_count)]
        total = sum(faces)
        self.gold += total
        self.lifetime_gold += total
        self._check_unlocks()
        return faces, total

    def spin_slots(self) -> tuple[list[str], int, int]:
        symbols = ["🍒", "🍋", "7️⃣", "💎", "⭐"]
        reels = [random.choice(symbols) for _ in range(3)]
        gold_won = 0
        diamonds_won = 0
        if len(set(reels)) == 1:
            if reels[0] == "💎":
                diamonds_won = 10
            else:
                gold_won = 500
        elif len(set(reels)) == 2:
            gold_won = 50
        self.gold += gold_won
        self.lifetime_gold += gold_won
        self.diamonds += diamonds_won
        return reels, gold_won, diamonds_won

    # ---------- Upgrades ----------
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
        self.dice_count = self.base_dice + sum(u.level * u.dice_gain for u in self.upgrades)
        self.die_sides = 6 + sum(u.level * u.die_sides_increase for u in self.upgrades)
        self.animation_speed = 1.0
        for u in self.upgrades:
            if u.level > 0 and u.animation_speed_mult != 1.0:
                self.animation_speed *= (u.animation_speed_mult ** u.level)
        self.slots_passive_income = sum(u.level * u.slots_passive for u in self.upgrades)

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

    # ---------- Unlocks / ticks ----------
    def _check_unlocks(self):
        if not self.slots_unlocked and self.lifetime_gold >= 2000:
            self.slots_unlocked = True

    def tick_passive(self):
        if self.slots_unlocked and self.slots_passive_income > 0:
            self.gold += self.slots_passive_income
            self.lifetime_gold += self.slots_passive_income

    # ---------- Persistence ----------
    def to_dict(self) -> dict[str, Any]:
        return {
            "version": SAVE_VERSION,
            "gold": self.gold,
            "lifetime_gold": self.lifetime_gold,
            "diamonds": self.diamonds,
            "base_dice": self.base_dice,
            "slots_unlocked": self.slots_unlocked,
            "upgrades": [{"key": u.key, "level": u.level} for u in self.upgrades],
            "inv": [{"uid": d.uid, "template_key": d.template_key, "level": d.level} for d in self.inventory],
            "next_uid": self._next_uid,
            "loadout": self.loadout,
        }

    def from_dict(self, data: dict[str, Any]):
        self.gold = float(data.get("gold", 0.0))
        self.lifetime_gold = float(data.get("lifetime_gold", 0.0))
        self.diamonds = int(data.get("diamonds", 0))
        self.base_dice = int(data.get("base_dice", 1))
        self.slots_unlocked = bool(data.get("slots_unlocked", False))
        saved_levels = {rec.get("key"): int(rec.get("level", 0)) for rec in data.get("upgrades", [])}
        for u in self.upgrades:
            if u.key in saved_levels:
                u.level = saved_levels[u.key]

        # inventory/loadout
        self.inventory.clear()
        for rec in data.get("inv", []):
            self.inventory.append(DiceInstance(uid=int(rec["uid"]), template_key=rec["template_key"], level=int(rec.get("level",1))))
        self._next_uid = int(data.get("next_uid", len(self.inventory)+1))
        ld = data.get("loadout", [0,0,0,0,0,0])
        self.loadout = [int(x) for x in (ld + [0,0,0,0,0,0])[:6]]

        self._recompute_stats()

    def save(self, path: Path = SAVE_PATH) -> bool:
        try:
            path.write_text(json.dumps(self.to_dict(), indent=2))
            return True
        except Exception:
            return False

    def load(self, path: Path = SAVE_PATH) -> bool:
        try:
            if not path.exists():
                # first-time players get a starter die
                self._grant_starter_if_empty()
                return False
            self.from_dict(json.loads(path.read_text()))
            # if somehow empty, still guarantee starter
            self._grant_starter_if_empty()
            return True
        except Exception:
            self._grant_starter_if_empty()
            return False

    # convenience for menu reset
    def reset(self):
        self.gold = 0.0
        self.lifetime_gold = 0.0
        self.diamonds = 0
        self.base_dice = 1
        self.dice_count = 1
        self.die_sides = 6
        self.animation_speed = 1.0
        self.slots_unlocked = False
        self.slots_passive_income = 0.0
        for u in self.upgrades:
            u.level = 0; u.locked = False; u.disabled = False
        self.inventory.clear()
        self._next_uid = 1
        self.loadout = [0,0,0,0,0,0]
        self._grant_starter_if_empty()
        self._recompute_stats()
