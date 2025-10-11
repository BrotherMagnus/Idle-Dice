from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root on sys.path when running as a script from scripts/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import game


def main() -> None:
    g = game.Game()
    g.gold = 10_000

    # Buildings: basic shape
    cards = g.get_building_data()
    print("buildings", len(cards))

    # Assert unlock requirement messaging goes away once prereq met
    # Example: Bar requires Kiosk >= 5
    kiosk = next(u for u in g.upgrades if u.key == "b_kiosk")
    bar = next(u for u in g.upgrades if u.key == "b_bar")
    kiosk.level = 5
    g._recompute_stats()
    cards2 = g.get_building_data()
    bar_card = next(c for c in cards2 if c["key"] == "b_bar")
    assert not bar_card.get("locked", False), "Bar should unlock when Kiosk >= 5"
    assert "requires" not in (k.lower() for k in bar_card.keys()), "No requires field expected"
    print("unlock_check_ok", True)

    # Bounties & Achievements counts
    print("bounties", len(g.list_bounties()))
    print("achievements", len(g.list_achievements()))

    # Casino ops
    _, gained = g.bet()
    _, slot_gold, slot_diam = g.spin_slots()
    print("casino_ok", gained >= 0 and slot_gold >= 0)

    # Persistence round-trip (in-memory)
    d = g.to_dict()
    g2 = game.Game()
    g2.from_dict(json.loads(json.dumps(d)))
    print("roundtrip_ok", int(g2.gold) == int(g.gold))


if __name__ == "__main__":
    main()
