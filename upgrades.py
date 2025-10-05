# upgrades.py
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class UpgradeDef:
    key: str
    category: str              # "dice" or "casino"
    name: str
    base_cost: int
    cost_multiplier: float = 1.15
    max_level: int = 9999

    # Effects
    dice_gain: int = 0
    animation_speed_mult: float = 1.0
    die_sides_increase: int = 0
    slots_passive: float = 0.0   # gold/sec per level

    # Visibility / flow
    reveal_after_key: Optional[str] = None
    reveal_after_level: int = 0
    disabled_when_reached_level: Optional[int] = None


UPGRADES: list[UpgradeDef] = [
    # Dice Quantity chain (I–V)
    UpgradeDef("dice_qty_1", "dice", "Dice Quantity I", 20, dice_gain=1, disabled_when_reached_level=50),
    UpgradeDef("dice_qty_2", "dice", "Dice Quantity II", 5000, dice_gain=2, reveal_after_key="dice_qty_1", reveal_after_level=50, disabled_when_reached_level=50),
    UpgradeDef("dice_qty_3", "dice", "Dice Quantity III", 50_000, dice_gain=3, reveal_after_key="dice_qty_2", reveal_after_level=50, disabled_when_reached_level=50),
    UpgradeDef("dice_qty_4", "dice", "Dice Quantity IV", 250_000, dice_gain=4, reveal_after_key="dice_qty_3", reveal_after_level=50, disabled_when_reached_level=50),
    UpgradeDef("dice_qty_5", "dice", "Dice Quantity V", 1_000_000, dice_gain=5, reveal_after_key="dice_qty_4", reveal_after_level=50),

    # Faster Roller chain
    UpgradeDef("faster_roller_1", "dice", "Faster Roller I", 100, animation_speed_mult=0.9),
    UpgradeDef("faster_roller_2", "dice", "Faster Roller II", 10_000, animation_speed_mult=0.9, reveal_after_key="faster_roller_1", reveal_after_level=25),
    UpgradeDef("faster_roller_3", "dice", "Faster Roller III", 100_000, animation_speed_mult=0.9, reveal_after_key="faster_roller_2", reveal_after_level=25),

    # More sides
    UpgradeDef("die_sides_1", "dice", "Die Sides I (d8)", 200_000, max_level=1, die_sides_increase=2),
    UpgradeDef("die_sides_2", "dice", "Die Sides II (d10)", 1_000_000, max_level=1, die_sides_increase=4, reveal_after_key="die_sides_1", reveal_after_level=1),

    # Casino: Slots passive income upgrades
    UpgradeDef("slots_passive_1", "casino", "Slots Passive I", 2500, slots_passive=0.5),
    UpgradeDef("slots_passive_2", "casino", "Slots Passive II", 25_000, slots_passive=2.0, reveal_after_key="slots_passive_1", reveal_after_level=25),
]
