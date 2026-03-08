import subprocess
import json
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Display:
    id: int
    name: str
    description: str
    disabled: bool
    width: int
    height: int
    refreshRate: float
    x: int = 0
    y: int = 0
    scale: float = 1.0
    active_workspace_id: int = 1
    active_workspace_name: str = "1"
    mirror_of: str = "none"
    available_modes: List[str] = field(default_factory=list)  # e.g. ["1920x1080@143.85Hz", ...]
    best_mode: str = "preferred"  # highest-refresh mode to re-enable with

class DisplayManager:
    @staticmethod
    def get_displays() -> List[Display]:
        """Fetch all displays from Hyprland."""
        try:
            result = subprocess.run(
                ["hyprctl", "monitors", "all", "-j"],
                capture_output=True, text=True, check=True
            )
            data = json.loads(result.stdout)
            displays = []
            for item in data:
                ws = item.get("activeWorkspace", {})
                raw_modes = item.get("availableModes", [])
                native_w = item.get("width", 0)
                native_h = item.get("height", 0)
                native_res = f"{native_w}x{native_h}"

                # Find best mode: highest refresh rate at the native resolution
                best_hz = 0.0
                best_mode = "preferred"
                for mode in raw_modes:
                    try:
                        res, hz_part = mode.split("@")
                        hz = float(hz_part.replace("Hz", ""))
                        if res == native_res and hz > best_hz:
                            best_hz = hz
                            best_mode = f"{res}@{hz:.2f}"
                    except Exception:
                        continue

                displays.append(Display(
                    id=item.get("id", 0),
                    name=item.get("name", ""),
                    description=item.get("description", ""),
                    disabled=item.get("disabled", False),
                    width=native_w,
                    height=native_h,
                    refreshRate=item.get("refreshRate", 0.0),
                    x=item.get("x", 0),
                    y=item.get("y", 0),
                    scale=item.get("scale", 1.0),
                    active_workspace_id=ws.get("id", 1),
                    active_workspace_name=ws.get("name", "1"),
                    mirror_of=item.get("mirrorOf", "none"),
                    available_modes=raw_modes,
                    best_mode=best_mode,
                ))
            return displays
        except subprocess.CalledProcessError as e:
            return []
        except json.JSONDecodeError:
            return []

    @staticmethod
    def set_display_state(name: str, enable: bool, best_mode: str = "preferred"):
        """Enable or disable a specific display using best available mode."""
        if enable:
            cmd = ["hyprctl", "keyword", "monitor", f"{name},{best_mode},auto,1"]
        else:
            cmd = ["hyprctl", "keyword", "monitor", f"{name},disable"]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, "Success"
        except subprocess.CalledProcessError as e:
            return False, f"Error: {e.stderr}"


    @staticmethod
    def set_mirror(source: str, mirror: str):
        """Set 'mirror' to mirror 'source'."""
        cmd = ["hyprctl", "keyword", "monitor", f"{mirror},preferred,auto,1,mirror,{source}"]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, "Success"
        except subprocess.CalledProcessError as e:
            return False, f"Error: {e.stderr}"

    @staticmethod
    def unset_mirror(name: str):
        """Remove mirror mode from a display and trigger Hyprland to re-render surfaces."""
        # Re-enable monitor
        cmd = ["hyprctl", "keyword", "monitor", f"{name},preferred,auto,1"]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            return False, f"Error re-enabling: {e.stderr}"

        # Dispatch dpms off/on to force Hyprland to re-render layers (wallpaper, bar, etc.)
        try:
            subprocess.run(["hyprctl", "dispatch", "dpms", f"off", name], capture_output=True)
            subprocess.run(["hyprctl", "dispatch", "dpms", f"on", name], capture_output=True)
        except Exception:
            pass  # Non-fatal, monitor is already unmirrored

        return True, "Success"

    @staticmethod
    def set_position(name: str, x: int, y: int, resolution: str = "preferred", scale: float = 1.0):
        """Move the monitor to a specific X/Y coordinate."""
        cmd = ["hyprctl", "keyword", "monitor", f"{name},{resolution},{x}x{y},{scale}"]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, "Success"
        except subprocess.CalledProcessError as e:
            return False, f"Error: {e.stderr}"

    @staticmethod
    def set_scale(name: str, scale: float, resolution: str = "preferred", x: int = 0, y: int = 0):
        """Set the scale (e.g., 1.0, 1.25, 1.5) for a monitor."""
        cmd = ["hyprctl", "keyword", "monitor", f"{name},{resolution},{x}x{y},{scale}"]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, "Success"
        except subprocess.CalledProcessError as e:
            return False, f"Error: {e.stderr}"

    @staticmethod
    def identify_blink(name: str):
        """Blink a monitor by rapidly cycling DPMS off and on to physically identify it."""
        try:
            # We don't check=True because if DPMS is already off it might throw, we just want the blink effect
            import time
            subprocess.run(["hyprctl", "dispatch", "dpms", "off", name], capture_output=True)
            time.sleep(0.3)
            subprocess.run(["hyprctl", "dispatch", "dpms", "on", name], capture_output=True)
            return True, "Blinked"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def bind_workspace_to_monitor(monitor_name: str, workspace_id: int):
        """Bind a specific workspace ID to always open on a specific monitor."""
        cmd = ["hyprctl", "keyword", "workspace", f"{workspace_id}, monitor:{monitor_name}, default:true"]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, "Bound workspace"
        except subprocess.CalledProcessError as e:
            return False, f"Error: {e.stderr}"

if __name__ == "__main__":
    manager = DisplayManager()
    displays = manager.get_displays()
    for d in displays:
        print(f"{d.name} (WS:{d.active_workspace_name}) - Mirror:{d.mirror_of} - Disabled:{d.disabled}")
