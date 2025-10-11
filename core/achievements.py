from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class AchvDef:
    key: str
    name: str
    desc: str
    category: str  # "Progress", "Buildings", "Scrap", "Games", "Collection"
    type: str      # progress metric key understood by Game.list_achievements
    target: float
    reward_diamonds: int
    # Optional multi-stage targets; if provided, UI will expand into separate tiered achievements
    stages: Optional[List[float]] = None
    stage_rewards: Optional[List[int]] = None


ACHIEVEMENTS: List[AchvDef] = [
    # Progress: lifetime gold
    AchvDef("lg_1k",   "First Grand",    "Reach 1,000 lifetime gold.", "Progress", "lifetime_gold", 1_000, 2),
    AchvDef("lg_10k",  "Ten-Spot",       "Reach 10,000 lifetime gold.", "Progress", "lifetime_gold", 10_000, 5),
    AchvDef("lg_100k", "Rolling In",     "Reach 100,000 lifetime gold.", "Progress", "lifetime_gold", 100_000, 10),

    # Buildings: total owned
    AchvDef("bld_10",  "Construction Crew", "Own 10 total buildings.", "Buildings", "buildings_owned_total", 10, 3),
    AchvDef("bld_50",  "Small Empire",      "Own 50 total buildings.", "Buildings", "buildings_owned_total", 50, 8),
    AchvDef("bld_200", "Casino Tycoon",     "Own 200 total buildings.", "Buildings", "buildings_owned_total", 200, 20),

    # Scrap totals
    AchvDef("scrap_1k",   "Grease Monkey",  "Accumulate 1,000 scrap.", "Scrap", "scrap_total", 1_000, 2),
    AchvDef("scrap_10k",  "Metal Hoarder",  "Accumulate 10,000 scrap.", "Scrap", "scrap_total", 10_000, 6),
    AchvDef("scrap_100k", "Industrialist",  "Accumulate 100,000 scrap.", "Scrap", "scrap_total", 100_000, 18),
    AchvDef("scrap_idle_1", "Passive Works", "Reach 1.0 scrap/s passive.", "Scrap", "scrap_idle_rate", 1.0, 5),
    AchvDef("scrap_idle_5", "Factory Flow",  "Reach 5.0 scrap/s passive.", "Scrap", "scrap_idle_rate", 5.0, 12),

    # Games unlocks
    AchvDef("unlock_slots",    "Slot Access",    "Unlock the Slots game.", "Games", "unlock_slots", 1, 3),
    AchvDef("unlock_roulette",  "Wheel Access",   "Unlock the Roulette game.", "Games", "unlock_roulette", 1, 6),

    # Crates and collection
    AchvDef("cr_basic_10",  "Getting Scrappy", "Open 10 Basic scrap crates.", "Collection", "crates_basic", 10, 4),
    AchvDef("cr_adv_5",     "Upcycling",       "Open 5 Advanced scrap crates.", "Collection", "crates_advanced", 5, 8),
    AchvDef("leg_own_1",    "Legendary Find",  "Own at least one Legendary die.", "Collection", "have_legendary", 1, 20),

    # --- Multi-stage examples ---
    AchvDef(
        key="builder",
        name="Master Builder",
        desc="Own many buildings.",
        category="Buildings",
        type="buildings_owned_total",
        target=25,
        reward_diamonds=4,
        stages=[25, 100, 300],
        stage_rewards=[4, 12, 30],
    ),
    AchvDef(
        key="scrap_tycoon",
        name="Scrap Tycoon",
        desc="Accumulate scrap reserves.",
        category="Scrap",
        type="scrap_total",
        target=5_000,
        reward_diamonds=3,
        stages=[5_000, 50_000, 250_000],
        stage_rewards=[3, 10, 25],
    ),
    AchvDef(
        key="high_roller",
        name="High Roller",
        desc="Reach massive lifetime gold milestones.",
        category="Progress",
        type="lifetime_gold",
        target=1_000_000,
        reward_diamonds=15,
        stages=[1_000_000, 10_000_000],
        stage_rewards=[15, 40],
    ),

    # New singles
    AchvDef("collection_20", "Collector", "Own 20 dice.", "Collection", "inventory_size", 20, 8),
    AchvDef("collection_60", "Archivist", "Own 60 dice.", "Collection", "inventory_size", 60, 20),
    AchvDef("crates_20", "Crate Diver", "Open 20 total scrap crates.", "Collection", "crates_total", 20, 6),
    AchvDef("idle_gold_200", "Idle Earner", "Reach 200 gold/s idle income.", "Progress", "idle_gold_ps", 200, 10),

    # Games activity
    AchvDef("dice_plays_100", "Dice Grinder", "Play dice 100 times.", "Games", "dice_plays", 100, 6),
    AchvDef("slots_spins_100", "Reel Rookie", "Spin slots 100 times.", "Games", "slots_spins", 100, 6),
    AchvDef("slots_wins_50", "Spin Winner", "Win on slots 50 times.", "Games", "slots_wins", 50, 8),
    AchvDef("roulette_spins_50", "Table Regular", "Spin roulette 50 times.", "Games", "roulette_spins", 50, 8),
    AchvDef("roulette_wins_20", "Wheel Winner", "Win 20 roulette spins.", "Games", "roulette_wins", 20, 12),
]
