from typing import List, Tuple
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Center, Middle
from textual.widgets import Button, Label
from textual.screen import ModalScreen

from hyprvisual.core.display_manager import DisplayManager, Display
from hyprvisual.ui.utils import mnemonic

class MirrorSelectScreen(ModalScreen[Tuple[bool, str] | None]):
    """Modal to select a source monitor for mirroring."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("space", "apply_focused", "Select"),
        ("enter", "apply_focused", "Select"),
    ]

    def __init__(self, target_name: str, monitors: List[Display], **kwargs):
        super().__init__(**kwargs)
        self.target_name = target_name
        self.monitors = monitors

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="mirror-dialog"):
                    yield Label(f"󰿏  Mirror  {self.target_name}  from:", id="mirror-title")
                    yield Label("↑↓ move  ·  Space/Enter select  ·  Esc cancel", id="mirror-prompt")
                    with Vertical(id="mirror-options"):
                        for m in self.monitors:
                            if m.name != self.target_name:
                                yield Button(
                                    mnemonic(f"󰍹  {m.name}  ({m.description[:28]})", m.name[0]),
                                    id=f"mirror-src-{m.name}",
                                    classes="modal-btn"
                                )
                        yield Button(
                            mnemonic("Disable Mirror Mode", "D"),
                            variant="warning", id="mirror-disable", classes="modal-btn"
                        )

    def action_apply_focused(self) -> None:
        focused = self.screen.focused
        if isinstance(focused, Button):
            focused.press()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "mirror-disable":
            success, msg = DisplayManager.unset_mirror(self.target_name)
            if success:
                self.dismiss((True, f"Mirror mode disabled for {self.target_name}"))
            else:
                self.dismiss((False, msg))
            return

        if btn_id and btn_id.startswith("mirror-src-"):
            source = btn_id.replace("mirror-src-", "")
            success, msg = DisplayManager.set_mirror(source, self.target_name)
            if success:
                self.dismiss((True, f"Mirroring {source} to {self.target_name}"))
            else:
                self.dismiss((False, msg))

    def action_cancel(self) -> None:
        self.dismiss(None)
