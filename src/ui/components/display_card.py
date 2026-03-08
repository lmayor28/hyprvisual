from typing import List, Tuple
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Switch
from textual.widget import Widget
from textual.reactive import reactive

from core.display_manager import Display
from ui.screens.hz import HzSelectScreen
from ui.screens.position import PositionSelectScreen
from ui.screens.scale import ScaleSelectScreen
from ui.screens.workspace import WorkspaceSelectScreen

class DisplayWidget(Widget):
    """A card widget representing a single monitor display."""

    is_enabled = reactive(False)
    has_focus_ring = reactive(False)

    BINDINGS = [
        ("space", "toggle_monitor", "Toggle On/Off"),
        ("enter", "toggle_monitor", "Toggle On/Off"),
        ("m", "open_mirror", "Mirror (m)"),
        ("h", "open_hz", "Hz (h)"),
        ("p", "open_position", "Position (p)"),
        ("s", "open_scale", "Scale (s)"),
        ("i", "identify_blink", "Identify (i)"),
        ("w", "open_workspace", "Workspace (w)")
    ]

    def __init__(self, monitor: Display, all_monitors: List[Display], **kwargs):
        super().__init__(**kwargs)
        self.monitor = monitor
        self.all_monitors = all_monitors
        self.is_enabled = not monitor.disabled
        self.can_focus = True

    def compose(self) -> ComposeResult:
        is_mirroring = self.monitor.mirror_of != "none"
        mirror_badge = f"  󰿏→{self.monitor.mirror_of}" if is_mirroring else ""
        ws = self.monitor.active_workspace_name
        hz = self.monitor.refreshRate
        hz_label = f"{hz:.0f}Hz"

        with Horizontal(classes="display-container"):
            yield Label("", id=f"icon-{self.monitor.name}", classes="status-icon")

            with Vertical(classes="display-info"):
                yield Label(
                    f"󰍹  {self.monitor.name}  [WS {ws}]{mirror_badge}",
                    classes="display-name"
                )
                yield Label(
                    f"{self.monitor.description}  ·  {self.monitor.width}x{self.monitor.height} @ {hz_label}  ·  Scale: {self.monitor.scale:.2f}x",
                    classes="display-desc"
                )

            with Vertical(classes="display-hints"):
                yield Label("[$accent]Space[/$accent]  On/Off", classes="hint-label", markup=True)
                yield Label("[$accent]m[/$accent]irror  ·  [$accent]p[/$accent]os  ·  [$accent]s[/$accent]cale  ·  [$accent]i[/$accent]dentify  ·  [$accent]w[/$accent]space", classes="hint-label", markup=True)

            switch = Switch(id=f"switch-{self.monitor.name}")
            switch.value = self.is_enabled
            switch.can_focus = False
            yield switch

    def watch_is_enabled(self, old_val: bool, new_val: bool) -> None:
        try:
            self.query_one(f"#icon-{self.monitor.name}", Label).update(
                "ON" if new_val else "OFF"
            )
        except Exception:
            pass

        try:
            switch = self.query_one(Switch)
            if switch.value != new_val:
                switch.value = new_val
        except Exception:
            pass

    def on_focus(self) -> None:
        self.has_focus_ring = True
        self.add_class("focused")

    def on_blur(self) -> None:
        self.has_focus_ring = False
        self.remove_class("focused")

    def action_toggle_monitor(self) -> None:
        """Called when Space/Enter is pressed while the card is focused."""
        from app import DisplayTUIApp # lazy import to avoid circular dependency
        app = self.app
        if isinstance(app, DisplayTUIApp):
            app.handle_toggle_for(self.monitor, not self.is_enabled)

    def action_open_mirror(self) -> None:
        from app import DisplayTUIApp
        app = self.app
        if isinstance(app, DisplayTUIApp):
            app.handle_mirror_for(self.monitor.name)

    def action_open_hz(self) -> None:
        if self.monitor.disabled:
            self.notify(f"{self.monitor.name} is disabled.", severity="error")
            return

        def check_hz(result: Tuple[bool, str] | None) -> None:
            if result:
                success, msg = result
                if success:
                    self.notify(f"Changed {self.monitor.name} resolution/hz.", severity="information")
                    self.app.refresh_displays()  # type: ignore
                else:
                    self.notify(f"Failed: {msg}", severity="error")

        self.app.push_screen(HzSelectScreen(self.monitor), check_hz)

    def action_open_position(self) -> None:
        if self.monitor.disabled:
            self.notify(f"{self.monitor.name} is disabled.", severity="error")
            return

        def check_pos(result: Tuple[bool, str] | None) -> None:
            if result:
                success, msg = result
                if success:
                    self.notify(f"Moved {self.monitor.name}.", severity="information")
                    self.app.refresh_displays()  # type: ignore
                else:
                    self.notify(f"Failed: {msg}", severity="error")

        self.app.push_screen(PositionSelectScreen(self.monitor, self.all_monitors), check_pos)

    def action_open_scale(self) -> None:
        if self.monitor.disabled:
            self.notify(f"{self.monitor.name} is disabled.", severity="error")
            return

        def check_scale(result: Tuple[bool, str] | None) -> None:
            if result:
                success, msg = result
                if success:
                    self.notify(msg, severity="information")
                    self.app.refresh_displays()  # type: ignore
                else:
                    self.notify(f"Failed: {msg}", severity="error")

        self.app.push_screen(ScaleSelectScreen(self.monitor), check_scale)

    def action_identify_blink(self) -> None:
        if self.monitor.disabled:
            self.notify(f"{self.monitor.name} is disabled.", severity="error")
            return
            
        from core.display_manager import DisplayManager
        self.notify(f"Blinking {self.monitor.name}...", severity="information")
        # Run asynchronously so we don't freeze the TUI during the time.sleep(0.3)
        self.run_worker(self._blink_worker)
        
    async def _blink_worker(self) -> None:
        from core.display_manager import DisplayManager
        DisplayManager.identify_blink(self.monitor.name)

    def action_open_workspace(self) -> None:
        if self.monitor.disabled:
            self.notify(f"{self.monitor.name} is disabled.", severity="error")
            return
            
        def check_ws(result: Tuple[bool, str] | None) -> None:
            if result:
                success, msg = result
                if success:
                    self.notify(msg, severity="information")
                    self.app.refresh_displays()  # type: ignore
                else:
                    self.notify(f"Failed: {msg}", severity="error")

        self.app.push_screen(WorkspaceSelectScreen(self.monitor), check_ws)
