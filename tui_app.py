from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Horizontal, Container, Vertical, Center, Middle
from textual.widgets import Header, Footer, Switch, Label, Button
from textual.reactive import reactive
from textual.theme import Theme
from textual.screen import ModalScreen
from display_manager import DisplayManager, Display
from typing import List


class MirrorSelectScreen(ModalScreen[str | None]):
    """Modal to select a source monitor to mirror from."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, monitors: List[Display], target_name: str, **kwargs):
        super().__init__(**kwargs)
        self.monitors = monitors
        self.target_name = target_name

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="mirror-dialog"):
                    yield Label(f"󰿏  Mirror  {self.target_name}  from:", id="mirror-title")
                    yield Label("Select a source (↑↓ navigate, Enter/Space select):", id="mirror-prompt")
                    with Vertical(id="mirror-options"):
                        for m in self.monitors:
                            if m.name != self.target_name:
                                yield Button(
                                    f"󰍹  {m.name}  ({m.description[:30]})",
                                    id=f"mirror-src-{m.name}",
                                    classes="mirror-btn"
                                )
                        yield Button("✕  Disable Mirror Mode", variant="warning", id="mirror-disable")
                    yield Button("Cancel", variant="default", id="mirror-cancel")

    def on_mount(self) -> None:
        # Focus the first option automatically for keyboard navigation
        try:
            first_btn = self.query(".mirror-btn").first(Button)
            first_btn.focus()
        except Exception:
            pass

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "mirror-cancel":
            self.dismiss(None)
        elif btn_id == "mirror-disable":
            self.dismiss("__disable__")
        elif btn_id and btn_id.startswith("mirror-src-"):
            self.dismiss(btn_id[len("mirror-src-"):])


class DisplayWidget(Horizontal):
    """A focusable card widget for a single display."""

    can_focus = True         # Allow Tab to land on this widget
    is_enabled = reactive(False)

    BINDINGS = [
        ("space", "toggle_switch", "Toggle On/Off"),
        ("m", "open_mirror", "Mirror"),
        ("enter", "toggle_switch", "Toggle On/Off"),
    ]

    def __init__(self, monitor: Display, all_monitors: List[Display], **kwargs):
        super().__init__(**kwargs)
        self.monitor = monitor
        self.all_monitors = all_monitors

    def compose(self) -> ComposeResult:
        is_mirroring = self.monitor.mirror_of != "none"
        mirror_label = f"→ {self.monitor.mirror_of}" if is_mirroring else ""
        ws = self.monitor.active_workspace_name
        hz = self.monitor.refreshRate

        # Mark 144Hz monitors with a special indicator
        hz_label = f"{hz:.0f}Hz"
        if hz >= 143:
            hz_label = f"⚡{hz:.0f}Hz"

        with Horizontal(classes="display-container"):
            yield Label("", id=f"icon-{self.monitor.name}", classes="status-icon")

            with Vertical(classes="display-info"):
                yield Label(
                    f"󰍹  {self.monitor.name}  [WS {ws}]{('  󰿏  ' + mirror_label) if is_mirroring else ''}",
                    classes="display-name"
                )
                yield Label(
                    f"{self.monitor.description[:48]}  ·  {self.monitor.width}×{self.monitor.height} @ {hz_label}",
                    classes="display-detail"
                )

            with Vertical(classes="display-actions"):
                switch = Switch(id=f"switch-{self.monitor.name}")
                switch.display_name = self.monitor.name
                yield switch
                mirror_variant = "warning" if is_mirroring else "default"
                mirror_btn = Button(
                    "󰿏 Mirror [m]",
                    variant=mirror_variant,
                    id=f"mirror-btn-{self.monitor.name}",
                    classes="action-btn"
                )
                mirror_btn.monitor_name = self.monitor.name
                yield mirror_btn

    def on_mount(self) -> None:
        self.is_enabled = not self.monitor.disabled
        self.query_one(Switch).value = self.is_enabled

    def watch_is_enabled(self, old_val: bool, new_val: bool) -> None:
        try:
            self.query_one(f"#icon-{self.monitor.name}", Label).update(
                "🟢" if new_val else "🔴"
            )
        except Exception:
            pass

    def action_toggle_switch(self) -> None:
        """Toggle the monitor's switch when Space/Enter pressed on the card."""
        sw = self.query_one(Switch)
        sw.value = not sw.value

    def action_open_mirror(self) -> None:
        """Open mirror dialog for this card via 'm' shortcut."""
        # Let the App handle it through on_button_pressed by simulating a button press
        self.app.handle_mirror_for(self.monitor.name)


class ConfirmDisplayScreen(ModalScreen[bool]):
    """A modal screen that asks for confirmation before a timeout."""

    countdown = reactive(15)

    BINDINGS = [
        ("left", "focus_keep", "Keep"),
        ("right", "focus_revert", "Revert"),
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
                        yield Button("Keep Changes  [←]", variant="success", id="btn-keep")
                        yield Button("[→]  Revert", variant="error", id="btn-revert")

    def on_mount(self) -> None:
        self.timer = self.set_interval(1, self.tick)
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
        self.dismiss(self.focused and self.focused.id == "btn-keep")

    def action_cancel(self) -> None:
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-keep")


class DisplayTUIApp(App):
    """hyprmonitor – TUI Display Layout Controller for Hyprland."""

    CSS = """
    Screen {
        align: center middle;
    }

    #main-container {
        width: 90%;
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

    /* Card */
    .display-container {
        height: auto;
        padding: 1 2;
        margin-bottom: 2;
        align: left middle;
        background: $surface;
        border: solid $surface-lighten-2;
        transition: background 300ms in_out_cubic, border 300ms in_out_cubic;
    }

    DisplayWidget:focus .display-container {
        border: solid $accent;
        background: $boost;
    }

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

    .display-actions {
        width: auto;
        height: auto;
        align: center middle;
        padding-left: 2;
    }

    .action-btn {
        margin-top: 1;
        min-width: 14;
    }

    /* Mirror Dialog */
    #mirror-dialog {
        width: 60%;
        height: auto;
        padding: 2 4;
        background: $surface;
        border: thick $accent;
        align: center middle;
    }

    #mirror-title {
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
    }

    #mirror-prompt { color: $text-muted; padding-bottom: 1; }

    #mirror-options { height: auto; padding-bottom: 1; }

    .mirror-btn { margin-bottom: 1; }

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

    #countdown-label { color: $text-muted; padding-bottom: 2; }

    #confirm-buttons {
        height: auto;
        align: center middle;
        padding-top: 1;
    }

    #confirm-buttons Button { margin: 0 2; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh_displays", "Refresh"),
        ("t", "cycle_theme", "Cycle Theme"),
    ]

    THEMES_LIST = ["textual-dark", "glass", "hacker", "nordic"]
    current_theme_idx = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_initializing = True
        self._displays: List[Display] = []

    def on_mount(self) -> None:
        self.title = "hyprmonitor – Display Layout Controller"

        self.register_theme(Theme(
            name="glass", primary="#42A5F5", accent="#2196F3",
            background="#121212", surface="#1E1E1E", boost="#2C2C2C", dark=True
        ))
        self.register_theme(Theme(
            name="hacker", primary="#00FF00", accent="#00FF00",
            background="#000000", surface="#0A1A0A", boost="#0F2F0F",
            success="#00FF00", dark=True
        ))
        self.register_theme(Theme(
            name="nordic", primary="#88C0D0", accent="#5E81AC",
            background="#2E3440", surface="#3B4252", boost="#434C5E",
            text_alpha=0.9, dark=True
        ))

        self.theme = self.THEMES_LIST[0]
        self.refresh_displays()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            yield Label("󰍹  DISPLAY LAYOUT CONTROLLER", classes="title")
            yield VerticalScroll(id="display-list")
        yield Footer()

    def action_refresh_displays(self) -> None:
        self.is_initializing = True
        self.refresh_displays()

    def action_cycle_theme(self) -> None:
        self.current_theme_idx = (self.current_theme_idx + 1) % len(self.THEMES_LIST)
        new_theme = self.THEMES_LIST[self.current_theme_idx]
        self.theme = new_theme
        self.notify(f"Theme: {new_theme.title()}", severity="information")

    def refresh_displays(self) -> None:
        display_list = self.query_one("#display-list")
        display_list.remove_children()
        self._displays = DisplayManager.get_displays()
        for d in self._displays:
            display_list.mount(DisplayWidget(monitor=d, all_monitors=self._displays))
        self.set_timer(0.2, self._finish_initialization)

    def _finish_initialization(self) -> None:
        self.is_initializing = False
        # Focus first card
        try:
            self.query_one(DisplayWidget).focus()
        except Exception:
            pass

    # ── Mirror ──────────────────────────────────────────────────────────────

    def handle_mirror_for(self, monitor_name: str) -> None:
        """Open the mirror selection modal for a given monitor name."""
        def handle_result(source: str | None) -> None:
            if source is None:
                return
            if source == "__disable__":
                ok, msg = DisplayManager.unset_mirror(monitor_name)
                severity = "information" if ok else "error"
                self.notify(
                    f"Mirror disabled on {monitor_name}" if ok else f"Error: {msg}",
                    severity=severity
                )
            else:
                ok, msg = DisplayManager.set_mirror(source, monitor_name)
                severity = "information" if ok else "error"
                self.notify(
                    f"{monitor_name} now mirrors {source}" if ok else f"Error: {msg}",
                    severity=severity
                )
            if ok:
                self.set_timer(0.5, self.action_refresh_displays)

        self.push_screen(
            MirrorSelectScreen(monitors=self._displays, target_name=monitor_name),
            handle_result
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("mirror-btn-"):
            monitor_name = btn_id[len("mirror-btn-"):]
            self.handle_mirror_for(monitor_name)

    # ── Switch toggle ────────────────────────────────────────────────────────

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if self.is_initializing:
            return

        switch = event.switch
        display_name = getattr(switch, "display_name", None)
        is_enabled = event.value

        if not display_name:
            return

        previous_state = not is_enabled
        # Find the monitor's best mode so re-enable uses 144Hz instead of 60Hz
        best_mode = next(
            (d.best_mode for d in self._displays if d.name == display_name),
            "preferred"
        )
        success, msg = DisplayManager.set_display_state(display_name, is_enabled, best_mode)

        if not success:
            self.notify(f"Failed: {msg}", severity="error")
            switch.value = previous_state
            return

        action = "enabled" if is_enabled else "disabled"
        widget = self._find_display_widget(switch)
        if widget:
            widget.is_enabled = is_enabled

        def check_confirmation(confirmed: bool) -> None:
            if confirmed:
                self.notify(f"{display_name} {action} ✓", severity="information")
            else:
                self.notify("Reverting...", severity="warning")
                DisplayManager.set_display_state(display_name, previous_state)
                self.is_initializing = True
                switch.value = previous_state
                if widget:
                    widget.is_enabled = previous_state
                self.set_timer(0.2, self._finish_initialization)

        self.push_screen(ConfirmDisplayScreen(), check_confirmation)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _find_display_widget(self, node) -> "DisplayWidget | None":
        for ancestor in node.ancestors:
            if isinstance(ancestor, DisplayWidget):
                return ancestor
        return None


if __name__ == "__main__":
    DisplayTUIApp().run()
