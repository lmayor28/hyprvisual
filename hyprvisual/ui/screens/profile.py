from typing import List, Tuple
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Center, Middle, VerticalScroll
from textual.widgets import Button, Label, Input
from textual.screen import ModalScreen

from hyprvisual.core.display_manager import Display
from hyprvisual.core.profile_manager import ProfileManager

class ProfileScreen(ModalScreen[Tuple[bool, str] | None]):
    """Modal to manage Layout Profiles."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, current_displays: List[Display], **kwargs):
        super().__init__(**kwargs)
        self.current_displays = current_displays
        self.profiles = ProfileManager.load_profiles()
        self._profile_names: List[str] = list(self.profiles.keys())

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="profile-dialog"):
                    yield Label("Layout Profiles", id="profile-title")
                    yield Label("Load an existing profile, or save the current one.", id="profile-prompt")

                    with Horizontal(id="profile-input-row"):
                        yield Input(placeholder="New profile name...", id="profile-input")
                        yield Button("Save Current", variant="success", id="btn-save-profile")

                    with VerticalScroll(id="profile-list"):
                        for idx, name in enumerate(self._profile_names):
                            with Horizontal(classes="profile-item"):
                                yield Label(f"📄 {name}", classes="profile-name")
                                yield Button("Load", variant="primary", id=f"load-{idx}", classes="btn-load")
                                yield Button("Delete", variant="error", id=f"delete-{idx}", classes="btn-delete")

                    yield Button("Cancel", id="btn-cancel-profile", classes="modal-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if not btn_id:
            return

        if btn_id == "btn-cancel-profile":
            self.dismiss(None)

        elif btn_id == "btn-save-profile":
            inp = self.query_one("#profile-input", Input)
            name = inp.value.strip()
            if not name:
                self.notify("Profile name cannot be empty.", severity="error")
                return

            success = ProfileManager.save_profile(name, self.current_displays)
            if success:
                self.dismiss((True, f"Profile '{name}' saved successfully."))
            else:
                self.dismiss((False, "Failed to save profile."))

        elif btn_id.startswith("load-"):
            idx = int(btn_id.split("-", 1)[1])
            name = self._profile_names[idx]
            success, msg = ProfileManager.apply_profile(name)
            if success:
                self.dismiss((True, f"Profile '{name}' loaded. Monitor states will refresh."))
            else:
                self.dismiss((False, f"Failed to load profile: {msg}"))

        elif btn_id.startswith("delete-"):
            idx = int(btn_id.split("-", 1)[1])
            name = self._profile_names[idx]
            success = ProfileManager.delete_profile(name)
            if success:
                self.profiles = ProfileManager.load_profiles()
                self._profile_names = list(self.profiles.keys())
                self._refresh_list()
                self.notify(f"Profile '{name}' deleted.", severity="warning")
            else:
                self.notify("Failed to delete profile.", severity="error")

    def _refresh_list(self) -> None:
        lst = self.query_one("#profile-list")
        lst.remove_children()
        for idx, name in enumerate(self._profile_names):
            with Horizontal(classes="profile-item"):
                lst.mount(Label(f"📄 {name}", classes="profile-name"))
                lst.mount(Button("Load", variant="primary", id=f"load-{idx}", classes="btn-load"))
                lst.mount(Button("Delete", variant="error", id=f"delete-{idx}", classes="btn-delete"))

    def action_cancel(self) -> None:
        self.dismiss(None)
