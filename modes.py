# modes.py
from __future__ import annotations
import random
from abc import ABC, abstractmethod
from game import Game

class GameMode(ABC):
    """Base class for a playable game mode."""
    def __init__(self, game: Game):
        self.game = game

    @abstractmethod
    def play(self):
        """Execute one active play (e.g., roll dice, spin slots)."""
        raise NotImplementedError

    def tick_passive(self):
        """Passive income tick (override if mode has any)."""
        pass


class DiceGame(GameMode):
    """Dice mode: rolls N dice of S sides, adds total to gold."""
    def play(self) -> tuple[list[int], int]:
        faces = [random.randint(1, self.game.die_sides) for _ in range(self.game.dice_count)]
        total = sum(faces)
        self.game.gold += total
        self.game.lifetime_gold += total
        self.game._check_unlocks()
        return faces, total


class SlotsGame(GameMode):
    """Slots mode: spin 3 reels; jackpots award diamonds; has passive income."""
    SYMBOLS = ["🍒", "🍋", "7️⃣", "💎", "⭐"]

    def play(self) -> tuple[list[str], int, int]:
        reels = [random.choice(self.SYMBOLS) for _ in range(3)]
        gold_won = 0
        diamonds_won = 0

        # 3 of a kind
        if len(set(reels)) == 1:
            if reels[0] == "💎":
                diamonds_won = 10
            else:
                gold_won = 500
        # 2 of a kind
        elif len(set(reels)) == 2:
            gold_won = 50

        self.game.gold += gold_won
        self.game.lifetime_gold += gold_won
        self.game.diamonds += diamonds_won
        return reels, gold_won, diamonds_won

    def tick_passive(self):
        if self.game.slots_unlocked and self.game.slots_passive_income > 0:
            self.game.gold += self.game.slots_passive_income
            self.game.lifetime_gold += self.game.slots_passive_income
