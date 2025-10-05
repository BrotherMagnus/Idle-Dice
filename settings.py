# settings.py
from __future__ import annotations
import json
from pathlib import Path

SETTINGS_PATH = Path(__file__).with_name("settings.json")

DEFAULTS = {
    "use_dice_icons": True,   # controls dice roll animation visuals
}

def load_settings() -> dict:
    try:
        if SETTINGS_PATH.exists():
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            # merge with defaults to avoid missing keys
            return {**DEFAULTS, **data}
    except Exception:
        pass
    return DEFAULTS.copy()

def save_settings(cfg: dict) -> bool:
    try:
        SETTINGS_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False
