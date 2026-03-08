import json
import os
from dataclasses import asdict
from typing import Dict, Any, List, Tuple
from pathlib import Path

from core.display_manager import Display, DisplayManager

CONFIG_DIR = Path(os.path.expanduser("~/.config/hypr"))
CONFIG_FILE = CONFIG_DIR / "hyprvisual.json"

class ProfileManager:
    @staticmethod
    def _ensure_config_dir():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def load_profiles() -> Dict[str, List[Dict[str, Any]]]:
        """Load saved profiles from the JSON configuration."""
        if not CONFIG_FILE.exists():
            return {}
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def save_profile(name: str, displays: List[Display]) -> bool:
        """Save the current active display state as a new profile."""
        ProfileManager._ensure_config_dir()
        profiles = ProfileManager.load_profiles()
        
        # Serialize only the data we need to re-apply
        serialized = []
        for d in displays:
            serialized.append({
                "name": d.name,
                "disabled": d.disabled,
                "x": d.x,
                "y": d.y,
                "scale": d.scale,
                "best_mode": d.best_mode,
                "mirror_of": d.mirror_of
            })
            
        profiles[name] = serialized
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(profiles, f, indent=4)
            return True
        except Exception:
            return False

    @staticmethod
    def delete_profile(name: str) -> bool:
        """Delete a profile from the JSON configuration."""
        profiles = ProfileManager.load_profiles()
        if name in profiles:
            del profiles[name]
            try:
                with open(CONFIG_FILE, "w") as f:
                    json.dump(profiles, f, indent=4)
                return True
            except Exception:
                return False
        return False

    @staticmethod
    def apply_profile(name: str) -> Tuple[bool, str]:
        """Apply a saved profile by iterating over its saved states."""
        profiles = ProfileManager.load_profiles()
        if name not in profiles:
            return False, "Profile not found."
            
        target_state = profiles[name]
        
        # Step 1: Disable everything that should be disabled first
        for saved in target_state:
            if saved.get("disabled", False):
                DisplayManager.set_display_state(saved["name"], False)
                
        # Step 2: Apply main monitors
        for saved in target_state:
            if not saved.get("disabled", False):
                # Standard monitors
                res = saved.get("best_mode", "preferred")
                x = saved.get("x", 0)
                y = saved.get("y", 0)
                scale = saved.get("scale", 1.0)
                DisplayManager.set_position(saved["name"], x, y, res, scale)
                
        # Step 3: Apply mirrors last (hyprland requires the source to exist first)
        for saved in target_state:
            mirror_of = saved.get("mirror_of", "none")
            name = saved["name"]
            if mirror_of != "none":
                DisplayManager.set_mirror(mirror_of, name)
                
        return True, "Success"
