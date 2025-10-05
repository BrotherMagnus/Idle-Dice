# upgrades.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

@dataclass(frozen=True)
class UpgradeDef:
    key: str
    category: str              # "global" | "dice" | "slots" | "roulette"
    name: str
    base_cost: int
    cost_multiplier: float = 1.15
    max_level: int = 999

    # Reveal/Disable logic
    reveal_after_key: Optional[str] = None
    reveal_after_level: int = 0
    disabled_when_reached_level: Optional[int] = None

    # Effects (all optional; Game interprets them)
    # Dice
    dice_gain: int = 0
    animation_speed_mult: float = 1.0
    die_sides_increase: int = 0
    # Slots
    slots_passive: float = 0.0
    # Global (affects every gold earning)
    global_gold_mult: float = 1.0    # e.g., 1.02 means +2%/lvl (Game multiplies)
    # Roulette
    roulette_payout_bonus: float = 0.0  # +% to payouts, e.g. 0.02/lvl
    roulette_maxbet_increase: int = 0   # +flat max bet

# --- Upgrade Catalog ---
UPGRADES: List[UpgradeDef] = [
    # ---------- GLOBAL ----------
    UpgradeDef(
        key="global_income_1", category="global", name="Casino Reputation I",
        base_cost=800, global_gold_mult=1.02, max_level=50
    ),
    UpgradeDef(
        key="global_income_2", category="global", name="High Roller Lounge",
        base_cost=8500, cost_multiplier=1.18, global_gold_mult=1.03, max_level=40,
        reveal_after_key="global_income_1", reveal_after_level=10
    ),

    # ---------- DICE ----------
    UpgradeDef(
        key="dice_qty_1", category="dice", name="Dice Quantity I",
        base_cost=20, dice_gain=1, disabled_when_reached_level=50,
    ),
    UpgradeDef(
        key="dice_qty_2", category="dice", name="Dice Quantity II",
        base_cost=5000, dice_gain=2, reveal_after_key="dice_qty_1", reveal_after_level=50,
    ),
    UpgradeDef(
        key="dice_qty_3", category="dice", name="Dice Quantity III",
        base_cost=120000, dice_gain=3, reveal_after_key="dice_qty_2", reveal_after_level=50,
    ),
    UpgradeDef(
        key="faster_roller_1", category="dice", name="Faster Roller I",
        base_cost=100, animation_speed_mult=0.9, max_level=10,
    ),
    UpgradeDef(
        key="faster_roller_2", category="dice", name="Faster Roller II",
        base_cost=5000, animation_speed_mult=0.9, max_level=10,
        reveal_after_key="faster_roller_1", reveal_after_level=10,
    ),
    UpgradeDef(
        key="more_sides_1", category="dice", name="Sharper Edges",
        base_cost=2000, die_sides_increase=1, max_level=6
    ),

    # ---------- SLOTS ----------
    UpgradeDef(
        key="slots_passive_1", category="slots", name="VIP Slot Floor",
        base_cost=1000, slots_passive=1.0
    ),
    UpgradeDef(
        key="slots_passive_2", category="slots", name="Loose Machines",
        base_cost=6000, cost_multiplier=1.2, slots_passive=3.0,
        reveal_after_key="slots_passive_1", reveal_after_level=5
    ),

    # ---------- ROULETTE ----------
    UpgradeDef(
        key="roulette_maxbet_1", category="roulette", name="Bigger Table Limits",
        base_cost=2000, roulette_maxbet_increase=250
    ),
    UpgradeDef(
        key="roulette_payout_bonus_1", category="roulette", name="Croupier Favor",
        base_cost=3500, roulette_payout_bonus=0.02, max_level=20  # +2% payout per level
    ),
]
