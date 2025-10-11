from __future__ import annotations

import random
import time
import datetime
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional


RewardType = Literal["shards", "diamonds", "gold", "scrap"]


@dataclass(frozen=True)
class BountyTemplate:
    key: str
    name: str
    category: Literal["daily", "weekly"]
    metric: str              # name of Game metric accessor
    target: float
    reward_type: RewardType
    reward_amount: float


class BountyManager:
    def __init__(self) -> None:
        self.daily_reset_at: int = 0
        self.weekly_reset_at: int = 0
        self.daily_claimed: Dict[str, bool] = {}
        self.weekly_claimed: Dict[str, bool] = {}
        self.daily_keys: List[str] = []
        self.weekly_keys: List[str] = []

        # Pool of possible bounties (add more as needed)
        self._pool: Dict[str, BountyTemplate] = {
            # Daily
            "daily_slots_50": BountyTemplate("daily_slots_50", "Spin Slots 50x", "daily", "counter_slots_spins", 50, "shards", 1500),
            "daily_roulette_win_5": BountyTemplate("daily_roulette_win_5", "Win Roulette 5x", "daily", "counter_roulette_wins", 5, "shards", 3000),
            "daily_salvage_10": BountyTemplate("daily_salvage_10", "Convert 2,000 Scrap", "daily", "scrap", 2000, "shards", 2500),
            # Weekly
            "weekly_crates_20": BountyTemplate("weekly_crates_20", "Open 20 Crates", "weekly", "crates_total", 20, "shards", 5000),
            "weekly_roulette_win_50": BountyTemplate("weekly_roulette_win_50", "Win Roulette 50x", "weekly", "counter_roulette_wins", 50, "shards", 12000),
            "weekly_lifetime_gold": BountyTemplate("weekly_lifetime_gold", "Earn 250k lifetime gold", "weekly", "lifetime_gold", 250_000, "diamonds", 25),
        }

    # ---------- persistence ----------
    def to_dict(self) -> dict:
        return {
            "daily_reset_at": self.daily_reset_at,
            "weekly_reset_at": self.weekly_reset_at,
            "daily_claimed": self.daily_claimed,
            "weekly_claimed": self.weekly_claimed,
            "daily_keys": self.daily_keys,
            "weekly_keys": self.weekly_keys,
        }

    def from_dict(self, data: dict) -> None:
        self.daily_reset_at = int(data.get("daily_reset_at", 0))
        self.weekly_reset_at = int(data.get("weekly_reset_at", 0))
        self.daily_claimed = {str(k): bool(v) for k, v in data.get("daily_claimed", {}).items()} if isinstance(data.get("daily_claimed", {}), dict) else {}
        self.weekly_claimed = {str(k): bool(v) for k, v in data.get("weekly_claimed", {}).items()} if isinstance(data.get("weekly_claimed", {}), dict) else {}
        self.daily_keys = list(data.get("daily_keys", []))
        self.weekly_keys = list(data.get("weekly_keys", []))

    # ---------- helpers ----------
    def _now_ts(self) -> int:
        return int(time.time())

    def _next_daily(self) -> int:
        now = datetime.datetime.utcnow()
        nxt = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return int(nxt.timestamp())

    def _next_weekly(self) -> int:
        now = datetime.datetime.utcnow()
        # Monday 00:00 UTC next week
        days_ahead = 7 - now.weekday()
        nxt = (now + datetime.timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)
        return int(nxt.timestamp())

    def _ensure_roll(self) -> None:
        # Initialize reset times if missing
        if not self.daily_reset_at:
            self.daily_reset_at = self._next_daily()
        if not self.weekly_reset_at:
            self.weekly_reset_at = self._next_weekly()

        now = self._now_ts()
        if now >= self.daily_reset_at:
            self.daily_claimed.clear()
            self.daily_keys = self._roll("daily", 2)
            self.daily_reset_at = self._next_daily()
        if now >= self.weekly_reset_at:
            self.weekly_claimed.clear()
            self.weekly_keys = self._roll("weekly", 2)
            self.weekly_reset_at = self._next_weekly()

        # First-time roll
        if not self.daily_keys:
            self.daily_keys = self._roll("daily", 2)
        if not self.weekly_keys:
            self.weekly_keys = self._roll("weekly", 2)

    def _roll(self, category: str, count: int) -> List[str]:
        pool = [k for k, v in self._pool.items() if v.category == category]
        if len(pool) <= count:
            return pool
        rnd = random.Random()
        return rnd.sample(pool, count)

    def reset_info(self) -> dict:
        now = self._now_ts()
        return {
            "daily_seconds": max(0, self.daily_reset_at - now),
            "weekly_seconds": max(0, self.weekly_reset_at - now),
        }

    # ---------- public API used by Game/UI ----------
    def list(self, game) -> List[dict]:
        self._ensure_roll()
        out: List[dict] = []
        info = self.reset_info()
        # build dicts
        def resolve_progress(metric: str) -> float:
            # Accept counters or totals accessible on Game
            return float(getattr(game, metric, 0.0))

        for cat, keys, claimed in (
            ("daily", self.daily_keys, self.daily_claimed),
            ("weekly", self.weekly_keys, self.weekly_claimed),
        ):
            for key in keys:
                t = self._pool.get(key)
                if not t: 
                    continue
                cur = resolve_progress(t.metric)
                out.append({
                    "key": key,
                    "name": t.name,
                    "category": cat,
                    "metric": t.metric,
                    "target": t.target,
                    "current": cur,
                    "done": cur >= t.target,
                    "claimed": bool(claimed.get(key, False)),
                    "reward_type": t.reward_type,
                    "reward": t.reward_amount,
                    **info,
                })
        return out

    def claim(self, game, key: str) -> bool:
        # Determine group
        if key in self.daily_keys:
            if self.daily_claimed.get(key):
                return False
            t = self._pool.get(key)
            if not t:
                return False
            cur = float(getattr(game, t.metric, 0.0))
            if cur < t.target:
                return False
            self._apply_reward(game, t)
            self.daily_claimed[key] = True
            return True
        if key in self.weekly_keys:
            if self.weekly_claimed.get(key):
                return False
            t = self._pool.get(key)
            if not t:
                return False
            cur = float(getattr(game, t.metric, 0.0))
            if cur < t.target:
                return False
            self._apply_reward(game, t)
            self.weekly_claimed[key] = True
            return True
        return False

    def _apply_reward(self, game, t: BountyTemplate) -> None:
        if t.reward_type == "shards":
            game.shards += float(t.reward_amount)
        elif t.reward_type == "diamonds":
            game.diamonds += int(t.reward_amount)
        elif t.reward_type == "gold":
            game.gold += float(t.reward_amount)
            game.lifetime_gold += float(t.reward_amount)
        elif t.reward_type == "scrap":
            game.scrap += float(t.reward_amount)

