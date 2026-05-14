"""
Tests for DisplayManager.

Strategy: mock subprocess.run so tests run without Hyprland.
Each test verifies the *contract* — what command gets sent to hyprctl —
not the internal implementation details.
"""
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from hyprvisual.core.display_manager import DisplayManager, Display
from tests.conftest import MONITOR_JSON, MONITOR_JSON_STR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_run(stdout: str = "", returncode: int = 0):
    """Return a mock that simulates subprocess.run with given stdout."""
    m = MagicMock()
    m.stdout = stdout
    m.returncode = returncode
    return m


def _capture_cmd(monkeypatch) -> list:
    """Patch subprocess.run to record calls; returns a list that fills on each call."""
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.stdout = ""
        m.returncode = 0
        return m

    monkeypatch.setattr(subprocess, "run", fake_run)
    return calls


# ---------------------------------------------------------------------------
# get_displays
# ---------------------------------------------------------------------------

class TestGetDisplays:
    def test_parses_all_monitors(self, monkeypatch):
        monkeypatch.setattr(
            subprocess, "run",
            lambda *a, **kw: _mock_run(stdout=MONITOR_JSON_STR),
        )
        displays = DisplayManager.get_displays()
        assert len(displays) == 3

    def test_fields_mapped_correctly(self, monkeypatch):
        monkeypatch.setattr(
            subprocess, "run",
            lambda *a, **kw: _mock_run(stdout=MONITOR_JSON_STR),
        )
        displays = DisplayManager.get_displays()
        dp1 = displays[0]

        assert dp1.name == "DP-1"
        assert dp1.width == 2560
        assert dp1.height == 1440
        assert dp1.refreshRate == 143.85
        assert dp1.x == 0
        assert dp1.y == 0
        assert dp1.scale == 1.0
        assert dp1.disabled is False
        assert dp1.active_workspace_id == 1
        assert dp1.mirror_of == "none"

    def test_scale_field_preserved(self, monkeypatch):
        monkeypatch.setattr(
            subprocess, "run",
            lambda *a, **kw: _mock_run(stdout=MONITOR_JSON_STR),
        )
        displays = DisplayManager.get_displays()
        assert displays[1].scale == 1.5  # HDMI-1 has scale 1.5

    def test_disabled_monitor_parsed(self, monkeypatch):
        monkeypatch.setattr(
            subprocess, "run",
            lambda *a, **kw: _mock_run(stdout=MONITOR_JSON_STR),
        )
        displays = DisplayManager.get_displays()
        edp = displays[2]
        assert edp.disabled is True
        assert edp.name == "eDP-1"

    def test_best_mode_picks_highest_hz_at_native_res(self, monkeypatch):
        """DP-1 native is 2560x1440; highest Hz at that res is 143.85 Hz."""
        monkeypatch.setattr(
            subprocess, "run",
            lambda *a, **kw: _mock_run(stdout=MONITOR_JSON_STR),
        )
        displays = DisplayManager.get_displays()
        assert displays[0].best_mode == "2560x1440@143.85"

    def test_best_mode_not_confused_by_other_resolutions(self, monkeypatch):
        """HDMI-1 native is 1920x1080 @ 60 Hz — 1920x1080@143.85Hz doesn't exist."""
        monkeypatch.setattr(
            subprocess, "run",
            lambda *a, **kw: _mock_run(stdout=MONITOR_JSON_STR),
        )
        displays = DisplayManager.get_displays()
        assert displays[1].best_mode == "1920x1080@60.00"

    def test_returns_empty_on_subprocess_error(self, monkeypatch):
        def boom(*a, **kw):
            raise subprocess.CalledProcessError(1, "hyprctl")

        monkeypatch.setattr(subprocess, "run", boom)
        assert DisplayManager.get_displays() == []

    def test_returns_empty_on_invalid_json(self, monkeypatch):
        monkeypatch.setattr(
            subprocess, "run",
            lambda *a, **kw: _mock_run(stdout="not json"),
        )
        assert DisplayManager.get_displays() == []

    def test_passes_correct_hyprctl_args(self, monkeypatch):
        calls = _capture_cmd(monkeypatch)
        # Override to also return valid JSON
        real_fake = calls.append

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            m = MagicMock()
            m.stdout = MONITOR_JSON_STR
            return m

        monkeypatch.setattr(subprocess, "run", fake_run)
        DisplayManager.get_displays()
        assert calls[0] == ["hyprctl", "monitors", "all", "-j"]


# ---------------------------------------------------------------------------
# set_display_state
# ---------------------------------------------------------------------------

class TestSetDisplayState:
    def test_disable_sends_correct_command(self, monkeypatch):
        calls = _capture_cmd(monkeypatch)
        DisplayManager.set_display_state("DP-1", enable=False)
        assert calls[0] == ["hyprctl", "keyword", "monitor", "DP-1,disable"]

    def test_enable_uses_provided_position(self, monkeypatch):
        """Regression: re-enabling a monitor must restore its X/Y/scale, not use 'auto'."""
        calls = _capture_cmd(monkeypatch)
        DisplayManager.set_display_state(
            "DP-1", enable=True, best_mode="2560x1440@143.85",
            x=2560, y=0, scale=1.25,
        )
        assert calls[0] == [
            "hyprctl", "keyword", "monitor",
            "DP-1,2560x1440@143.85,2560x0,1.25",
        ]

    def test_enable_defaults_position_to_origin(self, monkeypatch):
        """With no explicit x/y/scale, defaults to 0x0 at scale 1.0."""
        calls = _capture_cmd(monkeypatch)
        DisplayManager.set_display_state("DP-1", enable=True, best_mode="preferred")
        assert calls[0] == ["hyprctl", "keyword", "monitor", "DP-1,preferred,0x0,1.0"]

    def test_enable_does_not_use_auto_keyword(self, monkeypatch):
        """'auto' was the old default — must never appear after the fix."""
        calls = _capture_cmd(monkeypatch)
        DisplayManager.set_display_state("DP-1", enable=True)
        assert "auto" not in calls[0][3]

    def test_returns_false_on_error(self, monkeypatch):
        def boom(*a, **kw):
            raise subprocess.CalledProcessError(1, "hyprctl", stderr="bad")

        monkeypatch.setattr(subprocess, "run", boom)
        ok, msg = DisplayManager.set_display_state("DP-1", enable=False)
        assert ok is False
        assert "Error" in msg


# ---------------------------------------------------------------------------
# set_mirror / unset_mirror
# ---------------------------------------------------------------------------

class TestMirror:
    def test_set_mirror_command(self, monkeypatch):
        calls = _capture_cmd(monkeypatch)
        DisplayManager.set_mirror(source="DP-1", mirror="HDMI-1")
        assert calls[0] == [
            "hyprctl", "keyword", "monitor",
            "HDMI-1,preferred,auto,1,mirror,DP-1",
        ]

    def test_unset_mirror_re_enables_monitor(self, monkeypatch):
        calls = _capture_cmd(monkeypatch)
        DisplayManager.unset_mirror("HDMI-1")
        # First call must re-enable without mirror clause
        assert calls[0][3] == "HDMI-1,preferred,auto,1"
        assert "mirror" not in calls[0][3]


# ---------------------------------------------------------------------------
# set_position / set_scale
# ---------------------------------------------------------------------------

class TestPositionAndScale:
    def test_set_position_command(self, monkeypatch):
        calls = _capture_cmd(monkeypatch)
        DisplayManager.set_position("HDMI-1", x=2560, y=0, resolution="1920x1080@60.00", scale=1.5)
        assert calls[0] == [
            "hyprctl", "keyword", "monitor",
            "HDMI-1,1920x1080@60.00,2560x0,1.5",
        ]

    def test_set_scale_command(self, monkeypatch):
        calls = _capture_cmd(monkeypatch)
        DisplayManager.set_scale("DP-1", scale=2.0, resolution="2560x1440@143.85", x=0, y=0)
        assert calls[0] == [
            "hyprctl", "keyword", "monitor",
            "DP-1,2560x1440@143.85,0x0,2.0",
        ]

    def test_set_position_returns_false_on_error(self, monkeypatch):
        def boom(*a, **kw):
            raise subprocess.CalledProcessError(1, "hyprctl", stderr="nope")

        monkeypatch.setattr(subprocess, "run", boom)
        ok, _ = DisplayManager.set_position("X", 0, 0)
        assert ok is False
