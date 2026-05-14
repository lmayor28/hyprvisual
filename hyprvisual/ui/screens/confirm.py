from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Center, Middle
from textual.widgets import Button, Label
from textual.screen import ModalScreen

class ConfirmDisplayScreen(ModalScreen[bool]):
    """Modal to display a 15-second countdown to keep or revert changes."""

    BINDINGS = [
        ("escape", "revert", "Revert"),
        ("space", "apply_focused", "Select"),
        ("enter", "apply_focused", "Select"),
    ]

    def __init__(self, countdown: int = 15, **kwargs):
        super().__init__(**kwargs)
        self.countdown = countdown

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="confirm-dialog"):
                    yield Label("Display setup changed.", id="confirm-title")
                    yield Label("Keep this configuration?", id="confirm-prompt")
                    yield Label(f"Reverting automatically in {self.countdown} seconds...", id="confirm-timer")
                    with Horizontal(id="confirm-buttons"):
                        yield Button("Keep Changes  [←]", variant="success", id="btn-keep")
                        yield Button("[→]  Revert", variant="error", id="btn-revert")

    def on_mount(self) -> None:
        self.set_interval(1.0, self.tick)
        self.query_one("#btn-keep").focus()

    def tick(self) -> None:
        self.countdown -= 1
        self.query_one("#confirm-timer").update(f"Reverting automatically in {self.countdown} seconds...")
        if self.countdown <= 0:
            self.dismiss(False)

    def action_apply_focused(self) -> None:
        focused = self.screen.focused
        if isinstance(focused, Button):
            focused.press()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-keep":
            self.dismiss(True)
        elif event.button.id == "btn-revert":
            self.dismiss(False)

    def action_revert(self) -> None:
        self.dismiss(False)
