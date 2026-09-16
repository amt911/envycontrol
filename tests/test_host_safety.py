from types import SimpleNamespace

import pytest

import envycontrol


def test_real_etc_write_is_blocked():
    with pytest.raises(RuntimeError, match="blocked protected write"):
        envycontrol.create_file("/etc/modprobe.d/envycontrol-test.conf", "unsafe")


def test_real_systemctl_is_blocked():
    with pytest.raises(RuntimeError, match="blocked dangerous command: systemctl"):
        envycontrol.subprocess.run(["systemctl", "disable", "nvidia-persistenced.service"])


def test_real_lspci_is_blocked():
    with pytest.raises(RuntimeError, match="blocked host discovery command: lspci"):
        envycontrol.subprocess.check_output(["lspci"])


def test_tmp_path_write_is_allowed(tmp_path):
    target = tmp_path / "generated.conf"
    envycontrol.create_file(str(target), "safe")
    assert target.read_text() == "safe"


def test_mode_switch_can_replace_dangerous_boundaries_with_fakes(monkeypatch):
    calls = []
    files = []

    monkeypatch.setattr(
        envycontrol.subprocess,
        "run",
        lambda args, **kwargs: calls.append(tuple(args)) or SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(envycontrol, "cleanup", lambda: calls.append(("cleanup",)))
    monkeypatch.setattr(
        envycontrol,
        "create_file",
        lambda path, content, executable=False: files.append((path, content, executable)),
    )
    class FakePlan:
        def execute(self, runner, verbose=False):
            calls.append(("initramfs",))

    monkeypatch.setattr(envycontrol, "resolve_boot_rebuild_plan", lambda: FakePlan())

    envycontrol.graphics_mode_switcher("integrated", None, False, None, None, False)

    assert ("systemctl", "disable", "nvidia-persistenced.service") in calls
    assert ("cleanup",) in calls
    assert ("initramfs",) in calls
    assert [entry[0] for entry in files] == [
        envycontrol.BLACKLIST_PATH,
        envycontrol.UDEV_INTEGRATED_PATH,
    ]
