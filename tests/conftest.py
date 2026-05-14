import json
import pytest

# Realistic hyprctl monitors all -j payload used across tests
MONITOR_JSON = [
    {
        "id": 0,
        "name": "DP-1",
        "description": "Dell U2722D",
        "disabled": False,
        "width": 2560,
        "height": 1440,
        "refreshRate": 143.85,
        "x": 0,
        "y": 0,
        "scale": 1.0,
        "activeWorkspace": {"id": 1, "name": "1"},
        "mirrorOf": "none",
        "availableModes": [
            "2560x1440@143.85Hz",
            "2560x1440@60.00Hz",
            "1920x1080@143.85Hz",
            "1920x1080@60.00Hz",
        ],
    },
    {
        "id": 1,
        "name": "HDMI-1",
        "description": "LG 27UK850",
        "disabled": False,
        "width": 1920,
        "height": 1080,
        "refreshRate": 60.0,
        "x": 2560,
        "y": 0,
        "scale": 1.5,
        "activeWorkspace": {"id": 2, "name": "2"},
        "mirrorOf": "none",
        "availableModes": [
            "1920x1080@60.00Hz",
            "1280x720@60.00Hz",
        ],
    },
    {
        "id": 2,
        "name": "eDP-1",
        "description": "Built-in Laptop",
        "disabled": True,
        "width": 1920,
        "height": 1080,
        "refreshRate": 0.0,
        "x": 0,
        "y": 0,
        "scale": 1.0,
        "activeWorkspace": {"id": 3, "name": "3"},
        "mirrorOf": "none",
        "availableModes": ["1920x1080@60.00Hz"],
    },
]

MONITOR_JSON_STR = json.dumps(MONITOR_JSON)
