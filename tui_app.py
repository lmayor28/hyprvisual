from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Horizontal, Container, Vertical, Center, Middle
from textual.widgets import Header, Footer, Switch, Label, Button
from textual.reactive import reactive
from textual.theme import Theme
from textual.screen import ModalScreen
from display_manager import DisplayManager, Display

class DisplayWidget(Horizontal):
    """A card widget to represent a single display and its toggle switch."""
    
    is_enabled = reactive(False)

    def __init__(self, monitor: Display, **kwargs):
        super().__init__(**kwargs)
        self.monitor = monitor

    def compose(self) -> ComposeResult:
        with Horizontal(classes="display-container"):
            # Status icon that changes reactively
            yield Label("", id=f"icon-{self.monitor.name}", classes="status-icon")
            
            with Vertical(classes="display-info"):
                yield Label(f"󰍹  {self.monitor.name}", classes="display-name")
                yield Label(f"{self.monitor.description} ({self.monitor.width}x{self.monitor.height} @ {self.monitor.refreshRate:.1f}Hz)", classes="display-detail")
            
            # The switch
            switch = Switch(id=f"switch-{self.monitor.name}")
            switch.display_name = self.monitor.name
            yield switch

    def on_mount(self) -> None:
        self.is_enabled = not self.monitor.disabled
        # Manually set the switch initial value without triggering events if possible
        self.query_one(Switch).value = self.is_enabled

    def watch_is_enabled(self, old_val: bool, new_val: bool) -> None:
        """Textual reactive watcher: automatically updates UI when self.is_enabled changes."""
        try:
            icon_label = self.query_one(f"#icon-{self.monitor.name}", Label)
            if new_val:
                icon_label.update("🟢")
            else:
                icon_label.update("🔴")
        except Exception:
            pass


class ConfirmDisplayScreen(ModalScreen[bool]):
    """A modal screen that asks for confirmation before a timeout."""

    countdown = reactive(15)

    BINDINGS = [
        ("left", "focus_keep", "Focus Keep"),
        ("right", "focus_revert", "Focus Revert"),
        ("space", "accept", "Accept"),
        ("enter", "accept", "Accept"),
        ("escape", "cancel", "Cancel")
    ]

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="confirm-dialog"):
                    yield Label("Display setup changed.", id="confirm-title")
                    yield Label("Keep this configuration?", id="confirm-prompt")
                    yield Label(f"Reverting in {self.countdown} seconds...", id="countdown-label")
                    with Horizontal(id="confirm-buttons"):
                        yield Button("Keep Changes", variant="success", id="btn-keep")
                        yield Button("Revert", variant="error", id="btn-revert")

    def on_mount(self) -> None:
        self.timer = self.set_interval(1, self.tick)
        # Default security: Focus 'Revert' button so Space/Enter triggers revert by default
        self.query_one("#btn-revert").focus()

    def tick(self) -> None:
        self.countdown -= 1
        self.query_one("#countdown-label").update(f"Reverting in {self.countdown} seconds...")
        if self.countdown <= 0:
            self.dismiss(False)

    def action_focus_keep(self) -> None:
        self.query_one("#btn-keep").focus()
        
    def action_focus_revert(self) -> None:
        self.query_one("#btn-revert").focus()
        
    def action_accept(self) -> None:
        if self.focused and self.focused.id == "btn-keep":
            self.dismiss(True)
        else:
            # Revert is the default action if anything else is focused
            self.dismiss(False)
            
    def action_cancel(self) -> None:
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-keep":
            self.dismiss(True)
        else:
            self.dismiss(False)


class DisplayTUIApp(App):
    """A Textual app to manage display layouts using modern TUI best practices."""

    CSS = """
    Screen {
        align: center middle;
    }
    
    #main-container {
        width: 80%;
        height: 100%;
        min-height: 50%;
        padding: 2 4;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding-bottom: 2;
        margin-bottom: 1;
        width: 100%;
        border-bottom: solid $primary;
    }

    /* Card Design */
    .display-container {
        height: auto;
        padding: 1 2;
        margin-bottom: 2;
        align: left middle;
        background: $surface;
        border: solid $surface-lighten-2;
        transition: background 300ms in_out_cubic, border 300ms in_out_cubic;
    }

    /* Hover Effects */
    .display-container:hover {
        background: $boost;
        border: solid $accent;
    }

    .status-icon {
        width: 4;
        content-align: center middle;
        margin-right: 1;
    }

    .display-info {
        width: 1fr;
        height: auto;
        content-align: left middle;
    }

    .display-name {
        text-style: bold;
        color: $text;
    }

    .display-detail {
        color: $text-muted;
    }

    /* Confirm Dialog */
    #confirm-dialog {
        width: 60%;
        height: auto;
        padding: 2 4;
        background: $surface;
        border: thick $warning;
        align: center middle;
    }

    #confirm-title {
        text-style: bold;
        color: $warning;
        padding-bottom: 1;
    }
    
    #countdown-label {
        color: $text-muted;
        padding-bottom: 2;
    }

    #confirm-buttons {
        height: auto;
        align: center middle;
        padding-top: 1;
    }

    #confirm-buttons Button {
        margin: 0 2;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh_displays", "Refresh Displays"),
        ("t", "cycle_theme", "Cycle Theme")
    ]

    THEMES_LIST = ["textual-dark", "glass", "hacker", "nordic"]
    current_theme_idx = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_initializing = True

    def on_mount(self) -> None:
        self.title = "Phantom Rosette - Display TUI"
        
        # Register Custom Themes using the Native Theme API
        self.register_theme(Theme(
            name="glass",
            primary="#42A5F5",
            accent="#2196F3",
            background="#121212",
            surface="#1E1E1E",
            boost="#2C2C2C",
            dark=True
        ))
        
        self.register_theme(Theme(
            name="hacker",
            primary="#00FF00",
            accent="#00FF00",
            background="#000000",
            surface="#0A1A0A",
            boost="#0F2F0F",
            success="#00FF00",
            dark=True
        ))
        
        self.register_theme(Theme(
            name="nordic",
            primary="#88C0D0",
            accent="#5E81AC",
            background="#2E3440",
            surface="#3B4252",
            boost="#434C5E",
            text_alpha=0.9,
            dark=True
        ))
        
        self.theme = self.THEMES_LIST[0]
        self.refresh_displays()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        with Container(id="main-container"):
            yield Label("󰍹  DISPLAY LAYOUT CONTROLLER", classes="title")
            yield VerticalScroll(id="display-list")
        yield Footer()

    def action_refresh_displays(self) -> None:
        self.is_initializing = True
        self.refresh_displays()
        
    def action_cycle_theme(self) -> None:
        """Cycle through the registered themes using native Theme API."""
        self.current_theme_idx = (self.current_theme_idx + 1) % len(self.THEMES_LIST)
        new_theme = self.THEMES_LIST[self.current_theme_idx]
        self.theme = new_theme
        self.notify(f"Theme changed to: {new_theme.title()}", severity="information")

    def refresh_displays(self) -> None:
        display_list = self.query_one("#display-list")
        display_list.remove_children()
        
        manager = DisplayManager()
        self.displays = manager.get_displays()
        
        for d in self.displays:
             display_list.mount(DisplayWidget(monitor=d))
             
        # Allow time for switches to mount before enabling events
        self.set_timer(0.2, self._finish_initialization)

    def _finish_initialization(self) -> None:
        self.is_initializing = False

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle a switch toggle event."""
        if self.is_initializing:
            return
            
        switch = event.switch
        display_name = getattr(switch, "display_name", None)
        is_enabled = event.value
        
        if display_name:
            # 1. Store previous state in case we need to revert
            previous_state = not is_enabled
            
            # 2. Apply new state
            success, msg = DisplayManager.set_display_state(display_name, is_enabled)
            
            if not success:
               self.notify(f"Failed to change state: {msg}", severity="error")
               switch.value = previous_state
               return

            action = "enabled" if is_enabled else "disabled"
            
            # 3. Update the reactive state of the Widget temporally
            widget = switch.ancestors[1] # DisplayWidget is conceptually the parent
            if isinstance(widget, DisplayWidget):
                widget.is_enabled = is_enabled
            else:
                for node in switch.ancestors:
                    if isinstance(node, DisplayWidget):
                        node.is_enabled = is_enabled
                        break

            # 4. Push Confirm Dialog
            def check_confirmation(confirmed: bool) -> None:
                if confirmed:
                    self.notify(f"Display {display_name} {action} successfully kept", severity="information")
                else:
                    self.notify("Reverting display changes...", severity="warning")
                    # Revert backend
                    DisplayManager.set_display_state(display_name, previous_state)
                    # Revert UI Switch (this re-triggers on_switch_changed but we are initializing)
                    self.is_initializing = True
                    switch.value = previous_state
                    if isinstance(widget, DisplayWidget):
                        widget.is_enabled = previous_state
                    else:
                        for node in switch.ancestors:
                            if isinstance(node, DisplayWidget):
                                node.is_enabled = previous_state
                                break
                    self.set_timer(0.2, self._finish_initialization)

            self.push_screen(ConfirmDisplayScreen(), check_confirmation)

if __name__ == "__main__":
    app = DisplayTUIApp()
    app.run()
