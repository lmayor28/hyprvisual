import subprocess
import json
from dataclasses import dataclass
from typing import List

@dataclass
class Display:
    id: int
    name: str
    description: str
    disabled: bool
    width: int
    height: int
    refreshRate: float

class DisplayManager:
    @staticmethod
    def get_displays() -> List[Display]:
        """Fetch all displays from Hyprland."""
        try:
            result = subprocess.run(
                ["hyprctl", "monitors", "all", "-j"],
                capture_output=True,
                text=True,
                check=True
            )
            data = json.loads(result.stdout)
            displays = []
            for item in data:
                displays.append(Display(
                    id=item.get("id", 0),
                    name=item.get("name", ""),
                    description=item.get("description", ""),
                    disabled=item.get("disabled", False),
                    width=item.get("width", 0),
                    height=item.get("height", 0),
                    refreshRate=item.get("refreshRate", 0.0)
                ))
            return displays
        except subprocess.CalledProcessError as e:
            print(f"Error fetching displays: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing displays: {e}")
            return []

    @staticmethod
    def set_display_state(name: str, enable: bool):
        """Enable or disable a specific display."""
        if enable:
            # Enable with preferred resolution and auto placement
            cmd = ["hyprctl", "keyword", "monitor", f"{name},preferred,auto,1"]
        else:
            # Disable the monitor
            cmd = ["hyprctl", "keyword", "monitor", f"{name},disable"]
            
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, "Success"
        except subprocess.CalledProcessError as e:
            return False, f"Error: {e.stderr}"

if __name__ == "__main__":
    manager = DisplayManager()
    displays = manager.get_displays()
    for d in displays:
        print(f"{d.name} ({d.description}) - Disabled: {d.disabled}")
