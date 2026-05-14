# hyprvisual

A modern, fast, and feature-rich terminal user interface (TUI) to manage Hyprland monitor layouts, built with Python and [Textual](https://github.com/Textualize/textual).

![hyprvisual demo](https://textual.textualize.io/assets/images/logo.svg) <!-- Replace with an actual screenshot of the app -->

## Features

- **Interactive Layout Controller**: Visually manage your displays directly from the terminal.
- **Toggle Displays**: Turn monitors on and off with a single keystroke (`Space` or `Enter`).
- **Safety Revert**: If you disable a monitor, a 15-second countdown modal appears to confirm the change. If you don't confirm (or your screen goes black), it reverts automatically.
- **Mirror Mode**: Quickly mirror one display onto another with the `m` key.
- **Refresh Rate Picker**: Change the resolution and refresh rate (Hz) per monitor with the `h` key. Automatically detects the best available mode.
- **Live State**: Shows the active workspace for each monitor in real-time.
- **Theming**: Press `t` to cycle through built-in themes (Glass, Hacker, Nordic, Textual Dark).
- **Keyboard-First Design**: Completely navigable without a mouse using `Tab`, `Space`, `m`, and `h`.

## Prerequisites

- **[Hyprland](https://hyprland.org/)**: The Wayland compositor.
- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (recommended) or `pip` for dependency management.

## Installation

### Automated Install (Recommended)

You can easily install `hyprvisual` and add it to your `PATH` with a single command:

```bash
curl -sS https://raw.githubusercontent.com/lmayor28/hyprvisual/main/install.sh | bash
```

This will clone the repository, set up an isolated Python virtual environment, and create an executable command `hyprvisual` in your `~/.local/bin`.

### Manual Install

```bash
git clone https://github.com/yourusername/hyprvisual.git
cd hyprvisual/hyprvisual

# Using uv (recommended)
uv sync

# Or using pip
python3 -m venv .venv
source .venv/bin/activate
pip install textual
```

## Usage

Run the TUI directly:

```bash
uv run main.py
```

### Keybindings

| Key | Scope | Action |
| --- | --- | --- |
| `Tab` | Global | Navigate between monitor cards |
| `Space` / `Enter` | Card | Toggle the focused monitor On/Off |
| `m` | Card | Open Mirror source selection |
| `h` | Card | Open Refresh Rate and Resolution picker |
| `p` | Card | Adjust X/Y position |
| `s` | Card | Adjust scale (0.5x – 3.0x) |
| `i` | Card | Blink monitor to physically identify it |
| `w` | Card | Assign default workspace |
| `P` | Global | Open Layout Profiles manager |
| `r` | Global | Refresh displays |
| `t` | Global | Cycle through themes (Nordic, Hacker, Glass, Dark) |
| `q` | Global | Quit |

## Architecture

- **`src/app.py`**: Main `DisplayTUIApp` class — themes, global keybindings, modal orchestration.
- **`src/core/display_manager.py`**: All `hyprctl` interaction. Parses `hyprctl monitors all -j` into `Display` dataclasses and issues `hyprctl keyword monitor` commands.
- **`src/core/profile_manager.py`**: Saves/loads/applies layouts to `~/.config/hypr/hyprvisual.json`.
- **`src/ui/components/display_card.py`**: Per-monitor card widget with all per-card keybindings.
- **`src/ui/screens/`**: Modal screens — mirror, hz, position, scale, workspace, profile, confirm.
- **`main.py`**: Entry point.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
