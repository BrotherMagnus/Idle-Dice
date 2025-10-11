# dice_models.py
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Where dice images live (project_root/assets/dice)
# The previous path used a sibling of this file (core/assets),
# which doesn't exist in this repo and caused icons to fail to load.
# Resolve to the repository root by going up one directory from /core.
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets" / "dice"

# ============================================================
# Data classes
# ============================================================

@dataclass(frozen=True)
class DiceTemplate:
    key: str                 # e.g., "wooden_d8"
    name: str                # e.g., "Wooden d8"
    set_key: str             # e.g., "wooden"
    set_name: str            # e.g., "Wooden"
    rarity: str              # "Common" | "Uncommon" | "Rare" | "Legendary"
    sides: int               # 4, 6, 8, 12, 20

    # Combat stats
    hp: int
    atk: int
    defense: int
    speed: int

    # NEW: combat crit baseline (ready for the battler)
    crit_chance_pct: float = 0.0   # % chance to crit
    crit_mult: float = 1.5         # damage multiplier on crit

    # Economy bonuses from EQUIPPING this die
    gold_mult_pct: float = 0.0
    idle_gold_ps: float = 0.0
    slots_mult_pct: float = 0.0
    roulette_mult_pct: float = 0.0
    shard_rate_mult_pct: float = 0.0

    def resolve_icon_path(self) -> Optional[Path]:
        # Try common extensions (.png, .jpg, .jpeg)
        for ext in (".png", ".jpg", ".jpeg"):
            p = ASSETS_DIR / f"{self.key}{ext}"
            if p.exists():
                return p
        # Not found
        return None


@dataclass(frozen=True)
class SetBonusTier:
    pieces: int
    # bonuses: [("hp","pct",10), ("idle_gold_ps","flat",0.5), ...]
    bonuses: List[Tuple[str, str, float]] = field(default_factory=list)


@dataclass(frozen=True)
class DiceSet:
    key: str
    name: str
    rarity: str
    tiers: List[SetBonusTier]


@dataclass
class DiceInstance:
    uid: int
    template_key: str
    level: int = 1
    stars: int = 0  # 0-10; >5 shown as red stars in UI


# ============================================================
# Sets (mixed combat + economy bonuses)
# ============================================================

SETS: Dict[str, DiceSet] = {
    # ------------------ Common ------------------
    "wooden": DiceSet(
        key="wooden", name="Wooden", rarity="Common",
        tiers=[
            SetBonusTier(2, [("hp", "pct", 4), ("atk", "pct", 3),
                             ("gold_mult", "pct", 2), ("idle_gold_ps", "flat", 0.2)]),
            SetBonusTier(4, [("hp", "pct", 8), ("atk", "pct", 6),
                             ("gold_mult", "pct", 5), ("idle_gold_ps", "flat", 0.6)]),
            SetBonusTier(6, [("hp", "pct", 15), ("atk", "pct", 10),
                             ("gold_mult", "pct", 10), ("idle_gold_ps", "flat", 1.5)]),
        ]
    ),
    "stone": DiceSet(
        key="stone", name="Stone", rarity="Common",
        tiers=[
            SetBonusTier(2, [("hp", "pct", 6), ("defense", "pct", 6),
                             ("slots_mult", "pct", 5)]),
            SetBonusTier(4, [("hp", "pct", 12), ("defense", "pct", 10),
                             ("slots_mult", "pct", 10), ("idle_gold_ps", "flat", 0.5)]),
            SetBonusTier(6, [("hp", "pct", 20), ("defense", "pct", 15),
                             ("slots_mult", "pct", 15), ("gold_mult", "pct", 8)]),
        ]
    ),
    "plastic": DiceSet(
        key="plastic", name="Plastic", rarity="Common",
        tiers=[
            SetBonusTier(2, [("speed", "pct", 8), ("atk", "pct", 4),
                             ("roulette_mult", "pct", 5)]),
            SetBonusTier(4, [("speed", "pct", 15), ("atk", "pct", 10),
                             ("roulette_mult", "pct", 10), ("gold_mult", "pct", 4)]),
            SetBonusTier(6, [("speed", "pct", 22), ("atk", "pct", 16),
                             ("roulette_mult", "pct", 15), ("idle_gold_ps", "flat", 1.0)]),
        ]
    ),
    "clay": DiceSet(
        key="clay", name="Clay", rarity="Common",
        tiers=[
            SetBonusTier(2, [("hp", "pct", 6), ("defense", "pct", 5),
                             ("shard_rate_mult", "pct", 10)]),
            SetBonusTier(4, [("hp", "pct", 12), ("defense", "pct", 10),
                             ("gold_mult", "pct", 3), ("shard_rate_mult", "pct", 20)]),
            SetBonusTier(6, [("hp", "pct", 18), ("defense", "pct", 15),
                             ("gold_mult", "pct", 6), ("idle_gold_ps", "flat", 1.2),
                             ("shard_rate_mult", "pct", 30)]),
        ]
    ),
    "aluminum": DiceSet(
        key="aluminum", name="Aluminum", rarity="Common",
        tiers=[
            SetBonusTier(2, [("speed", "pct", 6), ("hp", "pct", 3)]),
            SetBonusTier(4, [("speed", "pct", 10), ("atk", "pct", 5), ("gold_mult", "pct", 4)]),
            SetBonusTier(6, [("speed", "pct", 15), ("atk", "pct", 8), ("gold_mult", "pct", 6),
                             ("idle_gold_ps", "flat", 1.0)]),
        ]
    ),

    # ------------------ Uncommon ------------------
    "bone": DiceSet(
        key="bone", name="Bone", rarity="Uncommon",
        tiers=[
            SetBonusTier(2, [("atk", "pct", 8), ("speed", "pct", 5)]),
            SetBonusTier(4, [("atk", "pct", 15), ("speed", "pct", 10), ("gold_mult", "pct", 4)]),
            SetBonusTier(6, [("atk", "pct", 25), ("hp", "pct", 10), ("gold_mult", "pct", 8)]),
        ]
    ),
    "marble": DiceSet(
        key="marble", name="Marble", rarity="Uncommon",
        tiers=[
            SetBonusTier(2, [("hp", "pct", 10), ("defense", "pct", 8)]),
            SetBonusTier(4, [("hp", "pct", 18), ("defense", "pct", 15),
                             ("slots_mult", "pct", 8)]),
            SetBonusTier(6, [("hp", "pct", 28), ("defense", "pct", 20),
                             ("slots_mult", "pct", 15), ("gold_mult", "pct", 8)]),
        ]
    ),
    "iron": DiceSet(
        key="iron", name="Iron", rarity="Uncommon",
        tiers=[
            SetBonusTier(2, [("hp", "pct", 8), ("defense", "pct", 8)]),
            SetBonusTier(4, [("hp", "pct", 15), ("defense", "pct", 15),
                             ("gold_mult", "pct", 4)]),
            SetBonusTier(6, [("hp", "pct", 25), ("defense", "pct", 20),
                             ("gold_mult", "pct", 10), ("idle_gold_ps", "flat", 1.0)]),
        ]
    ),
    "resin": DiceSet(
        key="resin", name="Resin", rarity="Uncommon",
        tiers=[
            SetBonusTier(2, [("atk", "pct", 8), ("roulette_mult", "pct", 5)]),
            SetBonusTier(4, [("atk", "pct", 15), ("speed", "pct", 8),
                             ("roulette_mult", "pct", 10)]),
            SetBonusTier(6, [("atk", "pct", 25), ("speed", "pct", 15),
                             ("roulette_mult", "pct", 15), ("gold_mult", "pct", 8)]),
        ]
    ),
    "glass": DiceSet(
        key="glass", name="Glass", rarity="Uncommon",
        tiers=[
            SetBonusTier(2, [("atk", "pct", 10), ("speed", "pct", 10)]),
            SetBonusTier(4, [("atk", "pct", 18), ("speed", "pct", 15),
                             ("gold_mult", "pct", 5)]),
            SetBonusTier(6, [("atk", "pct", 25), ("speed", "pct", 20),
                             ("gold_mult", "pct", 10), ("shard_rate_mult", "pct", 10)]),
        ]
    ),

    # ------------------ Rare ------------------
    "obsidian": DiceSet(
        key="obsidian", name="Obsidian", rarity="Rare",
        tiers=[
            SetBonusTier(2, [("defense", "pct", 10), ("hp", "pct", 8)]),
            SetBonusTier(4, [("defense", "pct", 20), ("hp", "pct", 15),
                             ("slots_mult", "pct", 12), ("gold_mult", "pct", 6)]),
            SetBonusTier(6, [("defense", "pct", 30), ("hp", "pct", 25),
                             ("slots_mult", "pct", 20), ("gold_mult", "pct", 10)]),
        ]
    ),
    "lapis": DiceSet(
        key="lapis", name="Lapis", rarity="Rare",
        tiers=[
            SetBonusTier(2, [("speed", "pct", 10), ("atk", "pct", 8)]),
            SetBonusTier(4, [("speed", "pct", 20), ("atk", "pct", 15),
                             ("roulette_mult", "pct", 12)]),
            SetBonusTier(6, [("speed", "pct", 28), ("atk", "pct", 20),
                             ("roulette_mult", "pct", 20), ("gold_mult", "pct", 10)]),
        ]
    ),
    "amethyst": DiceSet(
        key="amethyst", name="Amethyst", rarity="Rare",
        tiers=[
            SetBonusTier(2, [("atk", "pct", 10), ("hp", "pct", 8)]),
            SetBonusTier(4, [("atk", "pct", 20), ("hp", "pct", 15),
                             ("gold_mult", "pct", 8)]),
            SetBonusTier(6, [("atk", "pct", 30), ("hp", "pct", 25),
                             ("gold_mult", "pct", 12), ("shard_rate_mult", "pct", 20)]),
        ]
    ),
    "emerald": DiceSet(
        key="emerald", name="Emerald", rarity="Rare",
        tiers=[
            SetBonusTier(2, [("defense", "pct", 10), ("gold_mult", "pct", 4)]),
            SetBonusTier(4, [("defense", "pct", 18), ("hp", "pct", 12),
                             ("gold_mult", "pct", 8), ("idle_gold_ps", "flat", 1.0)]),
            SetBonusTier(6, [("defense", "pct", 25), ("hp", "pct", 18),
                             ("gold_mult", "pct", 12), ("idle_gold_ps", "flat", 2.0)]),
        ]
    ),
    "labradorite": DiceSet(
        key="labradorite", name="Labradorite", rarity="Rare",
        tiers=[
            SetBonusTier(2, [("speed", "pct", 10), ("shard_rate_mult", "pct", 10)]),
            SetBonusTier(4, [("speed", "pct", 20), ("atk", "pct", 10),
                             ("shard_rate_mult", "pct", 20)]),
            SetBonusTier(6, [("speed", "pct", 25), ("atk", "pct", 15),
                             ("shard_rate_mult", "pct", 30), ("gold_mult", "pct", 10)]),
        ]
    ),

    # ------------------ Legendary ------------------
    "volcanic": DiceSet(
        key="volcanic", name="Volcanic", rarity="Legendary",
        tiers=[
            SetBonusTier(2, [("atk", "pct", 15), ("speed", "pct", 10)]),
            SetBonusTier(4, [("atk", "pct", 30), ("speed", "pct", 20),
                             ("gold_mult", "pct", 10)]),
            SetBonusTier(6, [("atk", "pct", 45), ("speed", "pct", 30),
                             ("gold_mult", "pct", 20), ("idle_gold_ps", "flat", 2.0)]),
        ]
    ),
    "prism": DiceSet(
        key="prism", name="Prism", rarity="Legendary",
        tiers=[
            SetBonusTier(2, [("atk", "pct", 12), ("hp", "pct", 10), ("defense", "pct", 10)]),
            SetBonusTier(4, [("atk", "pct", 25), ("hp", "pct", 20), ("defense", "pct", 20),
                             ("slots_mult", "pct", 15), ("roulette_mult", "pct", 15)]),
            SetBonusTier(6, [("atk", "pct", 40), ("hp", "pct", 30), ("defense", "pct", 25),
                             ("slots_mult", "pct", 25), ("roulette_mult", "pct", 25),
                             ("gold_mult", "pct", 15)]),
        ]
    ),
    "moonstone": DiceSet(
        key="moonstone", name="Moonstone", rarity="Legendary",
        tiers=[
            SetBonusTier(2, [("speed", "pct", 12), ("shard_rate_mult", "pct", 15)]),
            SetBonusTier(4, [("speed", "pct", 25), ("atk", "pct", 15),
                             ("shard_rate_mult", "pct", 25), ("idle_gold_ps", "flat", 1.5)]),
            SetBonusTier(6, [("speed", "pct", 35), ("atk", "pct", 25),
                             ("shard_rate_mult", "pct", 35), ("gold_mult", "pct", 15)]),
        ]
    ),
    "star": DiceSet(
        key="star", name="Star", rarity="Legendary",
        tiers=[
            SetBonusTier(2, [("atk", "pct", 15), ("speed", "pct", 15)]),
            SetBonusTier(4, [("atk", "pct", 30), ("speed", "pct", 25),
                             ("gold_mult", "pct", 12), ("idle_gold_ps", "flat", 1.2)]),
            SetBonusTier(6, [("atk", "pct", 45), ("speed", "pct", 35),
                             ("gold_mult", "pct", 20), ("shard_rate_mult", "pct", 30)]),
        ]
    ),
    "dragon": DiceSet(
        key="dragon", name="Dragon", rarity="Legendary",
        tiers=[
            SetBonusTier(2, [("hp", "pct", 15), ("atk", "pct", 10)]),
            SetBonusTier(4, [("hp", "pct", 30), ("atk", "pct", 25),
                             ("gold_mult", "pct", 15), ("slots_mult", "pct", 10)]),
            SetBonusTier(6, [("hp", "pct", 45), ("atk", "pct", 35),
                             ("gold_mult", "pct", 25), ("slots_mult", "pct", 20),
                             ("shard_rate_mult", "pct", 25)]),
        ]
    ),
    "frozen": DiceSet(
        key="frozen", name="Frozen", rarity="Legendary",
        tiers=[
            SetBonusTier(2, [("defense", "pct", 15), ("hp", "pct", 10)]),
            SetBonusTier(4, [("defense", "pct", 25), ("hp", "pct", 20),
                             ("roulette_mult", "pct", 12), ("gold_mult", "pct", 10)]),
            SetBonusTier(6, [("defense", "pct", 35), ("hp", "pct", 30),
                             ("roulette_mult", "pct", 20), ("gold_mult", "pct", 20),
                             ("shard_rate_mult", "pct", 30)]),
        ]
    ),
}

# ============================================================
# Template generation (100 dice)
# ============================================================

BASE_BY_SIDES = {
    4:  {"hp": 6,   "atk": 4,  "def": 3,  "spd": 4},
    6:  {"hp": 8,   "atk": 5,  "def": 4,  "spd": 5},
    8:  {"hp": 10,  "atk": 6,  "def": 5,  "spd": 6},
    12: {"hp": 14,  "atk": 8,  "def": 7,  "spd": 7},
    20: {"hp": 18,  "atk": 10, "def": 9,  "spd": 8},
}

RARITY_MULT = {
    "Common":    1.00,
    "Uncommon":  1.40,
    "Rare":      1.65,
    "Legendary": 2.00,
}

# Economy identity weights for per-die (small, sets give the bigger bonuses)
ECON_IDENT = {
    # Common
    "wooden":      {"gold": 1.0, "idle": 0.7, "slots": 0.0, "roulette": 0.0, "shards": 0.0},
    "stone":       {"gold": 0.4, "idle": 0.2, "slots": 1.0, "roulette": 0.0, "shards": 0.0},
    "plastic":     {"gold": 0.4, "idle": 0.2, "slots": 0.0, "roulette": 1.0, "shards": 0.0},
    "clay":        {"gold": 0.5, "idle": 0.6, "slots": 0.0, "roulette": 0.0, "shards": 1.0},
    "aluminum":    {"gold": 0.7, "idle": 0.5, "slots": 0.0, "roulette": 0.0, "shards": 0.0},
    # Uncommon
    "bone":        {"gold": 0.6, "idle": 0.0, "slots": 0.0, "roulette": 0.3, "shards": 0.0},
    "marble":      {"gold": 0.5, "idle": 0.4, "slots": 0.9, "roulette": 0.0, "shards": 0.0},
    "iron":        {"gold": 0.8, "idle": 0.5, "slots": 0.0, "roulette": 0.0, "shards": 0.0},
    "resin":       {"gold": 0.4, "idle": 0.0, "slots": 0.0, "roulette": 0.9, "shards": 0.0},
    "glass":       {"gold": 0.9, "idle": 0.0, "slots": 0.0, "roulette": 0.0, "shards": 0.5},
    # Rare
    "obsidian":    {"gold": 0.8, "idle": 0.4, "slots": 1.0, "roulette": 0.0, "shards": 0.0},
    "lapis":       {"gold": 0.7, "idle": 0.0, "slots": 0.0, "roulette": 1.0, "shards": 0.0},
    "amethyst":    {"gold": 1.0, "idle": 0.0, "slots": 0.0, "roulette": 0.3, "shards": 0.7},
    "emerald":     {"gold": 1.0, "idle": 1.0, "slots": 0.0, "roulette": 0.0, "shards": 0.0},
    "labradorite": {"gold": 0.8, "idle": 0.0, "slots": 0.0, "roulette": 0.3, "shards": 1.0},
    # Legendary
    "volcanic":    {"gold": 1.0, "idle": 0.7, "slots": 0.0, "roulette": 0.4, "shards": 0.0},
    "prism":       {"gold": 1.0, "idle": 0.6, "slots": 1.0, "roulette": 1.0, "shards": 0.0},
    "moonstone":   {"gold": 1.0, "idle": 0.9, "slots": 0.0, "roulette": 0.0, "shards": 1.0},
    "star":        {"gold": 1.0, "idle": 0.8, "slots": 0.0, "roulette": 0.0, "shards": 0.8},
    "dragon":      {"gold": 1.2, "idle": 0.5, "slots": 1.0, "roulette": 0.0, "shards": 0.8},
    "frozen":      {"gold": 1.1, "idle": 0.5, "slots": 0.0, "roulette": 1.0, "shards": 0.9},
}

SIDE_SCALE = {4: 0.6, 6: 0.85, 8: 1.0, 12: 1.2, 20: 1.5}

RARITY_ECON_CAP = {
    "Common":    {"gold_pct": 3.0, "idle": 0.3, "slots_pct": 2.0, "roulette_pct": 2.0, "shards_pct": 8.0},
    "Uncommon":  {"gold_pct": 5.0, "idle": 0.5, "slots_pct": 4.0, "roulette_pct": 4.0, "shards_pct": 12.0},
    "Rare":      {"gold_pct": 8.0, "idle": 0.8, "slots_pct": 7.0, "roulette_pct": 7.0, "shards_pct": 18.0},
    "Legendary": {"gold_pct": 12.0,"idle": 1.2, "slots_pct": 10.0,"roulette_pct": 10.0,"shards_pct": 25.0},
}

# NEW: crit identity (per set) — weights for crit chance and crit multiplier
CRIT_IDENT = {
    # Common
    "wooden":      {"chance": 0.6, "mult": 0.6},
    "stone":       {"chance": 0.4, "mult": 0.7},
    "plastic":     {"chance": 0.8, "mult": 0.7},
    "clay":        {"chance": 0.5, "mult": 0.6},
    "aluminum":    {"chance": 0.7, "mult": 0.6},
    # Uncommon
    "bone":        {"chance": 0.8, "mult": 0.7},
    "marble":      {"chance": 0.5, "mult": 0.8},
    "iron":        {"chance": 0.4, "mult": 0.9},
    "resin":       {"chance": 0.7, "mult": 0.8},
    "glass":       {"chance": 1.0, "mult": 1.0},  # glass = crity
    # Rare
    "obsidian":    {"chance": 0.6, "mult": 1.0},
    "lapis":       {"chance": 0.9, "mult": 0.9},
    "amethyst":    {"chance": 0.9, "mult": 1.0},
    "emerald":     {"chance": 0.6, "mult": 0.9},
    "labradorite": {"chance": 0.8, "mult": 0.9},
    # Legendary
    "volcanic":    {"chance": 0.9, "mult": 1.0},
    "prism":       {"chance": 0.9, "mult": 1.0},
    "moonstone":   {"chance": 0.8, "mult": 1.0},
    "star":        {"chance": 1.0, "mult": 1.1},
    "dragon":      {"chance": 0.9, "mult": 1.2},
    "frozen":      {"chance": 0.7, "mult": 1.1},
}

def _econ_for_template(set_key: str, rarity: str, sides: int):
    ident = ECON_IDENT.get(set_key, {"gold":0,"idle":0,"slots":0,"roulette":0,"shards":0})
    cap = RARITY_ECON_CAP[rarity]; s = SIDE_SCALE[sides]
    total_w = sum(ident.values()) or 1.0
    gold_pct    = cap["gold_pct"]    * (ident["gold"]/total_w)    * s
    idle        = cap["idle"]        * (ident["idle"]/total_w)    * s
    slots_pct   = cap["slots_pct"]   * (ident["slots"]/total_w)   * s
    roulette_pct= cap["roulette_pct"]* (ident["roulette"]/total_w)* s
    shards_pct  = cap["shards_pct"]  * (ident["shards"]/total_w)  * s
    return {
        "gold_mult_pct": round(gold_pct, 2),
        "idle_gold_ps": round(idle, 2),
        "slots_mult_pct": round(slots_pct, 2),
        "roulette_mult_pct": round(roulette_pct, 2),
        "shard_rate_mult_pct": round(shards_pct, 2),
    }

def _base_stats(set_key: str, rarity: str, sides: int):
    b = BASE_BY_SIDES[sides]; r = RARITY_MULT[rarity]
    flavor = {
        # Common (widened so integer rounding no longer masks differences)
        "stone":       {"hp": 1.12, "atk": 0.92, "def": 1.18, "spd": 0.90},
        "plastic":     {"hp": 0.90, "atk": 1.12, "def": 0.90, "spd": 1.20},
        "clay":        {"hp": 1.10, "atk": 0.95, "def": 1.12, "spd": 0.92},
        "aluminum":    {"hp": 0.92, "atk": 1.12, "def": 0.92, "spd": 1.20},
        "bone":        {"hp": 0.98, "atk": 1.10, "def": 0.98, "spd": 1.06},
        "marble":      {"hp": 1.10, "atk": 0.98, "def": 1.10, "spd": 0.97},
        "iron":        {"hp": 1.08, "atk": 0.98, "def": 1.12, "spd": 0.96},
        "resin":       {"hp": 0.97, "atk": 1.10, "def": 0.97, "spd": 1.05},
        "glass":       {"hp": 0.97, "atk": 1.12, "def": 0.96, "spd": 1.08},
        "obsidian":    {"hp": 1.12, "atk": 1.00, "def": 1.15, "spd": 0.98},
        "lapis":       {"hp": 1.00, "atk": 1.10, "def": 1.00, "spd": 1.12},
        "amethyst":    {"hp": 1.10, "atk": 1.12, "def": 1.02, "spd": 1.02},
        "emerald":     {"hp": 1.08, "atk": 1.02, "def": 1.12, "spd": 1.00},
        "labradorite": {"hp": 1.02, "atk": 1.10, "def": 1.02, "spd": 1.15},
        "volcanic":    {"hp": 1.06, "atk": 1.18, "def": 1.02, "spd": 1.12},
        "prism":       {"hp": 1.12, "atk": 1.12, "def": 1.12, "spd": 1.10},
        "moonstone":   {"hp": 1.04, "atk": 1.08, "def": 1.04, "spd": 1.18},
        "star":        {"hp": 1.02, "atk": 1.16, "def": 1.02, "spd": 1.18},
        "dragon":      {"hp": 1.20, "atk": 1.16, "def": 1.10, "spd": 1.05},
        "frozen":      {"hp": 1.12, "atk": 1.02, "def": 1.20, "spd": 1.02},
    }.get(set_key, {"hp": 1.0, "atk": 1.0, "def": 1.0, "spd": 1.0})

    return {
        "hp":      int(round(b["hp"]   * r * flavor["hp"])),
        "atk":     int(round(b["atk"]  * r * flavor["atk"])),
        "defense": int(round(b["def"]  * r * flavor["def"])),
        "speed":   int(round(b["spd"]  * r * flavor["spd"])),
    }

# NEW: per-die crit baselines by rarity + set flavor + sides
RARITY_CRIT = {
    "Common":    {"chance": 1.0, "mult": 1.50},
    "Uncommon":  {"chance": 2.0, "mult": 1.55},
    "Rare":      {"chance": 3.0, "mult": 1.65},
    "Legendary": {"chance": 4.0, "mult": 1.80},
}

def _crit_for_template(set_key: str, rarity: str, sides: int):
    base = RARITY_CRIT[rarity]
    ident = CRIT_IDENT.get(set_key, {"chance": 0.6, "mult": 0.6})
    s = SIDE_SCALE[sides]
    # Chance scales gently with sides; multiplier gets a tiny bump too
    chance = base["chance"] * (0.8 + 0.2 * s) * (0.7 + 0.6 * ident["chance"])
    mult   = base["mult"]   * (0.98 + 0.02 * s) * (0.9 + 0.2 * ident["mult"])
    # clamp reasonable bounds
    chance = round(max(0.5, min(chance, 12.0)), 2)  # %
    mult   = round(max(1.4, min(mult, 2.2)), 2)
    return {"crit_chance_pct": chance, "crit_mult": mult}

def _title_case(s: str) -> str:
    return s[:1].upper() + s[1:]

def _make_template(set_key: str, rarity: str, sides: int) -> DiceTemplate:
    stats = _base_stats(set_key, rarity, sides)
    econ = _econ_for_template(set_key, rarity, sides)
    crt  = _crit_for_template(set_key, rarity, sides)
    key = f"{set_key}_d{sides}"
    name = f"{_title_case(set_key)} d{sides}"
    return DiceTemplate(
        key=key,
        name=name,
        set_key=set_key,
        set_name=_title_case(set_key),
        rarity=rarity,
        sides=sides,
        hp=stats["hp"], atk=stats["atk"], defense=stats["defense"], speed=stats["speed"],
        crit_chance_pct=crt["crit_chance_pct"], crit_mult=crt["crit_mult"],
        gold_mult_pct=econ["gold_mult_pct"], idle_gold_ps=econ["idle_gold_ps"],
        slots_mult_pct=econ["slots_mult_pct"], roulette_mult_pct=econ["roulette_mult_pct"],
        shard_rate_mult_pct=econ["shard_rate_mult_pct"],
    )

def _build_templates() -> Dict[str, DiceTemplate]:
    templates: Dict[str, DiceTemplate] = {}
    for set_key, s in SETS.items():
        rarity = s.rarity
        for sides in (4, 6, 8, 12, 20):
            t = _make_template(set_key, rarity, sides)
            templates[t.key] = t

    # Starter polish: Wooden d8 is a tad more econ-friendly
    if "wooden_d8" in templates:
        t = templates["wooden_d8"]
        templates["wooden_d8"] = DiceTemplate(
            key=t.key, name=t.name, set_key=t.set_key, set_name=t.set_name,
            rarity=t.rarity, sides=t.sides,
            hp=t.hp, atk=t.atk, defense=t.defense, speed=t.speed,
            crit_chance_pct=t.crit_chance_pct, crit_mult=t.crit_mult,
            gold_mult_pct=round(t.gold_mult_pct + 0.5, 2),
            idle_gold_ps=round(t.idle_gold_ps + 0.05, 2),
            slots_mult_pct=t.slots_mult_pct, roulette_mult_pct=t.roulette_mult_pct,
            shard_rate_mult_pct=t.shard_rate_mult_pct,
        )
    return templates

TEMPLATES: Dict[str, DiceTemplate] = _build_templates()

# ============================================================
# Public accessors
# ============================================================

def get_templates() -> Dict[str, DiceTemplate]:
    return TEMPLATES

def get_sets() -> Dict[str, DiceSet]:
    return SETS
