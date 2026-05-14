from pathlib import Path
from typing import List, Optional, Tuple
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Header, Footer
from textual.theme import Theme

from hyprvisual.core.display_manager import DisplayManager, Display
from hyprvisual.ui.screens.mirror import MirrorSelectScreen
from hyprvisual.ui.screens.confirm import ConfirmDisplayScreen
from hyprvisual.ui.screens.profile import ProfileScreen
from hyprvisual.ui.components.display_card import DisplayWidget

class DisplayTUIApp(App):
    # Textual equivalent of docstring / command name
    TITLE = "hyprvisual"
    """hyprvisual – TUI Display Layout Controller for Hyprland."""

    CSS_PATH = Path(__file__).parent / "app.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh_displays", "Refresh"),
        ("t", "cycle_theme", "Cycle Theme"),
        ("P", "open_profiles", "Profiles"),
    ]

    THEMES_LIST = ["textual-dark", "glass", "hacker", "nordic"]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_theme_idx = 0
        self._displays: List[Display] = []

    def on_mount(self) -> None:
        self.title = "hyprvisual – Display Layout Controller"

        self.register_theme(Theme(
            name="glass", primary="#42A5F5", accent="#2196F3",
            background="#0d1117", surface="#161b22", panel="#21262d",
            success="#238636", warning="#d29922", error="#f85149",
            dark=True,
        ))
        
        self.register_theme(Theme(
            name="hacker", primary="#00FF00", accent="#00CC00",
            background="#000000", surface="#0a0a0a", panel="#111111",
            success="#00FF00", warning="#CCCC00", error="#FF0000",
            dark=True,
        ))

        self.register_theme(Theme(
            name="nordic", primary="#88C0D0", accent="#8FBCBB",
            background="#2E3440", surface="#3B4252", panel="#434C5E",
            success="#A3BE8C", warning="#EBCB8B", error="#BF616A",
            dark=True,
        ))

        self.theme = "textual-dark"
        self._finish_initialization()

    def _finish_initialization(self) -> None:
        self.refresh_displays()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield VerticalScroll(id="display-list")
        yield Footer()

    def action_cycle_theme(self) -> None:
        self.current_theme_idx = (self.current_theme_idx + 1) % len(self.THEMES_LIST)
        new_theme = self.THEMES_LIST[self.current_theme_idx]
        self.theme = new_theme
        self.notify(f"Theme: {new_theme.title()}", severity="information")

    def refresh_displays(self) -> None:
        display_list = self.query_one("#display-list")
        display_list.remove_children()
        
        self._displays = DisplayManager.get_displays()
        
        if not self._displays:
            self.notify("No displays found from Hyprland.", severity="error")
            return
            
        for d in self._displays:
            display_list.mount(DisplayWidget(monitor=d, all_monitors=self._displays))
            
        # Refocus the first element to ensure keyboard nav works instantly
        if self._displays:
            first = display_list.children[0]
            if first:
                first.focus()

    def action_refresh_displays(self) -> None:
        self.refresh_displays()
        self.notify("Displays refreshed.", severity="information")

    def handle_toggle_for(self, monitor: Display, new_val: bool) -> None:
        if new_val:
            success, msg = DisplayManager.set_display_state(
                monitor.name, enable=True, best_mode=monitor.best_mode,
                x=monitor.x, y=monitor.y, scale=monitor.scale
            )
            if success:
                self.notify(f"{monitor.name} Enabled ✓", severity="information")
                self.refresh_displays()
            else:
                self.notify(f"Error enabling {monitor.name}: {msg}", severity="error")
                self.refresh_displays()
        else:
            success, msg = DisplayManager.set_display_state(monitor.name, enable=False)
            if success:
                self.notify(f"{monitor.name} Disabled! Verify within 15s...", severity="warning")
                self.refresh_displays()
                
                def check_confirm(result: bool | None) -> None:
                    if not result:
                        self.notify(f"Reverting {monitor.name} back ON.", severity="error")
                        DisplayManager.set_display_state(
                            monitor.name, enable=True, best_mode=monitor.best_mode,
                            x=monitor.x, y=monitor.y, scale=monitor.scale
                        )
                    else:
                        self.notify("Layout configuration kept.", severity="success")
                    self.refresh_displays()

                self.push_screen(ConfirmDisplayScreen(countdown=15), check_confirm)
            else:
                self.notify(f"Error disabling {monitor.name}: {msg}", severity="error")

    def handle_mirror_for(self, target_name: str) -> None:
        def check_mirror(result: Tuple[bool, str] | None) -> None:
            if result:
                success, msg = result
                if success:
                    self.notify(msg, severity="information")
                    self.refresh_displays()
                else:
                    self.notify(f"Failed: {msg}", severity="error")

        self.push_screen(MirrorSelectScreen(target_name, self._displays), check_mirror)

    def action_open_profiles(self) -> None:
        def check_profile(result: Tuple[bool, str] | None) -> None:
            if result:
                success, msg = result
                if success:
                    self.notify(msg, severity="information")
                    self.refresh_displays()
                else:
                    self.notify(f"Failed: {msg}", severity="error")

        self.push_screen(ProfileScreen(self._displays), check_profile)

def run() -> None:
    """Entry point for the installed `hyprvisual` command."""
    DisplayTUIApp().run()

if __name__ == "__main__":
    run()
