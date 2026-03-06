from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Horizontal, Container, Vertical, Center, Middle
from textual.widgets import Header, Footer, Switch, Label, Button
from textual.reactive import reactive
from textual.theme import Theme
from textual.screen import ModalScreen
from display_manager import DisplayManager, Display
from typing import List
from rich.text import Text


def mnemonic(label: str, key: str, key_style: str = "bold underline") -> Text:
    """Return a Rich Text with the first occurrence of `key` styled as a mnemonic."""
    t = Text()
    idx = label.lower().find(key.lower())
    if idx == -1:
        return Text(label)
    t.append(label[:idx])
    t.append(label[idx], style=key_style)
    t.append(label[idx + 1:])
    return t


# ─────────────────────────────────────────────────────────────
#  Modals
# ─────────────────────────────────────────────────────────────

class MirrorSelectScreen(ModalScreen[str | None]):
    """Modal to select a source monitor to mirror from."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("space", "press_focused", "Select"),
    ]

    def __init__(self, monitors: List[Display], target_name: str, **kwargs):
        super().__init__(**kwargs)
        self.monitors = monitors
        self.target_name = target_name

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
                            mnemonic("✕  Disable Mirror Mode", "D"),
                            variant="warning", id="mirror-disable", classes="modal-btn"
                        )
                    yield Button(
                        mnemonic("Cancel", "C"),
                        variant="default", id="mirror-cancel", classes="modal-btn"
                    )

    def on_mount(self) -> None:
        try:
            self.query(".modal-btn").first(Button).focus()
        except Exception:
            pass

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_press_focused(self) -> None:
        if self.focused and isinstance(self.focused, Button):
            self.focused.press()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id == "mirror-cancel":
            self.dismiss(None)
        elif btn_id == "mirror-disable":
            self.dismiss("__disable__")
        elif btn_id.startswith("mirror-src-"):
            self.dismiss(btn_id[len("mirror-src-"):])


class HzSelectScreen(ModalScreen[str | None]):
    """Modal to select a display mode (resolution@Hz)."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("space", "press_focused", "Select"),
    ]

    def __init__(self, monitor: Display, **kwargs):
        super().__init__(**kwargs)
        self.monitor = monitor

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="hz-dialog"):
                    yield Label(f"⚡  Frequency Selector — {self.monitor.name}", id="hz-title")
                    yield Label("↑↓ move  ·  Space/Enter select  ·  Esc cancel", id="hz-prompt")
                    with Vertical(id="hz-options"):
                        seen = set()
                        for mode in self.monitor.available_modes:
                            if mode in seen:
                                continue
                            seen.add(mode)
                            current = abs(self.monitor.refreshRate - float(mode.split("@")[1].replace("Hz", ""))) < 1
                            suffix = "  ← current" if current else ""
                            variant = "success" if current else "default"
                            label = Text()
                            label.append(mode)
                            if suffix:
                                label.append(suffix, style="dim")
                            yield Button(
                                label,
                                id=f"hz-mode-{mode.replace('@', '-').replace('.', '_')}",
                                classes="modal-btn",
                                variant=variant,
                            )
                    yield Button(
                        mnemonic("Cancel", "C"),
                        variant="default", id="hz-cancel", classes="modal-btn"
                    )

    def on_mount(self) -> None:
        try:
            btns = self.query(".modal-btn")
            for btn in btns:
                if "current" in str(btn.label):
                    btn.focus()
                    return
            btns.first(Button).focus()
        except Exception:
            pass

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_press_focused(self) -> None:
        if self.focused and isinstance(self.focused, Button):
            self.focused.press()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id == "hz-cancel":
            self.dismiss(None)
        elif btn_id.startswith("hz-mode-"):
            # Recover original mode string from id
            raw = btn_id[len("hz-mode-"):]
            # Find the matching original mode string
            key = raw.replace("-", "@", 1).replace("_", ".")
            # Match against available_modes
            for mode in self.monitor.available_modes:
                safe = mode.replace("@", "-").replace(".", "_")
                if safe == raw:
                    self.dismiss(mode)
                    return
            self.dismiss(None)


class ConfirmDisplayScreen(ModalScreen[bool]):
    """A modal that requires confirmation before a 15s timeout, then reverts."""

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


# ─────────────────────────────────────────────────────────────
#  Display Card Widget
# ─────────────────────────────────────────────────────────────

class DisplayWidget(Horizontal):
    """
    A focusable monitor card.

    Keyboard shortcuts (active when card is focused):
      Space / Enter  → toggle on/off switch
      m              → open Mirror selector
      h              → open Hz/frequency selector
    """

    can_focus = True
    is_enabled = reactive(False)

    BINDINGS = [
        ("space", "toggle_monitor", "Toggle On/Off"),
        ("enter", "toggle_monitor", "Toggle On/Off"),
        ("m", "open_mirror", "Mirror (m)"),
        ("h", "open_hz", "Hz Picker (h)"),
    ]

    def __init__(self, monitor: Display, all_monitors: List[Display], **kwargs):
        super().__init__(**kwargs)
        self.monitor = monitor
        self.all_monitors = all_monitors

    def compose(self) -> ComposeResult:
        is_mirroring = self.monitor.mirror_of != "none"
        mirror_badge = f"  󰿏→{self.monitor.mirror_of}" if is_mirroring else ""
        ws = self.monitor.active_workspace_name
        hz = self.monitor.refreshRate
        hz_label = f"⚡{hz:.0f}Hz" if hz >= 100 else f"{hz:.0f}Hz"

        with Horizontal(classes="display-container"):
            yield Label("", id=f"icon-{self.monitor.name}", classes="status-icon")

            with Vertical(classes="display-info"):
                yield Label(
                    f"󰍹  {self.monitor.name}  [WS {ws}]{mirror_badge}",
                    classes="display-name"
                )
                yield Label(
                    f"{self.monitor.description[:48]}  ·  {self.monitor.width}×{self.monitor.height} @ {hz_label}",
                    classes="display-detail"
                )

            with Vertical(classes="display-hints"):
                yield Label("[$accent]Space[/$accent]  On/Off", classes="hint-label", markup=True)
                yield Label("[$accent]m[/$accent]irror  ·  [$accent]h[/$accent]z-pick  ·  [$accent]i[/$accent]dentify", classes="hint-label", markup=True)

            # Switch is non-focusable; the card itself is the focus unit
            switch = Switch(id=f"switch-{self.monitor.name}")
            switch.display_name = self.monitor.name
            switch.can_focus = False
            yield switch

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

    def action_toggle_monitor(self) -> None:
        sw = self.query_one(Switch)
        sw.value = not sw.value

    def action_open_mirror(self) -> None:
        self.app.handle_mirror_for(self.monitor.name)

    def action_open_hz(self) -> None:
        self.app.handle_hz_for(self.monitor)


# ─────────────────────────────────────────────────────────────
#  Main App
# ─────────────────────────────────────────────────────────────

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

    /* Monitor Card */
    .display-container {
        height: auto;
        padding: 1 2;
        margin-bottom: 1;
        align: left middle;
        background: $surface;
        border: solid $surface-lighten-2;
        transition: background 200ms linear, border 200ms linear;
    }

    DisplayWidget:focus .display-container {
        border: solid $accent;
        background: $boost;
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

    .display-hints {
        width: 22;
        height: auto;
        content-align: right middle;
        padding-right: 2;
    }

    .hint-label {
        color: $text-muted;
        text-style: dim;
        text-align: right;
    }

    /* ── Modals shared ─────────────────────────── */
    #mirror-dialog, #hz-dialog {
        width: 62%;
        height: auto;
        padding: 2 4;
        background: $surface;
        border: thick $accent;
        align: center middle;
    }

    #confirm-dialog {
        width: 60%;
        height: auto;
        padding: 2 4;
        background: $surface;
        border: thick $warning;
        align: center middle;
    }

    #mirror-title, #hz-title {
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
    }

    #confirm-title {
        text-style: bold;
        color: $warning;
        padding-bottom: 1;
    }

    #mirror-prompt, #hz-prompt, #countdown-label {
        color: $text-muted;
        padding-bottom: 1;
    }

    #mirror-options, #hz-options {
        height: auto;
        padding-bottom: 1;
        max-height: 20;
        overflow-y: auto;
    }

    .modal-btn { margin-bottom: 1; }

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
        ("i", "identify_displays", "Identify Monitors"),
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

    def action_identify_displays(self) -> None:
        """Show numbered overlays on each physical monitor for 3 seconds."""
        active = [d for d in self._displays if not d.disabled]
        if not active:
            self.notify("No active monitors to identify.", severity="warning")
            return
        self.notify("Showing monitor numbers for 3 seconds...", severity="information")
        # Run in background thread so TUI stays responsive
        import threading
        t = threading.Thread(
            target=DisplayManager.identify_displays,
            args=(active,),
            daemon=True
        )
        t.start()

    def refresh_displays(self) -> None:
        display_list = self.query_one("#display-list")
        display_list.remove_children()
        self._displays = DisplayManager.get_displays()
        for d in self._displays:
            display_list.mount(DisplayWidget(monitor=d, all_monitors=self._displays))
        self.set_timer(0.2, self._finish_initialization)

    def _finish_initialization(self) -> None:
        self.is_initializing = False
        try:
            self.query_one(DisplayWidget).focus()
        except Exception:
            pass

    # ── Mirror ────────────────────────────────────────────────

    def handle_mirror_for(self, monitor_name: str) -> None:
        def handle_result(source: str | None) -> None:
            if source is None:
                return
            if source == "__disable__":
                ok, msg = DisplayManager.unset_mirror(monitor_name)
            else:
                ok, msg = DisplayManager.set_mirror(source, monitor_name)

            self.notify(
                f"{'Mirror disabled on' if source == '__disable__' else f'{monitor_name} mirrors'} {monitor_name if source == '__disable__' else source} ✓"
                if ok else f"Error: {msg}",
                severity="information" if ok else "error"
            )
            if ok:
                self.set_timer(0.6, self.action_refresh_displays)

        self.push_screen(
            MirrorSelectScreen(monitors=self._displays, target_name=monitor_name),
            handle_result
        )

    # ── Hz selector ───────────────────────────────────────────

    def handle_hz_for(self, monitor: Display) -> None:
        def handle_result(mode: str | None) -> None:
            if not mode:
                return
            # mode looks like "1920x1080@143.85Hz"
            try:
                res, hz_part = mode.split("@")
                hz = hz_part.replace("Hz", "")
                cmd_mode = f"{res}@{hz}"
            except Exception:
                cmd_mode = "preferred"

            import subprocess
            try:
                subprocess.run(
                    ["hyprctl", "keyword", "monitor", f"{monitor.name},{cmd_mode},auto,1"],
                    capture_output=True, text=True, check=True
                )
                self.notify(f"{monitor.name} → {mode} ✓", severity="information")
                self.set_timer(0.6, self.action_refresh_displays)
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")

        self.push_screen(HzSelectScreen(monitor=monitor), handle_result)

    # ── Switch toggle ─────────────────────────────────────────

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if self.is_initializing:
            return

        switch = event.switch
        display_name = getattr(switch, "display_name", None)
        is_enabled = event.value

        if not display_name:
            return

        previous_state = not is_enabled
        best_mode = next(
            (d.best_mode for d in self._displays if d.name == display_name),
            "preferred"
        )
        success, msg = DisplayManager.set_display_state(display_name, is_enabled, best_mode)

        if not success:
            self.notify(f"Failed: {msg}", severity="error")
            self.is_initializing = True
            switch.value = previous_state
            self.set_timer(0.2, self._finish_initialization)
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
                DisplayManager.set_display_state(display_name, previous_state, best_mode)
                self.is_initializing = True
                switch.value = previous_state
                if widget:
                    widget.is_enabled = previous_state
                self.set_timer(0.2, self._finish_initialization)

        self.push_screen(ConfirmDisplayScreen(), check_confirmation)

    # ── Helpers ───────────────────────────────────────────────

    def _find_display_widget(self, node) -> "DisplayWidget | None":
        for ancestor in node.ancestors:
            if isinstance(ancestor, DisplayWidget):
                return ancestor
        return None


if __name__ == "__main__":
    DisplayTUIApp().run()
