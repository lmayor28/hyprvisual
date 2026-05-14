# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

`hyprvisual` is a Textual-based terminal UI (TUI) for managing Hyprland monitor layouts. It wraps `hyprctl` commands to toggle, mirror, position, scale, and configure monitors at runtime — without touching config files (except profiles saved to `~/.config/hypr/hyprvisual.json`).

## Running and development

```bash
# Run the app
uv run main.py

# Install dependencies
uv sync

# Run with a specific Python version (project requires 3.12+)
uv run --python 3.12 main.py
```

There are no tests and no lint commands configured. The project uses `uv` exclusively — avoid `pip` or `python -m venv`.

## Architecture

All source lives under `src/`. `main.py` is just an entrypoint that adds `src/` to `sys.path` before importing `app.DisplayTUIApp`.

**`src/app.py` — `DisplayTUIApp`**
The Textual `App` subclass. Owns global state (`_displays: List[Display]`) and handles top-level actions: refresh, theme cycle, profile open, and the toggle/mirror callbacks. Modals are pushed via `self.push_screen(...)` with a callback; the callback receives the result and triggers `refresh_displays()` on success.

**`src/core/display_manager.py` — `DisplayManager` + `Display`**
All `hyprctl` interaction lives here. `Display` is a `@dataclass` populated from `hyprctl monitors all -j`. Every mutating method (`set_display_state`, `set_mirror`, `set_position`, `set_scale`, `bind_workspace_to_monitor`) issues a `hyprctl keyword monitor ...` command and returns `(bool, str)`. No state is mutated in-process — the TUI always re-fetches from Hyprland via `get_displays()` after any operation.

**`src/core/profile_manager.py` — `ProfileManager`**
Reads/writes `~/.config/hypr/hyprvisual.json`. Profile application order matters: disable first, then position non-mirrors, then apply mirrors (Hyprland requires the source to exist before mirroring).

**`src/ui/components/display_card.py` — `DisplayWidget`**
One card per monitor. Owns per-card keybindings (`space`, `m`, `h`, `p`, `s`, `i`, `w`). Actions on disabled monitors are blocked with a notification. The `identify_blink` action uses `self.run_worker(self._blink_worker)` to avoid freezing the TUI during `time.sleep`.

**`src/ui/screens/`** — Modal screens (all push results back via Textual's screen callback pattern):
- `confirm.py` — 15-second countdown modal for toggle-off safety revert
- `mirror.py` — Source selection for mirroring
- `hz.py` — Resolution + refresh rate picker (parses `available_modes`)
- `position.py` — X/Y offset editor relative to a primary monitor
- `scale.py` — Scale selector (0.5x–3.0x)
- `workspace.py` — Default workspace assignment

**`src/app.tcss`** — Textual CSS for all UI styling.

## Key patterns

- **Circular import avoidance**: `display_card.py` imports `DisplayTUIApp` lazily inside action methods (`from app import DisplayTUIApp`) to avoid a circular dependency at module load time.
- **Always re-fetch after mutations**: After any `DisplayManager` call, `refresh_displays()` clears and remounts all `DisplayWidget` children from a fresh `hyprctl` query. No in-memory state is patched.
- **Modal results**: Screens return `(bool, str) | None`. `None` means the user cancelled. The `bool` indicates success; `str` is a message for `self.notify(...)`.
- **`hyprctl keyword monitor` syntax**: `NAME,RESOLUTION@HZ,XxY,SCALE[,mirror,SOURCE]` — all mutations go through this single Hyprland keyword.
