"""Global settings used across the project."""

from __future__ import annotations

import sys
from pathlib import Path

WINDOW_WIDTH = 980
WINDOW_HEIGHT = 720
FPS = 60
WINDOW_TITLE = "Snake Legends"

GRID_SIZE = 24
BOARD_COLS = 26
BOARD_ROWS = 26
BOARD_OFFSET_X = 24
BOARD_OFFSET_Y = 48
BOARD_WIDTH = BOARD_COLS * GRID_SIZE
BOARD_HEIGHT = BOARD_ROWS * GRID_SIZE

SIDEBAR_WIDTH = 292

BASE_MOVE_DELAY = 150
MIN_MOVE_DELAY = 70

BACKGROUND_COLOR = (12, 16, 22)
BOARD_COLOR = (16, 22, 30)
GRID_COLOR = (28, 38, 52)
TEXT_COLOR = (241, 245, 249)
SUBTEXT_COLOR = (145, 156, 173)
PANEL_COLOR = (10, 13, 18)
PANEL_BORDER = (46, 60, 82)
HIGHLIGHT_COLOR = (66, 190, 142)
WARNING_COLOR = (244, 114, 94)
PORTAL_COLOR = (104, 132, 255)
OBSTACLE_COLOR = (74, 84, 102)

PLAYER_ONE_COLORS = {
    "head": (81, 214, 120),
    "body": (43, 154, 91),
}
PLAYER_TWO_COLORS = {
    "head": (90, 177, 255),
    "body": (54, 114, 214),
}
AI_COLORS = {
    "head": (255, 184, 77),
    "body": (222, 135, 52),
}

PLAYER_ONE_CONTROLS = {
    "up": "UP",
    "down": "DOWN",
    "left": "LEFT",
    "right": "RIGHT",
}
PLAYER_TWO_CONTROLS = {
    "up": "W",
    "down": "S",
    "left": "A",
    "right": "D",
}

FOOD_LIBRARY = {
    "apple": {
        "label": "Apple",
        "color": (232, 96, 96),
        "score": 1,
        "growth": 1,
        "ttl": None,
        "effect": None,
        "weight": 1.0,
    },
    "gold": {
        "label": "Gold Fruit",
        "color": (255, 201, 60),
        "score": 3,
        "growth": 2,
        "ttl": 9000,
        "effect": None,
        "weight": 0.12,
    },
    "phase": {
        "label": "Phase Fruit",
        "color": (139, 92, 246),
        "score": 2,
        "growth": 1,
        "ttl": 8000,
        "effect": "phase",
        "weight": 0.08,
    },
    "freeze": {
        "label": "Freeze Fruit",
        "color": (56, 189, 248),
        "score": 2,
        "growth": 1,
        "ttl": 8000,
        "effect": "freeze_others",
        "weight": 0.08,
    },
    "haste": {
        "label": "Haste Fruit",
        "color": (255, 132, 68),
        "score": 2,
        "growth": 1,
        "ttl": 8000,
        "effect": "haste",
        "weight": 0.08,
    },
    "bounce": {
        "label": "Bounce Fruit",
        "color": (120, 220, 255),
        "score": 2,
        "growth": 1,
        "ttl": 8000,
        "effect": "bounce",
        "weight": 0.06,
    },
    "magnet": {
        "label": "Magnet Fruit",
        "color": (255, 118, 182),
        "score": 2,
        "growth": 1,
        "ttl": 8000,
        "effect": "magnet",
        "weight": 0.06,
    },
}

MODE_DEFINITIONS = [
    {
        "id": "timed_solo",
        "label": "Timed Solo",
        "description": "Single-player score attack with editable countdown time.",
        "humans": 1,
        "ais": 0,
        "hazards": True,
        "coop": False,
        "category": "mode",
        "default_duration": (0, 1, 0),
    },
    {
        "id": "versus_ai",
        "label": "Human Vs AI",
        "description": "Compete for food, map control, and survival against the machine.",
        "humans": 1,
        "ais": 1,
        "hazards": True,
        "coop": False,
        "category": "mode",
        "default_duration": (0, 2, 0),
    },
    {
        "id": "local_duel",
        "label": "Local Duel",
        "description": "Two players on one keyboard. Arrow keys vs WASD.",
        "humans": 2,
        "ais": 0,
        "hazards": True,
        "coop": False,
        "category": "mode",
        "default_duration": (0, 2, 0),
    },
    {
        "id": "coop",
        "label": "Co-op Run",
        "description": "Two players cooperate to reach the shared score target.",
        "humans": 2,
        "ais": 0,
        "hazards": True,
        "coop": True,
        "category": "mode",
        "default_duration": (0, 3, 0),
    },
    {
        "id": "lan_host",
        "label": "LAN Host",
        "description": "Create a local room and host a remote duel match.",
        "humans": 1,
        "ais": 0,
        "hazards": True,
        "coop": False,
        "category": "network_host",
        "default_duration": (0, 2, 0),
    },
    {
        "id": "lan_join",
        "label": "LAN Join",
        "description": "Enter a host IP address and join over the local network.",
        "humans": 1,
        "ais": 0,
        "hazards": False,
        "coop": False,
        "category": "network_join",
        "default_duration": (0, 2, 0),
    },
]

COOP_TARGET_SCORE = 18
DUEL_TARGET_SCORE = 15
NETWORK_PORT = 47621
SUPPORTED_LANGUAGES = ["zh", "en", "de"]

if getattr(sys, "frozen", False):
    ROOT_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    APP_DIR = Path(sys.executable).resolve().parent
else:
    ROOT_DIR = Path(__file__).resolve().parent
    APP_DIR = ROOT_DIR

ASSETS_DIR = ROOT_DIR / "assets"
BUNDLED_DATA_DIR = ROOT_DIR / "data"
DATA_DIR = APP_DIR / "data"
STATS_FILE = DATA_DIR / "player_stats.json"
