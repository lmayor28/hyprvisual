from typing import Tuple
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Center, Middle, VerticalScroll
from textual.widgets import Button, Label, Input
from textual.screen import ModalScreen

from core.display_manager import DisplayManager, Display

class WorkspaceSelectScreen(ModalScreen[Tuple[bool, str] | None]):
    """Modal to assign a default workspace ID to a monitor."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "apply", "Apply")
    ]

    def __init__(self, monitor: Display, **kwargs):
        super().__init__(**kwargs)
        self.monitor = monitor

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="workspace-dialog"):
                    yield Label(f"Bind Workspace — {self.monitor.name}", id="workspace-title")
                    yield Label("Assign a default Workspace ID (1-10) to always open here.", id="workspace-prompt")
                    with Horizontal(id="workspace-input-row"):
                        yield Input(
                            placeholder="Workspace ID (ej: 1)", 
                            value=str(self.monitor.active_workspace_id),
                            type="integer", 
                            id="workspace-input"
                        )
                    with Horizontal(id="workspace-buttons"):
                        yield Button("Bind", variant="success", id="ws-bind", classes="modal-btn")
                        yield Button("Cancel", id="ws-cancel", classes="modal-btn")

    def on_mount(self) -> None:
        self.query_one("#workspace-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "ws-cancel":
            self.dismiss(None)
        elif btn_id == "ws-bind":
            self.action_apply()

    def action_apply(self) -> None:
        val = self.query_one("#workspace-input", Input).value.strip()
        try:
            ws_id = int(val)
            if ws_id < 1:
                raise ValueError
            success, msg = DisplayManager.bind_workspace_to_monitor(self.monitor.name, ws_id)
            if success:
                self.dismiss((True, f"Workspace {ws_id} bound to {self.monitor.name}"))
            else:
                self.dismiss((False, f"Failed to bind: {msg}"))
        except ValueError:
            self.notify("Please enter a valid positive integer.", severity="error")

    def action_cancel(self) -> None:
        self.dismiss(None)
