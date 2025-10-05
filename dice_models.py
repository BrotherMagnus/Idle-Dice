# dice_models.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Dict

class Rarity(str, Enum):
    COMMON = "Common"
    RARE = "Rare"
    EPIC = "Epic"
    LEGENDARY = "Legendary"

@dataclass(frozen=True)
class DiceTemplate:
    key: str
    name: str
    sides: int
    rarity: Rarity
    set_key: str
    set_name: str
    # base stats for idle battler
    hp: int
    atk: int
    defense: int
    speed: int
    ability: str = "None"

@dataclass
class DiceInstance:
    uid: int          # unique per save
    template_key: str
    level: int = 1    # for later growth
    # you can add XP, roll-skin, etc.

def get_templates() -> Dict[str, DiceTemplate]:
    # Starter “Common Set” (you can add more sets/rarities later)
    return {
        "common_d4":  DiceTemplate("common_d4",  "Common D4",  4,  Rarity.COMMON, "set_common_alpha", "Common Set Alpha",  hp=40,  atk=8,   defense=3,  speed=8,  ability="Chip"),
        "common_d6":  DiceTemplate("common_d6",  "Common D6",  6,  Rarity.COMMON, "set_common_alpha", "Common Set Alpha",  hp=60,  atk=10,  defense=5,  speed=7,  ability="Steady"),
        "common_d12": DiceTemplate("common_d12", "Common D12", 12, Rarity.COMMON, "set_common_alpha", "Common Set Alpha",  hp=80,  atk=9,   defense=8,  speed=5,  ability="Guard"),
        "common_d20": DiceTemplate("common_d20", "Common D20", 20, Rarity.COMMON, "set_common_alpha", "Common Set Alpha",  hp=70,  atk=16,  defense=6,  speed=6,  ability="Crit"),
    }
