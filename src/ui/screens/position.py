from typing import List, Tuple
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Center, Middle
from textual.widgets import Button, Label
from textual.screen import ModalScreen

from core.display_manager import DisplayManager, Display

class PositionSelectScreen(ModalScreen[Tuple[bool, str] | None]):
    """Modal to select a display position."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "apply", "Apply"),
        ("left", "move_left", "Move Left"),
        ("right", "move_right", "Move Right"),
        ("up", "move_up", "Move Up"),
        ("down", "move_down", "Move Down"),
    ]

    def __init__(self, monitor: Display, all_monitors: List[Display], **kwargs):
        super().__init__(**kwargs)
        self.monitor = monitor
        self.all_monitors = all_monitors
        self._initial_x = monitor.x
        self._initial_y = monitor.y

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="position-dialog"):
                    yield Label(f"Move {self.monitor.name}", id="position-title")
                    yield Label("Use Arrows to move · Enter to apply · Esc cancel", id="position-prompt")
                    yield Label(f"Current: X={self.monitor.x} Y={self.monitor.y}", id="position-current")

                    with Horizontal(id="position-buttons"):
                        yield Button("← Left", id="pos-left", classes="modal-btn")
                        yield Button("Right →", id="pos-right", classes="modal-btn")
                    with Horizontal(id="position-buttons-y"):
                        yield Button("↑ Up", id="pos-up", classes="modal-btn")
                        yield Button("Down ↓", id="pos-down", classes="modal-btn")

                    yield Button("Apply", variant="success", id="pos-apply", classes="modal-btn")

    def on_mount(self) -> None:
        self.query_one("#pos-apply").focus()

    def get_primary_monitor(self) -> Display:
        for m in self.all_monitors:
            if m.x == 0 and m.y == 0:
                return m
        return self.all_monitors[0] if self.all_monitors else self.monitor

    def _update_position_label(self) -> None:
        self.query_one("#position-current", Label).update(f"New: X={self.monitor.x} Y={self.monitor.y}")

    def _move_monitor(self, dx: int, dy: int) -> None:
        self.monitor.x += dx
        self.monitor.y += dy
        self._update_position_label()

    def action_move_left(self) -> None:
        primary = self.get_primary_monitor()
        step_x = primary.width if primary else 1920
        self._move_monitor(-step_x, 0)

    def action_move_right(self) -> None:
        primary = self.get_primary_monitor()
        step_x = primary.width if primary else 1920
        self._move_monitor(step_x, 0)

    def action_move_up(self) -> None:
        primary = self.get_primary_monitor()
        step_y = primary.height if primary else 1080
        self._move_monitor(0, -step_y)

    def action_move_down(self) -> None:
        primary = self.get_primary_monitor()
        step_y = primary.height if primary else 1080
        self._move_monitor(0, step_y)

    def action_apply(self) -> None:
        success, msg = DisplayManager.set_position(
            self.monitor.name, self.monitor.x, self.monitor.y,
            self.monitor.best_mode, self.monitor.scale
        )
        self.dismiss((success, msg))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        primary = self.get_primary_monitor()
        step_x = primary.width if primary else 1920
        step_y = primary.height if primary else 1080

        if btn_id == "pos-left":
            self._move_monitor(-step_x, 0)
        elif btn_id == "pos-right":
            self._move_monitor(step_x, 0)
        elif btn_id == "pos-up":
            self._move_monitor(0, -step_y)
        elif btn_id == "pos-down":
            self._move_monitor(0, step_y)
        elif btn_id == "pos-apply":
            self.action_apply()

    def action_cancel(self) -> None:
        self.monitor.x = self._initial_x
        self.monitor.y = self._initial_y
        self.dismiss(None)
