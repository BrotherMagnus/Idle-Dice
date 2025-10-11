# settings.py
from __future__ import annotations
import json
from pathlib import Path

# Store settings under data/settings.json, with legacy fallback
DATA_DIR = Path(__file__).parent / "data"
LEGACY_SETTINGS = Path(__file__).with_name("settings.json")
SETTINGS_PATH = DATA_DIR / "settings.json"

DEFAULTS = {
    "use_dice_icons": True,   # controls dice roll animation visuals
}

def load_settings() -> dict:
    # Try preferred location
    try:
        if SETTINGS_PATH.exists():
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            return {**DEFAULTS, **data}
    except Exception:
        pass
    # Fallback to legacy location
    try:
        if LEGACY_SETTINGS.exists():
            data = json.loads(LEGACY_SETTINGS.read_text(encoding="utf-8"))
            # migrate to new location on next save
            return {**DEFAULTS, **data}
    except Exception:
        pass
    return DEFAULTS.copy()

def save_settings(cfg: dict) -> bool:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False
