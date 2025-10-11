from __future__ import annotations

import random
from typing import List, Tuple


def bet(game) -> Tuple[List[int], int]:
    faces = [random.randint(1, game.die_sides) for _ in range(game.dice_count)]
    total = sum(faces)
    gained = game._apply_income(total)
    return faces, gained


def spin_slots(game) -> Tuple[List[str], int, int]:
    symbols = ["dY?'", "dY?<", "7�,?���", "dY'Z", "�-?"]
    reels = [random.choice(symbols) for _ in range(3)]
    gold_won = 0
    diamonds_won = 0
    if len(set(reels)) == 1:
        if reels[0] == "dY'Z":
            diamonds_won = 10
        else:
            gold_won = 500
    elif len(set(reels)) == 2:
        gold_won = 50

    if gold_won > 0:
        gold_won = int(round(gold_won * game.slots_yield_mult))

    gold_won = game._apply_income(gold_won)
    game.diamonds += diamonds_won
    return reels, gold_won, diamonds_won

