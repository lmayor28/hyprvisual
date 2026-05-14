from typing import Tuple
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Center, Middle, VerticalScroll
from textual.widgets import Button, Label
from textual.screen import ModalScreen

from hyprvisual.core.display_manager import DisplayManager, Display

class ScaleSelectScreen(ModalScreen[Tuple[bool, str] | None]):
    """Modal to select Wayland display scale."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("space", "apply_focused", "Select"),
        ("enter", "apply_focused", "Select"),
    ]

    SCALES = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]

    def __init__(self, monitor: Display, **kwargs):
        super().__init__(**kwargs)
        self.monitor = monitor

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="scale-dialog"):
                    yield Label(f"Scale Selector — {self.monitor.name}", id="scale-title")
                    yield Label("↑↓ move  ·  Space/Enter select  ·  Esc cancel", id="scale-prompt")
                    with VerticalScroll(id="scale-options"):
                        for s in self.SCALES:
                            is_current = abs(self.monitor.scale - s) < 0.01
                            suffix = "  [dim]← current[/dim]" if is_current else ""
                            yield Button(f"{s:.2f}x{suffix}", id=f"scale-{s}", classes="modal-btn")

    def action_apply_focused(self) -> None:
        focused = self.screen.focused
        if isinstance(focused, Button):
            focused.press()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id and btn_id.startswith("scale-"):
            val_str = btn_id.replace("scale-", "")
            try:
                scale_val = float(val_str)
                success, msg = DisplayManager.set_scale(
                    self.monitor.name, scale_val, self.monitor.best_mode, 
                    self.monitor.x, self.monitor.y
                )
                if success:
                    self.dismiss((True, f"Scale set to {scale_val}x for {self.monitor.name}"))
                else:
                    self.dismiss((False, f"Error applying scale: {msg}"))
            except ValueError:
                self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
