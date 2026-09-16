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


def test_arch_dracut_hybrid_never_runs_mkinitcpio(monkeypatch):
    class FakeProbe:
        def __init__(self):
            self.paths = {
                "/etc/arch-release",
                "/usr/share/libalpm/hooks/90-dracut-install.hook",
            }
            self.commands = {"dracut", "mkinitcpio"}

        def exists(self, path):
            return str(path) in self.paths

        def is_file(self, path):
            return str(path) in self.paths

        def is_masked(self, path):
            return False

        def command_exists(self, name):
            return name in self.commands

        def read_text(self, path):
            return None

        def glob(self, pattern):
            return ()

    boot_calls = []

    class RecordingRunner:
        def run(self, argv, *, verbose=False):
            boot_calls.append(tuple(argv))
            return boot.CommandResult(returncode=0)

    fake_probe = FakeProbe()
    monkeypatch.setattr(boot, "LocalSystemProbe", lambda: fake_probe)
    monkeypatch.setattr(boot, "SubprocessCommandRunner", RecordingRunner)
    monkeypatch.setattr(envycontrol, "cleanup", lambda: None)
    monkeypatch.setattr(envycontrol, "create_file", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        envycontrol.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0),
    )

    envycontrol.graphics_mode_switcher("hybrid", None, False, None, None, False)

    assert boot_calls == [("dracut", "-f", "--regenerate-all")]
    assert all("mkinitcpio" not in command for call in boot_calls for command in call)
