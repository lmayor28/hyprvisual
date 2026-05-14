"""
Tests for ProfileManager.

Strategy: use tmp_path so nothing touches ~/.config/hypr.
Patch DisplayManager calls in apply_profile to verify ordering.
"""
import json
from pathlib import Path
from unittest.mock import patch, call

import pytest

from hyprvisual.core.display_manager import DisplayManager, Display
from hyprvisual.core.profile_manager import ProfileManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def profile_manager_path(tmp_path, monkeypatch):
    """Redirect ProfileManager's config file to a temp directory."""
    config_file = tmp_path / "hyprvisual.json"
    monkeypatch.setattr("hyprvisual.core.profile_manager.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("hyprvisual.core.profile_manager.CONFIG_FILE", config_file)
    return config_file


def _make_display(name: str, x: int = 0, y: int = 0, scale: float = 1.0,
                  disabled: bool = False, mirror_of: str = "none",
                  best_mode: str = "1920x1080@60.00") -> Display:
    return Display(
        id=0, name=name, description="Test", disabled=disabled,
        width=1920, height=1080, refreshRate=60.0,
        x=x, y=y, scale=scale, mirror_of=mirror_of, best_mode=best_mode,
    )


# ---------------------------------------------------------------------------
# Save / Load / Delete
# ---------------------------------------------------------------------------

class TestSaveLoadDelete:
    def test_save_creates_file(self, profile_manager_path):
        displays = [_make_display("DP-1")]
        ProfileManager.save_profile("home", displays)
        assert profile_manager_path.exists()

    def test_save_and_load_roundtrip(self, profile_manager_path):
        d = _make_display("DP-1", x=100, y=200, scale=1.5)
        ProfileManager.save_profile("work", [d])
        profiles = ProfileManager.load_profiles()

        assert "work" in profiles
        saved = profiles["work"][0]
        assert saved["name"] == "DP-1"
        assert saved["x"] == 100
        assert saved["y"] == 200
        assert saved["scale"] == 1.5

    def test_multiple_profiles_coexist(self, profile_manager_path):
        ProfileManager.save_profile("home", [_make_display("DP-1")])
        ProfileManager.save_profile("work", [_make_display("HDMI-1")])
        profiles = ProfileManager.load_profiles()
        assert set(profiles.keys()) == {"home", "work"}

    def test_save_overwrites_existing(self, profile_manager_path):
        ProfileManager.save_profile("home", [_make_display("DP-1", x=0)])
        ProfileManager.save_profile("home", [_make_display("DP-1", x=999)])
        profiles = ProfileManager.load_profiles()
        assert profiles["home"][0]["x"] == 999

    def test_delete_removes_profile(self, profile_manager_path):
        ProfileManager.save_profile("home", [_make_display("DP-1")])
        ProfileManager.delete_profile("home")
        profiles = ProfileManager.load_profiles()
        assert "home" not in profiles

    def test_delete_nonexistent_returns_false(self, profile_manager_path):
        result = ProfileManager.delete_profile("ghost")
        assert result is False

    def test_load_returns_empty_when_no_file(self, profile_manager_path):
        assert ProfileManager.load_profiles() == {}

    def test_profile_name_with_spaces_and_special_chars(self, profile_manager_path):
        """Profile names are arbitrary strings — save/load must handle them."""
        name = "mi layout 2025 (final)"
        ProfileManager.save_profile(name, [_make_display("DP-1")])
        profiles = ProfileManager.load_profiles()
        assert name in profiles

    def test_saves_mirror_of_field(self, profile_manager_path):
        d = _make_display("HDMI-1", mirror_of="DP-1")
        ProfileManager.save_profile("mirrored", [d])
        profiles = ProfileManager.load_profiles()
        assert profiles["mirrored"][0]["mirror_of"] == "DP-1"


# ---------------------------------------------------------------------------
# apply_profile — ordering and correctness
# ---------------------------------------------------------------------------

class TestApplyProfile:
    def test_apply_nonexistent_profile_returns_error(self, profile_manager_path):
        ok, msg = ProfileManager.apply_profile("ghost")
        assert ok is False
        assert "not found" in msg.lower()

    def test_apply_disables_before_enables(self, profile_manager_path):
        """
        Regression: Hyprland requires disabled monitors first, then enables,
        then mirrors. Verify the ordering is respected.
        """
        displays = [
            _make_display("DP-1", disabled=False),
            _make_display("HDMI-1", disabled=True),
        ]
        ProfileManager.save_profile("test", displays)

        order = []

        def fake_disable(name, enabled, **kw):
            order.append(("disable", name))
            return True, "ok"

        def fake_position(name, x, y, *a, **kw):
            order.append(("enable", name))
            return True, "ok"

        with patch.object(DisplayManager, "set_display_state", side_effect=fake_disable), \
             patch.object(DisplayManager, "set_position", side_effect=fake_position):
            ProfileManager.apply_profile("test")

        # All disables must precede all enables
        disable_indices = [i for i, (op, _) in enumerate(order) if op == "disable"]
        enable_indices  = [i for i, (op, _) in enumerate(order) if op == "enable"]
        assert max(disable_indices) < min(enable_indices)

    def test_apply_mirrors_come_last(self, profile_manager_path):
        """Mirrors must be applied after all primary monitors are enabled."""
        displays = [
            _make_display("DP-1", disabled=False),
            _make_display("HDMI-1", disabled=False, mirror_of="DP-1"),
        ]
        ProfileManager.save_profile("test", displays)

        order = []

        def fake_position(name, *a, **kw):
            order.append(("enable", name))
            return True, "ok"

        def fake_mirror(source, mirror, **kw):
            order.append(("mirror", mirror))
            return True, "ok"

        with patch.object(DisplayManager, "set_display_state", return_value=(True, "ok")), \
             patch.object(DisplayManager, "set_position", side_effect=fake_position), \
             patch.object(DisplayManager, "set_mirror", side_effect=fake_mirror):
            ProfileManager.apply_profile("test")

        enable_indices = [i for i, (op, _) in enumerate(order) if op == "enable"]
        mirror_indices = [i for i, (op, _) in enumerate(order) if op == "mirror"]
        assert enable_indices  # at least one enable happened
        assert mirror_indices  # at least one mirror happened
        assert max(enable_indices) < min(mirror_indices)

    def test_apply_does_not_shadow_profile_name(self, profile_manager_path):
        """
        Regression for the 'name' variable shadowing bug in apply_profile.
        A profile with two monitors where the second has a mirror must
        correctly apply the mirror without corrupting the profile name.
        """
        displays = [
            _make_display("DP-1"),
            _make_display("HDMI-1", mirror_of="DP-1"),
        ]
        ProfileManager.save_profile("shadow-test", displays)

        mirrored = []

        def fake_mirror(source, mirror, **kw):
            mirrored.append((source, mirror))
            return True, "ok"

        with patch.object(DisplayManager, "set_display_state", return_value=(True, "ok")), \
             patch.object(DisplayManager, "set_position", return_value=(True, "ok")), \
             patch.object(DisplayManager, "set_mirror", side_effect=fake_mirror):
            ok, _ = ProfileManager.apply_profile("shadow-test")

        assert ok is True
        assert mirrored == [("DP-1", "HDMI-1")]

    def test_apply_restores_position_and_scale(self, profile_manager_path):
        d = _make_display("DP-1", x=1920, y=0, scale=1.25, best_mode="2560x1440@143.85")
        ProfileManager.save_profile("positions", [d])

        position_calls = []

        def fake_position(name, x, y, resolution, scale):
            position_calls.append((name, x, y, resolution, scale))
            return True, "ok"

        with patch.object(DisplayManager, "set_display_state", return_value=(True, "ok")), \
             patch.object(DisplayManager, "set_position", side_effect=fake_position):
            ProfileManager.apply_profile("positions")

        assert position_calls == [("DP-1", 1920, 0, "2560x1440@143.85", 1.25)]
