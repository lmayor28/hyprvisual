# hyprmonitor

A modern, fast, and feature-rich terminal user interface (TUI) to manage Hyprland monitor layouts, built with Python and [Textual](https://github.com/Textualize/textual).

![hyprmonitor demo](https://textual.textualize.io/assets/images/logo.svg) <!-- Replace with an actual screenshot of the app -->

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

You can easily install `hyprmonitor` and add it to your `PATH` with a single command:

```bash
curl -sS https://raw.githubusercontent.com/yourusername/hyprmonitor/main/install.sh | bash
```

This will clone the repository, set up an isolated Python virtual environment, and create an executable command `hyprmonitor` in your `~/.local/bin`.

### Manual Install

```bash
git clone https://github.com/yourusername/hyprmonitor.git
cd hyprmonitor/display-tui

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

| Key | Action |
| --- | --- |
| `Tab` | Navigate between monitor cards |
| `Space` / `Enter` | Toggle the focused monitor On/Off |
| `m` | Open Mirror source selection |
| `h` | Open Refresh Rate and Resolution picker |
| `r` | Refresh displays manually |
| `t` | Cycle through themes (Nordic, Hacker, Glass, Dark) |
| `q` | Quit the application |

## Architecture

- **`tui_app.py`**: The Textual frontend containing the layout, cards, and modals.
- **`display_manager.py`**: The backend logic that interfaces with `hyprctl monitors -j` and parses `availableModes` to configure Hyprland.
- **`main.py`**: The entry point.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
