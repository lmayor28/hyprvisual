from typing import Tuple
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Center, Middle, VerticalScroll
from textual.widgets import Button, Label
from textual.screen import ModalScreen

from core.display_manager import DisplayManager, Display

class HzSelectScreen(ModalScreen[Tuple[bool, str] | None]):
    """Modal to select resolution and frequency."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("space", "apply_focused", "Select"),
        ("enter", "apply_focused", "Select"),
    ]

    def __init__(self, monitor: Display, **kwargs):
        super().__init__(**kwargs)
        self.monitor = monitor

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="hz-dialog"):
                    yield Label(f"Frequency Selector — {self.monitor.name}", id="hz-title")
                    yield Label("↑↓ move  ·  Space/Enter select  ·  Esc cancel", id="hz-prompt")
                    with VerticalScroll(id="hz-options"):
                        seen = set()
                        for mode in self.monitor.available_modes:
                            safe = mode.replace("@", "-").replace(".", "_")
                            if safe not in seen:
                                seen.add(safe)
                                # highlight if it's currently active (we map against best_mode just as a proxy here)
                                is_current = mode.startswith(self.monitor.best_mode)
                                suffix = "  [dim]← current[/dim]" if is_current else ""
                                yield Button(f"{mode}{suffix}", id=f"mode-{safe}", classes="modal-btn")

    def action_apply_focused(self) -> None:
        focused = self.screen.focused
        if isinstance(focused, Button):
            focused.press()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id and btn_id.startswith("mode-"):
            raw = btn_id.replace("mode-", "")
            for mode in self.monitor.available_modes:
                safe = mode.replace("@", "-").replace(".", "_")
                if safe == raw:
                    try:
                        res, hz_part = mode.split("@")
                        hz = hz_part.replace("Hz", "")
                        cmd_mode = f"{res}@{hz}"
                    except Exception:
                        cmd_mode = "preferred"

                    success, msg = DisplayManager.set_display_state(self.monitor.name, True, cmd_mode)
                    if success:
                        self.dismiss((True, f"{self.monitor.name} → {mode}"))
                    else:
                        self.dismiss((False, f"Error applying mode: {msg}"))
                    return
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
