# upgrades.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

@dataclass(frozen=True)
class UpgradeDef:
    key: str
    category: str              # "global" | "dice" | "slots" | "roulette" | "buildings"
    name: str
    base_cost: int
    cost_multiplier: float = 1.15
    max_level: int = 999

    # Reveal/Disable logic
    reveal_after_key: Optional[str] = None
    reveal_after_level: int = 0
    disabled_when_reached_level: Optional[int] = None

    # Effects (interpreted by Game)
    # Dice
    dice_gain: int = 0
    animation_speed_mult: float = 1.0
    die_sides_increase: int = 0

    # Slots
    slots_passive: float = 0.0

    # Roulette
    roulette_payout_bonus: float = 0.0   # +% payouts per level (0.02 = +2%)
    roulette_maxbet_increase: int = 0
    roulette_passive: float = 0.0        # gold/sec

    # Buildings (generic passive gold/sec)
    building_gold_ps: float = 0.0

    # Global
    global_gold_mult: float = 1.0        # multiplicative
    shards_passive: float = 0.0          # shards/sec (new currency)

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
    UpgradeDef(
        key="shard_drip_1", category="global", name="Shard Drip",
        base_cost=3000, shards_passive=0.2, max_level=50
    ),
    UpgradeDef(
        key="global_income_3", category="global", name="Prime Time Promotions",
        base_cost=50000, cost_multiplier=1.2, global_gold_mult=1.05, max_level=30,
        reveal_after_key="global_income_2", reveal_after_level=15
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
        base_cost=3500, roulette_payout_bonus=0.02, max_level=20
    ),
    UpgradeDef(
        key="roulette_passive_1", category="roulette", name="Night Wheel",
        base_cost=4000, roulette_passive=1.5
    ),
    UpgradeDef(
        key="roulette_passive_2", category="roulette", name="VIP Wheel",
        base_cost=20000, cost_multiplier=1.2, roulette_passive=5.0,
        reveal_after_key="roulette_passive_1", reveal_after_level=5
    ),

    # ---------- BUILDINGS (Cookie-Clicker style) ----------
    UpgradeDef(
        key="b_kiosk", category="buildings", name="Cashier Kiosk",
        base_cost=500, building_gold_ps=0.5
    ),
    UpgradeDef(
        key="b_bar", category="buildings", name="Casino Bar",
        base_cost=2500, building_gold_ps=2.0, reveal_after_key="b_kiosk", reveal_after_level=5
    ),
    UpgradeDef(
        key="b_pitboss", category="buildings", name="Pit Boss",
        base_cost=10000, building_gold_ps=6.0, reveal_after_key="b_bar", reveal_after_level=5
    ),
    UpgradeDef(
        key="b_vip", category="buildings", name="VIP Lounge",
        base_cost=60000, building_gold_ps=20.0, reveal_after_key="b_pitboss", reveal_after_level=5
    ),
]
