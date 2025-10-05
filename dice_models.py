# dice_models.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, List, Tuple

IMAGES_DIR = Path(__file__).with_name("images")  # put PNG/JPG icons here

class Rarity(str, Enum):
    COMMON = "Common"
    RARE = "Rare"
    EPIC = "Epic"
    LEGENDARY = "Legendary"

# ---------- Dice Templates ----------
@dataclass(frozen=True)
class DiceTemplate:
    key: str
    name: str
    sides: int
    rarity: Rarity
    set_key: str
    set_name: str
    material: str              # "wooden", "stone", "plastic", "clay"
    icon_basename: str         # e.g., wooden_d8

    # Base battler stats (pre-bonuses)
    hp: int
    atk: int
    defense: int
    speed: int
    ability: str = "None"

    def resolve_icon_path(self) -> Optional[Path]:
        png = IMAGES_DIR / f"{self.icon_basename}.png"
        jpg = IMAGES_DIR / f"{self.icon_basename}.jpg"
        if png.exists(): return png
        if jpg.exists(): return jpg
        return None

# ---------- Owned Dice ----------
@dataclass
class DiceInstance:
    uid: int
    template_key: str
    level: int = 1  # future growth

# ---------- Set Bonuses ----------
# Simple, readable schema:
# Each bonus is (stat, kind, amount)
#   stat ∈ {"hp","atk","defense","speed"}
#   kind ∈ {"flat","pct"}  → flat adds value; pct multiplies (%) (5 => +5%)
Bonus = Tuple[str, str, float]

@dataclass(frozen=True)
class SetBonusTier:
    pieces: int
    bonuses: List[Bonus]
    label: str  # short label shown in UI

@dataclass(frozen=True)
class DiceSet:
    key: str
    name: str
    rarity: Rarity
    tiers: List[SetBonusTier]

def _common_tiers_balanced() -> List[SetBonusTier]:
    # modest balanced growth
    return [
        SetBonusTier(2, [("atk","pct",5)], "2pc: ATK +5%"),
        SetBonusTier(3, [("hp","pct",5)], "3pc: HP +5%"),
        SetBonusTier(5, [("atk","pct",5), ("defense","pct",5)], "5pc: ATK +5%, DEF +5%"),
    ]

def _common_tiers_tanky() -> List[SetBonusTier]:
    return [
        SetBonusTier(2, [("defense","pct",7)], "2pc: DEF +7%"),
        SetBonusTier(3, [("hp","pct",7)], "3pc: HP +7%"),
        SetBonusTier(5, [("defense","pct",8)], "5pc: DEF +8%"),
    ]

def _common_tiers_speedy() -> List[SetBonusTier]:
    return [
        SetBonusTier(2, [("speed","flat",2)], "2pc: SPD +2"),
        SetBonusTier(3, [("atk","pct",6)], "3pc: ATK +6%"),
        SetBonusTier(5, [("speed","flat",2), ("atk","pct",6)], "5pc: SPD +2, ATK +6%"),
    ]

def _common_tiers_ward() -> List[SetBonusTier]:
    # Clay = sustain/ward-style defense+hp
    return [
        SetBonusTier(2, [("hp","pct",6)], "2pc: HP +6%"),
        SetBonusTier(3, [("defense","pct",6)], "3pc: DEF +6%"),
        SetBonusTier(5, [("hp","pct",6), ("defense","pct",6)], "5pc: HP +6%, DEF +6%"),
    ]

def get_sets() -> Dict[str, DiceSet]:
    return {
        "set_wooden": DiceSet("set_wooden", "Wooden Set", Rarity.COMMON, _common_tiers_balanced()),
        "set_stone":  DiceSet("set_stone",  "Stone Set",  Rarity.COMMON, _common_tiers_tanky()),
        "set_plastic":DiceSet("set_plastic","Plastic Set",Rarity.COMMON, _common_tiers_speedy()),
        "set_clay":   DiceSet("set_clay",   "Clay Set",   Rarity.COMMON, _common_tiers_ward()),
    }

def get_templates() -> Dict[str, DiceTemplate]:
    # Helper for brevity
    def T(mat: str, sides: int, name: str, set_key: str, set_name: str, hp:int, atk:int, defense:int, speed:int, ability:str="None"):
        return DiceTemplate(
            key=f"{mat}_d{sides}",
            name=name, sides=sides, rarity=Rarity.COMMON,
            set_key=set_key, set_name=set_name,
            material=mat, icon_basename=f"{mat}_d{sides}",
            hp=hp, atk=atk, defense=defense, speed=speed, ability=ability
        )

    # ---- Wooden (balanced / crit-lean) ----
    wooden = {
        "wooden_d4":  T("wooden", 4,  "Wooden D4",  "set_wooden","Wooden Set",  hp=40, atk=8,  defense=3, speed=8,  ability="Chip"),
        "wooden_d6":  T("wooden", 6,  "Wooden D6",  "set_wooden","Wooden Set",  hp=60, atk=10, defense=5, speed=7,  ability="Steady"),
        "wooden_d8":  T("wooden", 8,  "Wooden D8",  "set_wooden","Wooden Set",  hp=65, atk=14, defense=5, speed=6,  ability="Pierce"),
        "wooden_d12": T("wooden", 12, "Wooden D12", "set_wooden","Wooden Set",  hp=80, atk=9,  defense=8, speed=5,  ability="Guard"),
        "wooden_d20": T("wooden", 20, "Wooden D20", "set_wooden","Wooden Set",  hp=70, atk=16, defense=6, speed=6,  ability="Crit"),
    }

    # ---- Stone (tanky) ----
    stone = {
        "stone_d4":  T("stone", 4,  "Stone D4",  "set_stone","Stone Set",  hp=48, atk=7,  defense=5, speed=7,  ability="Sturdy"),
        "stone_d6":  T("stone", 6,  "Stone D6",  "set_stone","Stone Set",  hp=70, atk=9,  defense=7, speed=6,  ability="Sturdy"),
        "stone_d8":  T("stone", 8,  "Stone D8",  "set_stone","Stone Set",  hp=78, atk=12, defense=8, speed=5,  ability="Shatter"),
        "stone_d12": T("stone", 12, "Stone D12", "set_stone","Stone Set",  hp=92, atk=9,  defense=10, speed=4, ability="Bulwark"),
        "stone_d20": T("stone", 20, "Stone D20", "set_stone","Stone Set",  hp=82, atk=14, defense=9, speed=5,  ability="Crusher"),
    }

    # ---- Plastic (speedy / aggro) ----
    plastic = {
        "plastic_d4":  T("plastic", 4,  "Plastic D4",  "set_plastic","Plastic Set",  hp=36, atk=9,  defense=3, speed=10, ability="Quick"),
        "plastic_d6":  T("plastic", 6,  "Plastic D6",  "set_plastic","Plastic Set",  hp=55, atk=11, defense=4, speed=9,  ability="Rush"),
        "plastic_d8":  T("plastic", 8,  "Plastic D8",  "set_plastic","Plastic Set",  hp=60, atk=15, defense=5, speed=8,  ability="Flurry"),
        "plastic_d12": T("plastic", 12, "Plastic D12", "set_plastic","Plastic Set",  hp=68, atk=11, defense=6, speed=8,  ability="Haste"),
        "plastic_d20": T("plastic", 20, "Plastic D20", "set_plastic","Plastic Set",  hp=64, atk=17, defense=5, speed=9,  ability="Surge"),
    }

    # ---- Clay (ward / sustain) ----
    clay = {
        "clay_d4":  T("clay", 4,  "Clay D4",  "set_clay","Clay Set",  hp=44, atk=7,  defense=5, speed=7,  ability="Ward"),
        "clay_d6":  T("clay", 6,  "Clay D6",  "set_clay","Clay Set",  hp=66, atk=9,  defense=6, speed=6,  ability="Ward"),
        "clay_d8":  T("clay", 8,  "Clay D8",  "set_clay","Clay Set",  hp=72, atk=12, defense=7, speed=6,  ability="Mend"),
        "clay_d12": T("clay", 12, "Clay D12", "set_clay","Clay Set",  hp=88, atk=9,  defense=9, speed=5,  ability="Plate"),
        "clay_d20": T("clay", 20, "Clay D20", "set_clay","Clay Set",  hp=78, atk=14, defense=8, speed=5,  ability="Fortify"),
    }

    templates: Dict[str, DiceTemplate] = {}
    templates.update(wooden)
    templates.update(stone)
    templates.update(plastic)
    templates.update(clay)
    return templates
