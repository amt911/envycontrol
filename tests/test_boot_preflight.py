from types import SimpleNamespace

import pytest

import envycontrol
import envycontrol_boot as boot


def test_preflight_failure_has_zero_system_side_effects(monkeypatch):
    effects = []

    def fail_preflight():
        raise boot.AmbiguousBootBackendError("ambiguous: dracut and mkinitcpio")

    monkeypatch.setattr(envycontrol, "resolve_boot_rebuild_plan", fail_preflight, raising=False)
    monkeypatch.setattr(envycontrol, "cleanup", lambda: effects.append("cleanup"))
    monkeypatch.setattr(
        envycontrol,
        "create_file",
        lambda *args, **kwargs: effects.append("file"),
    )
    monkeypatch.setattr(
        envycontrol.subprocess,
        "run",
        lambda *args, **kwargs: effects.append("subprocess") or SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(envycontrol, "rebuild_initramfs", lambda: effects.append("initramfs"))

    with pytest.raises(boot.AmbiguousBootBackendError, match="ambiguous"):
        envycontrol.graphics_mode_switcher("hybrid", None, False, None, None, False)

    assert effects == []


def test_one_preflight_plan_is_reused_for_hybrid_mode(monkeypatch):
    events = []

    class FakePlan:
        def execute(self, runner, verbose=False):
            events.append(("boot", verbose, type(runner).__name__))

    plan = FakePlan()
    resolutions = []

    def resolve_plan():
        resolutions.append("resolve")
        return plan

    monkeypatch.setattr(envycontrol, "resolve_boot_rebuild_plan", resolve_plan, raising=False)
    monkeypatch.setattr(envycontrol, "cleanup", lambda: events.append("cleanup"))
    monkeypatch.setattr(envycontrol, "create_file", lambda *args, **kwargs: events.append("file"))
    monkeypatch.setattr(
        envycontrol.subprocess,
        "run",
        lambda *args, **kwargs: events.append("systemctl") or SimpleNamespace(returncode=0),
    )

    envycontrol.graphics_mode_switcher("hybrid", None, False, None, None, False)

    assert resolutions == ["resolve"]
    assert events[0] == "cleanup"
    assert events[-1][0] == "boot"
