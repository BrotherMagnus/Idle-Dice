# combat_abilities.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Any, Tuple, Set

# ---- Lightweight combat scaffold ----
# You can wire these into your future battler without changing the game/save code.

# Triggers where abilities can fire
TRIGGER_ON_BATTLE_START   = "on_battle_start"
TRIGGER_ON_TURN_START     = "on_turn_start"
TRIGGER_ON_ATTACK         = "on_attack"         # just before damage is applied
TRIGGER_ON_HIT            = "on_hit"            # after damage is applied
TRIGGER_ON_TAKEN_DAMAGE   = "on_taken_damage"
TRIGGER_ON_ROLL_MAX       = "on_roll_max"       # e.g. rolled max face
TRIGGER_ON_KILL           = "on_kill"

@dataclass
class Unit:
    """Minimal unit state the abilities operate on.
    Your full battler can expand this (statuses, crit, energy, etc.)."""
    name: str
    max_hp: int
    hp: int
    atk: int
    defense: int
    speed: int
    # derived/temporary combat stats
    crit_chance: float = 0.05
    crit_mult: float = 1.5
    lifesteal_pct: float = 0.0
    dodge_chance: float = 0.0
    thorns_pct: float = 0.0
    armor_pen_pct: float = 0.0
    gold_steal_pct: float = 0.0  # convert dmg to gold (economy tie-in)
    # status flags / counters
    shield: int = 0
    stunned: bool = False
    frozen: bool = False
    fear: bool = False

@dataclass
class Team:
    units: List[Unit]

@dataclass
class CombatCtx:
    """Runtime context provided to abilities."""
    rnd: Callable[[], float]           # RNG in [0,1)
    log: Callable[[str], None]         # logger
    self_team: Team
    enemy_team: Team
    self_unit: Unit                    # unit whose ability is executing
    enemy_unit: Optional[Unit] = None  # primary target, if any
    last_roll: Optional[int] = None    # for dice-triggered effects
    max_face: Optional[int] = None     # the die's sides for max-roll checks
    damage: Optional[int] = None       # dmg about to be dealt/just dealt

# Ability function signature: returns optional (new_damage, extra_effects)
AbilityFn = Callable[[CombatCtx], Optional[Any]]

@dataclass(frozen=True)
class AbilityDef:
    key: str
    name: str
    trigger: str
    desc: str
    params: Dict[str, Any]
    impl: AbilityFn

# ------------- small helpers -------------
def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))

def pick_enemy(ctx: CombatCtx) -> Optional[Unit]:
    # simplistic: first alive
    for u in ctx.enemy_team.units:
        if u.hp > 0:
            return u
    return None

def team_buff(team: Team, stat: str, amt: float, ctx: CombatCtx):
    for u in team.units:
        if stat == "atk":
            delta = int(round(amt))
            u.atk += delta
        elif stat == "speed":
            delta = int(round(amt))
            u.speed += delta
        elif stat == "defense":
            delta = int(round(amt))
            u.defense += delta

# ------------- implementations for each material -------------

def impl_rally(ctx: CombatCtx):
    """Wooden — Rally: On max roll, buff team ATK."""
    if ctx.last_roll is not None and ctx.max_face and ctx.last_roll == ctx.max_face:
        inc = ctx.self_unit.atk * ctx.ability.params.get("atk_pct", 0.10)
        team_buff(ctx.self_team, "atk", inc, ctx)
        ctx.log(f"[Rally] Team ATK +{int(inc)} from {ctx.self_unit.name}")

def impl_bulwark(ctx: CombatCtx):
    """Stone — Bulwark: Gain a shield when taking damage."""
    dmg = ctx.damage or 0
    shield = int(dmg * ctx.ability.params.get("shield_pct", 0.20))
    ctx.self_unit.shield += shield
    ctx.log(f"[Bulwark] {ctx.self_unit.name} gains shield {shield}")

def impl_quickstep(ctx: CombatCtx):
    """Plastic — Quickstep: On attack, small chance extra action (speed burst)."""
    if ctx.rnd() < ctx.ability.params.get("extra_action_chance", 0.12):
        inc = ctx.ability.params.get("speed_flat", 2)
        ctx.self_unit.speed += inc
        ctx.log(f"[Quickstep] {ctx.self_unit.name} gains +{inc} speed (extra action potential)")

def impl_mend(ctx: CombatCtx):
    """Clay — Mend: Turn start, heal % max HP."""
    heal = int(ctx.self_unit.max_hp * ctx.ability.params.get("heal_pct", 0.04))
    ctx.self_unit.hp = clamp(ctx.self_unit.hp + heal, 0, ctx.self_unit.max_hp)
    ctx.log(f"[Mend] {ctx.self_unit.name} heals {heal}")

def impl_overclock(ctx: CombatCtx):
    """Aluminum — Overclock: Battle start, team speed buff."""
    inc = ctx.ability.params.get("team_speed", 2)
    team_buff(ctx.self_team, "speed", inc, ctx)
    ctx.log(f"[Overclock] Team speed +{inc}")

def impl_bone_piercer(ctx: CombatCtx):
    """Bone — Piercer: Attacks ignore % defense."""
    ctx.self_unit.armor_pen_pct = max(ctx.self_unit.armor_pen_pct,
                                      ctx.ability.params.get("armor_pen_pct", 0.20))
    ctx.log(f"[Bone Piercer] Armor penetration set to {int(ctx.self_unit.armor_pen_pct*100)}%")

def impl_statue(ctx: CombatCtx):
    """Marble — Statue: Turn start, flat damage reduction (as shield)."""
    ctx.self_unit.shield += ctx.ability.params.get("shield_flat", 8)
    ctx.log(f"[Statue] {ctx.self_unit.name} gains {ctx.ability.params.get('shield_flat', 8)} shield")

def impl_fortify(ctx: CombatCtx):
    """Iron — Fortify: Battle start, team defense up."""
    inc = ctx.ability.params.get("team_def", 2)
    team_buff(ctx.self_team, "defense", inc, ctx)
    ctx.log(f"[Fortify] Team defense +{inc}")

def impl_sticky(ctx: CombatCtx):
    """Resin — Sticky: On hit, slow target (reduce speed)."""
    tgt = ctx.enemy_unit or pick_enemy(ctx)
    if tgt:
        dec = ctx.ability.params.get("slow_flat", 2)
        tgt.speed = max(1, tgt.speed - dec)
        ctx.log(f"[Sticky] {tgt.name} speed -{dec}")

def impl_fragile_focus(ctx: CombatCtx):
    """Glass — Fragile Focus: High crit chance, small self-damage on attack."""
    ctx.self_unit.crit_chance = max(ctx.self_unit.crit_chance,
                                    ctx.ability.params.get("crit_chance", 0.20))
    recoil = ctx.ability.params.get("recoil", 1)
    ctx.self_unit.hp = max(1, ctx.self_unit.hp - recoil)
    ctx.log(f"[Fragile Focus] Crit chance boosted; {ctx.self_unit.name} takes {recoil} recoil")

def impl_void_edge(ctx: CombatCtx):
    """Obsidian — Void Edge: Thorns reflect % of taken damage."""
    ctx.self_unit.thorns_pct = max(ctx.self_unit.thorns_pct,
                                   ctx.ability.params.get("thorns_pct", 0.25))
    ctx.log(f"[Void Edge] Thorns set to {int(ctx.self_unit.thorns_pct*100)}%")

def impl_tidal_surge(ctx: CombatCtx):
    """Lapis — Tidal Surge: On hit, chance to stun."""
    tgt = ctx.enemy_unit or pick_enemy(ctx)
    if tgt and ctx.rnd() < ctx.ability.params.get("stun_chance", 0.12):
        tgt.stunned = True
        ctx.log(f"[Tidal Surge] {tgt.name} is stunned")

def impl_arcane_echo(ctx: CombatCtx):
    """Amethyst — Arcane Echo: On roll max, duplicate lowest ally ATK to target."""
    if ctx.last_roll is not None and ctx.max_face and ctx.last_roll == ctx.max_face:
        lowest = min(ctx.self_team.units, key=lambda u: u.atk)
        bonus = int(lowest.atk * ctx.ability.params.get("echo_pct", 0.5))
        if ctx.enemy_unit:
            # Return an extra damage chunk for the engine to add
            ctx.log(f"[Arcane Echo] Extra damage {bonus} from lowest ally {lowest.name}")
            return {"extra_damage": bonus}

def impl_prosperity(ctx: CombatCtx):
    """Emerald — Prosperity: Convert % of dealt damage into gold."""
    ctx.self_unit.gold_steal_pct = max(ctx.self_unit.gold_steal_pct,
                                       ctx.ability.params.get("gold_steal_pct", 0.10))
    ctx.log(f"[Prosperity] {int(ctx.self_unit.gold_steal_pct*100)}% of damage converts to gold")

def impl_shimmer(ctx: CombatCtx):
    """Labradorite — Shimmer: Turn start, chance to gain dodge."""
    if ctx.rnd() < ctx.ability.params.get("proc", 0.25):
        ctx.self_unit.dodge_chance = max(ctx.self_unit.dodge_chance,
                                         ctx.ability.params.get("dodge", 0.25))
        ctx.log(f"[Shimmer] {ctx.self_unit.name} gains {int(ctx.self_unit.dodge_chance*100)}% dodge this turn")

def impl_eruption(ctx: CombatCtx):
    """Volcanic — Eruption: On attack, small AoE splash to others."""
    splash = ctx.ability.params.get("splash", 3)
    # The engine can add this as extra_damage to non-primary enemies
    ctx.log(f"[Eruption] Splash {splash} to other enemies")
    return {"splash_damage": splash}

def impl_prismatic_harmony(ctx: CombatCtx):
    """Prism — Harmony: Turn start, random small buff to team."""
    roll = ctx.rnd()
    if roll < 0.33:
        team_buff(ctx.self_team, "atk", 2, ctx); ctx.log("[Harmony] Team ATK +2")
    elif roll < 0.66:
        team_buff(ctx.self_team, "speed", 2, ctx); ctx.log("[Harmony] Team SPEED +2")
    else:
        team_buff(ctx.self_team, "defense", 2, ctx); ctx.log("[Harmony] Team DEF +2")

def impl_lunar_blessing(ctx: CombatCtx):
    """Moonstone — Lifesteal buff."""
    ctx.self_unit.lifesteal_pct = max(ctx.self_unit.lifesteal_pct,
                                      ctx.ability.params.get("lifesteal", 0.15))
    ctx.log(f"[Lunar Blessing] Lifesteal set to {int(ctx.self_unit.lifesteal_pct*100)}%")

def impl_supernova(ctx: CombatCtx):
    """Star — Execute low HP on hit."""
    tgt = ctx.enemy_unit or pick_enemy(ctx)
    if not tgt: return
    threshold = ctx.ability.params.get("execute_pct", 0.10)
    if tgt.hp / max(1, tgt.max_hp) <= threshold:
        # Indicate to engine we want to execute
        ctx.log(f"[Supernova] Executed {tgt.name}")
        return {"execute": True}

def impl_dragons_roar(ctx: CombatCtx):
    """Dragon — Roar: On attack, chance to fear (lower atk & speed)."""
    tgt = ctx.enemy_unit or pick_enemy(ctx)
    if tgt and ctx.rnd() < ctx.ability.params.get("fear_chance", 0.20):
        tgt.fear = True
        tgt.atk = max(1, int(tgt.atk * 0.85))
        tgt.speed = max(1, int(tgt.speed * 0.85))
        ctx.log(f"[Roar] {tgt.name} is feared (-ATK/-SPD)")

def impl_freeze(ctx: CombatCtx):
    """Frozen — Freeze: On hit, chance to freeze target (skip next turn)."""
    tgt = ctx.enemy_unit or pick_enemy(ctx)
    if tgt and ctx.rnd() < ctx.ability.params.get("freeze_chance", 0.18):
        tgt.frozen = True
        ctx.log(f"[Freeze] {tgt.name} is frozen")

# ------------- Registry: one ability per material (set) -------------

def _ability(key: str, name: str, trigger: str, desc: str, params: Dict[str, Any], impl: AbilityFn) -> AbilityDef:
    return AbilityDef(key=key, name=name, trigger=trigger, desc=desc, params=params, impl=impl)

ABILITIES_BY_SET: Dict[str, AbilityDef] = {
    # Common
    "wooden":      _ability("rally",      "Rally",              TRIGGER_ON_ROLL_MAX,    "On max roll: team ATK up.",              {"atk_pct": 0.10}, impl_rally),
    "stone":       _ability("bulwark",    "Bulwark",            TRIGGER_ON_TAKEN_DAMAGE,"Gain shield equal to % of damage taken.", {"shield_pct": 0.20}, impl_bulwark),
    "plastic":     _ability("quickstep",  "Quickstep",          TRIGGER_ON_ATTACK,      "Chance for speed burst/extra action.",   {"extra_action_chance": 0.12, "speed_flat": 2}, impl_quickstep),
    "clay":        _ability("mend",       "Mend",               TRIGGER_ON_TURN_START,  "Heal a % of max HP each turn.",          {"heal_pct": 0.04}, impl_mend),
    "aluminum":    _ability("overclock",  "Overclock",          TRIGGER_ON_BATTLE_START,"Team speed up at battle start.",          {"team_speed": 2}, impl_overclock),

    # Uncommon
    "bone":        _ability("piercer",    "Bone Piercer",       TRIGGER_ON_ATTACK,      "Attacks ignore % of enemy defense.",     {"armor_pen_pct": 0.20}, impl_bone_piercer),
    "marble":      _ability("statue",     "Statue",             TRIGGER_ON_TURN_START,  "Gain flat shield each turn.",             {"shield_flat": 8}, impl_statue),
    "iron":        _ability("fortify",    "Fortify",            TRIGGER_ON_BATTLE_START,"Team defense up at battle start.",        {"team_def": 2}, impl_fortify),
    "resin":       _ability("sticky",     "Sticky",             TRIGGER_ON_HIT,         "On hit: slow the target.",               {"slow_flat": 2}, impl_sticky),
    "glass":       _ability("focus",      "Fragile Focus",      TRIGGER_ON_ATTACK,      "High crit chance but tiny recoil.",      {"crit_chance": 0.20, "recoil": 1}, impl_fragile_focus),

    # Rare
    "obsidian":    _ability("void_edge",  "Void Edge",          TRIGGER_ON_TAKEN_DAMAGE,"Reflect % damage (thorns).",              {"thorns_pct": 0.25}, impl_void_edge),
    "lapis":       _ability("tidal",      "Tidal Surge",        TRIGGER_ON_HIT,         "On hit: chance to stun.",                {"stun_chance": 0.12}, impl_tidal_surge),
    "amethyst":    _ability("echo",       "Arcane Echo",        TRIGGER_ON_ROLL_MAX,    "On max roll: echo damage from ally.",    {"echo_pct": 0.50}, impl_arcane_echo),
    "emerald":     _ability("prosperity", "Prosperity",         TRIGGER_ON_ATTACK,      "Convert % damage to gold.",              {"gold_steal_pct": 0.10}, impl_prosperity),
    "labradorite": _ability("shimmer",    "Shimmer",            TRIGGER_ON_TURN_START,  "Chance to gain dodge this turn.",        {"proc": 0.25, "dodge": 0.25}, impl_shimmer),

    # Legendary
    "volcanic":    _ability("eruption",   "Eruption",           TRIGGER_ON_ATTACK,      "AoE splash to other enemies.",           {"splash": 3}, impl_eruption),
    "prism":       _ability("harmony",    "Prismatic Harmony",  TRIGGER_ON_TURN_START,  "Random small team buff each turn.",      {}, impl_prismatic_harmony),
    "moonstone":   _ability("lunar",      "Lunar Blessing",     TRIGGER_ON_BATTLE_START,"Gain lifesteal.",                         {"lifesteal": 0.15}, impl_lunar_blessing),
    "star":        _ability("supernova",  "Supernova",          TRIGGER_ON_HIT,         "Execute low-HP enemies.",                {"execute_pct": 0.10}, impl_supernova),
    "dragon":      _ability("roar",       "Dragon's Roar",      TRIGGER_ON_ATTACK,      "Chance to fear on attack.",              {"fear_chance": 0.20}, impl_dragons_roar),
    "frozen":      _ability("freeze",     "Freeze",             TRIGGER_ON_HIT,         "Chance to freeze on hit.",               {"freeze_chance": 0.18}, impl_freeze),
}

# ------------- Public helpers -------------

def list_set_abilities() -> List[Tuple[str, AbilityDef]]:
    """[(set_key, ability)] — can be shown on a UI tooltip or codex."""
    return sorted(ABILITIES_BY_SET.items(), key=lambda kv: kv[0])

def collect_team_abilities(set_keys: List[str]) -> List[AbilityDef]:
    """Unique abilities for the team based on equipped materials."""
    seen: Set[str] = set()
    out: List[AbilityDef] = []
    for sk in set_keys:
        ab = ABILITIES_BY_SET.get(sk)
        if ab and ab.key not in seen:
            out.append(ab); seen.add(ab.key)
    return out

# For engines that want to execute: we attach the chosen AbilityDef to ctx dynamically
def execute_ability(ability: AbilityDef, ctx: CombatCtx) -> Optional[Any]:
    # Attach params+ability onto ctx for impl convenience
    setattr(ctx, "ability", ability)
    return ability.impl(ctx)
